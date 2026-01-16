"""
Security utilities for MarketGPS Backend
JWT verification for Supabase tokens
"""

import os
import logging
from typing import Optional

from fastapi import HTTPException, Header, Depends
from jose import jwt, JWTError
import httpx

logger = logging.getLogger(__name__)

# Supabase JWT settings
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_JWT_SECRET = None  # Will be fetched from Supabase or use anon key verification


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
    Verify a Supabase access token.
    
    Returns: Decoded token payload or None if invalid
    """
    try:
        # Supabase JWT secret can be found in project settings
        # For now, we'll use the Supabase API to verify
        jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
        
        if jwt_secret:
            # Direct JWT verification with secret
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            return payload
        else:
            # Fallback: Verify by calling Supabase
            return _verify_token_via_supabase(token)
            
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


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
        
        # Call Supabase to verify token
        with httpx.Client() as client:
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
