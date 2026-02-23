"""
MarketGPS - Admin AI Quota Endpoints

All AI quota management endpoints: list, exhausted, per-user, update, disable, enable, reset.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Query

from .shared import (
    logger,
    AIQuotaUpdate,
    require_admin,
)

from ai_quota_service import get_ai_quota_service

router = APIRouter()


@router.get("/ai-quotas")
async def list_ai_quotas(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all AI quota records.
    Shows usage statistics for OpenAI and Gemini per user.
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()
        quotas = quota_service.get_all_quotas(limit=limit, offset=offset)

        return {
            "quotas": quotas,
            "count": len(quotas),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error listing AI quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-quotas/exhausted")
async def list_exhausted_quotas(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    List users who have exhausted their AI quotas.
    Useful for identifying users who may need quota renewal.
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()
        exhausted = quota_service.get_exhausted_users()

        return {
            "exhausted_users": exhausted,
            "count": len(exhausted),
        }
    except Exception as e:
        logger.error(f"Error listing exhausted quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-quotas/user/{user_id}")
async def get_user_ai_quotas(
    user_id: str,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get AI quota information for a specific user.
    Shows OpenAI and Gemini quota status.
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()
        quotas = quota_service.get_user_quotas(user_id)

        return {
            "user_id": user_id,
            "quotas": quotas,
        }
    except Exception as e:
        logger.error(f"Error getting user quotas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/update")
async def update_ai_quota(
    request: AIQuotaUpdate,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Update AI quota for a user.

    Actions:
    - disable_limit: Remove quota limit (unlimited usage)
    - enable_limit: Re-enable quota limit
    - reset: Reset usage counter to 0
    - set_limit: Set a custom limit (requires new_limit parameter)

    Provider:
    - openai: ChatGPT/OpenAI quota only
    - gemini: Google Gemini quota only
    - all: Both OpenAI and Gemini
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()

        # Validate provider
        if request.provider not in ["openai", "gemini", "all"]:
            raise HTTPException(status_code=400, detail="Provider must be 'openai', 'gemini', or 'all'")

        # Validate action
        valid_actions = ["disable_limit", "enable_limit", "reset", "set_limit"]
        if request.action not in valid_actions:
            raise HTTPException(status_code=400, detail=f"Action must be one of: {valid_actions}")

        # Execute action
        providers = ["openai", "gemini"] if request.provider == "all" else [request.provider]
        results = {}

        for provider in providers:
            if request.action == "disable_limit":
                quota_service.set_limit_disabled(request.user_id, provider, True)
                results[provider] = "Limite d\u00e9sactiv\u00e9e (illimit\u00e9)"

            elif request.action == "enable_limit":
                quota_service.set_limit_disabled(request.user_id, provider, False)
                results[provider] = "Limite activ\u00e9e"

            elif request.action == "reset":
                quota_service.reset_user_quota(request.user_id, provider)
                results[provider] = "Quota r\u00e9initialis\u00e9 \u00e0 0"

            elif request.action == "set_limit":
                if request.new_limit is None or request.new_limit < 0:
                    raise HTTPException(status_code=400, detail="new_limit is required for set_limit action")
                quota_service.set_user_limit(request.user_id, provider, request.new_limit)
                results[provider] = f"Nouvelle limite: {request.new_limit}"

        logger.info(f"AI quota updated for user {request.user_id}: {request.action} on {request.provider}")

        return {
            "success": True,
            "user_id": request.user_id,
            "action": request.action,
            "provider": request.provider,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating AI quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/disable-limit/{user_id}")
async def disable_user_ai_limit(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Quick endpoint to disable AI quota limit for a user.
    User will have unlimited AI requests.
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()

        if provider == "all":
            quota_service.set_limit_disabled_all(user_id, True)
        else:
            quota_service.set_limit_disabled(user_id, provider, True)

        logger.info(f"AI quota limit disabled for user {user_id} on {provider}")

        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Limite IA d\u00e9sactiv\u00e9e pour {provider}. L'utilisateur a maintenant un acc\u00e8s illimit\u00e9.",
        }
    except Exception as e:
        logger.error(f"Error disabling AI limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/enable-limit/{user_id}")
async def enable_user_ai_limit(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Quick endpoint to re-enable AI quota limit for a user.
    User will be subject to normal quota limits (50 requests).
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()

        if provider == "all":
            quota_service.set_limit_disabled_all(user_id, False)
        else:
            quota_service.set_limit_disabled(user_id, provider, False)

        logger.info(f"AI quota limit enabled for user {user_id} on {provider}")

        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Limite IA activ\u00e9e pour {provider}. L'utilisateur est maintenant soumis aux quotas.",
        }
    except Exception as e:
        logger.error(f"Error enabling AI limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-quotas/reset/{user_id}")
async def reset_user_ai_quota(
    user_id: str,
    provider: str = Query("all", description="openai, gemini, or all"),
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Reset AI quota usage for a user.
    Sets their usage counter back to 0.
    """
    require_admin(admin_key)

    try:
        quota_service = get_ai_quota_service()

        if provider == "all":
            quota_service.reset_user_all_quotas(user_id)
        else:
            quota_service.reset_user_quota(user_id, provider)

        logger.info(f"AI quota reset for user {user_id} on {provider}")

        return {
            "success": True,
            "user_id": user_id,
            "provider": provider,
            "message": f"Quota IA r\u00e9initialis\u00e9 pour {provider}. L'utilisateur a \u00e0 nouveau 50 requ\u00eates disponibles.",
        }
    except Exception as e:
        logger.error(f"Error resetting AI quota: {e}")
        raise HTTPException(status_code=500, detail=str(e))
