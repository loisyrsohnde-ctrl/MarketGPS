# Data Providers for MarketGPS Wealth Module
# Real data sources replacing mock data

from .central_bank_rates import CentralBankRatesProvider
from .real_estate_news import RealEstateNewsProvider
from .market_data import MarketDataProvider

__all__ = [
    'CentralBankRatesProvider',
    'RealEstateNewsProvider', 
    'MarketDataProvider',
]
