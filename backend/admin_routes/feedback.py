"""
MarketGPS - Admin Feedback Endpoints

List feedbacks received.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Query

from .shared import (
    db, logger,
    FeedbackSummary,
    require_admin,
)

router = APIRouter()


@router.get("/feedbacks", response_model=List[FeedbackSummary])
async def list_feedbacks(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    status: Optional[str] = Query(None, description="Filter by status: new, reviewed, resolved"),
    feedback_type: Optional[str] = Query(None, alias="type", description="Filter by type: bug, feature, general"),
    limit: int = Query(50, ge=1, le=500),
):
    """
    List all feedbacks received.
    READ-ONLY: Does not modify any data.
    """
    require_admin(admin_key)

    try:
        feedbacks = []

        with db._get_conn() as conn:
            query = "SELECT id, type, subject, message, user_email, rating, platform, status, created_at FROM feedback WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if feedback_type:
                query += " AND type = ?"
                params.append(feedback_type)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            try:
                cursor = conn.execute(query, params)
                for row in cursor.fetchall():
                    feedbacks.append(FeedbackSummary(
                        id=row[0],
                        type=row[1] or "general",
                        subject=row[2],
                        message=row[3] or "",
                        user_email=row[4],
                        rating=row[5],
                        platform=row[6],
                        status=row[7] or "new",
                        created_at=row[8] or "",
                    ))
            except Exception as e:
                logger.warning(f"feedback table query failed: {e}")

        return feedbacks

    except Exception as e:
        logger.error(f"Error listing feedbacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
