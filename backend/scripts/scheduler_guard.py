#!/usr/bin/env python3
"""
MarketGPS - Pipeline Scheduler Guard
=====================================
Source de vérité pour:
- Heure actuelle en America/New_York (DST automatique)
- Calendrier boursier NYSE (jours fériés)
- Fenêtre d'exécution (open/close)
- Lock de protection contre double exécution

Exit codes:
  0  = OK, pipeline peut s'exécuter
  10 = SKIP, marché fermé (week-end ou jour férié)
  11 = SKIP, hors fenêtre d'exécution
  20 = SKIP, lock actif (pipeline déjà en cours)
  1  = ERROR, erreur inattendue
  
Usage:
  python scheduler_guard.py --mode open|close [--dry-run] [--force-date YYYY-MM-DD]
"""

import argparse
import os
import sys
import json
import fcntl
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Tuple, Optional

# Timezone handling
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # Python < 3.9

# Market calendar
try:
    import exchange_calendars as xcals
    HAS_CALENDAR = True
except ImportError:
    try:
        import pandas_market_calendars as mcal
        HAS_CALENDAR = "pandas"
    except ImportError:
        HAS_CALENDAR = False


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Timezone US
TZ_US = ZoneInfo("America/New_York")

# Heures d'exécution (America/New_York)
OPEN_RUN_TIME = time(9, 35)   # 09:35 ET
CLOSE_RUN_TIME = time(16, 10) # 16:10 ET

# Tolérance en minutes autour de l'heure cible
TOLERANCE_MINUTES = 15

# Lock file path (relatif au projet)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOCK_FILE = PROJECT_ROOT / "backend" / ".pipeline_us_eu.lock"

# Log directory
LOG_DIR = PROJECT_ROOT / "backend" / "logs"


# ═══════════════════════════════════════════════════════════════════════════
# TIME UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def get_now_et(force_date: Optional[str] = None) -> datetime:
    """
    Get current time in America/New_York timezone.
    
    Args:
        force_date: Optional date override for testing (YYYY-MM-DD)
    
    Returns:
        datetime in America/New_York timezone
    """
    now = datetime.now(TZ_US)
    
    if force_date:
        # Parse forced date and use current time
        forced = datetime.strptime(force_date, "%Y-%m-%d")
        now = now.replace(year=forced.year, month=forced.month, day=forced.day)
    
    return now


def is_in_window(now: datetime, target: time, tolerance_minutes: int = TOLERANCE_MINUTES) -> bool:
    """
    Check if current time is within tolerance window of target time.
    
    Args:
        now: Current datetime
        target: Target time (hour, minute)
        tolerance_minutes: Allowed deviation in minutes
    
    Returns:
        True if within window
    """
    # Build target datetime for today
    target_dt = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    
    # Calculate window
    window_start = target_dt - timedelta(minutes=tolerance_minutes)
    window_end = target_dt + timedelta(minutes=tolerance_minutes)
    
    return window_start <= now <= window_end


def get_run_mode(now: datetime) -> Optional[str]:
    """
    Determine which run mode we're in based on current time.
    
    Returns:
        'open', 'close', or None if not in any window
    """
    if is_in_window(now, OPEN_RUN_TIME):
        return "open"
    elif is_in_window(now, CLOSE_RUN_TIME):
        return "close"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# MARKET CALENDAR
# ═══════════════════════════════════════════════════════════════════════════

def is_trading_day(dt: datetime) -> Tuple[bool, str]:
    """
    Check if the given date is a NYSE trading day.
    
    Args:
        dt: datetime to check
    
    Returns:
        Tuple of (is_trading_day, reason)
    """
    date = dt.date()
    
    # Check weekend first (no calendar needed)
    if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False, f"weekend ({date.strftime('%A')})"
    
    # Try exchange_calendars first
    if HAS_CALENDAR is True:
        try:
            nyse = xcals.get_calendar("XNYS")
            if not nyse.is_session(date):
                # Get holiday name if possible
                return False, "NYSE holiday"
            return True, "trading day"
        except Exception as e:
            # Fallback: assume trading day on weekdays
            return True, f"calendar check failed ({e}), assuming open"
    
    # Try pandas_market_calendars
    elif HAS_CALENDAR == "pandas":
        try:
            nyse = mcal.get_calendar("NYSE")
            schedule = nyse.schedule(start_date=date, end_date=date)
            if schedule.empty:
                return False, "NYSE holiday"
            return True, "trading day"
        except Exception as e:
            return True, f"calendar check failed ({e}), assuming open"
    
    # No calendar library - assume weekdays are trading days
    else:
        return True, "no calendar lib - assuming weekday is trading day"


