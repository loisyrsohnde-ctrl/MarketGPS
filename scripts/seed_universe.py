#!/usr/bin/env python3
"""
MarketGPS - Seed Universe Script
================================
Peuple la table Universe avec tous les tickers disponibles depuis EODHD.
Les scores ne sont PAS calcules - seules les metadonnees sont chargees.

Usage:
    python scripts/seed_universe.py --scope US_EU --limit 60000
    python scripts/seed_universe.py --scope AFRICA --limit 5000
    python scripts/seed_universe.py --all
"""

import os
import sys
import time
import argparse
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_config, get_logger
from core.models import Asset, AssetType
from storage.sqlite_store import SQLiteStore
from providers.eodhd import EODHDProvider

logger = get_logger(__name__)

US_EU_EXCHANGES = {
    "US": {"market_code": "US", "country": "US", "currency": "USD"},
    "PA": {"market_code": "EU", "country": "FR", "currency": "EUR"},
    "XETRA": {"market_code": "EU", "country": "DE", "currency": "EUR"},
    "LSE": {"market_code": "UK", "country": "GB", "currency": "GBP"},
    "AS": {"market_code": "EU", "country": "NL", "currency": "EUR"},
    "BR": {"market_code": "EU", "country": "BE", "currency": "EUR"},
    "SW": {"market_code": "EU", "country": "CH", "currency": "CHF"},
    "MI": {"market_code": "EU", "country": "IT", "currency": "EUR"},
    "MC": {"market_code": "EU", "country": "ES", "currency": "EUR"},
    "VI": {"market_code": "EU", "country": "AT", "currency": "EUR"},
    "HE": {"market_code": "EU", "country": "FI", "currency": "EUR"},
    "ST": {"market_code": "EU", "country": "SE", "currency": "SEK"},
    "CO": {"market_code": "EU", "country": "DK", "currency": "DKK"},
    "OL": {"market_code": "EU", "country": "NO", "currency": "NOK"},
    "IR": {"market_code": "EU", "country": "IE", "currency": "EUR"},
    "LI": {"market_code": "EU", "country": "PT", "currency": "EUR"},
}

AFRICA_EXCHANGES = {
    "JSE": {"market_code": "JSE", "country": "ZA", "currency": "ZAR"},
    "NG": {"market_code": "NG", "country": "NG", "currency": "NGN"},
    "BC": {"market_code": "BRVM", "country": "CI", "currency": "XOF"},
    "CA": {"market_code": "EGX", "country": "EG", "currency": "EGP"},
    "NB": {"market_code": "NSE", "country": "KE", "currency": "KES"},
}

TYPE_MAP = {
    "Common Stock": AssetType.EQUITY,
    "Stock": AssetType.EQUITY,
    "ETF": AssetType.ETF,
    "FUND": AssetType.FUND,
    "Mutual Fund": AssetType.FUND,
    "Bond": AssetType.BOND,
    "INDEX": AssetType.INDEX,
    "Preferred Stock": AssetType.EQUITY,
    "Closed-end Fund": AssetType.FUND,
    "REIT": AssetType.EQUITY,
}


def fetch_exchange_listings(provider: EODHDProvider, exchange_code: str) -> List[Dict]:
    """Fetch all listings for an exchange from EODHD."""
    try:
        logger.info(f"Fetching listings for exchange: {exchange_code}")
        symbols = provider.get_exchange_symbols(exchange_code)
        if not symbols:
            logger.warning(f"No symbols found for {exchange_code}")
            return []
        logger.info(f"  -> Found {len(symbols)} symbols on {exchange_code}")
        return symbols
    except Exception as e:
        logger.error(f"Failed to fetch listings for {exchange_code}: {e}")
        return []


def transform_to_assets(listings: List[Dict], exchange_code: str, exchange_info: Dict, market_scope: str, priority_tier: int = 3) -> List[Dict]:
    """Transform raw EODHD listings to Asset dicts for bulk insert."""
    assets = []
    for item in listings:
        try:
            code = item.get("Code", "")
            if not code:
                continue
            asset_id = f"{code}.{exchange_code}"
            type_str = item.get("Type", "Common Stock")
            asset_type = TYPE_MAP.get(type_str, AssetType.EQUITY)
            assets.append({
                "asset_id": asset_id,
                "symbol": code,
                "name": item.get("Name", code),
                "asset_type": asset_type.value,
                "market_scope": market_scope,
                "market_code": exchange_info["market_code"],
                "exchange_code": exchange_code,
                "currency": item.get("Currency", exchange_info["currency"]),
                "country": item.get("Country", exchange_info["country"]),
                "sector": item.get("Sector"),
                "industry": item.get("Industry"),
                "active": 1,
                "tier": priority_tier,
                "priority_level": 2 if priority_tier <= 2 else 3,
            })
        except Exception as e:
            logger.debug(f"Failed to transform listing: {e}")
            continue
    return assets


