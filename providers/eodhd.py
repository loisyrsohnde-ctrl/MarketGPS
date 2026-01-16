"""
MarketGPS v7.0 - EODHD Provider
Implementation of DataProvider for EODHD API.
"""
import time
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from providers.base import DataProvider
from core.config import get_config, get_logger
from core.models import ProviderHealth, SearchResult

logger = get_logger(__name__)


class EODHDError(Exception):
    """EODHD API Error."""
    pass


class EODHDRateLimitError(EODHDError):
    """Rate limit exceeded."""
    pass


class EODHDProvider(DataProvider):
    """
    EODHD.com data provider implementation.
    
    Supports:
    - Daily EOD bars
    - Intraday bars (limited)
    - Fundamentals
    - Symbol search
    """
    
    def __init__(self):
        """Initialize EODHD provider."""
        self._config = get_config().eodhd
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "MarketGPS/7.0"
        })
        self._last_request_time = 0
        self._min_request_interval = 0.2  # 200ms between requests
        
        if not self._config.is_configured:
            logger.warning("EODHD API key not configured - provider will return empty data")
    
    @property
    def name(self) -> str:
        return "eodhd"
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.RequestException, EODHDRateLimitError))
    )
    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Make an API request with retry logic.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            EODHDError: On API error
            EODHDRateLimitError: On rate limit
        """
        if not self._config.is_configured:
            logger.debug("EODHD not configured, returning empty")
            return []
        
        self._rate_limit()
        
        url = f"{self._config.base_url}/{endpoint}"
        params = params or {}
        params["api_token"] = self._config.api_key
        params["fmt"] = "json"
        
        start_time = time.time()
        
        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self._config.timeout
            )
            latency_ms = int((time.time() - start_time) * 1000)
            
            if response.status_code == 429:
                logger.warning(f"EODHD rate limited on {endpoint}")
                raise EODHDRateLimitError("Rate limit exceeded")
            
            if response.status_code == 401:
                logger.error("EODHD: Invalid API key")
                raise EODHDError("Invalid API key")
            
            if response.status_code >= 500:
                logger.warning(f"EODHD server error {response.status_code}")
                raise EODHDError(f"Server error: {response.status_code}")
            
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"EODHD {endpoint} returned {len(data) if isinstance(data, list) else 'object'} in {latency_ms}ms")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.warning(f"EODHD timeout on {endpoint}")
            raise
        except requests.exceptions.RequestException as e:
            logger.warning(f"EODHD request error: {e}")
            raise
        except ValueError as e:
            logger.warning(f"EODHD JSON parse error: {e}")
            return []
    
    def normalize_symbol(self, raw: str, default_exchange: Optional[str] = None) -> str:
        """
        Normalize symbol to EODHD format (SYMBOL.EXCHANGE).
        
        Examples:
            "AAPL" -> "AAPL.US"
            "AAPL.US" -> "AAPL.US" (unchanged)
            "VOD.LSE" -> "VOD.LSE" (unchanged)
        """
        raw = raw.strip().upper()
        
        if "." in raw:
            return raw
        
        exchange = default_exchange or self._config.default_exchange
        return f"{raw}.{exchange}"
    
    def extract_symbol(self, normalized: str) -> str:
        """
        Extract base symbol from normalized format.
        
        Example: "AAPL.US" -> "AAPL"
        """
        if "." in normalized:
            return normalized.rsplit(".", 1)[0]
        return normalized
    
    def fetch_daily_bars(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars from EODHD.
        
        API: GET /eod/{SYMBOL}?from=YYYY-MM-DD&to=YYYY-MM-DD
        """
        try:
            # Ensure symbol is normalized
            symbol = self.normalize_symbol(symbol)
            
            params = {"period": "d"}
            
            if start:
                params["from"] = start.strftime("%Y-%m-%d")
            if end:
                params["to"] = end.strftime("%Y-%m-%d")
            
            data = self._request(f"eod/{symbol}", params)
            
            if not data or not isinstance(data, list):
                logger.debug(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # Rename columns to standard format
            column_map = {
                "date": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "adjusted_close": "Adj Close",
                "volume": "Volume"
            }
            df = df.rename(columns=column_map)
            
            # Convert date to datetime index
            df["Date"] = pd.to_datetime(df["Date"])
            df = df.set_index("Date")
            df.index = df.index.tz_localize(None)  # Ensure timezone-naive
            
            # Select and order columns
            cols = ["Open", "High", "Low", "Close", "Volume"]
            if "Adj Close" in df.columns:
                cols.append("Adj Close")
            
            df = df[[c for c in cols if c in df.columns]]
            
            # Sort by date
            df = df.sort_index()
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            logger.info(f"Fetched {len(df)} bars for {symbol}")
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
        EODHD doesn't have a true batch endpoint, so we fetch sequentially.
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
    
    def fetch_intraday_bars(
        self,
        symbol: str,
        interval: str = "5m",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch intraday bars from EODHD.
        
        API: GET /intraday/{SYMBOL}?interval=5m&from=TIMESTAMP&to=TIMESTAMP
        
        Note: EODHD intraday is limited to recent data.
        """
        try:
            symbol = self.normalize_symbol(symbol)
            
            params = {"interval": interval}
            
            if start:
                params["from"] = int(start.timestamp())
            if end:
                params["to"] = int(end.timestamp())
            
            data = self._request(f"intraday/{symbol}", params)
            
            if not data or not isinstance(data, list):
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # Convert timestamp
            if "datetime" in df.columns:
                df["Date"] = pd.to_datetime(df["datetime"])
            elif "timestamp" in df.columns:
                df["Date"] = pd.to_datetime(df["timestamp"], unit="s")
            
            df = df.set_index("Date")
            df.index = df.index.tz_localize(None)
            
            # Rename columns
            column_map = {
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            }
            df = df.rename(columns=column_map)
            
            cols = ["Open", "High", "Low", "Close", "Volume"]
            df = df[[c for c in cols if c in df.columns]]
            
            return df.sort_index()
            
        except Exception as e:
            logger.error(f"Failed to fetch intraday for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data from EODHD.
        
        API: GET /fundamentals/{SYMBOL}
        """
        try:
            symbol = self.normalize_symbol(symbol)
            
            data = self._request(f"fundamentals/{symbol}")
            
            if not data or not isinstance(data, dict):
                return {}
            
            # Extract key metrics
            result = {}
            
            # General info
            general = data.get("General", {})
            result["name"] = general.get("Name")
            result["sector"] = general.get("Sector")
            result["industry"] = general.get("Industry")
            result["description"] = general.get("Description")
            result["market_cap"] = general.get("MarketCapitalization")
            
            # Highlights
            highlights = data.get("Highlights", {})
            result["pe_ratio"] = highlights.get("PERatio")
            result["peg_ratio"] = highlights.get("PEGRatio")
            result["eps"] = highlights.get("EarningsShare")
            result["dividend_yield"] = highlights.get("DividendYield")
            result["profit_margin"] = highlights.get("ProfitMargin")
            result["operating_margin"] = highlights.get("OperatingMarginTTM")
            result["return_on_equity"] = highlights.get("ReturnOnEquityTTM")
            result["revenue_growth"] = highlights.get("QuarterlyRevenueGrowthYOY")
            
            # Valuation
            valuation = data.get("Valuation", {})
            result["forward_pe"] = valuation.get("ForwardPE")
            result["price_to_book"] = valuation.get("PriceBookMRQ")
            result["price_to_sales"] = valuation.get("PriceSalesTTM")
            
            # Technicals
            technicals = data.get("Technicals", {})
            result["beta"] = technicals.get("Beta")
            result["52_week_high"] = technicals.get("52WeekHigh")
            result["52_week_low"] = technicals.get("52WeekLow")
            result["50_day_ma"] = technicals.get("50DayMA")
            result["200_day_ma"] = technicals.get("200DayMA")
            
            # Filter out None values
            result = {k: v for k, v in result.items() if v is not None}
            
            logger.debug(f"Fetched fundamentals for {symbol}: {len(result)} fields")
            return result
            
        except Exception as e:
            logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
            return {}
    
    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search for symbols matching a query.
        
        API: GET /search/{QUERY}
        """
        try:
            data = self._request(f"search/{query}")
            
            if not data or not isinstance(data, list):
                return []
            
            results = []
            for item in data[:limit]:
                try:
                    result = SearchResult(
                        symbol=item.get("Code", ""),
                        name=item.get("Name", ""),
                        exchange=item.get("Exchange", "US"),
                        asset_type=item.get("Type", "Common Stock"),
                        currency=item.get("Currency", "USD"),
                        isin=item.get("ISIN")
                    )
                    results.append(result)
                except Exception:
                    continue
            
            logger.info(f"Search '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            return []
    
    def healthcheck(self) -> ProviderHealth:
        """
        Check EODHD API health.
        Uses a lightweight endpoint to test connectivity.
        """
        if not self._config.is_configured:
            return ProviderHealth(
                provider=self.name,
                status="down",
                message="API key not configured",
                latency_ms=0
            )
        
        try:
            start = time.time()
            
            # Use exchange list as a lightweight health check
            response = self._session.get(
                f"{self._config.base_url}/exchanges-list",
                params={"api_token": self._config.api_key, "fmt": "json"},
                timeout=5
            )
            
            latency_ms = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return ProviderHealth(
                    provider=self.name,
                    status="healthy",
                    message="API responding normally",
                    latency_ms=latency_ms,
                    last_check=datetime.now()
                )
            elif response.status_code == 429:
                return ProviderHealth(
                    provider=self.name,
                    status="degraded",
                    message="Rate limited",
                    latency_ms=latency_ms,
                    last_check=datetime.now()
                )
            else:
                return ProviderHealth(
                    provider=self.name,
                    status="degraded",
                    message=f"HTTP {response.status_code}",
                    latency_ms=latency_ms,
                    last_check=datetime.now()
                )
                
        except requests.exceptions.Timeout:
            return ProviderHealth(
                provider=self.name,
                status="degraded",
                message="Timeout",
                latency_ms=5000,
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
        return [
            # Americas
            "US",      # United States
            "TO",      # Toronto
            # Europe
            "LSE",     # London
            "PA",      # Paris
            "XETRA",   # Frankfurt
            "AS",      # Amsterdam
            "SW",      # Switzerland
            "MI",      # Milan
            "MC",      # Madrid
            # Asia-Pacific
            "HK",      # Hong Kong
            "SG",      # Singapore
            "AU",      # Australia
            # Africa
            "JSE",     # Johannesburg (South Africa)
            "NG",      # Nigeria (NGX)
            "CA",      # Cairo (Egypt)
            "BRVM",    # West Africa
        ]
    
    def get_africa_exchanges(self) -> Dict[str, Dict[str, str]]:
        """
        Get list of supported African exchanges with metadata.
        
        Returns:
            Dict mapping exchange code to metadata
        """
        return {
            "JSE": {
                "name": "Johannesburg Stock Exchange",
                "country": "South Africa",
                "currency": "ZAR",
                "timezone": "Africa/Johannesburg"
            },
            "NG": {
                "name": "Nigerian Exchange (NGX)",
                "country": "Nigeria",
                "currency": "NGN",
                "timezone": "Africa/Lagos"
            },
            "CA": {
                "name": "Egyptian Exchange (EGX)",
                "country": "Egypt",
                "currency": "EGP",
                "timezone": "Africa/Cairo"
            },
            "BRVM": {
                "name": "BRVM (West Africa)",
                "country": "Côte d'Ivoire",
                "currency": "XOF",
                "timezone": "Africa/Abidjan"
            }
        }
    
    @property
    def is_configured(self) -> bool:
        """Check if EODHD provider is configured."""
        return self._config.is_configured
    
    def get_listings(self, exchange_code: str = "US") -> List[Dict[str, Any]]:
        """
        Get list of available symbols for an exchange.
        
        API: GET /exchange-symbol-list/{EXCHANGE}
        """
        try:
            data = self._request(f"exchange-symbol-list/{exchange_code}")
            
            if not data or not isinstance(data, list):
                return []
            
            logger.info(f"Fetched {len(data)} listings for {exchange_code}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch listings for {exchange_code}: {e}")
            return []
    
    def list_exchanges(self) -> List[Dict[str, Any]]:
        """
        Get list of all available exchanges from EODHD.
        
        API: GET /exchanges-list
        
        Returns:
            List of exchange info dicts
        """
        try:
            data = self._request("exchanges-list")
            
            if not data or not isinstance(data, list):
                return []
            
            logger.info(f"Fetched {len(data)} exchanges")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch exchanges list: {e}")
            return []
    
    def list_symbols(self, exchange_code: str) -> List[Dict[str, Any]]:
        """
        Get list of symbols for a specific exchange.
        Alias for get_listings() with cleaner interface.
        
        Args:
            exchange_code: Exchange code (e.g., "JSE", "NG", "US")
            
        Returns:
            List of symbol info dicts with keys: Code, Name, Type, Exchange, Currency, ISIN
        """
        return self.get_listings(exchange_code)
    
    def get_eod(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Get End-of-Day data for a symbol.
        Alias for fetch_daily_bars() with cleaner interface.
        
        Args:
            symbol: Symbol with exchange suffix (e.g., "NPN.JSE", "DANGCEM.NG")
            from_date: Start date
            to_date: End date
            
        Returns:
            DataFrame with OHLCV data
        """
        return self.fetch_daily_bars(symbol, start=from_date, end=to_date)
    
    def get_bulk_eod(
        self,
        exchange_code: str,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get bulk EOD data for all symbols on an exchange for a specific date.
        
        API: GET /eod-bulk-last-day/{EXCHANGE}?date=YYYY-MM-DD
        
        Note: This is more efficient than fetching individual symbols
        but only returns the last trading day's data.
        
        Args:
            exchange_code: Exchange code (e.g., "JSE", "US")
            date_str: Date in YYYY-MM-DD format (default: last trading day)
            
        Returns:
            List of EOD data dicts for all symbols
        """
        try:
            params = {}
            if date_str:
                params["date"] = date_str
            
            data = self._request(f"eod-bulk-last-day/{exchange_code}", params)
            
            if not data or not isinstance(data, list):
                return []
            
            logger.info(f"Fetched bulk EOD for {exchange_code}: {len(data)} symbols")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch bulk EOD for {exchange_code}: {e}")
            return []
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key is configured and working.
        
        Returns:
            True if API key is valid, False otherwise
        """
        if not self._config.is_configured:
            logger.error("EODHD API key not configured")
            return False
        
        try:
            # Use a lightweight endpoint to test
            response = self._session.get(
                f"{self._config.base_url}/exchanges-list",
                params={"api_token": self._config.api_key, "fmt": "json"},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("EODHD API key validated successfully")
                return True
            elif response.status_code == 401:
                logger.error("EODHD API key is invalid")
                return False
            else:
                logger.warning(f"EODHD API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to validate EODHD API key: {e}")
            return False
