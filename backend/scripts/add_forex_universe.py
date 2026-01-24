"""
MarketGPS - Add Forex Universe
Adds major currency pairs to the universe using Yahoo Finance.

SAFE: Uses UPSERT - does not delete existing data.

Run: python scripts/add_forex_universe.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import AssetType, Asset
from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# FOREX PAIRS - Major, Minor, and Exotic currency pairs
# Format: Yahoo Finance uses EURUSD=X format
# ═══════════════════════════════════════════════════════════════════════════

# Major Pairs (most liquid)
MAJOR_PAIRS = [
    {"symbol": "EURUSD=X", "name": "Euro / US Dollar", "base": "EUR", "quote": "USD", "category": "Major"},
    {"symbol": "GBPUSD=X", "name": "British Pound / US Dollar", "base": "GBP", "quote": "USD", "category": "Major"},
    {"symbol": "USDJPY=X", "name": "US Dollar / Japanese Yen", "base": "USD", "quote": "JPY", "category": "Major"},
    {"symbol": "USDCHF=X", "name": "US Dollar / Swiss Franc", "base": "USD", "quote": "CHF", "category": "Major"},
    {"symbol": "AUDUSD=X", "name": "Australian Dollar / US Dollar", "base": "AUD", "quote": "USD", "category": "Major"},
    {"symbol": "USDCAD=X", "name": "US Dollar / Canadian Dollar", "base": "USD", "quote": "CAD", "category": "Major"},
    {"symbol": "NZDUSD=X", "name": "New Zealand Dollar / US Dollar", "base": "NZD", "quote": "USD", "category": "Major"},
]

# Minor Pairs (Cross pairs - no USD)
MINOR_PAIRS = [
    {"symbol": "EURGBP=X", "name": "Euro / British Pound", "base": "EUR", "quote": "GBP", "category": "Minor"},
    {"symbol": "EURJPY=X", "name": "Euro / Japanese Yen", "base": "EUR", "quote": "JPY", "category": "Minor"},
    {"symbol": "EURCHF=X", "name": "Euro / Swiss Franc", "base": "EUR", "quote": "CHF", "category": "Minor"},
    {"symbol": "EURAUD=X", "name": "Euro / Australian Dollar", "base": "EUR", "quote": "AUD", "category": "Minor"},
    {"symbol": "EURCAD=X", "name": "Euro / Canadian Dollar", "base": "EUR", "quote": "CAD", "category": "Minor"},
    {"symbol": "EURNZD=X", "name": "Euro / New Zealand Dollar", "base": "EUR", "quote": "NZD", "category": "Minor"},
    {"symbol": "GBPJPY=X", "name": "British Pound / Japanese Yen", "base": "GBP", "quote": "JPY", "category": "Minor"},
    {"symbol": "GBPCHF=X", "name": "British Pound / Swiss Franc", "base": "GBP", "quote": "CHF", "category": "Minor"},
    {"symbol": "GBPAUD=X", "name": "British Pound / Australian Dollar", "base": "GBP", "quote": "AUD", "category": "Minor"},
    {"symbol": "GBPCAD=X", "name": "British Pound / Canadian Dollar", "base": "GBP", "quote": "CAD", "category": "Minor"},
    {"symbol": "GBPNZD=X", "name": "British Pound / New Zealand Dollar", "base": "GBP", "quote": "NZD", "category": "Minor"},
    {"symbol": "CHFJPY=X", "name": "Swiss Franc / Japanese Yen", "base": "CHF", "quote": "JPY", "category": "Minor"},
    {"symbol": "AUDJPY=X", "name": "Australian Dollar / Japanese Yen", "base": "AUD", "quote": "JPY", "category": "Minor"},
    {"symbol": "AUDCHF=X", "name": "Australian Dollar / Swiss Franc", "base": "AUD", "quote": "CHF", "category": "Minor"},
    {"symbol": "AUDCAD=X", "name": "Australian Dollar / Canadian Dollar", "base": "AUD", "quote": "CAD", "category": "Minor"},
    {"symbol": "AUDNZD=X", "name": "Australian Dollar / New Zealand Dollar", "base": "AUD", "quote": "NZD", "category": "Minor"},
    {"symbol": "CADJPY=X", "name": "Canadian Dollar / Japanese Yen", "base": "CAD", "quote": "JPY", "category": "Minor"},
    {"symbol": "CADCHF=X", "name": "Canadian Dollar / Swiss Franc", "base": "CAD", "quote": "CHF", "category": "Minor"},
    {"symbol": "NZDJPY=X", "name": "New Zealand Dollar / Japanese Yen", "base": "NZD", "quote": "JPY", "category": "Minor"},
    {"symbol": "NZDCHF=X", "name": "New Zealand Dollar / Swiss Franc", "base": "NZD", "quote": "CHF", "category": "Minor"},
    {"symbol": "NZDCAD=X", "name": "New Zealand Dollar / Canadian Dollar", "base": "NZD", "quote": "CAD", "category": "Minor"},
]

# Exotic Pairs (Emerging market currencies)
EXOTIC_PAIRS = [
    # USD pairs with emerging markets
    {"symbol": "USDZAR=X", "name": "US Dollar / South African Rand", "base": "USD", "quote": "ZAR", "category": "Exotic"},
    {"symbol": "USDMXN=X", "name": "US Dollar / Mexican Peso", "base": "USD", "quote": "MXN", "category": "Exotic"},
    {"symbol": "USDBRL=X", "name": "US Dollar / Brazilian Real", "base": "USD", "quote": "BRL", "category": "Exotic"},
    {"symbol": "USDTRY=X", "name": "US Dollar / Turkish Lira", "base": "USD", "quote": "TRY", "category": "Exotic"},
    {"symbol": "USDRUB=X", "name": "US Dollar / Russian Ruble", "base": "USD", "quote": "RUB", "category": "Exotic"},
    {"symbol": "USDPLN=X", "name": "US Dollar / Polish Zloty", "base": "USD", "quote": "PLN", "category": "Exotic"},
    {"symbol": "USDHUF=X", "name": "US Dollar / Hungarian Forint", "base": "USD", "quote": "HUF", "category": "Exotic"},
    {"symbol": "USDCZK=X", "name": "US Dollar / Czech Koruna", "base": "USD", "quote": "CZK", "category": "Exotic"},
    {"symbol": "USDSEK=X", "name": "US Dollar / Swedish Krona", "base": "USD", "quote": "SEK", "category": "Exotic"},
    {"symbol": "USDNOK=X", "name": "US Dollar / Norwegian Krone", "base": "USD", "quote": "NOK", "category": "Exotic"},
    {"symbol": "USDDKK=X", "name": "US Dollar / Danish Krone", "base": "USD", "quote": "DKK", "category": "Exotic"},
    {"symbol": "USDSGD=X", "name": "US Dollar / Singapore Dollar", "base": "USD", "quote": "SGD", "category": "Exotic"},
    {"symbol": "USDHKD=X", "name": "US Dollar / Hong Kong Dollar", "base": "USD", "quote": "HKD", "category": "Exotic"},
    {"symbol": "USDCNY=X", "name": "US Dollar / Chinese Yuan", "base": "USD", "quote": "CNY", "category": "Exotic"},
    {"symbol": "USDINR=X", "name": "US Dollar / Indian Rupee", "base": "USD", "quote": "INR", "category": "Exotic"},
    {"symbol": "USDKRW=X", "name": "US Dollar / South Korean Won", "base": "USD", "quote": "KRW", "category": "Exotic"},
    {"symbol": "USDTHB=X", "name": "US Dollar / Thai Baht", "base": "USD", "quote": "THB", "category": "Exotic"},
    {"symbol": "USDIDR=X", "name": "US Dollar / Indonesian Rupiah", "base": "USD", "quote": "IDR", "category": "Exotic"},
    {"symbol": "USDMYR=X", "name": "US Dollar / Malaysian Ringgit", "base": "USD", "quote": "MYR", "category": "Exotic"},
    {"symbol": "USDPHP=X", "name": "US Dollar / Philippine Peso", "base": "USD", "quote": "PHP", "category": "Exotic"},
    {"symbol": "USDTWD=X", "name": "US Dollar / Taiwan Dollar", "base": "USD", "quote": "TWD", "category": "Exotic"},
    {"symbol": "USDILS=X", "name": "US Dollar / Israeli Shekel", "base": "USD", "quote": "ILS", "category": "Exotic"},
    {"symbol": "USDAED=X", "name": "US Dollar / UAE Dirham", "base": "USD", "quote": "AED", "category": "Exotic"},
    {"symbol": "USDSAR=X", "name": "US Dollar / Saudi Riyal", "base": "USD", "quote": "SAR", "category": "Exotic"},
    # African currencies
    {"symbol": "USDNGN=X", "name": "US Dollar / Nigerian Naira", "base": "USD", "quote": "NGN", "category": "Africa Exotic"},
    {"symbol": "USDEGP=X", "name": "US Dollar / Egyptian Pound", "base": "USD", "quote": "EGP", "category": "Africa Exotic"},
    {"symbol": "USDKES=X", "name": "US Dollar / Kenyan Shilling", "base": "USD", "quote": "KES", "category": "Africa Exotic"},
    {"symbol": "USDGHS=X", "name": "US Dollar / Ghanaian Cedi", "base": "USD", "quote": "GHS", "category": "Africa Exotic"},
    {"symbol": "USDMAD=X", "name": "US Dollar / Moroccan Dirham", "base": "USD", "quote": "MAD", "category": "Africa Exotic"},
    {"symbol": "USDTND=X", "name": "US Dollar / Tunisian Dinar", "base": "USD", "quote": "TND", "category": "Africa Exotic"},
    # EUR pairs with emerging markets
    {"symbol": "EURZAR=X", "name": "Euro / South African Rand", "base": "EUR", "quote": "ZAR", "category": "Exotic"},
    {"symbol": "EURTRY=X", "name": "Euro / Turkish Lira", "base": "EUR", "quote": "TRY", "category": "Exotic"},
    {"symbol": "EURPLN=X", "name": "Euro / Polish Zloty", "base": "EUR", "quote": "PLN", "category": "Exotic"},
    {"symbol": "EURHUF=X", "name": "Euro / Hungarian Forint", "base": "EUR", "quote": "HUF", "category": "Exotic"},
    {"symbol": "EURCZK=X", "name": "Euro / Czech Koruna", "base": "EUR", "quote": "CZK", "category": "Exotic"},
    {"symbol": "EURSEK=X", "name": "Euro / Swedish Krona", "base": "EUR", "quote": "SEK", "category": "Exotic"},
    {"symbol": "EURNOK=X", "name": "Euro / Norwegian Krone", "base": "EUR", "quote": "NOK", "category": "Exotic"},
    {"symbol": "EURDKK=X", "name": "Euro / Danish Krone", "base": "EUR", "quote": "DKK", "category": "Exotic"},
]

# All pairs combined
ALL_FOREX_PAIRS = MAJOR_PAIRS + MINOR_PAIRS + EXOTIC_PAIRS


def add_forex_to_universe(store: SQLiteStore, pairs: List[Dict], category_label: str) -> tuple:
    """Add forex pairs to the universe."""
    added = 0
    skipped = 0
    
    for pair in pairs:
        symbol = pair["symbol"]
        # Create a clean asset_id (remove =X suffix)
        clean_symbol = symbol.replace("=X", "")
        asset_id = f"{clean_symbol}.FX"
        
        # Check if already exists
        existing = store.get_asset(asset_id)
        if existing:
            skipped += 1
            continue
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=clean_symbol,
                name=pair["name"],
                asset_type=AssetType.FX,
                market_scope="US_EU",  # Forex is global but we put it in US_EU
                market_code="FX",
                exchange_code="FX",
                exchange="FOREX",
                currency=pair["quote"],  # Quote currency
                country="GLOBAL",
                tier=1 if pair["category"] == "Major" else 2,
                active=True,
                sector=pair["category"],
                industry="Foreign Exchange",
                data_source="YFINANCE",
            )
            store.upsert_asset(asset, market_scope="US_EU")
            added += 1
            logger.info(f"Added FX: {clean_symbol} - {pair['name']}")
        except Exception as e:
            logger.error(f"Failed to add {symbol}: {e}")
    
    return added, skipped


def verify_yfinance_forex():
    """Verify that yfinance can fetch forex data."""
    try:
        import yfinance as yf
    except ImportError:
        logger.error("yfinance not installed")
        return False
    
    print("Testing yfinance Forex connectivity...")
    test_pairs = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]
    
    for symbol in test_pairs:
        try:
            data = yf.download(symbol, period='5d', progress=False)
            if len(data) > 0:
                last_price = data['Close'].iloc[-1]
                print(f"  ✓ {symbol}: {len(data)} bars, last: {last_price:.4f}")
            else:
                print(f"  ✗ {symbol}: No data")
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {e}")
    
    return True


def main():
    """Main function to add Forex pairs to universe."""
    print("=" * 60)
    print("MarketGPS - Add Forex Universe")
    print("=" * 60)
    print(f"Source: Yahoo Finance")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    # Verify yfinance
    verify_yfinance_forex()
    print()
    
    # Add Major Pairs
    print("-" * 60)
    print("Adding Major Currency Pairs...")
    print("-" * 60)
    added, skipped = add_forex_to_universe(store, MAJOR_PAIRS, "Major")
    print(f"Major Pairs: {added} added, {skipped} already existed")
    
    # Add Minor Pairs
    print("-" * 60)
    print("Adding Minor Currency Pairs (Crosses)...")
    print("-" * 60)
    added, skipped = add_forex_to_universe(store, MINOR_PAIRS, "Minor")
    print(f"Minor Pairs: {added} added, {skipped} already existed")
    
    # Add Exotic Pairs
    print("-" * 60)
    print("Adding Exotic Currency Pairs...")
    print("-" * 60)
    added, skipped = add_forex_to_universe(store, EXOTIC_PAIRS, "Exotic")
    print(f"Exotic Pairs: {added} added, {skipped} already existed")
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT asset_type, COUNT(*) as count 
            FROM universe 
            WHERE asset_type = 'FX' AND active = 1
        """)
        fx_count = cursor.fetchone()
        
        cursor = conn.execute("""
            SELECT sector, COUNT(*) as count 
            FROM universe 
            WHERE asset_type = 'FX' AND active = 1
            GROUP BY sector
        """)
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"Total Forex pairs: {fx_count[1] if fx_count else 0}")
    print()
    print("By Category:")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat}: {count}")
    
    print()
    print("✓ Forex universe added successfully!")
    print()
    print("Next: Run scoring for Forex pairs")


if __name__ == "__main__":
    main()
