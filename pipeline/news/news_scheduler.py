"""
MarketGPS News Scheduler

Runs the news pipeline every 30 minutes:
1. Ingest RSS feeds from all enabled sources
2. Rewrite/translate articles with LLM
3. Publish to news_articles table

Usage:
    python -m pipeline.news.news_scheduler

Environment variables:
    OPENAI_API_KEY - For article rewriting (recommended)
    GEMINI_API_KEY - Alternative LLM
    NEWS_INTERVAL_MINUTES - Override default 30min interval
"""

import os
import sys
import time
import signal
import json
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# Constants
DEFAULT_INTERVAL_MINUTES = 30
LOCK_FILE = Path(__file__).parent.parent.parent / "backend" / ".news_pipeline.lock"
METRICS_FILE = Path(__file__).parent.parent.parent / "data" / "news_metrics.json"


class NewsSchedulerLock:
    """File-based lock to prevent concurrent news pipeline runs."""
    
    def __init__(self, lock_path: Path = LOCK_FILE):
        self.lock_path = lock_path
        self.lock_file = None
        
    def acquire(self) -> bool:
        """Try to acquire the lock. Returns True if successful."""
        try:
            self.lock_path.parent.mkdir(parents=True, exist_ok=True)
            self.lock_file = open(self.lock_path, 'w')
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Write lock info
            lock_info = {
                "pid": os.getpid(),
                "started_at": datetime.now().isoformat(),
                "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown"
            }
            self.lock_file.write(json.dumps(lock_info))
            self.lock_file.flush()
            
            return True
        except (IOError, OSError):
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False
    
    def release(self):
        """Release the lock."""
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
            except:
                pass
            finally:
                self.lock_file = None
                
            # Remove lock file
            try:
                self.lock_path.unlink()
            except:
                pass


def update_metrics(result: dict, success: bool = True):
    """Update metrics file with last run info."""
    try:
        METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing metrics
        metrics = {}
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, 'r') as f:
                    metrics = json.load(f)
            except:
                pass
        
        # Update
        metrics["last_run"] = datetime.now().isoformat()
        metrics["last_success"] = success
        metrics["last_result"] = result
        
        # Track history (last 10 runs)
        history = metrics.get("history", [])
        history.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "articles_published": result.get("publish", {}).get("items_published", 0),
            "items_ingested": result.get("ingest", {}).get("items_new", 0)
        })
        metrics["history"] = history[:10]
        
        # Save
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    except Exception as e:
        logger.warning(f"Failed to update metrics: {e}")


def run_news_pipeline():
    """Execute the full news pipeline with lock protection."""
    logger.info("=" * 60)
    logger.info("MarketGPS News Pipeline - Scheduled Run")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    lock = NewsSchedulerLock()
    
    if not lock.acquire():
        logger.warning("Another news pipeline is already running. Skipping this run.")
        return
    
    try:
        from pipeline.news.publish import run_full_pipeline
        
        start_time = time.time()
        result = run_full_pipeline(ingest_limit=None, publish_limit=100)
        elapsed = time.time() - start_time
        
        ingest = result.get("ingest", {})
        publish = result.get("publish", {})
        
        logger.info("-" * 60)
        logger.info("Pipeline Complete:")
        logger.info(f"  Sources fetched: {ingest.get('sources_success', 0)}/{ingest.get('sources_total', 0)}")
        logger.info(f"  New items ingested: {ingest.get('items_new', 0)}")
        logger.info(f"  Articles published: {publish.get('items_published', 0)}")
        logger.info(f"  LLM provider: {publish.get('llm_provider', 'none')}")
        logger.info(f"  Total time: {elapsed:.1f}s")
        logger.info("-" * 60)
        
        update_metrics(result, success=True)
        
    except Exception as e:
        logger.error(f"News pipeline failed: {e}", exc_info=True)
        update_metrics({"error": str(e)}, success=False)
        
    finally:
        lock.release()


def run_scheduler():
    """Start the news scheduler with APScheduler."""
    if not APSCHEDULER_AVAILABLE:
        logger.error("APScheduler not installed. Install with: pip install apscheduler")
        sys.exit(1)
    
    interval_minutes = int(os.environ.get("NEWS_INTERVAL_MINUTES", DEFAULT_INTERVAL_MINUTES))
    run_on_start = os.environ.get("NEWS_RUN_ON_START", "true").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("MarketGPS News Scheduler Starting")
    logger.info(f"Interval: Every {interval_minutes} minutes")
    logger.info(f"Run on start: {run_on_start}")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler()
    
    # Add job
    scheduler.add_job(
        run_news_pipeline,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="news_pipeline",
        name="News Pipeline (ingest + publish)",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300  # 5 minutes grace for misfires
    )
    
    # Graceful shutdown
    def shutdown(signum, frame):
        logger.info("Shutting down news scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Run immediately on start if configured
    if run_on_start:
        logger.info("Running initial pipeline...")
        run_news_pipeline()
    
    logger.info(f"Scheduler started. Next run in {interval_minutes} minutes.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketGPS News Scheduler")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run pipeline once and exit (no scheduling)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override interval in minutes"
    )
    
    args = parser.parse_args()
    
    if args.interval:
        os.environ["NEWS_INTERVAL_MINUTES"] = str(args.interval)
    
    if args.once:
        run_news_pipeline()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
