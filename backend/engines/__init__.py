# MarketGPS Real Estate - Tax Engines
# Modular tax calculation engines for different jurisdictions

from .base_engine import BaseTaxEngine
from .fr_lmnp_engine import FRLMNPEngine
from .us_tax_engine import USTaxEngine
from .ca_tax_engine import CanadaTaxEngine

__all__ = [
    "BaseTaxEngine",
    "FRLMNPEngine",
    "USTaxEngine",
    "CanadaTaxEngine",
]
