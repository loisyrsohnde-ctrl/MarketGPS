"""
MarketGPS - Smart Universe Builder (API Optimization)
Pre-filters assets using bulk data BEFORE making expensive API calls.

STRATEGY:
1. Use bulk_eod to get all assets with LATEST price/volume
2. Filter by volume (ADV proxy) - only keep liquid assets
3. Categorize into tiers based on liquidity
4. Only fetch full history for Tier 1 assets
5. Score only eligible assets

This dramatically reduces API calls while maintaining quality.

Usage:
    python scripts/smart_universe_builder.py --scope US_EU --tier1-limit 2000
    python scripts/smart_universe_builder.py --scope AFRICA --tier1-limit 500
"""
import os
import sys
import argparse
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from core.models import Asset, AssetType
from storage.sqlite_store import SQLiteStore
from providers.eodhd import EODHDProvider

logger = get_logger(__name__)


# Volume thresholds for tiering (daily dollar volume estimate)
# Based on: close * volume from bulk_eod
TIER_THRESHOLDS = {
    "US_EU": {
        "tier1": 5_000_000,      # >$5M daily = Tier 1 (very liquid)
        "tier2": 1_000_000,      # >$1M daily = Tier 2 (liquid)
        "tier3": 100_000,        # >$100K daily = Tier 3 (acceptable)
    },
    "AFRICA": {
        "tier1": 500_000,        # >$500K daily = Tier 1 (liquid for Africa)
        "tier2": 100_000,        # >$100K daily = Tier 2
        "tier3": 10_000,         # >$10K daily = Tier 3
    }
}


