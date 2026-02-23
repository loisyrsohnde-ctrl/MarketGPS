"""
MarketGPS News Module - FastAPI Routes
Endpoints for news feed, articles, and user saves.
"""

import json
import os
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Header
from pydantic import BaseModel

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from security import get_user_id_from_request

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/news", tags=["News"])

# Database store
db = SQLiteStore()

# Ensure news tables exist on import
db._ensure_news_tables()


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════

class NewsArticleSummary(BaseModel):
    """Article summary for list views."""
    id: int
    slug: str
    title: str
    excerpt: Optional[str]
    tldr: Optional[List[str]]
    tags: Optional[List[str]]
    country: Optional[str]
    image_url: Optional[str]
    source_name: str
    published_at: Optional[str]
    category: Optional[str] = None
    sentiment: Optional[str] = None
    engagement_score: Optional[float] = None
    is_breaking_news: Optional[bool] = None
    importance_level: Optional[str] = None

    @classmethod
    def from_db(cls, row: dict) -> "NewsArticleSummary":
        """Create from database row."""
        tldr = None
        if row.get("tldr_json"):
            try:
                tldr = json.loads(row["tldr_json"])
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing tldr JSON: {e}")

        tags = None
        if row.get("tags_json"):
            try:
                tags = json.loads(row["tags_json"])
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing tags JSON: {e}")

        return cls(
            id=row["id"],
            slug=row["slug"],
            title=row["title"],
            excerpt=row.get("excerpt"),
            tldr=tldr,
            tags=tags,
            country=row.get("country"),
            image_url=row.get("image_url"),
            source_name=row.get("source_name", "Unknown"),
            published_at=row.get("published_at"),
            category=row.get("category"),
            sentiment=row.get("sentiment"),
            engagement_score=row.get("engagement_score"),
            is_breaking_news=bool(row.get("is_breaking_news")),
            importance_level=row.get("importance_level")
        )


class NewsArticleFull(BaseModel):
    """Full article for detail view."""
    id: int
    slug: str
    title: str
    excerpt: Optional[str]
    content_md: Optional[str]
    tldr: Optional[List[str]]
    tags: Optional[List[str]]
    country: Optional[str]
    language: str
    image_url: Optional[str]
    source_name: str
    source_url: str
    canonical_url: Optional[str]
    published_at: Optional[str]
    view_count: int
    is_saved: bool = False
    
    @classmethod
    def from_db(cls, row: dict, is_saved: bool = False) -> "NewsArticleFull":
        """Create from database row."""
        tldr = None
        if row.get("tldr_json"):
            try:
                tldr = json.loads(row["tldr_json"])
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing tldr JSON: {e}")
        
        tags = None
        if row.get("tags_json"):
            try:
                tags = json.loads(row["tags_json"])
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing tags JSON: {e}")
        
        return cls(
            id=row["id"],
            slug=row["slug"],
            title=row["title"],
            excerpt=row.get("excerpt"),
            content_md=row.get("content_md"),
            tldr=tldr,
            tags=tags,
            country=row.get("country"),
            language=row.get("language", "fr"),
            image_url=row.get("image_url"),
            source_name=row.get("source_name", "Unknown"),
            source_url=row.get("source_url", ""),
            canonical_url=row.get("canonical_url"),
            published_at=row.get("published_at"),
            view_count=row.get("view_count", 0),
            is_saved=is_saved
        )


