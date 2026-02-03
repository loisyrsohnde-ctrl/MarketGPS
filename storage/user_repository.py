"""
User Repository - Manages user accounts and profiles.
"""
import sqlite3
import uuid
from typing import Optional, Dict

from storage.base_repository import BaseRepository
from core.config import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository):
    """Repository for user operations."""

    def create_user(self, email: str, password_hash: str) -> Optional[str]:
        """Create a new user and return user_id."""
        user_id = str(uuid.uuid4())

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (user_id, email, password_hash, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                """, (user_id, email.lower().strip(), password_hash))

                # Create default profile
                conn.execute("""
                    INSERT INTO user_profiles (user_id, display_name, created_at)
                    VALUES (?, ?, datetime('now'))
                """, (user_id, email.split('@')[0]))

                # Create default subscription (free)
                conn.execute("""
                    INSERT INTO subscriptions_state (user_id, plan, status, daily_quota_limit, created_at)
                    VALUES (?, 'free', 'active', 3, datetime('now'))
                """, (user_id,))

                # Create default user settings
                conn.execute("""
                    INSERT INTO user_settings (user_id, created_at)
                    VALUES (?, datetime('now'))
                """, (user_id,))

            logger.info(f"Created user {user_id} for {email}")
            return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"User with email {email} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email.lower().strip(),)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_last_login(self, user_id: str):
        """Update last login timestamp."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = datetime('now') WHERE user_id = ?",
                (user_id,)
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # USER PROFILES (NEW v12)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get user profile with subscription info."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT p.*, u.email, s.plan, s.status as subscription_status,
                       s.daily_quota_used, s.daily_quota_limit
                FROM user_profiles p
                JOIN users u ON p.user_id = u.user_id
                LEFT JOIN subscriptions_state s ON p.user_id = s.user_id
                WHERE p.user_id = ?
            """, (user_id,)).fetchone()
            return dict(row) if row else None

    def update_user_profile(self, user_id: str, display_name: str = None, avatar_path: str = None, bio: str = None) -> bool:
        """Update user profile."""
        try:
            updates = []
            params = []

            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            if avatar_path is not None:
                updates.append("avatar_path = ?")
                params.append(avatar_path)
            if bio is not None:
                updates.append("bio = ?")
                params.append(bio)

            if not updates:
                return True

            updates.append("updated_at = datetime('now')")
            params.append(user_id)

            with self._get_connection() as conn:
                conn.execute(f"""
                    UPDATE user_profiles SET {', '.join(updates)}
                    WHERE user_id = ?
                """, params)
            return True
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            return False
