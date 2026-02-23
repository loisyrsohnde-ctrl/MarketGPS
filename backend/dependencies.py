"""
Shared FastAPI dependencies for MarketGPS Backend.

Provides reusable Depends() callables for authentication,
admin access, and subscription tier checks.

Usage:
    from dependencies import require_auth, require_pro

    @router.get("/protected")
    async def protected(user_id: str = Depends(require_auth)):
        ...

    @router.get("/pro-only")
    async def pro_only(user_id: str = Depends(require_pro)):
        ...
"""

import os
import logging
from typing import Optional
from fastapi import Header, HTTPException, Depends

from security import verify_supabase_token, get_current_user_id, get_optional_user_id
from admin_auth import verify_admin

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Authentication Dependencies
# ═══════════════════════════════════════════════════════════════════════════

# Re-export existing dependencies for convenience
require_auth = get_current_user_id
optional_auth = get_optional_user_id


# ═══════════════════════════════════════════════════════════════════════════
# Admin Access Dependency
# ═══════════════════════════════════════════════════════════════════════════

def require_admin_access(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
) -> bool:
    """
    FastAPI dependency that requires a valid admin key.
    Raises 403 if the key is missing or invalid.
    """
    if not verify_admin(admin_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Subscription Tier Dependencies
# ═══════════════════════════════════════════════════════════════════════════

def _get_user_entitlements(user_id: str) -> dict:
    """Fetch user entitlements from database."""
    try:
        from supabase_admin import SupabaseAdmin
        admin = SupabaseAdmin()
        return admin.get_user_entitlements(user_id) or {}
    except Exception as e:
        logger.warning(f"Could not fetch entitlements for {user_id}: {e}")
        return {}


def require_pro(
    authorization: str = Header(None, alias="Authorization"),
) -> str:
    """
    FastAPI dependency that requires an authenticated PRO subscriber.
    Returns user_id if authorized.
    """
    user_id = get_current_user_id(authorization)
    entitlements = _get_user_entitlements(user_id)

    plan = entitlements.get("plan", "FREE").upper()
    status = entitlements.get("status", "inactive")

    if plan == "FREE" or status != "active":
        raise HTTPException(
            status_code=403,
            detail={
                "error": "subscription_required",
                "message": "This feature requires a PRO subscription",
                "current_plan": plan,
            }
        )

    return user_id


def require_subscription(min_tier: str = "PRO"):
    """
    Factory for subscription tier dependencies.

    Usage:
        @router.get("/premium")
        async def premium(user_id: str = Depends(require_subscription("PRO"))):
            ...
    """
    tier_levels = {"FREE": 0, "PRO": 1, "MONTHLY": 1, "YEARLY": 2}
    required_level = tier_levels.get(min_tier.upper(), 1)

    def _check_subscription(
        authorization: str = Header(None, alias="Authorization"),
    ) -> str:
        user_id = get_current_user_id(authorization)
        entitlements = _get_user_entitlements(user_id)

        plan = entitlements.get("plan", "FREE").upper()
        status = entitlements.get("status", "inactive")
        user_level = tier_levels.get(plan, 0)

        if status != "active" or user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "subscription_required",
                    "message": f"This feature requires a {min_tier} subscription",
                    "current_plan": plan,
                    "required_plan": min_tier,
                }
            )

        return user_id

    return _check_subscription
