"""
MarketGPS v7.0 - Providers Module
Data provider implementations with automatic fallback.
"""
from providers.base import DataProvider
from providers.eodhd import EODHDProvider
from providers.yfinance_provider import YFinanceProvider
from core.config import get_config, get_logger

logger = get_logger(__name__)

__all__ = ["DataProvider", "EODHDProvider", "YFinanceProvider", "get_provider"]


def get_provider(name: str = "auto") -> DataProvider:
    """
    Factory function to get a data provider instance.
    
    Args:
        name: Provider name:
            - "auto": Use EODHD if configured, else yfinance
            - "eodhd": Force EODHD
            - "yfinance": Force yfinance
        
    Returns:
        DataProvider instance
    """
    config = get_config()
    
    if name == "auto":
        # Check if EODHD is configured
        if config.eodhd.is_configured:
            logger.info("Using EODHD provider (API key configured)")
            return EODHDProvider()
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
