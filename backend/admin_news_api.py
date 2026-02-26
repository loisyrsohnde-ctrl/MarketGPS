"""
Unified Admin News API Router

Provides consolidated admin endpoints for news and video script management:
- GET /api/admin/news - List articles with filters
- GET /api/admin/editorial-scores - Get articles ranked by editorial intelligence
- POST /api/admin/rescore-articles - Manually trigger editorial scoring
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
    country: Optional[str] = None
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


class EditorialComponentScores(BaseModel):
    """Component breakdown of editorial score."""
    source_diversity: float = 0.0
    verified_engagement: float = 0.0
    topic_importance: float = 0.0
    freshness: float = 0.0
    geo_relevance: float = 0.0


class EditorialScoreItem(BaseModel):
    """Single article with editorial score data."""
    article_id: int
    title: Optional[str] = None
    source_name: Optional[str] = None
    editorial_score: float
    reasons: List[str] = []
    component_scores: EditorialComponentScores = EditorialComponentScores()
    cluster_id: Optional[str] = None
    cluster_size: int = 1
    cluster_sources: List[str] = []
    scored_at: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None
    total_interactions: Optional[int] = None


class EditorialScoresResponse(BaseModel):
    """Response for editorial scores endpoint."""
    articles: List[EditorialScoreItem]
    total: int
    updated_at: str


class RescoreRequest(BaseModel):
    """Request to trigger manual rescoring."""
    days_back: int = 7
    top_k: int = 100


class RescoreResponse(BaseModel):
    """Response after rescoring articles."""
    message: str
    total_scored: int
    top_score: float


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/admin/news - List news articles with filters
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/news", response_model=NewsListResponse)
async def list_news_articles(
    country: Optional[str] = Query(None, description="Filter by country"),
    language: Optional[str] = Query(None, description="Filter by language"),
    minViralityScore: Optional[float] = Query(None, description="Minimum virality score"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    List news articles with optional filters.

    Query params:
    - country: Filter by country
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

        if country:
            query += " AND country = ?"
            params.append(country)

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
# GET /api/admin/editorial-scores - Get articles ranked by editorial intelligence
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/editorial-scores", response_model=EditorialScoresResponse)
async def get_editorial_scores(
    top_k: int = Query(50, ge=1, le=200, description="Number of top articles to return"),
    days_back: int = Query(3, ge=1, le=30, description="Days of articles to analyze"),
    min_score: float = Query(25.0, ge=0, le=100, description="Minimum editorial score"),
):
    """
    Get articles ranked by editorial intelligence score.

    Uses the EditorialScorer pipeline to cluster articles by topic,
    evaluate source diversity, engagement, importance, freshness,
    and geographic relevance.

    Query params:
    - top_k: Number of top articles to return (default: 50)
    - days_back: Days of articles to analyze (default: 3)
    - min_score: Minimum editorial score threshold (default: 25)
    """
    try:
        from pipeline.news.editorial_scorer import EditorialScorer

        scorer = EditorialScorer(get_db_conn=db._get_conn)
        scored_articles = scorer.score_and_rank(
            top_k=top_k,
            min_score=min_score,
            days_back=days_back,
        )

        # Enrich with article metadata from DB
        enriched = []
        conn = db._get_conn()
        cursor = conn.cursor()

        for score_obj in scored_articles:
            # Fetch article title, source, etc.
            cursor.execute(
                """SELECT title, source_name, country, language, published_at,
                          canonical_url, total_interactions
                   FROM news_articles WHERE id = ?""",
                (score_obj.article_id,),
            )
            row = cursor.fetchone()

            item = EditorialScoreItem(
                article_id=score_obj.article_id,
                title=row[0] if row else None,
                source_name=row[1] if row else None,
                editorial_score=score_obj.editorial_score,
                reasons=score_obj.reasons,
                component_scores=EditorialComponentScores(
                    **score_obj.component_scores
                ),
                cluster_id=score_obj.cluster_id,
                cluster_size=score_obj.cluster_size,
                cluster_sources=score_obj.cluster_sources,
                scored_at=score_obj.scored_at,
                country=row[2] if row else None,
                language=row[3] if row else None,
                published_at=row[4] if row else None,
                url=row[5] if row else None,
                total_interactions=row[6] if row else None,
            )
            enriched.append(item)

        conn.close()

        return EditorialScoresResponse(
            articles=enriched,
            total=len(enriched),
            updated_at=datetime.utcnow().isoformat(),
        )

    except ImportError:
        logger.error("EditorialScorer module not found in pipeline.news")
        raise HTTPException(
            status_code=501,
            detail="Editorial Scorer module not available. Check pipeline/news/editorial_scorer.py",
        )
    except Exception as e:
        logger.error(f"Error getting editorial scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/admin/rescore-articles - Manually trigger editorial scoring
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/rescore-articles", response_model=RescoreResponse)
async def rescore_articles(request: RescoreRequest = RescoreRequest()):
    """
    Manually trigger editorial scoring for recent articles.

    Body (optional):
    - days_back: Number of days to analyze (default: 7)
    - top_k: Number of top articles to score (default: 100)
    """
    try:
        from pipeline.news.editorial_scorer import EditorialScorer

        scorer = EditorialScorer(get_db_conn=db._get_conn)
        results = scorer.score_and_rank(
            days_back=request.days_back,
            top_k=request.top_k,
        )

        # Persist scores to database
        saved_count = scorer.save_scores(results)

        top_score = max(
            [r.editorial_score for r in results], default=0
        )

        logger.info(
            f"Rescored {saved_count} articles (days_back={request.days_back}, "
            f"top_k={request.top_k}, top_score={top_score:.1f})"
        )

        return RescoreResponse(
            message=f"Rescored {saved_count} articles successfully",
            total_scored=saved_count,
            top_score=round(top_score, 1),
        )

    except ImportError:
        logger.error("EditorialScorer module not found in pipeline.news")
        raise HTTPException(
            status_code=501,
            detail="Editorial Scorer module not available. Check pipeline/news/editorial_scorer.py",
        )
    except Exception as e:
        logger.error(f"Error rescoring articles: {e}")
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
        with db._get_conn() as conn:
            # Ensure table exists before querying
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_scripts (
                    id TEXT PRIMARY KEY,
                    article_id TEXT,
                    title TEXT NOT NULL,
                    hook TEXT,
                    script_text TEXT,
                    word_count INTEGER DEFAULT 0,
                    estimated_duration_seconds INTEGER DEFAULT 0,
                    sources_mentioned TEXT DEFAULT '[]',
                    key_facts TEXT DEFAULT '[]',
                    status TEXT DEFAULT 'draft',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            """)

            count_query = "SELECT COUNT(*) FROM video_scripts WHERE 1=1"
            count_params = []

            if status:
                count_query += " AND status = ?"
                count_params.append(status)

            total = conn.execute(count_query, count_params).fetchone()[0]

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


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/admin/generate-from-url - Generate & publish article from URL or topic
# ═══════════════════════════════════════════════════════════════════════════════


