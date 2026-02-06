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
import logging
import asyncio
import sqlite3
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from pydantic import BaseModel


# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

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

            # Total articles in news_articles (processed by LLM)
            stats["total_articles"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles"
            ).fetchone()[0] or 0

            # "En attente" = articles not yet manually approved for app
            # (pipeline sets status='published' but published_to_app=0)
            stats["pending"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE (published_to_app = 0 OR published_to_app IS NULL) AND status != 'rejected'"
            ).fetchone()[0] or 0

            # "Publiés" = articles manually approved for app display
            stats["published"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE published_to_app = 1"
            ).fetchone()[0] or 0

            # "Rejetés" = articles explicitly rejected by admin
            stats["rejected"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE status = 'rejected'"
            ).fetchone()[0] or 0

            # Trending (100+ interactions)
            stats["trending"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE total_interactions >= 100"
            ).fetchone()[0] or 0

            # Raw items pending LLM processing
            try:
                raw_pending = conn.execute(
                    "SELECT COUNT(*) FROM news_raw_items WHERE processed = 0 AND process_error IS NULL"
                ).fetchone()[0] or 0
                stats["raw_pending"] = raw_pending

                raw_total = conn.execute(
                    "SELECT COUNT(*) FROM news_raw_items"
                ).fetchone()[0] or 0
                stats["raw_total"] = raw_total
            except Exception:
                stats["raw_pending"] = 0
                stats["raw_total"] = 0

            # Today's articles
            stats["today"] = conn.execute(
                "SELECT COUNT(*) FROM news_articles WHERE date(created_at) = date('now')"
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

            # Recent scraping / creation
            try:
                cursor = conn.execute("""
                    SELECT scraped_at FROM news_articles
                    ORDER BY scraped_at DESC LIMIT 1
                """)
                row = cursor.fetchone()
                stats["last_scraping"] = row[0] if row else None
            except Exception:
                # Fallback to created_at if scraped_at column doesn't exist
                cursor = conn.execute("""
                    SELECT created_at FROM news_articles
                    ORDER BY created_at DESC LIMIT 1
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


# ═══════════════════════════════════════════════════════════════════════════
# RSS Pipeline Endpoints (Modern Pipeline)
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/pipeline/run")
async def trigger_rss_pipeline(
    background_tasks: BackgroundTasks,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    ingest_limit: Optional[int] = Query(None, description="Limit sources to ingest"),
    publish_limit: int = Query(100, description="Limit articles to publish"),
    sync: bool = Query(False, description="Run synchronously (wait for result)"),
):
    """
    Trigger the modern RSS news pipeline.
    
    This is the recommended pipeline that:
    1. Ingests from 50+ RSS sources
    2. Processes with LLM for French rewriting
    3. Publishes to news_articles table
    
    Use sync=true to wait for result, or false for background execution.
    """
    require_admin(admin_key)
    
    try:
        # Import the pipeline
        from pipeline.news.publish import run_full_pipeline
        
        if sync:
            # Run synchronously
            logger.info("Starting RSS pipeline (sync mode)...")
            result = run_full_pipeline(
                ingest_limit=ingest_limit,
                publish_limit=publish_limit
            )
            return {
                "success": True,
                "mode": "sync",
                "result": result,
            }
        else:
            # Run in background
            def run_pipeline_task():
                try:
                    result = run_full_pipeline(
                        ingest_limit=ingest_limit,
                        publish_limit=publish_limit
                    )
                    logger.info(f"Background pipeline complete: {result}")
                except Exception as e:
                    logger.error(f"Background pipeline failed: {e}")
            
            background_tasks.add_task(run_pipeline_task)
            
            return {
                "success": True,
                "mode": "background",
                "message": "Pipeline started in background. Check /news-admin/pipeline/status for results.",
            }
            
    except ImportError as e:
        logger.error(f"Pipeline import error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Pipeline not available: {str(e)}. Ensure feedparser is installed."
        )
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/ingest")
async def trigger_rss_ingest(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: Optional[int] = Query(None, description="Limit sources to fetch"),
):
    """
    Run only the RSS ingestion step (no LLM processing).
    
    Useful for testing or when you want to ingest without publishing.
    """
    require_admin(admin_key)
    
    try:
        from pipeline.news.ingest_rss import run_ingest
        
        logger.info("Starting RSS ingestion...")
        result = run_ingest(limit=limit)
        
        return {
            "success": True,
            "result": result,
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Ingester not available: {str(e)}")
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/publish")
async def trigger_publish(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(50, description="Limit articles to publish"),
):
    """
    Run only the publish step (process pending raw items).
    
    Processes items already ingested and rewrites them with LLM.
    """
    require_admin(admin_key)
    
    try:
        from pipeline.news.publish import run_publish
        
        logger.info("Starting publish step...")
        result = run_publish(limit=limit)
        
        return {
            "success": True,
            "result": result,
        }
        
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Publisher not available: {str(e)}")
    except Exception as e:
        logger.error(f"Publish error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/status")
async def get_pipeline_status(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get the status of the RSS news pipeline.
    
    Returns:
    - Last run timestamp
    - Success/failure status
    - Number of articles processed
    - Sources status
    """
    require_admin(admin_key)
    
    import json
    from pathlib import Path
    
    try:
        result = {
            "pipeline_type": "rss",
            "scheduler_running": False,
            "last_run": None,
            "last_success": None,
            "sources": {"total": 0, "enabled": 0},
            "raw_items": {"pending": 0, "processed": 0},
            "articles": {"total": 0, "today": 0},
            "llm_provider": None,
        }
        
        # Check metrics file
        metrics_path = Path(__file__).parent.parent / "data" / "news_metrics.json"
        if metrics_path.exists():
            try:
                with open(metrics_path, 'r') as f:
                    metrics = json.load(f)
                    result["last_run"] = metrics.get("last_run")
                    result["last_success"] = metrics.get("last_success")
                    result["history"] = metrics.get("history", [])[:5]
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading metrics file: {e}")
        
        # Check sources registry
        sources_path = Path(__file__).parent.parent / "pipeline" / "news" / "sources_registry.json"
        if sources_path.exists():
            try:
                with open(sources_path, 'r') as f:
                    sources_data = json.load(f)
                    sources = sources_data.get("sources", [])
                    result["sources"]["total"] = len(sources)
                    result["sources"]["enabled"] = len([s for s in sources if s.get("enabled", True)])
            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error reading sources registry: {e}")
        
        # Check database
        with db._get_conn() as conn:
            # Raw items
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM news_raw_items WHERE processed = 0")
                result["raw_items"]["pending"] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM news_raw_items WHERE processed = 1")
                result["raw_items"]["processed"] = cursor.fetchone()[0]
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying raw items: {e}")
            
            # Articles
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM news_articles")
                result["articles"]["total"] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM news_articles WHERE date(created_at) = date('now')")
                result["articles"]["today"] = cursor.fetchone()[0]
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying articles: {e}")
            
            # Sources from DB
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM news_sources WHERE enabled = 1")
                db_enabled = cursor.fetchone()[0]
                if db_enabled > 0:
                    result["sources"]["enabled_in_db"] = db_enabled
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.error(f"Error querying enabled sources in DB: {e}")
        
        # Check LLM availability
        if os.environ.get("OPENAI_API_KEY"):
            result["llm_provider"] = "openai"
        elif os.environ.get("GEMINI_API_KEY"):
            result["llm_provider"] = "gemini"
        else:
            result["llm_provider"] = "none (fallback mode)"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/sources")
async def list_rss_sources(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    region: Optional[str] = Query(None, description="Filter by region: PAN, NORTH, WEST, CENTRAL, EAST, SOUTH"),
):
    """
    List all configured RSS sources from the registry.
    """
    require_admin(admin_key)
    
    import json
    from pathlib import Path
    
    try:
        sources_path = Path(__file__).parent.parent / "pipeline" / "news" / "sources_registry.json"
        
        if not sources_path.exists():
            return {"sources": [], "total": 0, "error": "Registry not found"}
        
        with open(sources_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sources = data.get("sources", [])
        
        # Filter by region if specified
        if region:
            sources = [s for s in sources if s.get("region") == region.upper()]
        
        # Only enabled sources
        enabled_sources = [s for s in sources if s.get("enabled", True)]
        
        # Group by region
        by_region = {}
        for s in enabled_sources:
            r = s.get("region", "OTHER")
            if r not in by_region:
                by_region[r] = []
            by_region[r].append(s["name"])
        
        return {
            "sources": enabled_sources,
            "total": len(enabled_sources),
            "by_region": {k: len(v) for k, v in by_region.items()},
            "regions": data.get("regions", {}),
        }
        
    except Exception as e:
        logger.error(f"Error listing RSS sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-interactions")
async def update_article_interactions(
    background_tasks: BackgroundTasks,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: Optional[int] = Query(None, description="Limit number of articles to update"),
    sync: bool = Query(False, description="Run synchronously (wait for result)"),
):
    """
    Update all articles with estimated interactions.

    This endpoint triggers the InteractionsFetcher to estimate likes, comments,
    shares for all articles based on source reputation, category, country, etc.
    """
    require_admin(admin_key)

    try:
        from datetime import datetime
        from pipeline.news.interactions_fetcher import InteractionsFetcher

        def update_interactions_task():
            """Background task to update interactions."""
            fetcher = InteractionsFetcher()
            updated = 0
            errors = 0

            with db._get_conn() as conn:
                # Ensure columns exist
                try:
                    conn.execute("ALTER TABLE news_articles ADD COLUMN likes INTEGER DEFAULT 0")
                except Exception:
                    pass
                try:
                    conn.execute("ALTER TABLE news_articles ADD COLUMN comments INTEGER DEFAULT 0")
                except Exception:
                    pass
                try:
                    conn.execute("ALTER TABLE news_articles ADD COLUMN shares INTEGER DEFAULT 0")
                except Exception:
                    pass

                # Get articles
                query = """
                    SELECT id, title, source_name, source_url, published_at,
                           category, country, language
                    FROM news_articles
                    ORDER BY published_at DESC
                """
                if limit:
                    query += f" LIMIT {limit}"

                articles = conn.execute(query).fetchall()
                columns = ['id', 'title', 'source_name', 'source_url', 'published_at',
                          'category', 'country', 'language']

                for row in articles:
                    article = dict(zip(columns, row))
                    try:
                        # Parse published_at
                        pub_at = article.get('published_at')
                        if isinstance(pub_at, str):
                            try:
                                pub_dt = datetime.fromisoformat(pub_at.replace("Z", "+00:00"))
                            except Exception:
                                pub_dt = datetime.utcnow()
                        else:
                            pub_dt = datetime.utcnow()

                        # Get interactions
                        metrics = fetcher.get_interactions(
                            url=article.get('source_url') or '',
                            source_name=article.get('source_name') or 'Unknown',
                            title=article.get('title') or '',
                            published_at=pub_dt,
                            category=article.get('category') or 'default',
                            country=article.get('country') or 'default',
                            language=article.get('language') or 'en'
                        )

                        # Update article
                        conn.execute("""
                            UPDATE news_articles
                            SET total_interactions = ?,
                                likes = ?,
                                comments = ?,
                                shares = ?
                            WHERE id = ?
                        """, (
                            metrics.total_interactions,
                            metrics.likes,
                            metrics.comments,
                            metrics.shares,
                            article['id']
                        ))
                        updated += 1

                        if updated % 100 == 0:
                            logger.info(f"Updated {updated} articles...")

                    except Exception as e:
                        logger.error(f"Error updating article {article['id']}: {e}")
                        errors += 1

                conn.commit()

            logger.info(f"Interactions update complete: {updated} updated, {errors} errors")
            return {"updated": updated, "errors": errors}

        if sync:
            result = update_interactions_task()
            return {"success": True, "mode": "sync", "result": result}
        else:
            background_tasks.add_task(update_interactions_task)
            return {
                "success": True,
                "mode": "background",
                "message": f"Updating interactions for {'all' if not limit else limit} articles in background..."
            }

    except Exception as e:
        logger.error(f"Error updating interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
