"""
MarketGPS v13.0 - Pipeline Jobs CLI (SCOPE-AWARE + PRODUCTION GRADE)
Command-line interface for running pipeline jobs with market scope support.
Supports: US_EU (default), AFRICA
Modes: daily_full, hourly_overlay, on_demand
"""
import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Literal

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from pipeline.universe import UniverseJob
from pipeline.gating import GatingJob
from pipeline.rotation import RotationJob

logger = get_logger(__name__)

MarketScope = Literal["US_EU", "AFRICA"]
JobMode = Literal["daily_full", "hourly_overlay", "on_demand"]


def run_init_universe(args) -> int:
    """Initialize the universe for a specific scope."""
    scope: MarketScope = getattr(args, 'scope', 'US_EU')
    
    print("\n" + "=" * 60)
    print(f"MarketGPS - Initialize Universe [{scope}]")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    try:
        store = SQLiteStore()
        
        # Check if we have a CSV source for this scope
        csv_path = getattr(args, 'from_csv', None)
        
        if csv_path:
            results = import_universe_from_csv(store, csv_path, scope)
        else:
            job = UniverseJob(store=store)
            results = job.run()
            
            # Update market_scope for all imported assets
            if scope != "US_EU":
                with store._get_connection() as conn:
                    conn.execute(
                        "UPDATE universe SET market_scope = ? WHERE market_scope IS NULL OR market_scope = 'US_EU'",
                        (scope,)
                    )
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Universe [{scope}] initialized in {elapsed:.1f}s")
        print(f"  Source: {results.get('source', 'parquet')}")
        print(f"  Added: {results.get('added', 0)}")
        print(f"  Errors: {results.get('errors', 0)}")
        
        return 0 if results.get('errors', 0) == 0 else 1
        
    except Exception as e:
        logger.error(f"Universe init failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1


def import_universe_from_csv(store: SQLiteStore, csv_path: str, scope: MarketScope) -> dict:
    """
    Import universe from CSV file for a specific scope.
    
    CSV format: asset_id,symbol,name,asset_type,market_code,exchange_code,currency,country,sector,industry,tier,priority_level
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    added = 0
    errors = 0
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assets = []
        
        for row in reader:
            try:
                asset = {
                    'asset_id': row.get('asset_id', f"{row['symbol']}.{row.get('exchange_code', 'US')}"),
                    'symbol': row['symbol'],
                    'name': row.get('name', row['symbol']),
                    'asset_type': row.get('asset_type', 'EQUITY'),
                    'market_code': row.get('market_code', 'US'),
                    'exchange_code': row.get('exchange_code', row.get('market_code', 'US')),
                    'currency': row.get('currency', 'USD'),
                    'country': row.get('country', 'US'),
                    'sector': row.get('sector'),
                    'industry': row.get('industry'),
                    'tier': int(row.get('tier', 2)),
                    'priority_level': int(row.get('priority_level', 2)),
                    'active': 1
                }
                assets.append(asset)
                added += 1
            except Exception as e:
                logger.error(f"Failed to parse row: {row} - {e}")
                errors += 1
        
        if assets:
            store.bulk_upsert_assets(assets, market_scope=scope)
    
    return {'source': csv_path, 'added': added, 'errors': errors}


def run_gating(args) -> int:
    """Run the gating job for a specific scope."""
    scope: MarketScope = getattr(args, 'scope', 'US_EU')
    
    print("\n" + "=" * 60)
    print(f"MarketGPS - Run Gating [{scope}]")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    try:
        store = SQLiteStore()
        parquet = ParquetStore(market_scope=scope)
        batch_size = args.batch_size if hasattr(args, 'batch_size') else 50
        
        if scope == "AFRICA":
            # Use Africa-specific gating with stricter rules
            from pipeline.africa.gating_africa import AfricaGatingJob
            job = AfricaGatingJob(store=store, parquet_store=parquet)
        else:
            # Standard US_EU gating
            job = GatingJob(store=store, parquet_store=parquet, market_scope=scope)
        
        results = job.run(batch_size=batch_size)
        
        elapsed = time.time() - start_time
        
        print(f"\n✓ Gating [{scope}] complete in {elapsed:.1f}s")
        print(f"  Processed: {results['processed']}")
        print(f"  Eligible: {results['eligible']}")
        print(f"  Ineligible: {results['ineligible']}")
        print(f"  Errors: {results['errors']}")
        
        return 0 if results['errors'] == 0 else 1
        
    except Exception as e:
        logger.error(f"Gating failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1


def run_rotation(args) -> int:
    """Run the rotation job for a specific scope."""
    scope: MarketScope = getattr(args, 'scope', 'US_EU')
    mode: JobMode = getattr(args, 'mode', 'daily_full')
    use_production = getattr(args, 'production', False)
    
    print("\n" + "=" * 60)
    print(f"MarketGPS - Run Rotation [{scope}] (mode={mode})")
    print("=" * 60 + "\n")
    
    start_time = time.time()
    
    try:
        batch_size = args.batch_size if hasattr(args, 'batch_size') else 50
        
        if use_production:
            # Use production job runner with staging → publish
            from pipeline.job_runner import ProductionJobRunner
            
            runner = ProductionJobRunner(market_scope=scope)
            result = runner.run_rotation(mode=mode, batch_size=batch_size)
            
            elapsed = time.time() - start_time
            
            print(f"\n✓ Rotation [{scope}] complete in {elapsed:.1f}s")
            print(f"  Run ID: {result.run_id[:8]}...")
            print(f"  Mode: {result.mode}")
            print(f"  Processed: {result.assets_processed}")
            print(f"  Success: {result.assets_success}")
            print(f"  Failed: {result.assets_failed}")
            
            return 0 if result.status == "success" else 1
        else:
            # Legacy mode (direct writes, no staging)
            store = SQLiteStore()
            parquet = ParquetStore(market_scope=scope)
            
            if scope == "AFRICA":
                # Use Africa-specific scoring
                results = run_africa_rotation(store, parquet, batch_size)
            else:
                # Standard US_EU rotation
                job = RotationJob(store=store, parquet_store=parquet, market_scope=scope)
                results = job.run(batch_size=batch_size)
            
            elapsed = time.time() - start_time
            
            print(f"\n✓ Rotation [{scope}] complete in {elapsed:.1f}s")
            print(f"  Processed: {results['processed']}")
            print(f"  Updated: {results['updated']}")
            print(f"  Errors: {results['errors']}")
            
            return 0 if results['errors'] == 0 else 1
        
    except Exception as e:
        logger.error(f"Rotation failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1


def run_africa_rotation(store: SQLiteStore, parquet: ParquetStore, batch_size: int = None) -> dict:
    """
    Run Africa-specific rotation with production-grade pipeline.
    
    Uses the new pipeline/africa/ module with:
    - Exchange-specific thresholds
    - FX risk calculation
    - Liquidity risk calculation
    - Staging → atomic publish
    """
    from pipeline.africa.rotation_africa import RotationAfricaJob
    
    batch_size = batch_size or 50
    
    # Use the new RotationAfricaJob
    job = RotationAfricaJob(store=store, parquet_store=parquet)
    result = job.run(mode="daily_full", batch_size=batch_size)
    
    return {
        'processed': result.assets_processed,
        'updated': result.assets_scored,
        'errors': result.assets_failed,
        'gated': result.assets_gated,
        'run_id': result.run_id,
        'status': result.status
    }


def run_full_pipeline(args) -> int:
    """Run the full pipeline for a specific scope."""
    scope: MarketScope = getattr(args, 'scope', 'US_EU')
    
    print("\n" + "=" * 60)
    print(f"MarketGPS - Full Pipeline Run [{scope}]")
    print("=" * 60 + "\n")
    
    total_start = time.time()
    
    # Universe
    print(f"Step 1/3: Initializing universe [{scope}]...")
    result = run_init_universe(args)
    if result != 0:
        return result
    
    # Gating
    print(f"\nStep 2/3: Running gating [{scope}]...")
    result = run_gating(args)
    if result != 0:
        return result
    
    # Rotation
    print(f"\nStep 3/3: Running rotation [{scope}]...")
    result = run_rotation(args)
    
    total_elapsed = time.time() - total_start
    print(f"\n{'=' * 60}")
    print(f"Full pipeline [{scope}] complete in {total_elapsed:.1f}s")
    print("=" * 60)
    
    return result


def run_worker(args) -> int:
    """
    Run the job queue worker.
    Processes PENDING jobs from jobs_queue table.
    """
    scope: MarketScope = getattr(args, 'scope', None)  # None = all scopes
    
    print("\n" + "=" * 60)
    print(f"MarketGPS - Job Queue Worker" + (f" [{scope}]" if scope else " [ALL]"))
    print("=" * 60 + "\n")
    
    store = SQLiteStore()
    
    max_iterations = args.max_jobs if hasattr(args, 'max_jobs') else 10
    processed = 0
    errors = 0
    
    print(f"Processing up to {max_iterations} jobs...\n")
    
    for _ in range(max_iterations):
        # Fetch next job atomically (optionally filtered by scope)
        job = store.fetch_next_job_atomic(market_scope=scope)
        
        if not job:
            print("No more pending jobs.")
            break
        
        job_id = job["id"]
        job_type = job["job_type"]
        job_scope = job.get("market_scope", "US_EU")
        payload = json.loads(job.get("payload_json") or "{}")
        
        print(f"Processing job #{job_id}: {job_type} [{job_scope}]")
        
        try:
            # Get scope-specific stores
            parquet = ParquetStore(market_scope=job_scope)
            
            if job_type == "SCORE_TICKERS":
                result = process_score_tickers(store, parquet, payload, job_scope)
            elif job_type == "REFRESH_UNIVERSE":
                result = process_refresh_universe(store, payload, job_scope)
            elif job_type == "FULL_GATING":
                result = process_full_gating(store, parquet, payload, job_scope)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            store.mark_job_done(job_id)
            processed += 1
            print(f"  ✓ Job #{job_id} completed: {result}")
            
        except Exception as e:
            store.mark_job_failed(job_id, str(e))
            errors += 1
            logger.error(f"Job #{job_id} failed: {e}")
            print(f"  ✗ Job #{job_id} failed: {e}")
    
    print(f"\nWorker finished: {processed} completed, {errors} failed")
    return 0 if errors == 0 else 1


def process_score_tickers(
    store: SQLiteStore, 
    parquet: ParquetStore, 
    payload: dict,
    scope: MarketScope
) -> str:
    """
    Process SCORE_TICKERS job for a specific scope.
    Sets high priority for requested tickers and runs targeted rotation.
    """
    tickers = payload.get("tickers", [])
    
    if not tickers:
        return "No tickers to process"
    
    # Set high priority for these tickers
    store.set_priority_level(tickers, priority=1, market_scope=scope)
    
    scored = 0
    
    if scope == "AFRICA":
        from pipeline.scoring_africa import run_africa_scoring_batch
        results = run_africa_scoring_batch(store, parquet, tickers)
        scored = results['success']
    else:
        # Run targeted rotation for US_EU
        rotation = RotationJob(store=store, parquet_store=parquet, market_scope=scope)
        for ticker in tickers:
            try:
                score = rotation.refresh_single(ticker)
                if score:
                    scored += 1
            except Exception as e:
                logger.warning(f"Failed to score {ticker}: {e}")
    
    return f"Scored {scored}/{len(tickers)} tickers"


def process_refresh_universe(store: SQLiteStore, payload: dict, scope: MarketScope) -> str:
    """Process REFRESH_UNIVERSE job."""
    csv_path = payload.get("csv_path")
    
    if csv_path:
        results = import_universe_from_csv(store, csv_path, scope)
    else:
        job = UniverseJob(store=store)
        results = job.run()
    
    return f"Added {results.get('added', 0)}, errors {results.get('errors', 0)}"


def process_full_gating(
    store: SQLiteStore, 
    parquet: ParquetStore, 
    payload: dict,
    scope: MarketScope
) -> str:
    """Process FULL_GATING job."""
    job = GatingJob(store=store, parquet_store=parquet, market_scope=scope)
    batch_size = payload.get("batch_size", 50)
    results = job.run(batch_size=batch_size)
    return f"Processed {results['processed']}, eligible {results['eligible']}"


def show_status(args) -> int:
    """Show current system status for all scopes."""
    print("\n" + "=" * 60)
    print("MarketGPS - System Status")
    print("=" * 60 + "\n")
    
    try:
        store = SQLiteStore()
        
        # Overall stats
        db_stats = store.get_stats()
        print("Overall Database:")
        print(f"  Universe: {db_stats['universe_total']} assets")
        print(f"  Scores: {db_stats['scores_total']} calculated")
        print(f"  Watchlist: {db_stats['watchlist_count']} items")
        print(f"  Jobs pending: {db_stats['jobs_pending']}")
        
        # By scope
        if db_stats.get("by_scope"):
            print("\nAssets by Scope:")
            for scope, count in db_stats["by_scope"].items():
                print(f"  {scope}: {count}")
        
        if db_stats.get("by_type"):
            print("\nAssets by Type:")
            for asset_type, count in db_stats["by_type"].items():
                print(f"  {asset_type}: {count}")
        
        # Per-scope storage stats
        for scope in ["US_EU", "AFRICA"]:
            parquet = ParquetStore(market_scope=scope)
            storage_stats = parquet.get_storage_stats()
            if storage_stats['files'] > 0:
                print(f"\nParquet Storage [{scope}]:")
                print(f"  Files: {storage_stats['files']}")
                print(f"  Size: {storage_stats['size_mb']:.1f} MB")
                print(f"  Total bars: {storage_stats['total_bars']:,}")
        
        # Top scores per scope
        for scope in ["US_EU", "AFRICA"]:
            top = store.list_top_n(market_scope=scope, n=5)
            if top:
                print(f"\nTop 5 Scores [{scope}]:")
                for row in top:
                    print(f"  {row['symbol']}: {row['score_total']:.0f} (conf: {row.get('confidence', 0)}%)")
        
        # Recent jobs
        jobs = store.get_recent_jobs(5)
        if jobs:
            print(f"\nRecent Jobs:")
            for job in jobs:
                scope_info = f" [{job.get('market_scope', 'US_EU')}]"
                print(f"  #{job['id']} {job['job_type']}{scope_info}: {job['status']}")
        
        # Quota
        usage = store.get_today_usage()
        print(f"\nToday's Quota:")
        print(f"  Used: {usage['calculations_count']}/{usage['calculations_limit']}")
        
        # Provider health
        try:
            from providers import get_provider
            provider = get_provider("auto")
            health = provider.healthcheck()
            print(f"\nProvider: {provider.name}")
            print(f"  Status: {health.status}")
            print(f"  Latency: {health.latency_ms}ms")
        except Exception as e:
            print(f"\nProvider: Error - {e}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MarketGPS Pipeline Jobs (Multi-Scope)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # US_EU (default scope) - Legacy mode
  python -m pipeline.jobs --init-universe
  python -m pipeline.jobs --run-gating
  python -m pipeline.jobs --run-rotation
  
  # PRODUCTION MODE (staging → atomic publish)
  python -m pipeline.jobs --run-rotation --production --mode daily_full
  python -m pipeline.jobs --run-rotation --production --mode hourly_overlay --scope US_EU
  python -m pipeline.jobs --run-rotation --production --mode daily_full --scope AFRICA
  
  # AFRICA scope
  python -m pipeline.jobs --init-universe --scope AFRICA --from-csv data/universe/universe_africa.csv
  python -m pipeline.jobs --run-gating --scope AFRICA
  python -m pipeline.jobs --run-rotation --scope AFRICA --production
  
  # Full pipeline for a scope
  python -m pipeline.jobs --full-pipeline --scope US_EU
  python -m pipeline.jobs --full-pipeline --scope AFRICA
  
  # Job queue worker
  python -m pipeline.jobs --worker
  python -m pipeline.jobs --worker --scope AFRICA --max-jobs 5
  
  # Status
  python -m pipeline.jobs --status
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--init-universe",
        action="store_true",
        help="Initialize the asset universe"
    )
    group.add_argument(
        "--run-gating",
        action="store_true",
        help="Run the gating (data quality) job"
    )
    group.add_argument(
        "--run-rotation",
        action="store_true",
        help="Run the rotation (incremental refresh) job"
    )
    group.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run full pipeline (universe + gating + rotation)"
    )
    group.add_argument(
        "--worker",
        action="store_true",
        help="Run job queue worker (process pending jobs)"
    )
    group.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    
    parser.add_argument(
        "--scope",
        type=str,
        choices=["US_EU", "AFRICA"],
        default="US_EU",
        help="Market scope to operate on (default: US_EU)"
    )
    
    parser.add_argument(
        "--from-csv",
        type=str,
        metavar="PATH",
        help="Import universe from CSV file (for --init-universe)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for processing (default: 50)"
    )
    
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=10,
        help="Max jobs to process in worker mode (default: 10)"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["daily_full", "hourly_overlay", "on_demand"],
        default="daily_full",
        help="Job mode: daily_full (all assets), hourly_overlay (tier1 only), on_demand (specific)"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use production job runner with staging → atomic publish"
    )
    
    args = parser.parse_args()
    
    print(f"\nMarketGPS Pipeline [{args.scope}] - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.init_universe:
        sys.exit(run_init_universe(args))
    elif args.run_gating:
        sys.exit(run_gating(args))
    elif args.run_rotation:
        sys.exit(run_rotation(args))
    elif args.full_pipeline:
        sys.exit(run_full_pipeline(args))
    elif args.worker:
        sys.exit(run_worker(args))
    elif args.status:
        sys.exit(show_status(args))


if __name__ == "__main__":
    main()
