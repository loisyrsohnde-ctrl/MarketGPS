"""
MarketGPS - Expand Universe Script (FULL)
Downloads ALL available instruments from EODHD:
- US stocks, ETFs, bonds
- EU stocks, ETFs, bonds (all exchanges)
- Africa stocks (JSE, NGX, EGX, BRVM)
"""
import os
import sys
import requests
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore
from core.models import Asset, AssetType

logger = get_logger(__name__)

# ============================================================================
# EXCHANGE CONFIGURATION
# ============================================================================

# US exchanges
US_EXCHANGES = ["US"]

# European exchanges
EU_EXCHANGES = [
    "PA",      # Paris (Euronext Paris)
    "XETRA",   # Frankfurt (Deutsche Börse)
    "LSE",     # London Stock Exchange
    "AS",      # Amsterdam (Euronext)
    "BR",      # Brussels (Euronext)
    "MI",      # Milan (Borsa Italiana)
    "MC",      # Madrid (BME)
    "SW",      # Swiss Exchange
    "VI",      # Vienna
    "CO",      # Copenhagen
    "HE",      # Helsinki
    "ST",      # Stockholm
    "OL",      # Oslo
    "IR",      # Ireland
    "LU",      # Luxembourg
    "WAR",     # Warsaw
    "AT",      # Athens
    "LIS",     # Lisbon
    "IS",      # Istanbul
]

# African exchanges
AFRICA_EXCHANGES = [
    "JSE",     # Johannesburg (South Africa)
    "NGX",     # Nigeria (Nigerian Exchange)
    # Note: EODHD uses different codes, we'll try alternatives
]

# Alternative Africa exchange codes (EODHD may use different names)
AFRICA_EXCHANGE_ALTERNATIVES = {
    "JSE": ["JSE", "XJSE"],
    "NGX": ["NGX", "NG", "NGSE"],
    "EGX": ["EGX", "CA", "CASE"],  # Cairo/Egypt
    "BRVM": ["BRVM"],  # West Africa
}

# Asset types to include (map EODHD types to our AssetType)
ASSET_TYPE_MAP = {
    "COMMON STOCK": AssetType.EQUITY,
    "PREFERRED STOCK": AssetType.EQUITY,
    "ETF": AssetType.ETF,
    "FUND": AssetType.ETF,
    "MUTUAL FUND": AssetType.ETF,
    "BOND": AssetType.BOND,
    "GOVERNMENT BOND": AssetType.BOND,
    "CORPORATE BOND": AssetType.BOND,
    "INDEX": AssetType.INDEX,
    "REIT": AssetType.EQUITY,  # Treat REITs as equity
}

# Types to EXCLUDE
EXCLUDED_TYPES = [
    "CURRENCY",
    "CRYPTOCURRENCY",
    "WARRANT",
    "RIGHT",
    "STRUCTURED PRODUCT",
    "CERTIFICATE",
]


def fetch_exchange_symbols(api_key: str, exchange: str) -> list:
    """Fetch all symbols for an exchange from EODHD."""
    url = f"https://eodhd.com/api/exchange-symbol-list/{exchange}?api_token={api_key}&fmt=json"
    
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"Failed to fetch symbols for {exchange}: {e}")
        return []


def filter_instruments(symbols: list) -> list:
    """Filter to keep tradeable instruments (stocks, ETFs, bonds)."""
    filtered = []
    
    for s in symbols:
        symbol_type = s.get("Type", "").upper()
        
        # Skip excluded types
        skip = False
        for excluded in EXCLUDED_TYPES:
            if excluded in symbol_type:
                skip = True
                break
        
        if not skip:
            # Check if it's a type we want
            for known_type in ASSET_TYPE_MAP.keys():
                if known_type in symbol_type:
                    filtered.append(s)
                    break
    
    return filtered


def get_asset_type(symbol_type: str) -> AssetType:
    """Map EODHD type to our AssetType."""
    symbol_type = symbol_type.upper()
    
    for known_type, asset_type in ASSET_TYPE_MAP.items():
        if known_type in symbol_type:
            return asset_type
    
    return AssetType.EQUITY  # Default to equity


def get_market_code(exchange: str) -> str:
    """Get market code from exchange."""
    if exchange in US_EXCHANGES:
        return "US"
    elif exchange in EU_EXCHANGES:
        return "EU"
    else:
        return "AFRICA"


def get_market_scope(exchange: str) -> str:
    """Get market scope from exchange."""
    if exchange in US_EXCHANGES or exchange in EU_EXCHANGES:
        return "US_EU"
    else:
        return "AFRICA"


