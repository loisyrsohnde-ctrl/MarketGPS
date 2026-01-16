"""
MarketGPS v13.0 - Africa Universe Builder
Constructs and maintains the AFRICA universe from multiple sources.

Sources (priority order):
1. EODHD exchange-symbol-list API
2. Manual CSV import (data/universe/universe_africa.csv)
3. AfricaFileProvider (for official exchange data - future)

Supported Exchanges:
- JSE (Johannesburg Stock Exchange, South Africa)
- NGX (Nigerian Exchange)
- BRVM (Bourse Régionale des Valeurs Mobilières, West Africa)
- EGX (Egyptian Exchange)
- NSE (Nairobi Securities Exchange, Kenya)
"""
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Literal

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# AFRICA EXCHANGE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

AFRICA_EXCHANGES = {
    "JSE": {
        "name": "Johannesburg Stock Exchange",
        "country": "ZA",
        "currency": "ZAR",
        "eodhd_code": "JSE",
        "tier": 1,  # High liquidity
        "active": True
    },
    "NGX": {
        "name": "Nigerian Exchange",
        "country": "NG",
        "currency": "NGN",
        "eodhd_code": "NG",  # EODHD uses "NG" for Nigeria
        "tier": 2,
        "active": True
    },
    "BRVM": {
        "name": "BRVM (West Africa)",
        "country": "CI",  # Côte d'Ivoire (headquarters)
        "currency": "XOF",
        "eodhd_code": "BRVM",
        "tier": 3,
        "active": True
    },
    "EGX": {
        "name": "Egyptian Exchange",
        "country": "EG",
        "currency": "EGP",
        "eodhd_code": "CA",  # Cairo
        "tier": 2,
        "active": True
    },
    "NSE": {
        "name": "Nairobi Securities Exchange",
        "country": "KE",
        "currency": "KES",
        "eodhd_code": "NSE",
        "tier": 2,
        "active": False  # Enable when data available
    }
}

# Top stocks per exchange (manually curated for tier 1)
AFRICA_TIER1_STOCKS = {
    "JSE": [
        "NPN", "AGL", "BID", "SBK", "SOL", "FSR", "MTN", "SHP", "ABG", "NED",
        "REM", "VOD", "BTI", "CFR", "MNP", "SLM", "INP", "DSY", "GFI", "AMS"
    ],
    "NGX": [
        "DANGCEM", "MTNN", "AIRTELAFRI", "BUACEMENT", "GTCO", "ZENITHBANK",
        "NESTLE", "SEPLAT", "FBNH", "ACCESSCORP", "STANBIC", "UBA", "WAPCO"
    ],
    "BRVM": [
        "SNTS", "SGBC", "ONTBF", "SIBC", "BOAB", "CABC", "ETIT", "NSBC"
    ]
}


