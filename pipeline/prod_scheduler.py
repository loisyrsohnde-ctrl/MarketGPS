#!/usr/bin/env python3
"""
MarketGPS Production Scheduler
==============================
Runs the pipeline at US market open (09:35 ET) and close (16:10 ET).

Features:
- Timezone-aware scheduling (America/New_York, DST-safe)
- Market calendar integration (skips weekends/holidays)
- Lock protection against double execution
- Dry-run mode for testing
- Graceful shutdown handling

Usage:
    python -m pipeline.prod_scheduler [--dry-run]
    
Environment Variables:
    SCHEDULER_MODE: "prod" or "test" (default: prod)
    MARKET_SCOPE: "US_EU" or "AFRICA" (default: US_EU)
    RUN_ON_START: "true" to run immediately on startup (default: false)
"""

import os
import sys
import signal
import time
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Timezone handling
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

# Market calendar
try:
    import exchange_calendars as xcals
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/logs/prod_scheduler.log', mode='a') if os.path.exists('/app/logs') 
            else logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

TZ_US = ZoneInfo("America/New_York")

# Run windows (hour, minute) in ET
SCHEDULE = {
    "open": (9, 35),    # 09:35 ET - after market open
    "close": (16, 10),  # 16:10 ET - after market close
}

# Lock file for preventing double execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = PROJECT_ROOT / "backend" / ".pipeline_us_eu.lock"

# Shutdown flag
_shutdown_requested = False


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_now_et() -> datetime:
    """Get current time in America/New_York."""
    return datetime.now(TZ_US)


def is_trading_day(dt: datetime) -> bool:
    """Check if given date is a NYSE trading day."""
    date = dt.date()
    
    # Weekend check
    if date.weekday() >= 5:
        return False
    
    # Calendar check
    if HAS_CALENDAR:
        try:
            nyse = xcals.get_calendar("XNYS")
            return nyse.is_session(date)
        except Exception as e:
            logger.warning(f"Calendar check failed: {e}, assuming weekday is trading day")
            return True
    
    return True


def get_next_run_time() -> tuple[datetime, str]:
    """
    Calculate the next scheduled run time.
    
    Returns:
        Tuple of (next_run_datetime, mode)
    """
    now = get_now_et()
    today = now.date()
    
    # Get today's run times
    open_time = now.replace(hour=SCHEDULE["open"][0], minute=SCHEDULE["open"][1], second=0, microsecond=0)
    close_time = now.replace(hour=SCHEDULE["close"][0], minute=SCHEDULE["close"][1], second=0, microsecond=0)
    
    # Determine next run
    if now < open_time and is_trading_day(now):
        return open_time, "open"
    elif now < close_time and is_trading_day(now):
        return close_time, "close"
    else:
        # Find next trading day
        next_day = now + timedelta(days=1)
        while not is_trading_day(next_day):
            next_day += timedelta(days=1)
            if next_day > now + timedelta(days=7):
                # Safety: don't look more than a week ahead
                break
        
        next_open = next_day.replace(
            hour=SCHEDULE["open"][0], 
            minute=SCHEDULE["open"][1], 
            second=0, 
            microsecond=0
        )
        return next_open, "open"


def check_lock() -> bool:
    """Check if lock file exists and is active."""
    if not LOCK_FILE.exists():
        return False
    
    try:
        import json
        with open(LOCK_FILE, 'r') as f:
            lock_info = json.load(f)
        
        pid = lock_info.get("pid")
        if pid:
            try:
                os.kill(pid, 0)
                return True  # Process is running
            except OSError:
                # Stale lock
                LOCK_FILE.unlink()
                return False
        return True
    except Exception:
        return False


def acquire_lock(mode: str) -> bool:
    """Acquire execution lock."""
    import json
    
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        lock_data = {
            "pid": os.getpid(),
            "mode": mode,
            "started_at": get_now_et().isoformat(),
        }
        
        with open(LOCK_FILE, 'w') as f:
            json.dump(lock_data, f)
        
        return True
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        return False


