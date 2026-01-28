"""
MarketGPS - News Admin & Scraping API Routes

Endpoints admin pour gérer le scraping d'actualités économiques africaines:
- Voir les articles scrapés
- Filtrer par trending/pending/published
- Publier des articles vers l'app
- Rejeter des articles
- Déclencher un scraping manuel
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore
from news_scraper import AfricanNewsScraper, NEWS_SOURCES

logger = logging.getLogger(__name__)

# Initialize
db = SQLiteStore()
scraper = AfricanNewsScraper(db)

# Create router
router = APIRouter(prefix="/news-admin", tags=["News Admin & Scraping"])


# ═══════════════════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════════════════

class PublishRequest(BaseModel):
    article_id: str
    notes: Optional[str] = ""


class RejectRequest(BaseModel):
    article_id: str
    reason: Optional[str] = ""


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
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/articles")
async def list_scraped_articles(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    status: Optional[str] = Query(None, description="Filter: pending, published, rejected"),
    trending: bool = Query(False, description="Only trending articles (100+ interactions)"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_interactions: int = Query(0, description="Minimum interactions"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List scraped news articles with filters.
    """
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='news_articles'
            """)
            if not cursor.fetchone():
                return {"articles": [], "total": 0, "limit": limit, "offset": offset}

            query = "SELECT * FROM news_articles WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if trending:
                query += " AND total_interactions >= 100"

            if source:
                query += " AND source_name LIKE ?"
                params.append(f"%{source}%")

            if category:
                query += " AND category = ?"
                params.append(category)

            if min_interactions > 0:
                query += " AND total_interactions >= ?"
                params.append(min_interactions)

            query += " ORDER BY total_interactions DESC, scraped_at DESC"
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]

            # Get total count
            count_query = "SELECT COUNT(*) FROM news_articles WHERE 1=1"
            count_params = []

            if status:
                count_query += " AND status = ?"
                count_params.append(status)
            if trending:
                count_query += " AND total_interactions >= 100"
            if source:
                count_query += " AND source_name LIKE ?"
                count_params.append(f"%{source}%")
            if category:
                count_query += " AND category = ?"
                count_params.append(category)
            if min_interactions > 0:
                count_query += " AND total_interactions >= ?"
                count_params.append(min_interactions)

            total = conn.execute(count_query, count_params).fetchone()[0]

        return {
            "articles": articles,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error listing articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}")
async def get_scraped_article(
    article_id: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Get single scraped article details."""
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM news_articles WHERE id = ?",
                (article_id,)
            )
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            return dict(zip(columns, row))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending")
async def get_trending_articles(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    min_interactions: int = Query(100, description="Minimum interactions"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get trending articles with high engagement."""
    require_admin(admin_key)

    try:
        articles = scraper.get_trending_articles(limit=limit, min_interactions=min_interactions)
        return {"articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error(f"Error getting trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending")
async def get_pending_articles(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(100, ge=1, le=200),
):
    """Get articles pending review."""
    require_admin(admin_key)

    try:
        articles = scraper.get_pending_articles(limit=limit)
        return {"articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error(f"Error getting pending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/published")
async def get_published_articles(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(50, ge=1, le=200),
):
    """Get articles published to app."""
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM news_articles
                WHERE published_to_app = 1
                ORDER BY published_to_app_at DESC
                LIMIT ?
            """, (limit,))
            columns = [desc[0] for desc in cursor.description]
            articles = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return {"articles": articles, "total": len(articles)}

    except Exception as e:
        logger.error(f"Error getting published: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_article(
    request: PublishRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Publish article to app."""
    require_admin(admin_key)

    try:
        success = scraper.publish_article(request.article_id, request.notes or "")
        if success:
            return {"success": True, "message": "Article published to app"}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish article")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject_article(
    request: RejectRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Reject article."""
    require_admin(admin_key)

    try:
        success = scraper.reject_article(request.article_id, request.reason or "")
        if success:
            return {"success": True, "message": "Article rejected"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reject article")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape")
async def trigger_scraping(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    min_interactions: int = Query(50, description="Minimum interactions threshold"),
):
    """Manually trigger news scraping."""
    require_admin(admin_key)

    try:
        logger.info("Starting manual scraping...")
        results = await scraper.run_scraping(min_interactions=min_interactions)

        return {
            "success": True,
            "message": "Scraping completed",
            "results": results,
        }

    except Exception as e:
        logger.error(f"Error triggering scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_news_stats(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """Get news scraping statistics."""
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            stats = {}

            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='news_articles'
            """)
            if not cursor.fetchone():
                return {
                    "total_articles": 0,
                    "pending": 0,
                    "published": 0,
                    "rejected": 0,
                    "trending": 0,
                    "by_category": {},
                    "top_sources": {},
                    "last_scraping": None
                }

            # Total articles
            stats["total_articles"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles"
            ).fetchone()[0] or 0

            # By status
            stats["pending"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE status = 'pending'"
            ).fetchone()[0] or 0

            stats["published"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE published_to_app = 1"
            ).fetchone()[0] or 0

            stats["rejected"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE status = 'rejected'"
            ).fetchone()[0] or 0

            # Trending (100+ interactions)
            stats["trending"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE total_interactions >= 100"
            ).fetchone()[0] or 0

            # By category
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count
                FROM news_articles
                GROUP BY category
                ORDER BY count DESC
            """)
            stats["by_category"] = {row[0]: row[1] for row in cursor.fetchall()}

            # By source
            cursor = conn.execute("""
                SELECT source_name, COUNT(*) as count
                FROM news_articles
                GROUP BY source_name
                ORDER BY count DESC
                LIMIT 10
            """)
            stats["top_sources"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Recent scraping
            cursor = conn.execute("""
                SELECT scraped_at FROM news_articles
                ORDER BY scraped_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            stats["last_scraping"] = row[0] if row else None

        return stats

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def list_sources(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """List all configured news sources."""
    require_admin(admin_key)

    return {"sources": NEWS_SOURCES, "total": len(NEWS_SOURCES)}
