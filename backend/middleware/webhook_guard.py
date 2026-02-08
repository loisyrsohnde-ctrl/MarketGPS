"""
Webhook Guard Module - Stripe Event Replay Attack Prevention

This module provides protection against webhook replay attacks by tracking
processed event IDs in SQLite and preventing duplicate event processing.
"""

import os
import sqlite3
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from fastapi import HTTPException, Header

logger = logging.getLogger(__name__)


class WebhookGuard:
    """
    Thread-safe Stripe webhook event tracker to prevent replay attacks.

    Stores processed event IDs in SQLite table `stripe_events_processed`.
    Automatically cleans up events older than 72 hours.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the WebhookGuard with database path.

        Args:
            db_path: Path to SQLite database. If None, uses SQLITE_DB_PATH
                    environment variable or defaults to "data/marketgps.db"
        """
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH", "data/marketgps.db")

        self.db_path = db_path
        self._lock = threading.RLock()
        self._initialized = False

        # Ensure database file exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_db()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for thread-safe database connections.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_db(self) -> None:
        """
        Create the stripe_events_processed table if it doesn't exist.

        Table schema:
        - event_id (TEXT PRIMARY KEY): Stripe event ID
        - processed_at (TIMESTAMP): When the event was processed
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stripe_events_processed (
                        event_id TEXT PRIMARY KEY,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Create index for faster timestamp-based queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_processed_at
                    ON stripe_events_processed(processed_at)
                """)
                conn.commit()
                self._initialized = True
                logger.info(f"WebhookGuard database initialized at {self.db_path}")

    def is_event_processed(self, event_id: str) -> bool:
        """
        Check if a webhook event has already been processed.

        Args:
            event_id: Stripe event ID to check

        Returns:
            bool: True if event has been processed, False otherwise
        """
        if not event_id:
            logger.warning("Empty event_id provided to is_event_processed")
            return False

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM stripe_events_processed WHERE event_id = ?",
                    (event_id,)
                )
                result = cursor.fetchone() is not None
                if result:
                    logger.info(f"Detected replay attack: event_id={event_id}")
                return result

    def mark_event_processed(self, event_id: str) -> bool:
        """
        Mark a webhook event as processed.

        Args:
            event_id: Stripe event ID to mark as processed

        Returns:
            bool: True if successfully marked, False if event was already processed

        Raises:
            sqlite3.Error: If database operation fails
        """
        if not event_id:
            logger.warning("Empty event_id provided to mark_event_processed")
            return False

        with self._lock:
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO stripe_events_processed (event_id) VALUES (?)",
                        (event_id,)
                    )
                    conn.commit()
                    logger.debug(f"Marked event as processed: event_id={event_id}")
                    return True
            except sqlite3.IntegrityError:
                logger.info(f"Event already marked as processed: event_id={event_id}")
                return False

    def cleanup_old_events(self, hours: int = 72) -> int:
        """
        Remove processed events older than specified hours.

        Args:
            hours: Number of hours to keep events (default: 72)

        Returns:
            int: Number of rows deleted
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM stripe_events_processed WHERE processed_at < ?",
                    (cutoff_time,)
                )
                conn.commit()
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"Cleanup: Deleted {deleted} events older than {hours} hours")
                return deleted

    def get_event_count(self) -> int:
        """
        Get total count of processed events in database.

        Returns:
            int: Number of processed events
        """
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM stripe_events_processed")
                result = cursor.fetchone()
                return result[0] if result else 0


# Global instance
_webhook_guard: Optional[WebhookGuard] = None


def get_webhook_guard() -> WebhookGuard:
    """
    Get or create the global WebhookGuard instance.

    Returns:
        WebhookGuard: Global webhook guard instance
    """
    global _webhook_guard
    if _webhook_guard is None:
        _webhook_guard = WebhookGuard()
    return _webhook_guard


async def verify_webhook_not_replayed(
    stripe_signature: str = Header(None),
    event_id: Optional[str] = None,
) -> str:
    """
    FastAPI dependency to verify webhook hasn't been replayed.

    This dependency should be used to check incoming webhook requests
    and prevent duplicate processing of the same event.

    Args:
        stripe_signature: Stripe signature header (for validation)
        event_id: Event ID to check (should be extracted from request body)

    Returns:
        str: The event_id if validation passes

    Raises:
        HTTPException: 409 Conflict if event has already been processed
    """
    if not event_id:
        logger.warning("verify_webhook_not_replayed called without event_id")
        raise HTTPException(
            status_code=400,
            detail="Missing event_id in request body"
        )

    guard = get_webhook_guard()

    if guard.is_event_processed(event_id):
        logger.warning(f"Replay attack detected: event_id={event_id}")
        raise HTTPException(
            status_code=409,
            detail="This webhook event has already been processed"
        )

    return event_id


def is_event_processed(event_id: str) -> bool:
    """
    Standalone function to check if event has been processed.

    Args:
        event_id: Stripe event ID to check

    Returns:
        bool: True if event has been processed, False otherwise
    """
    guard = get_webhook_guard()
    return guard.is_event_processed(event_id)


def mark_event_processed(event_id: str) -> bool:
    """
    Standalone function to mark an event as processed.

    Args:
        event_id: Stripe event ID to mark

    Returns:
        bool: True if successfully marked, False if already processed
    """
    guard = get_webhook_guard()
    return guard.mark_event_processed(event_id)


def cleanup_old_events(hours: int = 72) -> int:
    """
    Standalone function to cleanup old events.

    Args:
        hours: Number of hours to keep events

    Returns:
        int: Number of rows deleted
    """
    guard = get_webhook_guard()
    return guard.cleanup_old_events(hours)