def release_lock():
    """Release execution lock."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as e:
        logger.warning(f"Failed to release lock: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(mode: str, market_scope: str = "US_EU", dry_run: bool = False) -> bool:
    """
    Execute the pipeline for a given mode.
    
    Args:
        mode: 'open' or 'close'
        market_scope: 'US_EU' or 'AFRICA'
        dry_run: If True, log but don't execute
    
    Returns:
        True if successful, False otherwise
    """
    now = get_now_et()
    
    logger.info("=" * 60)
    logger.info(f"PIPELINE RUN: {mode.upper()} - {market_scope}")
    logger.info(f"Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("[DRY RUN] Would execute pipeline, skipping...")
        return True
    
    # Check lock
    if check_lock():
        logger.warning("Lock active, pipeline already running - skipping")
        return False
    
    # Acquire lock
    if not acquire_lock(mode):
        logger.error("Failed to acquire lock")
        return False
    
    try:
        # Build command
        cmd = [
            sys.executable, "-m", "pipeline.jobs",
            "--full-pipeline",
            "--scope", market_scope,
            "--production"
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        # Run pipeline
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logger.info("Pipeline completed successfully")
            logger.info(f"STDOUT:\n{result.stdout[-2000:]}")  # Last 2000 chars
            return True
        else:
            logger.error(f"Pipeline failed with code {result.returncode}")
            logger.error(f"STDERR:\n{result.stderr[-2000:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Pipeline timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        return False
    finally:
        release_lock()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SCHEDULER LOOP
# ═══════════════════════════════════════════════════════════════════════════

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global _shutdown_requested
    logger.info(f"Received signal {signum}, initiating shutdown...")
    _shutdown_requested = True


def main():
    """Main scheduler entry point."""
    global _shutdown_requested
    
    import argparse
    
    parser = argparse.ArgumentParser(description="MarketGPS Production Scheduler")
    parser.add_argument("--dry-run", action="store_true", help="Log but don't execute")
    parser.add_argument("--run-once", type=str, choices=["open", "close"], help="Run once and exit")
    args = parser.parse_args()
    
    # Environment config
    market_scope = os.environ.get("MARKET_SCOPE", "US_EU")
    run_on_start = os.environ.get("RUN_ON_START", "false").lower() == "true"
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("MARKETGPS PRODUCTION SCHEDULER STARTING")
    logger.info("=" * 60)
    logger.info(f"Market Scope: {market_scope}")
    logger.info(f"Timezone: America/New_York")
    logger.info(f"Open run: {SCHEDULE['open'][0]:02d}:{SCHEDULE['open'][1]:02d} ET")
    logger.info(f"Close run: {SCHEDULE['close'][0]:02d}:{SCHEDULE['close'][1]:02d} ET")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Calendar available: {HAS_CALENDAR}")
    logger.info("=" * 60)
    
    # Single run mode
    if args.run_once:
        success = run_pipeline(args.run_once, market_scope, args.dry_run)
        sys.exit(0 if success else 1)
    
    # Run on start if configured
    if run_on_start:
        logger.info("RUN_ON_START enabled, executing initial run...")
        run_pipeline("startup", market_scope, args.dry_run)
    
    # Main loop
    last_run_date = {}  # Track runs per mode per day
    
    while not _shutdown_requested:
        now = get_now_et()
        today = now.date().isoformat()
        
        # Check if we should run
        if is_trading_day(now):
            for mode, (hour, minute) in SCHEDULE.items():
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Check if within 2-minute window and not already run today
                if abs((now - target).total_seconds()) < 120:
                    run_key = f"{today}_{mode}"
                    if run_key not in last_run_date:
                        logger.info(f"Triggering {mode} run...")
                        success = run_pipeline(mode, market_scope, args.dry_run)
                        last_run_date[run_key] = success
        
        # Calculate and log next run
        next_run, next_mode = get_next_run_time()
        sleep_seconds = (next_run - now).total_seconds()
        
        if sleep_seconds > 300:  # More than 5 minutes away
            # Log every hour
            logger.info(f"Next run: {next_mode} at {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')} "
                       f"({sleep_seconds/3600:.1f}h)")
        
        # Sleep for 60 seconds between checks
        for _ in range(60):
            if _shutdown_requested:
                break
            time.sleep(1)
    
    logger.info("Scheduler shutdown complete")


if __name__ == "__main__":
    main()
