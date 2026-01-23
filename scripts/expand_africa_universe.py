"""
MarketGPS - Expand Africa Universe
Adds assets for African exchanges that are currently empty:
- EGX (Egypt - Cairo Stock Exchange)
- NSE (Kenya - Nairobi Securities Exchange)
- CSE (Morocco - Casablanca Stock Exchange)
- GSE (Ghana - Ghana Stock Exchange)
- BVMT (Tunisia - Bourse de Tunis)

SAFE: Uses UPSERT - does not delete existing data.
IDEMPOTENT: Safe to run multiple times.

Run: python scripts/expand_africa_universe.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.models import AssetType, Asset
from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# EGYPTIAN EXCHANGE (EGX) - Top companies
# EODHD code: CA (Cairo)
# ═══════════════════════════════════════════════════════════════════════════
EGX_ASSETS = [
    # Banks & Financial Services
    {"symbol": "COMI", "name": "Commercial International Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "HRHO", "name": "Hermes Holding", "sector": "Financials", "industry": "Investment Banking"},
    {"symbol": "CIEB", "name": "Credit Agricole Egypt", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ADIB", "name": "Abu Dhabi Islamic Bank Egypt", "sector": "Financials", "industry": "Banks"},
    {"symbol": "QNBA", "name": "QNB Alahli", "sector": "Financials", "industry": "Banks"},
    {"symbol": "SAIB", "name": "Societe Arabe Internationale de Banque", "sector": "Financials", "industry": "Banks"},
    {"symbol": "AIBANK", "name": "Arab Investment Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "FAISAL", "name": "Faisal Islamic Bank", "sector": "Financials", "industry": "Banks"},
    
    # Real Estate & Construction
    {"symbol": "TMGH", "name": "Talaat Moustafa Group Holding", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "PHDC", "name": "Palm Hills Development", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "OCDI", "name": "Orascom Development Egypt", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "MNHD", "name": "Madinet Nasr Housing", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "EMFD", "name": "Emaar Misr for Development", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "HELI", "name": "Heliopolis Housing", "sector": "Real Estate", "industry": "Development"},
    
    # Telecom & Technology
    {"symbol": "ETEL", "name": "Telecom Egypt", "sector": "Telecommunications", "industry": "Telecom Operators"},
    {"symbol": "OTMT", "name": "Orascom Investment Holding", "sector": "Technology", "industry": "Holding"},
    
    # Consumer & Retail
    {"symbol": "EAST", "name": "Eastern Company", "sector": "Consumer Goods", "industry": "Tobacco"},
    {"symbol": "JUFO", "name": "Juhayna Food Industries", "sector": "Consumer Goods", "industry": "Food Processing"},
    {"symbol": "EFID", "name": "Edita Food Industries", "sector": "Consumer Goods", "industry": "Food Processing"},
    {"symbol": "SKPC", "name": "Sidi Kerir Petrochemicals", "sector": "Materials", "industry": "Chemicals"},
    {"symbol": "AMOC", "name": "Alexandria Mineral Oils Company", "sector": "Energy", "industry": "Oil & Gas"},
    
    # Industrials
    {"symbol": "ESRS", "name": "Ezz Steel", "sector": "Materials", "industry": "Steel"},
    {"symbol": "EDBM", "name": "El Sewedy Electric", "sector": "Industrials", "industry": "Electrical Equipment"},
    {"symbol": "IRON", "name": "Egyptian Iron & Steel", "sector": "Materials", "industry": "Steel"},
    {"symbol": "ELEC", "name": "Electric Cable Egypt", "sector": "Industrials", "industry": "Electrical Equipment"},
]

# ═══════════════════════════════════════════════════════════════════════════
# NAIROBI SECURITIES EXCHANGE (NSE) - Kenya
# EODHD code: NBO
# ═══════════════════════════════════════════════════════════════════════════
NSE_KENYA_ASSETS = [
    # Banks
    {"symbol": "EQTY", "name": "Equity Group Holdings", "sector": "Financials", "industry": "Banks"},
    {"symbol": "KCB", "name": "KCB Group", "sector": "Financials", "industry": "Banks"},
    {"symbol": "COOP", "name": "Co-operative Bank of Kenya", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ABSA", "name": "ABSA Bank Kenya", "sector": "Financials", "industry": "Banks"},
    {"symbol": "SCBK", "name": "Standard Chartered Bank Kenya", "sector": "Financials", "industry": "Banks"},
    {"symbol": "NCBA", "name": "NCBA Group", "sector": "Financials", "industry": "Banks"},
    {"symbol": "DTB", "name": "Diamond Trust Bank Kenya", "sector": "Financials", "industry": "Banks"},
    {"symbol": "STBK", "name": "Stanbic Holdings", "sector": "Financials", "industry": "Banks"},
    {"symbol": "I&M", "name": "I&M Holdings", "sector": "Financials", "industry": "Banks"},
    
    # Telecom
    {"symbol": "SCOM", "name": "Safaricom", "sector": "Telecommunications", "industry": "Wireless"},
    
    # Manufacturing & Consumer
    {"symbol": "EABL", "name": "East African Breweries", "sector": "Consumer Goods", "industry": "Beverages"},
    {"symbol": "BAT", "name": "British American Tobacco Kenya", "sector": "Consumer Goods", "industry": "Tobacco"},
    {"symbol": "BAMB", "name": "Bamburi Cement", "sector": "Materials", "industry": "Construction Materials"},
    
    # Energy & Utilities
    {"symbol": "KPLC", "name": "Kenya Power and Lighting", "sector": "Utilities", "industry": "Electric Utilities"},
    {"symbol": "KEGN", "name": "KenGen", "sector": "Utilities", "industry": "Electric Utilities"},
    {"symbol": "TOTL", "name": "TotalEnergies Marketing Kenya", "sector": "Energy", "industry": "Oil & Gas"},
    
    # Insurance
    {"symbol": "BRIT", "name": "Britam Holdings", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "JUB", "name": "Jubilee Holdings", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "SANLAM", "name": "Sanlam Kenya", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "CIC", "name": "CIC Insurance Group", "sector": "Financials", "industry": "Insurance"},
    
    # Other
    {"symbol": "NMG", "name": "Nation Media Group", "sector": "Media", "industry": "Publishing"},
    {"symbol": "LKL", "name": "Longhorn Publishers", "sector": "Media", "industry": "Publishing"},
    {"symbol": "FIRE", "name": "Flame Tree Group", "sector": "Consumer Goods", "industry": "Household Products"},
]

# ═══════════════════════════════════════════════════════════════════════════
# CASABLANCA STOCK EXCHANGE (CSE) - Morocco
# EODHD code: BC
# ═══════════════════════════════════════════════════════════════════════════
CSE_MOROCCO_ASSETS = [
    # Banks
    {"symbol": "ATW", "name": "Attijariwafa Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BCP", "name": "Banque Centrale Populaire", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BOA", "name": "Bank of Africa", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BMCI", "name": "BMCI", "sector": "Financials", "industry": "Banks"},
    {"symbol": "CIH", "name": "CIH Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "CDM", "name": "Credit du Maroc", "sector": "Financials", "industry": "Banks"},
    
    # Telecom
    {"symbol": "IAM", "name": "Maroc Telecom", "sector": "Telecommunications", "industry": "Telecom Operators"},
    
    # Mining & Materials
    {"symbol": "MNG", "name": "Managem", "sector": "Materials", "industry": "Mining"},
    {"symbol": "CMT", "name": "Compagnie Miniere de Touissit", "sector": "Materials", "industry": "Mining"},
    {"symbol": "SMI", "name": "SMI", "sector": "Materials", "industry": "Mining"},
    {"symbol": "LHM", "name": "LafargeHolcim Maroc", "sector": "Materials", "industry": "Construction Materials"},
    {"symbol": "CMA", "name": "Ciments du Maroc", "sector": "Materials", "industry": "Construction Materials"},
    
    # Real Estate
    {"symbol": "ADI", "name": "Alliances Darna", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "RDS", "name": "Residences Dar Saada", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "ADH", "name": "Addoha", "sector": "Real Estate", "industry": "Development"},
    
    # Consumer & Retail
    {"symbol": "LBV", "name": "Label Vie", "sector": "Consumer Services", "industry": "Retail"},
    {"symbol": "SBM", "name": "Societe des Brasseries du Maroc", "sector": "Consumer Goods", "industry": "Beverages"},
    {"symbol": "LES", "name": "Lesieur Cristal", "sector": "Consumer Goods", "industry": "Food Processing"},
    {"symbol": "COL", "name": "Cosumar", "sector": "Consumer Goods", "industry": "Sugar"},
    {"symbol": "MUT", "name": "Mutandis", "sector": "Consumer Goods", "industry": "Consumer Products"},
    
    # Insurance
    {"symbol": "WAA", "name": "Wafa Assurance", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "SAH", "name": "Saham Assurance", "sector": "Financials", "industry": "Insurance"},
    
    # Energy & Utilities
    {"symbol": "TQM", "name": "Taqa Morocco", "sector": "Utilities", "industry": "Electric Utilities"},
    {"symbol": "AFM", "name": "Afriquia Gaz", "sector": "Energy", "industry": "Oil & Gas"},
    {"symbol": "TMA", "name": "Total Maroc", "sector": "Energy", "industry": "Oil & Gas"},
    
    # Industrials
    {"symbol": "NEX", "name": "Nexans Maroc", "sector": "Industrials", "industry": "Electrical Equipment"},
    {"symbol": "SNP", "name": "Sonasid", "sector": "Materials", "industry": "Steel"},
    {"symbol": "ALM", "name": "Aluminium du Maroc", "sector": "Materials", "industry": "Aluminum"},
]

# ═══════════════════════════════════════════════════════════════════════════
# GHANA STOCK EXCHANGE (GSE)
# EODHD code: GH
# ═══════════════════════════════════════════════════════════════════════════
GSE_GHANA_ASSETS = [
    # Banks
    {"symbol": "GCB", "name": "GCB Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "EGH", "name": "Ecobank Ghana", "sector": "Financials", "industry": "Banks"},
    {"symbol": "SCB", "name": "Standard Chartered Bank Ghana", "sector": "Financials", "industry": "Banks"},
    {"symbol": "CAL", "name": "CalBank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "RBGH", "name": "Republic Bank Ghana", "sector": "Financials", "industry": "Banks"},
    {"symbol": "SOGEGH", "name": "Societe Generale Ghana", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ADB", "name": "Agricultural Development Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ACCESS", "name": "Access Bank Ghana", "sector": "Financials", "industry": "Banks"},
    
    # Consumer & Manufacturing
    {"symbol": "GGBL", "name": "Guinness Ghana Breweries", "sector": "Consumer Goods", "industry": "Beverages"},
    {"symbol": "FML", "name": "Fan Milk", "sector": "Consumer Goods", "industry": "Dairy"},
    {"symbol": "UNIL", "name": "Unilever Ghana", "sector": "Consumer Goods", "industry": "Consumer Products"},
    {"symbol": "GOIL", "name": "Ghana Oil Company", "sector": "Energy", "industry": "Oil & Gas"},
    {"symbol": "TOTAL", "name": "TotalEnergies Marketing Ghana", "sector": "Energy", "industry": "Oil & Gas"},
    
    # Insurance
    {"symbol": "EIC", "name": "Enterprise Group", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "SIC", "name": "SIC Insurance Company", "sector": "Financials", "industry": "Insurance"},
    
    # Telecom
    {"symbol": "MTN", "name": "MTN Ghana", "sector": "Telecommunications", "industry": "Wireless"},
    
    # Mining
    {"symbol": "ANGLOGOLD", "name": "AngloGold Ashanti", "sector": "Materials", "industry": "Gold Mining"},
]

# ═══════════════════════════════════════════════════════════════════════════
# BOURSE DE TUNIS (BVMT) - Tunisia
# EODHD code: TN
# ═══════════════════════════════════════════════════════════════════════════
BVMT_TUNISIA_ASSETS = [
    # Banks
    {"symbol": "BIAT", "name": "Banque Internationale Arabe de Tunisie", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BNA", "name": "Banque Nationale Agricole", "sector": "Financials", "industry": "Banks"},
    {"symbol": "STB", "name": "Societe Tunisienne de Banque", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ATTIJ", "name": "Attijari Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BH", "name": "Banque de l'Habitat", "sector": "Financials", "industry": "Banks"},
    {"symbol": "UIB", "name": "Union Internationale de Banques", "sector": "Financials", "industry": "Banks"},
    {"symbol": "AB", "name": "Amen Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "ATB", "name": "Arab Tunisian Bank", "sector": "Financials", "industry": "Banks"},
    {"symbol": "BT", "name": "Banque de Tunisie", "sector": "Financials", "industry": "Banks"},
    {"symbol": "UBCI", "name": "Union Bancaire pour le Commerce et l'Industrie", "sector": "Financials", "industry": "Banks"},
    
    # Insurance
    {"symbol": "STAR", "name": "STAR Assurances", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "ASTREE", "name": "Astree Assurances", "sector": "Financials", "industry": "Insurance"},
    {"symbol": "BH ASSURANCE", "name": "BH Assurance", "sector": "Financials", "industry": "Insurance"},
    
    # Telecom
    {"symbol": "TLNET", "name": "Tunisie Telecom", "sector": "Telecommunications", "industry": "Telecom Operators"},
    
    # Consumer & Retail
    {"symbol": "SFBT", "name": "SFBT", "sector": "Consumer Goods", "industry": "Beverages"},
    {"symbol": "DELICE", "name": "Delice Holding", "sector": "Consumer Goods", "industry": "Food Processing"},
    {"symbol": "POULINA", "name": "Poulina Group Holding", "sector": "Consumer Goods", "industry": "Diversified"},
    {"symbol": "SOPAT", "name": "SOPAT", "sector": "Consumer Goods", "industry": "Food Processing"},
    {"symbol": "LAND'OR", "name": "Land'Or", "sector": "Consumer Goods", "industry": "Food Processing"},
    
    # Materials & Industry
    {"symbol": "SCB", "name": "Societe des Ciments de Bizerte", "sector": "Materials", "industry": "Construction Materials"},
    {"symbol": "SOTIPAPIER", "name": "Sotipapier", "sector": "Materials", "industry": "Paper"},
    {"symbol": "SOMOCER", "name": "Somocer", "sector": "Materials", "industry": "Construction Materials"},
    
    # Real Estate
    {"symbol": "SIMPAR", "name": "Simpar", "sector": "Real Estate", "industry": "Development"},
    {"symbol": "ESSOUKNA", "name": "Essoukna", "sector": "Real Estate", "industry": "Development"},
]

# ═══════════════════════════════════════════════════════════════════════════
# EXCHANGE MAPPING
# ═══════════════════════════════════════════════════════════════════════════
EXCHANGE_CONFIG = {
    "EGX": {
        "assets": EGX_ASSETS,
        "eodhd_code": "CA",
        "currency": "EGP",
        "country": "Egypt",
        "market_code": "EG",
        "tier": 2,
    },
    "NSE": {
        "assets": NSE_KENYA_ASSETS,
        "eodhd_code": "NBO",
        "currency": "KES",
        "country": "Kenya",
        "market_code": "KE",
        "tier": 2,
    },
    "CSE": {
        "assets": CSE_MOROCCO_ASSETS,
        "eodhd_code": "BC",
        "currency": "MAD",
        "country": "Morocco",
        "market_code": "MA",
        "tier": 2,
    },
    "GSE": {
        "assets": GSE_GHANA_ASSETS,
        "eodhd_code": "GH",
        "currency": "GHS",
        "country": "Ghana",
        "market_code": "GH",
        "tier": 3,
    },
    "BVMT": {
        "assets": BVMT_TUNISIA_ASSETS,
        "eodhd_code": "TN",
        "currency": "TND",
        "country": "Tunisia",
        "market_code": "TN",
        "tier": 3,
    },
}


def add_exchange_assets(
    store: SQLiteStore,
    exchange_code: str,
    config: Dict,
    dry_run: bool = False
) -> tuple:
    """Add assets from a specific exchange to the universe."""
    added = 0
    skipped = 0
    errors = 0
    
    assets = config["assets"]
    eodhd_code = config["eodhd_code"]
    currency = config["currency"]
    country = config["country"]
    market_code = config["market_code"]
    tier = config["tier"]
    
    for asset_data in assets:
        symbol = asset_data["symbol"]
        # Create asset_id in format: SYMBOL.EXCHANGE
        asset_id = f"{symbol}.{exchange_code}"
        
        # Check if already exists
        existing = store.get_asset(asset_id)
        if existing:
            skipped += 1
            logger.debug(f"Skipped (exists): {asset_id}")
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would add: {asset_id} - {asset_data['name']}")
            added += 1
            continue
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=symbol,
                name=asset_data["name"],
                asset_type=AssetType.EQUITY,
                market_scope="AFRICA",
                market_code=market_code,
                exchange_code=exchange_code,
                exchange=exchange_code,
                currency=currency,
                country=country,
                sector=asset_data.get("sector", ""),
                industry=asset_data.get("industry", ""),
                tier=tier,
                active=True,
                data_source="EODHD",
            )
            store.upsert_asset(asset, market_scope="AFRICA")
            added += 1
            logger.info(f"Added: {asset_id} - {asset_data['name']}")
        except Exception as e:
            errors += 1
            logger.error(f"Failed to add {asset_id}: {e}")
    
    return added, skipped, errors


def get_current_counts(store: SQLiteStore) -> Dict[str, int]:
    """Get current asset counts per exchange."""
    counts = {}
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT exchange_code, COUNT(*) as count
            FROM universe
            WHERE market_scope = 'AFRICA' AND active = 1
            GROUP BY exchange_code
        """)
        for row in cursor.fetchall():
            counts[row[0]] = row[1]
    return counts


