"""
MarketGPS - Feedback API Routes
Handles user feedback submission, storage in database, and email notifications.

Features:
- Save feedback to SQLite database
- Send email notification to admin
- Support different feedback types (bug, feature, general, etc.)
- Track feedback from both web and mobile apps
"""

import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteStore
from email_service import send_email, EMAIL_ENABLED, RESEND_API_KEY, EMAIL_FROM

logger = logging.getLogger(__name__)

# Initialize SQLite store
db = SQLiteStore()

# Create router
router = APIRouter(prefix="/feedback", tags=["Feedback"])

# Admin email to receive feedback
ADMIN_EMAIL = os.environ.get("FEEDBACK_EMAIL", "hello@realsohnde.com")


# ═══════════════════════════════════════════════════════════════════════════
# Database Setup
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_feedback_table():
    """Create feedback table if not exists."""
    with db._get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                user_email TEXT,
                type TEXT NOT NULL DEFAULT 'general',
                subject TEXT,
                message TEXT NOT NULL,
                rating INTEGER,
                app_version TEXT,
                platform TEXT,
                device_info TEXT,
                status TEXT DEFAULT 'new',
                admin_notes TEXT,
                email_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        logger.info("✅ Feedback table ready")


# Initialize table on module load
_ensure_feedback_table()


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class FeedbackSubmitRequest(BaseModel):
    type: str = "general"  # bug, feature, general, question, complaint, praise
    subject: Optional[str] = None
    message: str
    rating: Optional[int] = None  # 1-5 stars
    user_email: Optional[str] = None  # For non-authenticated users
    app_version: Optional[str] = None
    platform: Optional[str] = None  # web, ios, android
    device_info: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: str
    success: bool
    message: str
    email_sent: bool


class FeedbackItem(BaseModel):
    id: str
    user_id: Optional[str]
    user_email: Optional[str]
    type: str
    subject: Optional[str]
    message: str
    rating: Optional[int]
    platform: Optional[str]
    status: str
    created_at: str


class FeedbackListResponse(BaseModel):
    feedbacks: List[FeedbackItem]
    total: int


# ═══════════════════════════════════════════════════════════════════════════
# Email Template
# ═══════════════════════════════════════════════════════════════════════════

