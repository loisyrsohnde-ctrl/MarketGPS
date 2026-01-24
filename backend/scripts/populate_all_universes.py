"""
MarketGPS - Master Universe Population Script
Runs all universe expansion scripts to populate empty asset categories.

SAFE: All scripts use UPSERT - no data is deleted.
IDEMPOTENT: Safe to run multiple times.

This script populates:
1. Crypto (100+ cryptocurrencies)
2. Commodities (ETF proxies for metals, energy, agriculture)
3. Forex (Major and exotic currency pairs)
4. Derivatives (Futures + Options underlyings)
5. Africa Expansion (EGX, NSE, CSE, GSE, BVMT)

Run: python scripts/populate_all_universes.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)


def run_script(script_name: str, description: str) -> bool:
    """Run a universe expansion script."""
    script_path = project_root / "scripts" / script_name
    
    if not script_path.exists():
        print(f"  ✗ Script not found: {script_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=False,
            text=True,
            timeout=300  # 5 minutes max per script
        )
        
        if result.returncode == 0:
            print(f"  ✓ {description} completed successfully")
            return True
        else:
            print(f"  ✗ {description} failed with code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ {description} timed out")
        return False
    except Exception as e:
        print(f"  ✗ {description} error: {e}")
        return False


def get_universe_stats(store: SQLiteStore) -> dict:
    """Get current universe statistics."""
    stats = {}
    with store._get_connection() as conn:
        # By asset type
        cursor = conn.execute("""
            SELECT asset_type, COUNT(*) as count
            FROM universe WHERE active = 1
            GROUP BY asset_type
            ORDER BY count DESC
        """)
        stats["by_type"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By market scope
        cursor = conn.execute("""
            SELECT market_scope, COUNT(*) as count
            FROM universe WHERE active = 1
            GROUP BY market_scope
        """)
        stats["by_scope"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Africa by exchange
        cursor = conn.execute("""
            SELECT exchange_code, COUNT(*) as count
            FROM universe 
            WHERE market_scope = 'AFRICA' AND active = 1
            GROUP BY exchange_code
            ORDER BY count DESC
        """)
        stats["africa_exchanges"] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total
        cursor = conn.execute("SELECT COUNT(*) FROM universe WHERE active = 1")
        stats["total"] = cursor.fetchone()[0]
    
    return stats


def print_stats(stats: dict, title: str):
    """Print formatted statistics."""
    print(f"\n{'-'*60}")
    print(title)
    print('-'*60)
    
    print(f"\nTotal Active Assets: {stats['total']}")
    
    print("\nBy Asset Type:")
    for asset_type, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
        print(f"  {asset_type}: {count}")
    
    print("\nBy Market Scope:")
    for scope, count in stats["by_scope"].items():
        print(f"  {scope}: {count}")
    
    if stats["africa_exchanges"]:
        print("\nAfrica by Exchange:")
        for exchange, count in sorted(stats["africa_exchanges"].items(), key=lambda x: -x[1]):
            print(f"  {exchange}: {count}")


def main():
    """Main function to run all universe expansion scripts."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate All Universes")
    parser.add_argument("--skip-crypto", action="store_true", help="Skip crypto universe")
    parser.add_argument("--skip-commodities", action="store_true", help="Skip commodities universe")
    parser.add_argument("--skip-forex", action="store_true", help="Skip forex universe")
    parser.add_argument("--skip-derivatives", action="store_true", help="Skip derivatives universe")
    parser.add_argument("--skip-africa", action="store_true", help="Skip Africa expansion")
    parser.add_argument("--africa-only", action="store_true", help="Only run Africa expansion")
    args = parser.parse_args()
    
    print("=" * 70)
    print("MarketGPS - Master Universe Population")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize store
    store = SQLiteStore()
    
    # Show initial state
    initial_stats = get_universe_stats(store)
    print_stats(initial_stats, "INITIAL STATE")
    
    # Scripts to run
    scripts = []
    
    if args.africa_only:
        scripts = [
            ("expand_africa_universe.py", "Africa Universe Expansion"),
        ]
    else:
        if not args.skip_crypto:
            scripts.append(("add_crypto_universe.py", "Crypto Universe"))
        if not args.skip_commodities:
            scripts.append(("add_commodities_universe.py", "Commodities Universe"))
        if not args.skip_forex:
            scripts.append(("add_forex_universe.py", "Forex Universe"))
        if not args.skip_derivatives:
            scripts.append(("add_derivatives_universe.py", "Derivatives Universe"))
        if not args.skip_africa:
            scripts.append(("expand_africa_universe.py", "Africa Universe Expansion"))
    
    # Run scripts
    results = {}
    for script_name, description in scripts:
        success = run_script(script_name, description)
        results[description] = success
        time.sleep(1)  # Brief pause between scripts
    
    # Show final state
    final_stats = get_universe_stats(store)
    print_stats(final_stats, "FINAL STATE")
    
    # Summary
    print(f"\n{'='*70}")
    print("EXECUTION SUMMARY")
    print('='*70)
    
    for description, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {description}: {status}")
    
    added = final_stats["total"] - initial_stats["total"]
    print(f"\nTotal assets added: {added}")
    
    # Check for empty categories
    empty_types = []
    expected_types = ["EQUITY", "ETF", "CRYPTO", "COMMODITY", "FX", "FUTURE", "OPTION", "BOND"]
    for asset_type in expected_types:
        if asset_type not in final_stats["by_type"]:
            empty_types.append(asset_type)
    
    if empty_types:
        print(f"\n⚠ Empty asset types: {', '.join(empty_types)}")
    
    # Check Africa exchanges
    africa_exchanges = ["JSE", "NGX", "BRVM", "EGX", "NSE", "CSE", "GSE", "BVMT"]
    empty_africa = [ex for ex in africa_exchanges if ex not in final_stats["africa_exchanges"]]
    if empty_africa:
        print(f"\n⚠ Empty Africa exchanges: {', '.join(empty_africa)}")
    
    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print('='*70)
    print("1. Fetch price data:")
    print("   python -m pipeline.jobs --gating --scope US_EU")
    print("   python -m pipeline.jobs --gating --scope AFRICA")
    print()
    print("2. Calculate scores:")
    print("   python -m pipeline.jobs --rotation --scope US_EU")
    print("   python -m pipeline.jobs --rotation --scope AFRICA")
    print()
    print("3. Score alternative assets:")
    print("   python scripts/score_alternative_assets.py --type CRYPTO --limit 100")
    print("   python scripts/score_alternative_assets.py --type FX --limit 50")
    print()
    print("✓ Universe population complete!")


if __name__ == "__main__":
    main()
