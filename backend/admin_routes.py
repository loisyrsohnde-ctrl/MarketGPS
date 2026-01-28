"""
MarketGPS - Admin Dashboard API Routes (READ-ONLY)

Ce module fournit des endpoints en LECTURE SEULE pour surveiller :
- Utilisateurs inscrits (Supabase)
- Abonnements actifs (Stripe/DB)
- Activité utilisateur
- Feedbacks reçus

IMPORTANT: Ce module est 100% READ-ONLY et ne modifie RIEN dans le système.
Il se connecte aux sources de données existantes sans les affecter.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
import httpx

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# Initialize SQLite store (READ-ONLY usage)
db = SQLiteStore()

# Create router with /admin prefix
router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# Supabase configuration (for reading users)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


# ═══════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════

class UserSummary(BaseModel):
    id: str
    email: str
    created_at: Optional[str]
    last_sign_in: Optional[str]
    is_pro: bool
    plan: Optional[str]


class SubscriptionSummary(BaseModel):
    user_id: str
    email: Optional[str]
    plan: str
    status: str
    created_at: Optional[str]
    current_period_end: Optional[str]


class DashboardStats(BaseModel):
    total_users: int
    pro_users: int
    free_users: int
    new_users_today: int
    new_users_week: int
    active_subscriptions: int
    total_feedbacks: int
    feedbacks_today: int


class FeedbackSummary(BaseModel):
    id: str
    type: str
    subject: Optional[str]
    message: str
    user_email: Optional[str]
    rating: Optional[int]
    platform: Optional[str]
    status: str
    created_at: str


# ═══════════════════════════════════════════════════════════════════════════
# Admin Key Verification
# ═══════════════════════════════════════════════════════════════════════════

def verify_admin(admin_key: Optional[str]) -> bool:
    """Verify admin access key."""
    expected = os.environ.get("ADMIN_KEY", "marketgps-admin-2024")
    return admin_key == expected


def require_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Dependency to require admin access."""
    if not verify_admin(admin_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Supabase Integration (READ-ONLY)
# ═══════════════════════════════════════════════════════════════════════════

async def get_supabase_users() -> List[Dict[str, Any]]:
    """
    Fetch users from Supabase Auth (READ-ONLY).
    Uses the service role key to list all users.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("Supabase credentials not configured for admin")
        return []

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/auth/v1/admin/users",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "apikey": SUPABASE_SERVICE_KEY,
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("users", [])
            else:
                logger.error(f"Supabase users fetch failed: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Error fetching Supabase users: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Dashboard Endpoints (ALL READ-ONLY)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get overview statistics for the admin dashboard.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get Supabase users
        supabase_users = await get_supabase_users()
        total_users = len(supabase_users)

        # Calculate date thresholds
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        # Count new users
        new_users_today = 0
        new_users_week = 0
        for user in supabase_users:
            created = user.get("created_at", "")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created_dt.replace(tzinfo=None) >= today_start:
                        new_users_today += 1
                    if created_dt.replace(tzinfo=None) >= week_ago:
                        new_users_week += 1
                except:
                    pass

        # Get subscription stats from local DB
        pro_users = 0
        active_subscriptions = 0

        with db._get_conn() as conn:
            # Check subscriptions table
            try:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM subscriptions WHERE status = 'active'"
                )
                active_subscriptions = cursor.fetchone()[0] or 0
                pro_users = active_subscriptions
            except:
                pass

            # Check user_entitlements table
            try:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM user_entitlements WHERE plan != 'FREE' AND status = 'active'"
                )
                entitlement_pros = cursor.fetchone()[0] or 0
                if entitlement_pros > pro_users:
                    pro_users = entitlement_pros
            except:
                pass

            # Feedback stats
            total_feedbacks = 0
            feedbacks_today = 0
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM feedback")
                total_feedbacks = cursor.fetchone()[0] or 0

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM feedback WHERE date(created_at) = date('now')"
                )
                feedbacks_today = cursor.fetchone()[0] or 0
            except:
                pass

        free_users = total_users - pro_users if total_users > pro_users else 0

        return DashboardStats(
            total_users=total_users,
            pro_users=pro_users,
            free_users=free_users,
            new_users_today=new_users_today,
            new_users_week=new_users_week,
            active_subscriptions=active_subscriptions,
            total_feedbacks=total_feedbacks,
            feedbacks_today=feedbacks_today,
        )

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all users with their subscription status.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        supabase_users = await get_supabase_users()

        # Get subscription data from local DB
        subscriptions_map = {}
        with db._get_conn() as conn:
            try:
                cursor = conn.execute("SELECT user_id, plan, status FROM subscriptions")
                for row in cursor.fetchall():
                    subscriptions_map[row[0]] = {"plan": row[1], "status": row[2]}
            except:
                pass

            try:
                cursor = conn.execute("SELECT user_id, plan, status FROM user_entitlements")
                for row in cursor.fetchall():
                    if row[0] not in subscriptions_map:
                        subscriptions_map[row[0]] = {"plan": row[1], "status": row[2]}
            except:
                pass

        # Combine data
        users = []
        for user in supabase_users[offset:offset + limit]:
            user_id = user.get("id", "")
            sub_data = subscriptions_map.get(user_id, {})
            plan = sub_data.get("plan", "FREE")
            is_pro = plan and plan.upper() not in ("FREE", "")

            users.append(UserSummary(
                id=user_id,
                email=user.get("email", ""),
                created_at=user.get("created_at"),
                last_sign_in=user.get("last_sign_in_at"),
                is_pro=is_pro,
                plan=plan,
            ))

        return users

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscriptions", response_model=List[SubscriptionSummary])
async def list_subscriptions(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    status: Optional[str] = Query(None, description="Filter by status: active, canceled, etc."),
    limit: int = Query(50, ge=1, le=500),
):
    """
    List all subscriptions from the database.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        subscriptions = []

        with db._get_conn() as conn:
            # Query subscriptions table
            query = "SELECT user_id, plan, status, created_at, current_period_end FROM subscriptions"
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            try:
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    subscriptions.append(SubscriptionSummary(
                        user_id=row[0],
                        email=None,  # We'll enrich this below
                        plan=row[1] or "unknown",
                        status=row[2] or "unknown",
                        created_at=row[3],
                        current_period_end=row[4],
                    ))
            except Exception as e:
                logger.warning(f"subscriptions table query failed: {e}")

            # Also check user_entitlements if subscriptions is empty
            if not subscriptions:
                try:
                    cursor = conn.execute(
                        "SELECT user_id, plan, status, created_at FROM user_entitlements WHERE plan != 'FREE' LIMIT ?",
                        (limit,)
                    )
                    for row in cursor.fetchall():
                        subscriptions.append(SubscriptionSummary(
                            user_id=row[0],
                            email=None,
                            plan=row[1] or "unknown",
                            status=row[2] or "unknown",
                            created_at=row[3],
                            current_period_end=None,
                        ))
                except:
                    pass

        return subscriptions

    except Exception as e:
        logger.error(f"Error listing subscriptions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedbacks", response_model=List[FeedbackSummary])
async def list_feedbacks(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    status: Optional[str] = Query(None, description="Filter by status: new, reviewed, resolved"),
    feedback_type: Optional[str] = Query(None, alias="type", description="Filter by type: bug, feature, general"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    List all feedbacks received.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        feedbacks = []

        with db._get_conn() as conn:
            query = "SELECT id, type, subject, message, user_email, rating, platform, status, created_at FROM feedback WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if feedback_type:
                query += " AND type = ?"
                params.append(feedback_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            try:
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    feedbacks.append(FeedbackSummary(
                        id=row[0],
                        type=row[1] or "general",
                        subject=row[2],
                        message=row[3] or "",
                        user_email=row[4],
                        rating=row[5],
                        platform=row[6],
                        status=row[7] or "new",
                        created_at=row[8] or "",
                    ))
            except Exception as e:
                logger.warning(f"feedback table query failed: {e}")

        return feedbacks

    except Exception as e:
        logger.error(f"Error listing feedbacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_user_activity(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    days: int = Query(7, ge=1, le=30),
):
    """
    Get user activity metrics for the last N days.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get Supabase users and group by creation date
        supabase_users = await get_supabase_users()

        # Calculate daily signups
        daily_signups = {}
        now = datetime.utcnow()

        for i in range(days):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_signups[date] = 0

        for user in supabase_users:
            created = user.get("created_at", "")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    date_str = created_dt.strftime("%Y-%m-%d")
                    if date_str in daily_signups:
                        daily_signups[date_str] += 1
                except:
                    pass

        # Get daily feedback counts
        daily_feedbacks = {}
        with db._get_conn() as conn:
            for i in range(days):
                date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_feedbacks[date] = 0

            try:
                cursor = conn.execute(
                    f"SELECT date(created_at), COUNT(*) FROM feedback WHERE created_at >= date('now', '-{days} days') GROUP BY date(created_at)"
                )
                for row in cursor.fetchall():
                    if row[0] in daily_feedbacks:
                        daily_feedbacks[row[0]] = row[1]
            except:
                pass

        return {
            "period_days": days,
            "daily_signups": daily_signups,
            "daily_feedbacks": daily_feedbacks,
            "total_signups": sum(daily_signups.values()),
            "total_feedbacks": sum(daily_feedbacks.values()),
        }

    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def admin_health_check():
    """
    Health check endpoint for admin dashboard.
    No authentication required.
    """
    return {
        "status": "ok",
        "service": "MarketGPS Admin Dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "supabase_configured": bool(SUPABASE_URL and SUPABASE_SERVICE_KEY),
            "database_connected": True,
        }
    }
