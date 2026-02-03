"""
MarketGPS Alert System - Usage Examples
Demonstrates how to use the alert system programmatically
"""

from services.alert_service import AlertService
from services.alert_detector import AlertDetector
from storage.sqlite_store import SQLiteStore
from models.alerts import AlertType, AlertPriority


def example_create_basic_rules():
    """Example: Create basic alert rules for a user"""
    print("\n=== Example: Create Alert Rules ===\n")

    db = SQLiteStore()
    service = AlertService(db)
    user_id = "user_demo_001"

    # Rule 1: Alert when AAPL score is 80 or higher
    print("Creating rule: AAPL score >= 80")
    rule1 = service.create_rule(user_id, {
        "alert_type": AlertType.SCORE_THRESHOLD.value,
        "asset_id": "AAPL.US",
        "condition": {
            "field": "score",
            "operator": ">=",
            "value": 80
        },
        "channels": ["in_app", "email"],
        "is_active": True
    })
    print(f"  Created rule: {rule1.id}\n")

    # Rule 2: Alert on any 10%+ score change
    print("Creating rule: Score change >= 10%")
    rule2 = service.create_rule(user_id, {
        "alert_type": AlertType.SCORE_CHANGE.value,
        "condition": {
            "field": "score",
            "operator": "change_percent",
            "value": 10
        },
        "channels": ["in_app"],
        "is_active": True
    })
    print(f"  Created rule: {rule2.id}\n")

    # Rule 3: Alert on opportunities (high score)
    print("Creating rule: Opportunity detection")
    rule3 = service.create_rule(user_id, {
        "alert_type": AlertType.OPPORTUNITY.value,
        "condition": {
            "field": "score",
            "operator": ">=",
            "value": 85
        },
        "channels": ["push", "in_app"],
        "is_active": True
    })
    print(f"  Created rule: {rule3.id}\n")

    return [rule1, rule2, rule3]


def example_manage_alerts():
    """Example: Manage alerts (read, dismiss, etc.)"""
    print("\n=== Example: Manage Alerts ===\n")

    db = SQLiteStore()
    service = AlertService(db)
    user_id = "user_demo_001"

    # Create some test alerts
    print("Creating test alerts...")
    alert1 = service.create_alert(
        user_id=user_id,
        alert_type=AlertType.OPPORTUNITY.value,
        priority=AlertPriority.HIGH.value,
        title="High Opportunity: AAPL",
        message="Apple (AAPL) score reached 85 - excellent opportunity",
        data={
            "asset_id": "AAPL.US",
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "score": 85
        }
    )
    print(f"  Alert 1: {alert1.id}")

    alert2 = service.create_alert(
        user_id=user_id,
        alert_type=AlertType.SCORE_CHANGE.value,
        priority=AlertPriority.MEDIUM.value,
        title="Score Change: MSFT",
        message="Microsoft score increased by 12.5%",
        data={
            "asset_id": "MSFT.US",
            "symbol": "MSFT",
            "change_percent": 12.5
        }
    )
    print(f"  Alert 2: {alert2.id}\n")

    # Get all alerts
    print("Getting user alerts...")
    alerts, total = service.get_user_alerts(user_id, limit=10)
    print(f"  Total alerts: {total}")
    for alert in alerts:
        print(f"    - {alert.title} (status: {alert.status})")
    print()

    # Mark alert as read
    print("Marking alert as read...")
    updated = service.mark_as_read(alert1.id)
    print(f"  Status: {updated.status}")
    print(f"  Read at: {updated.read_at}\n")

    # Get unread count
    print("Getting unread count...")
    unread = service.get_unread_count(user_id)
    print(f"  Unread alerts: {unread}\n")

    # Dismiss alert
    print("Dismissing alert...")
    dismissed = service.dismiss_alert(alert2.id)
    print(f"  Status: {dismissed.status}")
    print(f"  Dismissed at: {dismissed.dismissed_at}\n")

    # Get statistics
    print("Getting user statistics...")
    stats = service.get_statistics(user_id)
    print(f"  Total alerts: {stats.total_alerts}")
    print(f"  Unread: {stats.unread_count}")
    print(f"  Pending: {stats.pending_count}")
    print(f"  Active rules: {stats.active_rules}")
    print(f"  Today's alerts: {stats.today_alerts}\n")