def create_asset_from_symbol(symbol_data: dict, exchange: str) -> Asset:
    """Create an Asset object from EODHD symbol data."""
    symbol = symbol_data.get("Code", "")
    name = symbol_data.get("Name", symbol)
    symbol_type = symbol_data.get("Type", "").upper()
    currency = symbol_data.get("Currency", "USD")
    country = symbol_data.get("Country", "")
    
    # Get asset type
    asset_type = get_asset_type(symbol_type)
    
    # Create asset_id
    asset_id = f"{symbol}.{exchange}"
    
    # Get market info
    market_code = get_market_code(exchange)
    market_scope = get_market_scope(exchange)
    
    return Asset(
        asset_id=asset_id,
        symbol=symbol,
        name=name[:200] if name else symbol,
        asset_type=asset_type,
        market_scope=market_scope,
        market_code=market_code,
        exchange=exchange,
        currency=currency,
        country=country,
        active=True,
        tier=2,
        priority_level=2,
    )


def process_exchange(api_key: str, exchange: str, store: SQLiteStore) -> int:
    """Process a single exchange and return count of added assets."""
    print(f"  Fetching {exchange}...")
    symbols = fetch_exchange_symbols(api_key, exchange)
    
    if not symbols:
        print(f"    No symbols found for {exchange}")
        return 0
    
    print(f"    Found {len(symbols)} total symbols")
    
    # Filter instruments
    instruments = filter_instruments(symbols)
    print(f"    Filtered to {len(instruments)} tradeable instruments")
    
    # Add to universe
    added = 0
    for sym in instruments:
        try:
            asset = create_asset_from_symbol(sym, exchange)
            store.upsert_asset(asset)
            added += 1
        except Exception as e:
            logger.warning(f"Failed to add {sym.get('Code')}: {e}")
    
    print(f"    Added/updated {added} assets")
    return added


def main():
    """Main function to expand the universe with ALL available instruments."""
    config = get_config()
    
    api_key = config.eodhd.api_key
    if not api_key or api_key == "changeme":
        print("ERROR: EODHD API key not configured. Set EODHD_API_KEY in .env")
        return
    
    store = SQLiteStore(config.storage.sqlite_path)
    
    print("=" * 70)
    print("MarketGPS - FULL Universe Expansion")
    print("=" * 70)
    print()
    print("This will download ALL available instruments from your EODHD plan:")
    print("  - US: Stocks, ETFs, Bonds")
    print("  - Europe: All major exchanges (15+)")
    print("  - Africa: JSE, NGX, EGX, BRVM")
    print()
    
    total_added = 0
    
    # =========================================================================
    # US EXCHANGES
    # =========================================================================
    print("=" * 70)
    print("FETCHING US INSTRUMENTS")
    print("=" * 70)
    
    for exchange in US_EXCHANGES:
        added = process_exchange(api_key, exchange, store)
        total_added += added
        time.sleep(1)
    
    # =========================================================================
    # EU EXCHANGES
    # =========================================================================
    print()
    print("=" * 70)
    print("FETCHING EU INSTRUMENTS")
    print("=" * 70)
    
    for exchange in EU_EXCHANGES:
        added = process_exchange(api_key, exchange, store)
        total_added += added
        time.sleep(1)
    
    # =========================================================================
    # AFRICA EXCHANGES
    # =========================================================================
    print()
    print("=" * 70)
    print("FETCHING AFRICA INSTRUMENTS")
    print("=" * 70)
    
    # Try different exchange codes for Africa
    for base_exchange, alternatives in AFRICA_EXCHANGE_ALTERNATIVES.items():
        for exchange in alternatives:
            added = process_exchange(api_key, exchange, store)
            if added > 0:
                total_added += added
                break  # Found working code, move to next exchange
            time.sleep(0.5)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print("UNIVERSE EXPANSION COMPLETE")
    print("=" * 70)
    
    # Get final counts
    with store._get_conn() as conn:
        cursor = conn.execute("SELECT market_scope, COUNT(*) FROM universe GROUP BY market_scope")
        counts = dict(cursor.fetchall())
        
        cursor = conn.execute("SELECT asset_type, COUNT(*) FROM universe GROUP BY asset_type")
        type_counts = dict(cursor.fetchall())
        
        cursor = conn.execute("SELECT COUNT(*) FROM universe")
        total = cursor.fetchone()[0]
    
    print()
    print("By Market Scope:")
    for scope, count in counts.items():
        print(f"  {scope}: {count:,} assets")
    
    print()
    print("By Asset Type:")
    for atype, count in type_counts.items():
        print(f"  {atype}: {count:,} assets")
    
    print()
    print(f"TOTAL: {total:,} assets")
    print()
    print("=" * 70)
    print("Next steps:")
    print("  1. Run US/EU pipeline:")
    print("     python -m pipeline.jobs --full-pipeline --scope US_EU --production --mode daily_full")
    print()
    print("  2. Run Africa pipeline (if applicable):")
    print("     python -m pipeline.jobs --full-pipeline --scope AFRICA --production --mode daily_full")
    print("=" * 70)


if __name__ == "__main__":
    main()
