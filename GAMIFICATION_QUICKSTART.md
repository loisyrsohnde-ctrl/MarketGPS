# Gamification System - Quick Start Guide

## Installation & Setup

### 1. Database Tables

Tables are automatically created on application startup via `ensure_tables_exist()` in `main.py`. No manual migration needed.

### 2. Import Routes

The gamification routes are already included in `main.py`:

```python
from gamification_routes import router as gamification_router
app.include_router(gamification_router)
```

### 3. Initialize User (Optional)

When a user first logs in, initialize their gamification profile:

```python
POST /api/gamification/initialize
```

Or let it auto-initialize on first action.

## Core Integration Points

### Track Actions

Whenever users perform key actions, call the gamification service:

```python
from services.gamification_service import GamificationService

gamification = GamificationService()

# When user views an asset
gamification.record_action("user_id", "view_asset", {"asset_id": "AAPL"})

# When user analyzes an asset
gamification.record_action("user_id", "analyze", {"asset_id": "AAPL", "score": 85})

# When user creates an alert
gamification.record_action("user_id", "create_alert", {"asset_id": "AAPL"})

# When user adds to watchlist
gamification.record_action("user_id", "add_watchlist", {"asset_id": "AAPL"})

# When user reads news
gamification.record_action("user_id", "read_news", {"news_id": "123"})

# When user runs backtest
gamification.record_action("user_id", "run_backtest", {"strategy_id": "123"})
```

The service automatically:
- Awards points
- Updates streaks
- Checks for badge unlocks
- Updates objective progress

### Display User Progress

Get user's gamification progress for UI display:

```python
GET /api/gamification/progress

Response:
{
  "user_id": "user_123",
  "total_points": 2500,
  "current_level": 6,
  "level_name": "Confirmed Strategist",
  "current_streak": 12,
  "longest_streak": 45,
  "badges_earned_count": 18,
  "last_activity_date": "2025-02-03T14:30:00"
}
```

### Get Objectives

Display daily and weekly objectives:

```python
GET /api/gamification/objectives?objective_type=daily

Response: [
  {
    "id": "obj_123",
    "title": "Daily Login",
    "description": "Log in today",
    "action": "login",
    "target": 1,
    "current": 1,
    "points_reward": 10,
    "objective_type": "daily",
    "expires_at": "2025-02-04T00:00:00",
    "progress_percentage": 100,
    "completed": true
  }
]
```

### Get Badges

Show earned and available badges:

```python
GET /api/gamification/badges

Response: {
  "earned": [
    {
      "id": "first_login",
      "name": "First Step",
      "description": "Complete your first login",
      "icon": "👣",
      "category": "explorer",
      "points_reward": 10,
      "rarity": "common",
      "earned_at": "2025-01-15T10:30:00"
    }
  ],
  "available": [
    {
      "id": "explorer_10",
      "name": "Explorer",
      "description": "View 10 different assets",
      "icon": "🔍",
      "category": "explorer",
      "points_reward": 25,
      "rarity": "common",
      "progress": {
        "current": 7,
        "target": 10,
        "percentage": 70
      }
    }
  ]
}
```

### Leaderboard

Show global rankings:

```python
GET /api/gamification/leaderboard/weekly?limit=100

Response: [
  {
    "rank": 1,
    "user_id": "top_user",
    "total_points": 5000,
    "current_level": 9,
    "level_name": "Finance Guru",
    "current_streak": 28,
    "badges_count": 25
  }
]
```

Get user's rank:

```python
GET /api/gamification/leaderboard/rank?period=weekly

Response: {
  "success": true,
  "period": "weekly",
  "rank": 45,
  "percentile": 78.5,
  "points": 1250
}
```

## Frontend Implementation Examples

### Level & Progress Widget

```html
<div class="gamification-card">
  <div class="level-section">
    <div class="level-badge">
      <span class="level-number">6</span>
      <div class="level-name">Confirmed Strategist</div>
    </div>
  </div>

  <div class="progress-section">
    <div class="points-display">
      <span class="current">1500</span>
      <span class="separator">/</span>
      <span class="next">2500</span>
      <span class="label">to Level 7</span>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" style="width: 60%"></div>
    </div>
  </div>

  <div class="streak-section">
    <span class="streak-icon">🔥</span>
    <span class="streak-count">12 days</span>
    <span class="label">current streak</span>
  </div>
</div>
```

### Daily Objectives Display

```html
<div class="objectives-panel">
  <h3>Today's Missions</h3>
  <div class="objectives-list">
    <div class="objective completed">
      <div class="checkbox">✓</div>
      <div class="content">
        <div class="title">Daily Login</div>
        <div class="progress">1 / 1</div>
      </div>
      <div class="reward">+10 pts</div>
    </div>
    <div class="objective in-progress">
      <div class="checkbox"></div>
      <div class="content">
        <div class="title">Quick Check</div>
        <div class="progress">2 / 3 assets</div>
        <div class="bar">
          <div class="fill" style="width: 66%"></div>
        </div>
      </div>
      <div class="reward">+15 pts</div>
    </div>
  </div>
</div>
```

### Badges Showcase

```html
<div class="badges-section">
  <h3>Badges Earned ({earned_count})</h3>
  <div class="badges-grid">
    <div class="badge earned" title="Pro Analyst - View 100 assets">
      <div class="icon">🎯</div>
      <div class="rarity epic">Epic</div>
    </div>
    <div class="badge earned" title="Devoted - 30 day streak">
      <div class="icon">👑</div>
      <div class="rarity legendary">Legendary</div>
    </div>
  </div>

  <h3>Unlock Next ({available_count})</h3>
  <div class="available-badges">
    <div class="badge available" title="Master Analyst - 500 analyses">
      <div class="icon">🏆</div>
      <div class="progress">280 / 500</div>
    </div>
  </div>
</div>
```

