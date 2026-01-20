"""
MarketGPS - Prepare Universe Script (PRE-GATING)
Reduces the active universe to a manageable size BEFORE running the pipeline.

This is an ADD-ONLY optimization that doesn't change the scoring algorithm.
It simply marks lower-priority assets as inactive so the pipeline processes
fewer assets initially.

Strategy:
- US: Top 3000 assets (by existing tier, or alphabetically if no tier)
- EU: Top 1500 assets total (across all exchanges)  
- Africa: All assets active (smaller universe)

Total target: ~5000 active assets

Usage:
    python scripts/prepare_universe.py [--limit-us 3000] [--limit-eu 1500] [--all-africa]
    python scripts/prepare_universe.py --reset  # Reset all to active
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)


def prepare_universe(
    limit_us: int = 3000,
    limit_eu: int = 1500,
    all_africa: bool = True,
    dry_run: bool = False
) -> dict:
    """
    Prepare the universe by activating only high-priority assets.
    
    Strategy:
    1. First, mark ALL assets as inactive
    2. Then, activate top N per region based on tier and priority
    3. Africa gets all assets (smaller, specialized market)
    
    Args:
        limit_us: Maximum US assets to activate
        limit_eu: Maximum EU assets to activate
        all_africa: If True, activate all Africa assets
        dry_run: If True, don't actually modify the database
        
    Returns:
        Dict with statistics
    """
    config = get_config()
    store = SQLiteStore(config.storage.sqlite_path)
    
    stats = {
        "total_assets": 0,
        "us_activated": 0,
        "eu_activated": 0,
        "africa_activated": 0,
        "total_activated": 0,
        "total_deactivated": 0,
    }
    
    print("=" * 60)
    print("MarketGPS - Prepare Universe (Pre-Gating)")
    print("=" * 60)
    print()
    
    with store._get_conn() as conn:
        # Get total count
        cursor = conn.execute("SELECT COUNT(*) FROM universe")
        stats["total_assets"] = cursor.fetchone()[0]
        print(f"Total assets in universe: {stats['total_assets']:,}")
        
        if dry_run:
            print("\n[DRY RUN - No changes will be made]")
        
        # Step 1: Deactivate ALL assets first
        if not dry_run:
            conn.execute("UPDATE universe SET active = 0")
            print("\n✓ All assets marked as inactive")
        
        # Step 2: Activate US assets (top N by tier, then by symbol)
        print(f"\nActivating top {limit_us:,} US assets...")
        us_query = """
            SELECT asset_id FROM universe 
            WHERE market_scope = 'US_EU' AND market_code = 'US'
            ORDER BY tier ASC, priority_level ASC, symbol ASC
            LIMIT ?
        """
        cursor = conn.execute(us_query, (limit_us,))
        us_assets = [row[0] for row in cursor.fetchall()]
        
        if not dry_run and us_assets:
            placeholders = ",".join("?" * len(us_assets))
            conn.execute(
                f"UPDATE universe SET active = 1, tier = 1 WHERE asset_id IN ({placeholders})",
                us_assets
            )
        
        stats["us_activated"] = len(us_assets)
        print(f"  ✓ {stats['us_activated']:,} US assets activated")
        
        # Step 3: Activate EU assets (top N by tier, then by symbol)
        print(f"\nActivating top {limit_eu:,} EU assets...")
        eu_query = """
            SELECT asset_id FROM universe 
            WHERE market_scope = 'US_EU' AND market_code = 'EU'
            ORDER BY tier ASC, priority_level ASC, symbol ASC
            LIMIT ?
        """
        cursor = conn.execute(eu_query, (limit_eu,))
        eu_assets = [row[0] for row in cursor.fetchall()]
        
        if not dry_run and eu_assets:
            placeholders = ",".join("?" * len(eu_assets))
            conn.execute(
                f"UPDATE universe SET active = 1, tier = 1 WHERE asset_id IN ({placeholders})",
                eu_assets
            )
        
        stats["eu_activated"] = len(eu_assets)
        print(f"  ✓ {stats['eu_activated']:,} EU assets activated")
        
        # Step 4: Activate Africa assets (all or limited)
        if all_africa:
            print("\nActivating ALL Africa assets...")
            africa_query = """
                SELECT asset_id FROM universe 
                WHERE market_scope = 'AFRICA'
                ORDER BY tier ASC, priority_level ASC, symbol ASC
            """
            cursor = conn.execute(africa_query)
        else:
            print("\nActivating top 500 Africa assets...")
            africa_query = """
                SELECT asset_id FROM universe 
                WHERE market_scope = 'AFRICA'
                ORDER BY tier ASC, priority_level ASC, symbol ASC
                LIMIT 500
            """
            cursor = conn.execute(africa_query)
        
        africa_assets = [row[0] for row in cursor.fetchall()]
        
        if not dry_run and africa_assets:
            placeholders = ",".join("?" * len(africa_assets))
            conn.execute(
                f"UPDATE universe SET active = 1, tier = 1 WHERE asset_id IN ({placeholders})",
                africa_assets
            )
        
        stats["africa_activated"] = len(africa_assets)
        print(f"  ✓ {stats['africa_activated']:,} Africa assets activated")
        
        # Calculate totals
        stats["total_activated"] = (
            stats["us_activated"] + 
            stats["eu_activated"] + 
            stats["africa_activated"]
        )
        stats["total_deactivated"] = stats["total_assets"] - stats["total_activated"]
        
        if not dry_run:
            conn.commit()
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total assets:     {stats['total_assets']:,}")
    print(f"  US activated:     {stats['us_activated']:,}")
    print(f"  EU activated:     {stats['eu_activated']:,}")
    print(f"  Africa activated: {stats['africa_activated']:,}")
    print(f"  ---")
    print(f"  TOTAL ACTIVE:     {stats['total_activated']:,}")
    print(f"  INACTIVE:         {stats['total_deactivated']:,}")
    print("=" * 60)
    
    if not dry_run:
        print("\n✅ Universe prepared! You can now run the pipeline:")
        print()
        print("  # US/EU pipeline (will process ~4,500 assets)")
        print("  python -m pipeline.jobs --full-pipeline --scope US_EU --production --mode daily_full")
        print()
        print("  # Africa pipeline")
        print("  python -m pipeline.jobs --full-pipeline --scope AFRICA --production --mode daily_full")
    
    return stats


def reset_universe(dry_run: bool = False) -> dict:
    """
    Reset all assets to active state.
    
    Args:
        dry_run: If True, don't actually modify the database
        
    Returns:
        Dict with statistics
    """
    config = get_config()
    store = SQLiteStore(config.storage.sqlite_path)
    
    print("=" * 60)
    print("MarketGPS - Reset Universe (All Active)")
    print("=" * 60)
    print()
    
    with store._get_conn() as conn:
        # Get total count
        cursor = conn.execute("SELECT COUNT(*) FROM universe")
        total = cursor.fetchone()[0]
        print(f"Total assets in universe: {total:,}")
        
        if dry_run:
            print("\n[DRY RUN - No changes will be made]")
        else:
            conn.execute("UPDATE universe SET active = 1")
            conn.commit()
            print(f"\n✓ All {total:,} assets marked as ACTIVE")
    
    return {"total": total, "activated": total}


def main():
    parser = argparse.ArgumentParser(
        description="Prepare MarketGPS universe for pipeline processing"
    )
    parser.add_argument(
        "--limit-us",
        type=int,
        default=3000,
        help="Maximum US assets to activate (default: 3000)"
    )
    parser.add_argument(
        "--limit-eu",
        type=int,
        default=1500,
        help="Maximum EU assets to activate (default: 1500)"
    )
    parser.add_argument(
        "--all-africa",
        action="store_true",
        default=True,
        help="Activate all Africa assets (default: True)"
    )
    parser.add_argument(
        "--limit-africa",
        type=int,
        default=None,
        help="If set, limit Africa assets to this number"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset all assets to active (undo prepare)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        reset_universe(dry_run=args.dry_run)
    else:
        # If limit-africa is set, don't activate all
        all_africa = args.limit_africa is None
        
        prepare_universe(
            limit_us=args.limit_us,
            limit_eu=args.limit_eu,
            all_africa=all_africa,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()