def seed_scope(store: SQLiteStore, provider: EODHDProvider, scope: str, exchanges: Dict, limit: Optional[int] = None, auto_tier_limit: int = 3000) -> Dict:
    """Seed the universe for a given scope."""
    logger.info(f"\n{'='*60}")
    logger.info(f"SEEDING UNIVERSE: {scope}")
    logger.info(f"{'='*60}")
    
    stats = {"scope": scope, "exchanges_processed": 0, "listings_fetched": 0, "assets_inserted": 0, "tier1_count": 0, "errors": 0}
    all_assets = []
    
    for exchange_code, exchange_info in exchanges.items():
        try:
            listings = fetch_exchange_listings(provider, exchange_code)
            stats["exchanges_processed"] += 1
            stats["listings_fetched"] += len(listings)
            assets = transform_to_assets(listings, exchange_code, exchange_info, scope, priority_tier=3)
            all_assets.extend(assets)
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error processing {exchange_code}: {e}")
            stats["errors"] += 1
    
    if limit and len(all_assets) > limit:
        all_assets = all_assets[:limit]
        logger.info(f"Limited to {limit} total assets")
    
    def sort_key(a):
        type_order = {"EQUITY": 0, "ETF": 1, "FUND": 2, "BOND": 3}
        return type_order.get(a.get("asset_type", "EQUITY"), 9)
    
    all_assets.sort(key=sort_key)
    
    for i, asset in enumerate(all_assets[:auto_tier_limit]):
        asset["tier"] = 1
        asset["priority_level"] = 1
    
    stats["tier1_count"] = min(len(all_assets), auto_tier_limit)
    
    logger.info(f"Inserting {len(all_assets)} assets into database...")
    
    try:
        store.bulk_upsert_assets(all_assets, market_scope=scope)
        stats["assets_inserted"] = len(all_assets)
        logger.info(f"Inserted {len(all_assets)} assets for {scope}")
    except Exception as e:
        logger.error(f"Failed to insert assets: {e}")
        stats["errors"] += 1
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed MarketGPS Universe")
    parser.add_argument("--scope", choices=["US_EU", "AFRICA"], help="Market scope to seed")
    parser.add_argument("--all", action="store_true", help="Seed all scopes")
    parser.add_argument("--limit", type=int, default=None, help="Max assets per scope")
    parser.add_argument("--auto-tier-limit", type=int, default=3000, help="Number of assets to mark as tier=1")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done without making changes")
    
    args = parser.parse_args()
    
    config = get_config()
    store = SQLiteStore()
    
    if not config.eodhd.is_configured:
        logger.error("EODHD API key not configured. Set EODHD_API_KEY environment variable.")
        sys.exit(1)
    
    provider = EODHDProvider()
    
    scopes_to_process = []
    if args.all:
        scopes_to_process = ["US_EU", "AFRICA"]
    elif args.scope:
        scopes_to_process = [args.scope]
    else:
        scopes_to_process = ["US_EU"]
    
    all_stats = []
    
    for scope in scopes_to_process:
        exchanges = US_EU_EXCHANGES if scope == "US_EU" else AFRICA_EXCHANGES
        if args.dry_run:
            logger.info(f"[DRY RUN] Would seed {scope} with exchanges: {list(exchanges.keys())}")
            continue
        stats = seed_scope(store, provider, scope, exchanges, args.limit, args.auto_tier_limit)
        all_stats.append(stats)
    
    print("\n" + "="*60)
    print("SEED UNIVERSE COMPLETE")
    print("="*60)
    
    for stats in all_stats:
        print(f"\n{stats['scope']}:")
        print(f"  Exchanges processed: {stats['exchanges_processed']}")
        print(f"  Listings fetched:    {stats['listings_fetched']}")
        print(f"  Assets inserted:     {stats['assets_inserted']}")
        print(f"  Tier 1 (auto-score): {stats['tier1_count']}")
        print(f"  Errors:              {stats['errors']}")
    
    print("\n" + "-"*40)
    print("DATABASE VERIFICATION:")
    counts = store.count_by_scope()
    print(f"  US_EU:  {counts.get('US_EU', 0):,} assets")
    print(f"  AFRICA: {counts.get('AFRICA', 0):,} assets")
    print(f"  Total:  {sum(counts.values()):,} assets")


if __name__ == "__main__":
    main()
