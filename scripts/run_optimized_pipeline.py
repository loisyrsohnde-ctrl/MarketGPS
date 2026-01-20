#!/usr/bin/env python3
"""
MarketGPS - Optimized Pipeline Runner
Orchestrates the entire pipeline with API call optimization.

This script replaces the need to run multiple commands manually.
It handles the complete flow:
1. Build universe with smart pre-filtering
2. Fetch price data using bulk endpoints
3. Run gating on active assets
4. Score eligible assets
5. Fetch logos for top scored

API CALL COMPARISON:
┌────────────────────────────────────────────────────────────────┐
│                    OLD APPROACH                                 │
├────────────────────────────────────────────────────────────────┤
│ expand_universe.py: 20,000 listings × 1 call = 20,000 calls    │
│ pipeline (gating):  20,000 assets × 1 call = 20,000 calls      │
│ pipeline (scoring): 10,000 eligible × 2 calls = 20,000 calls   │
│ TOTAL: ~60,000 API calls                                        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   NEW OPTIMIZED APPROACH                        │
├────────────────────────────────────────────────────────────────┤
│ smart_universe_builder: 20 exchanges × 2 calls = 40 calls      │
│ smart_bulk_fetcher:     20 exchanges × 1 call = 20 calls       │
│ gating:                 Uses cached Parquet = 0 new calls      │
│ scoring:                Uses cached Parquet = 0 new calls      │
│ full_history (new):     ~2,000 new assets × 1 call = 2,000     │
│ TOTAL: ~2,060 API calls (97% reduction!)                        │
└────────────────────────────────────────────────────────────────┘

Usage:
    python scripts/run_optimized_pipeline.py --scope US_EU
    python scripts/run_optimized_pipeline.py --scope AFRICA
    python scripts/run_optimized_pipeline.py --scope US_EU --skip-history  # Fast daily update
    python scripts/run_optimized_pipeline.py --full  # Both scopes, full rebuild
"""
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_logger

logger = get_logger(__name__)


