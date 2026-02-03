"""
Subscription Repository - Manages user subscriptions and quotas.
"""
from typing import Dict

from storage.base_repository import BaseRepository
from core.config import get_logger

logger = get_logger(__name__)


class SubscriptionRepository(BaseRepository):
    """Repository for subscription and quota operations."""

    def get_subscription(self, user_id: str) -> Dict:
        """Get user subscription info."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM subscriptions_state WHERE user_id = ?",
                (user_id,)
            ).fetchone()

            if row:
                return dict(row)

            # Return default free plan
            return {
                "user_id": user_id,
                "plan": "free",
                "status": "active",
                "daily_quota_used": 0,
                "daily_quota_limit": 3
            }

    def set_subscription(self, user_id: str, plan: str, status: str = "active", renews_at: str = None) -> bool:
        """Set or update subscription."""
        try:
            quota_limits = {
                "free": 3,
                "monthly_9_99": 200,
                "yearly_50": 200
            }
            quota = quota_limits.get(plan, 3)
            scopes = "US_EU,AFRICA" if plan != "free" else "US_EU"

            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO subscriptions_state (user_id, plan, status, daily_quota_limit,
                                                    scopes_access, started_at, renews_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'))
                    ON CONFLICT(user_id) DO UPDATE SET
                        plan = excluded.plan,
                        status = excluded.status,
                        daily_quota_limit = excluded.daily_quota_limit,
                        scopes_access = excluded.scopes_access,
                        started_at = COALESCE(subscriptions_state.started_at, datetime('now')),
                        renews_at = excluded.renews_at,
                        updated_at = datetime('now')
                """, (user_id, plan, status, quota, scopes, renews_at))

            logger.info(f"Set subscription for {user_id}: {plan} ({status})")
            return True
        except Exception as e:
            logger.error(f"Failed to set subscription: {e}")
            return False

    def is_pro_user(self, user_id: str) -> bool:
        """Check if user has an active pro subscription."""
        sub = self.get_subscription(user_id)
        return sub.get("status") == "active" and sub.get("plan") in ("monthly_9_99", "yearly_50")

    def can_calculate_score(self, user_id: str) -> bool:
        """Check if user can calculate a score (quota check)."""
        sub = self.get_subscription(user_id)
        return sub.get("daily_quota_used", 0) < sub.get("daily_quota_limit", 3)

    def consume_calculation_quota(self, user_id: str, count: int = 1) -> bool:
        """Consume calculation quota."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE subscriptions_state
                    SET daily_quota_used = daily_quota_used + ?
                    WHERE user_id = ?
                """, (count, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to consume quota: {e}")
            return False

    def reset_daily_quotas(self):
        """Reset all daily quotas (call this daily via scheduler)."""
        with self._get_connection() as conn:
            conn.execute("UPDATE subscriptions_state SET daily_quota_used = 0")
        logger.info("Reset all daily quotas")
