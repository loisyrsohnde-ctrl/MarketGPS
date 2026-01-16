"""
MarketGPS - Multi-Source Data Router
Routes data requests to the appropriate provider based on asset type.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from providers.base import DataProvider
from providers.eodhd import EODHDProvider
from providers.yfinance_provider import YFinanceProvider
from core.config import get_config, get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION DES SOURCES PAR TYPE D'INSTRUMENT
# ═══════════════════════════════════════════════════════════════════════════════

PROVIDER_CONFIG = {
    # Actions & ETF
    "EQUITY": {
        "primary": "eodhd",
        "fallback": "yfinance",
        "exchanges": {
            "US": "{ticker}.US",
            "EU": "{ticker}.{exchange}",  # .PA, .DE, .AS, .MI, etc.
            "AFRICA": "{ticker}.{exchange}",  # .JSE, .NSE, etc.
        }
    },
    "ETF": {
        "primary": "eodhd",
        "fallback": "yfinance",
        "exchanges": {
            "US": "{ticker}.US",
            "EU": "{ticker}.{exchange}",
        }
    },
    
    # Forex
    "FX": {
        "primary": "yfinance",  # Format: EURUSD=X
        "fallback": "eodhd",
        "format": "{base}{quote}=X",
    },
    
    # Crypto
    "CRYPTO": {
        "primary": "coingecko",
        "fallback": "yfinance",  # Format: BTC-USD
        "format": "{ticker}-USD",
    },
    
    # Obligations / Bonds
    "BOND": {
        "primary": "fred",  # Federal Reserve Economic Data
        "fallback": "yfinance",
        "symbols": {
            "US10Y": "^TNX",  # 10-Year Treasury
            "US2Y": "^IRX",   # 13-Week Treasury
            "US30Y": "^TYX",  # 30-Year Treasury
        }
    },
    
    # Futures
    "FUTURE": {
        "primary": "yfinance",
        "fallback": "eodhd",
        "symbols": {
            "ES": "ES=F",     # S&P 500 Futures
            "NQ": "NQ=F",     # Nasdaq Futures
            "CL": "CL=F",     # Crude Oil
            "GC": "GC=F",     # Gold
            "SI": "SI=F",     # Silver
        }
    },
    
    # Options (nécessite un provider spécialisé)
    "OPTION": {
        "primary": "tradier",  # À implémenter
        "fallback": None,
        "note": "Options require specialized provider (Tradier, IBKR)"
    },
    
    # Matières premières
    "COMMODITY": {
        "primary": "yfinance",
        "fallback": "eodhd",
        "symbols": {
            "GOLD": "GC=F",
            "SILVER": "SI=F",
            "OIL": "CL=F",
            "NATGAS": "NG=F",
            "WHEAT": "ZW=F",
            "CORN": "ZC=F",
        }
    },
    
    # Index
    "INDEX": {
        "primary": "yfinance",
        "fallback": "eodhd",
        "symbols": {
            "SPX": "^GSPC",
            "NDX": "^NDX",
            "DJI": "^DJI",
            "VIX": "^VIX",
            "DAX": "^GDAXI",
            "CAC": "^FCHI",
            "FTSE": "^FTSE",
        }
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER IMPLEMENTATIONS (À compléter)
# ═══════════════════════════════════════════════════════════════════════════════

class CoinGeckoProvider(DataProvider):
    """
    CoinGecko API for cryptocurrency data.
    Free tier: 10-30 calls/minute
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def get_bars(self, ticker: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from CoinGecko."""
        try:
            import requests
            
            # Map ticker to CoinGecko ID
            coin_id = self._get_coin_id(ticker)
            if not coin_id:
                logger.warning(f"CoinGecko: Unknown coin {ticker}")
                return None
            
            url = f"{self.BASE_URL}/coins/{coin_id}/ohlc"
            params = {"vs_currency": "usd", "days": str(days)}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return None
            
            df = pd.DataFrame(data, columns=["timestamp", "Open", "High", "Low", "Close"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            df["Volume"] = 0  # CoinGecko OHLC doesn't include volume
            
            return df
            
        except Exception as e:
            logger.error(f"CoinGecko error for {ticker}: {e}")
            return None
    
    def _get_coin_id(self, ticker: str) -> Optional[str]:
        """Map ticker to CoinGecko coin ID."""
        # Common mappings
        COIN_MAP = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LTC": "litecoin",
            "AVAX": "avalanche-2",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "XLM": "stellar",
        }
        return COIN_MAP.get(ticker.upper().replace("-USD", ""))
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for cryptocurrencies."""
        try:
            import requests
            
            url = f"{self.BASE_URL}/search"
            params = {"query": query}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            coins = data.get("coins", [])[:limit]
            
            return [
                {
                    "ticker": c["symbol"].upper(),
                    "name": c["name"],
                    "asset_type": "CRYPTO",
                    "market_cap_rank": c.get("market_cap_rank"),
                }
                for c in coins
            ]
            
        except Exception as e:
            logger.error(f"CoinGecko search error: {e}")
            return []


class FREDProvider(DataProvider):
    """
    Federal Reserve Economic Data (FRED) for bonds and economic indicators.
    Free API key required: https://fred.stlouisfed.org/docs/api/api_key.html
    """
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    def __init__(self, api_key: Optional[str] = None):
        config = get_config()
        self.api_key = api_key or getattr(config, 'fred_api_key', None)
    
    def get_bars(self, series_id: str, days: int = 365) -> Optional[pd.DataFrame]:
        """Fetch time series data from FRED."""
        if not self.api_key:
            logger.warning("FRED API key not configured")
            return None
        
        try:
            import requests
            from datetime import datetime, timedelta
            
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            url = f"{self.BASE_URL}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start_date,
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get("observations", [])
            
            if not observations:
                return None
            
            df = pd.DataFrame(observations)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df.set_index("date", inplace=True)
            
            # Convert to OHLCV format (Close only for bonds)
            result = pd.DataFrame(index=df.index)
            result["Open"] = df["value"]
            result["High"] = df["value"]
            result["Low"] = df["value"]
            result["Close"] = df["value"]
            result["Volume"] = 0
            
            return result.dropna()
            
        except Exception as e:
            logger.error(f"FRED error for {series_id}: {e}")
            return None
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search FRED series."""
        return []  # FRED doesn't have a simple search API


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class DataRouter:
    """
    Routes data requests to the appropriate provider.
    Handles fallbacks and error recovery.
    """
    
    def __init__(self):
        self.config = get_config()
        self._providers: Dict[str, DataProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """Initialize available providers."""
        # EODHD (premium, requires API key)
        if self.config.eodhd.is_configured:
            self._providers["eodhd"] = EODHDProvider()
            logger.info("EODHD provider initialized")
        
        # yfinance (free, always available)
        self._providers["yfinance"] = YFinanceProvider()
        logger.info("yfinance provider initialized")
        
        # CoinGecko (free)
        self._providers["coingecko"] = CoinGeckoProvider()
        logger.info("CoinGecko provider initialized")
        
        # FRED (free with API key)
        fred_key = getattr(self.config, 'fred_api_key', None)
        if fred_key:
            self._providers["fred"] = FREDProvider(fred_key)
            logger.info("FRED provider initialized")
    
    def get_bars(
        self,
        ticker: str,
        asset_type: str = "EQUITY",
        exchange: str = "US",
        days: int = 504
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for any asset type.
        
        Args:
            ticker: Asset ticker/symbol
            asset_type: EQUITY, ETF, FX, CRYPTO, BOND, FUTURE, COMMODITY, INDEX
            exchange: Exchange code (US, PA, DE, JSE, etc.)
            days: Number of days of history
            
        Returns:
            DataFrame with OHLCV data or None
        """
        config = PROVIDER_CONFIG.get(asset_type, PROVIDER_CONFIG["EQUITY"])
        
        # Build the full symbol
        full_symbol = self._build_symbol(ticker, asset_type, exchange, config)
        
        # Try primary provider
        primary = config.get("primary")
        if primary and primary in self._providers:
            logger.info(f"Trying {primary} for {full_symbol}")
            df = self._providers[primary].get_bars(full_symbol, days)
            if df is not None and not df.empty:
                return df
        
        # Try fallback
        fallback = config.get("fallback")
        if fallback and fallback in self._providers:
            logger.info(f"Fallback to {fallback} for {full_symbol}")
            df = self._providers[fallback].get_bars(full_symbol, days)
            if df is not None and not df.empty:
                return df
        
        logger.warning(f"No data found for {ticker} ({asset_type})")
        return None
    
    def _build_symbol(
        self,
        ticker: str,
        asset_type: str,
        exchange: str,
        config: Dict
    ) -> str:
        """Build the full symbol for the provider."""
        
        # Check for predefined symbol mappings
        symbols = config.get("symbols", {})
        if ticker.upper() in symbols:
            return symbols[ticker.upper()]
        
        # Check for format string
        format_str = config.get("format")
        if format_str:
            return format_str.format(ticker=ticker, base=ticker[:3], quote=ticker[3:])
        
        # Use exchange-based format
        exchanges = config.get("exchanges", {})
        if exchange in exchanges:
            return exchanges[exchange].format(ticker=ticker, exchange=exchange)
        
        # Default: return ticker as-is
        return ticker
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {name: True for name in self._providers.keys()}
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported asset types."""
        return list(PROVIDER_CONFIG.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

_router_instance: Optional[DataRouter] = None

def get_data_router() -> DataRouter:
    """Get singleton DataRouter instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = DataRouter()
    return _router_instance
