"""
MarketGPS v11.0 - Rotation Pipeline (SCOPE-AWARE)
Intelligent tiered refresh - no full market scan.
Job queue processing is handled separately by the worker.
Supports market scopes: US_EU, AFRICA
"""
from datetime import date, datetime, timedelta
from typing import Optional, List, Set, Literal
import pandas as pd

from core.config import get_config, get_logger
from core.models import Asset, RotationState, Score
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from providers import get_provider
from pipeline.scoring import ScoringEngine
from pipeline.quality_adjustments import apply_quality_liquidity_adjustments
from pipeline.scoring_longterm import compute_longterm_score
import json

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]


class RotationJob:
    """
    Rotation job for intelligent tiered refresh.
    
    Never scans the entire market. Instead:
    1. Refresh current Top 50
    2. Refresh Tier 1 (institutional) assets
    3. Refresh N oldest (stale) Tier 2 assets
    4. Union these sets, limited by batch_size
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        parquet_store: Optional[ParquetStore] = None,
        market_scope: MarketScope = "US_EU",
        run_longterm: bool = False
    ):
        """
        Initialize Rotation job.
        
        Args:
            store: SQLite store instance
            parquet_store: Parquet store instance
            market_scope: Market scope to operate on
            run_longterm: If True, also compute long-term institutional scores
        """
        self._config = get_config()
        self._store = store or SQLiteStore()
        self._parquet = parquet_store or ParquetStore(market_scope=market_scope)
        self._provider = get_provider("auto")
        self._scoring = ScoringEngine()
        self._market_scope = market_scope
        self._run_longterm = run_longterm
        
        # Ensure longterm schema if enabled
        if self._run_longterm and self._market_scope == "US_EU":
            self._store.ensure_longterm_schema()
    
    def run(self, batch_size: Optional[int] = None) -> dict:
        """
        Run the rotation job for this scope.
        
        Args:
            batch_size: Override batch size from config
            
        Returns:
            Dict with job results
        """
        batch_size = batch_size or self._config.pipeline.rotation_batch_size
        
        logger.info(f"Starting Rotation job [{self._market_scope}] (batch_size={batch_size})")
        
        results = {
            "processed": 0,
            "updated": 0,
            "errors": 0,
            "top50_refreshed": 0,
            "tier1_refreshed": 0,
            "tier2_refreshed": 0
        }
        
        try:
            # Build the set of assets to update
            assets_to_update = self._build_update_set(batch_size)
            
            if not assets_to_update:
                logger.info("No assets to update")
                return results
            
            logger.info(f"Updating {len(assets_to_update)} assets")
            
            # Process each asset
            for asset_id in assets_to_update:
                try:
                    success = self._process_asset(asset_id)
                    
                    results["processed"] += 1
                    if success:
                        results["updated"] += 1
                    else:
                        results["errors"] += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to process {asset_id}: {e}")
                    self._mark_rotation_error(asset_id, str(e))
                    results["errors"] += 1
            
            # Update Top 50 flags
            self._update_top50_flags()
            
            logger.info(f"Rotation job complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Rotation job failed: {e}")
            results["errors"] += 1
            return results
    
    def _build_update_set(self, batch_size: int) -> List[str]:
        """
        Build the set of assets to update in this rotation.
        
        Priority:
        1. Current Top 50 (always keep fresh)
        2. Tier 1 assets (institutional)
        3. Stale Tier 2 assets (fill remaining slots)
        """
        assets: Set[str] = set()
        
        # 1. Get current Top 50
        top50 = self._get_top50_asset_ids()
        for asset_id in top50:
            if len(assets) < batch_size:
                assets.add(asset_id)
        
        # 2. Get Tier 1 assets
        tier1 = self._get_tier_assets(tier=1, limit=batch_size)
        for asset_id in tier1:
            if len(assets) < batch_size:
                assets.add(asset_id)
        
        # 3. Get stale Tier 2 assets to fill remaining slots
        remaining_slots = batch_size - len(assets)
        if remaining_slots > 0:
            stale = self._get_stale_assets(limit=remaining_slots * 2)
            for asset_id in stale:
                if len(assets) < batch_size:
                    assets.add(asset_id)
        
        return list(assets)
    
    def _get_top50_asset_ids(self) -> List[str]:
        """Get current Top 50 asset IDs for this scope."""
        results = self._store.get_top_scores(limit=50, market_scope=self._market_scope)
        return [asset.asset_id for asset, score in results]
    
    def _get_tier_assets(self, tier: int, limit: int) -> List[str]:
        """Get assets by tier for this scope."""
        with self._store._get_connection() as conn:
            rows = conn.execute("""
                SELECT asset_id FROM universe
                WHERE active = 1 AND tier = ? AND market_scope = ?
                ORDER BY symbol
                LIMIT ?
            """, (tier, self._market_scope, limit)).fetchall()
            return [row["asset_id"] for row in rows]
    
    def _get_stale_assets(self, limit: int) -> List[str]:
        """Get assets with oldest refresh times for this scope."""
        return self._store.get_priority_assets(limit=limit, market_scope=self._market_scope)
    
    def _process_asset(self, asset_id: str) -> bool:
        """
        Process a single asset: fetch delta, compute score, update stores.
        """
        # Get asset info
        asset = self._store.get_asset(asset_id)
        if not asset:
            logger.warning(f"Asset not found: {asset_id}")
            return False
        
        # Check gating status
        gating = self._store.get_gating(asset_id)
        if gating and not gating.eligible:
            logger.debug(f"Skipping ineligible asset: {asset_id}")
            return False
        
        # Get last date from parquet
        last_date = self._parquet.get_last_date(asset_id)
        
        # Fetch delta
        if last_date:
            start_date = last_date + timedelta(days=1)
        else:
            start_date = date.today() - timedelta(days=730)
        
        end_date = date.today()
        
        # Get data
        if last_date and last_date >= end_date - timedelta(days=1):
            logger.debug(f"{asset_id} is up to date")
            df = self._parquet.load_bars(asset_id)
        else:
            new_data = self._provider.fetch_daily_bars(
                asset_id,
                start=start_date,
                end=end_date
            )
            
            if new_data.empty:
                logger.debug(f"No new data for {asset_id}")
                df = self._parquet.load_bars(asset_id)
            else:
                self._parquet.upsert_bars(asset_id, new_data)
                df = self._parquet.load_bars(asset_id)
        
        if df is None or df.empty:
            logger.warning(f"No data available for {asset_id}")
            return False
        
        # Fetch fundamentals for equities
        fundamentals = None
        if asset.asset_type.has_fundamentals:
            try:
                fundamentals = self._provider.fetch_fundamentals(asset_id)
            except Exception as e:
                logger.debug(f"No fundamentals for {asset_id}: {e}")
        
        # Compute score
        score = self._scoring.compute_score(
            asset=asset,
            df=df,
            fundamentals=fundamentals,
            gating=gating
        )
        
        # PATCH: Apply quality/liquidity adjustments for US_EU
        if self._market_scope == "US_EU" and gating:
            raw_score = score.score_total
            
            # Recalculate zero_volume_ratio from data if needed (not stored in DB)
            zero_volume_ratio = 0.0
            if not df.empty:
                try:
                    from pipeline.quality_adjustments import compute_investability_metrics
                    investability = compute_investability_metrics(df)
                    zero_volume_ratio = investability.get("zero_volume_ratio", 0.0)
                except Exception as e:
                    logger.debug(f"Could not compute zero_volume_ratio for {asset_id}: {e}")
            
            # Build gating metrics dict
            # For US_EU, liquidity field contains ADV_USD (set in gating.py)
            gating_metrics = {
                "adv_usd": gating.liquidity,  # liquidity is now ADV_USD for US_EU
                "coverage": gating.coverage,
                "stale_ratio": gating.stale_ratio,
                "zero_volume_ratio": zero_volume_ratio,
                "data_confidence": gating.data_confidence
            }
            
            # Apply adjustments
            adjusted_score, debug_dict = apply_quality_liquidity_adjustments(
                raw_score_total=raw_score,
                gating_metrics=gating_metrics,
                market_scope=self._market_scope
            )
            
            # Update score with adjusted value
            score.score_total = adjusted_score
            
            # Update confidence to use gating's data_confidence (take minimum)
            score.confidence = min(score.confidence or 100, gating.data_confidence)
            
            # Merge debug info into breakdown JSON
            if score.breakdown:
                try:
                    # Get existing breakdown as dict
                    existing_json_str = score.breakdown.to_json()
                    existing_data = json.loads(existing_json_str)
                    
                    # Add quality adjustment fields to features/raw_values
                    if "features" not in existing_data:
                        existing_data["features"] = existing_data.get("raw_values", {})
                    if "raw_values" not in existing_data:
                        existing_data["raw_values"] = existing_data.get("features", {})
                    
                    # Merge debug info into features
                    existing_data["features"].update(debug_dict)
                    existing_data["raw_values"].update(debug_dict)
                    
                    # Reconstruct breakdown
                    from core.models import ScoreBreakdown
                    score.breakdown = ScoreBreakdown.from_json(json.dumps(existing_data))
                except Exception as e:
                    logger.warning(f"Failed to merge breakdown for {asset_id}: {e}")
                    # Fallback: at least update the score
            else:
                # Create minimal breakdown with debug info
                from core.models import ScoreBreakdown
                score.breakdown = ScoreBreakdown(
                    version="1.1",
                    features=debug_dict,
                    raw_values=debug_dict
                )
        
        # Update stores with scope
        self._store.upsert_score(score, market_scope=self._market_scope)
        
        # ═══════════════════════════════════════════════════════════════════
        # LONG-TERM SCORING (ADD-ON) - Only for US_EU when enabled
        # ═══════════════════════════════════════════════════════════════════
        if self._run_longterm and self._market_scope == "US_EU":
            try:
                # Build price_data dict
                price_data = {
                    "last_price": score.last_price,
                    "sma200": score.sma200,
                    "rsi": score.rsi,
                    "volatility_annual": score.vol_annual,
                    "vol_annual": score.vol_annual,
                    "max_drawdown": score.max_drawdown,
                    "zscore": score.zscore,
                }
                
                # Build fundamentals dict
                fund_dict = {}
                if fundamentals:
                    fund_dict = fundamentals.to_dict() if hasattr(fundamentals, 'to_dict') else dict(fundamentals)
                
                # Build gating_data dict
                gating_data = {}
                if gating:
                    gating_data = {
                        "adv_usd": gating.liquidity,
                        "liquidity": gating.liquidity,
                        "coverage": gating.coverage,
                        "stale_ratio": gating.stale_ratio,
                        "data_confidence": gating.data_confidence,
                    }
                
                # Compute long-term score
                lt_result = compute_longterm_score(
                    asset_id=asset_id,
                    price_data=price_data,
                    fundamentals=fund_dict,
                    gating_data=gating_data,
                    market_scope=self._market_scope
                )
                
                # Upsert lt_score
                if lt_result.lt_score is not None:
                    self._store.upsert_longterm_score(
                        asset_id=asset_id,
                        lt_score=lt_result.lt_score,
                        lt_confidence=lt_result.lt_confidence,
                        lt_breakdown=lt_result.breakdown_json(),
                        market_scope=self._market_scope
                    )
                    logger.debug(f"LT score for {asset_id}: {lt_result.lt_score} (caps: {lt_result.lt_caps_applied})")
                    
            except Exception as e:
                logger.warning(f"Failed to compute LT score for {asset_id}: {e}")
        
        # Update rotation state
        state = RotationState(
            asset_id=asset_id,
            last_refresh_at=datetime.now().isoformat(),
            priority_level=asset.tier,
            in_top50=False,
            refresh_count=1
        )
        self._store.upsert_rotation_state(state, market_scope=self._market_scope)
        
        logger.debug(f"Processed {asset_id}: score={score.score_total}")
        return True
    
    def _mark_rotation_error(self, asset_id: str, error: str):
        """Mark rotation error for an asset."""
        state = RotationState(
            asset_id=asset_id,
            last_refresh_at=datetime.now().isoformat(),
            last_error=error
        )
        self._store.upsert_rotation_state(state, market_scope=self._market_scope)
    
    def _update_top50_flags(self) -> None:
        """Update in_top50 flags in rotation_state."""
        try:
            top50_ids = set(self._get_top50_asset_ids())
            logger.debug(f"Top 50 updated: {len(top50_ids)} assets")
        except Exception as e:
            logger.warning(f"Failed to update Top 50 flags: {e}")
    
    def refresh_single(self, asset_id: str) -> Optional[Score]:
        """Refresh a single asset immediately."""
        try:
            success = self._process_asset(asset_id)
            if success:
                return self._store.get_score(asset_id)
            return None
        except Exception as e:
            logger.error(f"Failed to refresh {asset_id}: {e}")
            return None