# ═══════════════════════════════════════════════════════════════════════════
# LOCK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def check_lock() -> Tuple[bool, Optional[dict]]:
    """
    Check if lock file exists and is active.
    
    Returns:
        Tuple of (is_locked, lock_info)
    """
    if not LOCK_FILE.exists():
        return False, None
    
    try:
        with open(LOCK_FILE, 'r') as f:
            lock_info = json.load(f)
        
        # Check if PID is still running
        pid = lock_info.get("pid")
        if pid:
            try:
                os.kill(pid, 0)  # Check if process exists
                return True, lock_info
            except OSError:
                # Process not running, stale lock
                return False, {"stale": True, **lock_info}
        
        return True, lock_info
        
    except (json.JSONDecodeError, IOError):
        # Corrupted lock file, treat as stale
        return False, {"stale": True, "error": "corrupted"}


def acquire_lock(mode: str) -> bool:
    """
    Try to acquire the lock file.
    
    Args:
        mode: 'open' or 'close'
    
    Returns:
        True if lock acquired, False otherwise
    """
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        lock_data = {
            "pid": os.getpid(),
            "mode": mode,
            "started_at": datetime.now(TZ_US).isoformat(),
            "host": os.uname().nodename
        }
        
        with open(LOCK_FILE, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to acquire lock: {e}", file=sys.stderr)
        return False


def release_lock():
    """Remove the lock file."""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception as e:
        print(f"WARNING: Failed to release lock: {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════

def log_message(mode: str, level: str, message: str):
    """
    Log a message to the appropriate log file.
    
    Args:
        mode: 'open' or 'close'
        level: 'INFO', 'WARN', 'ERROR', etc.
        message: Log message
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = LOG_DIR / f"pipeline_us_eu_{mode}.log"
    timestamp = datetime.now(TZ_US).strftime("%Y-%m-%d %H:%M:%S %Z")
    
    log_line = f"[{timestamp}] [{level}] {message}\n"
    
    # Also print to stdout
    print(log_line.strip())
    
    try:
        with open(log_file, 'a') as f:
            f.write(log_line)
    except Exception as e:
        print(f"WARNING: Could not write to log: {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN GUARD LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def run_guard(
    mode: str,
    dry_run: bool = False,
    force_date: Optional[str] = None,
    skip_time_check: bool = False,
    skip_calendar_check: bool = False
) -> int:
    """
    Main guard function - determines if pipeline should run.
    
    Args:
        mode: 'open' or 'close'
        dry_run: If True, don't acquire lock, just check
        force_date: Override date for testing
        skip_time_check: Skip time window verification
        skip_calendar_check: Skip market calendar check
    
    Returns:
        Exit code (0=run, 10=market closed, 11=wrong time, 20=locked)
    """
    now = get_now_et(force_date)
    
    log_message(mode, "INFO", f"=== GUARD CHECK START ===")
    log_message(mode, "INFO", f"Mode: {mode}")
    log_message(mode, "INFO", f"Current time (ET): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    log_message(mode, "INFO", f"Dry run: {dry_run}")
    
    if force_date:
        log_message(mode, "WARN", f"Forced date: {force_date}")
    
    # 1. Check market calendar
    if not skip_calendar_check:
        is_open, reason = is_trading_day(now)
        log_message(mode, "INFO", f"Market status: {'OPEN' if is_open else 'CLOSED'} ({reason})")
        
        if not is_open:
            log_message(mode, "INFO", f"SKIP market closed: {reason}")
            return 10
    else:
        log_message(mode, "WARN", "Calendar check SKIPPED")
    
    # 2. Check time window
    if not skip_time_check:
        target_time = OPEN_RUN_TIME if mode == "open" else CLOSE_RUN_TIME
        in_window = is_in_window(now, target_time)
        
        log_message(mode, "INFO", 
            f"Time window: target={target_time}, tolerance=±{TOLERANCE_MINUTES}min, in_window={in_window}")
        
        if not in_window:
            log_message(mode, "INFO", f"SKIP not in run window for mode '{mode}'")
            return 11
    else:
        log_message(mode, "WARN", "Time check SKIPPED")
    
    # 3. Check lock
    is_locked, lock_info = check_lock()
    
    if is_locked:
        log_message(mode, "WARN", f"Lock active: {json.dumps(lock_info)}")
        log_message(mode, "INFO", "SKIP pipeline already running")
        return 20
    elif lock_info and lock_info.get("stale"):
        log_message(mode, "INFO", f"Cleaning stale lock: {json.dumps(lock_info)}")
        release_lock()
    
    # 4. Acquire lock (unless dry run)
    if not dry_run:
        if not acquire_lock(mode):
            log_message(mode, "ERROR", "Failed to acquire lock")
            return 1
        log_message(mode, "INFO", f"Lock acquired: {LOCK_FILE}")
    else:
        log_message(mode, "INFO", "DRY RUN - lock not acquired")
    
    log_message(mode, "INFO", "=== GUARD CHECK PASSED - OK TO RUN ===")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="MarketGPS Pipeline Scheduler Guard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0  = OK, pipeline can run
  10 = SKIP, market closed
  11 = SKIP, not in run window
  20 = SKIP, lock active
  1  = ERROR

Examples:
  # Normal check for open run
  python scheduler_guard.py --mode open
  
  # Dry run (no lock)
  python scheduler_guard.py --mode close --dry-run
  
  # Test with forced date (holiday)
  python scheduler_guard.py --mode open --force-date 2025-12-25 --dry-run
  
  # Force run (skip all checks)
  python scheduler_guard.py --mode open --skip-all-checks
"""
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["open", "close"],
        default=None,
        help="Run mode: open (09:35 ET) or close (16:10 ET)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check only, don't acquire lock"
    )
    
    parser.add_argument(
        "--force-date",
        type=str,
        metavar="YYYY-MM-DD",
        help="Override date for testing (keeps current time)"
    )
    
    parser.add_argument(
        "--skip-time-check",
        action="store_true",
        help="Skip time window verification"
    )
    
    parser.add_argument(
        "--skip-calendar-check",
        action="store_true",
        help="Skip market calendar check"
    )
    
    parser.add_argument(
        "--skip-all-checks",
        action="store_true",
        help="Skip all checks (force run)"
    )
    
    parser.add_argument(
        "--release-lock",
        action="store_true",
        help="Just release the lock and exit"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current status and exit"
    )
    
    args = parser.parse_args()
    
    # Status check
    if args.status:
        now = get_now_et()
        is_open, reason = is_trading_day(now)
        is_locked, lock_info = check_lock()
        
        print(f"\n=== MarketGPS Scheduler Status ===")
        print(f"Time (ET): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Day of week: {now.strftime('%A')}")
        print(f"Market: {'OPEN' if is_open else 'CLOSED'} ({reason})")
        print(f"Lock: {'ACTIVE' if is_locked else 'FREE'}")
        if lock_info:
            print(f"Lock info: {json.dumps(lock_info, indent=2)}")
        print(f"OPEN window: {OPEN_RUN_TIME} ±{TOLERANCE_MINUTES}min")
        print(f"CLOSE window: {CLOSE_RUN_TIME} ±{TOLERANCE_MINUTES}min")
        
        current_mode = get_run_mode(now)
        if current_mode:
            print(f"Current window: {current_mode.upper()}")
        else:
            print(f"Current window: NONE (outside run windows)")
        
        return 0
    
    # Release lock only
    if args.release_lock:
        release_lock()
        print(f"Lock released: {LOCK_FILE}")
        return 0
    
    # Skip all checks
    if args.skip_all_checks:
        args.skip_time_check = True
        args.skip_calendar_check = True
    
    # Mode required for guard check
    if not args.mode:
        parser.error("--mode is required (use --status or --release-lock for other operations)")
    
    try:
        exit_code = run_guard(
            mode=args.mode,
            dry_run=args.dry_run,
            force_date=args.force_date,
            skip_time_check=args.skip_time_check,
            skip_calendar_check=args.skip_calendar_check
        )
        return exit_code
        
    except Exception as e:
        log_message(args.mode, "ERROR", f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
