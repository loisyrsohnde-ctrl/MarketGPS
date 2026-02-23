"""
MarketGPS - Centralized Admin Authentication

Single source of truth for admin key verification.
All admin-protected endpoints MUST use require_admin from this module.

Security features:
- No hardcoded fallback key (raises error if ADMIN_KEY not set)
- Timing-safe comparison (prevents timing attacks)
- Audit logging of all access attempts
"""

import os
import secrets
import logging
from typing import Optional
from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def _get_admin_key() -> str:
    """Get the admin key from environment. Raises if not configured."""
    key = os.environ.get("ADMIN_KEY", "")
    if not key:
        logger.error("ADMIN_KEY environment variable is not set")
        raise HTTPException(
            status_code=503,
            detail="Admin authentication not configured"
        )
    return key


def verify_admin(admin_key: Optional[str]) -> bool:
    """
    Verify admin access key using timing-safe comparison.

    Returns True if the key matches, False otherwise.
    Logs all verification attempts.
    """
    if not admin_key:
        logger.warning("Admin access attempt with no key provided")
        return False

    expected = _get_admin_key()
    is_valid = secrets.compare_digest(admin_key, expected)

    if is_valid:
        logger.info("Admin access granted")
    else:
        logger.warning("Admin access denied - invalid key")

    return is_valid


def require_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """FastAPI dependency to require admin access on any endpoint."""
    if not verify_admin(admin_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True
