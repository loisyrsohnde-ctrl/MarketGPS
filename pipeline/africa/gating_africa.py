"""
MarketGPS v14.0 - Africa Gating Pipeline
Data quality assessment and eligibility filtering for African markets.

Key differences from US_EU gating:
- More tolerant stale_ratio (35% vs 20%)
- Lower minimum coverage (70% vs 80%)
- Exchange-specific liquidity thresholds
- FX risk calculation
- Liquidity risk calculation
- Longer lookback for illiquid markets

Rules:
- coverage >= 0.70 (70% of expected trading days)
- stale_ratio <= 0.35 (35% unchanged days allowed)
- liquidity >= exchange_min_liquidity_usd
- at least 260 bars (1 year) for scoring, else low_confidence mode
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, Tuple, Literal
import pandas as pd
import numpy as np

from core.config import get_config, get_logger
from core.models import Asset, GatingStatus
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.africa.exchanges_catalog import (
    AFRICA_EXCHANGES,
    CURRENCY_INFO,
    get_exchange_info,
    get_min_liquidity_for_exchange,
    get_stale_threshold_for_exchange,
    get_currency_volatility,
)
from pipeline.africa.data_fetcher_africa import AfricaDataFetcher

logger = get_logger(__name__)

MarketScope = Literal["AFRICA"]


# ═══════════════════════════════════════════════════════════════════════════
# AFRICA GATING THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════

AFRICA_GATING_CONFIG = {
    "coverage_min": 0.70,           # 70% minimum coverage
    "stale_ratio_max": 0.35,        # 35% stale days allowed
    "min_bars_standard": 260,       # 1 year for standard scoring
    "min_bars_low_confidence": 60,  # 3 months for low confidence
    "min_price": 0.01,              # Very low threshold for emerging markets
    "fx_risk_threshold": 0.50,      # High FX volatility threshold
    "liquidity_risk_threshold": 0.40,  # Low liquidity threshold
}


# ═══════════════════════════════════════════════════════════════════════════
# GATING JOB CLASS
# ═══════════════════════════════════════════════════════════════════════════

class GatingAfricaJob:
    """
    Gating job specialized for African markets.
    
    Features:
    - Exchange-specific thresholds
    - FX risk calculation
    - Liquidity risk calculation
    - More tolerant for illiquid markets
    - Staging table support for atomic publish
    """
    
    def __init__(
        self,
        store: Optional[SQLiteStore] = None,
        parquet_store: Optional[ParquetStore] = None
    ):
        """
        Initialize Africa gating job.
        
        Args:
            store: SQLite store instance
            parquet_store: Parquet store for AFRICA scope
        """
        self._config = get_config()
        self._store = store or SQLiteStore()
        self._parquet = parquet_store or ParquetStore(market_scope="AFRICA")
        self._data_fetcher = AfricaDataFetcher(
            parquet_store=self._parquet,
            sqlite_store=self._store
        )
    
    def run(
        self,
        batch_size: int = 50,
        fetch_data: bool = True
    ) -> Dict[str, int]:
        """
        Run gating for all active AFRICA assets.
        
        Args:
            batch_size: Assets per batch
            fetch_data: Whether to fetch new data before gating
            
        Returns:
            Dict with processing stats
        """
        logger.info(f"[AFRICA] Starting gating job")
        
        results = {
            "processed": 0,
            "eligible": 0,
            "ineligible": 0,
            "errors": 0,
            "low_confidence": 0
        }
        
        try:
            # Get all active AFRICA assets
            assets = self._store.get_active_assets(market_scope="AFRICA")
            logger.info(f"[AFRICA] Gating {len(assets)} assets")
            
            # Process in batches
            for i in range(0, len(assets), batch_size):
                batch = assets[i:i + batch_size]
                
                for asset in batch:
                    try:
                        status = self._evaluate_asset(asset, fetch_data)
                        self._store.upsert_gating(status, market_scope="AFRICA")
                        
                        results["processed"] += 1
                        if status.eligible:
                            results["eligible"] += 1
                        else:
                            results["ineligible"] += 1
                        
                        if status.data_confidence < 50:
                            results["low_confidence"] += 1
                            
                    except Exception as e:
                        logger.warning(f"[AFRICA] Gating failed for {asset.asset_id}: {e}")
                        results["errors"] += 1
                
                logger.info(
                    f"[AFRICA] Batch {i // batch_size + 1}: "
                    f"{results['processed']} processed, {results['eligible']} eligible"
                )
            
            logger.info(f"[AFRICA] Gating complete: {results}")
            return results
            
        except Exception as e:
            logger.error(f"[AFRICA] Gating job failed: {e}")
            results["errors"] += 1
            return results
    
    def _evaluate_asset(
        self,
        asset: Asset,
        fetch_data: bool = True
    ) -> GatingStatus:
        """
        Evaluate a single asset for eligibility.
        
        Args:
            asset: Asset to evaluate
            fetch_data: Whether to fetch new data
            
        Returns:
            GatingStatus with all metrics
        """
        lookback_days = self._config.pipeline.gating_lookback_days or 504
        
        # Get or fetch data
        df = None
        if fetch_data:
            df = self._data_fetcher.fetch_bars(asset.asset_id, days=lookback_days)
        
        if df is None or df.empty:
            df = self._parquet.load_bars(asset.asset_id)
        
        # Get exchange info
        exchange_code = getattr(asset, 'exchange', None) or 'JSE'
        exchange_info = get_exchange_info(exchange_code)
        currency = getattr(asset, 'currency', None) or 'ZAR'
        
        # Calculate metrics
        coverage = compute_coverage_africa(df, lookback_days, exchange_code)
        stale_ratio = compute_stale_ratio_africa(df, exchange_code)
        liquidity = compute_liquidity_africa(df)
        price_min = self._get_min_price(df)
        last_bar_date = self._get_last_bar_date(df)
        
        # Calculate Africa-specific risks
        fx_risk = compute_fx_risk(currency)
        liquidity_risk = compute_liquidity_risk(df, exchange_code, liquidity)
        
        # Determine eligibility with Africa-specific rules
        eligible, reason = self._check_eligibility_africa(
            asset=asset,
            df=df,
            coverage=coverage,
            stale_ratio=stale_ratio,
            liquidity=liquidity,
            price_min=price_min,
            exchange_code=exchange_code
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence_africa(
            df=df,
            coverage=coverage,
            liquidity=liquidity,
            stale_ratio=stale_ratio,
            fx_risk=fx_risk,
            liquidity_risk=liquidity_risk,
            exchange_code=exchange_code
        )
        
        return GatingStatus(
            asset_id=asset.asset_id,
            coverage=coverage,
            liquidity=liquidity,
            price_min=price_min,
            stale_ratio=stale_ratio,
            eligible=eligible,
            reason=reason,
            data_confidence=confidence,
            last_bar_date=last_bar_date,
            fx_risk=fx_risk,
            liquidity_risk=liquidity_risk
        )
    
    def _get_min_price(self, df: pd.DataFrame) -> Optional[float]:
        """Get minimum price from data."""
        if df is None or df.empty:
            return None
        
        col = "low" if "low" in df.columns else "close"
        if col not in df.columns:
            return None
        
        try:
            min_price = df[col].min()
            return float(min_price) if pd.notna(min_price) else None
        except Exception:
            return None
    
    def _get_last_bar_date(self, df: pd.DataFrame) -> Optional[str]:
        """Get last bar date as ISO string."""
        if df is None or df.empty:
            return None
        
        try:
            last_date = df.index.max()
            if pd.notna(last_date):
                return last_date.strftime("%Y-%m-%d")
            return None
        except Exception:
            return None
    
    def _check_eligibility_africa(
        self,
        asset: Asset,
        df: pd.DataFrame,
        coverage: float,
        stale_ratio: float,
        liquidity: float,
        price_min: Optional[float],
        exchange_code: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check eligibility with Africa-specific rules.
        
        More tolerant than US_EU rules:
        - Lower coverage minimum (70%)
        - Higher stale ratio allowed (35%)
        - Exchange-specific liquidity thresholds
        """
        config = AFRICA_GATING_CONFIG
        
        # Get exchange-specific liquidity minimum
        min_liquidity = get_min_liquidity_for_exchange(exchange_code)
        
        # Check coverage
        if coverage < config["coverage_min"]:
            return False, f"Coverage {coverage:.1%} < {config['coverage_min']:.0%}"
        
        # Check stale ratio
        if stale_ratio > config["stale_ratio_max"]:
            return False, f"Stale ratio {stale_ratio:.1%} > {config['stale_ratio_max']:.0%}"
        
        # Check liquidity (more lenient for Africa)
        if liquidity < min_liquidity:
            return False, f"ADV ${liquidity:,.0f} < ${min_liquidity:,.0f}"
        
        # Check minimum bars
        bar_count = len(df) if df is not None else 0
        if bar_count < config["min_bars_low_confidence"]:
            return False, f"Only {bar_count} bars (need {config['min_bars_low_confidence']}+)"
        
        # Check minimum price
        if price_min is not None and price_min < config["min_price"]:
            return False, f"Min price ${price_min:.4f} < ${config['min_price']}"
        
        return True, None
    
    def _calculate_confidence_africa(
        self,
        df: pd.DataFrame,
        coverage: float,
        liquidity: float,
        stale_ratio: float,
        fx_risk: float,
        liquidity_risk: float,
        exchange_code: str
    ) -> int:
        """
        Calculate data confidence with Africa-specific factors.
        
        Components:
        - Coverage: 30%
        - Liquidity: 20%
        - Staleness: 20%
        - FX stability: 15%
        - Market tier: 15%
        """
        config = AFRICA_GATING_CONFIG
        
        # Coverage score (0-100)
        coverage_score = min(100, (coverage / config["coverage_min"]) * 100)
        
        # Liquidity score
        min_liq = get_min_liquidity_for_exchange(exchange_code)
        if liquidity > 0 and min_liq > 0:
            liq_ratio = min(3.0, liquidity / min_liq)  # Cap at 3x minimum
            liquidity_score = liq_ratio * 33.3  # 100 at 3x
        else:
            liquidity_score = 0
        
        # Staleness score (inverted)
        staleness_score = max(0, (1 - stale_ratio / config["stale_ratio_max"]) * 100)
        
        # FX stability score (inverted)
        fx_score = (1 - fx_risk) * 100
        
        # Market tier score
        exchange_info = get_exchange_info(exchange_code)
        tier = exchange_info.tier if exchange_info else 3
        tier_scores = {1: 100, 2: 70, 3: 45}
        tier_score = tier_scores.get(tier, 50)
        
        # Weighted combination
        confidence = (
            coverage_score * 0.30 +
            liquidity_score * 0.20 +
            staleness_score * 0.20 +
            fx_score * 0.15 +
            tier_score * 0.15
        )
        
        # Minimum bar penalty
        bar_count = len(df) if df is not None else 0
        if bar_count < config["min_bars_standard"]:
            # Reduce confidence for insufficient history
            history_factor = bar_count / config["min_bars_standard"]
            confidence *= max(0.5, history_factor)
        
        return int(round(min(100, max(0, confidence))))
    
    def gate_single(self, asset_id: str) -> Optional[GatingStatus]:
        """
        Run gating for a single asset.
        
        Args:
            asset_id: Asset to evaluate
            
        Returns:
            GatingStatus or None
        """
        asset = self._store.get_asset(asset_id)
        if not asset:
            logger.warning(f"[AFRICA] Asset not found: {asset_id}")
            return None
        
        try:
            status = self._evaluate_asset(asset)
            self._store.upsert_gating(status, market_scope="AFRICA")
            return status
        except Exception as e:
            logger.error(f"[AFRICA] Gating failed for {asset_id}: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════
# METRIC CALCULATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def compute_coverage_africa(
    df: pd.DataFrame,
    expected_days: int = 504,
    exchange_code: str = "JSE"
) -> float:
    """
    Compute data coverage for African market.
    
    Args:
        df: DataFrame with OHLCV data
        expected_days: Total calendar days in lookback
        exchange_code: Exchange code for trading day calculation
        
    Returns:
        Coverage ratio (0.0 - 1.0)
    """
    if df is None or df.empty:
        return 0.0
    
    try:
        # Get exchange info for trading days
        exchange_info = get_exchange_info(exchange_code)
        
        # Estimate expected trading days
        # Most African exchanges trade 5 days/week
        # Account for ~10 holidays/year
        trading_days_per_year = 250  # Conservative estimate
        expected_trading_days = int(expected_days * trading_days_per_year / 365)
        
        # EGX has different schedule (Sun-Thu)
        if exchange_code == "EGX":
            expected_trading_days = int(expected_days * 250 / 365)
        
        actual_days = len(df)
        
        if expected_trading_days <= 0:
            return 0.0
        
        coverage = min(1.0, actual_days / expected_trading_days)
        return round(coverage, 4)
        
    except Exception as e:
        logger.debug(f"Coverage calculation failed: {e}")
        return 0.0


