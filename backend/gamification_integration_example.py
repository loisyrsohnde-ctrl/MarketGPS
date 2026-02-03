"""
Gamification Integration Examples
Shows how to integrate gamification tracking into existing MarketGPS endpoints.

These are example implementations - integrate these patterns into your actual route files.
"""

from fastapi import APIRouter, Depends, HTTPException
from services.gamification_service import GamificationService
from typing import Optional
from datetime import datetime
from security import get_user_id_from_request


# Initialize service
gamification = GamificationService()


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 1: Track Asset Viewing
# ═══════════════════════════════════════════════════════════════════════════

def track_asset_view_example(asset_id: str, user_id: str):
    """
    Call this whenever a user views an asset detail page.

    Example from api_routes.py:
    ```python
    @router.get("/api/assets/{asset_id}")
    async def get_asset_detail(asset_id: str, user_id: str = Depends(get_user_id_from_header)):
        asset = fetch_asset(asset_id)

        # Add this line:
        track_asset_view_example(asset_id, user_id)

        return asset
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="view_asset",
        metadata={
            "asset_id": asset_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 2: Track Asset Analysis
# ═══════════════════════════════════════════════════════════════════════════

def track_asset_analysis_example(asset_id: str, score: float, user_id: str):
    """
    Call this when user performs asset analysis.

    Example from api_routes.py:
    ```python
    @router.post("/api/assets/{asset_id}/analyze")
    async def analyze_asset(
        asset_id: str,
        analysis_params: dict,
        user_id: str = Depends(get_user_id_from_header)
    ):
        analysis_result = perform_analysis(asset_id, analysis_params)

        # Add this line:
        track_asset_analysis_example(
            asset_id,
            analysis_result['score'],
            user_id
        )

        return analysis_result
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="analyze",
        metadata={
            "asset_id": asset_id,
            "score": score,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 3: Track Watchlist Addition
# ═══════════════════════════════════════════════════════════════════════════

def track_watchlist_add_example(asset_id: str, sector: str, user_id: str):
    """
    Call this when user adds asset to watchlist.

    Example from api_routes.py:
    ```python
    @router.post("/api/watchlist")
    async def add_to_watchlist(
        asset_id: str,
        user_id: str = Depends(get_user_id_from_header)
    ):
        asset = get_asset(asset_id)
        add_to_watchlist_db(user_id, asset_id)

        # Add this line:
        track_watchlist_add_example(asset_id, asset['sector'], user_id)

        return {"success": True, "asset": asset}
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="add_watchlist",
        metadata={
            "asset_id": asset_id,
            "sector": sector,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 4: Track Alert Creation
# ═══════════════════════════════════════════════════════════════════════════

def track_alert_creation_example(asset_id: str, alert_type: str, user_id: str):
    """
    Call this when user creates a price alert.

    Example from alert_routes.py:
    ```python
    @router.post("/api/alerts")
    async def create_alert(
        alert_config: AlertConfig,
        user_id: str = Depends(get_user_id_from_header)
    ):
        alert = save_alert(user_id, alert_config)

        # Add this line:
        track_alert_creation_example(
            alert_config.asset_id,
            alert_config.alert_type,
            user_id
        )

        return alert
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="create_alert",
        metadata={
            "asset_id": asset_id,
            "alert_type": alert_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 5: Track News Reading
# ═══════════════════════════════════════════════════════════════════════════

def track_news_read_example(news_id: str, source: str, user_id: str):
    """
    Call this when user reads a news article.

    Example from news_routes.py:
    ```python
    @router.get("/api/news/{news_id}")
    async def get_news(
        news_id: str,
        user_id: str = Depends(get_user_id_from_header)
    ):
        news = fetch_news(news_id)

        # Add this line:
        track_news_read_example(news_id, news['source'], user_id)

        return news
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="read_news",
        metadata={
            "news_id": news_id,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 6: Track Backtest Execution
# ═══════════════════════════════════════════════════════════════════════════

def track_backtest_example(strategy_id: str, result: dict, user_id: str):
    """
    Call this when user runs a backtest.

    Example from backtest_routes.py:
    ```python
    @router.post("/api/backtest/run")
    async def run_backtest(
        backtest_params: BacktestParams,
        user_id: str = Depends(get_user_id_from_header)
    ):
        result = execute_backtest(backtest_params)

        # Add this line:
        track_backtest_example(
            backtest_params.strategy_id,
            result,
            user_id
        )

        return result
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="run_backtest",
        metadata={
            "strategy_id": strategy_id,
            "return_pct": result.get('return_pct', 0),
            "sharpe_ratio": result.get('sharpe_ratio', 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 7: Track Portfolio View
# ═══════════════════════════════════════════════════════════════════════════

def track_portfolio_view_example(user_id: str):
    """
    Call this when user views their portfolio.

    Example from portfolio_routes.py:
    ```python
    @router.get("/api/portfolio")
    async def get_portfolio(user_id: str = Depends(get_user_id_from_header)):
        portfolio = fetch_user_portfolio(user_id)

        # Add this line:
        track_portfolio_view_example(user_id)

        return portfolio
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="view_portfolio",
        metadata={
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 8: Track Analysis Sharing
# ═══════════════════════════════════════════════════════════════════════════

def track_analysis_share_example(analysis_id: str, share_method: str, user_id: str):
    """
    Call this when user shares an analysis.

    Example from api_routes.py or custom endpoint:
    ```python
    @router.post("/api/analysis/{analysis_id}/share")
    async def share_analysis(
        analysis_id: str,
        share_request: ShareRequest,
        user_id: str = Depends(get_user_id_from_header)
    ):
        save_share(user_id, analysis_id, share_request.method)

        # Add this line:
        track_analysis_share_example(analysis_id, share_request.method, user_id)

        return {"success": True, "url": share_request.url}
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="share_analysis",
        metadata={
            "analysis_id": analysis_id,
            "share_method": share_method,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 9: Track Pro Subscription
# ═══════════════════════════════════════════════════════════════════════════

def track_pro_subscription_example(subscription_tier: str, user_id: str):
    """
    Call this when user upgrades to Pro.

    Example from billing_routes.py:
    ```python
    @router.post("/api/billing/upgrade-pro")
    async def upgrade_to_pro(
        billing_info: BillingInfo,
        user_id: str = Depends(get_user_id_from_header)
    ):
        subscription = process_subscription(user_id, billing_info)

        # Add this line:
        track_pro_subscription_example(subscription.tier, user_id)

        return subscription
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="subscribe_pro",
        metadata={
            "tier": subscription_tier,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 10: Track Login
# ═══════════════════════════════════════════════════════════════════════════

def track_login_example(user_id: str):
    """
    Call this when user logs in.

    Example from user_routes.py or auth endpoint:
    ```python
    @router.post("/api/auth/login")
    async def login(credentials: LoginCredentials):
        user = authenticate_user(credentials)

        # Add this line:
        track_login_example(user.id)

        return {"token": create_token(user.id), "user": user}
    ```
    """
    gamification.record_action(
        user_id=user_id,
        action="login",
        metadata={
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE 11: Get User Progress for UI Display
# ═══════════════════════════════════════════════════════════════════════════

def get_user_gamification_widget(user_id: str) -> dict:
    """
    Get all gamification data needed for UI widget display.

    Use this to populate a dashboard widget showing:
    - Level and progress bar
    - Streak counter
    - Recent badge achievements
    - Next objectives

    Example usage in frontend route:
    ```python
    @router.get("/api/user/gamification-widget")
    async def get_gamification_widget(user_id: str = Depends(get_user_id_from_header)):
        return get_user_gamification_widget(user_id)
    ```

    Returns:
        {
            "progress": {...},
            "next_objectives": [...],
            "earned_badges": [...],
            "rank_info": {...}
        }
    """
    progress = gamification.get_user_progress(user_id)
    if not progress:
        return {}

    objectives = gamification.get_objectives(user_id, "all")
    next_objectives = objectives[:3]  # Show top 3

    badges = gamification.get_badges(user_id)
    recent_badges = badges["earned"][-5:]  # Show 5 most recent

    rank_info = gamification.get_user_rank(user_id, "weekly")

    return {
        "progress": {
            "level": progress.current_level,
            "points": progress.total_points,
            "streak": progress.current_streak,
            "badges_count": len(progress.badges_earned)
        },
        "next_objectives": next_objectives,
        "recent_badges": recent_badges,
        "rank": rank_info
    }


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY: Actions to Track
# ═══════════════════════════════════════════════════════════════════════════

"""
Quick checklist of where to add tracking:

ASSET VIEWING
- [ ] GET /api/assets/{asset_id} → track_asset_view_example()
- [ ] GET /api/assets (search) → track_asset_view_example() for each viewed

ANALYSIS
- [ ] POST /api/analysis → track_asset_analysis_example()
- [ ] POST /api/assets/{id}/analyze → track_asset_analysis_example()

WATCHLIST
- [ ] POST /api/watchlist → track_watchlist_add_example()
- [ ] PUT /api/watchlist/{id} → track_watchlist_add_example()

ALERTS
- [ ] POST /api/alerts → track_alert_creation_example()

NEWS
- [ ] GET /api/news/{news_id} → track_news_read_example()

BACKTESTING
- [ ] POST /api/backtest → track_backtest_example()

PORTFOLIO
- [ ] GET /api/portfolio → track_portfolio_view_example()
- [ ] GET /api/portfolio/summary → track_portfolio_view_example()

SHARING
- [ ] POST /api/share → track_analysis_share_example()

SUBSCRIPTION
- [ ] POST /api/billing/upgrade → track_pro_subscription_example()

LOGIN
- [ ] POST /api/login → track_login_example()

MORNING BRIEF
- [ ] GET /api/morning-brief → record_action(user_id, "view_morning_brief")
"""

# ═══════════════════════════════════════════════════════════════════════════
# API REFERENCE: Quick Access
# ═══════════════════════════════════════════════════════════════════════════

"""
Gamification API Endpoints - Direct Integration

Get User Progress:
    GET /api/gamification/progress
    → Current level, points, streak, badges

Get Objectives:
    GET /api/gamification/objectives
    → Daily and weekly missions

Get Badges:
    GET /api/gamification/badges
    → Earned badges and progress on unlockable badges

Get Leaderboard:
    GET /api/gamification/leaderboard/weekly
    → Top 100 users this week

Get User Stats:
    GET /api/gamification/stats
    → Comprehensive user engagement metrics

Get User Rank:
    GET /api/gamification/leaderboard/rank?period=weekly
    → User's rank and percentile
"""