class AfricaUniverseBuilder:
    """
    Builds and maintains the AFRICA universe.
    
    Features:
    - Fetch listings from EODHD API
    - Import from CSV file
    - Merge multiple sources
    - Apply tier classification
    - Validate data quality
    """
    
    def __init__(self, store: Optional[SQLiteStore] = None):
        """Initialize the builder."""
        self._store = store or SQLiteStore()
        self._config = get_config()
        self._csv_path = Path("data/universe/universe_africa.csv")
    
    def build_from_eodhd(self, exchanges: List[str] = None) -> Dict[str, int]:
        """
        Build universe from EODHD exchange listings.
        
        Args:
            exchanges: List of exchange codes to fetch (default: all active)
            
        Returns:
            Dict with counts per exchange
        """
        from providers.eodhd import EODHDProvider
        
        provider = EODHDProvider()
        if not provider.is_configured:
            logger.error("EODHD API key not configured. Cannot build universe from API.")
            return {"error": "EODHD not configured"}
        
        exchanges = exchanges or [
            code for code, info in AFRICA_EXCHANGES.items()
            if info.get("active", False)
        ]
        
        results = {}
        all_assets = []
        
        for exchange_code in exchanges:
            exchange_info = AFRICA_EXCHANGES.get(exchange_code)
            if not exchange_info:
                logger.warning(f"Unknown exchange: {exchange_code}")
                continue
            
            eodhd_code = exchange_info["eodhd_code"]
            
            try:
                logger.info(f"Fetching listings for {exchange_code} ({eodhd_code})...")
                listings = provider.get_listings(eodhd_code)
                
                if not listings:
                    logger.warning(f"No listings returned for {exchange_code}")
                    results[exchange_code] = 0
                    continue
                
                # Transform to our format
                for item in listings:
                    symbol = item.get("Code", "")
                    name = item.get("Name", symbol)
                    asset_type = self._map_asset_type(item.get("Type", "Common Stock"))
                    
                    # Skip invalid entries
                    if not symbol or len(symbol) > 20:
                        continue
                    
                    # Determine tier
                    tier = 1 if symbol in AFRICA_TIER1_STOCKS.get(exchange_code, []) else 2
                    
                    asset = {
                        "asset_id": f"{symbol}.{eodhd_code}",
                        "symbol": symbol,
                        "name": name[:200] if name else symbol,
                        "asset_type": asset_type,
                        "market_code": exchange_code,
                        "exchange_code": eodhd_code,
                        "currency": exchange_info["currency"],
                        "country": exchange_info["country"],
                        "tier": tier,
                        "priority_level": tier,
                        "active": 1,
                        "data_source": "EODHD"
                    }
                    all_assets.append(asset)
                
                results[exchange_code] = len([a for a in all_assets if a["market_code"] == exchange_code])
                logger.info(f"  {exchange_code}: {results[exchange_code]} assets")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to fetch {exchange_code}: {e}")
                results[exchange_code] = 0
        
        # Bulk upsert to database
        if all_assets:
            self._store.bulk_upsert_assets(all_assets, market_scope="AFRICA")
            logger.info(f"Inserted {len(all_assets)} AFRICA assets into universe")
        
        results["total"] = len(all_assets)
        return results
    
    def build_from_csv(self, csv_path: str = None) -> Dict[str, int]:
        """
        Build universe from CSV file.
        
        CSV format:
        asset_id,symbol,name,asset_type,market_code,exchange_code,currency,country,tier
        
        Args:
            csv_path: Path to CSV file (default: data/universe/universe_africa.csv)
            
        Returns:
            Dict with counts
        """
        path = Path(csv_path) if csv_path else self._csv_path
        
        if not path.exists():
            logger.warning(f"CSV file not found: {path}")
            return {"error": f"File not found: {path}"}
        
        assets = []
        errors = 0
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    symbol = row.get("symbol", "").strip()
                    if not symbol:
                        continue
                    
                    exchange_code = row.get("exchange_code", row.get("market_code", "JSE"))
                    exchange_info = AFRICA_EXCHANGES.get(row.get("market_code", "JSE"), {})
                    
                    asset = {
                        "asset_id": row.get("asset_id", f"{symbol}.{exchange_code}"),
                        "symbol": symbol,
                        "name": row.get("name", symbol),
                        "asset_type": row.get("asset_type", "EQUITY"),
                        "market_code": row.get("market_code", "JSE"),
                        "exchange_code": exchange_code,
                        "currency": row.get("currency", exchange_info.get("currency", "ZAR")),
                        "country": row.get("country", exchange_info.get("country", "ZA")),
                        "tier": int(row.get("tier", 2)),
                        "priority_level": int(row.get("priority_level", row.get("tier", 2))),
                        "active": 1,
                        "data_source": "CSV"
                    }
                    assets.append(asset)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse row: {row} - {e}")
                    errors += 1
        
        # Bulk upsert
        if assets:
            self._store.bulk_upsert_assets(assets, market_scope="AFRICA")
            logger.info(f"Imported {len(assets)} assets from CSV")
        
        return {
            "imported": len(assets),
            "errors": errors,
            "source": str(path)
        }
    
    def export_to_csv(self, output_path: str = None) -> str:
        """
        Export current AFRICA universe to CSV.
        
        Args:
            output_path: Output file path (default: data/universe/universe_africa.csv)
            
        Returns:
            Path to exported file
        """
        path = Path(output_path) if output_path else self._csv_path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get all AFRICA assets
        assets = self._store.get_active_assets(market_scope="AFRICA")
        
        if not assets:
            logger.warning("No AFRICA assets to export")
            return str(path)
        
        fieldnames = [
            "asset_id", "symbol", "name", "asset_type", "market_code",
            "exchange_code", "currency", "country", "tier", "priority_level"
        ]
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for asset in assets:
                writer.writerow({
                    "asset_id": asset.asset_id,
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "asset_type": asset.asset_type.value if hasattr(asset.asset_type, 'value') else asset.asset_type,
                    "market_code": getattr(asset, 'market_code', 'JSE'),
                    "exchange_code": asset.exchange,
                    "currency": asset.currency,
                    "country": asset.country,
                    "tier": asset.tier,
                    "priority_level": getattr(asset, 'priority_level', asset.tier)
                })
        
        logger.info(f"Exported {len(assets)} assets to {path}")
        return str(path)
    
    def validate_universe(self) -> Dict[str, any]:
        """
        Validate the AFRICA universe for data quality.
        
        Returns:
            Dict with validation results
        """
        assets = self._store.get_active_assets(market_scope="AFRICA")
        
        results = {
            "total": len(assets),
            "by_exchange": {},
            "by_tier": {1: 0, 2: 0, 3: 0},
            "missing_currency": 0,
            "missing_country": 0,
            "issues": []
        }
        
        for asset in assets:
            # Count by exchange
            market_code = getattr(asset, 'market_code', 'UNKNOWN')
            results["by_exchange"][market_code] = results["by_exchange"].get(market_code, 0) + 1
            
            # Count by tier
            tier = asset.tier if asset.tier in [1, 2, 3] else 2
            results["by_tier"][tier] += 1
            
            # Check for missing data
            if not asset.currency:
                results["missing_currency"] += 1
            if not asset.country:
                results["missing_country"] += 1
        
        # Add issues
        if results["missing_currency"] > 0:
            results["issues"].append(f"{results['missing_currency']} assets missing currency")
        if results["missing_country"] > 0:
            results["issues"].append(f"{results['missing_country']} assets missing country")
        
        return results
    
    def _map_asset_type(self, eodhd_type: str) -> str:
        """Map EODHD asset type to our format."""
        type_map = {
            "Common Stock": "EQUITY",
            "Preferred Stock": "EQUITY",
            "ETF": "ETF",
            "Fund": "FUND",
            "Bond": "BOND",
            "Index": "INDEX"
        }
        return type_map.get(eodhd_type, "EQUITY")


