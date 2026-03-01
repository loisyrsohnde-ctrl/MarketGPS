"""
MarketGPS - AI Quota Management Service
========================================
Manages usage limits for AI services (OpenAI/ChatGPT and Google Gemini).

Features:
- Track usage per user per AI provider
- Default limit: 50 requests per provider
- Admin can disable limits for specific users
- Automatic reset option (monthly)

Usage:
    from ai_quota_service import AIQuotaService
    
    quota_service = AIQuotaService()
    
    # Check and consume quota
    result = quota_service.check_and_consume(user_id, "openai")
    if not result["allowed"]:
        raise HTTPException(status_code=429, detail=result["message"])
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Literal
from enum import Enum


# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Default quota limits (free tier: 3 messages to create urgency → Pro)
DEFAULT_OPENAI_LIMIT = 3
DEFAULT_GEMINI_LIMIT = 3

# AI Provider types
AIProvider = Literal["openai", "gemini"]


# ═══════════════════════════════════════════════════════════════════════════════
# AI QUOTA SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class AIQuotaService:
    """
    Service to manage AI request quotas per user.
    
    Tracks usage for:
    - OpenAI (ChatGPT) - used for strategy generation
    - Gemini - used for AI concierge and visual inspection
    """
    
    def __init__(self):
        self.db = SQLiteStore()
        self._ensure_quota_table()
    
    def _ensure_quota_table(self):
        """Create the AI quota table if it doesn't exist."""
        with self.db._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL CHECK(provider IN ('openai', 'gemini')),
                    requests_used INTEGER DEFAULT 0,
                    requests_limit INTEGER DEFAULT 50,
                    limit_disabled INTEGER DEFAULT 0,
                    last_request_at TEXT,
                    reset_at TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(user_id, provider)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_quotas_user ON ai_quotas(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_quotas_provider ON ai_quotas(provider)")
            logger.info("✅ AI quotas table verified/created")
    
    def _get_or_create_quota(self, user_id: str, provider: AIProvider) -> Dict[str, Any]:
        """Get or create quota record for a user and provider."""
        default_limit = DEFAULT_OPENAI_LIMIT if provider == "openai" else DEFAULT_GEMINI_LIMIT
        
        with self.db._get_connection() as conn:
            # Try to get existing quota
            row = conn.execute("""
                SELECT * FROM ai_quotas WHERE user_id = ? AND provider = ?
            """, (user_id, provider)).fetchone()
            
            if row:
                return dict(row)
            
            # Create new quota record
            conn.execute("""
                INSERT INTO ai_quotas (user_id, provider, requests_used, requests_limit, limit_disabled)
                VALUES (?, ?, 0, ?, 0)
            """, (user_id, provider, default_limit))
            
            return {
                "user_id": user_id,
                "provider": provider,
                "requests_used": 0,
                "requests_limit": default_limit,
                "limit_disabled": 0,
                "last_request_at": None,
                "reset_at": None
            }
    
    def check_quota(self, user_id: str, provider: AIProvider) -> Dict[str, Any]:
        """
        Check if user has remaining quota for the given AI provider.
        
        Returns:
            {
                "allowed": bool,
                "remaining": int,
                "limit": int,
                "used": int,
                "limit_disabled": bool,
                "message": str (only if not allowed)
            }
        """
        quota = self._get_or_create_quota(user_id, provider)
        
        # Check if limit is disabled for this user
        if quota["limit_disabled"]:
            return {
                "allowed": True,
                "remaining": -1,  # Unlimited
                "limit": quota["requests_limit"],
                "used": quota["requests_used"],
                "limit_disabled": True
            }
        
        remaining = quota["requests_limit"] - quota["requests_used"]
        
        if remaining <= 0:
            provider_name = "ChatGPT (OpenAI)" if provider == "openai" else "Gemini"
            return {
                "allowed": False,
                "remaining": 0,
                "limit": quota["requests_limit"],
                "used": quota["requests_used"],
                "limit_disabled": False,
                "message": f"Vous avez épuisé vos {quota['requests_limit']} requêtes {provider_name}. "
                          f"Veuillez contacter le service client pour renouveler votre quota."
            }
        
        return {
            "allowed": True,
            "remaining": remaining,
            "limit": quota["requests_limit"],
            "used": quota["requests_used"],
            "limit_disabled": False
        }
    
    def consume_quota(self, user_id: str, provider: AIProvider) -> bool:
        """
        Consume one quota unit for the given provider.
        
        Returns True if successful, False if quota exhausted.
        """
        quota = self._get_or_create_quota(user_id, provider)
        
        # If limit is disabled, just track usage without blocking
        if quota["limit_disabled"]:
            with self.db._get_connection() as conn:
                conn.execute("""
                    UPDATE ai_quotas SET
                        requests_used = requests_used + 1,
                        last_request_at = datetime('now'),
                        updated_at = datetime('now')
                    WHERE user_id = ? AND provider = ?
                """, (user_id, provider))
            return True
        
        # Check if quota is available
        if quota["requests_used"] >= quota["requests_limit"]:
            return False
        
        # Consume quota
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE ai_quotas SET
                    requests_used = requests_used + 1,
                    last_request_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE user_id = ? AND provider = ?
            """, (user_id, provider))
        
        return True
    
    def check_and_consume(self, user_id: str, provider: AIProvider) -> Dict[str, Any]:
        """
        Check quota and consume if available. Combined operation for convenience.
        
        Returns:
            {
                "allowed": bool,
                "remaining": int (after consumption),
                "message": str (only if not allowed)
            }
        """
        check_result = self.check_quota(user_id, provider)
        
        if not check_result["allowed"]:
            return check_result
        
        # Consume quota
        self.consume_quota(user_id, provider)
        
        # Return updated remaining count
        new_remaining = check_result["remaining"] - 1 if check_result["remaining"] > 0 else -1
        
        return {
            "allowed": True,
            "remaining": new_remaining,
            "limit": check_result["limit"],
            "used": check_result["used"] + 1,
            "limit_disabled": check_result["limit_disabled"]
        }
    
    def get_user_quotas(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all quota information for a user."""
        openai_quota = self.check_quota(user_id, "openai")
        gemini_quota = self.check_quota(user_id, "gemini")
        
        return {
            "openai": openai_quota,
            "gemini": gemini_quota
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # ADMIN FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def set_limit_disabled(self, user_id: str, provider: AIProvider, disabled: bool) -> bool:
        """
        Enable or disable quota limit for a specific user and provider.
        
        Args:
            user_id: The user's ID
            provider: "openai" or "gemini"
            disabled: True to disable limit (unlimited), False to enable limit
        
        Returns:
            True if successful
        """
        # Ensure quota record exists
        self._get_or_create_quota(user_id, provider)
        
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE ai_quotas SET
                    limit_disabled = ?,
                    updated_at = datetime('now')
                WHERE user_id = ? AND provider = ?
            """, (1 if disabled else 0, user_id, provider))
        
        action = "désactivée" if disabled else "activée"
        logger.info(f"AI quota limit {action} for user {user_id} on {provider}")
        return True
    
    def set_limit_disabled_all(self, user_id: str, disabled: bool) -> bool:
        """
        Enable or disable quota limits for ALL providers for a user.
        """
        self.set_limit_disabled(user_id, "openai", disabled)
        self.set_limit_disabled(user_id, "gemini", disabled)
        return True
    
    def set_user_limit(self, user_id: str, provider: AIProvider, new_limit: int) -> bool:
        """
        Set a custom quota limit for a user and provider.
        """
        self._get_or_create_quota(user_id, provider)
        
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE ai_quotas SET
                    requests_limit = ?,
                    updated_at = datetime('now')
                WHERE user_id = ? AND provider = ?
            """, (new_limit, user_id, provider))
        
        logger.info(f"AI quota limit set to {new_limit} for user {user_id} on {provider}")
        return True
    
    def reset_user_quota(self, user_id: str, provider: AIProvider) -> bool:
        """
        Reset a user's quota usage to 0.
        """
        self._get_or_create_quota(user_id, provider)
        
        with self.db._get_connection() as conn:
            conn.execute("""
                UPDATE ai_quotas SET
                    requests_used = 0,
                    reset_at = datetime('now'),
                    updated_at = datetime('now')
                WHERE user_id = ? AND provider = ?
            """, (user_id, provider))
        
        logger.info(f"AI quota reset for user {user_id} on {provider}")
        return True
    
    def reset_user_all_quotas(self, user_id: str) -> bool:
        """Reset all quotas for a user."""
        self.reset_user_quota(user_id, "openai")
        self.reset_user_quota(user_id, "gemini")
        return True
    
    def get_all_quotas(self, limit: int = 100, offset: int = 0) -> list:
        """
        Get all quota records (for admin dashboard).
        """
        with self.db._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM ai_quotas
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_exhausted_users(self) -> list:
        """
        Get list of users who have exhausted their quotas.
        """
        with self.db._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM ai_quotas
                WHERE limit_disabled = 0 AND requests_used >= requests_limit
                ORDER BY updated_at DESC
            """).fetchall()
            
            return [dict(row) for row in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_quota_service_instance = None

def get_ai_quota_service() -> AIQuotaService:
    """Get or create the singleton AI quota service instance."""
    global _quota_service_instance
    if _quota_service_instance is None:
        _quota_service_instance = AIQuotaService()
    return _quota_service_instance


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR EASY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def check_openai_quota(user_id: str) -> Dict[str, Any]:
    """Check OpenAI quota for a user. Returns dict with 'allowed' key."""
    return get_ai_quota_service().check_and_consume(user_id, "openai")


def check_gemini_quota(user_id: str) -> Dict[str, Any]:
    """Check Gemini quota for a user. Returns dict with 'allowed' key."""
    return get_ai_quota_service().check_and_consume(user_id, "gemini")


def get_quota_exhausted_message(provider: AIProvider) -> str:
    """Get the standard message for exhausted quota."""
    provider_name = "ChatGPT (OpenAI)" if provider == "openai" else "Gemini"
    return (
        f"Vous avez épuisé vos requêtes {provider_name}. "
        f"Veuillez contacter le service client pour renouveler votre quota."
    )