def main():
    """Main function to expand Africa universe."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Expand Africa Universe")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--exchange", type=str, help="Only process specific exchange (EGX, NSE, CSE, GSE, BVMT)")
    args = parser.parse_args()
    
    print("=" * 70)
    print("MarketGPS - Expand Africa Universe")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    # Show current state
    print("-" * 70)
    print("CURRENT STATE")
    print("-" * 70)
    current_counts = get_current_counts(store)
    for exchange in ["JSE", "NGX", "BRVM", "EGX", "NSE", "CSE", "GSE", "BVMT"]:
        count = current_counts.get(exchange, 0)
        status = "✓" if count > 0 else "✗ EMPTY"
        print(f"  {exchange}: {count} assets {status}")
    print()
    
    # Process exchanges
    total_added = 0
    total_skipped = 0
    total_errors = 0
    
    exchanges_to_process = [args.exchange] if args.exchange else EXCHANGE_CONFIG.keys()
    
    for exchange_code in exchanges_to_process:
        if exchange_code not in EXCHANGE_CONFIG:
            print(f"Unknown exchange: {exchange_code}")
            continue
            
        config = EXCHANGE_CONFIG[exchange_code]
        current = current_counts.get(exchange_code, 0)
        
        print("-" * 70)
        print(f"Processing {exchange_code} ({config['country']})")
        print(f"  Current assets: {current}")
        print(f"  Assets to add: {len(config['assets'])}")
        print("-" * 70)
        
        added, skipped, errors = add_exchange_assets(
            store, exchange_code, config, dry_run=args.dry_run
        )
        
        print(f"  Added: {added}, Skipped: {skipped}, Errors: {errors}")
        total_added += added
        total_skipped += skipped
        total_errors += errors
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Added: {total_added}")
    print(f"Total Skipped: {total_skipped}")
    print(f"Total Errors: {total_errors}")
    print()
    
    if not args.dry_run:
        # Show new state
        print("NEW STATE")
        print("-" * 70)
        new_counts = get_current_counts(store)
        for exchange in ["JSE", "NGX", "BRVM", "EGX", "NSE", "CSE", "GSE", "BVMT"]:
            count = new_counts.get(exchange, 0)
            old_count = current_counts.get(exchange, 0)
            diff = count - old_count
            diff_str = f" (+{diff})" if diff > 0 else ""
            status = "✓" if count > 0 else "✗ EMPTY"
            print(f"  {exchange}: {count} assets{diff_str} {status}")
        print()
        print("✓ Africa universe expanded successfully!")
        print()
        print("NEXT STEPS:")
        print("1. Run data fetching: python -m pipeline.jobs --gating --scope AFRICA")
        print("2. Run scoring: python -m pipeline.jobs --rotation --scope AFRICA")
    else:
        print("DRY RUN completed. Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
