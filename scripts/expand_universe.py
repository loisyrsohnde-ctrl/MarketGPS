"""
MarketGPS - Expand Universe Script (FULL COVERAGE)
Downloads ALL stocks, ETFs, and bonds from EODHD for US, EU, and Africa markets.
NO LIMITS - fetches everything your EODHD plan allows.
"""
import os
import sys
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore
from core.models import Asset, AssetType

logger = get_logger(__name__)

# ============================================================================
# EXCHANGE CONFIGURATIONS
# ============================================================================

# US Exchanges
US_EXCHANGES = ["US"]  # Main US exchange on EODHD (includes NYSE, NASDAQ, AMEX)

# EU Exchanges (comprehensive list)
EU_EXCHANGES = [
    "PA",      # Euronext Paris
    "XETRA",   # Frankfurt
    "LSE",     # London Stock Exchange
    "AS",      # Euronext Amsterdam
    "BR",      # Euronext Brussels
    "LI",      # Euronext Lisbon
    "MI",      # Borsa Italiana (Milan)
    "MC",      # Bolsa de Madrid
    "SW",      # SIX Swiss Exchange
    "VI",      # Vienna Stock Exchange
    "IR",      # Irish Stock Exchange
    "HE",      # Nasdaq Helsinki
    "ST",      # Nasdaq Stockholm
    "CO",      # Nasdaq Copenhagen
    "OL",      # Oslo Stock Exchange
]

# African Exchanges (from your existing pipeline/africa/exchanges_catalog.py)
AFRICA_EXCHANGES = [
    ("JSE", "ZAR", "AFRICA"),     # Johannesburg Stock Exchange (South Africa)
    ("NGX", "NGN", "AFRICA"),     # Nigerian Stock Exchange (replaces NSE Lagos)
    ("EGX", "EGP", "AFRICA"),     # Egyptian Exchange
    ("NSE", "KES", "AFRICA"),     # Nairobi Securities Exchange (Kenya)
    ("CSE", "MAD", "AFRICA"),     # Casablanca Stock Exchange (Morocco)
    ("BRVM", "XOF", "AFRICA"),    # BRVM (West Africa - 8 countries)
    ("GSE", "GHS", "AFRICA"),     # Ghana Stock Exchange
    ("BVMT", "TND", "AFRICA"),    # Bourse de Tunis
    ("DSE", "TZS", "AFRICA"),     # Dar es Salaam Stock Exchange (Tanzania)
    ("USE", "UGX", "AFRICA"),     # Uganda Securities Exchange
    ("RSE", "RWF", "AFRICA"),     # Rwanda Stock Exchange
    ("ZSE", "ZWL", "AFRICA"),     # Zimbabwe Stock Exchange
    ("BSE", "BWP", "AFRICA"),     # Botswana Stock Exchange
    ("LUSE", "ZMW", "AFRICA"),    # Lusaka Stock Exchange (Zambia)
    ("MSE", "MWK", "AFRICA"),     # Malawi Stock Exchange
    ("SEM", "MUR", "AFRICA"),     # Stock Exchange of Mauritius
    ("BVMAC", "XAF", "AFRICA"),   # BVMAC (Central Africa - 6 countries)
    ("AAE", "ETB", "AFRICA"),     # Addis Ababa Exchange (Ethiopia) - if available
]

# Accepted types (comprehensive)
ACCEPTED_TYPES = [
    "COMMON STOCK",
    "ETF", 
    "BOND",
    "PREFERRED STOCK",
    "REIT",
    "FUND",
]


def fetch_exchange_symbols(api_key: str, exchange: str) -> list:
    """Fetch all symbols for an exchange from EODHD."""
    url = f"https://eodhd.com/api/exchange-symbol-list/{exchange}?api_token={api_key}&fmt=json"
    
    try:
        response = requests.get(url, timeout=120)
        
        if response.status_code == 403:
            logger.warning(f"Exchange {exchange} not available on your plan (403)")
            return []
            
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        return []
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {exchange}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch symbols for {exchange}: {e}")
        return []


def filter_instruments(symbols: list) -> list:
    """Filter to keep stocks, ETFs, bonds, and other investable assets."""
    filtered = []
    
    for s in symbols:
        symbol_type = s.get("Type", "").upper()
        
        # Keep accepted types
        for accepted in ACCEPTED_TYPES:
            if accepted in symbol_type:
                filtered.append(s)
                break
    
    return filtered


def map_asset_type(symbol_type: str) -> AssetType:
    """Map EODHD type to our AssetType."""
    symbol_type = symbol_type.upper()
    
    if "ETF" in symbol_type:
        return AssetType.ETF
    elif "BOND" in symbol_type:
        return AssetType.BOND
    else:
        return AssetType.EQUITY


def create_asset(
    symbol_data: dict, 
    exchange: str, 
    market_scope: str,
    market_code: str,
    default_currency: str = "USD"
) -> Asset:
    """Create an Asset object from EODHD symbol data."""
    symbol = symbol_data.get("Code", "")
    name = symbol_data.get("Name", symbol)
    symbol_type = symbol_data.get("Type", "")
    currency = symbol_data.get("Currency") or default_currency
    country = symbol_data.get("Country", "")
    
    # Map type
    asset_type = map_asset_type(symbol_type)
    
    # Create asset_id (ticker.exchange format)
    asset_id = f"{symbol}.{exchange}"
    
    return Asset(
        asset_id=asset_id,
        symbol=symbol,
        name=name[:200] if name else symbol,  # Truncate long names
        asset_type=asset_type,
        market_scope=market_scope,
        market_code=market_code,
        exchange=exchange,
        currency=currency,
        country=country,
        active=True,
        tier=2,  # Extended universe
        priority_level=2,
    )