def build_africa_universe(
    source: Literal["eodhd", "csv", "both"] = "both",
    csv_path: str = None
) -> Dict[str, any]:
    """
    Build AFRICA universe from specified source(s).
    
    Args:
        source: "eodhd", "csv", or "both"
        csv_path: Path to CSV file (for csv/both modes)
        
    Returns:
        Dict with build results
    """
    builder = AfricaUniverseBuilder()
    results = {}
    
    if source in ("eodhd", "both"):
        logger.info("Building AFRICA universe from EODHD...")
        results["eodhd"] = builder.build_from_eodhd()
    
    if source in ("csv", "both"):
        logger.info("Building AFRICA universe from CSV...")
        results["csv"] = builder.build_from_csv(csv_path)
    
    # Validate
    results["validation"] = builder.validate_universe()
    
    return results


# ═══════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketGPS AFRICA Universe Builder")
    parser.add_argument(
        "--source",
        choices=["eodhd", "csv", "both"],
        default="both",
        help="Data source to use"
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        help="Path to CSV file"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export current universe to CSV"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current universe"
    )
    
    args = parser.parse_args()
    
    builder = AfricaUniverseBuilder()
    
    if args.export:
        path = builder.export_to_csv()
        print(f"Exported to: {path}")
    elif args.validate:
        results = builder.validate_universe()
        print("\nAFRICA Universe Validation:")
        print(f"  Total assets: {results['total']}")
        print(f"  By exchange: {results['by_exchange']}")
        print(f"  By tier: {results['by_tier']}")
        if results['issues']:
            print(f"  Issues: {results['issues']}")
    else:
        results = build_africa_universe(source=args.source, csv_path=args.csv_path)
        print("\nBuild Results:")
        for key, value in results.items():
            print(f"  {key}: {value}")
