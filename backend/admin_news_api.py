"""
Unified Admin News API Router

Provides consolidated admin endpoints for news and video script management:
- GET /api/admin/news - List articles with filters
- GET /api/admin/scripts - List all scripts
- GET /api/admin/scripts/{id} - Get script details
- POST /api/admin/scripts - Generate script from article
- PUT /api/admin/scripts/{id} - Update script
- DELETE /api/admin/scripts/{id} - Delete script
- POST /api/admin/scripts/{id}/approve - Approve script
- POST /api/admin/scripts/{id}/publish - Publish with journalistic rewrite
"""

import asyncio
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel
from datetime import datetime

from core.config import get_logger
from storage.sqlite_store import SQLiteStore
from services.video_script_service import VideoScriptService, VideoScript

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["Admin News"])

# Database store
db = SQLiteStore()

# Initialize services
video_script_service = None


def get_services():
    """Récupère les instances des services."""
    global video_script_service

    if not video_script_service:
        video_script_service = VideoScriptService(get_db_conn=db._get_conn)

    return video_script_service


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════


class NewsArticleResponse(BaseModel):
    """Response model for news article."""
    id: str
    title: str
    content_md: Optional[str] = None
    summary: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    published_at: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    total_interactions: Optional[int] = None
    status: Optional[str] = None


class VideoScriptResponse(BaseModel):
    """Response model for video script."""
    id: str
    article_id: str
    title: str
    hook: str
    script_text: str
    word_count: int
    estimated_duration_seconds: int
    sources_mentioned: List[str]
    key_facts: List[str]
    status: str
    created_at: str
    updated_at: str


class GenerateScriptRequest(BaseModel):
    """Request to generate script from article."""
    article_id: str


class UpdateScriptRequest(BaseModel):
    """Request to update script."""
    script_text: Optional[str] = None
    hook: Optional[str] = None
    status: Optional[str] = None


class ApproveScriptRequest(BaseModel):
    """Request to approve script."""
    notes: Optional[str] = None


class PublishScriptRequest(BaseModel):
    """Request to publish script with journalistic rewrite."""
    journalistic_style: bool = True
    notes: Optional[str] = None


class ScriptsListResponse(BaseModel):
    """Response for scripts list."""
    scripts: List[VideoScriptResponse]
    total: int
    page: int
    limit: int


