"""
MarketGPS v13.0 - Production Job Runner
Wraps pipeline jobs with staging → atomic publish pattern.
Supports: daily_full, hourly_overlay, on_demand modes.
"""
import time
from datetime import date, datetime, timedelta
from typing import Literal, Optional, List, Dict, Any
from dataclasses import dataclass

from core.config import get_config, get_logger
from core.models import Score, GatingStatus
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from providers import get_provider
from pipeline.scoring import ScoringEngine

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]
JobMode = Literal["daily_full", "hourly_overlay", "on_demand"]


@dataclass
class JobResult:
    """Result of a job run."""
    run_id: str
    market_scope: str
    job_type: str
    mode: str
    status: str
    assets_processed: int
    assets_success: int
    assets_failed: int
    duration_seconds: float
    error: Optional[str] = None


class ProductionJobRunner:
    """
    Production-grade job runner with staging → publish pattern.
    
    Features:
    - Atomic publish (staging tables → production tables in transaction)
    - Job run tracking with metrics
    - Rate limiting for API calls
    - Error handling and rollback
    - Support for multiple modes
    """
    
    def __init__(
        self,
        market_scope: MarketScope = "US_EU",
        store: Optional[SQLiteStore] = None
    ):
        """
        Initialize the job runner.
        
        Args:
            market_scope: US_EU or AFRICA
            store: SQLite store instance (optional)
        """
        self._scope = market_scope
        self._config = get_config()
        self._store = store or SQLiteStore()
        self._parquet = ParquetStore(market_scope=market_scope)
        self._provider = get_provider("auto")
        self._scoring = ScoringEngine()
        
        # Validate API key at startup
        if not self._config.eodhd.is_configured:
            logger.warning(
                "EODHD API key not configured. "
                "Set EODHD_API_KEY environment variable for production use."
            )
    
    def run_gating(
        self,
        mode: JobMode = "daily_full",
        batch_size: int = 50,
        asset_ids: Optional[List[str]] = None
    ) -> JobResult:
        """
        Run gating job with staging → publish pattern.
        
        Args:
            mode: daily_full, hourly_overlay, or on_demand
            batch_size: Number of assets per batch
            asset_ids: Specific assets to process (for on_demand mode)
            
        Returns:
            JobResult with metrics
        """
        start_time = time.time()
        
        # Create job run
        run_id = self._store.create_job_run(
            market_scope=self._scope,
            job_type="gating",
            mode=mode,
            created_by="scheduler" if mode != "on_demand" else "api"
        )
        
        processed = 0
        success = 0
        failed = 0
        error_msg = None
        
        try:
            # Get assets to process based on mode
            if mode == "on_demand" and asset_ids:
                assets = [self._store.get_asset(aid) for aid in asset_ids]
                assets = [a for a in assets if a is not None]
            elif mode == "hourly_overlay":
                # Only tier 1 assets
                assets = self._get_tier1_assets()
            else:
                # daily_full: all active assets
                assets = self._store.get_active_assets(market_scope=self._scope)
            
            logger.info(f"[{self._scope}] Gating {len(assets)} assets (mode={mode})")
            
            # Process in batches
            for i in range(0, len(assets), batch_size):
                batch = assets[i:i + batch_size]
                
                for asset in batch:
                    try:
                        gating = self._evaluate_gating(asset)
                        if gating:
                            self._store.insert_staging_gating(run_id, gating, self._scope)
                            success += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.warning(f"Gating failed for {asset.asset_id}: {e}")
                        failed += 1
                    
                    processed += 1
                
                # Update progress
                self._store.update_job_run_status(
                    run_id, "staging",
                    assets_processed=processed,
                    assets_success=success,
                    assets_failed=failed
                )
            
            # Atomic publish
            self._store.publish_run(run_id, self._scope, publish_scores=False, publish_gating=True)
            
            duration = time.time() - start_time
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="gating",
                mode=mode,
                status="success",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gating job failed: {e}")
            self._store.rollback_run(run_id)
            
            duration = time.time() - start_time
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="gating",
                mode=mode,
                status="failed",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration,
                error=error_msg
            )
    
    def run_scoring(
        self,
        mode: JobMode = "daily_full",
        batch_size: int = 50,
        asset_ids: Optional[List[str]] = None
    ) -> JobResult:
        """
        Run scoring job with staging → publish pattern.
        
        Args:
            mode: daily_full, hourly_overlay, or on_demand
            batch_size: Number of assets per batch
            asset_ids: Specific assets to process (for on_demand mode)
            
        Returns:
            JobResult with metrics
        """
        start_time = time.time()
        
        # Create job run
        run_id = self._store.create_job_run(
            market_scope=self._scope,
            job_type="scoring",
            mode=mode,
            created_by="scheduler" if mode != "on_demand" else "api"
        )
        
        processed = 0
        success = 0
        failed = 0
        error_msg = None
        
        try:
            # Get assets to process based on mode
            if mode == "on_demand" and asset_ids:
                asset_id_list = asset_ids
            elif mode == "hourly_overlay":
                # Only tier 1 + current top 50
                asset_id_list = self._get_priority_asset_ids(batch_size)
            else:
                # daily_full: all eligible assets
                asset_id_list = self._store.get_eligible_assets(self._scope)
            
            logger.info(f"[{self._scope}] Scoring {len(asset_id_list)} assets (mode={mode})")
            
            # Process in batches
            for i in range(0, len(asset_id_list), batch_size):
                batch_ids = asset_id_list[i:i + batch_size]
                
                for asset_id in batch_ids:
                    try:
                        score = self._compute_score(asset_id, mode)
                        if score and score.score_total is not None:
                            self._store.insert_staging_score(run_id, score, self._scope)
                            success += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.warning(f"Scoring failed for {asset_id}: {e}")
                        failed += 1
                    
                    processed += 1
                
                # Update progress
                self._store.update_job_run_status(
                    run_id, "staging",
                    assets_processed=processed,
                    assets_success=success,
                    assets_failed=failed
                )
            
            # Atomic publish
            self._store.publish_run(run_id, self._scope, publish_scores=True, publish_gating=False)
            
            duration = time.time() - start_time
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="scoring",
                mode=mode,
                status="success",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Scoring job failed: {e}")
            self._store.rollback_run(run_id)
            
            duration = time.time() - start_time
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="scoring",
                mode=mode,
                status="failed",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration,
                error=error_msg
            )
    
    def run_rotation(
        self,
        mode: JobMode = "daily_full",
        batch_size: int = 50,
        asset_ids: Optional[List[str]] = None
    ) -> JobResult:
        """
        Run rotation job (fetch data + score) with staging → publish pattern.
        
        This is the main production job that:
        1. Fetches new price data from provider
        2. Computes scores
        3. Stages results
        4. Atomically publishes
        
        Args:
            mode: daily_full, hourly_overlay, or on_demand
            batch_size: Number of assets per batch
            asset_ids: Specific assets to process (for on_demand mode)
            
        Returns:
            JobResult with metrics
        """
        start_time = time.time()
        
        # Create job run
        run_id = self._store.create_job_run(
            market_scope=self._scope,
            job_type="rotation",
            mode=mode,
            created_by="scheduler" if mode != "on_demand" else "api"
        )
        
        processed = 0
        success = 0
        failed = 0
        error_msg = None
        
        try:
            # Get assets to process based on mode
            if mode == "on_demand" and asset_ids:
                asset_id_list = asset_ids
            elif mode == "hourly_overlay":
                # Only tier 1 + current top 50
                asset_id_list = self._get_priority_asset_ids(batch_size)
            else:
                # daily_full: tier 1 + tier 2 eligible
                asset_id_list = self._build_rotation_set(batch_size * 4)
            
            logger.info(f"[{self._scope}] Rotation {len(asset_id_list)} assets (mode={mode})")
            
            # Process in batches
            for i in range(0, len(asset_id_list), batch_size):
                batch_ids = asset_id_list[i:i + batch_size]
                
                for asset_id in batch_ids:
                    try:
                        # Fetch data and compute score
                        score = self._process_rotation_asset(asset_id, mode)
                        if score and score.score_total is not None:
                            self._store.insert_staging_score(run_id, score, self._scope)
                            success += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.warning(f"Rotation failed for {asset_id}: {e}")
                        failed += 1
                    
                    processed += 1
                
                # Update progress
                self._store.update_job_run_status(
                    run_id, "staging",
                    assets_processed=processed,
                    assets_success=success,
                    assets_failed=failed
                )
                
                logger.info(f"[{self._scope}] Processed batch {i // batch_size + 1}, total: {processed}")
            
            # Atomic publish
            self._store.publish_run(run_id, self._scope, publish_scores=True, publish_gating=False)
            
            duration = time.time() - start_time
            logger.info(
                f"[{self._scope}] Rotation complete: {success}/{processed} success in {duration:.1f}s"
            )
            
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="rotation",
                mode=mode,
                status="success",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Rotation job failed: {e}")
            self._store.rollback_run(run_id)
            
            duration = time.time() - start_time
            return JobResult(
                run_id=run_id,
                market_scope=self._scope,
                job_type="rotation",
                mode=mode,
                status="failed",
                assets_processed=processed,
                assets_success=success,
                assets_failed=failed,
                duration_seconds=duration,
                error=error_msg
            )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # INTERNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _get_tier1_assets(self) -> list:
        """Get tier 1 assets for this scope."""
        with self._store._get_connection() as conn:
            rows = conn.execute("""
                SELECT asset_id FROM universe
                WHERE active = 1 AND tier = 1 AND market_scope = ?
            """, (self._scope,)).fetchall()
            return [self._store.get_asset(row["asset_id"]) for row in rows]
    
    def _get_priority_asset_ids(self, limit: int) -> List[str]:
        """Get priority asset IDs (top 50 + tier 1)."""
        asset_ids = set()
        
        # Current top 50
        top_scores = self._store.get_top_scores(limit=50, market_scope=self._scope)
        for asset, score in top_scores:
            asset_ids.add(asset.asset_id)
        
        # Tier 1 assets
        tier1 = self._store.get_priority_assets(limit=limit, market_scope=self._scope)
        for aid in tier1:
            asset_ids.add(aid)
        
        return list(asset_ids)[:limit]
    
    def _build_rotation_set(self, limit: int) -> List[str]:
        """Build set of assets to rotate (tier 1 + stale tier 2)."""
        asset_ids = set()
        
        # Current top 50
        top_scores = self._store.get_top_scores(limit=50, market_scope=self._scope)
        for asset, score in top_scores:
            asset_ids.add(asset.asset_id)
        
        # Tier 1 assets
        tier1 = self._store.get_priority_assets(limit=100, market_scope=self._scope)
        for aid in tier1:
            asset_ids.add(aid)
        
        # Fill with eligible assets
        remaining = limit - len(asset_ids)
        if remaining > 0:
            eligible = self._store.get_eligible_assets(self._scope)
            for aid in eligible:
                if len(asset_ids) >= limit:
                    break
                asset_ids.add(aid)
        
        return list(asset_ids)
    
    def _evaluate_gating(self, asset) -> Optional[GatingStatus]:
        """Evaluate gating for a single asset."""
        from pipeline.gating import GatingJob
        
        gating_job = GatingJob(
            store=self._store,
            parquet_store=self._parquet,
            market_scope=self._scope
        )
        return gating_job._evaluate_asset(asset)
    
    def _compute_score(self, asset_id: str, mode: JobMode) -> Optional[Score]:
        """Compute score for a single asset using existing data."""
        asset = self._store.get_asset(asset_id)
        if not asset:
            return None
        
        # Load existing data from parquet
        df = self._parquet.load_bars(asset_id)
        if df is None or df.empty:
            return None
        
        # Get gating info
        gating = self._store.get_gating(asset_id)
        
        # Compute score
        if self._scope == "AFRICA":
            from pipeline.scoring_africa import AfricaScoringPipeline
            pipeline = AfricaScoringPipeline(self._store, self._parquet)
            return pipeline.score_asset(asset_id)
        else:
            return self._scoring.compute_score(
                asset=asset,
                df=df,
                fundamentals=None,
                gating=gating
            )
    
    def _process_rotation_asset(self, asset_id: str, mode: JobMode) -> Optional[Score]:
        """Process a single asset in rotation: fetch data + compute score."""
        asset = self._store.get_asset(asset_id)
        if not asset:
            return None
        
        # Check gating
        gating = self._store.get_gating(asset_id)
        if gating and not gating.eligible:
            logger.debug(f"Skipping ineligible: {asset_id}")
            return None
        
        # Determine date range
        last_date = self._parquet.get_last_date(asset_id)
        
        if mode == "hourly_overlay":
            # Only fetch last few days for overlay
            start_date = date.today() - timedelta(days=7)
        elif last_date:
            start_date = last_date + timedelta(days=1)
        else:
            # 5+ years of history for institutional-grade scoring
            start_date = date.today() - timedelta(days=1825)
        
        end_date = date.today()
        
        # Skip if already up to date
        if last_date and last_date >= end_date - timedelta(days=1):
            df = self._parquet.load_bars(asset_id)
        else:
            # Fetch new data
            try:
                new_data = self._provider.fetch_daily_bars(
                    asset_id,
                    start=start_date,
                    end=end_date
                )
                
                if not new_data.empty:
                    self._parquet.upsert_bars(asset_id, new_data)
                
                df = self._parquet.load_bars(asset_id)
            except Exception as e:
                logger.warning(f"Failed to fetch data for {asset_id}: {e}")
                df = self._parquet.load_bars(asset_id)
        
        if df is None or df.empty:
            return None
        
        # Compute score
        if self._scope == "AFRICA":
            from pipeline.scoring_africa import AfricaScoringPipeline
            pipeline = AfricaScoringPipeline(self._store, self._parquet)
            return pipeline.score_asset(asset_id)
        else:
            # Fetch fundamentals for equities
            fundamentals = None
            if asset.asset_type.has_fundamentals:
                try:
                    fundamentals = self._provider.fetch_fundamentals(asset_id)
                except Exception:
                    pass
            
            return self._scoring.compute_score(
                asset=asset,
                df=df,
                fundamentals=fundamentals,
                gating=gating
            )


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def run_us_eu(mode: JobMode = "daily_full", batch_size: int = 50) -> JobResult:
    """
    Run rotation job for US_EU scope.
    
    Args:
        mode: daily_full, hourly_overlay, or on_demand
        batch_size: Number of assets per batch
        
    Returns:
        JobResult with metrics
    """
    runner = ProductionJobRunner(market_scope="US_EU")
    return runner.run_rotation(mode=mode, batch_size=batch_size)


def run_africa(mode: JobMode = "daily_full", batch_size: int = 50) -> JobResult:
    """
    Run rotation job for AFRICA scope.
    
    Args:
        mode: daily_full, hourly_overlay, or on_demand
        batch_size: Number of assets per batch
        
    Returns:
        JobResult with metrics
    """
    runner = ProductionJobRunner(market_scope="AFRICA")
    return runner.run_rotation(mode=mode, batch_size=batch_size)


def score_on_demand(
    asset_ids: List[str],
    market_scope: MarketScope = "US_EU"
) -> JobResult:
    """
    Score specific assets on demand (for premium users).
    
    Args:
        asset_ids: List of asset IDs to score
        market_scope: US_EU or AFRICA
        
    Returns:
        JobResult with metrics
    """
    runner = ProductionJobRunner(market_scope=market_scope)
    return runner.run_scoring(mode="on_demand", asset_ids=asset_ids)
