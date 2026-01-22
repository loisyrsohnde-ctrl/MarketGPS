"""
MarketGPS v7.0 - Providers Module
Data provider implementations with automatic fallback.
"""
from datetime import date
from typing import Optional, Dict, Any, List
import pandas as pd

from providers.base import DataProvider
from providers.eodhd import EODHDProvider, EODHDQuotaExhaustedError
from providers.yfinance_provider import YFinanceProvider
from core.config import get_config, get_logger

logger = get_logger(__name__)

__all__ = ["DataProvider", "EODHDProvider", "YFinanceProvider", "get_provider", "SmartProvider"]


class SmartProvider(DataProvider):
    """
    Smart provider that uses EODHD by default but automatically
    falls back to yfinance when EODHD quota is exhausted (402 error).
    """
    
    def __init__(self):
        """Initialize smart provider with EODHD primary and yfinance fallback."""
        self._eodhd = EODHDProvider()
        self._yfinance = YFinanceProvider()
        self._eodhd_quota_exhausted = False
        
    @property
    def name(self) -> str:
        return "smart"
    
    def _get_active_provider(self) -> DataProvider:
        """Get the currently active provider."""
        if self._eodhd_quota_exhausted:
            return self._yfinance
        return self._eodhd
    
    def fetch_daily_bars(
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch daily bars with automatic fallback.
        """
        # If EODHD quota is already exhausted, use yfinance directly
        if self._eodhd_quota_exhausted:
            return self._yfinance.fetch_daily_bars(symbol, start, end)
        
        try:
            return self._eodhd.fetch_daily_bars(symbol, start, end)
        except EODHDQuotaExhaustedError:
            logger.warning(f"EODHD quota exhausted - switching to yfinance for {symbol}")
            self._eodhd_quota_exhausted = True
            # Convert symbol format from EODHD (AAPL.US) to yfinance (AAPL)
            yf_symbol = symbol.rsplit(".", 1)[0] if "." in symbol else symbol
            return self._yfinance.fetch_daily_bars(yf_symbol, start, end)
        except Exception as e:
            # On any other EODHD error, try yfinance as fallback
            logger.warning(f"EODHD failed for {symbol}, trying yfinance: {e}")
            yf_symbol = symbol.rsplit(".", 1)[0] if "." in symbol else symbol
            return self._yfinance.fetch_daily_bars(yf_symbol, start, end)
    
    def fetch_daily_bars_batch(
        self,
        symbols: List[str],
        start: Optional[date] = None,
        end: Optional[date] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch daily bars for multiple symbols with automatic fallback.
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
        """Fetch fundamentals from EODHD only (yfinance fundamentals not implemented)."""
        if self._eodhd_quota_exhausted:
            return {}
        
        try:
            return self._eodhd.fetch_fundamentals(symbol)
        except EODHDQuotaExhaustedError:
            self._eodhd_quota_exhausted = True
            return {}
        except Exception:
            return {}
    
    def normalize_symbol(self, raw: str, default_exchange: Optional[str] = None) -> str:
        """Normalize symbol to EODHD format."""
        return self._eodhd.normalize_symbol(raw, default_exchange)
    
    def extract_symbol(self, normalized: str) -> str:
        """Extract base symbol from normalized format."""
        return self._eodhd.extract_symbol(normalized)
    
    def reset_fallback(self):
        """Reset the fallback state (e.g., when quota resets)."""
        self._eodhd_quota_exhausted = False
        logger.info("Smart provider fallback state reset")
    
    def healthcheck(self):
        """Check provider health - delegates to active provider."""
        from core.models import ProviderHealth
        from datetime import datetime
        
        if self._eodhd_quota_exhausted:
            # If EODHD quota exhausted, return yfinance health
            return ProviderHealth(
                provider="smart (yfinance fallback)",
                status="degraded",
                message="Using yfinance fallback (EODHD quota exhausted)",
                latency_ms=0,
                last_check=datetime.now()
            )
        
        # Try EODHD healthcheck
        try:
            return self._eodhd.healthcheck()
        except Exception:
            return ProviderHealth(
                provider="smart",
                status="degraded",
                message="EODHD healthcheck failed",
                latency_ms=0,
                last_check=datetime.now()
            )


def get_provider(name: str = "auto") -> DataProvider:
    """
    Factory function to get a data provider instance.
    
    Args:
        name: Provider name:
            - "auto": Use SmartProvider (EODHD with yfinance fallback)
            - "smart": Same as auto
            - "eodhd": Force EODHD only (no fallback)
            - "yfinance": Force yfinance only
        
    Returns:
        DataProvider instance
    """
    config = get_config()
    
    if name in ("auto", "smart"):
        # Check if EODHD is configured
        if config.eodhd.is_configured:
            logger.info("Using SmartProvider (EODHD with yfinance fallback)")
            return SmartProvider()
        else:
            logger.info("Using yfinance provider (EODHD API key not configured)")
            return YFinanceProvider()
    
    providers = {
        "eodhd": EODHDProvider,
        "yfinance": YFinanceProvider,
    }
    
    provider_class = providers.get(name.lower())
    if provider_class is None:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")
    
    return provider_class()
