"""
MarketGPS v14.0 - Africa Data Fetcher
Reliable OHLCV data retrieval for African markets.

Features:
- EODHD priority with yfinance fallback
- Data normalization (column names, types)
- Date validation and deduplication
- Gap detection and handling
- Rate limiting and retry logic
- Provider status logging
"""

import time
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Literal, Tuple
import pandas as pd
import numpy as np

from core.config import get_config, get_logger
from storage.parquet_store import ParquetStore
from storage.sqlite_store import SQLiteStore
from pipeline.africa.exchanges_catalog import (
    AFRICA_EXCHANGES,
    get_exchange_info,
    get_stale_threshold_for_exchange,
)

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA FETCHER CLASS
# ═══════════════════════════════════════════════════════════════════════════

class AfricaDataFetcher:
    """
    Data fetcher for African markets with provider fallback.
    
    Features:
    - Primary: EODHD API
    - Fallback: yfinance (when ticker mapping available)
    - Data normalization
    - Quality validation
    - Parquet storage
    """
    
    # Standard column names
    STANDARD_COLUMNS = ["open", "high", "low", "close", "volume"]
    
    def __init__(
        self,
        parquet_store: Optional[ParquetStore] = None,
        sqlite_store: Optional[SQLiteStore] = None
    ):
        """
        Initialize data fetcher.
        
        Args:
            parquet_store: ParquetStore for saving bars
            sqlite_store: SQLiteStore for logging
        """
        self._config = get_config()
        self._parquet = parquet_store or ParquetStore(market_scope="AFRICA")
        self._store = sqlite_store or SQLiteStore()
        
        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = 0.2  # 200ms between requests
    
    def fetch_bars(
        self,
        asset_id: str,
        days: int = 756,  # 3 years
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch daily OHLCV bars for an asset.
        
        Args:
            asset_id: Asset ID (e.g., "NPN.JSE")
            days: Number of days to fetch
            force_refresh: If True, ignore cached data
            
        Returns:
            DataFrame with OHLCV data, or None if fetch failed
        """
        # Check cache first
        if not force_refresh:
            cached = self._parquet.load_bars(asset_id)
            if cached is not None and len(cached) > 50:
                last_date = self._parquet.get_last_date(asset_id)
                if last_date and (date.today() - last_date).days <= 3:
                    logger.debug(f"[AFRICA] Using cached data for {asset_id}")
                    return cached
        
        # Fetch from providers
        df = self._fetch_from_providers(asset_id, days)
        
        if df is not None and not df.empty:
            # Normalize and validate
            df = self._normalize_dataframe(df)
            df = self._validate_data(df, asset_id)
            
            if df is not None and not df.empty:
                # Save to parquet
                self._parquet.upsert_bars(asset_id, df)
                logger.info(f"[AFRICA] Fetched {len(df)} bars for {asset_id}")
                return df
        
        # Return cached if fresh fetch failed
        return self._parquet.load_bars(asset_id)
    
    def fetch_batch(
        self,
        asset_ids: List[str],
        days: int = 756,
        delay_ms: int = 200
    ) -> Dict[str, int]:
        """
        Fetch data for multiple assets.
        
        Args:
            asset_ids: List of asset IDs
            days: Days of history
            delay_ms: Delay between requests in milliseconds
            
        Returns:
            Dict with success/failure counts
        """
        results = {"success": 0, "failed": 0, "cached": 0}
        
        for asset_id in asset_ids:
            try:
                df = self.fetch_bars(asset_id, days)
                
                if df is not None and len(df) >= 50:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                logger.warning(f"Failed to fetch {asset_id}: {e}")
                results["failed"] += 1
            
            # Rate limiting
            time.sleep(delay_ms / 1000)
        
        logger.info(f"[AFRICA] Batch fetch: {results}")
        return results
    
    def _fetch_from_providers(
        self,
        asset_id: str,
        days: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch from providers with fallback logic.
        
        Args:
            asset_id: Asset ID
            days: Days of history
            
        Returns:
            DataFrame or None
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Rate limiting
        self._wait_for_rate_limit()
        
        # Try EODHD first
        df = self._fetch_eodhd(asset_id, start_date, end_date)
        
        if df is not None and len(df) >= 20:
            self._log_provider_success("EODHD", asset_id)
            return df
        
        # Try yfinance fallback
        df = self._fetch_yfinance(asset_id, start_date, end_date)
        
        if df is not None and len(df) >= 20:
            self._log_provider_success("yfinance", asset_id)
            return df
        
        self._log_provider_failure(asset_id)
        return None
    
    def _fetch_eodhd(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Fetch from EODHD API.
        
        Args:
            asset_id: Asset ID (SYMBOL.EXCHANGE format)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame or None
        """
        try:
            from providers.eodhd import EODHDProvider
            
            provider = EODHDProvider()
            if not provider.is_configured:
                logger.debug("EODHD not configured, skipping")
                return None
            
            df = provider.fetch_daily_bars(asset_id, start=start_date, end=end_date)
            return df if df is not None and not df.empty else None
            
        except Exception as e:
            logger.debug(f"EODHD fetch failed for {asset_id}: {e}")
            return None
    
    def _fetch_yfinance(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        Fetch from yfinance (fallback).
        
        Note: yfinance ticker format differs from EODHD.
        Examples:
        - "NPN.JSE" → "NPN.JO" (yfinance uses .JO for JSE)
        - "DANGCEM.NGX" → "DANGCEM.LG" (yfinance uses .LG for Nigeria)
        
        Args:
            asset_id: Asset ID
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame or None
        """
        try:
            # Map EODHD format to yfinance format
            yf_ticker = self._map_to_yfinance_ticker(asset_id)
            if not yf_ticker:
                return None
            
            from providers.yfinance_provider import YFinanceProvider
            
            provider = YFinanceProvider()
            df = provider.fetch_daily_bars(yf_ticker, start=start_date, end=end_date)
            return df if df is not None and not df.empty else None
            
        except Exception as e:
            logger.debug(f"yfinance fetch failed for {asset_id}: {e}")
            return None
    
    def _map_to_yfinance_ticker(self, asset_id: str) -> Optional[str]:
        """
        Map EODHD asset_id to yfinance ticker format.
        
        Args:
            asset_id: EODHD format (SYMBOL.EXCHANGE)
            
        Returns:
            yfinance ticker or None if unmappable
        """
        # EODHD to yfinance exchange suffixes
        EXCHANGE_MAP = {
            "JSE": ".JO",      # Johannesburg
            "NG": ".LG",       # Lagos/Nigeria
            "CA": ".CA",       # Cairo
            "NSE": ".NR",      # Nairobi
            "BRVM": None,      # No yfinance coverage
            "BVMAC": None,     # No yfinance coverage
            "GH": None,        # Limited coverage
        }
        
        try:
            parts = asset_id.rsplit(".", 1)
            if len(parts) != 2:
                return None
            
            symbol, exchange = parts
            suffix = EXCHANGE_MAP.get(exchange)
            
            if suffix is None:
                return None
            
            return f"{symbol}{suffix}"
            
        except Exception:
            return None
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame columns and types.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower()
        
        # Rename common variants
        column_map = {
            "adj close": "adj_close",
            "adjusted_close": "adj_close",
            "adj_close": "adj_close",
        }
        df = df.rename(columns=column_map)
        
        # Ensure required columns exist
        for col in self.STANDARD_COLUMNS:
            if col not in df.columns:
                logger.warning(f"Missing column: {col}")
        
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
            else:
                df.index = pd.to_datetime(df.index)
        
        # Remove timezone
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Sort by date
        df = df.sort_index()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep="last")]
        
        # Convert numeric columns
        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        return df
    
    def _validate_data(
        self,
        df: pd.DataFrame,
        asset_id: str
    ) -> Optional[pd.DataFrame]:
        """
        Validate data quality.
        
        Checks:
        - Monotonic dates
        - No future dates
        - Required columns present
        - Non-negative prices
        - Non-negative volume
        
        Args:
            df: DataFrame to validate
            asset_id: For logging
            
        Returns:
            Validated DataFrame or None if invalid
        """
        if df.empty:
            return None
        
        df = df.copy()
        
        # Check required columns
        required = ["close"]
        for col in required:
            if col not in df.columns:
                logger.warning(f"[AFRICA] {asset_id}: Missing required column '{col}'")
                return None
        
        # Remove future dates
        today = pd.Timestamp.now().normalize()
        future_mask = df.index > today
        if future_mask.any():
            logger.warning(f"[AFRICA] {asset_id}: Removing {future_mask.sum()} future dates")
            df = df[~future_mask]
        
        # Ensure monotonic dates
        if not df.index.is_monotonic_increasing:
            df = df.sort_index()
        
        # Remove rows with all NaN OHLC
        ohlc_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]
        if ohlc_cols:
            all_nan_mask = df[ohlc_cols].isna().all(axis=1)
            if all_nan_mask.any():
                df = df[~all_nan_mask]
        
        # Remove negative prices
        for col in ["open", "high", "low", "close"]:
            if col in df.columns:
                neg_mask = df[col] < 0
                if neg_mask.any():
                    logger.warning(f"[AFRICA] {asset_id}: Removing {neg_mask.sum()} negative {col} values")
                    df.loc[neg_mask, col] = np.nan
        
        # Fill missing volume with 0
        if "volume" in df.columns:
            df["volume"] = df["volume"].fillna(0)
            df.loc[df["volume"] < 0, "volume"] = 0
        
        if df.empty:
            return None
        
        return df
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limits."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _log_provider_success(self, provider: str, asset_id: str):
        """Log successful provider fetch."""
        try:
            with self._store._get_connection() as conn:
                conn.execute("""
                    INSERT INTO provider_logs (provider, market_scope, endpoint, status)
                    VALUES (?, 'AFRICA', ?, 'success')
                """, (provider, asset_id))
        except Exception:
            pass
    
    def _log_provider_failure(self, asset_id: str):
        """Log failed fetch attempt."""
        try:
            with self._store._get_connection() as conn:
                conn.execute("""
                    INSERT INTO provider_logs (provider, market_scope, endpoint, status, error)
                    VALUES ('all', 'AFRICA', ?, 'failed', 'All providers failed')
                """, (asset_id,))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def fetch_bars_africa(
    asset_id: str,
    days: int = 756,
    parquet_store: Optional[ParquetStore] = None
) -> Optional[pd.DataFrame]:
    """
    Fetch bars for an African asset.
    
    Args:
        asset_id: Asset ID (e.g., "NPN.JSE")
        days: Days of history
        parquet_store: Optional ParquetStore instance
        
    Returns:
        DataFrame with OHLCV data
    """
    fetcher = AfricaDataFetcher(parquet_store=parquet_store)
    return fetcher.fetch_bars(asset_id, days)


def refresh_africa_data(
    asset_ids: List[str],
    days: int = 756
) -> Dict[str, int]:
    """
    Refresh data for multiple African assets.
    
    Args:
        asset_ids: List of asset IDs
        days: Days of history
        
    Returns:
        Dict with success/failed counts
    """
    fetcher = AfricaDataFetcher()
    return fetcher.fetch_batch(asset_ids, days)


def get_data_freshness(asset_id: str) -> Optional[int]:
    """
    Get data freshness in days for an asset.
    
    Args:
        asset_id: Asset ID
        
    Returns:
        Days since last data point, or None
    """
    parquet = ParquetStore(market_scope="AFRICA")
    last_date = parquet.get_last_date(asset_id)
    
    if last_date:
        return (date.today() - last_date).days
    
    return None


def is_data_stale(asset_id: str, threshold_days: int = None) -> bool:
    """
    Check if data is stale for an asset.
    
    Args:
        asset_id: Asset ID
        threshold_days: Override stale threshold
        
    Returns:
        True if data is stale
    """
    freshness = get_data_freshness(asset_id)
    
    if freshness is None:
        return True
    
    if threshold_days is None:
        # Get threshold from exchange config
        parts = asset_id.rsplit(".", 1)
        exchange = parts[1] if len(parts) == 2 else "JSE"
        threshold_days = get_stale_threshold_for_exchange(exchange)
    
    return freshness > threshold_days