class SmartUniverseBuilder:
    """
    Builds and categorizes the universe using bulk data.
    
    Key Optimization:
    - Uses bulk_eod to estimate liquidity WITHOUT individual API calls
    - Categorizes assets into tiers
    - Only marks Tier 1 as active for full processing
    - Tier 2/3 can be processed on-demand or in batches
    """
    
    # Exchange groupings - Complete list including derivatives and bonds
    US_EU_EXCHANGES = [
        # Main equity markets
        "US", "LSE", "PA", "XETRA", "AS", "SW", "MI", "MC",
        "BR", "LIS", "VI", "HE", "ST", "CO", "OL", "IR",
        # US Bonds and Futures
        "BOND", "MONEY",  # Bond markets
        # Futures exchanges
        "CME", "COMEX", "CBOT", "NYMEX",  # US Futures
        "EUREX",  # European derivatives
        # ETF specific
        "ETLX",  # ETF exchange
    ]
    
    AFRICA_EXCHANGES = ["JSE", "NG", "CA", "BRVM"]
    
    # Derivative/Bond specific exchanges (lower tier by default due to complexity)
    DERIVATIVE_EXCHANGES = ["CME", "COMEX", "CBOT", "NYMEX", "EUREX"]
    BOND_EXCHANGES = ["BOND", "MONEY"]
    
    # Market code mapping
    MARKET_CODE_MAP = {
        # Equity markets
        "US": "US",
        "LSE": "UK",
        "PA": "FR",
        "XETRA": "DE",
        "AS": "NL",
        "SW": "CH",
        "MI": "IT",
        "MC": "ES",
        "BR": "BE",
        "LIS": "PT",
        "VI": "AT",
        "HE": "FI",
        "ST": "SE",
        "CO": "DK",
        "OL": "NO",
        "IR": "IE",
        # African markets
        "JSE": "ZA",
        "NG": "NG",
        "CA": "EG",
        "BRVM": "CI",
        # Bond markets
        "BOND": "US",
        "MONEY": "US",
        # Futures exchanges
        "CME": "US",
        "COMEX": "US",
        "CBOT": "US",
        "NYMEX": "US",
        "EUREX": "DE",
        # ETF
        "ETLX": "US",
    }
    
    def __init__(self, market_scope: str = "US_EU"):
        """Initialize the builder."""
        self._scope = market_scope
        self._config = get_config()
        self._store = SQLiteStore()
        self._provider = EODHDProvider()
        
        self._exchanges = (
            self.US_EU_EXCHANGES if market_scope == "US_EU"
            else self.AFRICA_EXCHANGES
        )
        
        self._thresholds = TIER_THRESHOLDS.get(market_scope, TIER_THRESHOLDS["US_EU"])
        
        if not self._provider.is_configured:
            raise RuntimeError("EODHD API key not configured")
    
    def fetch_all_listings(self) -> List[Dict]:
        """
        Fetch symbol listings for all exchanges.
        
        Uses: GET /exchange-symbol-list/{EXCHANGE}
        1 call per exchange (~20 calls total)
        
        Returns:
            List of symbol info dicts
        """
        all_listings = []
        
        logger.info(f"[{self._scope}] Fetching listings for {len(self._exchanges)} exchanges")
        
        for exchange in self._exchanges:
            try:
                listings = self._provider.list_symbols(exchange)
                
                # Add exchange info
                for item in listings:
                    item["Exchange"] = exchange
                
                all_listings.extend(listings)
                logger.info(f"  {exchange}: {len(listings)} symbols")
                
            except Exception as e:
                logger.error(f"  Failed to fetch listings for {exchange}: {e}")
        
        logger.info(f"[{self._scope}] Total listings: {len(all_listings)}")
        return all_listings
    
    def fetch_bulk_eod_data(self) -> Dict[str, Dict]:
        """
        Fetch latest EOD data for all exchanges using bulk endpoint.
        
        Uses: GET /eod-bulk-last-day/{EXCHANGE}
        1 call per exchange (~20 calls total)
        
        Returns:
            Dict mapping symbol to latest price/volume
        """
        all_data = {}
        
        logger.info(f"[{self._scope}] Fetching bulk EOD for liquidity estimation")
        
        for exchange in self._exchanges:
            try:
                bulk = self._provider.get_bulk_eod(exchange)
                
                for item in bulk:
                    code = item.get("code", "")
                    if code:
                        asset_id = f"{code}.{exchange}"
                        all_data[asset_id] = {
                            "close": item.get("close", 0) or 0,
                            "volume": item.get("volume", 0) or 0,
                            "date": item.get("date"),
                        }
                
                logger.info(f"  {exchange}: {len(bulk)} symbols with EOD")
                
            except Exception as e:
                logger.error(f"  Bulk EOD failed for {exchange}: {e}")
        
        return all_data
    
    def estimate_liquidity(self, bulk_data: Dict[str, Dict]) -> Dict[str, float]:
        """
        Estimate daily dollar volume from bulk EOD data.
        
        ADV estimate = Close * Volume
        
        Returns:
            Dict mapping asset_id to estimated ADV
        """
        liquidity = {}
        
        for asset_id, data in bulk_data.items():
            close = data.get("close", 0) or 0
            volume = data.get("volume", 0) or 0
            
            adv = close * volume
            liquidity[asset_id] = adv
        
        return liquidity
    
    def categorize_by_tier(
        self,
        listings: List[Dict],
        liquidity: Dict[str, float]
    ) -> Dict[int, List[Dict]]:
        """
        Categorize assets into tiers based on liquidity.
        
        Tier 1: Very liquid (active immediately)
        Tier 2: Liquid (processed in batches)
        Tier 3: Low liquidity (on-demand only)
        Tier 4: No liquidity data (inactive)
        
        Returns:
            Dict mapping tier number to list of assets
        """
        tiers = {1: [], 2: [], 3: [], 4: []}
        
        for item in listings:
            code = item.get("Code", "")
            exchange = item.get("Exchange", "US")
            asset_id = f"{code}.{exchange}"
            
            adv = liquidity.get(asset_id, 0)
            
            if adv >= self._thresholds["tier1"]:
                tier = 1
            elif adv >= self._thresholds["tier2"]:
                tier = 2
            elif adv >= self._thresholds["tier3"]:
                tier = 3
            else:
                tier = 4
            
            item["estimated_adv"] = adv
            item["tier"] = tier
            tiers[tier].append(item)
        
        logger.info(f"[{self._scope}] Tier distribution:")
        for tier, assets in tiers.items():
            logger.info(f"  Tier {tier}: {len(assets)} assets")
        
        return tiers
    
    def insert_to_database(
        self,
        tiers: Dict[int, List[Dict]],
        tier1_limit: Optional[int] = None,
        tier2_limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Insert categorized assets into database.
        
        Args:
            tiers: Categorized assets
            tier1_limit: Max Tier 1 assets to activate
            tier2_limit: Max Tier 2 assets to activate
            
        Returns:
            Dict with insert stats
        """
        stats = {"inserted": 0, "tier1_active": 0, "tier2_active": 0, "inactive": 0}
        
        # Sort each tier by liquidity (highest first)
        for tier in [1, 2, 3, 4]:
            tiers[tier].sort(key=lambda x: x.get("estimated_adv", 0), reverse=True)
        
        # Process Tier 1 (active)
        tier1_count = 0
        for item in tiers[1]:
            if tier1_limit and tier1_count >= tier1_limit:
                active = False
            else:
                active = True
                tier1_count += 1
                stats["tier1_active"] += 1
            
            self._insert_asset(item, tier=1, active=active)
            stats["inserted"] += 1
        
        # Process Tier 2 (active with limit)
        tier2_count = 0
        for item in tiers[2]:
            if tier2_limit and tier2_count >= tier2_limit:
                active = False
            else:
                active = True
                tier2_count += 1
                stats["tier2_active"] += 1
            
            self._insert_asset(item, tier=2, active=active)
            stats["inserted"] += 1
        
        # Process Tier 3 & 4 (inactive)
        for tier in [3, 4]:
            for item in tiers[tier]:
                self._insert_asset(item, tier=tier, active=False)
                stats["inserted"] += 1
                stats["inactive"] += 1
        
        logger.info(f"[{self._scope}] Inserted {stats['inserted']} assets")
        logger.info(f"  Active Tier 1: {stats['tier1_active']}")
        logger.info(f"  Active Tier 2: {stats['tier2_active']}")
        logger.info(f"  Inactive: {stats['inactive']}")
        
        return stats
    
    def _insert_asset(self, item: Dict, tier: int, active: bool):
        """Insert a single asset into the database."""
        code = item.get("Code", "")
        exchange = item.get("Exchange", "US")
        asset_id = f"{code}.{exchange}"
        
        # Map type - Complete mapping for all EODHD asset types
        type_str = item.get("Type", "Common Stock")
        type_map = {
            # Equity types
            "Common Stock": AssetType.EQUITY,
            "Preferred Stock": AssetType.EQUITY,
            "Depositary Receipt": AssetType.EQUITY,
            "Unit": AssetType.EQUITY,
            "Trust": AssetType.EQUITY,
            "REIT": AssetType.EQUITY,
            # ETF / Funds
            "ETF": AssetType.ETF,
            "FUND": AssetType.FUND,
            "Mutual Fund": AssetType.FUND,
            "Closed-End Fund": AssetType.FUND,
            # Fixed Income
            "Bond": AssetType.BOND,
            "Corporate Bond": AssetType.BOND,
            "Government Bond": AssetType.BOND,
            "Municipal Bond": AssetType.BOND,
            # Derivatives
            "Option": AssetType.OPTION,
            "Warrant": AssetType.OPTION,
            "Rights": AssetType.OPTION,
            "Future": AssetType.FUTURE,
            "Futures": AssetType.FUTURE,
            # Other
            "INDEX": AssetType.INDEX,
            "Commodity": AssetType.COMMODITY,
            "Currency": AssetType.FX,
            "Cryptocurrency": AssetType.CRYPTO,
        }
        asset_type = type_map.get(type_str, AssetType.EQUITY)
        
        # Market code (used as attribute on Asset, not separate parameter)
        market_code = self.MARKET_CODE_MAP.get(exchange, exchange)
        if market_code in ["US", "UK", "FR", "DE", "NL", "CH", "IT", "ES", 
                           "BE", "PT", "AT", "FI", "SE", "DK", "NO", "IE"]:
            market_code_final = "EU" if market_code != "US" else "US"
        else:
            market_code_final = market_code
        
        try:
            asset = Asset(
                asset_id=asset_id,
                symbol=code,
                name=item.get("Name", code),
                asset_type=asset_type,
                exchange=exchange,
                currency=item.get("Currency", "USD"),
                country=item.get("Country", ""),
                isin=item.get("ISIN"),
                active=active,
                tier=tier,
                market_code=market_code_final,  # Set on asset object
            )
            
            # upsert_asset only takes asset and market_scope
            self._store.upsert_asset(asset, market_scope=self._scope)
            
        except Exception as e:
            logger.warning(f"Failed to insert {asset_id}: {e}")
    
    def run(
        self,
        tier1_limit: int = 2000,
        tier2_limit: int = 1000
    ) -> Dict:
        """
        Run the smart universe builder.
        
        Args:
            tier1_limit: Max Tier 1 assets to activate
            tier2_limit: Max Tier 2 assets to activate
            
        Returns:
            Dict with all results
        """
        results = {
            "scope": self._scope,
            "thresholds": self._thresholds,
        }
        
        # Step 1: Fetch listings
        logger.info("=" * 60)
        logger.info("STEP 1: Fetch symbol listings")
        logger.info("=" * 60)
        listings = self.fetch_all_listings()
        results["total_listings"] = len(listings)
        
        # Step 2: Fetch bulk EOD for liquidity
        logger.info("=" * 60)
        logger.info("STEP 2: Fetch bulk EOD for liquidity estimation")
        logger.info("=" * 60)
        bulk_data = self.fetch_bulk_eod_data()
        results["bulk_data_count"] = len(bulk_data)
        
        # Step 3: Estimate liquidity
        logger.info("=" * 60)
        logger.info("STEP 3: Estimate liquidity (ADV)")
        logger.info("=" * 60)
        liquidity = self.estimate_liquidity(bulk_data)
        
        # Step 4: Categorize by tier
        logger.info("=" * 60)
        logger.info("STEP 4: Categorize by liquidity tier")
        logger.info("=" * 60)
        tiers = self.categorize_by_tier(listings, liquidity)
        
        results["tier_distribution"] = {
            f"tier{t}": len(assets) for t, assets in tiers.items()
        }
        
        # Step 5: Insert to database
        logger.info("=" * 60)
        logger.info("STEP 5: Insert to database")
        logger.info("=" * 60)
        insert_stats = self.insert_to_database(
            tiers,
            tier1_limit=tier1_limit,
            tier2_limit=tier2_limit
        )
        results["insert_stats"] = insert_stats
        
        # Summary
        total_active = insert_stats["tier1_active"] + insert_stats["tier2_active"]
        logger.info("=" * 60)
        logger.info(f"SMART UNIVERSE BUILDER COMPLETE")
        logger.info(f"  Total listings: {len(listings)}")
        logger.info(f"  Active assets: {total_active}")
        logger.info(f"  API calls used: ~{len(self._exchanges) * 2} (instead of {len(listings)})")
        logger.info("=" * 60)
        
        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Smart Universe Builder")
    parser.add_argument(
        "--scope",
        choices=["US_EU", "AFRICA"],
        default="US_EU",
        help="Market scope"
    )
    parser.add_argument(
        "--tier1-limit",
        type=int,
        default=2000,
        help="Max Tier 1 assets to activate"
    )
    parser.add_argument(
        "--tier2-limit",
        type=int,
        default=1000,
        help="Max Tier 2 assets to activate"
    )
    
    args = parser.parse_args()
    
    builder = SmartUniverseBuilder(market_scope=args.scope)
    results = builder.run(
        tier1_limit=args.tier1_limit,
        tier2_limit=args.tier2_limit
    )
    
    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