### Leaderboard View

```html
<div class="leaderboard">
  <div class="tabs">
    <button class="active" onclick="loadLeaderboard('weekly')">This Week</button>
    <button onclick="loadLeaderboard('monthly')">This Month</button>
    <button onclick="loadLeaderboard('all-time')">All Time</button>
  </div>

  <div class="leaderboard-table">
    <div class="header-row">
      <div class="col rank">Rank</div>
      <div class="col user">User</div>
      <div class="col level">Level</div>
      <div class="col points">Points</div>
      <div class="col streak">Streak</div>
    </div>
    <div class="data-row">
      <div class="col rank">1</div>
      <div class="col user">top_trader</div>
      <div class="col level">
        <span class="badge">9</span>
        <span class="name">Finance Guru</span>
      </div>
      <div class="col points">5,240</div>
      <div class="col streak">🔥 28</div>
    </div>
  </div>
</div>
```

## Event Tracking Checklist

Add gamification tracking to these user actions:

- [ ] **Login** - Already tracked if you call the endpoint
- [ ] **View Asset** - Add when user views asset details
- [ ] **Analyze Asset** - Add when analysis is performed
- [ ] **Create Alert** - Add when alert is created
- [ ] **Add to Watchlist** - Add when asset is saved
- [ ] **Read News** - Add when news article is read
- [ ] **Run Backtest** - Add when backtest is executed
- [ ] **View Portfolio** - Add when portfolio page is loaded
- [ ] **View Morning Brief** - Add when morning brief is opened
- [ ] **Share Analysis** - Add when user shares content
- [ ] **Subscribe to Pro** - Add after successful subscription

## Example: Adding Tracking to Asset Analysis

In your asset analysis endpoint:

```python
# In your api_routes.py or similar
from services.gamification_service import GamificationService

gamification_service = GamificationService()

@router.post("/api/assets/{asset_id}/analyze")
async def analyze_asset(asset_id: str, user_id: str = Depends(get_user_id)):
    # Perform analysis...
    result = perform_analysis(asset_id)

    # Track for gamification
    gamification_service.record_action(
        user_id=user_id,
        action="analyze",
        metadata={
            "asset_id": asset_id,
            "score": result.score,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    return result
```

## Customization

### Change Point Values

Edit `backend/config/gamification_config.py`:

```python
POINTS_PER_ACTION = {
    "analyze": 20,  # Increase reward
    "view_asset": 1,  # Decrease reward
}
```

### Add New Badge

Add to `BADGES` list in `backend/config/gamification_config.py`:

```python
{
    "id": "my_new_badge",
    "name": "Badge Name",
    "description": "What user must do",
    "icon": "🎉",
    "category": "milestone",
    "points_reward": 50,
    "condition": {"action": "some_action", "count": 5},
    "rarity": "rare"
}
```

### Change Level Requirements

Edit `LEVELS` in config:

```python
{
    "level": 11,
    "name": "Supreme Legend",
    "min_points": 15000,
    "max_points": 25000,
    "perks": ["ultimate_features", "legendary_status"]
}
```

### Disable Daily Cap

In `backend/config/gamification_config.py`:

```python
ENGAGEMENT_SETTINGS = {
    "MAX_DAILY_POINTS": float('inf'),  # Remove cap
}
```

## Monitoring & Analytics

Get comprehensive stats on user engagement:

```python
GET /api/gamification/stats

Response: {
  "total_points": 2500,
  "current_level": 6,
  "current_streak": 12,
  "longest_streak": 45,
  "badges_earned": 18,
  "objectives_completed": 45,
  "points_7_days": 320,
  "points_30_days": 1200,
  "avg_daily_points": 15.8,
  "rank": 45,
  "rank_percentile": 78.5,
  "account_age_days": 89
}
```

## Testing

Run test suite:

```bash
cd /sessions/funny-exciting-einstein/mnt/MarketGPS/backend
pytest tests/test_gamification_service.py -v
```

## Troubleshooting

### User has no progress

Call `/api/gamification/initialize` to create profile.

### Actions not being recorded

1. Ensure `gamification_service.record_action()` is called
2. Check user_id is passed correctly
3. Verify action name matches configured actions

### Badges not unlocking

1. Check condition in badge config
2. Run `/api/gamification/badges` to see progress
3. Verify action is being recorded (check user_actions table)

### Performance Issues

- Add database indexes (already done in schema)
- Cache leaderboards for 1 hour
- Archive old actions (> 90 days) to separate table

## File Structure

```
backend/
├── models/
│   └── gamification.py          # Data models
├── config/
│   └── gamification_config.py   # Levels, badges, config
├── services/
│   └── gamification_service.py  # Core business logic
├── gamification_routes.py       # API endpoints
├── tests/
│   └── test_gamification_service.py  # Tests
└── migrations/
    └── 001_gamification_tables.sql  # Schema

GAMIFICATION_SYSTEM.md            # Full documentation
GAMIFICATION_QUICKSTART.md        # This file
```

## Support

For issues or questions:
1. Check `GAMIFICATION_SYSTEM.md` for detailed info
2. Review test examples in `test_gamification_service.py`
3. Check API response status codes and error messages