def print_banner(title: str):
    """Print a section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def run_smart_universe(scope: str, tier1_limit: int, tier2_limit: int) -> Dict:
    """Run the smart universe builder."""
    print_banner(f"STEP 1: Smart Universe Builder ({scope})")
    
    from scripts.smart_universe_builder import SmartUniverseBuilder
    
    builder = SmartUniverseBuilder(market_scope=scope)
    return builder.run(tier1_limit=tier1_limit, tier2_limit=tier2_limit)


def run_smart_bulk_fetch(
    scope: str, 
    fetch_history: bool = True,
    history_years: int = 5,
    limit_new: int = None
) -> Dict:
    """Run the smart bulk fetcher."""
    print_banner(f"STEP 2: Smart Bulk Fetcher ({scope})")
    
    from pipeline.smart_bulk_fetcher import SmartBulkFetcher
    
    fetcher = SmartBulkFetcher(market_scope=scope)
    return fetcher.run(
        fetch_new_history=fetch_history,
        history_years=history_years,
        limit_new=limit_new
    )


def run_gating(scope: str) -> Dict:
    """Run the gating job."""
    print_banner(f"STEP 3: Gating Job ({scope})")
    
    from storage.sqlite_store import SQLiteStore
    from storage.parquet_store import ParquetStore
    from pipeline.gating import GatingJob
    
    store = SQLiteStore()
    parquet = ParquetStore(market_scope=scope)
    
    if scope == "AFRICA":
        from pipeline.africa.gating_africa import GatingAfricaJob
        job = GatingAfricaJob(store=store, parquet_store=parquet)
    else:
        job = GatingJob(store=store, parquet_store=parquet, market_scope=scope)
    
    return job.run()


def run_scoring(scope: str) -> Dict:
    """Run the scoring job."""
    print_banner(f"STEP 4: Scoring Job ({scope})")
    
    from pipeline.job_runner import ProductionJobRunner
    
    runner = ProductionJobRunner(market_scope=scope)
    result = runner.run_scoring(mode="daily_full")
    
    return {
        "status": result.status,
        "processed": result.assets_processed,
        "success": result.assets_success,
        "failed": result.assets_failed,
        "duration": result.duration_seconds,
    }


def run_logo_fetch(scope: str, limit: int = 200) -> Dict:
    """Run the logo fetcher for top scored."""
    print_banner(f"STEP 5: Logo Fetcher ({scope})")
    
    from pipeline.smart_logo_fetcher import SmartLogoFetcher
    
    fetcher = SmartLogoFetcher()
    return fetcher.run(scope=scope, top_scored=True, limit=limit)


def run_full_pipeline(
    scope: str,
    tier1_limit: int = 2000,
    tier2_limit: int = 1000,
    fetch_history: bool = True,
    history_years: int = 5,
    limit_new_history: int = None,
    fetch_logos: bool = True,
    logo_limit: int = 200
) -> Dict:
    """
    Run the complete optimized pipeline.
    
    Args:
        scope: US_EU or AFRICA
        tier1_limit: Max Tier 1 assets
        tier2_limit: Max Tier 2 assets
        fetch_history: Fetch full history for new assets
        history_years: Years of history
        limit_new_history: Limit new asset history fetches
        fetch_logos: Fetch logos for top scored
        logo_limit: Max logos to fetch
        
    Returns:
        Dict with all results
    """
    start_time = time.time()
    
    results = {
        "scope": scope,
        "started_at": datetime.now().isoformat(),
        "steps": {}
    }
    
    try:
        # Step 1: Smart Universe
        results["steps"]["universe"] = run_smart_universe(
            scope, tier1_limit, tier2_limit
        )
        
        # Step 2: Smart Bulk Fetch
        results["steps"]["bulk_fetch"] = run_smart_bulk_fetch(
            scope, 
            fetch_history=fetch_history,
            history_years=history_years,
            limit_new=limit_new_history
        )
        
        # Step 3: Gating
        results["steps"]["gating"] = run_gating(scope)
        
        # Step 4: Scoring
        results["steps"]["scoring"] = run_scoring(scope)
        
        # Step 5: Logos (optional)
        if fetch_logos:
            results["steps"]["logos"] = run_logo_fetch(scope, logo_limit)
        
        results["status"] = "success"
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
    
    duration = time.time() - start_time
    results["duration_seconds"] = round(duration, 1)
    results["completed_at"] = datetime.now().isoformat()
    
    return results


def print_summary(results: Dict):
    """Print a summary of results."""
    print_banner("PIPELINE SUMMARY")
    
    print(f"Scope: {results.get('scope')}")
    print(f"Status: {results.get('status', 'unknown').upper()}")
    print(f"Duration: {results.get('duration_seconds', 0)}s")
    print()
    
    steps = results.get("steps", {})
    
    if "universe" in steps:
        u = steps["universe"]
        print(f"Universe: {u.get('total_listings', 0)} listings")
        print(f"  Tier distribution: {u.get('tier_distribution', {})}")
        print(f"  Active: {u.get('insert_stats', {}).get('tier1_active', 0) + u.get('insert_stats', {}).get('tier2_active', 0)}")
    
    if "bulk_fetch" in steps:
        b = steps["bulk_fetch"]
        print(f"Bulk Fetch: {b.get('bulk_fetch', {}).get('total', 0)} assets")
        print(f"  Updated: {b.get('updated', {}).get('updated', 0)}")
        print(f"  New: {b.get('new_assets', {}).get('success', 0)}")
    
    if "gating" in steps:
        g = steps["gating"]
        print(f"Gating: {g.get('total', 0)} processed")
        print(f"  Eligible: {g.get('eligible', 0)}")
    
    if "scoring" in steps:
        s = steps["scoring"]
        print(f"Scoring: {s.get('processed', 0)} processed")
        print(f"  Success: {s.get('success', 0)}")
    
    if "logos" in steps:
        l = steps["logos"]
        print(f"Logos: {l.get('success', 0)} fetched")
    
    print()
    
    if results.get("error"):
        print(f"ERROR: {results['error']}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MarketGPS Optimized Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard daily run for US/EU
  python scripts/run_optimized_pipeline.py --scope US_EU
  
  # Quick update (skip new asset history)
  python scripts/run_optimized_pipeline.py --scope US_EU --skip-history
  
  # Africa with custom limits
  python scripts/run_optimized_pipeline.py --scope AFRICA --tier1-limit 500
  
  # Full rebuild both scopes
  python scripts/run_optimized_pipeline.py --full
        """
    )
    
    parser.add_argument(
        "--scope",
        choices=["US_EU", "AFRICA"],
        default="US_EU",
        help="Market scope to process"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run for both US_EU and AFRICA scopes"
    )
    parser.add_argument(
        "--tier1-limit",
        type=int,
        default=2000,
        help="Max Tier 1 (very liquid) assets to activate"
    )
    parser.add_argument(
        "--tier2-limit",
        type=int,
        default=1000,
        help="Max Tier 2 (liquid) assets to activate"
    )
    parser.add_argument(
        "--skip-history",
        action="store_true",
        help="Skip fetching full history for new assets (faster)"
    )
    parser.add_argument(
        "--history-years",
        type=int,
        default=5,
        help="Years of history to fetch for new assets"
    )
    parser.add_argument(
        "--limit-new",
        type=int,
        default=None,
        help="Limit number of new assets to fetch history for"
    )
    parser.add_argument(
        "--skip-logos",
        action="store_true",
        help="Skip fetching logos"
    )
    parser.add_argument(
        "--logo-limit",
        type=int,
        default=200,
        help="Max logos to fetch"
    )
    
    args = parser.parse_args()
    
    print_banner("MARKETGPS OPTIMIZED PIPELINE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scope: {args.scope if not args.full else 'US_EU + AFRICA'}")
    print(f"Tier limits: T1={args.tier1_limit}, T2={args.tier2_limit}")
    print(f"Fetch history: {not args.skip_history}")
    print(f"Fetch logos: {not args.skip_logos}")
    
    scopes = ["US_EU", "AFRICA"] if args.full else [args.scope]
    all_results = {}
    
    for scope in scopes:
        results = run_full_pipeline(
            scope=scope,
            tier1_limit=args.tier1_limit,
            tier2_limit=args.tier2_limit,
            fetch_history=not args.skip_history,
            history_years=args.history_years,
            limit_new_history=args.limit_new,
            fetch_logos=not args.skip_logos,
            logo_limit=args.logo_limit
        )
        
        all_results[scope] = results
        print_summary(results)
    
    print_banner("COMPLETE")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
