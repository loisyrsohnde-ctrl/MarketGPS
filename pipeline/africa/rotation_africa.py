"""
MarketGPS v14.0 - Africa Rotation Job
Complete rotation pipeline for African markets with atomic publish.

Features:
- Tiered asset selection (tier 1 first, then tier 2)
- Watchlist and user_interest priority
- Data fetching with provider fallback
- Gating evaluation
- Scoring with Africa-specific weights
- Staging table writes
- Atomic publish at end

This is the main production job for AFRICA scope.
"""

import time
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Set, Literal
from dataclasses import dataclass

from core.config import get_config, get_logger
from core.models import Asset, Score, GatingStatus, RotationState
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.africa.data_fetcher_africa import AfricaDataFetcher
from pipeline.africa.gating_africa import GatingAfricaJob
from pipeline.africa.scoring_africa_v2 import ScoringAfricaEngine

logger = get_logger(__name__)

MarketScope = Literal["AFRICA"]
JobMode = Literal["daily_full", "hourly_overlay", "on_demand"]


# ═══════════════════════════════════════════════════════════════════════════
# JOB RESULT DATACLASS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AfricaRotationResult:
    """Result of Africa rotation job."""
    run_id: str
    mode: str
    status: str
    assets_processed: int
    assets_scored: int
    assets_gated: int
    assets_failed: int
    duration_seconds: float
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "status": self.status,
            "assets_processed": self.assets_processed,
            "assets_scored": self.assets_scored,
            "assets_gated": self.assets_gated,
            "assets_failed": self.assets_failed,
            "duration_seconds": round(self.duration_seconds, 2),
            "error": self.error
        }


# ═══════════════════════════════════════════════════════════════════════════
# ROTATION JOB CLASS
# ═══════════════════════════════════════════════════════════════════════════

