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
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
import httpx


# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# Initialize SQLite store (READ-ONLY usage)
db = SQLiteStore()

# Create router with /admin prefix
router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# Supabase configuration (for reading users)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""))
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


# ═══════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════

class UserSummary(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    provider: Optional[str] = None  # email, google, apple, etc.
    email_confirmed: bool = False
    created_at: Optional[str] = None
    last_sign_in: Optional[str] = None
    sign_in_count: int = 0
    is_pro: bool = False
    plan: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_started: Optional[str] = None
    subscription_ends: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = None


class SubscriptionSummary(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    plan: str
    status: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    interval: Optional[str] = None  # month, year
    created_at: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method: Optional[str] = None


class DashboardStats(BaseModel):
    total_users: int
    pro_users: int
    free_users: int
    new_users_today: int
    new_users_week: int
    active_subscriptions: int
    total_feedbacks: int
    feedbacks_today: int
    # News & Pipeline stats
    articles_today: int = 0
    viral_count: int = 0
    scripts_generated: int = 0
    sources_active: int = 0
    last_pipeline_run: Optional[str] = None
    llm_provider: str = "openai"
    data_warnings: List[str] = []


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
# Auth Check Endpoint
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/auth/check")
async def admin_auth_check(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Check if admin key is valid.
    Used by the frontend to verify admin access.
    """
    require_admin(admin_key)
    return {"status": "authorized", "role": "admin"}


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
        data_warnings: List[str] = []

        # Track warning if Supabase is not available
        if not supabase_users and (SUPABASE_URL and SUPABASE_SERVICE_KEY):
            data_warnings.append("Supabase non disponible - données utilisateurs incomplètes")

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
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing user creation date: {e}")

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
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying subscriptions table: {e}")

            # Check user_entitlements table
            try:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM user_entitlements WHERE plan != 'FREE' AND status = 'active'"
                )
                entitlement_pros = cursor.fetchone()[0] or 0
                if entitlement_pros > pro_users:
                    pro_users = entitlement_pros
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying user_entitlements table: {e}")

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
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying feedback count: {e}")

        free_users = total_users - pro_users if total_users > pro_users else 0

        # ── News & Pipeline stats ─────────────────────────────────
        articles_today = 0
        viral_count = 0
        scripts_generated = 0
        sources_active = 0
        last_pipeline_run = None
        llm_provider = os.environ.get("LLM_PROVIDER", "openai")

        with db._get_conn() as conn:
            # Articles scraped today
            try:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM news_articles WHERE date(created_at) = date('now')"
                )
                articles_today = cursor.fetchone()[0] or 0
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error querying news_articles for today count: {e}")

            # Viral articles count (editorial_score >= 70 or virality_score >= 3)
            try:
                cursor = conn.execute(
                    """SELECT COUNT(*) FROM news_articles
                       WHERE editorial_score >= 70 OR virality_score >= 3"""
                )
                viral_count = cursor.fetchone()[0] or 0
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error querying viral count: {e}")

            # Scripts generated (stored in video_scripts table)
            try:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM video_scripts"
                )
                scripts_generated = cursor.fetchone()[0] or 0
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error querying scripts count: {e}")

        # Sources active (from sources registry)
        try:
            import json
            from pathlib import Path
            sources_file = Path(__file__).parent.parent / "pipeline" / "news" / "sources_registry.json"
            if sources_file.exists():
                with open(sources_file, 'r') as f:
                    sources_data = json.load(f)
                    enabled_sources = [s for s in sources_data.get("sources", []) if s.get("enabled", True)]
                    sources_active = len(enabled_sources)
        except Exception as e:
            logger.debug(f"Error reading sources registry: {e}")

        # Last pipeline run (from metrics file)
        try:
            import json
            from pathlib import Path
            metrics_file = Path(__file__).parent / "data" / "news_metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    last_pipeline_run = metrics.get("last_run")
        except Exception as e:
            logger.debug(f"Error reading pipeline metrics: {e}")

        return DashboardStats(
            total_users=total_users,
            pro_users=pro_users,
            free_users=free_users,
            new_users_today=new_users_today,
            new_users_week=new_users_week,
            active_subscriptions=active_subscriptions,
            total_feedbacks=total_feedbacks,
            feedbacks_today=feedbacks_today,
            articles_today=articles_today,
            viral_count=viral_count,
            scripts_generated=scripts_generated,
            sources_active=sources_active,
            last_pipeline_run=last_pipeline_run,
            llm_provider=llm_provider,
            data_warnings=data_warnings,
        )

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[UserSummary])
async def list_users(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    filter: Optional[str] = Query(None, description="Filter: all, pro, free"),
):
    """
    List all users with their full subscription details.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        supabase_users = await get_supabase_users()

        # Get detailed subscription data from local DB
        subscriptions_map = {}
        with db._get_conn() as conn:
            try:
                cursor = conn.execute("""
                    SELECT user_id, plan, status, created_at, current_period_end,
                           stripe_customer_id, stripe_subscription_id, amount, currency
                    FROM subscriptions
                """)
                for row in cursor.fetchall():
                    subscriptions_map[row[0]] = {
                        "plan": row[1],
                        "status": row[2],
                        "subscription_started": row[3],
                        "subscription_ends": row[4],
                        "stripe_customer_id": row[5],
                        "stripe_subscription_id": row[6],
                        "amount": row[7],
                        "currency": row[8],
                    }
            except Exception as e:
                logger.warning(f"Error fetching subscriptions: {e}")

            try:
                cursor = conn.execute("""
                    SELECT user_id, plan, status, created_at
                    FROM user_entitlements
                """)
                for row in cursor.fetchall():
                    if row[0] not in subscriptions_map:
                        subscriptions_map[row[0]] = {
                            "plan": row[1],
                            "status": row[2],
                            "subscription_started": row[3],
                        }
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error fetching user_entitlements: {e}")

        # Combine data
        users = []
        for user in supabase_users:
            user_id = user.get("id", "")
            sub_data = subscriptions_map.get(user_id, {})
            plan = sub_data.get("plan", "FREE")
            is_pro = plan and plan.upper() not in ("FREE", "")

            # Apply filter
            if filter == "pro" and not is_pro:
                continue
            if filter == "free" and is_pro:
                continue

            # Extract user metadata
            user_metadata = user.get("user_metadata", {}) or {}
            app_metadata = user.get("app_metadata", {}) or {}
            identities = user.get("identities", []) or []

            # Determine provider
            provider = "email"
            if identities:
                provider = identities[0].get("provider", "email")

            # Get full name from various possible sources
            full_name = (
                user_metadata.get("full_name") or
                user_metadata.get("name") or
                f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
                None
            )

            users.append(UserSummary(
                id=user_id,
                email=user.get("email", ""),
                full_name=full_name,
                phone=user.get("phone"),
                provider=provider,
                email_confirmed=user.get("email_confirmed_at") is not None,
                created_at=user.get("created_at"),
                last_sign_in=user.get("last_sign_in_at"),
                sign_in_count=app_metadata.get("sign_in_count", 0) if app_metadata else 0,
                is_pro=is_pro,
                plan=plan if plan else "FREE",
                subscription_status=sub_data.get("status"),
                subscription_started=sub_data.get("subscription_started"),
                subscription_ends=sub_data.get("subscription_ends"),
                stripe_customer_id=sub_data.get("stripe_customer_id"),
                amount_paid=sub_data.get("amount"),
                currency=sub_data.get("currency"),
            ))

        # Sort by creation date (newest first)
        users.sort(key=lambda x: x.created_at or "", reverse=True)

        return users[offset:offset + limit]

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
    List all subscriptions with detailed payment information.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get Supabase users for email lookup
        supabase_users = await get_supabase_users()
        users_map = {}
        for user in supabase_users:
            user_id = user.get("id", "")
            user_metadata = user.get("user_metadata", {}) or {}
            full_name = (
                user_metadata.get("full_name") or
                user_metadata.get("name") or
                f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
                None
            )
            users_map[user_id] = {
                "email": user.get("email", ""),
                "full_name": full_name
            }

        subscriptions = []

        with db._get_conn() as conn:
            # Query subscriptions table with all details
            query = """
                SELECT user_id, plan, status, created_at, current_period_start, current_period_end,
                       stripe_customer_id, stripe_subscription_id, amount, currency, interval,
                       cancel_at_period_end, payment_method
                FROM subscriptions
            """
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            try:
                cursor = conn.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                for row in cursor.fetchall():
                    user_id = row[0]
                    user_info = users_map.get(user_id, {})

                    subscriptions.append(SubscriptionSummary(
                        user_id=user_id,
                        email=user_info.get("email"),
                        full_name=user_info.get("full_name"),
                        plan=row[1] or "unknown",
                        status=row[2] or "unknown",
                        created_at=row[3],
                        current_period_start=row[4] if len(row) > 4 else None,
                        current_period_end=row[5] if len(row) > 5 else None,
                        stripe_customer_id=row[6] if len(row) > 6 else None,
                        stripe_subscription_id=row[7] if len(row) > 7 else None,
                        amount=row[8] if len(row) > 8 else None,
                        currency=row[9] if len(row) > 9 else None,
                        interval=row[10] if len(row) > 10 else None,
                        cancel_at_period_end=bool(row[11]) if len(row) > 11 else False,
                        payment_method=row[12] if len(row) > 12 else None,
                    ))
            except Exception as e:
                logger.warning(f"subscriptions table query failed: {e}")
                # Try simpler query
                try:
                    cursor = conn.execute(
                        "SELECT user_id, plan, status, created_at, current_period_end FROM subscriptions ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                    for row in cursor.fetchall():
                        user_id = row[0]
                        user_info = users_map.get(user_id, {})
                        subscriptions.append(SubscriptionSummary(
                            user_id=user_id,
                            email=user_info.get("email"),
                            full_name=user_info.get("full_name"),
                            plan=row[1] or "unknown",
                            status=row[2] or "unknown",
                            created_at=row[3],
                            current_period_end=row[4],
                        ))
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error processing subscription row: {e}")

            # Also check user_entitlements if subscriptions is empty
            if not subscriptions:
                try:
                    cursor = conn.execute(
                        "SELECT user_id, plan, status, created_at FROM user_entitlements WHERE plan != 'FREE' LIMIT ?",
                        (limit,)
                    )
                    for row in cursor.fetchall():
                        user_id = row[0]
                        user_info = users_map.get(user_id, {})
                        subscriptions.append(SubscriptionSummary(
                            user_id=user_id,
                            email=user_info.get("email"),
                            full_name=user_info.get("full_name"),
                            plan=row[1] or "unknown",
                            status=row[2] or "unknown",
                            created_at=row[3],
                        ))
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error processing user_entitlements row: {e}")

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


@router.get("/user/{user_id}")
async def get_user_detail(
    user_id: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get detailed information about a specific user.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        # Get user from Supabase
        supabase_users = await get_supabase_users()
        user = None
        for u in supabase_users:
            if u.get("id") == user_id:
                user = u
                break

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get subscription data
        subscription_data = None
        with db._get_conn() as conn:
            try:
                cursor = conn.execute("""
                    SELECT plan, status, created_at, current_period_start, current_period_end,
                           stripe_customer_id, stripe_subscription_id, amount, currency, interval,
                           cancel_at_period_end, payment_method
                    FROM subscriptions WHERE user_id = ?
                """, (user_id,))
                row = cursor.fetchone()
                if row:
                    subscription_data = {
                        "plan": row[0],
                        "status": row[1],
                        "created_at": row[2],
                        "current_period_start": row[3] if len(row) > 3 else None,
                        "current_period_end": row[4] if len(row) > 4 else None,
                        "stripe_customer_id": row[5] if len(row) > 5 else None,
                        "stripe_subscription_id": row[6] if len(row) > 6 else None,
                        "amount": row[7] if len(row) > 7 else None,
                        "currency": row[8] if len(row) > 8 else None,
                        "interval": row[9] if len(row) > 9 else None,
                        "cancel_at_period_end": bool(row[10]) if len(row) > 10 else False,
                        "payment_method": row[11] if len(row) > 11 else None,
                    }
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error processing subscription data: {e}")

            # Check entitlements if no subscription
            if not subscription_data:
                try:
                    cursor = conn.execute(
                        "SELECT plan, status, created_at FROM user_entitlements WHERE user_id = ?",
                        (user_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        subscription_data = {
                            "plan": row[0],
                            "status": row[1],
                            "created_at": row[2],
                        }
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    logger.error(f"Error querying entitlements: {e}")

        # Extract user metadata
        user_metadata = user.get("user_metadata", {}) or {}
        app_metadata = user.get("app_metadata", {}) or {}
        identities = user.get("identities", []) or []

        # Determine provider
        provider = "email"
        if identities:
            provider = identities[0].get("provider", "email")

        # Get full name
        full_name = (
            user_metadata.get("full_name") or
            user_metadata.get("name") or
            f"{user_metadata.get('first_name', '')} {user_metadata.get('last_name', '')}".strip() or
            None
        )

        return {
            "id": user_id,
            "email": user.get("email", ""),
            "full_name": full_name,
            "phone": user.get("phone"),
            "provider": provider,
            "email_confirmed": user.get("email_confirmed_at") is not None,
            "email_confirmed_at": user.get("email_confirmed_at"),
            "created_at": user.get("created_at"),
            "last_sign_in": user.get("last_sign_in_at"),
            "updated_at": user.get("updated_at"),
            "sign_in_count": app_metadata.get("sign_in_count", 0) if app_metadata else 0,
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
            "identities": [{
                "provider": i.get("provider"),
                "created_at": i.get("created_at"),
                "last_sign_in_at": i.get("last_sign_in_at"),
            } for i in identities],
            "subscription": subscription_data,
            "is_pro": subscription_data and subscription_data.get("plan", "").upper() not in ("FREE", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user detail: {e}")
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
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error processing signup date: {e}")

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
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying daily feedback counts: {e}")

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


# ═══════════════════════════════════════════════════════════════════════════
# Data Diagnostics Endpoints (Phase 1 - Stabilisation)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/diagnostics")
async def get_data_diagnostics(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get comprehensive data diagnostics for troubleshooting.
    READ-ONLY: Shows database health and content statistics.
    
    Returns:
    - Universe counts by scope, type, status
    - Scores counts and freshness
    - News pipeline status
    - Strategy templates status
    """
    require_admin(admin_key)
    
    try:
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "universe": {},
            "scores": {},
            "news": {},
            "strategies": {},
            "watchlist": {},
        }
        
        with db._get_conn() as conn:
            # ─────────────────────────────────────────────────────────────
            # Universe Statistics
            # ─────────────────────────────────────────────────────────────
            try:
                # Total by scope
                cursor = conn.execute("""
                    SELECT market_scope, COUNT(*) as count 
                    FROM universe 
                    GROUP BY market_scope
                """)
                by_scope = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Active by scope
                cursor = conn.execute("""
                    SELECT market_scope, COUNT(*) as count 
                    FROM universe 
                    WHERE active = 1
                    GROUP BY market_scope
                """)
                active_by_scope = {row[0]: row[1] for row in cursor.fetchall()}
                
                # By asset type
                cursor = conn.execute("""
                    SELECT asset_type, COUNT(*) as count 
                    FROM universe 
                    WHERE active = 1
                    GROUP BY asset_type
                """)
                by_type = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Total
                cursor = conn.execute("SELECT COUNT(*) FROM universe")
                total = cursor.fetchone()[0]
                
                diagnostics["universe"] = {
                    "total": total,
                    "by_scope": by_scope,
                    "active_by_scope": active_by_scope,
                    "by_type": by_type,
                }
            except Exception as e:
                diagnostics["universe"] = {"error": str(e)}
            
            # ─────────────────────────────────────────────────────────────
            # Scores Statistics
            # ─────────────────────────────────────────────────────────────
            try:
                # Total scored
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM scores_latest 
                    WHERE score_total IS NOT NULL
                """)
                total_scored = cursor.fetchone()[0]
                
                # Scored by scope (join with universe)
                cursor = conn.execute("""
                    SELECT u.market_scope, COUNT(*) as count
                    FROM scores_latest s
                    JOIN universe u ON s.asset_id = u.asset_id
                    WHERE s.score_total IS NOT NULL
                    GROUP BY u.market_scope
                """)
                scored_by_scope = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Last update
                cursor = conn.execute("""
                    SELECT MAX(updated_at) FROM scores_latest
                """)
                last_update = cursor.fetchone()[0]
                
                # Score distribution
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN score_total >= 70 THEN 1 ELSE 0 END) as high,
                        SUM(CASE WHEN score_total >= 40 AND score_total < 70 THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN score_total < 40 THEN 1 ELSE 0 END) as low
                    FROM scores_latest
                    WHERE score_total IS NOT NULL
                """)
                dist = cursor.fetchone()
                
                diagnostics["scores"] = {
                    "total_scored": total_scored,
                    "by_scope": scored_by_scope,
                    "last_update": last_update,
                    "distribution": {
                        "high_70_plus": dist[0] or 0,
                        "medium_40_69": dist[1] or 0,
                        "low_below_40": dist[2] or 0,
                    }
                }
            except Exception as e:
                diagnostics["scores"] = {"error": str(e)}
            
            # ─────────────────────────────────────────────────────────────
            # News Statistics
            # ─────────────────────────────────────────────────────────────
            try:
                # Total articles
                cursor = conn.execute("SELECT COUNT(*) FROM news_articles")
                total_articles = cursor.fetchone()[0]
                
                # By region
                cursor = conn.execute("""
                    SELECT region, COUNT(*) as count 
                    FROM news_articles 
                    WHERE region IS NOT NULL
                    GROUP BY region
                """)
                by_region = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Latest article
                cursor = conn.execute("""
                    SELECT MAX(created_at), MAX(published_at) FROM news_articles
                """)
                row = cursor.fetchone()
                last_created = row[0]
                last_published = row[1]
                
                # Articles today
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM news_articles 
                    WHERE date(created_at) = date('now')
                """)
                today = cursor.fetchone()[0]
                
                # Articles this week
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM news_articles 
                    WHERE created_at >= date('now', '-7 days')
                """)
                this_week = cursor.fetchone()[0]
                
                diagnostics["news"] = {
                    "total_articles": total_articles,
                    "by_region": by_region,
                    "last_article_created": last_created,
                    "last_article_published": last_published,
                    "articles_today": today,
                    "articles_this_week": this_week,
                }
            except Exception as e:
                diagnostics["news"] = {"error": str(e), "note": "news_articles table may not exist"}
            
            # ─────────────────────────────────────────────────────────────
            # Strategies Statistics
            # ─────────────────────────────────────────────────────────────
            try:
                # Templates
                cursor = conn.execute("SELECT COUNT(*) FROM strategy_templates")
                total_templates = cursor.fetchone()[0]
                
                # User strategies
                cursor = conn.execute("SELECT COUNT(*) FROM user_strategies")
                user_strategies = cursor.fetchone()[0]
                
                diagnostics["strategies"] = {
                    "templates_count": total_templates,
                    "user_strategies_count": user_strategies,
                }
            except Exception as e:
                diagnostics["strategies"] = {"error": str(e)}
            
            # ─────────────────────────────────────────────────────────────
            # Watchlist Statistics
            # ─────────────────────────────────────────────────────────────
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM user_watchlist")
                total = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(DISTINCT user_id) FROM user_watchlist")
                unique_users = cursor.fetchone()[0]
                
                diagnostics["watchlist"] = {
                    "total_items": total,
                    "unique_users": unique_users,
                }
            except Exception as e:
                diagnostics["watchlist"] = {"error": str(e)}
        
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error getting diagnostics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-pipeline-status")
async def get_news_pipeline_status(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get news pipeline scheduler status.
    Shows last run, next scheduled run, and recent history.
    """
    require_admin(admin_key)
    
    import json
    from pathlib import Path
    
    try:
        metrics_file = Path(__file__).parent / "data" / "news_metrics.json"
        history_file = Path(__file__).parent / "data" / "news_scraping_history.json"
        
        result = {
            "scheduler_configured": False,
            "last_run": None,
            "last_success": None,
            "last_result": None,
            "history": [],
            "sources_configured": 0,
        }
        
        # Check metrics file (from pipeline/news/news_scheduler.py)
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                    result["last_run"] = metrics.get("last_run")
                    result["last_success"] = metrics.get("last_success")
                    result["last_result"] = metrics.get("last_result")
                    result["history"] = metrics.get("history", [])[:5]
                    result["scheduler_configured"] = True
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading metrics file: {e}")

        # Check legacy history file (from backend/news_scheduler.py)
        if not result["scheduler_configured"] and history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    if history:
                        result["last_run"] = history[0].get("timestamp")
                        result["last_result"] = history[0]
                        result["history"] = history[:5]
                        result["scheduler_configured"] = True
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading history file: {e}")

        # Check sources registry
        sources_file = Path(__file__).parent.parent / "pipeline" / "news" / "sources_registry.json"
        if sources_file.exists():
            try:
                with open(sources_file, 'r') as f:
                    sources_data = json.load(f)
                    enabled_sources = [s for s in sources_data.get("sources", []) if s.get("enabled", True)]
                    result["sources_configured"] = len(enabled_sources)
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading sources registry: {e}")

        # Calculate time since last run
        if result["last_run"]:
            try:
                last_run_dt = datetime.fromisoformat(result["last_run"].replace("Z", "+00:00"))
                delta = datetime.utcnow() - last_run_dt.replace(tzinfo=None)
                result["minutes_since_last_run"] = int(delta.total_seconds() / 60)
                result["is_stale"] = delta.total_seconds() > 3600  # >1 hour = stale
            except (ValueError, TypeError) as e:
                logger.error(f"Error calculating time since last run: {e}")

        return result
        
    except Exception as e:
        logger.error(f"Error getting news pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# AI QUOTA MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

from ai_quota_service import get_ai_quota_service


class AIQuotaUpdate(BaseModel):
    """Request to update AI quota for a user."""
    user_id: str
    provider: str  # "openai" or "gemini" or "all"
    action: str  # "disable_limit", "enable_limit", "reset", "set_limit"
    new_limit: Optional[int] = None  # Only for "set_limit" action


@router.get("/ai-quotas")
async def list_ai_quotas(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all AI quota records.
    Shows usage statistics for OpenAI and Gemini per user.
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        quotas = quota_service.get_all_quotas(limit=limit, offset=offset)
        
        return {
            "quotas": quotas,
            "count": len(quotas),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error listing AI quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-quotas/exhausted")
async def list_exhausted_quotas(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    List users who have exhausted their AI quotas.
    Useful for identifying users who may need quota renewal.
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        exhausted = quota_service.get_exhausted_users()
        
        return {
            "exhausted_users": exhausted,
            "count": len(exhausted),
        }
    except Exception as e:
        logger.error(f"Error listing exhausted quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-quotas/user/{user_id}")
async def get_user_ai_quotas(
    user_id: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get AI quota information for a specific user.
    Shows OpenAI and Gemini quota status.
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        quotas = quota_service.get_user_quotas(user_id)
        
        return {
            "user_id": user_id,
            "quotas": quotas,
        }
    except Exception as e:
        logger.error(f"Error getting user quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/update")
async def update_ai_quota(
    request: AIQuotaUpdate,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Update AI quota for a user.
    
    Actions:
    - disable_limit: Remove quota limit (unlimited usage)
    - enable_limit: Re-enable quota limit
    - reset: Reset usage counter to 0
    - set_limit: Set a custom limit (requires new_limit parameter)
    
    Provider:
    - openai: ChatGPT/OpenAI quota only
    - gemini: Google Gemini quota only
    - all: Both OpenAI and Gemini
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        
        # Validate provider
        if request.provider not in ["openai", "gemini", "all"]:
            raise HTTPException(status_code=400, detail="Provider must be 'openai', 'gemini', or 'all'")
        
        # Validate action
        valid_actions = ["disable_limit", "enable_limit", "reset", "set_limit"]
        if request.action not in valid_actions:
            raise HTTPException(status_code=400, detail=f"Action must be one of: {valid_actions}")
        
        # Execute action
        providers = ["openai", "gemini"] if request.provider == "all" else [request.provider]
        results = {}
        
        for provider in providers:
            if request.action == "disable_limit":
                quota_service.set_limit_disabled(request.user_id, provider, True)
                results[provider] = "Limite désactivée (illimité)"
                
            elif request.action == "enable_limit":
                quota_service.set_limit_disabled(request.user_id, provider, False)
                results[provider] = "Limite activée"
                
            elif request.action == "reset":
                quota_service.reset_user_quota(request.user_id, provider)
                results[provider] = "Quota réinitialisé à 0"
                
            elif request.action == "set_limit":
                if request.new_limit is None or request.new_limit < 0:
                    raise HTTPException(status_code=400, detail="new_limit is required for set_limit action")
                quota_service.set_user_limit(request.user_id, provider, request.new_limit)
                results[provider] = f"Nouvelle limite: {request.new_limit}"
        
        logger.info(f"AI quota updated for user {request.user_id}: {request.action} on {request.provider}")
        
        return {
            "success": True,
            "user_id": request.user_id,
            "action": request.action,
            "provider": request.provider,
            "results": results,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/disable-limit/{user_id}")
async def disable_user_ai_limit(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Quick endpoint to disable AI quota limit for a user.
    User will have unlimited AI requests.
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        
        if provider == "all":
            quota_service.set_limit_disabled_all(user_id, True)
        else:
            quota_service.set_limit_disabled(user_id, provider, True)
        
        logger.info(f"AI quota limit disabled for user {user_id} on {provider}")
        
        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Limite IA désactivée pour {provider}. L'utilisateur a maintenant un accès illimité.",
        }
    except Exception as e:
        logger.error(f"Error disabling AI limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/enable-limit/{user_id}")
async def enable_user_ai_limit(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Quick endpoint to re-enable AI quota limit for a user.
    User will be subject to normal quota limits (50 requests).
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        
        if provider == "all":
            quota_service.set_limit_disabled_all(user_id, False)
        else:
            quota_service.set_limit_disabled(user_id, provider, False)
        
        logger.info(f"AI quota limit enabled for user {user_id} on {provider}")
        
        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Limite IA activée pour {provider}. L'utilisateur est maintenant soumis aux quotas.",
        }
    except Exception as e:
        logger.error(f"Error enabling AI limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/reset/{user_id}")
async def reset_user_ai_quota(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Reset AI quota usage for a user.
    Sets their usage counter back to 0.
    """
    require_admin(admin_key)
    
    try:
        quota_service = get_ai_quota_service()
        
        if provider == "all":
            quota_service.reset_user_all_quotas(user_id)
        else:
            quota_service.reset_user_quota(user_id, provider)
        
        logger.info(f"AI quota reset for user {user_id} on {provider}")
        
        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Quota IA réinitialisé pour {provider}. L'utilisateur a à nouveau 50 requêtes disponibles.",
        }
    except Exception as e:
        logger.error(f"Error resetting AI quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))