def compute_stale_ratio_africa(
    df: pd.DataFrame,
    exchange_code: str = "JSE"
) -> float:
    """
    Compute stale data ratio (days with unchanged close).
    
    For African markets, some staleness is expected due to
    lower trading activity.
    
    Args:
        df: DataFrame with OHLCV data
        exchange_code: Exchange code
        
    Returns:
        Stale ratio (0.0 - 1.0)
    """
    if df is None or df.empty or len(df) < 2:
        return 0.0
    
    try:
        close_col = "close" if "close" in df.columns else "Close"
        if close_col not in df.columns:
            return 0.0
        
        close = df[close_col].dropna()
        
        if len(close) < 2:
            return 0.0
        
        # Count unchanged days
        unchanged = (close == close.shift(1)).sum()
        
        return round(unchanged / (len(close) - 1), 4)
        
    except Exception:
        return 0.0


def compute_liquidity_africa(
    df: pd.DataFrame,
    window: int = 60
) -> float:
    """
    Compute Average Dollar Volume for African market.
    
    Uses median instead of mean to handle outliers better
    in illiquid markets.
    
    Args:
        df: DataFrame with OHLCV data
        window: Days for averaging
        
    Returns:
        ADV in base currency (approximate USD)
    """
    if df is None or df.empty:
        return 0.0
    
    try:
        # Normalize column names
        close_col = "close" if "close" in df.columns else "Close"
        vol_col = "volume" if "volume" in df.columns else "Volume"
        
        if close_col not in df.columns or vol_col not in df.columns:
            return 0.0
        
        recent = df.tail(window)
        
        if recent.empty:
            return 0.0
        
        # Dollar volume
        dollar_volume = recent[close_col] * recent[vol_col]
        
        # Use median for illiquid markets (more robust)
        adv = dollar_volume.median()
        
        # Also check mean to ensure we're not missing high volume days
        adv_mean = dollar_volume.mean()
        
        # Use the higher of median and 50% of mean
        adv = max(adv, adv_mean * 0.5)
        
        return float(adv) if pd.notna(adv) else 0.0
        
    except Exception as e:
        logger.debug(f"Liquidity calculation failed: {e}")
        return 0.0


