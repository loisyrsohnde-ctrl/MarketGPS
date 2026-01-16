"""
MarketGPS v14.0 - African Exchanges Catalog
Complete reference for African stock exchanges with data provider mappings.

Exchanges covered:
- JSE (South Africa) - Tier 1, highest liquidity
- NGX (Nigeria) - Tier 2, growing market
- EGX (Egypt) - Tier 2, large market
- NSE Kenya (Kenya) - Tier 2
- BRVM (West Africa) - Tier 3, multiple countries
- BVMAC (Central Africa) - Tier 3
- CSE (Morocco) - Tier 2
- BVMT (Tunisia) - Tier 3
- GSE (Ghana) - Tier 3
- DSE (Tanzania) - Tier 3
- USE (Uganda) - Tier 3
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set


# ═══════════════════════════════════════════════════════════════════════════
# EXCHANGE CONFIGURATION DATACLASS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ExchangeInfo:
    """African stock exchange configuration."""
    code: str                    # Our internal code
    name: str                    # Full name
    country: str                 # ISO country code
    currency: str                # Primary currency
    eodhd_code: str              # EODHD API exchange code
    mic: Optional[str]           # ISO Market Identifier Code
    timezone: str                # Timezone
    trading_days: List[str]      # Trading days (mon-fri typical)
    tier: int                    # Liquidity tier (1=high, 2=medium, 3=low)
    active: bool                 # Whether to process
    min_liquidity_usd: float     # Minimum ADV in USD
    stale_days_threshold: int    # Days before data considered stale
    data_source_priority: List[str]  # Provider priority


# ═══════════════════════════════════════════════════════════════════════════
# AFRICAN EXCHANGES CATALOG
# ═══════════════════════════════════════════════════════════════════════════

AFRICA_EXCHANGES: Dict[str, ExchangeInfo] = {
    # ─────────────────────────────────────────────────────────────────────
    # TIER 1 - High Liquidity
    # ─────────────────────────────────────────────────────────────────────
    "JSE": ExchangeInfo(
        code="JSE",
        name="Johannesburg Stock Exchange",
        country="ZA",
        currency="ZAR",
        eodhd_code="JSE",
        mic="XJSE",
        timezone="Africa/Johannesburg",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=1,
        active=True,
        min_liquidity_usd=100_000,
        stale_days_threshold=5,
        data_source_priority=["EODHD", "yfinance"]
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # TIER 2 - Medium Liquidity
    # ─────────────────────────────────────────────────────────────────────
    "NGX": ExchangeInfo(
        code="NGX",
        name="Nigerian Exchange Group",
        country="NG",
        currency="NGN",
        eodhd_code="NG",
        mic="XNSA",
        timezone="Africa/Lagos",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=2,
        active=True,
        min_liquidity_usd=50_000,
        stale_days_threshold=7,
        data_source_priority=["EODHD"]
    ),
    "EGX": ExchangeInfo(
        code="EGX",
        name="Egyptian Exchange",
        country="EG",
        currency="EGP",
        eodhd_code="CA",  # Cairo
        mic="XCAI",
        timezone="Africa/Cairo",
        trading_days=["sun", "mon", "tue", "wed", "thu"],
        tier=2,
        active=True,
        min_liquidity_usd=50_000,
        stale_days_threshold=7,
        data_source_priority=["EODHD"]
    ),
    "NSE": ExchangeInfo(
        code="NSE",
        name="Nairobi Securities Exchange",
        country="KE",
        currency="KES",
        eodhd_code="NBO",  # Nairobi
        mic="XNAI",
        timezone="Africa/Nairobi",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=2,
        active=True,
        min_liquidity_usd=30_000,
        stale_days_threshold=7,
        data_source_priority=["EODHD"]
    ),
    "CSE": ExchangeInfo(
        code="CSE",
        name="Casablanca Stock Exchange",
        country="MA",
        currency="MAD",
        eodhd_code="BC",  # Casablanca
        mic="XCAS",
        timezone="Africa/Casablanca",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=2,
        active=True,
        min_liquidity_usd=40_000,
        stale_days_threshold=7,
        data_source_priority=["EODHD"]
    ),
    
    # ─────────────────────────────────────────────────────────────────────
    # TIER 3 - Lower Liquidity / Regional
    # ─────────────────────────────────────────────────────────────────────
    "BRVM": ExchangeInfo(
        code="BRVM",
        name="Bourse Régionale des Valeurs Mobilières",
        country="CI",  # Côte d'Ivoire (HQ)
        currency="XOF",
        eodhd_code="BRVM",
        mic="XBRV",
        timezone="Africa/Abidjan",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=True,
        min_liquidity_usd=20_000,
        stale_days_threshold=10,
        data_source_priority=["EODHD"]
    ),
    "BVMAC": ExchangeInfo(
        code="BVMAC",
        name="Bourse des Valeurs Mobilières de l'Afrique Centrale",
        country="CM",  # Cameroon (HQ)
        currency="XAF",
        eodhd_code="BVMAC",
        mic=None,
        timezone="Africa/Douala",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=False,  # Limited data availability
        min_liquidity_usd=10_000,
        stale_days_threshold=14,
        data_source_priority=["EODHD", "manual"]
    ),
    "GSE": ExchangeInfo(
        code="GSE",
        name="Ghana Stock Exchange",
        country="GH",
        currency="GHS",
        eodhd_code="GH",
        mic="XGHA",
        timezone="Africa/Accra",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=True,
        min_liquidity_usd=15_000,
        stale_days_threshold=10,
        data_source_priority=["EODHD"]
    ),
    "BVMT": ExchangeInfo(
        code="BVMT",
        name="Bourse de Tunis",
        country="TN",
        currency="TND",
        eodhd_code="TN",
        mic="XTUN",
        timezone="Africa/Tunis",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=True,
        min_liquidity_usd=20_000,
        stale_days_threshold=10,
        data_source_priority=["EODHD"]
    ),
    "DSE": ExchangeInfo(
        code="DSE",
        name="Dar es Salaam Stock Exchange",
        country="TZ",
        currency="TZS",
        eodhd_code="DSE",
        mic="XDAR",
        timezone="Africa/Dar_es_Salaam",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=False,
        min_liquidity_usd=10_000,
        stale_days_threshold=14,
        data_source_priority=["EODHD"]
    ),
    "USE": ExchangeInfo(
        code="USE",
        name="Uganda Securities Exchange",
        country="UG",
        currency="UGX",
        eodhd_code="UG",
        mic="XUGA",
        timezone="Africa/Kampala",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=False,
        min_liquidity_usd=10_000,
        stale_days_threshold=14,
        data_source_priority=["EODHD"]
    ),
    "RSE": ExchangeInfo(
        code="RSE",
        name="Rwanda Stock Exchange",
        country="RW",
        currency="RWF",
        eodhd_code="RW",
        mic=None,
        timezone="Africa/Kigali",
        trading_days=["mon", "tue", "wed", "thu", "fri"],
        tier=3,
        active=False,
        min_liquidity_usd=5_000,
        stale_days_threshold=14,
        data_source_priority=["EODHD", "manual"]
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# CURRENCY INFORMATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class CurrencyInfo:
    """Currency information for FX risk calculation."""
    code: str
    name: str
    countries: List[str]
    volatility_rating: float  # 0-1, higher = more volatile
    is_hard_currency: bool
    usd_rate_source: str  # Where to get USD conversion


CURRENCY_INFO: Dict[str, CurrencyInfo] = {
    "ZAR": CurrencyInfo(
        code="ZAR",
        name="South African Rand",
        countries=["ZA"],
        volatility_rating=0.35,
        is_hard_currency=False,
        usd_rate_source="USDZAR.FOREX"
    ),
    "NGN": CurrencyInfo(
        code="NGN",
        name="Nigerian Naira",
        countries=["NG"],
        volatility_rating=0.60,
        is_hard_currency=False,
        usd_rate_source="USDNGN.FOREX"
    ),
    "EGP": CurrencyInfo(
        code="EGP",
        name="Egyptian Pound",
        countries=["EG"],
        volatility_rating=0.55,
        is_hard_currency=False,
        usd_rate_source="USDEGP.FOREX"
    ),
    "KES": CurrencyInfo(
        code="KES",
        name="Kenyan Shilling",
        countries=["KE"],
        volatility_rating=0.40,
        is_hard_currency=False,
        usd_rate_source="USDKES.FOREX"
    ),
    "GHS": CurrencyInfo(
        code="GHS",
        name="Ghanaian Cedi",
        countries=["GH"],
        volatility_rating=0.55,
        is_hard_currency=False,
        usd_rate_source="USDGHS.FOREX"
    ),
    "XOF": CurrencyInfo(
        code="XOF",
        name="CFA Franc BCEAO",
        countries=["CI", "SN", "BF", "ML", "NE", "TG", "BJ", "GW"],
        volatility_rating=0.15,  # Pegged to EUR
        is_hard_currency=False,
        usd_rate_source="USDXOF.FOREX"
    ),
    "XAF": CurrencyInfo(
        code="XAF",
        name="CFA Franc BEAC",
        countries=["CM", "CF", "CG", "GA", "GQ", "TD"],
        volatility_rating=0.15,  # Pegged to EUR
        is_hard_currency=False,
        usd_rate_source="USDXAF.FOREX"
    ),
    "MAD": CurrencyInfo(
        code="MAD",
        name="Moroccan Dirham",
        countries=["MA"],
        volatility_rating=0.20,
        is_hard_currency=False,
        usd_rate_source="USDMAD.FOREX"
    ),
    "TND": CurrencyInfo(
        code="TND",
        name="Tunisian Dinar",
        countries=["TN"],
        volatility_rating=0.30,
        is_hard_currency=False,
        usd_rate_source="USDTND.FOREX"
    ),
    "TZS": CurrencyInfo(
        code="TZS",
        name="Tanzanian Shilling",
        countries=["TZ"],
        volatility_rating=0.35,
        is_hard_currency=False,
        usd_rate_source="USDTZS.FOREX"
    ),
    "UGX": CurrencyInfo(
        code="UGX",
        name="Ugandan Shilling",
        countries=["UG"],
        volatility_rating=0.40,
        is_hard_currency=False,
        usd_rate_source="USDUGX.FOREX"
    ),
    "RWF": CurrencyInfo(
        code="RWF",
        name="Rwandan Franc",
        countries=["RW"],
        volatility_rating=0.25,
        is_hard_currency=False,
        usd_rate_source="USDRWF.FOREX"
    ),
    # Reference currencies
    "USD": CurrencyInfo(
        code="USD",
        name="US Dollar",
        countries=["US"],
        volatility_rating=0.0,
        is_hard_currency=True,
        usd_rate_source=None
    ),
    "EUR": CurrencyInfo(
        code="EUR",
        name="Euro",
        countries=["EU"],
        volatility_rating=0.10,
        is_hard_currency=True,
        usd_rate_source="EURUSD.FOREX"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_exchange_info(code: str) -> Optional[ExchangeInfo]:
    """Get exchange info by code."""
    return AFRICA_EXCHANGES.get(code.upper())


def get_supported_exchanges(active_only: bool = True) -> List[str]:
    """Get list of supported exchange codes."""
    if active_only:
        return [code for code, info in AFRICA_EXCHANGES.items() if info.active]
    return list(AFRICA_EXCHANGES.keys())


def is_valid_exchange(code: str) -> bool:
    """Check if exchange code is valid."""
    return code.upper() in AFRICA_EXCHANGES


def get_valid_market_codes() -> Set[str]:
    """Get set of all valid market codes for AFRICA."""
    codes = set()
    for info in AFRICA_EXCHANGES.values():
        codes.add(info.code)
        codes.add(info.country)
    return codes


def get_currency_volatility(currency: str) -> float:
    """Get currency volatility rating (0-1)."""
    info = CURRENCY_INFO.get(currency.upper())
    return info.volatility_rating if info else 0.50  # Default to medium


def is_hard_currency(currency: str) -> bool:
    """Check if currency is a hard currency."""
    info = CURRENCY_INFO.get(currency.upper())
    return info.is_hard_currency if info else False


def get_exchange_by_eodhd_code(eodhd_code: str) -> Optional[ExchangeInfo]:
    """Find exchange by EODHD code."""
    for info in AFRICA_EXCHANGES.values():
        if info.eodhd_code == eodhd_code:
            return info
    return None


def get_min_liquidity_for_exchange(code: str) -> float:
    """Get minimum liquidity requirement for an exchange."""
    info = AFRICA_EXCHANGES.get(code.upper())
    return info.min_liquidity_usd if info else 50_000


def get_stale_threshold_for_exchange(code: str) -> int:
    """Get stale data threshold in days for an exchange."""
    info = AFRICA_EXCHANGES.get(code.upper())
    return info.stale_days_threshold if info else 7


# ═══════════════════════════════════════════════════════════════════════════
# BRVM COUNTRY MAPPING (Multiple countries in one exchange)
# ═══════════════════════════════════════════════════════════════════════════

BRVM_COUNTRIES = {
    "CI": "Côte d'Ivoire",
    "SN": "Senegal",
    "BF": "Burkina Faso",
    "ML": "Mali",
    "NE": "Niger",
    "TG": "Togo",
    "BJ": "Benin",
    "GW": "Guinea-Bissau"
}

BVMAC_COUNTRIES = {
    "CM": "Cameroon",
    "CF": "Central African Republic",
    "CG": "Republic of Congo",
    "GA": "Gabon",
    "GQ": "Equatorial Guinea",
    "TD": "Chad"
}
