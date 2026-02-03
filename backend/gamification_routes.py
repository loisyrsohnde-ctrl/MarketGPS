"""
MarketGPS - Gamification API Routes
Endpoints for gamification features: progress, badges, objectives, leaderboard
"""

# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List, Dict, Any
from datetime import datetime
from security import get_user_id_from_request
from services.gamification_service import GamificationService
from pydantic import BaseModel

# Initialize service
gamification_service = GamificationService()

# Create router
router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class ProgressResponse(BaseModel):
    """User's gamification progress"""
    user_id: str
    total_points: int
    current_level: int
    level_name: str
    current_streak: int
    longest_streak: int
    badges_earned_count: int
    last_activity_date: Optional[str] = None


class BadgeResponse(BaseModel):
    """Badge information"""
    id: str
    name: str
    description: str
    icon: str
    category: str
    points_reward: int
    rarity: str
    earned_at: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class ObjectiveResponse(BaseModel):
    """Objective information"""
    id: str
    title: str
    description: str
    action: str
    target: int
    current: int
    points_reward: int
    objective_type: str
    expires_at: str
    progress_percentage: int
    completed: bool


class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry"""
    rank: int
    user_id: str
    total_points: int
    current_level: int
    level_name: str
    current_streak: int
    badges_count: int


class GamificationStatsResponse(BaseModel):
    """Complete gamification statistics"""
    total_points: int
    current_level: int
    level_name: str
    current_streak: int
    longest_streak: int
    badges_earned: int
    objectives_completed: int
    points_7_days: int
    points_30_days: int
    avg_daily_points: float
    rank: Optional[int] = None
    rank_percentile: float = 0.0
    account_age_days: int


class RecordActionRequest(BaseModel):
    """Request to record an action"""
    action: str
    metadata: Optional[Dict[str, Any]] = None


class AwardPointsRequest(BaseModel):
    """Request to award points"""
    points: int
    reason: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def _get_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from authorization header (JWT) with dev fallback."""
    return get_user_id_from_request(authorization, fallback_user_id="default_user")


def _ensure_user_initialized(user_id: str):
    """Ensure user is initialized in gamification system"""
    progress = gamification_service.get_user_progress(user_id)
    if not progress:
        gamification_service.initialize_user(user_id)


