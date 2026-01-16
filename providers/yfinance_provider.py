"""
MarketGPS v7.0 - Yahoo Finance Provider (Fallback)
Free provider using yfinance library.
"""
import time
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd

from providers.base import DataProvider
from core.config import get_logger
from core.models import ProviderHealth, SearchResult

logger = get_logger(__name__)

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not installed - YFinanceProvider will not work")


class YFinanceProvider(DataProvider):
    """
    Yahoo Finance data provider using yfinance library.
    Free fallback when EODHD API key is not configured.
    """
    
    def __init__(self):
        """Initialize YFinance provider."""
        if not YFINANCE_AVAILABLE:
            logger.error("yfinance is not installed")
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 500ms between requests to avoid rate limiting
    
    @property
    def name(self) -> str:
        return "yfinance"
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def normalize_symbol(self, raw: str, default_exchange: Optional[str] = None) -> str:
        """
        Normalize symbol for yfinance.
        yfinance uses simple symbols for US stocks (AAPL, not AAPL.US)
        """
        raw = raw.strip().upper()
        
        # Remove exchange suffix if present (convert AAPL.US to AAPL)
        if "." in raw:
            parts = raw.split(".")
            # Keep the suffix only for non-US exchanges
            if parts[-1] in ["US", "NYSE", "NASDAQ"]:
                return parts[0]
            return raw
        
        return raw
    
    def extract_symbol(self, normalized: str) -> str:
        """Extract base symbol."""
        if "." in normalized:
            return normalized.split(".")[0]
        return normalized
    
    def fetch_daily_bars(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars from Yahoo Finance.
        """
        if not YFINANCE_AVAILABLE:
            return pd.DataFrame()
        
        try:
            self._rate_limit()
            
            # Normalize symbol for yfinance
            yf_symbol = self.normalize_symbol(symbol)
            
            # Default date range
            if end is None:
                end = date.today()
            if start is None:
                start = end - timedelta(days=730)  # 2 years
            
            # Create ticker
            ticker = yf.Ticker(yf_symbol)
            
            # Download data
            df = ticker.history(
                start=start.strftime("%Y-%m-%d"),
                end=(end + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d",
                auto_adjust=False
            )
            
            if df.empty:
                logger.debug(f"No data returned for {yf_symbol}")
                return pd.DataFrame()
            
            # Standardize columns
            df = df.rename(columns={
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume",
                "Adj Close": "Adj Close"
            })
            
            # Ensure timezone-naive index
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Select standard columns
            cols = ["Open", "High", "Low", "Close", "Volume"]
            df = df[[c for c in cols if c in df.columns]]
            
            # Sort by date
            df = df.sort_index()
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            logger.info(f"Fetched {len(df)} bars for {yf_symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch bars for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_daily_bars_batch(
        self,
        symbols: List[str],
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch daily bars for multiple symbols.
        """
        results = {}
        
        for symbol in symbols:
            try:
                df = self.fetch_daily_bars(symbol, start, end)
                if not df.empty:
                    results[symbol] = df
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                continue
        
        return results
    
    def fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data from Yahoo Finance.
        """
        if not YFINANCE_AVAILABLE:
            return {}
        
        try:
            self._rate_limit()
            
            yf_symbol = self.normalize_symbol(symbol)
            ticker = yf.Ticker(yf_symbol)
            
            info = ticker.info
            
            if not info:
                return {}
            
            result = {}
            
            # Map yfinance fields to our standard format
            field_mapping = {
                "shortName": "name",
                "sector": "sector",
                "industry": "industry",
                "longBusinessSummary": "description",
                "marketCap": "market_cap",
                "trailingPE": "pe_ratio",
                "forwardPE": "forward_pe",
                "pegRatio": "peg_ratio",
                "trailingEps": "eps",
                "dividendYield": "dividend_yield",
                "profitMargins": "profit_margin",
                "operatingMargins": "operating_margin",
                "returnOnEquity": "return_on_equity",
                "revenueGrowth": "revenue_growth",
                "priceToBook": "price_to_book",
                "beta": "beta",
                "fiftyTwoWeekHigh": "52_week_high",
                "fiftyTwoWeekLow": "52_week_low",
                "fiftyDayAverage": "50_day_ma",
                "twoHundredDayAverage": "200_day_ma",
            }
            
            for yf_field, our_field in field_mapping.items():
                value = info.get(yf_field)
                if value is not None:
                    result[our_field] = value
            
            logger.debug(f"Fetched fundamentals for {yf_symbol}: {len(result)} fields")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            return {}
    
    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search is not well supported by yfinance.
        Returns empty list - use EODHD for search.
        """
        return []
    
    def healthcheck(self) -> ProviderHealth:
        """
        Check Yahoo Finance connectivity.
        """
        if not YFINANCE_AVAILABLE:
            return ProviderHealth(
                provider=self.name,
                status="down",
                message="yfinance not installed",
                latency_ms=0
            )
        
        try:
            start = time.time()
            
            # Try to fetch a known symbol
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            
            latency_ms = int((time.time() - start) * 1000)
            
            if info and info.get("symbol"):
                return ProviderHealth(
                    provider=self.name,
                    status="healthy",
                    message="Yahoo Finance responding",
                    latency_ms=latency_ms,
                    last_check=datetime.now()
                )
            else:
                return ProviderHealth(
                    provider=self.name,
                    status="degraded",
                    message="Limited response from Yahoo Finance",
                    latency_ms=latency_ms,
                    last_check=datetime.now()
                )
                
        except Exception as e:
            return ProviderHealth(
                provider=self.name,
                status="down",
                message=str(e),
                latency_ms=0,
                last_check=datetime.now()
            )
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchanges."""
        return ["US", "NYSE", "NASDAQ"]
    
    @property
    def is_configured(self) -> bool:
        """yfinance is always available if installed."""
        return YFINANCE_AVAILABLE
