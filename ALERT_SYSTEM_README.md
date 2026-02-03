# MarketGPS Alert System Documentation

## Overview

The MarketGPS Alert System is a comprehensive framework for generating, managing, and delivering intelligent notifications to users based on market data changes and user-defined rules. The system detects significant market events and delivers timely alerts through multiple channels.

## Features

### Alert Types

1. **Score Changes** (`score_change`)
   - Detects when an asset's score changes by a threshold percentage (default 10%)
   - Triggered automatically when comparing daily scores
   - Includes direction and magnitude of change

2. **Score Thresholds** (`score_threshold`)
   - User-defined rules that trigger when scores cross specific values
   - Supports operators: `>=`, `>`, `<=`, `<`, `==`, `!=`
   - Can be set up for individual assets

3. **Opportunities** (`opportunity`)
   - Detects high-scoring assets (default threshold: 80)
   - Identifies potential investment opportunities
   - Only alerts once per asset per 24 hours

4. **Watchlist Alerts** (`watchlist_alert`)
   - Monitors changes in user's watched assets
   - Triggers on 5% score changes
   - Provides quick overview of portfolio changes

5. **Breaking News** (`breaking_news`)
   - Detects important news items affecting assets
   - Filters by news sentiment score (default minimum: 7)
   - High priority alerts for time-sensitive information

6. **Price Alerts** (`price_alert`)
   - Monitors price levels (infrastructure ready)
   - Supports price above/below triggers

## Architecture

### Components

#### 1. Data Models (`backend/models/alerts.py`)
- `Alert` - Individual notification instance
- `AlertRule` - User-defined trigger rule
- `AlertType` - Enum of alert categories
- `AlertStatus` - Alert lifecycle states
- `AlertPriority` - Severity levels (low, medium, high, critical)
- `AlertCondition` - Single condition in a rule
- `AlertConfig` - System configuration

#### 2. Alert Service (`backend/services/alert_service.py`)
Manages all alert and rule operations:

```python
# Create a rule
rule = alert_service.create_rule(user_id, {
    "alert_type": "score_threshold",
    "asset_id": "AAPL.US",
    "condition": {
        "field": "score",
        "operator": ">=",
        "value": 80
    },
    "channels": ["email", "in_app"]
})

# Get user's rules
rules = alert_service.get_user_rules(user_id, active_only=True)

# Create an alert
alert = alert_service.create_alert(
    user_id=user_id,
    alert_type="opportunity",
    title="New Opportunity",
    message="AAPL.US scored 85 - high opportunity",
    data={"asset_id": "AAPL.US", "score": 85}
)

# Get user's alerts
alerts, total = alert_service.get_user_alerts(
    user_id=user_id,
    status="pending",
    limit=50,
    offset=0
)

# Mark as read
alert = alert_service.mark_as_read(alert_id)

# Dismiss alert
alert = alert_service.dismiss_alert(alert_id)

# Get statistics
stats = alert_service.get_statistics(user_id)
# Returns: {total_alerts, unread_count, pending_count, active_rules, today_alerts}
```

#### 3. Alert Detector (`backend/services/alert_detector.py`)
Automatically detects alert conditions and generates alerts:

```python
# Detect score changes (called by scheduler)
alerts = detector.detect_score_changes(threshold_percent=10)

# Detect opportunities
alerts = detector.detect_opportunities(min_score=80)

# Detect score thresholds from active rules
alerts = detector.detect_score_thresholds()

# Detect watchlist changes for a user
alerts = detector.detect_watchlist_changes(user_id)

# Detect breaking news
alerts = detector.detect_breaking_news(min_score=7)

# Check all rules for a user
alerts = detector.check_user_rules(user_id)
```

#### 4. API Routes (`backend/alert_routes.py`)
RESTful endpoints for alert management:

```
GET    /api/alerts                    - List user alerts
GET    /api/alerts/unread-count       - Get unread count
GET    /api/alerts/statistics         - Get alert statistics
GET    /api/alerts/{alert_id}         - Get specific alert
POST   /api/alerts/{alert_id}/read    - Mark as read
POST   /api/alerts/{alert_id}/dismiss - Dismiss alert
POST   /api/alerts/dismiss-all        - Dismiss all pending

GET    /api/alerts/rules              - List user's rules
POST   /api/alerts/rules              - Create new rule
GET    /api/alerts/rules/{rule_id}    - Get specific rule
PUT    /api/alerts/rules/{rule_id}    - Update rule
DELETE /api/alerts/rules/{rule_id}    - Delete rule
POST   /api/alerts/rules/{rule_id}/toggle - Toggle active/inactive

POST   /api/alerts/detect/score-changes   - Trigger score detection
POST   /api/alerts/detect/opportunities   - Trigger opportunity detection
POST   /api/alerts/detect/breaking-news   - Trigger news detection
```

### Database Schema

#### alert_rules Table
```sql
CREATE TABLE alert_rules (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- User who owns the rule
    alert_type TEXT NOT NULL,               -- Type of alert
    asset_id TEXT,                          -- Specific asset (NULL for global)
    condition_json TEXT NOT NULL,           -- {field, operator, value}
    channels_json TEXT,                     -- ["email", "push", "in_app"]
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### alerts Table
```sql
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,                    -- UUID
    user_id TEXT NOT NULL,                  -- Who receives this
    rule_id TEXT,                           -- Which rule triggered it
    alert_type TEXT NOT NULL,               -- Type of alert
    priority TEXT DEFAULT 'medium',         -- low, medium, high, critical
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    data_json TEXT,                         -- {asset_id, symbol, score, etc}
    status TEXT DEFAULT 'pending',          -- pending, sent, read, dismissed
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    read_at TEXT,
    dismissed_at TEXT,
    sent_at TEXT
);
```

## Usage Examples

### Create Alert Rules Programmatically

```python
from services.alert_service import AlertService
from storage.sqlite_store import SQLiteStore

