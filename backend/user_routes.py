"""
MarketGPS - User Settings API Routes
Manages user profile, security, and notification preferences.
Persists all changes to the database.
"""

from storage.sqlite_store import SQLiteStore
import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from security import get_user_id_from_request
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Initialize SQLite store
db = SQLiteStore()

# Create router - accessible at /users (included directly in main.py)
# Note: This router is included in main.py without /api prefix
# Endpoints: /users/profile, /users/notifications, etc.
router = APIRouter(prefix="/users", tags=["Users"])


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class UserProfile(BaseModel):
    id: str
    email: str
    displayName: str
    avatar: Optional[str] = None
    createdAt: str
    updatedAt: str


class UpdateProfileRequest(BaseModel):
    displayName: Optional[str] = None
    avatar: Optional[str] = None


class NotificationSettings(BaseModel):
    emailNotifications: bool
    marketAlerts: bool
    priceAlerts: bool
    portfolioUpdates: bool


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class DeleteAccountRequest(BaseModel):
    password: str


class UserEntitlements(BaseModel):
    plan: str
    status: str
    dailyRequestsLimit: int


class UserNotification(BaseModel):
    id: str
    type: str  # 'success', 'warning', 'info', 'alert'
    title: str
    description: str
    time: str
    read: bool


class MarkNotificationsReadRequest(BaseModel):
    notification_ids: Optional[list] = None  # If None, mark all as read


# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

