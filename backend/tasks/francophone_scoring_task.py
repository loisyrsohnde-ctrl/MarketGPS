"""
Scheduled Task: Daily Francophone Article Scoring

This task should be executed once daily to:
1. Recalculate francophone relevance scores for all articles
2. Generate the daily TOP 20 selection
3. Store historical data in francophone_daily_top20 table
4. Log filtering statistics

Integration:
- APScheduler: Use with @scheduled_job decorator
- Celery: Use with @periodic_task decorator
- Airflow: Create as a DAG task
- Cron: Execute via command line at midnight

Example cron job:
    0 0 * * * cd /path/to/MarketGPS && python -m backend.tasks.francophone_scoring_task
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from storage.sqlite_store import SQLiteStore
from services.francophone_filter_service import FrancophonicFilterService

logger = logging.getLogger(__name__)


class FrancophonicScoringTask:
    """Executes daily francophone article scoring and TOP 20 selection."""

    def __init__(self, db_conn=None):
        """
        Initialize the task.

        Args:
            db_conn: Function to get SQLite connection (optional)
        """
        if db_conn is None:
            db = SQLiteStore()
            db_conn = db._get_conn

        self.get_conn = db_conn
        self.filter_svc = FrancophonicFilterService(db_conn=db_conn)

    def run(self, date: Optional[str] = None) -> bool:
        """
        Execute the daily francophone scoring task.

        Args:
            date: Date to process (YYYY-MM-DD format, default: today)

        Returns:
            True if successful
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        logger.info(f"Starting francophone scoring task for {date}")

        try:
            # Step 1: Recalculate all scores
            logger.info("Step 1: Recalculating francophone relevance scores...")
            if not self._recalculate_scores():
                logger.error("Failed to recalculate scores")
                return False

            # Step 2: Generate daily TOP 20
            logger.info("Step 2: Generating daily TOP 20...")
            articles, stats = self._generate_daily_top20(date)
            if articles is None:
                logger.error("Failed to generate TOP 20")
                return False

            # Step 3: Log statistics
            logger.info("Step 3: Logging statistics...")
            if not self._log_statistics(date, stats):
                logger.error("Failed to log statistics")
                return False

            logger.info(
                f"Francophone scoring task completed successfully. "
                f"TOP 20 generated: {len(articles)} articles, "
                f"Avg score: {stats['avg_relevance_score']:.1f}"
            )

            return True

        except Exception as e:
            logger.error(f"Error in francophone scoring task: {e}", exc_info=True)
            return False

    def _recalculate_scores(self) -> bool:
        """
        Step 1: Recalculate francophone relevance scores.

        Returns:
            True if successful
        """
        try:
            success = self.filter_svc.calculate_and_store_scores()
            if success:
                logger.info("Scores recalculated successfully")
            else:
                logger.error("Score calculation failed")
            return success

        except Exception as e:
            logger.error(f"Error recalculating scores: {e}")
            return False

    def _generate_daily_top20(self, date: str) -> tuple:
        """
        Step 2: Generate and store daily TOP 20.

        Args:
            date: Date in YYYY-MM-DD format

        Returns:
            Tuple of (articles, stats_dict) or (None, {}) on error
        """
        try:
            # Get TOP 20
            articles = self.filter_svc.get_daily_top_20(days=1, include_featured=True)

            if not articles:
                logger.warning("No articles qualified for TOP 20 today")
                return articles, {"articles_top20": 0, "avg_relevance_score": 0.0}

            # Store in history table
            conn = self.get_conn()
            cursor = conn.cursor()

            for article in articles:
                try:
                    cursor.execute("""
                        INSERT INTO francophone_daily_top20
                        (date, article_id, rank, francophone_relevance_score,
                         interaction_score, language_score, region_score,
                         recency_score, topic_score, is_featured)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date,
                        article.article_id,
                        article.rank,
                        article.francophone_relevance_score,
                        article.interaction_score,
                        article.language_score,
                        article.region_score,
                        article.recency_score,
                        article.topic_score,
                        int(article.is_featured)
                    ))

                except sqlite3.IntegrityError:
                    # Article already in history for this date
                    logger.debug(f"Article {article.article_id} already in history for {date}")
                    pass

            conn.commit()
            conn.close()

            # Calculate statistics
            avg_score = sum(a.francophone_relevance_score for a in articles) / len(articles)
            featured_count = sum(1 for a in articles if a.is_featured)

            stats = {
                "articles_top20": len(articles),
                "featured_count": featured_count,
                "avg_relevance_score": avg_score,
                "min_relevance_score": min(a.francophone_relevance_score for a in articles),
                "max_relevance_score": max(a.francophone_relevance_score for a in articles),
            }

            logger.info(
                f"TOP 20 generated: {len(articles)} articles, "
                f"Featured: {featured_count}, "
                f"Avg score: {avg_score:.1f}"
            )

            return articles, stats

        except Exception as e:
            logger.error(f"Error generating TOP 20: {e}")
            return None, {}

    def _log_statistics(self, date: str, stats: dict) -> bool:
        """
        Step 3: Log filtering statistics.

        Args:
            date: Date in YYYY-MM-DD format
            stats: Statistics dictionary

        Returns:
            True if successful
        """
        try:
            conn = self.get_conn()
            cursor = conn.cursor()

            # Get additional stats from database
            cursor.execute("""
                SELECT COUNT(*) as analyzed
                FROM news_articles
                WHERE status = 'published' AND language = 'fr'
            """)

            analyzed = cursor.fetchone()[0]

            # Insert log entry
            cursor.execute("""
                INSERT INTO francophone_filter_log
                (date, articles_analyzed, articles_qualified, articles_top20,
                 featured_count, avg_relevance_score, status, ended_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                analyzed,
                0,  # Will be calculated from actual filtering
                stats.get("articles_top20", 0),
                stats.get("featured_count", 0),
                stats.get("avg_relevance_score", 0.0),
                "success",
                datetime.utcnow().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.info(f"Statistics logged for {date}")
            return True

        except Exception as e:
            logger.error(f"Error logging statistics: {e}")
            return False

    def cleanup_old_records(self, days_to_keep: int = 90) -> bool:
        """
        Clean up old records from daily TOP 20 and logs (optional).

        Args:
            days_to_keep: Keep records from last N days (default: 90)

        Returns:
            True if successful
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

            conn = self.get_conn()
            cursor = conn.cursor()

            # Delete old daily top 20 records
            cursor.execute("""
                DELETE FROM francophone_daily_top20
                WHERE date < ?
            """, (cutoff_date,))

            deleted_top20 = cursor.rowcount

            # Delete old log records
            cursor.execute("""
                DELETE FROM francophone_filter_log
                WHERE date < ?
            """, (cutoff_date,))

            deleted_logs = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(
                f"Cleanup completed: Deleted {deleted_top20} TOP 20 records, "
                f"{deleted_logs} log records older than {cutoff_date}"
            )

            return True

        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduler Integration Examples
# ═══════════════════════════════════════════════════════════════════════════════

def run_apscheduler():
    """APScheduler integration example."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()

        def task():
            task = FrancophonicScoringTask()
            task.run()
            task.cleanup_old_records(days_to_keep=90)

        # Run daily at 00:00 UTC
        scheduler.add_job(task, 'cron', hour=0, minute=0)
        scheduler.start()

        logger.info("APScheduler: Francophone scoring task scheduled for 00:00 UTC daily")

    except ImportError:
        logger.error("APScheduler not installed. Install with: pip install apscheduler")


def run_celery():
    """Celery integration example."""
    try:
        from celery import Celery

        app = Celery('tasks')

        @app.task
        def francophone_scoring_task():
            task = FrancophonicScoringTask()
            success = task.run()
            task.cleanup_old_records(days_to_keep=90)
            return {"status": "success" if success else "failed"}

        # Configure periodic task in celerybeat
        logger.info(
            "Celery task 'francophone_scoring_task' registered. "
            "Configure in celerybeat schedule."
        )

        return francophone_scoring_task

    except ImportError:
        logger.error("Celery not installed. Install with: pip install celery")


def run_standalone():
    """Standalone CLI execution."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Francophone Article Scoring Task")
    parser.add_argument(
        "--date",
        default=None,
        help="Date to process (YYYY-MM-DD format, default: today)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Also cleanup old records"
    )
    parser.add_argument(
        "--cleanup-days",
        type=int,
        default=90,
        help="Keep records from last N days (default: 90)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run task
    task = FrancophonicScoringTask()
    success = task.run(date=args.date)

    if not success:
        sys.exit(1)

    # Optional cleanup
    if args.cleanup:
        task.cleanup_old_records(days_to_keep=args.cleanup_days)


if __name__ == "__main__":
    run_standalone()