db = SQLiteStore()
service = AlertService(db)

# Rule: Alert when AAPL score >= 80
rule = service.create_rule("user123", {
    "alert_type": "score_threshold",
    "asset_id": "AAPL.US",
    "condition": {
        "field": "score",
        "operator": ">=",
        "value": 80
    },
    "channels": ["email", "in_app"]
})

# Rule: Alert on 10% score changes (global)
rule = service.create_rule("user123", {
    "alert_type": "score_change",
    "condition": {
        "field": "score",
        "operator": "change_percent",
        "value": 10
    },
    "channels": ["in_app"]
})

# Rule: Price alerts
rule = service.create_rule("user123", {
    "alert_type": "price_alert",
    "asset_id": "AAPL.US",
    "condition": {
        "field": "price",
        "operator": "above",
        "value": 150.0
    },
    "channels": ["push", "in_app"]
})
```

### API Usage Examples

```bash
# Create a rule via API
curl -X POST http://localhost:8000/api/alerts/rules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "alert_type": "score_threshold",
    "asset_id": "AAPL.US",
    "condition": {"field": "score", "operator": ">=", "value": 80},
    "channels": ["email", "in_app"]
  }'

# Get user alerts
curl http://localhost:8000/api/alerts?status=pending&limit=20 \
  -H "Authorization: Bearer TOKEN"

# Mark alert as read
curl -X POST http://localhost:8000/api/alerts/{alert_id}/read \
  -H "Authorization: Bearer TOKEN"

# Get statistics
curl http://localhost:8000/api/alerts/statistics \
  -H "Authorization: Bearer TOKEN"
```

## Scheduler Integration

### Running Alert Generation Job

```bash
# Generate all alerts (detect changes, opportunities, news)
python -m pipeline.jobs --generate-alerts

# Can be run hourly or daily via cron:
0 * * * * cd /path/to/marketgps && python -m pipeline.jobs --generate-alerts
```

### Scheduler Configuration

Add to your cron or APScheduler configuration:

```python
from apscheduler.schedulers.background import BackgroundScheduler
from pipeline.jobs import run_generate_alerts

scheduler = BackgroundScheduler()

# Run alert detection every hour
scheduler.add_job(
    func=run_generate_alerts,
    trigger="cron",
    hour="*",  # Every hour
    minute="0",
    id="generate_alerts"
)

scheduler.start()
```

## Configuration

### Alert System Config (`models/alerts.py`)

```python
class AlertConfig:
    # Score change detection threshold
    SCORE_CHANGE_THRESHOLD_PERCENT = 10

    # Opportunity detection threshold
    OPPORTUNITY_MIN_SCORE = 80

    # News score minimum
    BREAKING_NEWS_MIN_SCORE = 7

    # How long to keep alerts
    ALERT_RETENTION_DAYS = 30

    # Rate limiting
    MAX_ALERTS_PER_HOUR = 50

    # Email digest settings
    EMAIL_DIGEST_ENABLED = True
    EMAIL_DIGEST_TIME = "08:00"  # UTC
    EMAIL_DIGEST_FREQUENCY = "daily"

    # Notification channels
    PUSH_ENABLED = True
    INAPP_ENABLED = True
```

## Frontend Integration

### Alert Display Component Example

```javascript
// Get alerts
async function fetchAlerts() {
  const response = await fetch('/api/alerts?limit=10', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
}

// Mark as read
async function markAsRead(alertId) {
  await fetch(`/api/alerts/${alertId}/read`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// Get unread count for badge
async function getUnreadCount() {
  const response = await fetch('/api/alerts/unread-count', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.unread_count;
}

// Create rule
async function createAlertRule(ruleData) {
  const response = await fetch('/api/alerts/rules', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(ruleData)
  });
  return response.json();
}
```

## Testing

```bash
# Run alert system tests
pytest tests/test_alert_system.py -v

# Test with coverage
pytest tests/test_alert_system.py --cov=services --cov=models
```

## Performance Considerations

1. **Database Indexing** - Queries are indexed by user_id, status, and created_at
2. **Alert Cleanup** - Old alerts (>30 days) can be archived/deleted
3. **Rate Limiting** - Max 50 alerts per user per hour to prevent spam
4. **Batch Processing** - Detection runs once per hour, not on every request
5. **User Rules** - Only active rules are checked during detection

## Future Enhancements

- Email digest summaries
- SMS notifications
- Push notification providers (Firebase, OneSignal)
- Machine learning for alert timing optimization
- Alert templates with customizable messages
- Notification scheduling (quiet hours)
- Alert analytics and insights
- Bulk alert management
- Webhook integrations
- Alert frequency learning

## Troubleshooting

### Alerts not being generated
1. Check if rules are active: `GET /api/alerts/rules`
2. Verify market data exists in database
3. Check logs: `python -m pipeline.jobs --generate-alerts`
4. Ensure detection job is running

### High alert volume
- Adjust thresholds in AlertConfig
- Set MAX_ALERTS_PER_HOUR lower
- Enable alert batching
- Use email digests instead of instant notifications

### Database size growing
- Increase ALERT_RETENTION_DAYS or decrease it
- Run cleanup: `alert_service.cleanup_old_alerts(days=7)`
- Archive old alerts to separate table

## Support

For issues or questions about the alert system, check:
- API response status codes and error messages
- Database constraints and indexes
- Alert rule conditions and operators
- Notification channel configuration