class RotationAfricaJob:
    """
    Africa-specific rotation job with staging → atomic publish.
    
    Process:
    1. Select assets to update (priority-based)
    2. Fetch price data
    3. Run gating
    4. Score eligible assets
    5. Stage all results
    6. Atomically publish
    
    Modes:
    - daily_full: All tier 1 + tier 2 assets
    - hourly_overlay: Only tier 1 + watchlist + top 30
    - on_demand: Specific assets only
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        parquet_store: Optional[ParquetStore] = None
    ):
        """
        Initialize rotation job.
        
        Args:
            store: SQLite store
            parquet_store: Parquet store for AFRICA scope
        """
        self._config = get_config()
        self._store = store or SQLiteStore()
        self._parquet = parquet_store or ParquetStore(market_scope="AFRICA")
        
        # Initialize components
        self._data_fetcher = AfricaDataFetcher(
            parquet_store=self._parquet,
            sqlite_store=self._store
        )
        self._gating = GatingAfricaJob(
            store=self._store,
            parquet_store=self._parquet
        )
        self._scoring = ScoringAfricaEngine(
            store=self._store,
            parquet_store=self._parquet
        )
    
    def run(
        self,
        mode: JobMode = "daily_full",
        batch_size: int = 50,
        asset_ids: Optional[List[str]] = None
    ) -> AfricaRotationResult:
        """
        Run rotation job with staging → atomic publish.
        
        Args:
            mode: Job mode (daily_full, hourly_overlay, on_demand)
            batch_size: Assets per batch
            asset_ids: Specific assets (for on_demand mode)
            
        Returns:
            AfricaRotationResult with job metrics
        """
        start_time = time.time()
        
        # Create job run
        run_id = self._store.create_job_run(
            market_scope="AFRICA",
            job_type="rotation",
            mode=mode,
            created_by="scheduler" if mode != "on_demand" else "api"
        )
        
        logger.info(f"[AFRICA] Starting rotation job {run_id[:8]}... (mode={mode})")
        
        # Initialize counters
        processed = 0
        scored = 0
        gated = 0
        failed = 0
        error_msg = None
        
        try:
            # 1. Build asset set based on mode
            if mode == "on_demand" and asset_ids:
                target_assets = asset_ids
            elif mode == "hourly_overlay":
                target_assets = self._build_overlay_set(batch_size)
            else:  # daily_full
                target_assets = self._build_full_set(batch_size * 4)
            
            logger.info(f"[AFRICA] Processing {len(target_assets)} assets")
            
            # 2. Process in batches
            for i in range(0, len(target_assets), batch_size):
                batch = target_assets[i:i + batch_size]
                
                for asset_id in batch:
                    try:
                        # Fetch data
                        df = self._data_fetcher.fetch_bars(
                            asset_id,
                            days=504 if mode == "daily_full" else 252
                        )
                        
                        # Get asset info
                        asset = self._store.get_asset(asset_id)
                        if not asset:
                            failed += 1
                            continue
                        
                        # Run gating
                        gating_status = self._gating._evaluate_asset(asset, fetch_data=False)
                        self._store.insert_staging_gating(run_id, gating_status, "AFRICA")
                        gated += 1
                        
                        # Score if eligible
                        if gating_status.eligible:
                            score = self._scoring.score_asset(asset_id)
                            
                            if score and score.score_total is not None:
                                self._store.insert_staging_score(run_id, score, "AFRICA")
                                scored += 1
                            else:
                                failed += 1
                        
                        # Update rotation state
                        self._update_rotation_state(asset_id)
                        processed += 1
                        
                    except Exception as e:
                        logger.warning(f"[AFRICA] Failed to process {asset_id}: {e}")
                        failed += 1
                
                # Update job progress
                self._store.update_job_run_status(
                    run_id,
                    status="staging",
                    assets_processed=processed,
                    assets_success=scored,
                    assets_failed=failed
                )
                
                logger.info(
                    f"[AFRICA] Batch {i // batch_size + 1}: "
                    f"{processed} processed, {scored} scored, {failed} failed"
                )
            
            # 3. Atomic publish
            publish_result = self._store.publish_run(
                run_id,
                market_scope="AFRICA",
                publish_scores=True,
                publish_gating=True
            )
            
            duration = time.time() - start_time
            
            logger.info(
                f"[AFRICA] Rotation complete: "
                f"{scored} scores, {gated} gating in {duration:.1f}s"
            )
            
            return AfricaRotationResult(
                run_id=run_id,
                mode=mode,
                status="success",
                assets_processed=processed,
                assets_scored=scored,
                assets_gated=gated,
                assets_failed=failed,
                duration_seconds=duration
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[AFRICA] Rotation failed: {e}", exc_info=True)
            
            # Rollback
            self._store.rollback_run(run_id)
            
            duration = time.time() - start_time
            
            return AfricaRotationResult(
                run_id=run_id,
                mode=mode,
                status="failed",
                assets_processed=processed,
                assets_scored=scored,
                assets_gated=gated,
                assets_failed=failed,
                duration_seconds=duration,
                error=error_msg
            )
    
    def _build_full_set(self, limit: int) -> List[str]:
        """
        Build full asset set for daily_full mode.
        
        Priority:
        1. Current top 30 (keep fresh)
        2. Tier 1 assets
        3. Watchlist
        4. User interest
        5. Stale tier 2 assets
        """
        asset_ids: Set[str] = set()
        
        # 1. Current top 30
        top_scores = self._store.get_top_scores(limit=30, market_scope="AFRICA")
        for asset, score in top_scores:
            asset_ids.add(asset.asset_id)
        
        # 2. Tier 1 assets
        tier1 = self._get_tier_assets(tier=1, limit=100)
        for aid in tier1:
            if len(asset_ids) < limit:
                asset_ids.add(aid)
        
        # 3. Watchlist
        watchlist = self._store.get_watchlist_tickers()
        for ticker in watchlist[:50]:
            # Find asset_id from ticker
            with self._store._get_connection() as conn:
                row = conn.execute(
                    "SELECT asset_id FROM universe WHERE symbol = ? AND market_scope = 'AFRICA'",
                    (ticker,)
                ).fetchone()
                if row and len(asset_ids) < limit:
                    asset_ids.add(row["asset_id"])
        
        # 4. User interest (high priority)
        with self._store._get_connection() as conn:
            rows = conn.execute("""
                SELECT asset_id FROM user_interest
                WHERE market_scope = 'AFRICA' AND expires_at > datetime('now')
                ORDER BY priority_boost DESC
                LIMIT 30
            """).fetchall()
            for row in rows:
                if len(asset_ids) < limit:
                    asset_ids.add(row["asset_id"])
        
        # 5. Stale tier 2 assets
        stale = self._get_stale_assets(limit=limit - len(asset_ids))
        for aid in stale:
            if len(asset_ids) < limit:
                asset_ids.add(aid)
        
        # 6. Fill with remaining active assets
        if len(asset_ids) < limit:
            remaining = self._store.get_priority_assets(
                limit=limit - len(asset_ids),
                market_scope="AFRICA"
            )
            for aid in remaining:
                asset_ids.add(aid)
        
        return list(asset_ids)[:limit]
    
    def _build_overlay_set(self, limit: int) -> List[str]:
        """
        Build asset set for hourly_overlay mode.
        
        Only high-priority assets:
        1. Current top 30
        2. Tier 1
        3. Watchlist
        """
        asset_ids: Set[str] = set()
        
        # Current top 30
        top_scores = self._store.get_top_scores(limit=30, market_scope="AFRICA")
        for asset, score in top_scores:
            asset_ids.add(asset.asset_id)
        
        # Tier 1
        tier1 = self._get_tier_assets(tier=1, limit=50)
        for aid in tier1:
            if len(asset_ids) < limit:
                asset_ids.add(aid)
        
        # Watchlist (top 20)
        watchlist = self._store.get_watchlist_tickers()
        for ticker in watchlist[:20]:
            with self._store._get_connection() as conn:
                row = conn.execute(
                    "SELECT asset_id FROM universe WHERE symbol = ? AND market_scope = 'AFRICA'",
                    (ticker,)
                ).fetchone()
                if row and len(asset_ids) < limit:
                    asset_ids.add(row["asset_id"])
        
        return list(asset_ids)[:limit]
    
    def _get_tier_assets(self, tier: int, limit: int) -> List[str]:
        """Get assets by tier."""
        with self._store._get_connection() as conn:
            rows = conn.execute("""
                SELECT asset_id FROM universe
                WHERE active = 1 AND tier = ? AND market_scope = 'AFRICA'
                ORDER BY priority_level ASC, symbol ASC
                LIMIT ?
            """, (tier, limit)).fetchall()
            return [row["asset_id"] for row in rows]
    
    def _get_stale_assets(self, limit: int) -> List[str]:
        """Get assets with oldest refresh."""
        with self._store._get_connection() as conn:
            rows = conn.execute("""
                SELECT u.asset_id 
                FROM universe u
                LEFT JOIN rotation_state r ON u.asset_id = r.asset_id
                WHERE u.active = 1 AND u.market_scope = 'AFRICA' AND u.tier = 2
                ORDER BY r.last_refresh_at ASC NULLS FIRST
                LIMIT ?
            """, (limit,)).fetchall()
            return [row["asset_id"] for row in rows]
    
    def _update_rotation_state(self, asset_id: str):
        """Update rotation state for an asset."""
        state = RotationState(
            asset_id=asset_id,
            last_refresh_at=datetime.now().isoformat(),
            priority_level=2,
            in_top50=False,
            refresh_count=1
        )
        self._store.upsert_rotation_state(state, market_scope="AFRICA")
    
    def refresh_single(self, asset_id: str) -> Optional[Score]:
        """
        Refresh a single asset (for on_demand scoring).
        
        Args:
            asset_id: Asset to refresh
            
        Returns:
            Score or None
        """
        try:
            # Fetch data
            df = self._data_fetcher.fetch_bars(asset_id, days=504)
            
            # Score
            score = self._scoring.score_asset(asset_id)
            
            if score and score.score_total is not None:
                self._store.upsert_score(score, market_scope="AFRICA")
                return score
            
            return None
            
        except Exception as e:
            logger.error(f"[AFRICA] Refresh failed for {asset_id}: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def run_africa_rotation(
    mode: JobMode = "daily_full",
    batch_size: int = 50
) -> AfricaRotationResult:
    """
    Run Africa rotation job.
    
    Args:
        mode: daily_full, hourly_overlay, or on_demand
        batch_size: Assets per batch
        
    Returns:
        AfricaRotationResult
    """
    job = RotationAfricaJob()
    return job.run(mode=mode, batch_size=batch_size)


def refresh_africa_asset(asset_id: str) -> Optional[Score]:
    """
    Refresh a single African asset.
    
    Args:
        asset_id: Asset to refresh
        
    Returns:
        Score or None
    """
    job = RotationAfricaJob()
    return job.refresh_single(asset_id)


def run_africa_gating_only(batch_size: int = 50) -> Dict[str, int]:
    """
    Run gating only (no scoring).
    
    Args:
        batch_size: Assets per batch
        
    Returns:
        Dict with stats
    """
    gating_job = GatingAfricaJob()
    return gating_job.run(batch_size=batch_size)