def example_update_rules():
    """Example: Update and manage alert rules"""
    print("\n=== Example: Update Alert Rules ===\n")

    db = SQLiteStore()
    service = AlertService(db)
    user_id = "user_demo_001"

    # Create a rule
    print("Creating alert rule...")
    rule = service.create_rule(user_id, {
        "alert_type": AlertType.SCORE_THRESHOLD.value,
        "asset_id": "GOOG.US",
        "condition": {"field": "score", "operator": ">=", "value": 75},
        "channels": ["in_app"],
        "is_active": True
    })
    print(f"  Rule: {rule.id}")
    print(f"  Threshold: {rule.condition['value']}\n")

    # Update the rule
    print("Updating rule threshold to 80...")
    updated = service.update_rule(rule.id, {
        "condition": {"field": "score", "operator": ">=", "value": 80}
    })
    print(f"  New threshold: {updated.condition['value']}\n")

    # Toggle active status
    print("Disabling rule...")
    toggled = service.toggle_rule(rule.id)
    print(f"  Active: {toggled.is_active}\n")

    # Get all user rules
    print("Getting all user rules...")
    rules = service.get_user_rules(user_id)
    print(f"  Total rules: {len(rules)}")
    for r in rules:
        status = "active" if r.is_active else "inactive"
        print(f"    - {r.alert_type} on {r.asset_id or 'all assets'} ({status})")
    print()

    # Delete rule
    print("Deleting rule...")
    deleted = service.delete_rule(rule.id)
    print(f"  Deleted: {deleted}\n")


def example_detector_score_changes():
    """Example: Detect score changes"""
    print("\n=== Example: Score Change Detection ===\n")

    db = SQLiteStore()
    detector = AlertDetector(db)

    print("Running score change detection...")
    print("  Threshold: 10% change\n")

    # Note: This requires real data in database
    alerts = detector.detect_score_changes(threshold_percent=10)

    print(f"Detected {len(alerts)} score change alerts:")
    for alert in alerts:
        print(f"  - {alert.title}")
        if alert.data:
            print(f"    Symbol: {alert.data.get('symbol')}")
            print(f"    Previous: {alert.data.get('previous_score')}")
            print(f"    Current: {alert.data.get('current_score')}")
            print(f"    Change: {alert.data.get('change_percent')}%")
    print()


def example_detector_opportunities():
    """Example: Detect opportunities"""
    print("\n=== Example: Opportunity Detection ===\n")

    db = SQLiteStore()
    detector = AlertDetector(db)

    print("Running opportunity detection...")
    print("  Minimum score: 80\n")

    # Note: This requires real data in database
    alerts = detector.detect_opportunities(min_score=80)

    print(f"Detected {len(alerts)} opportunities:")
    for alert in alerts:
        print(f"  - {alert.title}")
        if alert.data:
            print(f"    Symbol: {alert.data.get('symbol')}")
            print(f"    Score: {alert.data.get('score')}")
    print()


def example_detector_check_rules():
    """Example: Check user rules against market data"""
    print("\n=== Example: Check User Rules ===\n")

    db = SQLiteStore()
    detector = AlertDetector(db)
    user_id = "user_demo_001"

    print(f"Checking all rules for user: {user_id}\n")

    # Note: This requires real data in database
    alerts = detector.check_user_rules(user_id)

    print(f"Rule evaluation triggered {len(alerts)} alerts:")
    for alert in alerts:
        print(f"  - {alert.title}")
        print(f"    Type: {alert.alert_type}")
        if alert.data:
            print(f"    Asset: {alert.data.get('symbol')}")
    print()


def example_complete_workflow():
    """Example: Complete alert workflow"""
    print("\n" + "=" * 60)
    print("Complete Alert System Workflow Example")
    print("=" * 60)

    # Step 1: Create rules
    rules = example_create_basic_rules()

    # Step 2: Manage alerts
    example_manage_alerts()

    # Step 3: Update rules
    example_update_rules()

    # Step 4: Detection (requires data)
    print("\n" + "=" * 60)
    print("Detection Examples (require market data)")
    print("=" * 60)
    print("These examples show detection but need real market data:")
    print("  - example_detector_score_changes()")
    print("  - example_detector_opportunities()")
    print("  - example_detector_check_rules()")
    print()


if __name__ == "__main__":
    print("\nMarketGPS Alert System Examples\n")
    print("Run individual examples:")
    print("  python -c 'from alert_examples import example_create_basic_rules; example_create_basic_rules()'")
    print("  python -c 'from alert_examples import example_manage_alerts; example_manage_alerts()'")
    print("  python -c 'from alert_examples import example_update_rules; example_update_rules()'")
    print("\nOr run complete workflow:")
    print("  python -c 'from alert_examples import example_complete_workflow; example_complete_workflow()'")
    print()
