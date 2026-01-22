"""
MarketGPS v11.0 - Gating Pipeline (SCOPE-AWARE)
Data quality assessment and eligibility filtering.
Supports market scopes: US_EU, AFRICA
"""
from datetime import date, timedelta
from typing import Optional, Tuple, Literal
import pandas as pd
import numpy as np

from core.config import get_config, get_logger
from core.models import Asset, AssetType, GatingStatus
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from providers import get_provider
from pipeline.quality_adjustments import (
    compute_investability_metrics,
    compute_data_confidence
)

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]


class GatingJob:
    """
    Gating job for data quality assessment.
    
    Evaluates each asset for:
    - Data coverage (% of expected trading days with data)
    - Liquidity (Average Dollar Volume)
    - Data staleness (% of days with unchanged close)
    - Minimum price threshold
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        parquet_store: Optional[ParquetStore] = None,
        market_scope: MarketScope = "US_EU"
    ):
        """
        Initialize Gating job.
        
        Args:
            store: SQLite store instance
            parquet_store: Parquet store instance
            market_scope: Market scope to operate on
        """
        self._config = get_config()
        self._store = store or SQLiteStore()
        self._parquet = parquet_store or ParquetStore(market_scope=market_scope)
        self._provider = get_provider("auto")
        self._market_scope = market_scope
    
    def run(self, batch_size: int = 50) -> dict:
        """
        Run the gating job for all active assets in this scope.
        
        Args:
            batch_size: Number of assets to process in each batch
            
        Returns:
            Dict with job results
        """
        logger.info(f"Starting Gating job [{self._market_scope}]")
        
        results = {
            "processed": 0,
            "eligible": 0,
            "ineligible": 0,
            "errors": 0
        }
        
        try:
            # Get all active assets for this scope
            assets = self._store.get_active_assets(market_scope=self._market_scope)
            logger.info(f"[{self._market_scope}] Processing {len(assets)} active assets")
            
            # Process in batches
            for i in range(0, len(assets), batch_size):
                batch = assets[i:i + batch_size]
                
                for asset in batch:
                    try:
                        status = self._evaluate_asset(asset)
                        self._store.upsert_gating(status, market_scope=self._market_scope)
                        
                        results["processed"] += 1
                        if status.eligible:
                            results["eligible"] += 1
                        else:
                            results["ineligible"] += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to gate {asset.asset_id}: {e}")
                        results["errors"] += 1
                
                logger.info(f"[{self._market_scope}] Processed batch {i // batch_size + 1}, total: {results['processed']}")
            
            logger.info(f"Gating job complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Gating job failed: {e}")
            results["errors"] += 1
            return results
    
    def _evaluate_asset(self, asset: Asset) -> GatingStatus:
        """
        Evaluate a single asset for eligibility.
        
        Args:
            asset: Asset to evaluate
            
        Returns:
            GatingStatus with evaluation results
        """
        lookback_days = self._config.pipeline.gating_lookback_days
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        # First, check if we have cached data in Parquet
        df = None
        use_cached = False
        
        try:
            cached_df = self._parquet.load_bars(asset.asset_id)
            if cached_df is not None and len(cached_df) > 50:
                # Check if data is fresh (within last 5 trading days)
                last_date = self._parquet.get_last_date(asset.asset_id)
                if last_date and (end_date - last_date).days <= 7:
                    logger.debug(f"Using cached data for {asset.asset_id} (last: {last_date})")
                    df = cached_df
                    use_cached = True
        except Exception:
            pass  # No cached data available
        
        # If no valid cache, fetch from provider
        if df is None or df.empty:
            df = self._provider.fetch_daily_bars(
                asset.asset_id,
                start=start_date,
                end=end_date
            )
            
            # Store the data for later use
            if not df.empty:
                self._parquet.upsert_bars(asset.asset_id, df)
        
        # For US_EU: use enhanced investability metrics
        if self._market_scope == "US_EU" and not df.empty:
            # Compute enhanced metrics
            investability = compute_investability_metrics(df, expected_days=lookback_days)
            adv_usd = investability["adv_usd"]
            zero_volume_ratio = investability["zero_volume_ratio"]
            stale_ratio_60 = investability["stale_ratio"]
            coverage = investability["coverage"]
            
            # Use ADV_USD as liquidity metric
            liquidity = adv_usd
            
            # Use stale_ratio_60 (60-day window) instead of full period
            stale_ratio = stale_ratio_60
            
            # Calculate enhanced data confidence
            confidence = compute_data_confidence(
                coverage=coverage,
                adv_usd=adv_usd,
                stale_ratio=stale_ratio_60,
                zero_volume_ratio=zero_volume_ratio
            )
        else:
            # Fallback to original metrics for AFRICA or empty data
            coverage = self._calculate_coverage(df, start_date, end_date)
            liquidity = self._calculate_liquidity(df)
            stale_ratio = self._calculate_stale_ratio(df)
            
            # Calculate data confidence (original method)
            confidence = self._calculate_confidence(
                coverage=coverage,
                liquidity=liquidity,
                stale_ratio=stale_ratio
            )
        
        price_min = self._get_min_price(df)
        last_bar_date = self._get_last_bar_date(df)
        
        # Determine eligibility
        eligible, reason = self._check_eligibility(
            asset=asset,
            coverage=coverage,
            liquidity=liquidity,
            stale_ratio=stale_ratio,
            price_min=price_min
        )
        
        # If no data, mark as ineligible
        if df.empty:
            eligible = False
            reason = "NO_DATA"
            confidence = 5
        
        return GatingStatus(
            asset_id=asset.asset_id,
            coverage=coverage,
            liquidity=liquidity,
            price_min=price_min,
            stale_ratio=stale_ratio,
            eligible=eligible,
            reason=reason,
            data_confidence=confidence,
            last_bar_date=last_bar_date
        )
    
    def _calculate_coverage(
        self,
        df: pd.DataFrame,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate data coverage as percentage of expected trading days.
        
        Assumes ~252 trading days per year (US market).
        """
        if df.empty:
            return 0.0
        
        total_days = (end_date - start_date).days
        expected_trading_days = int(total_days * 252 / 365)  # Approximate
        
        actual_days = len(df)
        
        if expected_trading_days <= 0:
            return 0.0
        
        coverage = min(1.0, actual_days / expected_trading_days)
        return round(coverage, 4)
    
    def _calculate_liquidity(self, df: pd.DataFrame, window: int = 60) -> float:
        """
        Calculate Average Dollar Volume (ADV) over the specified window.
        """
        if df.empty or "Close" not in df.columns or "Volume" not in df.columns:
            return 0.0
        
        try:
            # Use most recent 'window' days
            recent = df.tail(window)
            
            if recent.empty:
                return 0.0
            
            # Calculate dollar volume
            dollar_volume = recent["Close"] * recent["Volume"]
            
            # Average, handling NaN
            adv = dollar_volume.mean()
            
            return float(adv) if pd.notna(adv) else 0.0
            
        except Exception as e:
            logger.warning(f"Liquidity calculation failed: {e}")
            return 0.0
    
    def _calculate_stale_ratio(self, df: pd.DataFrame) -> float:
        """
        Calculate percentage of days where close price didn't change.
        High stale ratio indicates potential data issues.
        """
        if df.empty or "Close" not in df.columns or len(df) < 2:
            return 0.0
        
        try:
            close = df["Close"].dropna()
            
            if len(close) < 2:
                return 0.0
            
            # Count days where close equals previous close
            unchanged = (close == close.shift(1)).sum()
            
            return round(unchanged / (len(close) - 1), 4)
            
        except Exception:
            return 0.0
    
    def _get_min_price(self, df: pd.DataFrame) -> Optional[float]:
        """Get minimum price from the data."""
        if df.empty or "Low" not in df.columns:
            return None
        
        try:
            min_price = df["Low"].min()
            return float(min_price) if pd.notna(min_price) else None
        except Exception:
            return None
    
    def _get_last_bar_date(self, df: pd.DataFrame) -> Optional[str]:
        """Get the last bar date as ISO string."""
        if df.empty:
            return None
        
        try:
            last_date = df.index.max()
            if pd.notna(last_date):
                return last_date.strftime("%Y-%m-%d")
            return None
        except Exception:
            return None
    
    def _check_eligibility(
        self,
        asset: Asset,
        coverage: float,
        liquidity: float,
        stale_ratio: float,
        price_min: Optional[float]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if asset meets eligibility criteria.
        
        Returns:
            Tuple of (eligible, reason_if_not_eligible)
        """
        config = self._config.pipeline
        
        # Check coverage
        # For US_EU, use 0.60 (more permissive to allow patch to apply penalties)
        # For AFRICA, use config threshold
        coverage_min = 0.60 if self._market_scope == "US_EU" else config.gating_coverage_min
        if coverage < coverage_min:
            return False, f"Coverage {coverage:.1%} < {coverage_min:.0%}"
        
        # Check liquidity based on asset type
        # For US_EU, use 250K minimum (consistent with quality patch MIN_ADV_HARD)
        # For AFRICA, use config thresholds
        if self._market_scope == "US_EU":
            adv_min = 250_000  # MIN_ADV_HARD from quality patch
        elif asset.asset_type == AssetType.ETF:
            adv_min = config.gating_adv_min_etf
        else:
            adv_min = config.gating_adv_min_equity
        
        if liquidity < adv_min:
            return False, f"ADV ${liquidity:,.0f} < ${adv_min:,.0f}"
        
        # Check stale ratio (too much stale data is suspicious)
        if stale_ratio > 0.20:  # More than 20% stale days
            return False, f"Stale ratio {stale_ratio:.1%} > 20%"
        
        # Check minimum price (avoid penny stocks)
        min_price_threshold = 1.0  # $1 minimum
        if price_min is not None and price_min < min_price_threshold:
            return False, f"Min price ${price_min:.2f} < ${min_price_threshold}"
        
        return True, None
    
    def _calculate_confidence(
        self,
        coverage: float,
        liquidity: float,
        stale_ratio: float
    ) -> int:
        """
        Calculate data confidence score (0-100).
        
        Factors:
        - Coverage (weight: 40%)
        - Liquidity (weight: 30%)
        - Data freshness/staleness (weight: 30%)
        """
        # Coverage score (0-100)
        coverage_score = min(100, coverage * 100)
        
        # Liquidity score (0-100, logarithmic scale)
        # $10M+ ADV = 100, $100K ADV = ~50
        if liquidity > 0:
            liq_log = np.log10(liquidity / 100_000)  # Normalize to $100K
            liquidity_score = min(100, max(0, 50 + liq_log * 25))
        else:
            liquidity_score = 0
        
        # Staleness score (0-100, inverted)
        staleness_score = max(0, (1 - stale_ratio * 5) * 100)
        
        # Weighted combination
        confidence = (
            coverage_score * 0.40 +
            liquidity_score * 0.30 +
            staleness_score * 0.30
        )
        
        return int(round(min(100, max(0, confidence))))
    
    def gate_single(self, asset_id: str) -> Optional[GatingStatus]:
        """
        Run gating for a single asset.
        
        Args:
            asset_id: Asset to evaluate
            
        Returns:
            GatingStatus or None if asset not found
        """
        asset = self._store.get_asset(asset_id)
        if not asset:
            logger.warning(f"Asset not found: {asset_id}")
            return None
        
        try:
            status = self._evaluate_asset(asset)
            self._store.upsert_gating(status, market_scope=self._market_scope)
            return status
        except Exception as e:
            logger.error(f"Failed to gate {asset_id}: {e}")
            return None
