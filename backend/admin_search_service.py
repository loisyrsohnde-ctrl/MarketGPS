"""
MarketGPS Admin - Global Search Service
Search across articles, scripts, and users

Provides endpoints for searching:
- News articles by title, content, summary, source
- Video scripts by title and content
- Unified results with relevance scoring
"""

import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from datetime import datetime

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from core.config import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["Admin Search"])

# Database store
db = SQLiteStore()


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Key Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify_admin(admin_key: Optional[str]) -> bool:
    """Verify admin access key."""
    expected = os.environ.get("ADMIN_KEY", "marketgps-admin-2024")
    return admin_key == expected


def require_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Dependency to require admin access."""
    if not verify_admin(admin_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════

class SearchResult(BaseModel):
    """Individual search result."""
    id: str
    type: str  # article, script, user
    title: str
    subtitle: Optional[str] = None
    snippet: str  # 50 chars of matching context
    score: float  # Relevance score
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Search response."""
    query: str
    results: List[SearchResult]
    total: int
    limit: int


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/search", response_model=SearchResponse)
async def search_global(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: article, script, user"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    limit: int = Query(20, ge=1, le=100, description="Result limit"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Global search across articles, scripts, and users.

    Returns unified results sorted by relevance (title matches first).
    Each result includes: {id, type, title, subtitle, snippet, score, metadata}
    """
    require_admin(admin_key)

    results: List[SearchResult] = []

    try:
        with db._get_conn() as conn:
            # Search news articles
            if not type or type == "article":
                article_results = _search_articles(conn, q, country, limit)
                results.extend(article_results)

            # Search video scripts
            if not type or type == "script":
                script_results = _search_scripts(conn, q, limit)
                results.extend(script_results)

            # Search users (from user_profiles)
            if not type or type == "user":
                user_results = _search_users(conn, q, limit)
                results.extend(user_results)

        # Sort by score descending (title matches first due to higher score)
        results.sort(key=lambda x: x.score, reverse=True)

        # Apply limit to final results
        final_results = results[:limit]

        return SearchResponse(
            query=q,
            results=final_results,
            total=len(final_results),
            limit=limit
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _search_articles(conn, query: str, country: Optional[str], limit: int) -> List[SearchResult]:
    """Search news articles."""
    results = []
    pattern = f"%{query}%"

    # Build WHERE clause
    where_parts = ["(title LIKE ? OR content_md LIKE ? OR excerpt LIKE ? OR source_name LIKE ?)"]
    params = [pattern, pattern, pattern, pattern]

    if country:
        where_parts.append("country = ?")
        params.append(country)

    where_clause = " AND ".join(where_parts)

    # Search with relevance scoring
    # Title matches get higher score (100), content/excerpt get 50, source gets 25
    sql = f"""
        SELECT
            id, title, excerpt, source_name, country, status,
            CASE
                WHEN title LIKE ? THEN 100
                WHEN source_name LIKE ? THEN 25
                ELSE 50
            END as relevance_score
        FROM news_articles
        WHERE {where_clause}
        ORDER BY relevance_score DESC, id DESC
        LIMIT ?
    """

    relevance_params = [pattern, pattern] + params + [limit]

    try:
        rows = conn.execute(sql, relevance_params).fetchall()

        for row in rows:
            # Extract snippet (first 50 chars of matching field)
            snippet = row["title"][:50] if row["title"] else ""
            if len(row["title"]) < 20 and row["excerpt"]:
                snippet = row["excerpt"][:50]

            result = SearchResult(
                id=str(row["id"]),
                type="article",
                title=row["title"],
                subtitle=f"Source: {row['source_name']}" if row["source_name"] else None,
                snippet=snippet,
                score=row["relevance_score"] / 100.0,  # Normalize to 0-1
                metadata={
                    "country": row["country"],
                    "status": row["status"],
                    "source": row["source_name"]
                }
            )
            results.append(result)
    except Exception as e:
        logger.warning(f"Article search error: {e}")

    return results


def _search_scripts(conn, query: str, limit: int) -> List[SearchResult]:
    """Search video scripts."""
    results = []
    pattern = f"%{query}%"

    sql = """
        SELECT
            id, title, script_text, status,
            CASE
                WHEN title LIKE ? THEN 100
                ELSE 50
            END as relevance_score
        FROM video_scripts
        WHERE title LIKE ? OR script_text LIKE ?
        ORDER BY relevance_score DESC, id DESC
        LIMIT ?
    """

    params = [pattern, pattern, pattern, limit]

    try:
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            # Extract snippet from script_text
            snippet = row["script_text"][:50] if row["script_text"] else ""

            result = SearchResult(
                id=str(row["id"]),
                type="script",
                title=row["title"],
                subtitle=f"Status: {row['status']}" if row["status"] else None,
                snippet=snippet,
                score=row["relevance_score"] / 100.0,  # Normalize to 0-1
                metadata={
                    "status": row["status"]
                }
            )
            results.append(result)
    except Exception as e:
        logger.warning(f"Script search error: {e}")

    return results


def _search_users(conn, query: str, limit: int) -> List[SearchResult]:
    """Search users by email or display name."""
    results = []
    pattern = f"%{query}%"

    sql = """
        SELECT
            u.user_id, u.email, up.display_name,
            CASE
                WHEN up.display_name LIKE ? THEN 100
                ELSE 50
            END as relevance_score
        FROM users u
        LEFT JOIN user_profiles up ON u.user_id = up.user_id
        WHERE u.email LIKE ? OR up.display_name LIKE ?
        ORDER BY relevance_score DESC, u.created_at DESC
        LIMIT ?
    """

    params = [pattern, pattern, pattern, limit]

    try:
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            display_name = row["display_name"] or row["email"]

            result = SearchResult(
                id=row["user_id"],
                type="user",
                title=display_name,
                subtitle=row["email"],
                snippet=row["email"][:50],
                score=row["relevance_score"] / 100.0,  # Normalize to 0-1
                metadata={
                    "email": row["email"],
                    "display_name": row["display_name"]
                }
            )
            results.append(result)
    except Exception as e:
        logger.warning(f"User search error: {e}")

    return results
