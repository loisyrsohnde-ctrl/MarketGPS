"""
MarketGPS Admin - Article Editorial Workflow Service
Manages the 4-step editorial workflow: Research → Rewrite → Validate → Publish

Endpoints for:
- Getting article with workflow state
- Triggering LLM French rewrite
- Saving manually edited French content
- Validating/approving articles
- Publishing articles
- Batch operations
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Body, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from core.config import get_logger
from pipeline.news.publish import NewsPublisher

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["Admin Workflow"])

# Database store
db = SQLiteStore()

# Initialize LLM-based publisher for rewriting
publisher = None


def get_publisher():
    """Get or initialize the NewsPublisher instance."""
    global publisher
    if not publisher:
        publisher = NewsPublisher(store=db)
    return publisher


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

class ArticleWorkflowResponse(BaseModel):
    """Article with workflow state."""
    id: int
    title: str
    excerpt: Optional[str] = None
    content_md: Optional[str] = None
    french_content_md: Optional[str] = None
    source_name: str
    status: str  # published, pending, rejected
    editorial_status: str  # pending, rewritten, validated, published
    country: Optional[str] = None
    language: Optional[str] = None
    editorial_notes: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: str


class RewriteRequest(BaseModel):
    """Request to trigger LLM rewrite."""
    source_language: str = "en"


class UpdateFrenchContentRequest(BaseModel):
    """Request to save manually edited French content."""
    french_content_md: str
    editorial_notes: Optional[str] = None


class ValidateRequest(BaseModel):
    """Request to validate/approve article."""
    approved_by: str
    editorial_notes: Optional[str] = None


class PublishRequest(BaseModel):
    """Request to publish article."""
    approved_by: str
    editorial_notes: Optional[str] = None


class BatchActionRequest(BaseModel):
    """Request for batch operations."""
    article_ids: List[int]
    action: str  # publish, reject, validate
    approved_by: str
    editorial_notes: Optional[str] = None


class BatchActionResponse(BaseModel):
    """Response for batch operations."""
    action: str
    total: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/articles/{article_id}/workflow", response_model=ArticleWorkflowResponse)
async def get_article_workflow(
    article_id: int,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get article with its workflow state.

    Returns article data including editorial_status, french_content_md, and approval info.
    """
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            row = conn.execute(
                """
                SELECT id, title, excerpt, content_md, french_content_md,
                       source_name, status, editorial_status, country, language,
                       editorial_notes, approved_at, approved_by, created_at
                FROM news_articles
                WHERE id = ?
                """,
                (article_id,)
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            return ArticleWorkflowResponse(
                id=row["id"],
                title=row["title"],
                excerpt=row["excerpt"],
                content_md=row["content_md"],
                french_content_md=row["french_content_md"],
                source_name=row["source_name"],
                status=row["status"],
                editorial_status=row["editorial_status"] or "pending",
                country=row["country"],
                language=row["language"],
                editorial_notes=row["editorial_notes"],
                approved_at=row["approved_at"],
                approved_by=row["approved_by"],
                created_at=row["created_at"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")


@router.post("/articles/{article_id}/rewrite")
async def rewrite_article_with_llm(
    article_id: int,
    request: RewriteRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Trigger LLM French rewrite for an article.

    Uses the NewsPublisher._rewrite_with_llm() method to:
    1. Translate/rewrite content to French with editorial style
    2. Save result to french_content_md column
    3. Update editorial_status to 'rewritten'
    """
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            # Get article
            row = conn.execute(
                "SELECT id, title, content_md, language FROM news_articles WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            # Prepare payload for rewriting
            raw_payload = {
                "title": row["title"],
                "content": row["content_md"],
                "summary": None
            }

            # Get publisher and rewrite
            pub = get_publisher()
            rewrite_result = pub._rewrite_with_llm(raw_payload, request.source_language)

            if not rewrite_result:
                raise HTTPException(status_code=500, detail="LLM rewriting failed or unavailable")

            if rewrite_result.get("skip"):
                raise HTTPException(
                    status_code=400,
                    detail="Article was skipped by editorial filter (not economics-related)"
                )

            # Extract French content
            french_content = rewrite_result.get("content_md", "")
            if not french_content:
                raise HTTPException(status_code=500, detail="LLM did not return content")

            # Update article with rewritten content
            conn.execute(
                """
                UPDATE news_articles
                SET french_content_md = ?, editorial_status = 'rewritten', updated_at = datetime('now')
                WHERE id = ?
                """,
                (french_content, article_id)
            )

            # Log activity
            _log_activity(
                conn, "rewrite", "article", article_id,
                f"LLM rewrite completed ({request.source_language} → fr)"
            )

            return {
                "status": "success",
                "article_id": article_id,
                "editorial_status": "rewritten",
                "french_content_length": len(french_content),
                "metadata": {
                    "title_fr": rewrite_result.get("title_fr"),
                    "excerpt_fr": rewrite_result.get("excerpt_fr"),
                    "category": rewrite_result.get("category"),
                    "sentiment": rewrite_result.get("sentiment")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rewrite failed for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)}")


@router.put("/articles/{article_id}/french-content")
async def update_french_content(
    article_id: int,
    request: UpdateFrenchContentRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Save manually edited French content.

    Allows admins to update the french_content_md with manual edits.
    """
    require_admin(admin_key)

    if not request.french_content_md or len(request.french_content_md.strip()) == 0:
        raise HTTPException(status_code=400, detail="French content cannot be empty")

    try:
        with db._get_conn() as conn:
            # Get article
            row = conn.execute(
                "SELECT id FROM news_articles WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            # Update French content
            conn.execute(
                """
                UPDATE news_articles
                SET french_content_md = ?, editorial_status = 'rewritten', updated_at = datetime('now')
                WHERE id = ?
                """,
                (request.french_content_md, article_id)
            )

            # Log activity
            _log_activity(
                conn, "update_french", "article", article_id,
                request.editorial_notes or "Manual French content update"
            )

            return {
                "status": "success",
                "article_id": article_id,
                "editorial_status": "rewritten"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update French content for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@router.post("/articles/{article_id}/validate")
async def validate_article(
    article_id: int,
    request: ValidateRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Mark article as validated/approved.

    Updates editorial_status to 'validated' and records approval info.
    """
    require_admin(admin_key)

    if not request.approved_by or len(request.approved_by.strip()) == 0:
        raise HTTPException(status_code=400, detail="approved_by is required")

    try:
        with db._get_conn() as conn:
            # Get article
            row = conn.execute(
                "SELECT id, french_content_md FROM news_articles WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            # Check that french content exists
            if not row["french_content_md"]:
                raise HTTPException(
                    status_code=400,
                    detail="Article must have French content before validation"
                )

            # Update validation status
            conn.execute(
                """
                UPDATE news_articles
                SET editorial_status = 'validated', approved_by = ?, approved_at = datetime('now'),
                    editorial_notes = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (request.approved_by, request.editorial_notes or "", article_id)
            )

            # Log activity
            _log_activity(
                conn, "validate", "article", article_id,
                f"Validated by {request.approved_by}: {request.editorial_notes or ''}"
            )

            return {
                "status": "success",
                "article_id": article_id,
                "editorial_status": "validated",
                "approved_by": request.approved_by,
                "approved_at": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/articles/{article_id}/publish-final")
async def publish_article_final(
    article_id: int,
    request: PublishRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Final publication of article.

    Sets editorial_status to 'published' and status to 'published'.
    Logs to admin_activity_log.
    """
    require_admin(admin_key)

    if not request.approved_by or len(request.approved_by.strip()) == 0:
        raise HTTPException(status_code=400, detail="approved_by is required")

    try:
        with db._get_conn() as conn:
            # Get article
            row = conn.execute(
                "SELECT id, title, french_content_md FROM news_articles WHERE id = ?",
                (article_id,)
            ).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Article not found")

            # Publish the article
            conn.execute(
                """
                UPDATE news_articles
                SET editorial_status = 'published', status = 'published',
                    approved_by = ?, approved_at = datetime('now'),
                    editorial_notes = ?, updated_at = datetime('now')
                WHERE id = ?
                """,
                (request.approved_by, request.editorial_notes or "", article_id)
            )

            # Log activity
            _log_activity(
                conn, "publish", "article", article_id,
                f"Published by {request.approved_by}: {request.editorial_notes or ''}"
            )

            return {
                "status": "success",
                "article_id": article_id,
                "editorial_status": "published",
                "status": "published",
                "approved_by": request.approved_by,
                "published_at": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publication failed for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Publication failed: {str(e)}")


@router.post("/articles/batch", response_model=BatchActionResponse)
async def batch_article_action(
    request: BatchActionRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Batch operations on multiple articles (publish, reject, validate).

    Returns summary of successful and failed operations.
    """
    require_admin(admin_key)

    if not request.article_ids or len(request.article_ids) == 0:
        raise HTTPException(status_code=400, detail="No article IDs provided")

    if request.action not in ["publish", "reject", "validate"]:
        raise HTTPException(status_code=400, detail="Invalid action")

    successful = 0
    failed = 0
    errors = []

    try:
        with db._get_conn() as conn:
            for article_id in request.article_ids:
                try:
                    if request.action == "publish":
                        _batch_publish_article(
                            conn, article_id, request.approved_by,
                            request.editorial_notes
                        )
                    elif request.action == "validate":
                        _batch_validate_article(
                            conn, article_id, request.approved_by,
                            request.editorial_notes
                        )
                    elif request.action == "reject":
                        _batch_reject_article(
                            conn, article_id, request.approved_by,
                            request.editorial_notes
                        )

                    successful += 1
                except Exception as e:
                    failed += 1
                    errors.append({
                        "article_id": article_id,
                        "error": str(e)
                    })
                    logger.warning(f"Batch action failed for article {article_id}: {e}")

    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch operation failed: {str(e)}")

    return BatchActionResponse(
        action=request.action,
        total=len(request.article_ids),
        successful=successful,
        failed=failed,
        errors=errors
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _log_activity(
    conn,
    action: str,
    resource_type: str,
    resource_id: str,
    details: str,
    admin_id: str = "admin"
):
    """Log admin activity."""
    try:
        conn.execute(
            """
            INSERT INTO admin_activity_log (admin_id, action, resource_type, resource_id, details, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (admin_id, action, resource_type, str(resource_id), details)
        )
    except Exception as e:
        logger.warning(f"Failed to log activity: {e}")


def _batch_publish_article(conn, article_id: int, approved_by: str, notes: Optional[str]):
    """Helper to publish article in batch."""
    conn.execute(
        """
        UPDATE news_articles
        SET editorial_status = 'published', status = 'published',
            approved_by = ?, approved_at = datetime('now'),
            editorial_notes = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (approved_by, notes or "", article_id)
    )
    _log_activity(conn, "batch_publish", "article", article_id, f"Batch published by {approved_by}")


def _batch_validate_article(conn, article_id: int, approved_by: str, notes: Optional[str]):
    """Helper to validate article in batch."""
    conn.execute(
        """
        UPDATE news_articles
        SET editorial_status = 'validated', approved_by = ?, approved_at = datetime('now'),
            editorial_notes = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (approved_by, notes or "", article_id)
    )
    _log_activity(conn, "batch_validate", "article", article_id, f"Batch validated by {approved_by}")


def _batch_reject_article(conn, article_id: int, approved_by: str, notes: Optional[str]):
    """Helper to reject article in batch."""
    conn.execute(
        """
        UPDATE news_articles
        SET status = 'rejected', approved_by = ?, approved_at = datetime('now'),
            editorial_notes = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (approved_by, notes or "", article_id)
    )
    _log_activity(conn, "batch_reject", "article", article_id, f"Batch rejected by {approved_by}")


# ═══════════════════════════════════════════════════════════════════════════════
# Activity Log Endpoint
# ═══════════════════════════════════════════════════════════════════════════════

class ActivityLogEntry(BaseModel):
    """Single activity log entry."""
    id: int
    admin_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Optional[str] = None
    changes_json: Optional[str] = None
    created_at: str


class ActivityLogResponse(BaseModel):
    """Activity log response with pagination."""
    entries: List[ActivityLogEntry]
    total: int
    limit: int
    offset: int


@router.get("/activity", response_model=ActivityLogResponse)
async def get_activity_log(
    admin_key: str = Header(None, alias="X-Admin-Key"),
    action: str = Query(None),
    resource_type: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Get paginated admin activity log with optional filtering.

    Query parameters:
    - action: Filter by action type (e.g., publish, reject, validate, rewrite, batch_publish, batch_reject, settings_update)
    - resource_type: Filter by resource type (e.g., article, script, source, settings)
    - limit: Number of entries per page (1-200, default 50)
    - offset: Number of entries to skip (default 0)

    Returns paginated activity log entries sorted by creation time (newest first).
    """
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            # Build WHERE clause dynamically
            where_conditions = []
            params = []

            if action:
                where_conditions.append("action = ?")
                params.append(action)

            if resource_type:
                where_conditions.append("resource_type = ?")
                params.append(resource_type)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) as count FROM admin_activity_log WHERE {where_clause}"
            count_row = conn.execute(count_query, params).fetchone()
            total = count_row["count"] if count_row else 0

            # Get paginated entries (newest first)
            query = f"""
                SELECT id, admin_id, action, resource_type, resource_id, details, changes_json, created_at
                FROM admin_activity_log
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            query_params = params + [limit, offset]
            rows = conn.execute(query, query_params).fetchall()

            entries = [
                ActivityLogEntry(
                    id=row["id"],
                    admin_id=row["admin_id"],
                    action=row["action"],
                    resource_type=row["resource_type"],
                    resource_id=row["resource_id"],
                    details=row["details"],
                    changes_json=row["changes_json"],
                    created_at=row["created_at"]
                )
                for row in rows
            ]

            return ActivityLogResponse(
                entries=entries,
                total=total,
                limit=limit,
                offset=offset
            )

    except Exception as e:
        logger.error(f"Failed to get activity log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve activity log: {str(e)}")
