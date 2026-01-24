"""
MarketGPS - Add Commodities Universe
Adds major commodities (via ETFs and Futures proxies) to the universe.

SAFE: Uses UPSERT - does not delete existing data.

Run: python scripts/add_commodities_universe.py
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
# COMMODITIES - Using ETFs as liquid proxies
# ═══════════════════════════════════════════════════════════════════════════

PRECIOUS_METALS = [
    {"symbol": "GLD", "name": "SPDR Gold Shares", "commodity": "Gold", "category": "Precious Metals"},
    {"symbol": "SLV", "name": "iShares Silver Trust", "commodity": "Silver", "category": "Precious Metals"},
    {"symbol": "PPLT", "name": "abrdn Platinum ETF", "commodity": "Platinum", "category": "Precious Metals"},
    {"symbol": "PALL", "name": "abrdn Palladium ETF", "commodity": "Palladium", "category": "Precious Metals"},
    {"symbol": "IAU", "name": "iShares Gold Trust", "commodity": "Gold", "category": "Precious Metals"},
    {"symbol": "SGOL", "name": "abrdn Physical Gold Shares ETF", "commodity": "Gold", "category": "Precious Metals"},
    {"symbol": "SIVR", "name": "abrdn Physical Silver Shares ETF", "commodity": "Silver", "category": "Precious Metals"},
    {"symbol": "GLTR", "name": "abrdn Physical Precious Metals Basket ETF", "commodity": "Mixed Metals", "category": "Precious Metals"},
]

ENERGY = [
    {"symbol": "USO", "name": "United States Oil Fund", "commodity": "Crude Oil WTI", "category": "Energy"},
    {"symbol": "BNO", "name": "United States Brent Oil Fund", "commodity": "Crude Oil Brent", "category": "Energy"},
    {"symbol": "UNG", "name": "United States Natural Gas Fund", "commodity": "Natural Gas", "category": "Energy"},
    {"symbol": "UGA", "name": "United States Gasoline Fund", "commodity": "Gasoline", "category": "Energy"},
    {"symbol": "DBO", "name": "Invesco DB Oil Fund", "commodity": "Crude Oil", "category": "Energy"},
    {"symbol": "OIL", "name": "iPath S&P GSCI Crude Oil TR ETN", "commodity": "Crude Oil", "category": "Energy"},
    {"symbol": "GAZ", "name": "iPath Bloomberg Natural Gas ETN", "commodity": "Natural Gas", "category": "Energy"},
    {"symbol": "XLE", "name": "Energy Select Sector SPDR", "commodity": "Energy Sector", "category": "Energy"},
    {"symbol": "VDE", "name": "Vanguard Energy ETF", "commodity": "Energy Sector", "category": "Energy"},
    {"symbol": "XOP", "name": "SPDR S&P Oil & Gas Exploration ETF", "commodity": "Oil & Gas", "category": "Energy"},
]

AGRICULTURE = [
    {"symbol": "DBA", "name": "Invesco DB Agriculture Fund", "commodity": "Agriculture Basket", "category": "Agriculture"},
    {"symbol": "CORN", "name": "Teucrium Corn Fund", "commodity": "Corn", "category": "Agriculture"},
    {"symbol": "WEAT", "name": "Teucrium Wheat Fund", "commodity": "Wheat", "category": "Agriculture"},
    {"symbol": "SOYB", "name": "Teucrium Soybean Fund", "commodity": "Soybeans", "category": "Agriculture"},
    {"symbol": "CANE", "name": "Teucrium Sugar Fund", "commodity": "Sugar", "category": "Agriculture"},
    {"symbol": "JO", "name": "iPath Bloomberg Coffee ETN", "commodity": "Coffee", "category": "Agriculture"},
    {"symbol": "NIB", "name": "iPath Bloomberg Cocoa ETN", "commodity": "Cocoa", "category": "Agriculture"},
    {"symbol": "COW", "name": "iPath Bloomberg Livestock ETN", "commodity": "Livestock", "category": "Agriculture"},
    {"symbol": "BAL", "name": "iPath Bloomberg Cotton ETN", "commodity": "Cotton", "category": "Agriculture"},
    {"symbol": "MOO", "name": "VanEck Agribusiness ETF", "commodity": "Agribusiness", "category": "Agriculture"},
]

INDUSTRIAL_METALS = [
    {"symbol": "CPER", "name": "United States Copper Index Fund", "commodity": "Copper", "category": "Industrial Metals"},
    {"symbol": "DBB", "name": "Invesco DB Base Metals Fund", "commodity": "Base Metals Basket", "category": "Industrial Metals"},
    {"symbol": "JJC", "name": "iPath Bloomberg Copper ETN", "commodity": "Copper", "category": "Industrial Metals"},
    {"symbol": "JJN", "name": "iPath Bloomberg Nickel ETN", "commodity": "Nickel", "category": "Industrial Metals"},
    {"symbol": "JJU", "name": "iPath Bloomberg Aluminum ETN", "commodity": "Aluminum", "category": "Industrial Metals"},
    {"symbol": "COPX", "name": "Global X Copper Miners ETF", "commodity": "Copper Miners", "category": "Industrial Metals"},
    {"symbol": "REMX", "name": "VanEck Rare Earth/Strategic Metals ETF", "commodity": "Rare Earth", "category": "Industrial Metals"},
    {"symbol": "LIT", "name": "Global X Lithium & Battery Tech ETF", "commodity": "Lithium", "category": "Industrial Metals"},
    {"symbol": "PAVE", "name": "Global X US Infrastructure Development ETF", "commodity": "Infrastructure", "category": "Industrial Metals"},
]

BROAD_COMMODITIES = [
    {"symbol": "DJP", "name": "iPath Bloomberg Commodity Index TR ETN", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "GSG", "name": "iShares S&P GSCI Commodity-Indexed Trust", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "PDBC", "name": "Invesco Optimum Yield Diversified Commodity Strategy", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "DBC", "name": "Invesco DB Commodity Index Tracking Fund", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "COM", "name": "Direxion Auspice Broad Commodity Strategy ETF", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "COMT", "name": "iShares US Commodity Strategy ETF", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "GCC", "name": "WisdomTree Enhanced Commodity Strategy Fund", "commodity": "Broad Basket", "category": "Broad Commodities"},
    {"symbol": "USCI", "name": "United States Commodity Index Fund", "commodity": "Broad Basket", "category": "Broad Commodities"},
]

# All commodities combined
ALL_COMMODITIES = PRECIOUS_METALS + ENERGY + AGRICULTURE + INDUSTRIAL_METALS + BROAD_COMMODITIES


def add_commodities_to_universe(store: SQLiteStore, commodities: List[Dict], category_label: str) -> tuple:
    """Add commodities to the universe."""
    added = 0
    skipped = 0
    
    for item in commodities:
        symbol = item["symbol"]
        asset_id = f"{symbol}.CMDTY"
        
        # Check if already exists
        existing = store.get_asset(asset_id)
        if existing:
            skipped += 1
            continue
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=symbol,
                name=item["name"],
                asset_type=AssetType.COMMODITY,
                market_scope="US_EU",
                market_code="US",
                exchange_code="US",
                exchange="US",
                currency="USD",
                country="US",
                tier=1 if category_label in ["Precious Metals", "Energy"] else 2,
                active=True,
                sector=item["category"],
                industry=item["commodity"],
                data_source="YFINANCE",
            )
            store.upsert_asset(asset, market_scope="US_EU")
            added += 1
            logger.info(f"Added COMMODITY: {symbol} - {item['name']} ({item['commodity']})")
        except Exception as e:
            logger.error(f"Failed to add {symbol}: {e}")
    
    return added, skipped


def main():
    """Main function to add Commodities to universe."""
    print("=" * 60)
    print("MarketGPS - Add Commodities Universe")
    print("=" * 60)
    print(f"Source: ETF proxies via Yahoo Finance")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    total_added = 0
    total_skipped = 0
    
    # Add each category
    categories = [
        ("Precious Metals", PRECIOUS_METALS),
        ("Energy", ENERGY),
        ("Agriculture", AGRICULTURE),
        ("Industrial Metals", INDUSTRIAL_METALS),
        ("Broad Commodities", BROAD_COMMODITIES),
    ]
    
    for category_name, items in categories:
        print("-" * 60)
        print(f"Adding {category_name}...")
        print("-" * 60)
        added, skipped = add_commodities_to_universe(store, items, category_name)
        print(f"{category_name}: {added} added, {skipped} already existed")
        total_added += added
        total_skipped += skipped
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM universe 
            WHERE asset_type = 'COMMODITY' AND active = 1
        """)
        count = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT sector, COUNT(*) as count 
            FROM universe 
            WHERE asset_type = 'COMMODITY' AND active = 1
            GROUP BY sector
            ORDER BY count DESC
        """)
        by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    print(f"Total Commodities: {count}")
    print(f"Added this run: {total_added}")
    print()
    print("By Category:")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    
    print()
    print("✓ Commodities universe added successfully!")


if __name__ == "__main__":
    main()
