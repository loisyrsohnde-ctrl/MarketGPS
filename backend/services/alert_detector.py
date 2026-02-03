"""
MarketGPS - Alert Detector
Detects conditions that trigger alerts based on market data and user rules
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from storage.parquet_store import ParquetStore
from services.alert_service import AlertService
from models.alerts import (
    Alert,
    AlertType,
    AlertPriority,
    AlertConfig,
)

logger = get_logger(__name__)


class AlertDetector:
    """Detects alert conditions and generates alerts"""

    def __init__(self, db: Optional[SQLiteStore] = None):
        """Initialize alert detector"""
        self.db = db or SQLiteStore()
        self.alert_service = AlertService(self.db)
        self.parquet_us_eu = ParquetStore(market_scope="US_EU")
        self.parquet_africa = ParquetStore(market_scope="AFRICA")

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORE CHANGE DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_score_changes(
        self, threshold_percent: float = AlertConfig.SCORE_CHANGE_THRESHOLD_PERCENT
    ) -> List[Alert]:
        """
        Detect significant score changes since previous day

        Args:
            threshold_percent: Minimum percentage change to trigger alert (default 10%)

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get all assets with current scores
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT asset_id, score, created_at FROM scores_latest
                    ORDER BY asset_id
                    """
                )
                current_scores = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

            # Get yesterday's scores
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()
            yesterday_start = f"{yesterday} 00:00:00"
            yesterday_end = f"{yesterday} 23:59:59"

            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT asset_id, score FROM scores_history
                    WHERE DATE(created_at) = DATE(?)
                    ORDER BY asset_id, created_at DESC
                    """,
                    (yesterday_start,),
                )
                yesterday_scores = {}
                for row in cursor.fetchall():
                    if row[0] not in yesterday_scores:
                        yesterday_scores[row[0]] = row[1]

            # Detect changes
            for asset_id, (current_score, updated_at) in current_scores.items():
                if asset_id not in yesterday_scores:
                    continue

                prev_score = yesterday_scores[asset_id]
                if prev_score == 0:
                    continue

                # Calculate percentage change
                change_pct = ((current_score - prev_score) / prev_score) * 100

                if abs(change_pct) >= threshold_percent:
                    # Get asset info
                    with self.db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT symbol, name FROM universe WHERE asset_id = ?",
                            (asset_id,),
                        )
                        asset_row = cursor.fetchone()

                    if not asset_row:
                        continue

                    symbol, name = asset_row
                    direction = "increased" if change_pct > 0 else "decreased"

                    # Find all users with score_change rules for this asset
                    users_with_rules = self._get_users_for_asset_alerts(
                        asset_id, AlertType.SCORE_CHANGE.value
                    )

                    for user_id in users_with_rules:
                        alert = self.alert_service.create_alert(
                            user_id=user_id,
                            alert_type=AlertType.SCORE_CHANGE.value,
                            priority=AlertPriority.HIGH.value if abs(change_pct) > 20 else AlertPriority.MEDIUM.value,
                            title=f"Score Change: {symbol}",
                            message=f"{name} ({symbol}) score has {direction} by {abs(change_pct):.1f}% (from {prev_score:.1f} to {current_score:.1f})",
                            data={
                                "asset_id": asset_id,
                                "symbol": symbol,
                                "name": name,
                                "previous_score": prev_score,
                                "current_score": current_score,
                                "change_percent": change_pct,
                                "direction": direction,
                            },
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error detecting score changes: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORE THRESHOLD DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_score_thresholds(self) -> List[Alert]:
        """
        Detect when scores cross user-defined thresholds

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get all score threshold rules
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT id, user_id, asset_id, condition_json, channels_json
                    FROM alert_rules
                    WHERE alert_type = ? AND is_active = 1
                    """,
                    (AlertType.SCORE_THRESHOLD.value,),
                )
                rules = cursor.fetchall()

            for rule in rules:
                rule_id, user_id, asset_id, condition_json, channels_json = rule
                condition = json.loads(condition_json) if condition_json else {}

                if not asset_id:
                    continue

                # Get current score
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT score FROM scores_latest WHERE asset_id = ?",
                        (asset_id,),
                    )
                    score_row = cursor.fetchone()

                if not score_row:
                    continue

                current_score = score_row[0]
                threshold = condition.get("value", 50)
                operator = condition.get("operator", ">=")

                # Check if threshold is crossed
                if self._check_condition(current_score, operator, threshold):
                    # Get asset info
                    with self.db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT symbol, name FROM universe WHERE asset_id = ?",
                            (asset_id,),
                        )
                        asset_row = cursor.fetchone()

                    if asset_row:
                        symbol, name = asset_row
                        alert = self.alert_service.create_alert(
                            user_id=user_id,
                            alert_type=AlertType.SCORE_THRESHOLD.value,
                            priority=AlertPriority.MEDIUM.value,
                            title=f"Score Threshold: {symbol}",
                            message=f"{name} ({symbol}) score of {current_score:.1f} has crossed {operator} {threshold}",
                            data={
                                "asset_id": asset_id,
                                "symbol": symbol,
                                "name": name,
                                "score": current_score,
                                "threshold": threshold,
                            },
                            rule_id=rule_id,
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error detecting score thresholds: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # OPPORTUNITY DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_opportunities(self, min_score: float = AlertConfig.OPPORTUNITY_MIN_SCORE) -> List[Alert]:
        """
        Detect high-scoring assets as opportunities

        Args:
            min_score: Minimum score to consider as opportunity (default 80)

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get high-scoring assets from last 24 hours
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT DISTINCT asset_id, score, created_at
                    FROM scores_latest
                    WHERE score >= ? AND created_at >= ?
                    ORDER BY score DESC
                    """,
                    (min_score, yesterday),
                )
                opportunities = cursor.fetchall()

            # Check if already alerted recently
            recent_alerts_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

            for asset_id, score, created_at in opportunities:
                # Get asset info
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT symbol, name, market_scope FROM universe WHERE asset_id = ?",
                        (asset_id,),
                    )
                    asset_row = cursor.fetchone()

                if not asset_row:
                    continue

                symbol, name, market_scope = asset_row

                # Find users watching this market
                users_to_alert = self._get_users_for_asset_alerts(
                    asset_id, AlertType.OPPORTUNITY.value
                )

                for user_id in users_to_alert:
                    # Check if we already alerted this user recently
                    with self.db._get_connection() as conn:
                        cursor = conn.execute(
                            """
                            SELECT COUNT(*) FROM alerts
                            WHERE user_id = ? AND asset_id = ? AND alert_type = ? AND created_at >= ?
                            """,
                            (user_id, asset_id, AlertType.OPPORTUNITY.value, recent_alerts_cutoff),
                        )
                        if cursor.fetchone()[0] > 0:
                            continue

                    alert = self.alert_service.create_alert(
                        user_id=user_id,
                        alert_type=AlertType.OPPORTUNITY.value,
                        priority=AlertPriority.HIGH.value,
                        title=f"Opportunity: {symbol}",
                        message=f"{name} ({symbol}) scores {score:.1f} - high opportunity detected!",
                        data={
                            "asset_id": asset_id,
                            "symbol": symbol,
                            "name": name,
                            "score": score,
                            "market_scope": market_scope,
                        },
                    )
                    alerts.append(alert)

        except Exception as e:
            logger.error(f"Error detecting opportunities: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHLIST CHANGES DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_watchlist_changes(self, user_id: str) -> List[Alert]:
        """
        Detect changes in watchlist assets

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get user's watchlist
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT asset_id FROM watchlist WHERE user_id = ?",
                    (user_id,),
                )
                watchlist_assets = [row[0] for row in cursor.fetchall()]

            if not watchlist_assets:
                return alerts

            # Check for score changes in watchlist
            yesterday = (datetime.utcnow() - timedelta(days=1)).date()

            for asset_id in watchlist_assets:
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        SELECT score FROM scores_latest
                        WHERE asset_id = ?
                        """,
                        (asset_id,),
                    )
                    current_row = cursor.fetchone()

                if not current_row:
                    continue

                current_score = current_row[0]

                # Get yesterday's score
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        SELECT score FROM scores_history
                        WHERE asset_id = ? AND DATE(created_at) = ?
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (asset_id, yesterday),
                    )
                    yesterday_row = cursor.fetchone()

                if not yesterday_row:
                    continue

                prev_score = yesterday_row[0]
                change_pct = ((current_score - prev_score) / prev_score * 100) if prev_score else 0

                if abs(change_pct) >= 5:  # At least 5% change for watchlist items
                    with self.db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT symbol, name FROM universe WHERE asset_id = ?",
                            (asset_id,),
                        )
                        asset_row = cursor.fetchone()

                    if asset_row:
                        symbol, name = asset_row
                        direction = "📈" if change_pct > 0 else "📉"
                        alert = self.alert_service.create_alert(
                            user_id=user_id,
                            alert_type=AlertType.WATCHLIST_ALERT.value,
                            priority=AlertPriority.MEDIUM.value,
                            title=f"Watchlist Update: {symbol} {direction}",
                            message=f"{name} ({symbol}) changed by {change_pct:.1f}% (score: {current_score:.1f})",
                            data={
                                "asset_id": asset_id,
                                "symbol": symbol,
                                "name": name,
                                "previous_score": prev_score,
                                "current_score": current_score,
                                "change_percent": change_pct,
                            },
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error detecting watchlist changes for user {user_id}: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # BREAKING NEWS DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def detect_breaking_news(self, min_score: float = AlertConfig.BREAKING_NEWS_MIN_SCORE) -> List[Alert]:
        """
        Detect breaking news items

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get recent high-scoring news
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT DISTINCT asset_id, news_title, news_score, news_date
                    FROM scores_latest
                    WHERE news_score >= ? AND news_date >= ?
                    ORDER BY news_score DESC
                    LIMIT 10
                    """,
                    (min_score, one_hour_ago),
                )
                news_items = cursor.fetchall()

            for asset_id, title, score, date in news_items:
                # Get asset info
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT symbol, name FROM universe WHERE asset_id = ?",
                        (asset_id,),
                    )
                    asset_row = cursor.fetchone()

                if not asset_row:
                    continue

                symbol, name = asset_row

                # Find users watching this asset for news
                users_to_alert = self._get_users_for_asset_alerts(
                    asset_id, AlertType.BREAKING_NEWS.value
                )

                for user_id in users_to_alert:
                    alert = self.alert_service.create_alert(
                        user_id=user_id,
                        alert_type=AlertType.BREAKING_NEWS.value,
                        priority=AlertPriority.HIGH.value,
                        title=f"Breaking News: {symbol}",
                        message=f"{title}",
                        data={
                            "asset_id": asset_id,
                            "symbol": symbol,
                            "name": name,
                            "news_score": score,
                            "news_date": date,
                        },
                    )
                    alerts.append(alert)

        except Exception as e:
            logger.error(f"Error detecting breaking news: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # RULE-BASED DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def check_user_rules(self, user_id: str) -> List[Alert]:
        """
        Check all active rules for a user and generate alerts

        Returns:
            List of generated alerts
        """
        alerts = []

        try:
            # Get all active rules for user
            user_rules = self.alert_service.get_user_rules(user_id, active_only=True)

            for rule in user_rules:
                # Skip if no asset_id and rule type requires one
                if rule.alert_type == AlertType.SCORE_THRESHOLD.value and not rule.asset_id:
                    continue

                if rule.asset_id:
                    # Single asset rule
                    alert = self._check_single_asset_rule(rule)
                    if alert:
                        alerts.append(alert)
                else:
                    # Global rule - check all assets
                    alerts.extend(self._check_global_rule(rule))

        except Exception as e:
            logger.error(f"Error checking rules for user {user_id}: {e}")

        return alerts

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _check_condition(self, value: float, operator: str, threshold: float) -> bool:
        """Check if a condition is met"""
        if operator == ">":
            return value > threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<":
            return value < threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        elif operator == "between":
            # For between, threshold is min and condition['value_high'] is max
            return value >= threshold  # Simplified - needs value_high
        return False

    def _get_users_for_asset_alerts(self, asset_id: str, alert_type: str) -> List[str]:
        """Get all users who should receive alerts for an asset"""
        users = []

        try:
            # Get users with rules for this asset
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT DISTINCT user_id FROM alert_rules
                    WHERE asset_id = ? AND alert_type = ? AND is_active = 1
                    """,
                    (asset_id, alert_type),
                )
                users.extend([row[0] for row in cursor.fetchall()])

            # For some alerts, also include users watching this asset in general
            if alert_type in [
                AlertType.OPPORTUNITY.value,
                AlertType.BREAKING_NEWS.value,
            ]:
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        """
                        SELECT DISTINCT user_id FROM watchlist
                        WHERE asset_id = ?
                        """,
                        (asset_id,),
                    )
                    users.extend([row[0] for row in cursor.fetchall()])

        except Exception as e:
            logger.error(f"Error getting users for asset {asset_id}: {e}")

        return list(set(users))  # Remove duplicates

    def _check_single_asset_rule(self, rule) -> Optional[Alert]:
        """Check a single asset alert rule"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT score FROM scores_latest WHERE asset_id = ?",
                    (rule.asset_id,),
                )
                score_row = cursor.fetchone()

            if not score_row:
                return None

            current_score = score_row[0]
            operator = rule.condition.get("operator", ">=")
            threshold = rule.condition.get("value", 50)

            if self._check_condition(current_score, operator, threshold):
                with self.db._get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT symbol, name FROM universe WHERE asset_id = ?",
                        (rule.asset_id,),
                    )
                    asset_row = cursor.fetchone()

                if asset_row:
                    symbol, name = asset_row
                    return self.alert_service.create_alert(
                        user_id=rule.user_id,
                        alert_type=rule.alert_type,
                        priority=AlertPriority.MEDIUM.value,
                        title=f"{rule.alert_type.replace('_', ' ').title()}: {symbol}",
                        message=f"{name} ({symbol}) meets condition: score {current_score:.1f} {operator} {threshold}",
                        data={
                            "asset_id": rule.asset_id,
                            "symbol": symbol,
                            "name": name,
                            "score": current_score,
                            "threshold": threshold,
                        },
                        rule_id=rule.id,
                    )

        except Exception as e:
            logger.error(f"Error checking rule {rule.id}: {e}")

        return None

    def _check_global_rule(self, rule) -> List[Alert]:
        """Check a global (all-assets) alert rule"""
        alerts = []

        try:
            # Check all assets
            with self.db._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT asset_id, score FROM scores_latest
                    ORDER BY asset_id
                    """
                )
                assets = cursor.fetchall()

            operator = rule.condition.get("operator", ">=")
            threshold = rule.condition.get("value", 50)

            for asset_id, score in assets:
                if self._check_condition(score, operator, threshold):
                    with self.db._get_connection() as conn:
                        cursor = conn.execute(
                            "SELECT symbol, name FROM universe WHERE asset_id = ?",
                            (asset_id,),
                        )
                        asset_row = cursor.fetchone()

                    if asset_row:
                        symbol, name = asset_row
                        alert = self.alert_service.create_alert(
                            user_id=rule.user_id,
                            alert_type=rule.alert_type,
                            priority=AlertPriority.MEDIUM.value,
                            title=f"Asset Alert: {symbol}",
                            message=f"{name} ({symbol}) meets rule: score {score:.1f} {operator} {threshold}",
                            data={
                                "asset_id": asset_id,
                                "symbol": symbol,
                                "name": name,
                                "score": score,
                            },
                            rule_id=rule.id,
                        )
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking global rule {rule.id}: {e}")

        return alerts