class NewsListResponse(BaseModel):
    """Response for news articles list."""
    articles: List[NewsArticleResponse]
    total: int
    page: int
    limit: int


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/admin/news - List news articles with filters
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/news", response_model=NewsListResponse)
async def list_news_articles(
    region: Optional[str] = Query(None, description="Filter by region"),
    language: Optional[str] = Query(None, description="Filter by language"),
    minViralityScore: Optional[float] = Query(None, description="Minimum virality score"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List news articles with optional filters.

    Query params:
    - region: Filter by region
    - language: Filter by language
    - minViralityScore: Minimum virality score
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)

    Returns:
        NewsListResponse with articles and pagination info
    """
    try:
        conn = db._get_conn()
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM news_articles WHERE 1=1"
        params = []

        if region:
            query += " AND region = ?"
            params.append(region)

        if language:
            query += " AND language = ?"
            params.append(language)

        if minViralityScore is not None:
            query += " AND (viral_score_v2 >= ? OR total_interactions >= ?)"
            params.extend([minViralityScore, int(minViralityScore)])

        # Count total
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        total = cursor.execute(count_query, params).fetchone()[0]

        # Get paginated results
        offset = (page - 1) * limit
        query += " ORDER BY total_interactions DESC, published_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return NewsListResponse(
            articles=articles,
            total=total,
            page=page,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing news articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/admin/scripts - List scripts
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/scripts", response_model=ScriptsListResponse)
async def list_scripts(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List video scripts with optional filters.

    Query params:
    - status: Filter by status ('draft', 'reviewed', 'approved', 'published')
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)

    Returns:
        ScriptsListResponse with scripts and pagination info
    """
    try:
        video_svc = get_services()

        # Calculate offset
        offset = (page - 1) * limit

        # Get scripts
        scripts = video_svc.get_scripts(status=status, limit=limit, offset=offset)

        # Get total count
        conn = db._get_conn()
        cursor = conn.cursor()

        count_query = "SELECT COUNT(*) FROM video_scripts WHERE 1=1"
        count_params = []

        if status:
            count_query += " AND status = ?"
            count_params.append(status)

        total = cursor.execute(count_query, count_params).fetchone()[0]
        conn.close()

        return ScriptsListResponse(
            scripts=[
                VideoScriptResponse(
                    id=s.id,
                    article_id=s.article_id,
                    title=s.title,
                    hook=s.hook,
                    script_text=s.script_text,
                    word_count=s.word_count,
                    estimated_duration_seconds=s.estimated_duration_seconds,
                    sources_mentioned=s.sources_mentioned,
                    key_facts=s.key_facts,
                    status=s.status,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
                for s in scripts
            ],
            total=total,
            page=page,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Error listing scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/admin/scripts/{id} - Get script details
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/scripts/{script_id}", response_model=VideoScriptResponse)
async def get_script(script_id: str):
    """
    Get script details by ID.

    Path params:
    - script_id: Script ID

    Returns:
        VideoScriptResponse
    """
    try:
        video_svc = get_services()
        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/admin/scripts - Generate script from article
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/scripts", response_model=VideoScriptResponse)
async def generate_script(request: GenerateScriptRequest):
    """
    Generate video script from article.

    Body:
    - article_id: ID of article to generate script from

    Returns:
        VideoScriptResponse with generated script
    """
    try:
        video_svc = get_services()

        # Get article from database
        conn = db._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, content_md, summary, source_name, published_at
            FROM news_articles
            WHERE id = ?
        """, (request.article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article_id, title, content_md, summary, source, published_at = article
        content = content_md or summary or ""

        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Article has no content to generate script from"
            )

        # Generate script (run in threadpool since Gemini SDK is synchronous)
        script = await asyncio.to_thread(
            video_svc.generate_script_sync,
            article_id=article_id,
            title=title,
            content=content,
            source=source,
            date=published_at or "",
        )

        if not script:
            raise HTTPException(
                status_code=500,
                detail="Gemini generation failed — check GEMINI_API_KEY and API quota"
            )

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /api/admin/scripts/{id} - Update script
# ═══════════════════════════════════════════════════════════════════════════════


@router.put("/scripts/{script_id}", response_model=VideoScriptResponse)
async def update_script(script_id: str, request: UpdateScriptRequest):
    """
    Update script content or status.

    Path params:
    - script_id: Script ID

    Body:
    - script_text: New script text (optional)
    - hook: New hook (optional)
    - status: New status (optional)

    Returns:
        VideoScriptResponse with updated script
    """
    try:
        video_svc = get_services()

        success = video_svc.update_script(
            script_id=script_id,
            script_text=request.script_text,
            hook=request.hook,
            status=request.status,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to update script")

        # Get updated script
        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found after update")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /api/admin/scripts/{id} - Delete script
# ═══════════════════════════════════════════════════════════════════════════════


@router.delete("/scripts/{script_id}")
async def delete_script(script_id: str):
    """
    Delete a script.

    Path params:
    - script_id: Script ID

    Returns:
        Success response
    """
    try:
        conn = db._get_conn()
        cursor = conn.cursor()

        # Check if script exists
        cursor.execute("SELECT id FROM video_scripts WHERE id = ?", (script_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Script not found")

        # Delete script
        cursor.execute("DELETE FROM video_scripts WHERE id = ?", (script_id,))
        conn.commit()
        conn.close()

        logger.info(f"Script {script_id} deleted")

        return {"success": True, "message": f"Script {script_id} deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/admin/scripts/{id}/approve - Approve script
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/scripts/{script_id}/approve")
async def approve_script(script_id: str, request: ApproveScriptRequest):
    """
    Approve a script for publishing.

    Path params:
    - script_id: Script ID

    Body:
    - notes: Optional approval notes

    Returns:
        Updated VideoScriptResponse with status='approved'
    """
    try:
        video_svc = get_services()

        # Update status to 'approved'
        success = video_svc.update_script(
            script_id=script_id,
            status="approved",
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to approve script")

        # Get updated script
        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found after approval")

        logger.info(f"Script {script_id} approved{' with notes: ' + request.notes if request.notes else ''}")

        return VideoScriptResponse(
            id=script.id,
            article_id=script.article_id,
            title=script.title,
            hook=script.hook,
            script_text=script.script_text,
            word_count=script.word_count,
            estimated_duration_seconds=script.estimated_duration_seconds,
            sources_mentioned=script.sources_mentioned,
            key_facts=script.key_facts,
            status=script.status,
            created_at=script.created_at,
            updated_at=script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/admin/scripts/{id}/publish - Publish with journalistic rewrite
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/scripts/{script_id}/publish", response_model=VideoScriptResponse)
async def publish_script(script_id: str, request: PublishScriptRequest):
    """
    Publish script with optional journalistic rewrite.

    Path params:
    - script_id: Script ID

    Body:
    - journalistic_style: Whether to rewrite in journalistic style (default: true)
    - notes: Optional publication notes

    Returns:
        Updated VideoScriptResponse with status='published' and rewritten content
    """
    try:
        video_svc = get_services()

        # Get script
        script = video_svc.get_script_by_id(script_id)

        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        # Get article for context
        conn = db._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, content_md, summary
            FROM news_articles
            WHERE id = ?
        """, (script.article_id,))

        article = cursor.fetchone()
        conn.close()

        if not article:
            raise HTTPException(
                status_code=404,
                detail="Associated article not found"
            )

        article_id, article_title, content_md, summary = article
        article_content = content_md or summary or ""

        # Rewrite in journalistic style if requested
        rewritten_script_text = script.script_text
        if request.journalistic_style:
            rewritten_script_text = await asyncio.to_thread(
                video_svc.rewrite_as_journalistic_article,
                article_content=article_content,
                script_text=script.script_text,
            )

            if not rewritten_script_text:
                logger.warning(f"Journalistic rewrite failed for {script_id}, using original")
                rewritten_script_text = script.script_text

        # Update script with rewritten content and published status
        success = video_svc.update_script(
            script_id=script_id,
            script_text=rewritten_script_text,
            status="published",
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to publish script")

        # Get updated script
        updated_script = video_svc.get_script_by_id(script_id)

        if not updated_script:
            raise HTTPException(status_code=404, detail="Script not found after publication")

        logger.info(f"Script {script_id} published{'with journalistic rewrite' if request.journalistic_style else ''}")

        return VideoScriptResponse(
            id=updated_script.id,
            article_id=updated_script.article_id,
            title=updated_script.title,
            hook=updated_script.hook,
            script_text=updated_script.script_text,
            word_count=updated_script.word_count,
            estimated_duration_seconds=updated_script.estimated_duration_seconds,
            sources_mentioned=updated_script.sources_mentioned,
            key_facts=updated_script.key_facts,
            status=updated_script.status,
            created_at=updated_script.created_at,
            updated_at=updated_script.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing script: {e}")
        raise HTTPException(status_code=500, detail=str(e))
