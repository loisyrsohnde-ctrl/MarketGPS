"""
Tests for the Alert System
"""

import pytest
import json
from datetime import datetime, timedelta
from models.alerts import (
    Alert,
    AlertRule,
    AlertType,
    AlertStatus,
    AlertPriority,
    AlertCondition,
    AlertStatistics,
    AlertConfig,
)
from services.alert_service import AlertService
from services.alert_detector import AlertDetector
from storage.sqlite_store import SQLiteStore


class TestAlertModels:
    """Test alert data models"""

    def test_alert_creation(self):
        """Test creating an alert"""
        alert = Alert(
            user_id="user123",
            alert_type=AlertType.SCORE_CHANGE.value,
            priority=AlertPriority.MEDIUM.value,
            title="Test Alert",
            message="This is a test alert",
            data={"asset_id": "AAPL.US", "score": 85},
        )

        assert alert.user_id == "user123"
        assert alert.alert_type == AlertType.SCORE_CHANGE.value
        assert alert.status == AlertStatus.PENDING.value
        assert alert.id is not None
        assert alert.created_at is not None

    def test_alert_rule_creation(self):
        """Test creating an alert rule"""
        rule = AlertRule(
            user_id="user123",
            alert_type=AlertType.SCORE_THRESHOLD.value,
            asset_id="AAPL.US",
            condition={
                "field": "score",
                "operator": ">=",
                "value": 80,
            },
            channels=["email", "in_app"],
        )

        assert rule.user_id == "user123"
        assert rule.alert_type == AlertType.SCORE_THRESHOLD.value
        assert rule.asset_id == "AAPL.US"
        assert rule.is_active is True
        assert "email" in rule.channels

    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        alert = Alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Opportunity Found",
            message="New opportunity detected",
        )

        alert_dict = alert.to_dict()

        assert isinstance(alert_dict, dict)
        assert alert_dict["user_id"] == "user123"
        assert alert_dict["alert_type"] == AlertType.OPPORTUNITY.value
        assert "id" in alert_dict
        assert "created_at" in alert_dict

    def test_alert_condition(self):
        """Test alert condition"""
        condition = AlertCondition(
            field="score",
            operator=">=",
            value=80,
        )

        assert condition.field == "score"
        assert condition.operator == ">="
        assert condition.value == 80


