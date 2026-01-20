"""
MarketGPS - Expand Universe Script
Downloads US and EU stock listings from EODHD and adds them to the universe.
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

# All supported exchanges (US + Europe)
US_EXCHANGES = ["US"]  # Main US exchange on EODHD
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
]

def fetch_exchange_symbols(api_key: str, exchange: str) -> list:
    """Fetch all symbols for an exchange from EODHD."""
    url = f"https://eodhd.com/api/exchange-symbol-list/{exchange}?api_token={api_key}&fmt=json"
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        logger.error(f"Failed to fetch symbols for {exchange}: {e}")
        return []


def filter_equities(symbols: list) -> list:
    """Filter to keep only common stocks and ETFs."""
    filtered = []
    
    for s in symbols:
        symbol_type = s.get("Type", "").upper()
        
        # Keep Common Stock, ETF
        if symbol_type in ["COMMON STOCK", "ETF"]:
            filtered.append(s)
    
    return filtered


def create_asset_from_symbol(symbol_data: dict, exchange: str, market_scope: str = "US_EU") -> Asset:
    """Create an Asset object from EODHD symbol data."""
    symbol = symbol_data.get("Code", "")
    name = symbol_data.get("Name", symbol)
    symbol_type = symbol_data.get("Type", "").upper()
    currency = symbol_data.get("Currency", "USD")
    country = symbol_data.get("Country", "US")
    
    # Map type
    asset_type = AssetType.ETF if "ETF" in symbol_type else AssetType.EQUITY
    
    # Create asset_id
    asset_id = f"{symbol}.{exchange}"
    
    # Map exchange to market_code
    market_code_map = {
        "US": "US",
        "PA": "EU",
        "XETRA": "EU",
        "LSE": "EU",
    }
    market_code = market_code_map.get(exchange, "US")
    
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
        tier=2,  # Default to tier 2 (extended universe)
        priority_level=2,
    )


def main():
    """Main function to expand the universe."""
    config = get_config()
    
    api_key = config.eodhd.api_key
    if not api_key or api_key == "changeme":
        print("ERROR: EODHD API key not configured. Set EODHD_API_KEY in .env")
        return
    
    store = SQLiteStore(config.storage.sqlite_path)
    
    print("=" * 60)
    print("MarketGPS - Expand Universe")
    print("=" * 60)
    print()
    
    total_added = 0
    total_updated = 0
    
    # Process US exchanges
    print("Fetching US stocks...")
    for exchange in US_EXCHANGES:
        print(f"  Fetching {exchange}...")
        symbols = fetch_exchange_symbols(api_key, exchange)
        
        if not symbols:
            print(f"    No symbols found for {exchange}")
            continue
        
        print(f"    Found {len(symbols)} total symbols")
        
        # Filter to equities and ETFs
        equities = filter_equities(symbols)
        print(f"    Filtered to {len(equities)} equities/ETFs")
        
        # No limit - take ALL available stocks
        print(f"    Adding ALL {len(equities)} stocks (no limit)")
        
        # Add to universe
        added = 0
        for sym in equities:
            try:
                asset = create_asset_from_symbol(sym, exchange, "US_EU")
                store.upsert_asset(asset)
                added += 1
            except Exception as e:
                logger.warning(f"Failed to add {sym.get('Code')}: {e}")
        
        print(f"    Added/updated {added} assets")
        total_added += added
        
        time.sleep(1)  # Be nice to API
    
    # Process EU exchanges
    print()
    print("Fetching EU stocks...")
    for exchange in EU_EXCHANGES:
        print(f"  Fetching {exchange}...")
        symbols = fetch_exchange_symbols(api_key, exchange)
        
        if not symbols:
            print(f"    No symbols found for {exchange}")
            continue
        
        print(f"    Found {len(symbols)} total symbols")
        
        # Filter to equities and ETFs
        equities = filter_equities(symbols)
        print(f"    Filtered to {len(equities)} equities/ETFs")
        
        # No limit - take ALL available stocks
        print(f"    Adding ALL {len(equities)} stocks (no limit)")
        
        # Add to universe
        added = 0
        for sym in equities:
            try:
                asset = create_asset_from_symbol(sym, exchange, "US_EU")
                store.upsert_asset(asset)
                added += 1
            except Exception as e:
                logger.warning(f"Failed to add {sym.get('Code')}: {e}")
        
        print(f"    Added/updated {added} assets")
        total_added += added
        
        time.sleep(1)  # Be nice to API
    
    # Get final count
    with store._get_conn() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM universe WHERE market_scope = 'US_EU'")
        final_count = cursor.fetchone()[0]
    
    print()
    print("=" * 60)
    print(f"Universe expansion complete!")
    print(f"  Total US/EU assets: {final_count}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run gating: python -m pipeline.jobs --run-gating --scope US_EU")
    print("  2. Run rotation: python -m pipeline.jobs --run-rotation --scope US_EU")


if __name__ == "__main__":
    main()
