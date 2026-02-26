"""
MarketGPS - Admin Dashboard Endpoints

Auth check, dashboard stats, user activity, and health check.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query

from .shared import (
    db, logger, SUPABASE_URL, SUPABASE_SERVICE_KEY,
    DashboardStats,
    require_admin, get_supabase_users,
)

router = APIRouter()


# ===================================================================
# Auth Check Endpoint
# ===================================================================

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


# ===================================================================
# Dashboard Endpoints (ALL READ-ONLY)
# ===================================================================

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
            data_warnings.append("Supabase non disponible - donn\u00e9es utilisateurs incompl\u00e8tes")

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

        # -- News & Pipeline stats --
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
            sources_file = Path(__file__).parent.parent.parent / "pipeline" / "news" / "sources_registry.json"
            if sources_file.exists():
                with open(sources_file, 'r') as f:
                    sources_data = json.load(f)
                    enabled_sources = [s for s in sources_data.get("sources", []) if s.get("enabled", True)]
                    sources_active = len(enabled_sources)
        except Exception as e:
            logger.debug(f"Error reading sources registry: {e}")

        # Last pipeline run (from most recent article in database)
        try:
            with db._get_conn() as conn:
                cursor = conn.execute("SELECT MAX(created_at) FROM news_articles")
                result = cursor.fetchone()
                if result and result[0]:
                    last_pipeline_run = result[0]
        except Exception as e:
            logger.debug(f"Error getting last pipeline run: {e}")

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