def get_feedback_email_template(
    feedback_id: str,
    feedback_type: str,
    subject: Optional[str],
    message: str,
    user_email: Optional[str],
    user_id: Optional[str],
    rating: Optional[int],
    platform: Optional[str],
    device_info: Optional[str],
    app_version: Optional[str],
) -> dict:
    """Generate HTML email template for feedback notification."""

    type_labels = {
        "bug": "Bug Report",
        "feature": "Feature Request",
        "general": "General Feedback",
        "question": "Question",
        "complaint": "Complaint",
        "praise": "Praise",
    }
    type_label = type_labels.get(feedback_type, feedback_type.title())

    type_colors = {
        "bug": "#ef4444",
        "feature": "#8b5cf6",
        "general": "#3b82f6",
        "question": "#f59e0b",
        "complaint": "#f97316",
        "praise": "#10b981",
    }
    type_color = type_colors.get(feedback_type, "#6b7280")

    rating_display = ""
    if rating:
        stars = "★" * rating + "☆" * (5 - rating)
        rating_display = f"""
        <tr>
            <td style="padding: 10px 0; color: #a3a3a3; font-size: 14px; border-bottom: 1px solid #333;">Note</td>
            <td style="padding: 10px 0; color: #fbbf24; font-size: 18px; text-align: right; border-bottom: 1px solid #333;">{stars}</td>
        </tr>
        """

    email_subject = f"[MarketGPS Feedback] {type_label}" + (f": {subject}" if subject else "")

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nouveau Feedback MarketGPS</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0a0a0a; color: #e5e5e5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #141414; border-radius: 16px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {type_color}; padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">
                                Nouveau Feedback
                            </h1>
                            <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                {type_label}
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px;">
                            <!-- Subject -->
                            {f'<h2 style="margin: 0 0 20px; color: #ffffff; font-size: 20px; font-weight: 600;">{subject}</h2>' if subject else ''}

                            <!-- Message -->
                            <div style="background-color: #1f1f1f; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                                <p style="margin: 0; color: #e5e5e5; font-size: 15px; line-height: 1.7; white-space: pre-wrap;">{message}</p>
                            </div>

                            <!-- Metadata -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1a1a1a; border-radius: 8px;">
                                <tr>
                                    <td style="padding: 15px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="padding: 8px 0; color: #a3a3a3; font-size: 13px; border-bottom: 1px solid #333;">ID</td>
                                                <td style="padding: 8px 0; color: #ffffff; font-size: 13px; text-align: right; border-bottom: 1px solid #333; font-family: monospace;">{feedback_id[:8]}...</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #a3a3a3; font-size: 13px; border-bottom: 1px solid #333;">Email</td>
                                                <td style="padding: 8px 0; color: #10b981; font-size: 13px; text-align: right; border-bottom: 1px solid #333;">
                                                    {f'<a href="mailto:{user_email}" style="color: #10b981;">{user_email}</a>' if user_email else '<span style="color: #6b7280;">Non fourni</span>'}
                                                </td>
                                            </tr>
                                            {rating_display}
                                            <tr>
                                                <td style="padding: 8px 0; color: #a3a3a3; font-size: 13px; border-bottom: 1px solid #333;">Plateforme</td>
                                                <td style="padding: 8px 0; color: #ffffff; font-size: 13px; text-align: right; border-bottom: 1px solid #333;">{platform or 'Non spécifié'}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #a3a3a3; font-size: 13px; border-bottom: 1px solid #333;">Version</td>
                                                <td style="padding: 8px 0; color: #ffffff; font-size: 13px; text-align: right; border-bottom: 1px solid #333;">{app_version or 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; color: #a3a3a3; font-size: 13px;">User ID</td>
                                                <td style="padding: 8px 0; color: #6b7280; font-size: 12px; text-align: right; font-family: monospace;">{user_id[:16] + '...' if user_id and len(user_id) > 16 else user_id or 'Anonymous'}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            {f'''
                            <!-- Device Info -->
                            <div style="margin-top: 15px; padding: 12px; background-color: #1a1a1a; border-radius: 8px;">
                                <p style="margin: 0; color: #6b7280; font-size: 12px; font-family: monospace;">{device_info}</p>
                            </div>
                            ''' if device_info else ''}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; background-color: #0f0f0f; text-align: center; border-top: 1px solid #262626;">
                            <p style="margin: 0; color: #525252; font-size: 12px;">
                                MarketGPS Feedback System
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    text = f"""
Nouveau Feedback MarketGPS - {type_label}

{f"Sujet: {subject}" if subject else ""}

Message:
{message}

---
ID: {feedback_id}
Email: {user_email or 'Non fourni'}
{f"Note: {'★' * rating}{'☆' * (5-rating)}" if rating else ""}
Plateforme: {platform or 'Non spécifié'}
Version: {app_version or 'N/A'}
User ID: {user_id or 'Anonymous'}
{f"Device: {device_info}" if device_info else ""}
"""

    return {
        "to": ADMIN_EMAIL,
        "subject": email_subject,
        "html": html,
        "text": text,
    }


# ═══════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════

def _get_user_id_optional(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract user_id from token if available, otherwise return None."""
    if not authorization:
        return None

    try:
        from security import verify_supabase_token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        payload = verify_supabase_token(parts[1])
        if payload:
            return payload.get("sub") or payload.get("user_id")
    except:
        pass

    return None


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackSubmitRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Submit user feedback.

    - Saves to database
    - Sends email notification to admin
    - Works for both authenticated and anonymous users
    """
    user_id = _get_user_id_optional(authorization)
    feedback_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # Validate
    if not request.message or len(request.message.strip()) < 3:
        raise HTTPException(status_code=400, detail="Message is required (minimum 3 characters)")

    if request.rating and (request.rating < 1 or request.rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Save to database
    try:
        with db._get_conn() as conn:
            conn.execute("""
                INSERT INTO feedback (
                    id, user_id, user_email, type, subject, message,
                    rating, app_version, platform, device_info,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id,
                user_id,
                request.user_email,
                request.type,
                request.subject,
                request.message.strip(),
                request.rating,
                request.app_version,
                request.platform,
                request.device_info,
                "new",
                now,
                now,
            ))
            conn.commit()
            logger.info(f"✅ Feedback saved: {feedback_id}")
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")

    # Send email notification
    email_sent = False
    try:
        template = get_feedback_email_template(
            feedback_id=feedback_id,
            feedback_type=request.type,
            subject=request.subject,
            message=request.message,
            user_email=request.user_email,
            user_id=user_id,
            rating=request.rating,
            platform=request.platform,
            device_info=request.device_info,
            app_version=request.app_version,
        )

        email_sent = send_email(
            to=template["to"],
            subject=template["subject"],
            html=template["html"],
            text=template["text"],
            tags=[{"name": "type", "value": "feedback"}],
        )

        # Update email_sent status
        if email_sent:
            with db._get_conn() as conn:
                conn.execute(
                    "UPDATE feedback SET email_sent = 1 WHERE id = ?",
                    (feedback_id,)
                )
                conn.commit()

    except Exception as e:
        logger.error(f"Failed to send feedback email: {e}")

    return FeedbackResponse(
        id=feedback_id,
        success=True,
        message="Merci pour votre feedback ! Nous l'avons bien reçu.",
        email_sent=email_sent,
    )


@router.get("/list", response_model=FeedbackListResponse)
async def list_feedbacks(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    List all feedbacks (admin only).
    """
    expected_key = os.environ.get("ADMIN_KEY", "marketgps-admin-2024")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        with db._get_conn() as conn:
            # Build query
            query = "SELECT id, user_id, user_email, type, subject, message, rating, platform, status, created_at FROM feedback WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if feedback_type:
                query += " AND type = ?"
                params.append(feedback_type)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Get total count
            count_query = "SELECT COUNT(*) FROM feedback WHERE 1=1"
            count_params = []
            if status:
                count_query += " AND status = ?"
                count_params.append(status)
            if feedback_type:
                count_query += " AND type = ?"
                count_params.append(feedback_type)

            total = conn.execute(count_query, count_params).fetchone()[0]

            feedbacks = [
                FeedbackItem(
                    id=row[0],
                    user_id=row[1],
                    user_email=row[2],
                    type=row[3],
                    subject=row[4],
                    message=row[5],
                    rating=row[6],
                    platform=row[7],
                    status=row[8],
                    created_at=row[9],
                )
                for row in rows
            ]

            return FeedbackListResponse(feedbacks=feedbacks, total=total)

    except Exception as e:
        logger.error(f"Failed to list feedbacks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-email")
async def test_feedback_email(
    to_email: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Test endpoint to send a test feedback email.
    Requires admin key for security.
    """
    expected_key = os.environ.get("ADMIN_KEY", "marketgps-admin-2024")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Admin access required")

    template = get_feedback_email_template(
        feedback_id="test-" + str(uuid.uuid4())[:8],
        feedback_type="general",
        subject="Test Feedback System",
        message="Ceci est un test du système de feedback MarketGPS.\n\nLe système fonctionne correctement si vous recevez cet email !",
        user_email="test@example.com",
        user_id="test-user-123",
        rating=5,
        platform="web",
        device_info="Test Device",
        app_version="1.0.0",
    )

    success = send_email(
        to=to_email,
        subject=template["subject"],
        html=template["html"],
        text=template["text"],
        tags=[{"name": "type", "value": "feedback_test"}],
    )

    return {
        "success": success,
        "to": to_email,
        "message": "Email envoyé avec succès !" if success else "Échec de l'envoi. Vérifiez RESEND_API_KEY.",
        "email_enabled": EMAIL_ENABLED,
        "resend_configured": bool(RESEND_API_KEY),
    }