class NewsPaginatedResponse(BaseModel):
    """Paginated response for news list."""
    data: List[NewsArticleSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_user_id(authorization: Optional[str] = None) -> str:
    """Resolve user ID from authorization header or use default."""
    if authorization:
        user_id = get_user_id_from_request(authorization, fallback_user_id="default")
        if user_id:
            return user_id
    return "default"


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/health")
async def news_health():
    """Health check for news module."""
    return {"status": "healthy", "module": "news"}


@router.get("", response_model=NewsPaginatedResponse)
async def get_news_feed(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Search query"),
    country: Optional[str] = Query(None, description="Filter by country code (NG, ZA, KE, etc.)"),
    tag: Optional[str] = Query(None, description="Filter by tag (fintech, startup, vc, etc.)"),
    region: Optional[str] = Query(None, description="Filter by region (PAN, WEST, CENTRAL, EAST, NORTH, SOUTH)"),
    sort_by: Optional[str] = Query("date", description="Sort by: date or relevance")
):
    """
    Get paginated news feed.

    Supports filtering by:
    - Search query (title, excerpt, content)
    - Country code
    - Tag
    - Region (PAN, WEST, CENTRAL, EAST, NORTH, SOUTH)
    - Sort by date or relevance (engagement_score)
    """
    try:
        result = db.get_news_articles(
            page=page,
            page_size=page_size,
            query=q,
            country=country,
            tag=tag,
            region=region,
            sort_by=sort_by
        )

        articles = [NewsArticleSummary.from_db(row) for row in result["data"]]

        return NewsPaginatedResponse(
            data=articles,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        logger.error(f"Error fetching news feed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch news")


@router.get("/saved", response_model=NewsPaginatedResponse)
async def get_saved_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """Get user's saved articles."""
    user_id = _resolve_user_id(authorization)
    
    try:
        result = db.get_saved_news_articles(user_id, page, page_size)
        articles = [NewsArticleSummary.from_db(row) for row in result["data"]]
        
        return NewsPaginatedResponse(
            data=articles,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
    except Exception as e:
        logger.error(f"Error fetching saved articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch saved articles")


@router.get("/health")
async def get_news_health():
    """
    Get news pipeline health status.
    Returns last run time, article counts, and error status.
    """
    import json
    from pathlib import Path
    from datetime import datetime, timedelta
    
    metrics_file = Path(__file__).parent.parent / "data" / "news_metrics.json"
    
    # Load metrics
    metrics = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading metrics file: {e}")
    
    # Get article counts from DB
    try:
        total_articles = db.get_news_articles(page=1, page_size=1).get("total", 0)
        
        # Count articles from last 24h
        recent_articles = db.get_news_articles(page=1, page_size=100)
        now = datetime.now()
        articles_24h = sum(
            1 for a in recent_articles.get("data", [])
            if a.get("published_at") and
            (now - datetime.fromisoformat(a["published_at"].replace('Z', ''))).total_seconds() < 86400
        )
    except (ValueError, TypeError, KeyError) as e:
        logger.error(f"Error calculating 24h articles: {e}")
        total_articles = 0
        articles_24h = 0
    
    # Check if pipeline is healthy (ran in last 45 min)
    last_run = metrics.get("last_run")
    is_healthy = False
    minutes_since_last_run = None
    
    if last_run:
        try:
            last_run_dt = datetime.fromisoformat(last_run)
            minutes_since_last_run = int((datetime.now() - last_run_dt).total_seconds() / 60)
            is_healthy = minutes_since_last_run < 45  # Allow some slack
        except (ValueError, TypeError) as e:
            logger.debug(f"Error parsing last run time: {e}")
    
    return {
        "status": "healthy" if is_healthy else "degraded",
        "last_run": last_run,
        "minutes_since_last_run": minutes_since_last_run,
        "last_success": metrics.get("last_success", False),
        "total_articles": total_articles,
        "articles_last_24h": articles_24h,
        "last_result": metrics.get("last_result", {}),
        "history": metrics.get("history", [])[:5]
    }


@router.get("/regions")
async def get_regions_with_counts():
    """
    Get regions with article counts for dynamic UI.
    Returns real counts from database.
    """
    # Get all articles and count by region
    try:
        all_articles = db.get_news_articles(page=1, page_size=500)
        articles = all_articles.get("data", [])
        
        # Region mapping based on country
        country_to_region = {
            "MA": "NORTH", "DZ": "NORTH", "TN": "NORTH", "EG": "NORTH", "LY": "NORTH",
            "NG": "WEST", "GH": "WEST", "SN": "WEST", "CI": "WEST", "BF": "WEST", 
            "ML": "WEST", "NE": "WEST", "TG": "WEST", "BJ": "WEST", "GN": "WEST",
            "CM": "CENTRAL", "GA": "CENTRAL", "CG": "CENTRAL", "TD": "CENTRAL", 
            "CF": "CENTRAL", "GQ": "CENTRAL", "CD": "CENTRAL",
            "KE": "EAST", "TZ": "EAST", "UG": "EAST", "RW": "EAST", "ET": "EAST", "SS": "EAST",
            "ZA": "SOUTH", "AO": "SOUTH", "MZ": "SOUTH", "ZW": "SOUTH", 
            "NA": "SOUTH", "BW": "SOUTH", "ZM": "SOUTH", "MW": "SOUTH"
        }
        
        # Count by region
        counts = {"PAN": 0, "NORTH": 0, "WEST": 0, "CENTRAL": 0, "EAST": 0, "SOUTH": 0}
        
        for article in articles:
            country = article.get("country")
            if country:
                region = country_to_region.get(country, "PAN")
                counts[region] = counts.get(region, 0) + 1
            else:
                counts["PAN"] += 1
        
        return {
            "regions": [
                {"id": "cemac", "name": "CEMAC", "description": "Afrique Centrale", "count": counts["CENTRAL"]},
                {"id": "uemoa", "name": "UEMOA", "description": "Afrique de l'Ouest", "count": counts["WEST"]},
                {"id": "north-africa", "name": "Afrique du Nord", "description": "Maghreb & Égypte", "count": counts["NORTH"]},
                {"id": "east-africa", "name": "Afrique de l'Est", "description": "Kenya, Rwanda...", "count": counts["EAST"]},
                {"id": "southern-africa", "name": "Afrique Australe", "description": "Afrique du Sud...", "count": counts["SOUTH"]},
                {"id": "pan-africa", "name": "Panafricain", "description": "Tout le continent", "count": counts["PAN"]}
            ],
            "total": sum(counts.values())
        }
    except Exception as e:
        logger.error(f"Error getting region counts: {e}")
        return {"regions": [], "total": 0}


@router.get("/countries")
async def get_available_countries():
    """Get list of countries with articles."""
    # Common Africa countries for news
    return {
        "countries": [
            {"code": "NG", "name": "Nigeria", "flag": "🇳🇬"},
            {"code": "ZA", "name": "Afrique du Sud", "flag": "🇿🇦"},
            {"code": "KE", "name": "Kenya", "flag": "🇰🇪"},
            {"code": "EG", "name": "Égypte", "flag": "🇪🇬"},
            {"code": "GH", "name": "Ghana", "flag": "🇬🇭"},
            {"code": "CI", "name": "Côte d'Ivoire", "flag": "🇨🇮"},
            {"code": "SN", "name": "Sénégal", "flag": "🇸🇳"},
            {"code": "MA", "name": "Maroc", "flag": "🇲🇦"},
            {"code": "TN", "name": "Tunisie", "flag": "🇹🇳"},
            {"code": "RW", "name": "Rwanda", "flag": "🇷🇼"},
        ]
    }


@router.get("/tags")
async def get_available_tags():
    """Get list of common tags."""
    return {
        "tags": [
            {"id": "fintech", "label": "Fintech", "color": "accent"},
            {"id": "startup", "label": "Startup", "color": "blue"},
            {"id": "vc", "label": "VC / Levée", "color": "purple"},
            {"id": "regulation", "label": "Régulation", "color": "orange"},
            {"id": "crypto", "label": "Crypto", "color": "yellow"},
            {"id": "banking", "label": "Banque", "color": "green"},
            {"id": "payments", "label": "Paiements", "color": "cyan"},
            {"id": "insurtech", "label": "Insurtech", "color": "pink"},
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# News Pipeline Status (Public - for frontend freshness indicator)
# NOTE: This MUST be before /{slug} route to avoid conflict
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/status")
async def get_news_status():
    """
    Get news feed status for freshness indicator.
    Returns when articles were last updated.
    
    Frontend can use this to show "Rafraîchi il y a X minutes".
    """
    from datetime import datetime
    
    try:
        with db._get_conn() as conn:
            # Get latest article creation time
            cursor = conn.execute("""
                SELECT MAX(created_at) as last_created,
                       MAX(published_at) as last_published,
                       COUNT(*) as total_articles
                FROM news_articles
            """)
            row = cursor.fetchone()
            
            last_created = row[0] if row else None
            last_published = row[1] if row else None
            total = row[2] if row else 0
            
            # Articles in last 24h
            cursor = conn.execute("""
                SELECT COUNT(*) FROM news_articles 
                WHERE created_at >= datetime('now', '-24 hours')
            """)
            last_24h = cursor.fetchone()[0]
            
            # Calculate minutes since last article
            minutes_ago = None
            if last_created:
                try:
                    last_dt = datetime.fromisoformat(last_created.replace("Z", "+00:00"))
                    delta = datetime.utcnow() - last_dt.replace(tzinfo=None)
                    minutes_ago = int(delta.total_seconds() / 60)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error calculating minutes ago: {e}")
            
            return {
                "status": "ok" if total > 0 else "empty",
                "total_articles": total,
                "last_article_at": last_created,
                "last_published_at": last_published,
                "minutes_since_update": minutes_ago,
                "articles_last_24h": last_24h,
                "is_fresh": minutes_ago is not None and minutes_ago < 60,
            }
            
    except Exception as e:
        logger.error(f"Error getting news status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_articles": 0,
            "is_fresh": False,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Breaking News Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/breaking")
async def get_breaking_news(
    limit: int = Query(5, ge=1, le=20, description="Maximum number of breaking news"),
    max_age_hours: int = Query(6, ge=1, le=48, description="Maximum age in hours")
):
    """
    Get recent breaking news articles.
    Used for the breaking news banner and alerts.
    """
    from news_notifications import get_notification_service

    try:
        service = get_notification_service()
        articles = service.get_breaking_news(limit=limit, max_age_hours=max_age_hours)

        return {
            "data": articles,
            "count": len(articles),
            "has_breaking": len(articles) > 0
        }
    except Exception as e:
        logger.error(f"Error fetching breaking news: {e}")
        return {"data": [], "count": 0, "has_breaking": False}


@router.get("/important")
async def get_important_news(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of articles"),
    max_age_hours: int = Query(24, ge=1, le=168, description="Maximum age in hours")
):
    """
    Get high importance news articles.
    Used for featured/trending sections.
    """
    from news_notifications import get_notification_service

    try:
        service = get_notification_service()
        articles = service.get_high_importance_news(limit=limit, max_age_hours=max_age_hours)

        return {
            "data": articles,
            "count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error fetching important news: {e}")
        return {"data": [], "count": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# Article Detail (Dynamic route - must be AFTER static routes)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{slug}", response_model=NewsArticleFull)
async def get_article_detail(
    slug: str,
    authorization: Optional[str] = Header(None)
):
    """Get full article by slug."""
    article = db.get_news_article_by_slug(slug)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Check if saved by user
    user_id = _resolve_user_id(authorization)
    is_saved = db.is_article_saved_by_user(user_id, article["id"])
    
    return NewsArticleFull.from_db(article, is_saved=is_saved)


@router.post("/{article_id}/save")
async def save_article(
    article_id: int,
    authorization: Optional[str] = Header(None)
):
    """Save an article to user's list."""
    user_id = _resolve_user_id(authorization)
    
    success = db.save_news_article_for_user(user_id, article_id)
    
    if success:
        return {"status": "saved", "article_id": article_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save article")


@router.delete("/{article_id}/save")
async def unsave_article(
    article_id: int,
    authorization: Optional[str] = Header(None)
):
    """Remove an article from user's saved list."""
    user_id = _resolve_user_id(authorization)
    
    success = db.unsave_news_article_for_user(user_id, article_id)
    
    if success:
        return {"status": "removed", "article_id": article_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to remove article")


@router.get("/check/{article_id}/saved")
async def check_article_saved(
    article_id: int,
    authorization: Optional[str] = Header(None)
):
    """Check if an article is saved by the user."""
    user_id = _resolve_user_id(authorization)
    is_saved = db.is_article_saved_by_user(user_id, article_id)
    
    return {"article_id": article_id, "is_saved": is_saved}


# ═══════════════════════════════════════════════════════════════════════════════
# Internal Pipeline Ingest Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")


class ArticleIngest(BaseModel):
    slug: str
    title: str
    excerpt: Optional[str] = None
    content_md: Optional[str] = None
    tldr_json: Optional[str] = None
    tags_json: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = "fr"
    image_url: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    canonical_url: Optional[str] = None
    published_at: Optional[str] = None
    status: Optional[str] = "published"
    category: Optional[str] = None
    sentiment: Optional[str] = "neutral"
    is_ai_processed: Optional[bool] = False
    engagement_score: Optional[float] = 0.0
    is_breaking_news: Optional[bool] = False
    importance_level: Optional[str] = "normal"
    raw_item_id: Optional[int] = None


class IngestRequest(BaseModel):
    articles: List[ArticleIngest]


@router.post("/ingest")
async def ingest_articles(
    request: IngestRequest,
    x_internal_key: Optional[str] = Header(None)
):
    """
    Bulk ingest articles from the pipeline scheduler.
    Protected by internal API key.
    """
    # Verify internal API key
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid internal API key")

    inserted = 0
    duplicates = 0
    errors = 0

    for art in request.articles:
        article_dict = art.dict()
        # Convert booleans to integers for SQLite
        article_dict["is_ai_processed"] = 1 if article_dict.get("is_ai_processed") else 0
        article_dict["is_breaking_news"] = 1 if article_dict.get("is_breaking_news") else 0

        # Check for duplicates before insert
        if db.article_exists(article_dict.get("source_url", ""), article_dict.get("title", "")):
            duplicates += 1
            continue

        article_id = db.insert_news_article(article_dict)
        if article_id:
            inserted += 1
        else:
            errors += 1

    logger.info(
        f"Ingest complete: {inserted} inserted, {duplicates} duplicates skipped, "
        f"{errors} errors out of {len(request.articles)}"
    )
    return {
        "status": "ok",
        "inserted": inserted,
        "duplicates": duplicates,
        "errors": errors,
        "total": len(request.articles)
    }


# NOTE: /status endpoint moved above /{slug} route to avoid conflict
