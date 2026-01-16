"""
MarketGPS Job Scheduler.
Background job orchestration with APScheduler.
"""
import signal
import sys
from datetime import datetime

from core.utils import get_logger
from core.config import get_config
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from .universe import UniverseJob
from .gating import GatingJob
from .pool import PoolJob
from .rotation import RotationJob

logger = get_logger(__name__)


class Scheduler:
    """
    Job scheduler for MarketGPS pipeline.
    
    Schedules:
    - Rotation: Every 15 minutes
    - Gating + Pool: Every 6 hours
    - Universe: Weekly
    """
    
    def __init__(self, provider_name: str = "yfinance"):
        """Initialize scheduler."""
        self.provider_name = provider_name
        self.config = get_config()
        self.store = SQLiteStore()
        self.parquet_store = ParquetStore()
        self._scheduler = None
        self._running = False
    
    def _create_scheduler(self):
        """Create APScheduler instance."""
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            from apscheduler.triggers.cron import CronTrigger
            
            self._scheduler = BlockingScheduler()
            
            # Rotation job: every 15 minutes
            self._scheduler.add_job(
                self._run_rotation,
                IntervalTrigger(minutes=self.config.schedule_rotation_minutes),
                id="rotation",
                name="Rotation Job",
                max_instances=1,
                coalesce=True,
            )
            
            # Gating job: every 6 hours
            self._scheduler.add_job(
                self._run_gating,
                IntervalTrigger(hours=self.config.schedule_gating_hours),
                id="gating",
                name="Gating Job",
                max_instances=1,
                coalesce=True,
            )
            
            # Pool job: every 6 hours (after gating)
            self._scheduler.add_job(
                self._run_pool,
                IntervalTrigger(hours=self.config.schedule_pool_hours),
                id="pool",
                name="Pool Job",
                max_instances=1,
                coalesce=True,
            )
            
            # Universe job: weekly (Sunday at 2 AM)
            self._scheduler.add_job(
                self._run_universe,
                CronTrigger(day_of_week="sun", hour=2),
                id="universe",
                name="Universe Job",
                max_instances=1,
                coalesce=True,
            )
            
            return True
            
        except ImportError:
            logger.error(
                "APScheduler not installed. "
                "Run: pip install apscheduler"
            )
            return False
    
    def _run_rotation(self):
        """Execute rotation job."""
        logger.info("[Scheduler] Running Rotation job")
        try:
            job = RotationJob(
                store=self.store,
                parquet_store=self.parquet_store,
                provider_name=self.provider_name
            )
            stats = job.run()
            logger.info(f"[Scheduler] Rotation completed: {stats.get('scored', 0)} scored")
        except Exception as e:
            logger.error(f"[Scheduler] Rotation failed: {e}")
    
    def _run_gating(self):
        """Execute gating job."""
        logger.info("[Scheduler] Running Gating job")
        try:
            job = GatingJob(
                store=self.store,
                parquet_store=self.parquet_store,
                provider_name=self.provider_name
            )
            stats = job.run()
            logger.info(f"[Scheduler] Gating completed: {stats.get('eligible', 0)} eligible")
        except Exception as e:
            logger.error(f"[Scheduler] Gating failed: {e}")
    
    def _run_pool(self):
        """Execute pool job."""
        logger.info("[Scheduler] Running Pool job")
        try:
            job = PoolJob(store=self.store)
            stats = job.run()
            logger.info(f"[Scheduler] Pool completed: {stats.get('pool_size', 0)} in pool")
        except Exception as e:
            logger.error(f"[Scheduler] Pool failed: {e}")
    
    def _run_universe(self):
        """Execute universe job."""
        logger.info("[Scheduler] Running Universe job")
        try:
            job = UniverseJob(store=self.store, provider_name=self.provider_name)
            stats = job.run()
            logger.info(f"[Scheduler] Universe completed: {stats.get('total', 0)} assets")
        except Exception as e:
            logger.error(f"[Scheduler] Universe failed: {e}")
    
    def start(self, run_initial: bool = True):
        """
        Start the scheduler.
        
        Args:
            run_initial: Run initial jobs before starting scheduler
        """
        if not self._create_scheduler():
            return False
        
        # Handle signals for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("=" * 60)
        logger.info("MARKETGPS SCHEDULER STARTING")
        logger.info("=" * 60)
        logger.info(f"Rotation interval: {self.config.schedule_rotation_minutes} minutes")
        logger.info(f"Gating interval: {self.config.schedule_gating_hours} hours")
        logger.info(f"Pool interval: {self.config.schedule_pool_hours} hours")
        logger.info(f"Universe interval: {self.config.schedule_universe_days} days")
        logger.info("=" * 60)
        
        # Run initial jobs if requested
        if run_initial:
            logger.info("Running initial rotation...")
            self._run_rotation()
        
        self._running = True
        
        try:
            self._scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
        
        return True
    
    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Scheduler stopped")
    
    def run_once(self, job_name: str) -> dict:
        """
        Run a specific job once.
        
        Args:
            job_name: Job name (rotation, gating, pool, universe)
            
        Returns:
            Job statistics
        """
        jobs_map = {
            "rotation": self._run_rotation,
            "gating": self._run_gating,
            "pool": self._run_pool,
            "universe": self._run_universe,
        }
        
        job_func = jobs_map.get(job_name.lower())
        if job_func:
            job_func()
            return {"status": "completed", "job": job_name}
        
        return {"status": "error", "message": f"Unknown job: {job_name}"}


def main():
    """Main entry point for scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketGPS Job Scheduler")
    parser.add_argument("--provider", default="yfinance", help="Data provider")
    parser.add_argument("--no-initial", action="store_true", help="Skip initial job run")
    
    args = parser.parse_args()
    
    scheduler = Scheduler(provider_name=args.provider)
    scheduler.start(run_initial=not args.no_initial)


if __name__ == "__main__":
    main()
