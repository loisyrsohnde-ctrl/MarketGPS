"""
MarketGPS Tiingo Provider.
Premium data provider - requires API key.
"""
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from core.utils import get_logger
from .base import (
    BaseProvider, ProviderError, AuthenticationError,
    HealthCheckResult, Fundamentals, AssetMetadata
)

logger = get_logger(__name__)


class TiingoProvider(BaseProvider):
    """
    Tiingo data provider.
    
    Requires API key from https://www.tiingo.com/
    Set TIINGO_API_KEY environment variable.
    
    Features:
    - High quality EOD data
    - Fundamentals
    - News
    - IEX real-time data (with higher tier)
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Tiingo provider.
        
        Args:
            api_key: Tiingo API key (or set TIINGO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TIINGO_API_KEY")
        self._client = None
        self._available = False
        
        if not self.api_key:
            logger.warning(
                "Tiingo API key not set. "
                "Set TIINGO_API_KEY environment variable or pass api_key parameter."
            )
        else:
            self._setup_client()
    
    def _setup_client(self):
        """Setup Tiingo client if available."""
        try:
            # Try to import tiingo library
            from tiingo import TiingoClient
            
            config = {"api_key": self.api_key}
            self._client = TiingoClient(config)
            self._available = True
            logger.info("Tiingo provider initialized")
            
        except ImportError:
            logger.warning(
                "tiingo library not installed. "
                "Run: pip install tiingo"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Tiingo: {e}")
    
    @property
    def name(self) -> str:
        return "tiingo"
    
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
        """Fetch OHLCV bars."""
        if not self._available:
            raise AuthenticationError(
                "Tiingo provider not available. "
                "Ensure TIINGO_API_KEY is set and tiingo library is installed."
            )
        
        results = {}
        
        for symbol in symbols:
            try:
                # Tiingo API call
                data = self._client.get_dataframe(
                    symbol,
                    startDate=start.strftime("%Y-%m-%d"),
                    endDate=end.strftime("%Y-%m-%d"),
                    frequency="daily" if interval == "1d" else interval
                )
                
                if data is not None and not data.empty:
                    # Normalize column names
                    column_map = {
                        "open": "Open",
                        "high": "High",
                        "low": "Low",
                        "close": "Close",
                        "adjClose": "Close",
                        "volume": "Volume",
                    }
                    data = data.rename(columns=column_map)
                    
                    # Select required columns
                    required = ["Open", "High", "Low", "Close", "Volume"]
                    available = [c for c in required if c in data.columns]
                    data = data[available]
                    
                    results[symbol] = self.normalize_dataframe(data)
                    
            except Exception as e:
                logger.warning(f"Tiingo: Failed to fetch {symbol}: {e}")
        
        return results
    
    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        """Fetch fundamental data."""
        if not self._available:
            return None
        
        try:
            # Tiingo fundamentals endpoint
            data = self._client.get_fundamentals_statements(
                symbol,
                startDate="2020-01-01"
            )
            
            if not data:
                return None
            
            # Extract latest fundamentals
            # Note: Tiingo returns detailed financial statements
            # This is a simplified extraction
            latest = data[0] if data else {}
            
            return Fundamentals(
                pe_ratio=latest.get("peRatio"),
                profit_margin=latest.get("netMargin"),
                revenue_growth=latest.get("revenueGrowthYoy"),
                market_cap=latest.get("marketCap"),
            )
            
        except Exception as e:
            logger.warning(f"Tiingo: Failed to get fundamentals for {symbol}: {e}")
            return None
    
    def get_metadata(self, symbol: str) -> Optional[AssetMetadata]:
        """Fetch asset metadata."""
        if not self._available:
            return None
        
        try:
            meta = self._client.get_ticker_metadata(symbol)
            
            if not meta:
                return None
            
            return AssetMetadata(
                symbol=symbol.upper(),
                name=meta.get("name", symbol),
                asset_type="EQUITY",  # Tiingo primarily covers equities
                exchange=meta.get("exchangeCode"),
                currency="USD",
            )
            
        except Exception as e:
            logger.warning(f"Tiingo: Failed to get metadata for {symbol}: {e}")
            return None
    
    def healthcheck(self) -> HealthCheckResult:
        """Check provider health."""
        if not self.api_key:
            return HealthCheckResult(
                status="unhealthy",
                message="API key not configured",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        if not self._available:
            return HealthCheckResult(
                status="unhealthy",
                message="Provider not initialized",
                latency_ms=0,
                timestamp=datetime.now()
            )
        
        start = time.time()
        
        try:
            # Test API with simple request
            self._client.get_ticker_metadata("AAPL")
            latency = int((time.time() - start) * 1000)
            
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