class TestAlertService:
    """Test alert service"""

    @pytest.fixture
    def alert_service(self):
        """Create alert service with test database"""
        store = SQLiteStore(":memory:")
        # Initialize tables
        store.init_db()
        service = AlertService(store)
        return service

    def test_create_rule(self, alert_service):
        """Test creating an alert rule"""
        rule_data = {
            "alert_type": AlertType.SCORE_THRESHOLD.value,
            "asset_id": "AAPL.US",
            "condition": {
                "field": "score",
                "operator": ">=",
                "value": 80,
            },
            "channels": ["in_app"],
        }

        rule = alert_service.create_rule("user123", rule_data)

        assert rule.user_id == "user123"
        assert rule.alert_type == AlertType.SCORE_THRESHOLD.value
        assert rule.asset_id == "AAPL.US"

    def test_get_user_rules(self, alert_service):
        """Test retrieving user rules"""
        rule_data = {
            "alert_type": AlertType.SCORE_THRESHOLD.value,
            "asset_id": "AAPL.US",
            "condition": {"field": "score", "operator": ">=", "value": 80},
            "channels": ["in_app"],
        }

        alert_service.create_rule("user123", rule_data)
        alert_service.create_rule("user123", rule_data)

        rules = alert_service.get_user_rules("user123")

        assert len(rules) == 2
        assert all(r.user_id == "user123" for r in rules)

    def test_update_rule(self, alert_service):
        """Test updating an alert rule"""
        rule_data = {
            "alert_type": AlertType.SCORE_THRESHOLD.value,
            "asset_id": "AAPL.US",
            "condition": {"field": "score", "operator": ">=", "value": 80},
            "channels": ["in_app"],
        }

        rule = alert_service.create_rule("user123", rule_data)

        updated = alert_service.update_rule(rule.id, {"is_active": False})

        assert updated.is_active is False

    def test_create_alert(self, alert_service):
        """Test creating an alert"""
        alert = alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="New Opportunity",
            message="High score detected",
            data={"asset_id": "AAPL.US", "score": 85},
        )

        assert alert.user_id == "user123"
        assert alert.title == "New Opportunity"
        assert alert.status == AlertStatus.PENDING.value

    def test_get_user_alerts(self, alert_service):
        """Test retrieving user alerts"""
        alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Alert 1",
            message="Test",
        )

        alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Alert 2",
            message="Test",
        )

        alerts, total = alert_service.get_user_alerts("user123")

        assert total == 2
        assert len(alerts) == 2

    def test_mark_alert_as_read(self, alert_service):
        """Test marking alert as read"""
        alert = alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Test",
            message="Test",
        )

        updated = alert_service.mark_as_read(alert.id)

        assert updated.status == AlertStatus.READ.value
        assert updated.read_at is not None

    def test_dismiss_alert(self, alert_service):
        """Test dismissing an alert"""
        alert = alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Test",
            message="Test",
        )

        updated = alert_service.dismiss_alert(alert.id)

        assert updated.status == AlertStatus.DISMISSED.value
        assert updated.dismissed_at is not None

    def test_get_unread_count(self, alert_service):
        """Test getting unread alert count"""
        alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Alert 1",
            message="Test",
        )

        alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Alert 2",
            message="Test",
        )

        count = alert_service.get_unread_count("user123")

        assert count == 2

    def test_get_statistics(self, alert_service):
        """Test getting alert statistics"""
        alert_service.create_alert(
            user_id="user123",
            alert_type=AlertType.OPPORTUNITY.value,
            title="Test",
            message="Test",
        )

        alert_service.create_rule(
            "user123",
            {
                "alert_type": AlertType.SCORE_THRESHOLD.value,
                "asset_id": "AAPL.US",
                "condition": {"field": "score", "operator": ">=", "value": 80},
            },
        )

        stats = alert_service.get_statistics("user123")

        assert stats.user_id == "user123"
        assert stats.total_alerts == 1
        assert stats.unread_count == 1
        assert stats.active_rules == 1


class TestAlertDetector:
    """Test alert detector"""

    @pytest.fixture
    def detector(self):
        """Create alert detector with test database"""
        store = SQLiteStore(":memory:")
        store.init_db()
        detector = AlertDetector(store)
        return detector

    def test_detector_initialization(self, detector):
        """Test detector initializes properly"""
        assert detector.db is not None
        assert detector.alert_service is not None

    def test_score_change_detection(self, detector):
        """Test score change detection"""
        # This would require mock data in the database
        # For now, test that the method exists and is callable
        assert callable(detector.detect_score_changes)

    def test_opportunity_detection(self, detector):
        """Test opportunity detection"""
        assert callable(detector.detect_opportunities)

    def test_check_condition(self, detector):
        """Test condition checking"""
        assert detector._check_condition(85, ">=", 80) is True
        assert detector._check_condition(75, ">=", 80) is False
        assert detector._check_condition(85, ">", 80) is True
        assert detector._check_condition(80, ">", 80) is False
        assert detector._check_condition(75, "<", 80) is True
        assert detector._check_condition(85, "<", 80) is False


class TestAlertConfig:
    """Test alert configuration"""

    def test_config_defaults(self):
        """Test default configuration values"""
        assert AlertConfig.SCORE_CHANGE_THRESHOLD_PERCENT == 10
        assert AlertConfig.OPPORTUNITY_MIN_SCORE == 80
        assert AlertConfig.BREAKING_NEWS_MIN_SCORE == 7
        assert AlertConfig.ALERT_RETENTION_DAYS == 30
        assert AlertConfig.MAX_ALERTS_PER_HOUR == 50
        assert "in_app" in AlertConfig.DEFAULT_CHANNELS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
