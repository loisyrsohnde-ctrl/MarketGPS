"""
MarketGPS Alpaca Provider.
Premium data provider - requires API key.
"""
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from core.utils import get_logger
from .base import (
    BaseProvider, ProviderError, AuthenticationError,
    HealthCheckResult, Fundamentals, AssetMetadata
)

logger = get_logger(__name__)


class AlpacaProvider(BaseProvider):
    """
    Alpaca Markets data provider.
    
    Requires API key from https://alpaca.markets/
    Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.
    
    Features:
    - Real-time and historical data
    - Stocks, ETFs, Crypto
    - Free tier available
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper: bool = True,
        **kwargs
    ):
        """
        Initialize Alpaca provider.
        
        Args:
            api_key: Alpaca API key (or set ALPACA_API_KEY env var)
            secret_key: Alpaca secret key (or set ALPACA_SECRET_KEY env var)
            paper: Use paper trading endpoint (default True)
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        self.paper = paper
        self._client = None
        self._available = False
        
        if not self.api_key or not self.secret_key:
            logger.warning(
                "Alpaca API credentials not set. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
            )
        else:
            self._setup_client()
    
    def _setup_client(self):
        """Setup Alpaca client if available."""
        try:
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockBarsRequest
            from alpaca.data.timeframe import TimeFrame
            
            self._client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            self._StockBarsRequest = StockBarsRequest
            self._TimeFrame = TimeFrame
            self._available = True
            logger.info("Alpaca provider initialized")
            
        except ImportError:
            logger.warning(
                "alpaca-py library not installed. "
                "Run: pip install alpaca-py"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca: {e}")
    
    @property
    def name(self) -> str:
        return "alpaca"
    
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
                "Alpaca provider not available. "
                "Ensure ALPACA_API_KEY and ALPACA_SECRET_KEY are set."
            )
        
        results = {}
        
        try:
            # Map interval to Alpaca TimeFrame
            timeframe_map = {
                "1d": self._TimeFrame.Day,
                "1h": self._TimeFrame.Hour,
                "1m": self._TimeFrame.Minute,
            }
            timeframe = timeframe_map.get(interval, self._TimeFrame.Day)
            
            # Create request
            request = self._StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end
            )
            
            # Fetch data
            bars = self._client.get_stock_bars(request)
            
            # Convert to DataFrames
            for symbol in symbols:
                try:
                    if symbol in bars:
                        symbol_bars = bars[symbol]
                        
                        # Convert to DataFrame
                        data = []
                        for bar in symbol_bars:
                            data.append({
                                "timestamp": bar.timestamp,
                                "Open": bar.open,
                                "High": bar.high,
                                "Low": bar.low,
                                "Close": bar.close,
                                "Volume": bar.volume,
                            })
                        
                        if data:
                            df = pd.DataFrame(data)
                            df.set_index("timestamp", inplace=True)
                            results[symbol] = self.normalize_dataframe(df)
                            
                except Exception as e:
                    logger.warning(f"Alpaca: Failed to process {symbol}: {e}")
            
        except Exception as e:
            logger.error(f"Alpaca bars fetch failed: {e}")
        
        return results
    
    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        """
        Fetch fundamental data.
        
        Note: Alpaca doesn't provide fundamentals directly.
        Would need to use another source.
        """
        # Alpaca doesn't provide fundamentals
        return None
    
    def get_metadata(self, symbol: str) -> Optional[AssetMetadata]:
        """Fetch asset metadata."""
        if not self._available:
            return None
        
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import GetAssetsRequest
            from alpaca.trading.enums import AssetClass
            
            trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.paper
            )
            
            asset = trading_client.get_asset(symbol)
            
            asset_type = "EQUITY"
            if asset.asset_class == AssetClass.CRYPTO:
                asset_type = "CRYPTO"
            
            return AssetMetadata(
                symbol=symbol.upper(),
                name=asset.name or symbol,
                asset_type=asset_type,
                exchange=str(asset.exchange),
                currency="USD",
            )
            
        except Exception as e:
            logger.warning(f"Alpaca: Failed to get metadata for {symbol}: {e}")
            return None
    
    def healthcheck(self) -> HealthCheckResult:
        """Check provider health."""
        if not self.api_key or not self.secret_key:
            return HealthCheckResult(
                status="unhealthy",
                message="API credentials not configured",
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
            # Simple test: get recent bars for AAPL
            end = datetime.now()
            start_date = end - timedelta(days=5)
            
            request = self._StockBarsRequest(
                symbol_or_symbols=["AAPL"],
                timeframe=self._TimeFrame.Day,
                start=start_date,
                end=end
            )
            
            bars = self._client.get_stock_bars(request)
            latency = int((time.time() - start) * 1000)
            
            if "AAPL" in bars and len(bars["AAPL"]) > 0:
                return HealthCheckResult(
                    status="healthy",
                    message="OK",
                    latency_ms=latency,
                    timestamp=datetime.now()
                )
            else:
                return HealthCheckResult(
                    status="degraded",
                    message="Empty response",
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
