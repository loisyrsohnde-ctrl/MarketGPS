"""
Security utilities for MarketGPS Backend
JWT verification for Supabase tokens
"""

import os
import logging
import time
import hashlib
from typing import Optional, Tuple

from fastapi import HTTPException, Header, Depends
from jose import jwt, JWTError
import httpx

logger = logging.getLogger(__name__)

# Supabase JWT settings
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = None  # Will be fetched from Supabase or use anon key verification

# JWT Token Cache: {token_hash: (payload, expiry_timestamp)}
_token_cache: dict = {}
_verify_count: int = 0
_CACHE_TTL = 300  # 5 minutes in seconds
_CLEANUP_THRESHOLD = 100  # Cleanup cache every 100 verifications


def _cleanup_cache() -> None:
    """
    Purge expired entries from token cache.
    Called periodically during verification to prevent unbounded memory growth.
    """
    global _token_cache
    current_time = time.time()
    expired_keys = [
        key for key, (_, expiry) in _token_cache.items()
        if expiry <= current_time
    ]
    for key in expired_keys:
        del _token_cache[key]

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired tokens from cache")


async def get_supabase_jwks() -> dict:
    """
    Fetch JWKS from Supabase for token verification.
    In practice, Supabase uses a simpler approach with the JWT secret.
    """
    # Supabase uses HS256 with the JWT secret from project settings
    # For this implementation, we'll verify using the anon key approach
    pass


def verify_supabase_token(token: str) -> Optional[dict]:
    """
    Verify a Supabase access token with in-memory caching (TTL: 5 minutes).

    Checks cache first for previously verified tokens to reduce verification overhead.
    Cache entries are automatically purged every 100 verifications.

    Returns: Decoded token payload or None if invalid
    """
    global _verify_count

    # Check cache first
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    current_time = time.time()

    if token_hash in _token_cache:
        payload, expiry = _token_cache[token_hash]
        if expiry > current_time:
            logger.debug(f"Token cache hit (expires in {expiry - current_time:.0f}s)")
            return payload
        else:
            # Expired cache entry
            del _token_cache[token_hash]

    # Token not in cache or expired, perform verification
    try:
        # Supabase JWT secret can be found in project settings
        # For now, we'll use the Supabase API to verify
        jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")

        # Debug: log token prefix for troubleshooting
        token_preview = token[:20] + "..." if len(token) > 20 else token
        logger.debug(f"Verifying token: {token_preview}, secret configured: {bool(jwt_secret)}")

        payload = None
        if jwt_secret:
            # Direct JWT verification with secret
            # Note: Supabase JWT may not have audience claim, so we don't verify it
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
            except JWTError as e:
                # Try without audience verification (Supabase tokens may not have it)
                logger.debug(f"JWT verification with audience failed, trying without: {e}")
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
        else:
            # Fallback: Verify by calling Supabase
            payload = _verify_token_via_supabase(token)

        # Cache successful verification
        if payload:
            expiry_time = current_time + _CACHE_TTL
            _token_cache[token_hash] = (payload, expiry_time)
            logger.debug(f"Token cached (hash: {token_hash[:8]}..., expires at {expiry_time})")

        # Periodic cleanup
        _verify_count += 1
        if _verify_count >= _CLEANUP_THRESHOLD:
            _cleanup_cache()
            _verify_count = 0

        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def is_auth_required() -> bool:
    """
    Determine if auth should be enforced.
    Set AUTH_REQUIRED=true or ENV/APP_ENV=production in production.
    """
    auth_required = os.environ.get("AUTH_REQUIRED", "").lower() in ("1", "true", "yes")
    env = os.environ.get("ENV", "").lower()
    app_env = os.environ.get("APP_ENV", "").lower()
    return auth_required or env in ("prod", "production") or app_env in ("prod", "production")


def get_user_id_from_request(
    authorization: Optional[str],
    fallback_user_id: str = "default_user",
) -> str:
    """
    Resolve user_id from Authorization header with a dev fallback.
    In production (auth required), missing/invalid tokens are rejected.
    """
    auth_required = is_auth_required()

    if not authorization:
        if auth_required:
            raise HTTPException(
                status_code=401,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return fallback_user_id

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        if auth_required:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return fallback_user_id

    token = parts[1]
    payload = verify_supabase_token(token)
    if not payload:
        if auth_required:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return fallback_user_id

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        if auth_required:
            raise HTTPException(
                status_code=401,
                detail="Token missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return fallback_user_id

    return user_id


def _verify_token_via_supabase(token: str) -> Optional[dict]:
    """
    Verify token by calling Supabase auth endpoint.
    """
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        anon_key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not anon_key:
            logger.error("Supabase credentials not configured")
            return None
        
        # Call Supabase to verify token (with timeout to prevent resource exhaustion)
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": anon_key,
                }
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "sub": user_data.get("id"),
                    "email": user_data.get("email"),
                    "role": "authenticated",
                }
            else:
                logger.warning(f"Supabase token verification failed: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Supabase verification error: {e}")
        return None


def get_current_user_id(
    authorization: str = Header(None, alias="Authorization"),
) -> str:
    """
    FastAPI dependency to extract and verify user ID from token.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            ...
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    payload = verify_supabase_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_optional_user_id(
    authorization: str = Header(None, alias="Authorization"),
) -> Optional[str]:
    """
    FastAPI dependency to optionally extract user ID.
    Returns None if no valid token provided.
    """
    if not authorization:
        return None
    
    try:
        return get_current_user_id(authorization)
    except HTTPException:
        return None
