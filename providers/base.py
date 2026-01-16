"""
MarketGPS v7.0 - Abstract Base Provider
Interface definition for all data providers.
"""
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from core.models import ProviderHealth, SearchResult


class DataProvider(ABC):
    """
    Abstract base class for data providers.
    All providers must implement these methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass
    
    @abstractmethod
    def normalize_symbol(self, raw: str, default_exchange: Optional[str] = None) -> str:
        """
        Normalize a user-input symbol to provider format.
        
        Args:
            raw: Raw symbol input (e.g., "AAPL", "SPY")
            default_exchange: Default exchange if not specified (e.g., "US")
            
        Returns:
            Normalized symbol (e.g., "AAPL.US")
        """
        pass
    
    @abstractmethod
    def extract_symbol(self, normalized: str) -> str:
        """
        Extract the base symbol from normalized format.
        
        Args:
            normalized: Normalized symbol (e.g., "AAPL.US")
            
        Returns:
            Base symbol (e.g., "AAPL")
        """
        pass
    
    @abstractmethod
    def fetch_daily_bars(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV bars for a symbol.
        
        Args:
            symbol: Normalized symbol (e.g., "AAPL.US")
            start: Start date (inclusive)
            end: End date (inclusive)
            
        Returns:
            DataFrame with DatetimeIndex and columns: Open, High, Low, Close, Volume
            Empty DataFrame if no data or error.
        """
        pass
    
    @abstractmethod
    def fetch_daily_bars_batch(
        self,
        symbols: List[str],
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch daily bars for multiple symbols.
        
        Args:
            symbols: List of normalized symbols
            start: Start date
            end: End date
            
        Returns:
            Dict mapping symbol to DataFrame
        """
        pass
    
    def fetch_intraday_bars(
        self,
        symbol: str,
        interval: str = "5m",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Fetch intraday bars (optional - not all providers support this).
        
        Args:
            symbol: Normalized symbol
            interval: Bar interval ("1m", "5m", "15m", "1h")
            start: Start datetime
            end: End datetime
            
        Returns:
            DataFrame with OHLCV data, or empty if not supported
        """
        return pd.DataFrame()
    
    def fetch_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data for a symbol (optional).
        
        Args:
            symbol: Normalized symbol
            
        Returns:
            Dict with fundamental metrics, empty if not available
        """
        return {}
    
    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Search for symbols matching a query (optional).
        
        Args:
            query: Search query string
            limit: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        return []
    
    @abstractmethod
    def healthcheck(self) -> ProviderHealth:
        """
        Check provider health and connectivity.
        
        Returns:
            ProviderHealth object with status information
        """
        pass
    
    def get_supported_exchanges(self) -> List[str]:
        """
        Get list of supported exchanges.
        
        Returns:
            List of exchange codes
        """
        return ["US"]
    
    def is_market_open(self, exchange: str = "US") -> bool:
        """
        Check if market is currently open (optional).
        
        Args:
            exchange: Exchange code
            
        Returns:
            True if market is open
        """
        return True  # Default: assume always available
    
    def get_bars(
        self,
        symbol: str,
        days: int = 504,
        end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Convenience method to fetch daily bars for N days.
        
        Args:
            symbol: Symbol (will be normalized)
            days: Number of days of history to fetch
            end: End date (default: today)
            
        Returns:
            DataFrame with OHLCV data
        """
        from datetime import timedelta
        
        end_date = end or date.today()
        start_date = end_date - timedelta(days=days)
        
        normalized = self.normalize_symbol(symbol)
        return self.fetch_daily_bars(normalized, start=start_date, end=end_date)
    
    @property
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        return True
