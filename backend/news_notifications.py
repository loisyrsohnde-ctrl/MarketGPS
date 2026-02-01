"""
MarketGPS News Notifications Service
Handles breaking news alerts and user notifications.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core.config import get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# Try to import Resend for email notifications
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    resend = None


class NewsNotificationService:
    """Service for handling news notifications."""

    def __init__(self, store: Optional[SQLiteStore] = None):
        """Initialize the notification service."""
        self.store = store or SQLiteStore()
        self._init_resend()

    def _init_resend(self):
        """Initialize Resend email client."""
        self.email_enabled = False
        resend_key = os.environ.get("RESEND_API_KEY")

        if RESEND_AVAILABLE and resend_key:
            try:
                resend.api_key = resend_key
                self.email_enabled = True
                logger.info("Resend email notifications enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Resend: {e}")

    def get_breaking_news(self, limit: int = 5, max_age_hours: int = 6) -> List[Dict]:
        """
        Get recent breaking news articles.

        Args:
            limit: Maximum number of articles to return
            max_age_hours: Maximum age in hours for breaking news

        Returns:
            List of breaking news articles
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

        with self.store._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, slug, title, excerpt, source_name, published_at,
                       engagement_score, importance_level, category, country
                FROM news_articles
                WHERE is_breaking_news = 1
                  AND status = 'published'
                  AND published_at >= ?
                ORDER BY published_at DESC
                LIMIT ?
            """, (cutoff_str, limit)).fetchall()

            return [dict(row) for row in rows]

    def get_high_importance_news(self, limit: int = 10, max_age_hours: int = 24) -> List[Dict]:
        """
        Get high importance news articles.

        Args:
            limit: Maximum number of articles to return
            max_age_hours: Maximum age in hours

        Returns:
            List of high importance articles
        """
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

        with self.store._get_connection() as conn:
            rows = conn.execute("""
                SELECT id, slug, title, excerpt, source_name, published_at,
                       engagement_score, importance_level, category, country
                FROM news_articles
                WHERE (importance_level = 'high' OR importance_level = 'breaking')
                  AND status = 'published'
                  AND published_at >= ?
                ORDER BY engagement_score DESC, published_at DESC
                LIMIT ?
            """, (cutoff_str, limit)).fetchall()

            return [dict(row) for row in rows]

    def create_alert(
        self,
        article_id: int,
        alert_type: str,
        title: str,
        message: Optional[str] = None,
        importance_score: float = 0.0
    ) -> Optional[int]:
        """
        Create a news alert.

        Args:
            article_id: ID of the article
            alert_type: Type of alert (breaking, high_importance, trending)
            title: Alert title
            message: Optional message/excerpt
            importance_score: Score that triggered the alert

        Returns:
            Alert ID if created, None otherwise
        """
        try:
            with self.store._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO news_alerts (article_id, alert_type, title, message, importance_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, alert_type, title, message, importance_score))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    def get_user_alert_preferences(self, user_id: str) -> Dict:
        """Get user's notification preferences."""
        with self.store._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM user_news_alert_prefs WHERE user_id = ?
            """, (user_id,)).fetchone()

            if row:
                return dict(row)

            # Return defaults
            return {
                "user_id": user_id,
                "receive_breaking_news": True,
                "receive_high_importance": True,
                "receive_trending": False,
                "email_enabled": True,
                "min_importance_score": 0.7
            }

    def update_user_alert_preferences(self, user_id: str, prefs: Dict) -> bool:
        """Update user's notification preferences."""
        try:
            with self.store._get_connection() as conn:
                conn.execute("""
                    INSERT INTO user_news_alert_prefs (
                        user_id, receive_breaking_news, receive_high_importance,
                        receive_trending, email_enabled, min_importance_score,
                        preferred_regions, preferred_countries, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    ON CONFLICT(user_id) DO UPDATE SET
                        receive_breaking_news = excluded.receive_breaking_news,
                        receive_high_importance = excluded.receive_high_importance,
                        receive_trending = excluded.receive_trending,
                        email_enabled = excluded.email_enabled,
                        min_importance_score = excluded.min_importance_score,
                        preferred_regions = excluded.preferred_regions,
                        preferred_countries = excluded.preferred_countries,
                        updated_at = datetime('now')
                """, (
                    user_id,
                    prefs.get("receive_breaking_news", True),
                    prefs.get("receive_high_importance", True),
                    prefs.get("receive_trending", False),
                    prefs.get("email_enabled", True),
                    prefs.get("min_importance_score", 0.7),
                    json.dumps(prefs.get("preferred_regions")) if prefs.get("preferred_regions") else None,
                    json.dumps(prefs.get("preferred_countries")) if prefs.get("preferred_countries") else None
                ))
                return True
        except Exception as e:
            logger.error(f"Failed to update alert preferences: {e}")
            return False

    def send_breaking_news_notification(
        self,
        user_email: str,
        article: Dict,
        user_prefs: Optional[Dict] = None
    ) -> bool:
        """
        Send a breaking news email notification.

        Args:
            user_email: User's email address
            article: Article data
            user_prefs: User preferences (optional)

        Returns:
            True if sent successfully
        """
        if not self.email_enabled:
            logger.warning("Email notifications not enabled")
            return False

        if user_prefs and not user_prefs.get("email_enabled", True):
            logger.info(f"Email disabled for user")
            return False

        try:
            from_email = os.environ.get("RESEND_FROM_EMAIL", "alerts@marketgps.africa")

            # Build email content
            subject = f"🔴 ALERTE INFO: {article['title'][:60]}..."

            html_content = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #dc2626; color: white; padding: 12px 20px; border-radius: 4px 4px 0 0;">
                    <span style="font-weight: bold; font-size: 14px;">🔴 ALERTE INFO</span>
                </div>

                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-top: none; padding: 24px; border-radius: 0 0 4px 4px;">
                    <h1 style="font-size: 24px; color: #0f172a; margin: 0 0 16px 0; line-height: 1.3;">
                        {article['title']}
                    </h1>

                    {f'<p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">{article.get("excerpt", "")}</p>' if article.get("excerpt") else ''}

                    <div style="font-size: 13px; color: #64748b; margin-bottom: 20px;">
                        <span>{article.get('source_name', 'MarketGPS')}</span>
                        {f" • {article.get('country', '')}" if article.get('country') else ''}
                    </div>

                    <a href="https://marketgps.africa/news/{article['slug']}"
                       style="display: inline-block; background: #0f172a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: 600;">
                        Lire l'article →
                    </a>
                </div>

                <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 12px;">
                    <p>MarketGPS • Plateforme d'analyse quantitative Afrique</p>
                    <p><a href="https://marketgps.africa/settings/notifications" style="color: #3b82f6;">Gérer mes notifications</a></p>
                </div>
            </div>
            """

            resend.Emails.send({
                "from": from_email,
                "to": [user_email],
                "subject": subject,
                "html": html_content
            })

            logger.info(f"Breaking news email sent to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send breaking news email: {e}")
            return False

    def process_new_breaking_news(self, article: Dict) -> Dict:
        """
        Process a new breaking news article and create notifications.

        Args:
            article: Article data with is_breaking_news=True

        Returns:
            Summary of notifications created/sent
        """
        result = {
            "alert_created": False,
            "emails_sent": 0,
            "in_app_notifications": 0
        }

        if not article.get("is_breaking_news"):
            return result

        # Create alert record
        alert_id = self.create_alert(
            article_id=article["id"],
            alert_type="breaking",
            title=article["title"],
            message=article.get("excerpt"),
            importance_score=article.get("engagement_score", 0.8)
        )

        if alert_id:
            result["alert_created"] = True
            logger.info(f"Created breaking news alert {alert_id} for article {article['id']}")

        # Note: Email sending to subscribed users would happen here
        # For now, this is handled on-demand or via a separate job

        return result


# Create singleton instance
notification_service = NewsNotificationService()


def get_notification_service() -> NewsNotificationService:
    """Get the notification service singleton."""
    return notification_service
