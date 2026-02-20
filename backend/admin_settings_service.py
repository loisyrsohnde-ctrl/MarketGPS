"""
MarketGPS Admin - Settings Persistence Service

Manages global admin settings stored in app_settings table (key-value pairs).
Provides endpoints to:
- Get all settings as JSON
- Update settings (accepts partial updates)
"""

import os
import logging
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from datetime import datetime

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore
from core.config import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/admin", tags=["Admin Settings"])

# Database store
db = SQLiteStore()


# ═══════════════════════════════════════════════════════════════════════════════
# Database Initialization
# ═══════════════════════════════════════════════════════════════════════════════

def _ensure_app_settings_table():
    """Create app_settings table if it doesn't exist."""
    try:
        with db._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("app_settings table initialized")
    except Exception as e:
        logger.error(f"Error creating app_settings table: {e}")

# Initialize table on module load
_ensure_app_settings_table()


# ═══════════════════════════════════════════════════════════════════════════════
# Admin Key Verification
# ═══════════════════════════════════════════════════════════════════════════════

def verify_admin(admin_key: Optional[str]) -> bool:
    """Verify admin access key."""
    expected = os.environ.get("ADMIN_KEY", "marketgps-admin-2024")
    return admin_key == expected


def require_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Dependency to require admin access."""
    if not verify_admin(admin_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ═══════════════════════════════════════════════════════════════════════════════

class SettingsResponse(BaseModel):
    """Settings response with all key-value pairs."""
    settings: Dict[str, Any]
    updated_at: Optional[str] = None


class UpdateSettingsRequest(BaseModel):
    """Request to update settings (partial update)."""
    settings: Dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════════
# Default Settings
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_SETTINGS = {
    "pro_mode_enabled": "false",
    "default_top_n": "50",
    "refresh_interval_minutes": "15",
    "tier1_size": "100",
    "tier2_batch_size": "50",
    "daily_quota_free": "10",
    "daily_quota_pro": "200",
    "daily_quota_premium": "2000",
    "enabled_markets": "US,EU,NG,BRVM,JSE",
    "enabled_scopes": "US_EU,AFRICA",
    "last_universe_update_us_eu": "",
    "last_universe_update_africa": "",
    "last_gating_run_us_eu": "",
    "last_gating_run_africa": "",
    "last_rotation_run_us_eu": "",
    "last_rotation_run_africa": "",
    "admin_panel_theme": "dark",
    "admin_notifications_enabled": "true",
    "admin_auto_refresh_seconds": "60",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Get all admin settings as JSON.

    Returns all key-value pairs from app_settings table with defaults for missing keys.
    """
    require_admin(admin_key)

    try:
        with db._get_conn() as conn:
            # Fetch all settings from database
            rows = conn.execute(
                "SELECT key, value, updated_at FROM app_settings ORDER BY key"
            ).fetchall()

            settings = {}
            latest_updated = None

            for row in rows:
                settings[row["key"]] = row["value"]
                if row["updated_at"] and (not latest_updated or row["updated_at"] > latest_updated):
                    latest_updated = row["updated_at"]

            # Fill in any missing default values
            for key, default_value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = default_value

            return SettingsResponse(
                settings=settings,
                updated_at=latest_updated
            )

    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
):
    """
    Update admin settings (partial update).

    Accepts a dictionary of settings to update. Only provided keys are updated.
    """
    require_admin(admin_key)

    if not request.settings:
        raise HTTPException(status_code=400, detail="No settings provided")

    try:
        with db._get_conn() as conn:
            for key, value in request.settings.items():
                # Validate key is not empty
                if not key or not isinstance(key, str):
                    raise HTTPException(status_code=400, detail=f"Invalid setting key: {key}")

                # Convert value to string
                value_str = str(value) if value is not None else ""

                # Insert or update
                conn.execute(
                    """
                    INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (key, value_str)
                )

                logger.info(f"Updated setting '{key}' to '{value_str}'")

        # Return updated settings
        return await get_settings(admin_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