def _get_user_id_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from authorization header (JWT) with dev fallback."""
    return get_user_id_from_request(authorization, fallback_user_id="default_user")


def _hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Profile Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/profile", response_model=UserProfile)
async def get_profile(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """
    Get user profile information.
    Fetches all profile data from the database.
    """
    try:
        with db._get_conn() as conn:
            # Get profile from user_profiles table (email is in users table or we use a default)
            cursor = conn.execute(
                """SELECT 
                     p.user_id, 
                     COALESCE(u.email, p.user_id || '@marketgps.io') as email,
                     p.display_name, 
                     p.avatar_path, 
                     p.created_at, 
                     p.updated_at 
                   FROM user_profiles p
                   LEFT JOIN users u ON p.user_id = u.user_id
                   WHERE p.user_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                # Create default profile if not exists
                now = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO user_profiles 
                       (user_id, display_name, created_at, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, "User", now, now)
                )

                # Also create security record
                conn.execute(
                    """INSERT OR IGNORE INTO user_security 
                       (user_id, password_hash, created_at, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, _hash_password("password"), now, now)
                )

                # Create preferences
                conn.execute(
                    """INSERT OR IGNORE INTO user_preferences
                       (user_id, email_notifications, market_alerts, price_alerts, portfolio_updates, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, 1, 1, 1, 1, now, now)
                )

                # Create entitlements
                conn.execute(
                    """INSERT OR IGNORE INTO user_entitlements
                       (user_id, plan, status, daily_requests_limit, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, "FREE", "active", 10, now, now)
                )

                conn.commit()
                return {
                    "id": user_id,
                    "email": f"{user_id}@marketgps.io",
                    "displayName": "User",
                    "avatar": None,
                    "createdAt": now,
                    "updatedAt": now,
                }

            return {
                "id": row[0],
                "email": row[1],
                "displayName": row[2],
                "avatar": row[3],
                "createdAt": row[4],
                "updatedAt": row[5],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/update", response_model=UserProfile)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Update user profile (name and/or avatar).
    Persists changes to the database.
    """
    try:
        now = datetime.now().isoformat()

        with db._get_conn() as conn:
            # Build update query dynamically
            updates = []
            values = []

            if request.displayName is not None:
                updates.append("display_name = ?")
                values.append(request.displayName)

            if request.avatar is not None:
                updates.append("avatar_path = ?")
                values.append(request.avatar)

            if not updates:
                raise HTTPException(
                    status_code=400, detail="No updates provided")

            updates.append("updated_at = ?")
            values.append(now)
            values.append(user_id)

            query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE user_id = ?"
            conn.execute(query, tuple(values))
            conn.commit()

            # Fetch and return updated profile
            cursor = conn.execute(
                """SELECT 
                     p.user_id, 
                     COALESCE(u.email, p.user_id || '@marketgps.io') as email,
                     p.display_name, 
                     p.avatar_path, 
                     p.created_at, 
                     p.updated_at 
                   FROM user_profiles p
                   LEFT JOIN users u ON p.user_id = u.user_id
                   WHERE p.user_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()

            # Create notification for profile update
            update_type = []
            if request.displayName is not None:
                update_type.append("nom")
            if request.avatar is not None:
                update_type.append("avatar")
            
            create_notification(
                user_id=user_id,
                type="success",
                title="Profil mis à jour",
                description=f"Votre {' et '.join(update_type)} a été modifié avec succès"
            )

            return {
                "id": row[0],
                "email": row[1],
                "displayName": row[2],
                "avatar": row[3],
                "createdAt": row[4],
                "updatedAt": row[5],
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/avatar/upload")
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Upload user avatar image.
    Supports JPG, PNG, GIF. Max 2MB.
    Saves to disk and updates database.
    """
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/gif"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="File must be JPG, PNG, or GIF"
            )

        # Validate file size
        contents = await file.read()
        if len(contents) > 2 * 1024 * 1024:  # 2MB
            raise HTTPException(
                status_code=400,
                detail="File size must not exceed 2MB"
            )

        # Save file to disk
        upload_dir = "data/uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate filename
        ext = file.filename.split(".")[-1] if file.filename else "jpg"
        filename = f"{user_id}_avatar.{ext}"
        filepath = os.path.join(upload_dir, filename)

        # Write file
        with open(filepath, "wb") as f:
            f.write(contents)

        avatar_url = f"/uploads/avatars/{filename}"

        # Update in database
        now = datetime.now().isoformat()
        with db._get_conn() as conn:
            conn.execute(
                """UPDATE user_profiles 
                   SET avatar_path = ?, updated_at = ? WHERE user_id = ?""",
                (avatar_url, now, user_id)
            )
            conn.commit()

        return {"url": avatar_url, "path": filepath}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Notification Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/notifications", response_model=NotificationSettings)
async def get_notifications(
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Get user notification preferences.
    Fetches settings from the database.
    """
    try:
        with db._get_conn() as conn:
            cursor = conn.execute(
                """SELECT email_notifications, market_alerts, price_alerts, portfolio_updates 
                   FROM user_preferences WHERE user_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                # Create default preferences
                now = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO user_preferences 
                       (user_id, email_notifications, market_alerts, price_alerts, portfolio_updates, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, True, True, True, True, now, now)
                )
                conn.commit()
                return {
                    "emailNotifications": True,
                    "marketAlerts": True,
                    "priceAlerts": True,
                    "portfolioUpdates": True,
                }

            return {
                "emailNotifications": bool(row[0]),
                "marketAlerts": bool(row[1]),
                "priceAlerts": bool(row[2]),
                "portfolioUpdates": bool(row[3]),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/update", response_model=NotificationSettings)
async def update_notifications(
    request: NotificationSettings,
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Update user notification preferences.
    Persists changes to the database.
    """
    try:
        now = datetime.now().isoformat()

        with db._get_conn() as conn:
            conn.execute(
                """UPDATE user_preferences 
                   SET email_notifications = ?, market_alerts = ?, price_alerts = ?, portfolio_updates = ?, updated_at = ?
                   WHERE user_id = ?""",
                (
                    request.emailNotifications,
                    request.marketAlerts,
                    request.priceAlerts,
                    request.portfolioUpdates,
                    now,
                    user_id,
                )
            )
            conn.commit()

        return request

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# Security Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/security/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Change user password.
    Validates current password and updates to new one.
    Persists to the database.
    """
    try:
        # Validate input
        if not request.currentPassword or not request.newPassword:
            raise HTTPException(
                status_code=400,
                detail="Current and new password are required"
            )

        if len(request.newPassword) < 8:
            raise HTTPException(
                status_code=400,
                detail="New password must be at least 8 characters"
            )

        with db._get_conn() as conn:
            # Get current password hash
            cursor = conn.execute(
                "SELECT password_hash FROM user_security WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                # Create security record if doesn't exist
                new_hash = _hash_password(request.newPassword)
                conn.execute(
                    """INSERT INTO user_security (user_id, password_hash, created_at, updated_at)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, new_hash, datetime.now().isoformat(),
                     datetime.now().isoformat())
                )
                conn.commit()
                return {"success": True}

            # Verify current password
            current_hash = _hash_password(request.currentPassword)
            if current_hash != row[0]:
                raise HTTPException(
                    status_code=401,
                    detail="Current password is incorrect"
                )

            # Hash and update new password
            new_hash = _hash_password(request.newPassword)
            conn.execute(
                "UPDATE user_security SET password_hash = ?, updated_at = ? WHERE user_id = ?",
                (new_hash, datetime.now().isoformat(), user_id)
            )
            conn.commit()

        # Create security notification
        create_notification(
            user_id=user_id,
            type="success",
            title="Mot de passe modifié",
            description="Votre mot de passe a été changé avec succès"
        )

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout(user_id: Optional[str] = Depends(_get_user_id_from_header)):
    """
    Logout user by clearing session.
    Persists logout to the database.
    """
    try:
        with db._get_conn() as conn:
            # Delete user sessions
            conn.execute(
                "DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            conn.commit()

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete-account")
async def delete_account(
    request: DeleteAccountRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Delete user account permanently.
    Requires password confirmation.
    Removes all user data from database.
    """
    try:
        # Verify password
        with db._get_conn() as conn:
            cursor = conn.execute(
                "SELECT password_hash FROM user_security WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                password_hash = _hash_password(request.password)
                if password_hash != row[0]:
                    raise HTTPException(
                        status_code=401,
                        detail="Password is incorrect"
                    )

            # Delete all user data
            conn.execute(
                "DELETE FROM user_profiles WHERE user_id = ?", (user_id,))
            conn.execute(
                "DELETE FROM user_security WHERE user_id = ?", (user_id,))
            conn.execute(
                "DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            conn.execute(
                "DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
            conn.commit()

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# User Notifications (Messages) Endpoints
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_notifications_table(conn):
    """Ensure the user_notifications table exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('success', 'warning', 'info', 'alert')),
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_user 
        ON user_notifications(user_id, created_at DESC)
    """)
    conn.commit()


def _format_time_ago(created_at: str) -> str:
    """Format a timestamp as human-readable relative time."""
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - created.replace(tzinfo=None)
        
        if diff.days > 30:
            return f"Il y a {diff.days // 30} mois"
        elif diff.days > 0:
            return f"Il y a {diff.days} jour{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"Il y a {minutes} min"
        else:
            return "À l'instant"
    except:
        return "Récemment"


@router.get("/notifications/messages", response_model=list)
async def get_notification_messages(
    user_id: Optional[str] = Depends(_get_user_id_from_header),
    limit: int = 20,
):
    """
    Get user notification messages (not preferences).
    Returns the most recent notifications.
    """
    try:
        with db._get_conn() as conn:
            _ensure_notifications_table(conn)
            
            cursor = conn.execute(
                """SELECT id, type, title, description, created_at, read 
                   FROM user_notifications 
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (user_id, limit)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "type": row[1],
                    "title": row[2],
                    "description": row[3],
                    "time": _format_time_ago(row[4]),
                    "read": bool(row[5]),
                }
                for row in rows
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/read")
async def mark_notifications_read(
    request: MarkNotificationsReadRequest,
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Mark notifications as read.
    If notification_ids is None, marks all user notifications as read.
    """
    try:
        with db._get_conn() as conn:
            _ensure_notifications_table(conn)
            
            if request.notification_ids:
                # Mark specific notifications as read
                placeholders = ','.join(['?' for _ in request.notification_ids])
                conn.execute(
                    f"""UPDATE user_notifications 
                       SET read = 1 
                       WHERE user_id = ? AND id IN ({placeholders})""",
                    (user_id, *request.notification_ids)
                )
            else:
                # Mark all as read
                conn.execute(
                    "UPDATE user_notifications SET read = 1 WHERE user_id = ?",
                    (user_id,)
                )
            conn.commit()
            
        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread-count")
async def get_unread_count(
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Get the count of unread notifications.
    Used for the badge in the UI.
    """
    try:
        with db._get_conn() as conn:
            _ensure_notifications_table(conn)
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM user_notifications WHERE user_id = ? AND read = 0",
                (user_id,)
            )
            row = cursor.fetchone()
            
            return {"count": row[0] if row else 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_notification(
    user_id: str,
    type: str,
    title: str,
    description: str,
) -> dict:
    """
    Create a new notification for a user.
    This is a utility function to be called from other parts of the application.
    """
    import uuid
    notification_id = str(uuid.uuid4())
    created_at = datetime.now().isoformat()
    
    with db._get_conn() as conn:
        _ensure_notifications_table(conn)
        
        conn.execute(
            """INSERT INTO user_notifications 
               (id, user_id, type, title, description, created_at, read)
               VALUES (?, ?, ?, ?, ?, ?, 0)""",
            (notification_id, user_id, type, title, description, created_at)
        )
        conn.commit()
    
    return {
        "id": notification_id,
        "type": type,
        "title": title,
        "description": description,
        "time": "À l'instant",
        "read": False,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Entitlements Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/entitlements", response_model=UserEntitlements)
async def get_entitlements(
    user_id: Optional[str] = Depends(_get_user_id_from_header),
):
    """
    Get user plan and entitlements.
    Returns subscription plan, status, and daily request limit.
    """
    try:
        with db._get_conn() as conn:
            cursor = conn.execute(
                """SELECT plan, status, daily_requests_limit 
                   FROM user_entitlements WHERE user_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()

            if not row:
                # Default to free plan
                return {
                    "plan": "FREE",
                    "status": "active",
                    "dailyRequestsLimit": 10,
                }

            return {
                "plan": row[0] or "FREE",
                "status": row[1] or "active",
                "dailyRequestsLimit": row[2] or 10,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
