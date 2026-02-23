# MarketGPS Gamification System

Complete gamification system for MarketGPS that encourages daily engagement through points, levels, badges, streaks, and objectives.

## Architecture Overview

The gamification system consists of:

- **Backend Service**: `services/gamification_service.py` - Core business logic
- **Data Models**: `models/gamification.py` - Data structures for all gamification entities
- **Configuration**: `config/gamification_config.py` - Levels, badges, objectives, and settings
- **API Routes**: `gamification_routes.py` - RESTful endpoints
- **Database**: SQLite tables with proper schema and indexes
- **Tests**: `tests/test_gamification_service.py` - Comprehensive test coverage

## Key Components

### 1. Points System

Users earn points for various actions:

```python
POINTS_PER_ACTION = {
    "login": 5,
    "view_asset": 2,
    "analyze": 10,
    "create_alert": 5,
    "add_watchlist": 3,
    "read_news": 2,
    "run_backtest": 20,
    "view_portfolio": 3,
    "view_morning_brief": 5,
    "share_analysis": 15,
    "subscribe_pro": 100,
}
```

**Streak Bonus Multipliers:**
- 3 days: +10% bonus
- 7 days: +25% bonus
- 14 days: +50% bonus
- 30 days: +100% bonus (double points)

Daily cap: 200 points/day to prevent abuse

### 2. Levels System

10 levels from "Curious Beginner" to "Wall Street Titan":

| Level | Name | Points Required | Max Points | Perks |
|-------|------|-----------------|------------|-------|
| 1 | Curious Beginner | 0 | 100 | basic_features |
| 2 | Novice Investor | 100 | 300 | watchlist_alerts, daily_alerts |
| 3 | Junior Analyst | 300 | 600 | advanced_analysis, custom_indicators |
| 4 | Savvy Trader | 600 | 1000 | backtesting, strategy_templates |
| 5 | Financial Expert | 1000 | 1500 | ai_insights, portfolio_optimization |
| 6 | Confirmed Strategist | 1500 | 2500 | multi_account, api_access |
| 7 | Market Master | 2500 | 4000 | vip_support, premium_news |
| 8 | Stock Legend | 4000 | 6000 | early_features, custom_alerts |
| 9 | Finance Guru | 6000 | 10000 | unlimited_analyses, beta_features |
| 10 | Wall Street Titan | 10000+ | ∞ | elite_status, private_concierge |

### 3. Badge System

Over 30 badges across 6 categories:

#### Explorer Badges 🔍
- **First Step** (👣) - Complete first login
- **Explorer** (🔍) - View 10 assets
- **Globe Trotter** (🌍) - View 50 assets
- **Market Navigator** (🗺️) - View 500 assets

#### Analyst Badges 📊
- **First Analysis** (📊) - Complete first analysis
- **Analytical Mind** (🧠) - Analyze 10 assets
- **Pro Analyst** (🎯) - Analyze 100 assets
- **Master Analyst** (🏆) - Analyze 500 assets
- **News Junkie** (📰) - Read 50 news articles

#### Investor Badges 💼
- **Watcher** (👀) - Add first watchlist item
- **Portfolio Builder** (📁) - Have 10 watchlist items
- **Diversified** (🎨) - Track 5 different sectors
- **Alert Master** (🔔) - Create 10 alerts
- **Backtester** (⚙️) - Run first backtest

#### Social Badges 🤝
- **Sharer** (🤝) - Share first analysis
- **Community Helper** (💪) - Share 10 analyses

#### Streak Badges 🔥
- **Regular** (🔥) - 3-day streak
- **Dedicated** (⚡) - 7-day streak
- **Consistent** (💎) - 14-day streak
- **Devoted** (👑) - 30-day streak
- **Unstoppable** (⭐) - 100-day streak

#### Milestone Badges 🎯
- **Rising Star** (⭐) - Reach level 5
- **Legendary** (👑) - Reach level 10
- **Pro Member** (💎) - Upgrade to Pro
- **Point Collector** (💰) - Earn 1000 total points

### 4. Streaks

Users maintain engagement streaks by taking at least one action per day.

- **Current Streak**: Days of consecutive engagement
- **Longest Streak**: Personal best streak
- **Multiplier Bonus**: Increases point earnings based on streak length

Streaks reset at UTC 00:00 if user doesn't perform any action.

### 5. Objectives/Quests

