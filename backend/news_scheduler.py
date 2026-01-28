"""
MarketGPS - News Scraping Scheduler

Runs the African news scraper on a schedule:
- Active hours: 6h to 21h (local time)
- Frequency: Every hour during active hours
- Minimum interactions: 50 (configurable)

Usage:
    # Run once (for cron)
    python news_scheduler.py --once

    # Run continuously (for Docker/process)
    python news_scheduler.py --daemon

    # Cron example (every hour from 6h to 21h):
    0 6-21 * * * cd /path/to/backend && python news_scheduler.py --once
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from storage.sqlite_store import SQLiteStore
from news_scraper import AfricanNewsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

START_HOUR = int(os.environ.get("NEWS_START_HOUR", 6))   # 6h
END_HOUR = int(os.environ.get("NEWS_END_HOUR", 21))      # 21h
MIN_INTERACTIONS = int(os.environ.get("NEWS_MIN_INTERACTIONS", 50))
SCRAPE_INTERVAL_MINUTES = int(os.environ.get("NEWS_INTERVAL_MINUTES", 60))

# Results storage
RESULTS_FILE = Path(__file__).parent / "data" / "news_scraping_history.json"


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def is_active_hours() -> bool:
    """Check if current time is within active scraping hours."""
    current_hour = datetime.now().hour
    return START_HOUR <= current_hour < END_HOUR


def save_results(results: dict):
    """Save scraping results to history file."""
    try:
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Load existing history
        history = []
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE, 'r') as f:
                    history = json.load(f)
            except:
                history = []

        # Add new result
        results['timestamp'] = datetime.now().isoformat()
        history.insert(0, results)

        # Keep only last 100 results
        history = history[:100]

        # Save
        with open(RESULTS_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        logger.info(f"Results saved to {RESULTS_FILE}")

    except Exception as e:
        logger.error(f"Error saving results: {e}")


async def run_scraping():
    """Run a single scraping session."""
    logger.info("=" * 60)
    logger.info(f"Starting news scraping at {datetime.now().isoformat()}")
    logger.info(f"Active hours: {START_HOUR}h - {END_HOUR}h")
    logger.info(f"Minimum interactions: {MIN_INTERACTIONS}")
    logger.info("=" * 60)

    if not is_active_hours():
        logger.info(f"Outside active hours ({START_HOUR}h-{END_HOUR}h). Skipping.")
        return None

    try:
        db = SQLiteStore()
        scraper = AfricanNewsScraper(db)

        results = await scraper.run_scraping(min_interactions=MIN_INTERACTIONS)

        logger.info("=" * 60)
        logger.info("Scraping completed!")
        logger.info(f"  Sources scraped: {results.get('sources_scraped', 0)}")
        logger.info(f"  Articles found: {results.get('articles_found', 0)}")
        logger.info(f"  Articles saved: {results.get('articles_saved', 0)}")
        logger.info(f"  Trending articles: {results.get('trending_articles', 0)}")
        logger.info("=" * 60)

        # Save results
        save_results(results)

        return results

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        save_results({
            "error": str(e),
            "sources_scraped": 0,
            "articles_found": 0,
            "articles_saved": 0,
        })
        return None


async def run_daemon():
    """Run continuously, scraping every hour during active hours."""
    logger.info("Starting news scraper daemon...")
    logger.info(f"Will run every {SCRAPE_INTERVAL_MINUTES} minutes during {START_HOUR}h-{END_HOUR}h")

    while True:
        if is_active_hours():
            await run_scraping()
        else:
            logger.info(f"Outside active hours. Current hour: {datetime.now().hour}. Waiting...")

        # Wait for next interval
        logger.info(f"Sleeping for {SCRAPE_INTERVAL_MINUTES} minutes...")
        await asyncio.sleep(SCRAPE_INTERVAL_MINUTES * 60)


def get_scraping_history(limit: int = 10) -> list:
    """Get recent scraping history."""
    try:
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE, 'r') as f:
                history = json.load(f)
                return history[:limit]
    except:
        pass
    return []


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='MarketGPS News Scraper Scheduler')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run continuously')
    parser.add_argument('--history', action='store_true', help='Show scraping history')
    parser.add_argument('--force', action='store_true', help='Ignore active hours check')

    args = parser.parse_args()

    if args.history:
        history = get_scraping_history(20)
        print(json.dumps(history, indent=2))
        return

    if args.force:
        global START_HOUR, END_HOUR
        START_HOUR = 0
        END_HOUR = 24
        logger.info("Force mode: ignoring active hours")

    if args.daemon:
        asyncio.run(run_daemon())
    else:
        # Default: run once
        asyncio.run(run_scraping())


if __name__ == "__main__":
    main()