def process_exchange(
    store: SQLiteStore,
    api_key: str,
    exchange: str,
    market_scope: str,
    market_code: str,
    default_currency: str = "USD",
    limit: Optional[int] = None
) -> int:
    """Process a single exchange and add to universe. Returns count added."""
    
    print(f"  Fetching {exchange}...")
    symbols = fetch_exchange_symbols(api_key, exchange)
    
    if not symbols:
        print(f"    No symbols found for {exchange}")
        return 0
    
    print(f"    Found {len(symbols)} total symbols")
    
    # Filter to investable instruments
    instruments = filter_instruments(symbols)
    print(f"    Filtered to {len(instruments)} investable instruments")
    
    # Apply limit if specified
    if limit and len(instruments) > limit:
        instruments = instruments[:limit]
        print(f"    Limited to {len(instruments)} instruments")
    
    # Add to universe
    added = 0
    errors = 0
    
    for sym in instruments:
        try:
            asset = create_asset(
                sym, 
                exchange, 
                market_scope, 
                market_code,
                default_currency
            )
            store.upsert_asset(asset)
            added += 1
        except Exception as e:
            errors += 1
            if errors <= 5:  # Only log first 5 errors per exchange
                logger.warning(f"Failed to add {sym.get('Code')}: {e}")
    
    print(f"    Added/updated {added} assets ({errors} errors)")
    return added


def main():
    """Main function to expand the universe with ALL available assets."""
    config = get_config()
    
    api_key = config.eodhd.api_key
    if not api_key or api_key == "changeme":
        print("ERROR: EODHD API key not configured. Set EODHD_API_KEY in .env")
        sys.exit(1)
    
    store = SQLiteStore(config.storage.sqlite_path)
    
    print("=" * 70)
    print("MarketGPS - FULL Universe Expansion")
    print("Fetching ALL available stocks, ETFs, and bonds from EODHD")
    print("=" * 70)
    print()
    
    total_added = 0
    
    # ========================================================================
    # 1. US EXCHANGES (no limit)
    # ========================================================================
    print("=" * 50)
    print("US MARKET")
    print("=" * 50)
    
    for exchange in US_EXCHANGES:
        added = process_exchange(
            store=store,
            api_key=api_key,
            exchange=exchange,
            market_scope="US_EU",
            market_code="US",
            default_currency="USD",
            limit=None  # NO LIMIT - fetch all
        )
        total_added += added
        time.sleep(1)  # Rate limiting
    
    # ========================================================================
    # 2. EU EXCHANGES (no limit)
    # ========================================================================
    print()
    print("=" * 50)
    print("EU MARKET")
    print("=" * 50)
    
    eu_currency_map = {
        "PA": "EUR", "AS": "EUR", "BR": "EUR", "LI": "EUR", "MI": "EUR",
        "MC": "EUR", "VI": "EUR", "IR": "EUR", "HE": "EUR",
        "XETRA": "EUR",
        "LSE": "GBP",
        "SW": "CHF",
        "ST": "SEK", "CO": "DKK", "OL": "NOK",
    }
    
    for exchange in EU_EXCHANGES:
        currency = eu_currency_map.get(exchange, "EUR")
        added = process_exchange(
            store=store,
            api_key=api_key,
            exchange=exchange,
            market_scope="US_EU",
            market_code="EU",
            default_currency=currency,
            limit=None  # NO LIMIT
        )
        total_added += added
        time.sleep(1)
    
    # ========================================================================
    # 3. AFRICAN EXCHANGES (no limit)
    # ========================================================================
    print()
    print("=" * 50)
    print("AFRICAN MARKET")
    print("=" * 50)
    
    for exchange, currency, scope in AFRICA_EXCHANGES:
        added = process_exchange(
            store=store,
            api_key=api_key,
            exchange=exchange,
            market_scope="AFRICA",
            market_code="AF",
            default_currency=currency,
            limit=None  # NO LIMIT
        )
        total_added += added
        time.sleep(1)
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print()
    print("=" * 70)
    print("UNIVERSE EXPANSION COMPLETE!")
    print("=" * 70)
    
    # Get final counts
    with store._get_conn() as conn:
        cursor = conn.execute("SELECT market_scope, COUNT(*) FROM universe WHERE active = 1 GROUP BY market_scope")
        counts = dict(cursor.fetchall())
        
        cursor = conn.execute("SELECT asset_type, COUNT(*) FROM universe WHERE active = 1 GROUP BY asset_type")
        type_counts = dict(cursor.fetchall())
        
        cursor = conn.execute("SELECT COUNT(*) FROM universe WHERE active = 1")
        total = cursor.fetchone()[0]
    
    print()
    print(f"  Total assets added: {total_added}")
    print()
    print("  By Market Scope:")
    for scope, count in counts.items():
        print(f"    {scope}: {count:,} assets")
    print()
    print("  By Asset Type:")
    for atype, count in type_counts.items():
        print(f"    {atype}: {count:,}")
    print()
    print(f"  GRAND TOTAL: {total:,} assets in universe")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run gating US/EU:  python -m pipeline.jobs --run-gating --scope US_EU")
    print("  2. Run rotation US/EU: python -m pipeline.jobs --run-rotation --scope US_EU --mode daily_full")
    print("  3. Run gating Africa:  python -m pipeline.jobs --run-gating --scope AFRICA")
    print("  4. Run rotation Africa: python -m pipeline.jobs --run-rotation --scope AFRICA --mode daily_full")


if __name__ == "__main__":
    main()