class GenerateFromURLRequest(BaseModel):
    """Request to generate an article from a source URL or a topic."""
    url: str  # Can be a URL or a topic/title text


class GenerateFromURLResponse(BaseModel):
    """Response after generating article from URL or topic."""
    success: bool
    article_id: Optional[int] = None
    title: Optional[str] = None
    message: str


def _is_url(text: str) -> bool:
    """Check if text looks like a URL."""
    import re
    text = text.strip()
    return bool(re.match(r'^https?://', text, re.I)) or bool(re.match(r'^www\.', text, re.I))


@router.post("/generate-from-url", response_model=GenerateFromURLResponse)
async def generate_article_from_url(request: GenerateFromURLRequest):
    """
    Generate a full French article and publish it immediately.

    Supports two modes:
    - URL mode: Paste a URL → fetches, translates, enriches, publishes
    - Topic mode: Paste a subject/title → LLM writes a full article from scratch

    Body:
    - url: Source article URL or topic/title text

    Returns:
        GenerateFromURLResponse with article details
    """
    import asyncio

    input_text = request.url.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="URL ou sujet requis")

    try:
        if _is_url(input_text):
            # URL mode: fetch content from source
            url = input_text if input_text.startswith("http") else f"https://{input_text}"
            result = await asyncio.to_thread(_generate_from_url_sync, url)
        else:
            # Topic mode: generate article from topic/title
            result = await asyncio.to_thread(_generate_from_topic_sync, input_text)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating article: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_from_topic_sync(topic: str) -> GenerateFromURLResponse:
    """Generate an article from a topic/title using LLM (no source URL needed)."""
    import json
    import re
    from datetime import datetime

    try:
        from pipeline.news.publish import NewsPublisher
    except ImportError as e:
        logger.error(f"Cannot import NewsPublisher: {e}")
        return GenerateFromURLResponse(
            success=False,
            message="Pipeline module not available on this server"
        )

    publisher = NewsPublisher(store=db)

    if not publisher.llm_provider:
        return GenerateFromURLResponse(
            success=False,
            message="Aucun LLM disponible. Configurez OPENAI_API_KEY ou GEMINI_API_KEY."
        )

    # Build a specific prompt for topic-based generation
    prompt = f"""Tu es un Rédacteur en Chef senior pour "MarketGPS", un média économique et financier de référence couvrant l'Afrique et les marchés internationaux.

SUJET À TRAITER : {topic}

LANGUE OBLIGATOIRE : FRANÇAIS. L'article DOIT être intégralement en français.

INSTRUCTIONS :
Rédige un article journalistique complet, approfondi et professionnel sur ce sujet.

1. STYLE : Journalistique premium (niveau Jeune Afrique / Les Échos).
   - Commence par un LEAD percutant.
   - INTERDIT : "Introduction", "Conclusion", "En résumé".
   - Ton factuel, analytique et engageant.

2. CONTENU (800-1200 mots) :
   - Contextualise : historique, enjeux, pourquoi c'est important maintenant.
   - Chiffres & données : intègre des données pertinentes, comparaisons.
   - Acteurs clés : entreprises, dirigeants, institutions impliquées.
   - Impact marché : conséquences économiques, financières, business.
   - Perspectives : scénarios futurs, implications.
   - Utilise le **gras** pour les noms d'entreprises et chiffres clés.
   - Structure avec 2-3 sous-titres en ## markdown.

3. IMAGE SEARCH : Génère une requête de recherche d'image précise en anglais.

Réponds UNIQUEMENT en JSON valide :
{{
  "skip": false,
  "title_fr": "Titre accrocheur en français (max 100 caractères)",
  "excerpt_fr": "Résumé de 2-3 phrases en français",
  "content_md": "Article complet en markdown (800-1200 mots, EN FRANÇAIS)",
  "category": "Finance|Tech|Business|Startup|Régulation|Énergie|Marchés",
  "sentiment": "positive|neutral|negative",
  "image_search_query": "requête image en anglais",
  "tldr": ["Point clé 1", "Point clé 2", "Point clé 3"]
}}"""

    try:
        if publisher.llm_provider == "openai" and publisher.openai_client:
            response = publisher.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=6000,
                temperature=0.7
            )
            text = response.choices[0].message.content
        elif publisher.llm_provider == "gemini":
            response = publisher.gemini_model.generate_content(prompt)
            text = response.text
        else:
            return GenerateFromURLResponse(
                success=False,
                message="Aucun LLM configuré"
            )

        # Parse JSON response
        json_str = text.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        try:
            rewritten = json.loads(json_str)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                rewritten = json.loads(json_match.group())
            else:
                return GenerateFromURLResponse(
                    success=False,
                    message="Erreur de parsing de la réponse LLM"
                )

        if rewritten.get("skip"):
            return GenerateFromURLResponse(
                success=False,
                message="Le LLM a estimé que ce sujet est hors-thème pour MarketGPS."
            )

        if not rewritten.get("title_fr") or not rewritten.get("content_md"):
            return GenerateFromURLResponse(
                success=False,
                message="Réponse LLM incomplète (titre ou contenu manquant)"
            )

    except Exception as e:
        logger.error(f"LLM generation failed for topic '{topic}': {e}")
        return GenerateFromURLResponse(
            success=False,
            message=f"Erreur LLM : {str(e)[:200]}"
        )

    # Detect country and tags from generated content
    content_for_detection = f"{rewritten.get('title_fr', '')} {rewritten.get('content_md', '')}"
    country = publisher._detect_country(content_for_detection, None)
    tags = publisher._extract_tags(content_for_detection, [])
    category = rewritten.get("category") or (tags[0].capitalize() if tags else "Actualité")

    # Fetch image
    from pipeline.news.image_fetcher import fetch_article_image
    image_url = fetch_article_image(
        title=rewritten.get("title_fr", topic),
        category=category,
        country=country,
        keywords=rewritten.get("image_search_query"),
        existing_url=None
    )

    # Generate slug with timestamp to avoid duplicates for admin-generated articles
    import time
    base_slug = publisher._generate_slug(rewritten.get("title_fr", "article"))
    slug = f"{base_slug}-{int(time.time())}"

    title_fr = rewritten.get("title_fr", topic)
    now = datetime.utcnow().isoformat()

    # Direct SQL insert — bypass dedup check for admin-generated articles
    try:
        conn = db._get_conn()
        cursor = conn.execute("""
            INSERT INTO news_articles (
                slug, title, excerpt, content_md, tldr_json,
                tags_json, country, language, image_url, source_name,
                source_url, canonical_url, published_at, status,
                category, sentiment, is_ai_processed,
                engagement_score, is_breaking_news, importance_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            slug,
            title_fr,
            rewritten.get("excerpt_fr", ""),
            rewritten.get("content_md", ""),
            json.dumps(rewritten.get("tldr")) if rewritten.get("tldr") else None,
            json.dumps(tags) if tags else None,
            country,
            "fr",
            image_url,
            "MarketGPS Rédaction",
            None,  # source_url
            None,  # canonical_url
            now,
            "published",
            category,
            rewritten.get("sentiment", "neutral"),
            1,   # is_ai_processed
            0.95,  # engagement_score
            0,   # is_breaking_news
            "high",  # importance_level
        ))
        conn.commit()
        article_id = cursor.lastrowid
        conn.close()

        logger.info(f"Article generated from topic: {title_fr[:60]}...")
        return GenerateFromURLResponse(
            success=True,
            article_id=article_id,
            title=title_fr,
            message="Article généré depuis le sujet et publié avec succès"
        )
    except Exception as e:
        logger.error(f"Failed to insert topic article: {e}")
        return GenerateFromURLResponse(
            success=False,
            message=f"Erreur lors de l'insertion : {str(e)[:200]}"
        )


def _generate_from_url_sync(url: str) -> GenerateFromURLResponse:
    """Synchronous article generation from URL (runs in threadpool)."""
    import json
    import re
    from datetime import datetime

    try:
        from pipeline.news.publish import NewsPublisher
    except ImportError as e:
        logger.error(f"Cannot import NewsPublisher: {e}")
        return GenerateFromURLResponse(
            success=False,
            message="Pipeline module not available on this server"
        )

    publisher = NewsPublisher(store=db)

    # 1. Fetch full article content
    full_text = publisher._fetch_full_article(url)
    if not full_text or len(full_text.strip()) < 100:
        return GenerateFromURLResponse(
            success=False,
            message=f"Impossible de récupérer le contenu depuis cette URL. Vérifiez que le lien est accessible."
        )

    logger.info(f"Fetched {len(full_text)} chars from {url}")

    # 2. Detect source language (simple heuristic)
    french_words = ['le', 'la', 'les', 'des', 'une', 'est', 'dans', 'pour', 'avec', 'sur']
    words = full_text.lower().split()[:200]
    fr_count = sum(1 for w in words if w in french_words)
    source_language = "fr" if fr_count > 10 else "en"

    # 3. Build a raw payload for the LLM
    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
    raw_title = lines[0][:150] if lines else "Article"

    raw_payload = {
        "title": raw_title,
        "content": full_text,
        "summary": full_text[:500],
    }

    # 4. LLM rewrite to French
    rewritten = publisher._rewrite_with_llm(raw_payload, source_language, full_article_text=full_text)

    if not rewritten or rewritten.get("skip"):
        return GenerateFromURLResponse(
            success=False,
            message="Le LLM a filtré cet article (hors-thème) ou n'est pas disponible. Vérifiez OPENAI_API_KEY / GEMINI_API_KEY."
        )

    # 5. Detect country and tags
    content_for_detection = f"{rewritten.get('title_fr', '')} {rewritten.get('content_md', '')}"
    country = publisher._detect_country(content_for_detection, None)
    tags = publisher._extract_tags(content_for_detection, [])
    category = rewritten.get("category") or (tags[0].capitalize() if tags else "Actualité")

    # 6. Fetch image
    from pipeline.news.image_fetcher import fetch_article_image
    image_url = fetch_article_image(
        title=rewritten.get("title_fr", raw_title),
        category=category,
        country=country,
        keywords=rewritten.get("image_search_query"),
        existing_url=None
    )

    # 7. Generate slug with timestamp to avoid duplicates
    import time
    base_slug = publisher._generate_slug(rewritten.get("title_fr", "article"))
    slug = f"{base_slug}-{int(time.time())}"

    title_fr = rewritten.get("title_fr", raw_title)
    now = datetime.utcnow().isoformat()

    # 8. Direct SQL insert — bypass dedup for admin-generated articles
    try:
        conn = db._get_conn()
        cursor = conn.execute("""
            INSERT INTO news_articles (
                slug, title, excerpt, content_md, tldr_json,
                tags_json, country, language, image_url, source_name,
                source_url, canonical_url, published_at, status,
                category, sentiment, is_ai_processed,
                engagement_score, is_breaking_news, importance_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            slug,
            title_fr,
            rewritten.get("excerpt_fr", ""),
            rewritten.get("content_md", full_text[:2000]),
            json.dumps(rewritten.get("tldr")) if rewritten.get("tldr") else None,
            json.dumps(tags) if tags else None,
            country,
            "fr",
            image_url,
            "MarketGPS Rédaction",
            url,
            url,
            now,
            "published",
            category,
            rewritten.get("sentiment", "neutral"),
            1,
            0.95,
            0,
            "high",
        ))
        conn.commit()
        article_id = cursor.lastrowid
        conn.close()

        logger.info(f"Article generated from URL: {title_fr[:60]}...")
        return GenerateFromURLResponse(
            success=True,
            article_id=article_id,
            title=title_fr,
            message="Article généré et publié avec succès"
        )
    except Exception as e:
        logger.error(f"Failed to insert URL article: {e}")
        return GenerateFromURLResponse(
            success=False,
            message=f"Erreur lors de l'insertion : {str(e)[:200]}"
        )