def compute_fx_risk(currency: str) -> float:
    """
    Compute FX risk score based on currency volatility.
    
    Higher score = higher risk (worse).
    
    Args:
        currency: Currency code (e.g., "ZAR", "NGN")
        
    Returns:
        FX risk score (0.0 - 1.0)
    """
    # Get currency volatility from catalog
    volatility = get_currency_volatility(currency)
    
    # Scale to 0-1 range (already in that range in catalog)
    return min(1.0, max(0.0, volatility))


def compute_liquidity_risk(
    df: pd.DataFrame,
    exchange_code: str,
    adv: float
) -> float:
    """
    Compute liquidity risk score.
    
    Factors:
    - ADV relative to exchange minimum
    - Zero-volume days ratio
    - Market tier
    
    Higher score = higher risk (worse).
    
    Args:
        df: DataFrame with OHLCV data
        exchange_code: Exchange code
        adv: Pre-computed ADV
        
    Returns:
        Liquidity risk score (0.0 - 1.0)
    """
    risk_score = 0.0
    
    # ADV component (40% weight)
    min_liquidity = get_min_liquidity_for_exchange(exchange_code)
    if adv > 0 and min_liquidity > 0:
        adv_ratio = adv / min_liquidity
        if adv_ratio >= 3.0:
            adv_risk = 0.0
        elif adv_ratio >= 1.0:
            adv_risk = 0.3 * (3.0 - adv_ratio) / 2.0
        else:
            adv_risk = 0.3 + 0.7 * (1.0 - adv_ratio)
    else:
        adv_risk = 1.0
    
    risk_score += adv_risk * 0.40
    
    # Zero-volume days (30% weight)
    if df is not None and not df.empty:
        vol_col = "volume" if "volume" in df.columns else "Volume"
        if vol_col in df.columns:
            zero_vol_ratio = (df[vol_col] == 0).sum() / len(df)
            risk_score += zero_vol_ratio * 0.30
    else:
        risk_score += 0.30  # Assume worst if no data
    
    # Market tier (30% weight)
    exchange_info = get_exchange_info(exchange_code)
    tier = exchange_info.tier if exchange_info else 3
    tier_risk = {1: 0.1, 2: 0.3, 3: 0.5}
    risk_score += tier_risk.get(tier, 0.5) * 0.30
    
    return round(min(1.0, max(0.0, risk_score)), 4)
