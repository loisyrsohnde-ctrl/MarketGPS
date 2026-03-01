"""
MarketGPS - Gamification Configuration
Defines levels, badges, and objectives for the gamification system.
"""

from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# LEVELS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

LEVELS = [
    {
        "level": 1,
        "name": "Curious Beginner",
        "min_points": 0,
        "max_points": 100,
        "perks": ["basic_features"]
    },
    {
        "level": 2,
        "name": "Novice Investor",
        "min_points": 100,
        "max_points": 300,
        "perks": ["watchlist_alerts", "daily_alerts"]
    },
    {
        "level": 3,
        "name": "Junior Analyst",
        "min_points": 300,
        "max_points": 600,
        "perks": ["advanced_analysis", "custom_indicators"]
    },
    {
        "level": 4,
        "name": "Savvy Trader",
        "min_points": 600,
        "max_points": 1000,
        "perks": ["backtesting", "strategy_templates"]
    },
    {
        "level": 5,
        "name": "Financial Expert",
        "min_points": 1000,
        "max_points": 1500,
        "perks": ["ai_insights", "portfolio_optimization"]
    },
    {
        "level": 6,
        "name": "Confirmed Strategist",
        "min_points": 1500,
        "max_points": 2500,
        "perks": ["multi_account", "api_access"]
    },
    {
        "level": 7,
        "name": "Market Master",
        "min_points": 2500,
        "max_points": 4000,
        "perks": ["vip_support", "premium_news"]
    },
    {
        "level": 8,
        "name": "Stock Legend",
        "min_points": 4000,
        "max_points": 6000,
        "perks": ["early_features", "custom_alerts"]
    },
    {
        "level": 9,
        "name": "Finance Guru",
        "min_points": 6000,
        "max_points": 10000,
        "perks": ["unlimited_analyses", "beta_features"]
    },
    {
        "level": 10,
        "name": "Wall Street Titan",
        "min_points": 10000,
        "max_points": None,
        "perks": ["elite_status", "private_concierge", "lifetime_pro"]
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# BADGES CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

BADGES = [
    # ─────────────────────────────────────────────────────────────────────
    # EXPLORER BADGES - Discovery and exploration
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "first_login",
        "name": "First Step",
        "description": "Complete your first login",
        "icon": "👣",
        "category": "explorer",
        "points_reward": 10,
        "condition": {"action": "login", "count": 1},
        "rarity": "common"
    },
    {
        "id": "explorer_10",
        "name": "Explorer",
        "description": "View 10 different assets",
        "icon": "🔍",
        "category": "explorer",
        "points_reward": 25,
        "condition": {"action": "view_asset", "count": 10},
        "rarity": "common"
    },
    {
        "id": "explorer_50",
        "name": "Globe Trotter",
        "description": "Explore 50 different assets",
        "icon": "🌍",
        "category": "explorer",
        "points_reward": 50,
        "condition": {"action": "view_asset", "count": 50},
        "rarity": "rare"
    },
    {
        "id": "explorer_500",
        "name": "Market Navigator",
        "description": "Explore 500 different assets",
        "icon": "🗺️",
        "category": "explorer",
        "points_reward": 150,
        "condition": {"action": "view_asset", "count": 500},
        "rarity": "epic"
    },

    # ─────────────────────────────────────────────────────────────────────
    # ANALYST BADGES - Analysis and research
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "first_analysis",
        "name": "First Analysis",
        "description": "Complete your first asset analysis",
        "icon": "📊",
        "category": "analyst",
        "points_reward": 15,
        "condition": {"action": "analyze", "count": 1},
        "rarity": "common"
    },
    {
        "id": "analyst_10",
        "name": "Analytical Mind",
        "description": "Analyze 10 assets",
        "icon": "🧠",
        "category": "analyst",
        "points_reward": 50,
        "condition": {"action": "analyze", "count": 10},
        "rarity": "common"
    },
    {
        "id": "analyst_100",
        "name": "Pro Analyst",
        "description": "Analyze 100 assets",
        "icon": "🎯",
        "category": "analyst",
        "points_reward": 150,
        "condition": {"action": "analyze", "count": 100},
        "rarity": "epic"
    },
    {
        "id": "analyst_500",
        "name": "Master Analyst",
        "description": "Analyze 500 assets",
        "icon": "🏆",
        "category": "analyst",
        "points_reward": 300,
        "condition": {"action": "analyze", "count": 500},
        "rarity": "legendary"
    },
    {
        "id": "news_reader",
        "name": "News Junkie",
        "description": "Read 50 news articles",
        "icon": "📰",
        "category": "analyst",
        "points_reward": 75,
        "condition": {"action": "read_news", "count": 50},
        "rarity": "rare"
    },

    # ─────────────────────────────────────────────────────────────────────
    # INVESTOR BADGES - Investment activities
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "first_watchlist",
        "name": "Watcher",
        "description": "Add your first asset to watchlist",
        "icon": "👀",
        "category": "investor",
        "points_reward": 10,
        "condition": {"action": "add_watchlist", "count": 1},
        "rarity": "common"
    },
    {
        "id": "watchlist_10",
        "name": "Portfolio Builder",
        "description": "Have 10 assets in watchlist",
        "icon": "📁",
        "category": "investor",
        "points_reward": 40,
        "condition": {"action": "add_watchlist", "count": 10},
        "rarity": "common"
    },
    {
        "id": "diversified",
        "name": "Diversified",
        "description": "Track assets from 5 different sectors",
        "icon": "🎨",
        "category": "investor",
        "points_reward": 75,
        "condition": {"action": "watchlist_sectors", "count": 5},
        "rarity": "rare"
    },
    {
        "id": "alert_master",
        "name": "Alert Master",
        "description": "Create 10 price alerts",
        "icon": "🔔",
        "category": "investor",
        "points_reward": 50,
        "condition": {"action": "create_alert", "count": 10},
        "rarity": "rare"
    },
    {
        "id": "backtester",
        "name": "Backtester",
        "description": "Run your first backtest",
        "icon": "⚙️",
        "category": "investor",
        "points_reward": 40,
        "condition": {"action": "run_backtest", "count": 1},
        "rarity": "rare"
    },

    # ─────────────────────────────────────────────────────────────────────
    # SOCIAL BADGES - Community and sharing
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "first_share",
        "name": "Sharer",
        "description": "Share your first analysis",
        "icon": "🤝",
        "category": "social",
        "points_reward": 20,
        "condition": {"action": "share_analysis", "count": 1},
        "rarity": "common"
    },
    {
        "id": "community_helper",
        "name": "Community Helper",
        "description": "Share 10 analyses",
        "icon": "💪",
        "category": "social",
        "points_reward": 75,
        "condition": {"action": "share_analysis", "count": 10},
        "rarity": "rare"
    },

    # ─────────────────────────────────────────────────────────────────────
    # STREAK BADGES - Consistency and engagement
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "streak_3",
        "name": "Regular",
        "description": "Maintain a 3-day streak",
        "icon": "🔥",
        "category": "streak",
        "points_reward": 30,
        "condition": {"action": "streak", "count": 3},
        "rarity": "common"
    },
    {
        "id": "streak_7",
        "name": "Dedicated",
        "description": "Maintain a 7-day streak",
        "icon": "⚡",
        "category": "streak",
        "points_reward": 75,
        "condition": {"action": "streak", "count": 7},
        "rarity": "rare"
    },
    {
        "id": "streak_14",
        "name": "Consistent",
        "description": "Maintain a 14-day streak",
        "icon": "💎",
        "category": "streak",
        "points_reward": 150,
        "condition": {"action": "streak", "count": 14},
        "rarity": "epic"
    },
    {
        "id": "streak_30",
        "name": "Devoted",
        "description": "Maintain a 30-day streak",
        "icon": "👑",
        "category": "streak",
        "points_reward": 300,
        "condition": {"action": "streak", "count": 30},
        "rarity": "legendary"
    },
    {
        "id": "streak_100",
        "name": "Unstoppable",
        "description": "Maintain a 100-day streak",
        "icon": "⭐",
        "category": "streak",
        "points_reward": 500,
        "condition": {"action": "streak", "count": 100},
        "rarity": "legendary"
    },

    # ─────────────────────────────────────────────────────────────────────
    # MILESTONE BADGES - Major achievements
    # ─────────────────────────────────────────────────────────────────────
    {
        "id": "level_5",
        "name": "Rising Star",
        "description": "Reach level 5",
        "icon": "⭐",
        "category": "milestone",
        "points_reward": 100,
        "condition": {"action": "level_up", "target_level": 5},
        "rarity": "rare"
    },
    {
        "id": "level_10",
        "name": "Legendary",
        "description": "Reach level 10 - Maximum level!",
        "icon": "👑",
        "category": "milestone",
        "points_reward": 500,
        "condition": {"action": "level_up", "target_level": 10},
        "rarity": "legendary"
    },
    {
        "id": "pro_subscriber",
        "name": "Pro Member",
        "description": "Upgrade to Pro subscription",
        "icon": "💎",
        "category": "milestone",
        "points_reward": 200,
        "condition": {"action": "subscribe_pro", "count": 1},
        "rarity": "epic"
    },
    {
        "id": "1000_points",
        "name": "Point Collector",
        "description": "Earn 1000 total points",
        "icon": "💰",
        "category": "milestone",
        "points_reward": 0,  # Awarded automatically
        "condition": {"action": "total_points", "count": 1000},
        "rarity": "rare"
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# WEEKLY OBJECTIVES POOL
# ═══════════════════════════════════════════════════════════════════════════

WEEKLY_OBJECTIVES_POOL = [
    {
        "title": "Portfolio Check",
        "description": "View your portfolio 3 times this week",
        "action": "view_portfolio",
        "target": 3,
        "points_reward": 20
    },
    {
        "title": "Analysis Spree",
        "description": "Analyze 5 different assets",
        "action": "analyze",
        "target": 5,
        "points_reward": 30
    },
    {
        "title": "Alert Creator",
        "description": "Create 2 price alerts",
        "action": "create_alert",
        "target": 2,
        "points_reward": 25
    },
    {
        "title": "News Digest",
        "description": "Read 10 news articles",
        "action": "read_news",
        "target": 10,
        "points_reward": 25
    },
    {
        "title": "Morning Routine",
        "description": "Check the morning brief 5 times",
        "action": "view_morning_brief",
        "target": 5,
        "points_reward": 35
    },
    {
        "title": "Backtest Champion",
        "description": "Run at least 1 backtest",
        "action": "run_backtest",
        "target": 1,
        "points_reward": 40
    },
    {
        "title": "Watchlist Manager",
        "description": "Add 5 assets to watchlist",
        "action": "add_watchlist",
        "target": 5,
        "points_reward": 20
    },
    {
        "title": "Explorer",
        "description": "View 20 different assets",
        "action": "view_asset",
        "target": 20,
        "points_reward": 30
    },
    {
        "title": "Sharing is Caring",
        "description": "Share 2 analyses with others",
        "action": "share_analysis",
        "target": 2,
        "points_reward": 35
    },
    {
        "title": "Consistency King",
        "description": "Log in 7 days this week",
        "action": "login",
        "target": 7,
        "points_reward": 50
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# DAILY OBJECTIVES POOL
# ═══════════════════════════════════════════════════════════════════════════

# Simplified: each objective = 1 trivial action (< 10 seconds)
# This maximizes streak maintenance and daily habit formation

# This objective is ALWAYS included every day
DAILY_OBJECTIVE_MANDATORY = {
    "title": "Consulter 1 score",
    "description": "Consultez le score d'un actif",
    "action": "view_asset",
    "target": 1,
    "points_reward": 5
}

DAILY_OBJECTIVES_POOL = [
    {
        "title": "Connexion du jour",
        "description": "Connectez-vous aujourd'hui",
        "action": "login",
        "target": 1,
        "points_reward": 5
    },
    {
        "title": "Lire une actu",
        "description": "Lisez un article d'actualité",
        "action": "read_news",
        "target": 1,
        "points_reward": 5
    },
    {
        "title": "Morning Brief",
        "description": "Consultez votre briefing du matin",
        "action": "view_brief",
        "target": 1,
        "points_reward": 10
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# LEADERBOARD CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════

LEADERBOARD_CONFIG = {
    "WEEKLY": {
        "label": "This Week",
        "period_days": 7,
        "top_users": 100,
        "min_actions": 2,  # Minimum actions to appear
    },
    "MONTHLY": {
        "label": "This Month",
        "period_days": 30,
        "top_users": 100,
        "min_actions": 5,
    },
    "ALL_TIME": {
        "label": "All Time",
        "period_days": None,
        "top_users": 100,
        "min_actions": 10,
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# ENGAGEMENT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════

ENGAGEMENT_SETTINGS = {
    "STREAK_REQUIRES_DAILY_ACTION": True,  # User must take an action daily to maintain streak
    "STREAK_RESET_HOUR": 0,                 # Hour in UTC when streak resets daily
    "MAX_DAILY_POINTS": 200,                # Safety cap to prevent abuse
    "BONUS_POINTS_ENABLED": True,
    "LEVEL_UP_NOTIFICATIONS": True,
    "BADGE_UNLOCK_NOTIFICATIONS": True,
    "OBJECTIVE_COMPLETION_NOTIFICATIONS": True,
}
