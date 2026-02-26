"""
MarketGPS - Admin Diagnostics Endpoints

Data diagnostics and news pipeline status.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header

from .shared import (
    db, logger,
    require_admin,
)

router = APIRouter()


# ===================================================================
# Data Diagnostics Endpoints (Phase 1 - Stabilisation)
# ===================================================================

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
            # ---------------------------------------------------------
            # Universe Statistics
            # ---------------------------------------------------------
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

            # ---------------------------------------------------------
            # Scores Statistics
            # ---------------------------------------------------------
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

            # ---------------------------------------------------------
            # News Statistics
            # ---------------------------------------------------------
            try:
                # Total articles
                cursor = conn.execute("SELECT COUNT(*) FROM news_articles")
                total_articles = cursor.fetchone()[0]

                # By country (was incorrectly querying non-existent 'region' column)
                cursor = conn.execute("""
                    SELECT country, COUNT(*) as count
                    FROM news_articles
                    WHERE country IS NOT NULL AND country != ''
                    GROUP BY country
                    ORDER BY count DESC
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

                # Daily breakdown (last 7 days) for trend chart
                cursor = conn.execute("""
                    SELECT date(created_at) as day, COUNT(*) as count
                    FROM news_articles
                    WHERE created_at >= date('now', '-7 days')
                    GROUP BY day
                    ORDER BY day
                """)
                daily_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

                # By status for workflow pipeline
                cursor = conn.execute("""
                    SELECT status, COUNT(*) as count
                    FROM news_articles
                    WHERE status IS NOT NULL AND status != ''
                    GROUP BY status
                """)
                by_status = {row[0]: row[1] for row in cursor.fetchall()}

                diagnostics["news"] = {
                    "total_articles": total_articles,
                    "by_region": by_region,
                    "last_article_created": last_created,
                    "last_article_published": last_published,
                    "articles_today": today,
                    "articles_this_week": this_week,
                    "daily_breakdown": daily_breakdown,
                    "by_status": by_status,
                }
            except Exception as e:
                diagnostics["news"] = {"error": str(e), "note": "news_articles table may not exist"}

            # ---------------------------------------------------------
            # Strategies Statistics
            # ---------------------------------------------------------
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

            # ---------------------------------------------------------
            # Watchlist Statistics
            # ---------------------------------------------------------
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
        metrics_file = Path(__file__).parent.parent / "data" / "news_metrics.json"
        history_file = Path(__file__).parent.parent / "data" / "news_scraping_history.json"

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
        sources_file = Path(__file__).parent.parent.parent / "pipeline" / "news" / "sources_registry.json"
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