#### Weekly Objectives (5 random per week)
- Portfolio Check - View portfolio 3 times
- Analysis Spree - Analyze 5 assets
- Alert Creator - Create 2 alerts
- News Digest - Read 10 articles
- Morning Routine - Check morning brief 5 times
- Backtest Champion - Run 1 backtest
- Watchlist Manager - Add 5 assets to watchlist
- Explorer - View 20 assets
- Sharing is Caring - Share 2 analyses
- Consistency King - Log in 7 days

#### Daily Objectives (3 random per day)
- Daily Login - Log in today
- Quick Check - View 3 assets
- One Analysis - Analyze 1 asset
- News Update - Read 2 articles

Objectives award points when completed and reset on schedule.

## API Endpoints

### Progress

```http
GET /api/gamification/progress
Response: {
  "user_id": "string",
  "total_points": number,
  "current_level": number,
  "level_name": "string",
  "current_streak": number,
  "longest_streak": number,
  "badges_earned_count": number,
  "last_activity_date": "ISO datetime"
}
```

```http
GET /api/gamification/stats
Response: {
  "total_points": number,
  "current_level": number,
  "level_name": "string",
  "current_streak": number,
  "longest_streak": number,
  "badges_earned": number,
  "objectives_completed": number,
  "points_7_days": number,
  "points_30_days": number,
  "avg_daily_points": number,
  "rank": number,
  "rank_percentile": number,
  "account_age_days": number
}
```

### Actions

```http
POST /api/gamification/action
Body: {
  "action": "analyze",
  "metadata": {"asset_id": "AAPL", "score": 85}
}
Response: {
  "success": true,
  "action": "string",
  "current_points": number,
  "current_level": number,
  "current_streak": number,
  "message": "string"
}
```

```http
POST /api/gamification/award-points
Body: {
  "points": 50,
  "reason": "Manual award"
}
```

### Badges

```http
GET /api/gamification/badges
Response: {
  "earned": [
    {
      "id": "badge_id",
      "name": "Badge Name",
      "description": "Description",
      "icon": "🏆",
      "category": "milestone",
      "points_reward": 100,
      "rarity": "legendary",
      "earned_at": "ISO datetime"
    }
  ],
  "available": [
    {
      "id": "badge_id",
      "name": "Badge Name",
      "description": "Description",
      "icon": "🏆",
      "category": "milestone",
      "points_reward": 100,
      "rarity": "epic",
      "progress": {
        "current": 50,
        "target": 100,
        "percentage": 50
      }
    }
  ]
}
```

```http
GET /api/gamification/badges/earned
GET /api/gamification/badges/available
```

### Objectives

```http
GET /api/gamification/objectives?objective_type=all|daily|weekly
Response: [
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "action": "string",
    "target": number,
    "current": number,
    "points_reward": number,
    "objective_type": "weekly|daily",
    "expires_at": "ISO datetime",
    "progress_percentage": number,
    "completed": boolean
  }
]
```

```http
GET /api/gamification/objectives/daily
GET /api/gamification/objectives/weekly
POST /api/gamification/objectives/refresh-weekly
```

### Leaderboards

```http
GET /api/gamification/leaderboard?period=weekly|monthly|all-time&limit=100
Response: [
  {
    "rank": number,
    "user_id": "string",
    "total_points": number,
    "current_level": number,
    "level_name": "string",
    "current_streak": number,
    "badges_count": number
  }
]
```

```http
GET /api/gamification/leaderboard/weekly
GET /api/gamification/leaderboard/monthly
GET /api/gamification/leaderboard/all-time
GET /api/gamification/leaderboard/rank?period=weekly
```

### Initialization

```http
POST /api/gamification/initialize
Response: {
  "success": true,
  "initialized": boolean,
  "message": "string"
}
```

## Integration with MarketGPS

### Automatic Action Tracking

When users perform actions in MarketGPS, record them:

```python
from services.gamification_service import GamificationService

gamification = GamificationService()

# When user analyzes an asset
gamification.record_action(
    user_id="user_123",
    action="analyze",
    metadata={"asset_id": "AAPL", "score": 85}
)

# When user views asset
gamification.record_action(
    user_id="user_123",
    action="view_asset",
    metadata={"asset_id": "AAPL"}
)

# When user creates alert
gamification.record_action(
    user_id="user_123",
    action="create_alert",
    metadata={"asset_id": "AAPL", "price_target": 150}
)
```

### Middleware for Automatic Tracking

Create middleware that automatically tracks relevant actions:

```python
# In main.py or middleware
@app.middleware("http")
async def track_engagement(request: Request, call_next):
    response = await call_next(request)

    # Track based on endpoint
    # This is automatic and transparent to users

    return response
```

## Database Schema

Four main tables:

