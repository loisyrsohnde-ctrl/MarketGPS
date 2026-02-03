"""
MarketGPS - Alert Service
Manages alert rules, generates alerts, and tracks alert lifecycle
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from models.alerts import (
    Alert,
    AlertRule,
    AlertType,
    AlertStatus,
    AlertPriority,
    AlertStatistics,
    AlertConfig,
)

logger = get_logger(__name__)


class AlertService:
    """Service for managing alerts and alert rules"""

    def __init__(self, db: Optional[SQLiteStore] = None):
        """Initialize alert service with database connection"""
        self.db = db or SQLiteStore()

    # ═══════════════════════════════════════════════════════════════════════════
    # ALERT RULES MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def create_rule(self, user_id: str, rule_data: Dict[str, Any]) -> AlertRule:
        """
        Create a new alert rule for a user

        Args:
            user_id: User ID
            rule_data: Rule configuration containing:
                - alert_type: Type of alert (from AlertType enum)
                - asset_id: Optional, specific asset ID or None for global
                - condition: Dict with field, operator, value
                - channels: List of notification channels

        Returns:
            Created AlertRule
        """
        rule_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        # Validate alert type
        try:
            AlertType[rule_data.get("alert_type", "").upper()]
        except KeyError:
            raise ValueError(f"Invalid alert type: {rule_data.get('alert_type')}")

        rule = AlertRule(
            id=rule_id,
            user_id=user_id,
            alert_type=rule_data.get("alert_type", ""),
            asset_id=rule_data.get("asset_id"),
            condition=rule_data.get("condition", {}),
            channels=rule_data.get("channels", ["in_app"]),
            is_active=rule_data.get("is_active", True),
            created_at=now,
            updated_at=now,
        )

        # Store in database
        with self.db._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO alert_rules
                (id, user_id, alert_type, asset_id, condition_json, channels_json, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule.id,
                    rule.user_id,
                    rule.alert_type,
                    rule.asset_id,
                    json.dumps(rule.condition),
                    json.dumps(rule.channels),
                    1 if rule.is_active else 0,
                    rule.created_at,
                    rule.updated_at,
                ),
            )
            conn.commit()

        logger.info(f"Created alert rule {rule_id} for user {user_id}")
        return rule

    def get_user_rules(self, user_id: str, active_only: bool = False) -> List[AlertRule]:
        """Get all alert rules for a user"""
        query = "SELECT * FROM alert_rules WHERE user_id = ?"
        params = [user_id]

        if active_only:
            query += " AND is_active = 1"

        with self.db._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        rules = []
        for row in rows:
            rule = self._row_to_rule(row)
            rules.append(rule)

        return rules

    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific alert rule"""
        with self.db._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
            row = cursor.fetchone()

        if row:
            return self._row_to_rule(row)
        return None

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> AlertRule:
        """Update an alert rule"""
        rule = self.get_rule(rule_id)
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        # Update fields
        if "alert_type" in updates:
            rule.alert_type = updates["alert_type"]
        if "asset_id" in updates:
            rule.asset_id = updates["asset_id"]
        if "condition" in updates:
            rule.condition = updates["condition"]
        if "channels" in updates:
            rule.channels = updates["channels"]
        if "is_active" in updates:
            rule.is_active = updates["is_active"]

        rule.updated_at = datetime.utcnow().isoformat()

        # Store in database
        with self.db._get_connection() as conn:
            conn.execute(
                """
                UPDATE alert_rules
                SET alert_type = ?, asset_id = ?, condition_json = ?, channels_json = ?,
                    is_active = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    rule.alert_type,
                    rule.asset_id,
                    json.dumps(rule.condition),
                    json.dumps(rule.channels),
                    1 if rule.is_active else 0,
                    rule.updated_at,
                    rule.id,
                ),
            )
            conn.commit()

        logger.info(f"Updated alert rule {rule_id}")
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        with self.db._get_connection() as conn:
            cursor = conn.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
            conn.commit()
            return cursor.rowcount > 0

    def toggle_rule(self, rule_id: str) -> AlertRule:
        """Toggle rule active/inactive status"""
        rule = self.get_rule(rule_id)
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        rule.is_active = not rule.is_active
        return self.update_rule(rule_id, {"is_active": rule.is_active})

    # ═══════════════════════════════════════════════════════════════════════════
    # ALERT GENERATION AND MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def create_alert(
        self,
        user_id: str,
        alert_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        rule_id: Optional[str] = None,
        priority: str = "medium",
        channels: Optional[List[str]] = None,
    ) -> Alert:
        """Create a new alert"""
        alert_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        alert = Alert(
            id=alert_id,
            user_id=user_id,
            rule_id=rule_id,
            alert_type=alert_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            status=AlertStatus.PENDING.value,
            created_at=now,
            read_at=None,
            dismissed_at=None,
            sent_at=None,
        )

        # Store in database
        with self.db._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO alerts
                (id, user_id, rule_id, alert_type, priority, title, message, data_json, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.id,
                    alert.user_id,
                    alert.rule_id,
                    alert.alert_type,
                    alert.priority,
                    alert.title,
                    alert.message,
                    json.dumps(alert.data),
                    alert.status,
                    alert.created_at,
                ),
            )
            conn.commit()

        logger.info(f"Created alert {alert_id} for user {user_id}")
        return alert

    def get_user_alerts(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        days: Optional[int] = None,
    ) -> Tuple[List[Alert], int]:
        """
        Get alerts for a user

        Returns:
            Tuple of (alerts list, total count)
        """
        query = "SELECT * FROM alerts WHERE user_id = ?"
        params = [user_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        if days:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            query += " AND created_at >= ?"
            params.append(cutoff_date)

        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        with self.db._get_connection() as conn:
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()[0]

        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.db._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        alerts = [self._row_to_alert(row) for row in rows]
        return alerts, total

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get a specific alert"""
        with self.db._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
            row = cursor.fetchone()

        if row:
            return self._row_to_alert(row)
        return None

    def mark_as_read(self, alert_id: str) -> Alert:
        """Mark alert as read"""
        alert = self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        now = datetime.utcnow().isoformat()
        alert.read_at = now
        alert.status = AlertStatus.READ.value

        with self.db._get_connection() as conn:
            conn.execute(
                "UPDATE alerts SET read_at = ?, status = ? WHERE id = ?",
                (now, alert.status, alert_id),
            )
            conn.commit()

        return alert

    def mark_as_sent(self, alert_id: str) -> Alert:
        """Mark alert as sent"""
        alert = self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        now = datetime.utcnow().isoformat()
        alert.sent_at = now
        alert.status = AlertStatus.SENT.value

        with self.db._get_connection() as conn:
            conn.execute(
                "UPDATE alerts SET sent_at = ?, status = ? WHERE id = ?",
                (now, alert.status, alert_id),
            )
            conn.commit()

        return alert

    def dismiss_alert(self, alert_id: str) -> Alert:
        """Dismiss an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")

        now = datetime.utcnow().isoformat()
        alert.dismissed_at = now
        alert.status = AlertStatus.DISMISSED.value

        with self.db._get_connection() as conn:
            conn.execute(
                "UPDATE alerts SET dismissed_at = ?, status = ? WHERE id = ?",
                (now, alert.status, alert_id),
            )
            conn.commit()

        return alert

    def dismiss_all_for_user(self, user_id: str) -> int:
        """Dismiss all pending alerts for a user"""
        now = datetime.utcnow().isoformat()

        with self.db._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE alerts
                SET status = ?, dismissed_at = ?
                WHERE user_id = ? AND status = ?
                """,
                (AlertStatus.DISMISSED.value, now, user_id, AlertStatus.PENDING.value),
            )
            conn.commit()
            return cursor.rowcount

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS AND QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread alerts"""
        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE user_id = ? AND status IN (?, ?)",
                (user_id, AlertStatus.SENT.value, AlertStatus.PENDING.value),
            )
            count = cursor.fetchone()[0]
        return count

    def get_statistics(self, user_id: str) -> AlertStatistics:
        """Get alert statistics for a user"""
        with self.db._get_connection() as conn:
            # Total alerts
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE user_id = ?", (user_id,)
            )
            total = cursor.fetchone()[0]

            # Unread alerts
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE user_id = ? AND status IN (?, ?)",
                (user_id, AlertStatus.SENT.value, AlertStatus.PENDING.value),
            )
            unread = cursor.fetchone()[0]

            # Pending alerts
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE user_id = ? AND status = ?",
                (user_id, AlertStatus.PENDING.value),
            )
            pending = cursor.fetchone()[0]

            # Active rules
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alert_rules WHERE user_id = ? AND is_active = 1",
                (user_id,),
            )
            active_rules = cursor.fetchone()[0]

            # Today's alerts
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM alerts WHERE user_id = ? AND created_at >= ?",
                (user_id, today_start),
            )
            today_alerts = cursor.fetchone()[0]

        return AlertStatistics(
            user_id=user_id,
            total_alerts=total,
            unread_count=unread,
            pending_count=pending,
            active_rules=active_rules,
            today_alerts=today_alerts,
        )

    def cleanup_old_alerts(self, days: int = 30) -> int:
        """Remove alerts older than specified days"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self.db._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM alerts WHERE created_at < ?", (cutoff_date,)
            )
            conn.commit()
            return cursor.rowcount

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _row_to_rule(self, row: tuple) -> AlertRule:
        """Convert database row to AlertRule object"""
        return AlertRule(
            id=row[0],
            user_id=row[1],
            alert_type=row[2],
            asset_id=row[3],
            condition=json.loads(row[4]) if row[4] else {},
            channels=json.loads(row[5]) if row[5] else ["in_app"],
            is_active=bool(row[6]),
            created_at=row[7],
            updated_at=row[8],
        )

    def _row_to_alert(self, row: tuple) -> Alert:
        """Convert database row to Alert object"""
        return Alert(
            id=row[0],
            user_id=row[1],
            rule_id=row[2],
            alert_type=row[3],
            priority=row[4] if len(row) > 4 else "medium",
            title=row[5] if len(row) > 5 else "",
            message=row[6] if len(row) > 6 else "",
            data=json.loads(row[7]) if (len(row) > 7 and row[7]) else {},
            status=row[8] if len(row) > 8 else AlertStatus.PENDING.value,
            created_at=row[9] if len(row) > 9 else "",
            read_at=row[10] if len(row) > 10 else None,
            dismissed_at=row[11] if len(row) > 11 else None,
            sent_at=row[12] if len(row) > 12 else None,
        )
