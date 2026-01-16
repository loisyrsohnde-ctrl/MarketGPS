"""
MarketGPS YFinance Provider.
Free data provider using yfinance library.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from core.utils import get_logger, safe_float
from .base import (
    BaseProvider, ProviderError, DataNotFoundError,
    HealthCheckResult, Fundamentals, AssetMetadata
)

logger = get_logger(__name__)


class YFinanceProvider(BaseProvider):
    """
    Yahoo Finance data provider using yfinance library.
    
    Free, no API key required.
    Rate limits apply but are generally generous.
    """
    
    def __init__(self, **kwargs):
        """Initialize provider."""
        self._yf = None
        self._available = False
        self._last_error: Optional[str] = None
        
        try:
            import yfinance as yf
            self._yf = yf
            self._available = True
            logger.info("YFinance provider initialized")
        except ImportError:
            self._last_error = "yfinance not installed"
            logger.error("yfinance not installed. Run: pip install yfinance")
    
    @property
    def name(self) -> str:
        return "yfinance"
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def get_bars(
        self,
        symbols: List[str],
        start: datetime,
        end: datetime,
        interval: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV bars for symbols.
        
        Handles both single and batch downloads.
        Normalizes MultiIndex columns from batch downloads.
        """
        if not self._available:
            logger.error("YFinance not available")
            return {}
        
        if not symbols:
            return {}
        
        results = {}
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")
        
        try:
            # Batch download for efficiency
            if len(symbols) == 1:
                # Single symbol - simpler handling
                df = self._yf.download(
                    symbols[0],
                    start=start_str,
                    end=end_str,
                    interval=interval,
                    progress=False,
                    auto_adjust=True
                )
                if not df.empty:
                    results[symbols[0]] = self.normalize_dataframe(df)
            else:
                # Multiple symbols - batch download
                df = self._yf.download(
                    symbols,
                    start=start_str,
                    end=end_str,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    group_by="ticker"
                )
                
                if not df.empty:
                    # Handle MultiIndex columns
                    if isinstance(df.columns, pd.MultiIndex):
                        for symbol in symbols:
                            try:
                                if symbol in df.columns.get_level_values(0):
                                    symbol_df = df[symbol].copy()
                                    normalized = self.normalize_dataframe(symbol_df)
                                    if not normalized.empty:
                                        results[symbol] = normalized
                            except Exception as e:
                                logger.warning(f"Failed to extract {symbol}: {e}")
                    else:
                        # Single column level - single symbol in batch
                        normalized = self.normalize_dataframe(df)
                        if not normalized.empty and len(symbols) == 1:
                            results[symbols[0]] = normalized
        
        except Exception as e:
            logger.error(f"Batch download failed: {e}")
            # Fallback: individual downloads
            for symbol in symbols:
                try:
                    df = self._yf.download(
                        symbol,
                        start=start_str,
                        end=end_str,
                        interval=interval,
                        progress=False,
                        auto_adjust=True
                    )
                    if not df.empty:
                        results[symbol] = self.normalize_dataframe(df)
                except Exception as sym_e:
                    logger.warning(f"Failed to download {symbol}: {sym_e}")
        
        return results
    
    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        """Fetch fundamental data for equity."""
        if not self._available:
            return None
        
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info
            
            if not info or "symbol" not in info:
                return None
            
            return Fundamentals(
                pe_ratio=safe_float(info.get("trailingPE")),
                forward_pe=safe_float(info.get("forwardPE")),
                profit_margin=safe_float(info.get("profitMargins")),
                operating_margin=safe_float(info.get("operatingMargins")),
                roe=safe_float(info.get("returnOnEquity")),
                roa=safe_float(info.get("returnOnAssets")),
                revenue_growth=safe_float(info.get("revenueGrowth")),
                earnings_growth=safe_float(info.get("earningsGrowth")),
                debt_to_equity=safe_float(info.get("debtToEquity")),
                current_ratio=safe_float(info.get("currentRatio")),
                market_cap=safe_float(info.get("marketCap")),
                sector=info.get("sector"),
                industry=info.get("industry"),
            )
        except Exception as e:
            logger.warning(f"Failed to get fundamentals for {symbol}: {e}")
            return None
    
    def get_metadata(self, symbol: str) -> Optional[AssetMetadata]:
        """Fetch asset metadata."""
        if not self._available:
            return None
        
        try:
            ticker = self._yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            # Infer asset type
            asset_type = self.infer_asset_type(info)
            
            return AssetMetadata(
                symbol=symbol.upper(),
                name=info.get("shortName", info.get("longName", symbol)),
                asset_type=asset_type,
                exchange=info.get("exchange"),
                currency=info.get("currency", "USD"),
            )
        except Exception as e:
            logger.warning(f"Failed to get metadata for {symbol}: {e}")
            return AssetMetadata(
                symbol=symbol.upper(),
                name=symbol.upper(),
                asset_type="UNKNOWN",
            )
    
    def healthcheck(self) -> HealthCheckResult:
        """Check provider health."""
        if not self._available:
            return HealthCheckResult(
                status="unhealthy",
                message=self._last_error or "yfinance not available",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        start = time.time()
        
        try:
            # Simple test: fetch 1 day of SPY
            end = datetime.now()
            start_date = end - timedelta(days=5)
            
            df = self._yf.download(
                "SPY",
                start=start_date.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                progress=False
            )
            
            latency = int((time.time() - start) * 1000)
            
            if df.empty:
                return HealthCheckResult(
                    status="degraded",
                    message="Data fetch returned empty",
                    latency_ms=latency,
                    timestamp=datetime.now()
                )
            
            return HealthCheckResult(
                status="healthy",
                message="OK",
                latency_ms=latency,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return HealthCheckResult(
                status="unhealthy",
                message=str(e),
                latency_ms=latency,
                timestamp=datetime.now()
            )
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get current quotes for multiple symbols.
        
        Returns dict with last price, change, volume for each symbol.
        """
        if not self._available or not symbols:
            return {}
        
        results = {}
        
        try:
            # Use fast_info for quick quotes
            for symbol in symbols:
                try:
                    ticker = self._yf.Ticker(symbol)
                    fast_info = ticker.fast_info
                    
                    results[symbol] = {
                        "last_price": safe_float(fast_info.get("lastPrice")),
                        "previous_close": safe_float(fast_info.get("previousClose")),
                        "market_cap": safe_float(fast_info.get("marketCap")),
                        "currency": fast_info.get("currency", "USD"),
                    }
                except Exception as e:
                    logger.debug(f"Failed to get quote for {symbol}: {e}")
        
        except Exception as e:
            logger.error(f"Batch quotes failed: {e}")
        
        return results
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for symbols matching query.
        
        Note: yfinance doesn't have great search, this is limited.
        """
        # yfinance doesn't have a proper search API
        # Return empty - implement with another source if needed
        return []