### user_gamification
Stores progress for each user:
- user_id (PRIMARY KEY)
- total_points
- current_level
- current_streak
- longest_streak
- last_activity_date
- created_at, updated_at

### user_badges
Tracks earned badges:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- badge_id
- earned_at
- UNIQUE(user_id, badge_id)

### user_objectives
Stores active and completed objectives:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- objective_type (daily|weekly|monthly|special)
- title, description, action
- target, current
- points_reward
- expires_at
- completed_at
- created_at

### user_actions
Audit log of all actions:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY)
- action
- metadata_json
- points_earned
- created_at

All tables have proper indexes for performance.

## Configuration

Edit `config/gamification_config.py` to customize:

- **LEVELS**: Change point requirements, names, perks
- **BADGES**: Add/remove badges or change conditions
- **WEEKLY_OBJECTIVES_POOL**: Change weekly quests
- **DAILY_OBJECTIVES_POOL**: Change daily quests
- **ENGAGEMENT_SETTINGS**: Adjust streaks, daily caps, notifications

## Usage Examples

### Initialize Gamification for User

```python
gamification = GamificationService()
gamification.initialize_user("user_123")
```

### Record Action and Auto-Award Points

```python
# Points are awarded automatically based on action type
gamification.record_action("user_123", "analyze")
```

### Check for New Badges

```python
new_badges = gamification.check_badges("user_123")
if new_badges:
    # Notify user of new badges
    notify_user(user_id, f"Congratulations! Earned {len(new_badges)} badges!")
```

### Get User Progress

```python
progress = gamification.get_user_progress("user_123")
print(f"User level: {progress.current_level}")
print(f"Points: {progress.total_points}")
print(f"Streak: {progress.current_streak} days")
```

### Get Leaderboard

```python
leaderboard = gamification.get_leaderboard("weekly", limit=100)
for entry in leaderboard:
    print(f"#{entry['rank']}: {entry['user_id']} - {entry['total_points']} pts")
```

### Get Objectives

```python
daily_objectives = gamification.get_objectives("user_123", "daily")
weekly_objectives = gamification.get_objectives("user_123", "weekly")
```

## Frontend Widget

A compact gamification widget for header/sidebar:

```html
<div class="gamification-widget">
  <div class="level-badge">
    <span class="level-number">5</span>
    <span class="level-name">Financial Expert</span>
  </div>

  <div class="progress-bar">
    <div class="progress-fill" style="width: 60%"></div>
    <span class="progress-text">600 / 1000 points to next level</span>
  </div>

  <div class="streak">
    <span class="streak-icon">🔥</span>
    <span class="streak-count">7 days</span>
  </div>

  <div class="badges">
    <span class="badge earned" title="Pro Analyst">🎯</span>
    <span class="badge earned" title="Devoted">👑</span>
    <span class="badge available" title="Level 10 - 20% towards">⭐</span>
  </div>
</div>
```

## Testing

Run tests with:

```bash
pytest backend/tests/test_gamification_service.py -v
```

Tests cover:
- Points and levels
- Badge unlocking
- Streaks
- Objectives
- Leaderboards
- Statistics

## Future Enhancements

1. **Social Features**
   - Challenge friends
   - Team competitions
   - Leaderboard filters (friends, region, sector)

2. **Seasonal Events**
   - Limited-time special objectives
   - Event-specific badges
   - Seasonal leaderboards

3. **Daily/Weekly Rewards**
   - Login streaks trigger rewards
   - Weekly achievement bonuses
   - Level-up prizes

4. **Personalization**
   - Achievement notifications
   - Progress notifications
   - Milestone celebrations

5. **Analytics**
   - User engagement metrics
   - Feature adoption tracking
   - Gamification effectiveness

6. **Monetization**
   - Premium cosmetics
   - Battle pass system
   - Exclusive rewards for Pro members

## Maintenance

### Database Cleanup

Remove expired objectives older than 30 days:

```sql
DELETE FROM user_objectives
WHERE expires_at < datetime('now', '-30 days')
AND completed_at IS NULL
AND objective_type != 'milestone';
```

### Refresh Leaderboards

Leaderboards are computed on-demand, but consider caching for performance:

```python
# Cache leaderboard for 1 hour
cache_key = f"leaderboard:{period}"
if cache_key in cache and cache_age < 3600:
    return cache[cache_key]
```

## Security Considerations

- Points/level changes are logged in user_actions for audit trail
- Badge conditions are verified server-side
- Leaderboard respects privacy (no email/sensitive data shown)
- Daily points cap prevents farming/abuse
- Streak logic requires genuine daily engagement