# ═══════════════════════════════════════════════════════════════════════════
# PROGRESS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/progress", response_model=ProgressResponse)
async def get_progress(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """
    Get user's current gamification progress.

    Returns:
        User progress including points, level, streak, and badges
    """
    try:
        _ensure_user_initialized(user_id)
        progress = gamification_service.get_user_progress(user_id)

        if not progress:
            raise HTTPException(status_code=404, detail="User progress not found")

        level_config = gamification_service.levels_map.get(progress.current_level, {})

        return ProgressResponse(
            user_id=user_id,
            total_points=progress.total_points,
            current_level=progress.current_level,
            level_name=level_config.get("name", "Unknown"),
            current_streak=progress.current_streak,
            longest_streak=progress.longest_streak,
            badges_earned_count=len(progress.badges_earned),
            last_activity_date=progress.last_activity_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=GamificationStatsResponse)
async def get_stats(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """
    Get comprehensive gamification statistics for user.

    Returns:
        Detailed stats including points earned in different periods, rank, etc.
    """
    try:
        _ensure_user_initialized(user_id)
        stats = gamification_service.get_gamification_stats(user_id)

        if not stats:
            raise HTTPException(status_code=404, detail="User stats not found")

        return GamificationStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
async def record_action(
    request: RecordActionRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header)
):
    """
    Record a user action for gamification tracking.

    Automatically:
    - Awards points if configured for the action
    - Updates streak
    - Checks for badge unlocks
    - Updates objective progress

    Args:
        request: Action details (action type and optional metadata)

    Returns:
        Summary of rewards earned
    """
    try:
        _ensure_user_initialized(user_id)

        # Record the action
        gamification_service.record_action(
            user_id,
            request.action,
            request.metadata or {}
        )

        # Get updated progress
        progress = gamification_service.get_user_progress(user_id)

        return {
            "success": True,
            "action": request.action,
            "current_points": progress.total_points,
            "current_level": progress.current_level,
            "current_streak": progress.current_streak,
            "message": f"Action '{request.action}' recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/award-points")
async def award_points_endpoint(
    request: AwardPointsRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header)
):
    """
    Award points to a user (admin only in production).

    Args:
        request: Points to award and reason

    Returns:
        Result including level up info and new badges
    """
    try:
        _ensure_user_initialized(user_id)

        result = gamification_service.award_points(
            user_id,
            request.points,
            request.reason or "Manual award"
        )

        return {
            "success": True,
            "points_awarded": result["points_awarded"],
            "new_total": result["new_total"],
            "new_level": result["new_level"],
            "level_up": result["level_up"],
            "new_badges": result["rewards"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# BADGES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/badges", response_model=Dict[str, List[BadgeResponse]])
async def get_badges(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """
    Get all badges with earned and available status.

    Returns:
        Dict with:
        - earned: List of badges the user has earned with timestamps
        - available: List of badges the user can still earn with progress
    """
    try:
        _ensure_user_initialized(user_id)
        badges = gamification_service.get_badges(user_id)

        # Convert to response models
        earned = [BadgeResponse(**badge) for badge in badges["earned"]]
        available = [BadgeResponse(**badge) for badge in badges["available"]]

        return {
            "earned": earned,
            "available": available
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/badges/earned", response_model=List[BadgeResponse])
async def get_earned_badges(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Get only badges the user has earned"""
    try:
        _ensure_user_initialized(user_id)
        badges = gamification_service.get_badges(user_id)
        return [BadgeResponse(**badge) for badge in badges["earned"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/badges/available", response_model=List[BadgeResponse])
async def get_available_badges(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Get only badges the user can still earn"""
    try:
        _ensure_user_initialized(user_id)
        badges = gamification_service.get_badges(user_id)
        return [BadgeResponse(**badge) for badge in badges["available"]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# OBJECTIVES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/objectives", response_model=List[ObjectiveResponse])
async def get_objectives(
    user_id: Optional[str] = Depends(_get_user_id_from_header),
    objective_type: str = "all"
):
    """
    Get active objectives for user.

    Args:
        objective_type: "daily", "weekly", or "all" (default)

    Returns:
        List of active objectives with progress info
    """
    try:
        _ensure_user_initialized(user_id)

        # Generate daily objectives if needed (first call of the day)
        today = datetime.utcnow().date().isoformat()
        last_activity = None
        progress = gamification_service.get_user_progress(user_id)
        if progress and progress.last_activity_date:
            last_activity = progress.last_activity_date[:10]

        if last_activity != today:
            gamification_service.generate_daily_objectives(user_id)

        objectives = gamification_service.get_objectives(user_id, objective_type)
        return [ObjectiveResponse(**obj) for obj in objectives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objectives/daily", response_model=List[ObjectiveResponse])
async def get_daily_objectives(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Get today's daily objectives"""
    try:
        _ensure_user_initialized(user_id)

        # Generate if needed
        today = datetime.utcnow().date().isoformat()
        last_activity = None
        progress = gamification_service.get_user_progress(user_id)
        if progress and progress.last_activity_date:
            last_activity = progress.last_activity_date[:10]

        if last_activity != today:
            gamification_service.generate_daily_objectives(user_id)

        objectives = gamification_service.get_objectives(user_id, "daily")
        return [ObjectiveResponse(**obj) for obj in objectives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objectives/weekly", response_model=List[ObjectiveResponse])
async def get_weekly_objectives(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Get current week's objectives"""
    try:
        _ensure_user_initialized(user_id)
        objectives = gamification_service.get_objectives(user_id, "weekly")
        return [ObjectiveResponse(**obj) for obj in objectives]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/objectives/refresh-weekly")
async def refresh_weekly_objectives(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Manually refresh weekly objectives (admin only in production)"""
    try:
        _ensure_user_initialized(user_id)
        objectives = gamification_service.generate_weekly_objectives(user_id)
        return {
            "success": True,
            "objectives_generated": len(objectives),
            "message": "Weekly objectives refreshed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# LEADERBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/leaderboard", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(
    period: str = "weekly",
    limit: int = 100
):
    """
    Get global leaderboard for specified period.

    Args:
        period: "weekly", "monthly", or "all-time"
        limit: Number of top users to return (max 100)

    Returns:
        Ranked list of top users with stats
    """
    try:
        leaderboard = gamification_service.get_leaderboard(period, min(limit, 100))
        return [LeaderboardEntryResponse(**entry) for entry in leaderboard]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/weekly", response_model=List[LeaderboardEntryResponse])
async def get_weekly_leaderboard(limit: int = 100):
    """Get this week's leaderboard"""
    try:
        leaderboard = gamification_service.get_leaderboard("weekly", min(limit, 100))
        return [LeaderboardEntryResponse(**entry) for entry in leaderboard]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/monthly", response_model=List[LeaderboardEntryResponse])
async def get_monthly_leaderboard(limit: int = 100):
    """Get this month's leaderboard"""
    try:
        leaderboard = gamification_service.get_leaderboard("monthly", min(limit, 100))
        return [LeaderboardEntryResponse(**entry) for entry in leaderboard]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/all-time", response_model=List[LeaderboardEntryResponse])
async def get_all_time_leaderboard(limit: int = 100):
    """Get all-time leaderboard"""
    try:
        leaderboard = gamification_service.get_leaderboard("all-time", min(limit, 100))
        return [LeaderboardEntryResponse(**entry) for entry in leaderboard]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/rank")
async def get_user_rank(
    period: str = "weekly",
    user_id: Optional[str] = Depends(_get_user_id_from_header)
):
    """
    Get user's rank and percentile in leaderboard.

    Args:
        period: "weekly", "monthly", or "all-time"
        user_id: User ID (from header)

    Returns:
        User's rank, percentile, and stats
    """
    try:
        _ensure_user_initialized(user_id)
        rank_info = gamification_service.get_user_rank(user_id, period)

        return {
            "success": True,
            "period": period,
            **rank_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/initialize")
async def initialize_gamification(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """Initialize gamification system for user (if not already initialized)"""
    try:
        progress = gamification_service.get_user_progress(user_id)

        if progress and progress.total_points > 0:
            return {
                "success": True,
                "initialized": False,
                "message": "User already initialized"
            }

        gamification_service.initialize_user(user_id)

        return {
            "success": True,
            "initialized": True,
            "message": "Gamification initialized for user"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
