"""
General Repository - Manages jobs, quotas, settings, and statistics.
"""
import json
from datetime import date
from typing import Optional, List, Dict, Any

from storage.base_repository import BaseRepository, MarketScope, VALID_SCOPES
from core.config import get_logger

logger = get_logger(__name__)


class GeneralRepository(BaseRepository):
    """Repository for general database operations (jobs, quotas, stats, settings)."""

    # ═══════════════════════════════════════════════════════════════════════════
    # JOBS QUEUE (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def enqueue_job(
        self,
        job_type: str,
        payload: Dict,
        market_scope: MarketScope = "US_EU",
        priority: int = 2,
        user_id: str = "default"
    ) -> int:
        """Add a job to the queue with scope."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO jobs_queue (job_type, market_scope, payload_json, priority, status, user_id, created_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?, datetime('now'))
            """, (job_type, market_scope, json.dumps(payload), priority, user_id))
            return cursor.lastrowid

    def fetch_next_job_atomic(self, market_scope: Optional[MarketScope] = None) -> Optional[Dict]:
        """Atomically fetch and lock the next pending job."""
        with self._get_connection() as conn:
            conditions = ["status = 'PENDING'"]
            params = []

            if market_scope and market_scope in VALID_SCOPES:
                conditions.append("market_scope = ?")
                params.append(market_scope)

            row = conn.execute(f"""
                SELECT * FROM jobs_queue
                WHERE {' AND '.join(conditions)}
                ORDER BY priority ASC, created_at ASC
                LIMIT 1
            """, params).fetchone()

            if not row:
                return None

            job_id = row["id"]

            conn.execute("""
                UPDATE jobs_queue
                SET status = 'RUNNING', started_at = datetime('now')
                WHERE id = ? AND status = 'PENDING'
            """, (job_id,))

            return dict(row)

    def mark_job_done(self, job_id: int):
        """Mark a job as completed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs_queue
                SET status = 'DONE', completed_at = datetime('now')
                WHERE id = ?
            """, (job_id,))

    def mark_job_failed(self, job_id: int, error: str):
        """Mark a job as failed."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE jobs_queue
                SET status = 'FAILED', completed_at = datetime('now'), error_message = ?
                WHERE id = ?
            """, (error, job_id))

    def get_pending_jobs_count(self, market_scope: Optional[MarketScope] = None) -> int:
        """Count pending jobs."""
        with self._get_connection() as conn:
            if market_scope and market_scope in VALID_SCOPES:
                result = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING' AND market_scope = ?",
                    (market_scope,)
                ).fetchone()
            else:
                result = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING'"
                ).fetchone()
            return result[0] if result else 0

    def get_recent_jobs(self, limit: int = 10, market_scope: Optional[MarketScope] = None) -> List[Dict]:
        """Get recent jobs for status display."""
        conditions = []
        params = []

        if market_scope and market_scope in VALID_SCOPES:
            conditions.append("market_scope = ?")
            params.append(market_scope)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._get_connection() as conn:
            rows = conn.execute(f"""
                SELECT * FROM jobs_queue
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """, params + [limit]).fetchall()
            return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════════════════
    # QUOTA
    # ═══════════════════════════════════════════════════════════════════════════

    def get_today_usage(self, user_id: str = "default") -> Dict:
        """Get today's usage and limits."""
        today = date.today().isoformat()

        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM usage_daily
                WHERE user_id = ? AND date = ?
            """, (user_id, today)).fetchone()

            if row:
                return dict(row)

            limit_row = conn.execute(
                "SELECT value FROM app_settings WHERE key = 'daily_quota_free'"
            ).fetchone()
            default_limit = int(limit_row["value"]) if limit_row else 200

            conn.execute("""
                INSERT INTO usage_daily (user_id, date, calculations_count, calculations_limit)
                VALUES (?, ?, 0, ?)
            """, (user_id, today, default_limit))

            return {
                "user_id": user_id,
                "date": today,
                "calculations_count": 0,
                "calculations_limit": default_limit,
                "tier": "free"
            }

    def can_consume_quota(self, count: int, user_id: str = "default") -> bool:
        """Check if user can consume quota for N calculations."""
        usage = self.get_today_usage(user_id)
        return (usage["calculations_count"] + count) <= usage["calculations_limit"]

    def consume_quota(self, count: int, user_id: str = "default") -> bool:
        """Consume quota for N calculations."""
        if not self.can_consume_quota(count, user_id):
            return False

        today = date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE usage_daily
                SET calculations_count = calculations_count + ?
                WHERE user_id = ? AND date = ?
            """, (count, user_id, today))

        return True

    def set_user_tier(self, user_id: str, tier: str, limit: int):
        """Set user tier and daily limit."""
        today = date.today().isoformat()

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE usage_daily
                SET tier = ?, calculations_limit = ?
                WHERE user_id = ? AND date = ?
            """, (tier, limit, user_id, today))

    # ═══════════════════════════════════════════════════════════════════════════
    # SETTINGS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get app setting."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """Set app setting."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value, updated_at = datetime('now')
            """, (key, value))

    def is_pro_mode_enabled(self) -> bool:
        """Check if pro mode is enabled."""
        return self.get_setting("pro_mode_enabled", "false") == "true"

    def set_pro_mode(self, enabled: bool):
        """Enable or disable pro mode."""
        self.set_setting("pro_mode_enabled", "true" if enabled else "false")

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS (SCOPE-AWARE)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self, market_scope: Optional[MarketScope] = None) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        with self._get_connection() as conn:
            stats = {}

            scope_filter = ""
            params = []
            if market_scope and market_scope in VALID_SCOPES:
                scope_filter = " AND market_scope = ?"
                params = [market_scope]
                stats["scope"] = market_scope

            # Universe counts
            stats["universe_total"] = conn.execute(
                f"SELECT COUNT(*) FROM universe WHERE active = 1{scope_filter}", params
            ).fetchone()[0]

            # Scores counts
            if market_scope:
                stats["scores_total"] = conn.execute(
                    "SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL AND market_scope = ?",
                    (market_scope,)
                ).fetchone()[0]
            else:
                stats["scores_total"] = conn.execute(
                    "SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL"
                ).fetchone()[0]

            # Watchlist count
            stats["watchlist_count"] = conn.execute(
                "SELECT COUNT(*) FROM watchlist"
            ).fetchone()[0]

            # Pending jobs
            if market_scope:
                stats["jobs_pending"] = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING' AND market_scope = ?",
                    (market_scope,)
                ).fetchone()[0]
            else:
                stats["jobs_pending"] = conn.execute(
                    "SELECT COUNT(*) FROM jobs_queue WHERE status = 'PENDING'"
                ).fetchone()[0]

            # Types breakdown
            types = conn.execute(f"""
                SELECT asset_type, COUNT(*) as count
                FROM universe WHERE active = 1{scope_filter}
                GROUP BY asset_type
            """, params).fetchall()
            stats["by_type"] = {row["asset_type"]: row["count"]
                                for row in types}

            # Scope breakdown
            scopes = conn.execute("""
                SELECT market_scope, COUNT(*) as count
                FROM universe WHERE active = 1
                GROUP BY market_scope
            """).fetchall()
            stats["by_scope"] = {row["market_scope"]: row["count"] for row in scopes}

            return stats
