"""
Standardized authentication dependencies for all MarketGPS routes.

Provides consistent, reusable FastAPI dependencies for authentication across all route files.
This module replaces the scattered auth patterns (get_current_user_id, _resolve_user_id, etc.)
with a unified interface.

Usage in route files:
    from auth_dependencies import require_auth, optional_auth, require_admin, resolve_user_id

    @router.get("/protected")
    async def protected(user_id: str = Depends(require_auth)):
        '''Requires valid token, returns user_id. Raises 401 if missing/invalid.'''
        ...

    @router.get("/public-with-optional-auth")
    async def public(user_id: Optional[str] = Depends(optional_auth)):
        '''Returns user_id if valid token present, None otherwise. Never raises.'''
        ...

    @router.get("/admin-only")
    async def admin(user_id: str = Depends(require_admin)):
        '''Requires valid token AND admin status. Raises 401 or 403 if not admin.'''
        ...

    @router.get("/mixed")
    async def mixed(user_id: str = Depends(resolve_user_id)):
        '''For backward compat: returns user_id if token present, fallback to "default_user".'''
        ...
"""

import os
import logging
from typing import Optional

from fastapi import HTTPException, Header

from security import verify_supabase_token, is_auth_required

logger = logging.getLogger(__name__)


def _extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    Returns None if header is missing or malformed.
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def require_auth(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Requires valid authentication token. Returns user_id.
    Raises 401 HTTPException if token is missing, invalid, or expired.

    Use this for protected endpoints that require authentication.
    """
    if not authorization:
        logger.debug("Authentication required but Authorization header missing")
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = _extract_token_from_header(authorization)
    if not token:
        logger.debug("Authorization header present but malformed")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_supabase_token(token)
    if not payload:
        logger.debug("Token verification failed")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        logger.warning("Token missing user ID claim")
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authentication successful for user: {user_id}")
    return user_id


def optional_auth(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[str]:
    """
    Optional authentication. Returns user_id if valid token present, None otherwise.
    Never raises HTTPException - gracefully handles missing or invalid tokens.

    Use this for endpoints that work with or without authentication.
    """
    if not authorization:
        logger.debug("No Authorization header provided (optional auth)")
        return None

    token = _extract_token_from_header(authorization)
    if not token:
        logger.debug("Authorization header malformed, treating as unauthenticated")
        return None

    payload = verify_supabase_token(token)
    if not payload:
        logger.debug("Token verification failed, treating as unauthenticated")
        return None

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        logger.debug("Token missing user ID claim, treating as unauthenticated")
        return None

    logger.debug(f"Optional authentication successful for user: {user_id}")
    return user_id


def require_admin(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Requires valid authentication token AND admin status.
    Returns user_id if authorized.
    Raises 401 if token is invalid, 403 if user is not admin.

    Admin status is determined by ADMIN_USER_IDS environment variable
    (comma-separated list of user IDs with admin privileges).

    Use this for admin-only endpoints.
    """
    # First verify authentication
    if not authorization:
        logger.warning("Admin access attempted without Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = _extract_token_from_header(authorization)
    if not token:
        logger.warning("Admin access attempted with malformed Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_supabase_token(token)
    if not payload:
        logger.warning("Admin access attempted with invalid token")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        logger.warning("Admin token missing user ID claim")
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Now check admin status
    admin_user_ids = os.environ.get("ADMIN_USER_IDS", "").split(",")
    admin_user_ids = [uid.strip() for uid in admin_user_ids if uid.strip()]

    if user_id not in admin_user_ids:
        logger.warning(f"Non-admin user {user_id} attempted admin access")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required for this endpoint",
        )

    logger.info(f"Admin access granted for user: {user_id}")
    return user_id


def resolve_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Resolve user_id from Authorization header with development fallback.
    Returns user_id from token if present, falls back to "default_user" in dev mode.

    This function provides backward compatibility for routes using _resolve_user_id pattern.
    In production (AUTH_REQUIRED=true), missing/invalid tokens are rejected.
    In development, missing/invalid tokens return "default_user" for testing.

    Use this for backward compatibility. New endpoints should prefer require_auth()
    or optional_auth() instead.
    """
    auth_required = is_auth_required()

    if not authorization:
        if auth_required:
            logger.debug("User ID resolution required but Authorization header missing")
            raise HTTPException(
                status_code=401,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug("No Authorization header, using fallback: 'default_user'")
        return "default_user"

    token = _extract_token_from_header(authorization)
    if not token:
        if auth_required:
            logger.debug("Authorization header malformed in auth-required mode")
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format. Expected: 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug("Malformed Authorization header, using fallback: 'default_user'")
        return "default_user"

    payload = verify_supabase_token(token)
    if not payload:
        if auth_required:
            logger.debug("Token verification failed in auth-required mode")
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug("Token verification failed, using fallback: 'default_user'")
        return "default_user"

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        if auth_required:
            logger.warning("Token missing user ID claim in auth-required mode")
            raise HTTPException(
                status_code=401,
                detail="Token missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.debug("Token missing user ID, using fallback: 'default_user'")
        return "default_user"

    logger.debug(f"User ID resolved: {user_id}")
    return user_id
