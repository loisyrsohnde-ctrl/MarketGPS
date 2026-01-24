"""
MarketGPS News Module - FastAPI Routes
Endpoints for news feed, articles, and user saves.
"""

import json
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Header
from pydantic import BaseModel

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from backend.security import get_user_id_from_request

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
    
    @classmethod
    def from_db(cls, row: dict) -> "NewsArticleSummary":
        """Create from database row."""
        tldr = None
        if row.get("tldr_json"):
            try:
                tldr = json.loads(row["tldr_json"])
            except:
                pass
        
        tags = None
        if row.get("tags_json"):
            try:
                tags = json.loads(row["tags_json"])
            except:
                pass
        
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
            published_at=row.get("published_at")
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
            except:
                pass
        
        tags = None
        if row.get("tags_json"):
            try:
                tags = json.loads(row["tags_json"])
            except:
                pass
        
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
    tag: Optional[str] = Query(None, description="Filter by tag (fintech, startup, vc, etc.)")
):
    """
    Get paginated news feed.
    
    Supports filtering by:
    - Search query (title, excerpt, content)
    - Country code
    - Tag
    """
    try:
        result = db.get_news_articles(
            page=page,
            page_size=page_size,
            query=q,
            country=country,
            tag=tag
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
