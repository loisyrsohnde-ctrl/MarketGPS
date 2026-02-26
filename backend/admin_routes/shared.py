"""
MarketGPS - Admin Routes Shared Dependencies

All imports, configuration, Pydantic models, and helper functions
shared across admin route sub-modules.
"""

import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
import httpx


# Bootstrap application (load environment variables and set up paths)
from core.bootstrap import bootstrap
bootstrap()

from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# Initialize SQLite store (READ-ONLY usage)
db = SQLiteStore()

# Supabase configuration (for reading users)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""))
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


# ===================================================================
# Response Models
# ===================================================================

class UserSummary(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    provider: Optional[str] = None  # email, google, apple, etc.
    email_confirmed: bool = False
    created_at: Optional[str] = None
    last_sign_in: Optional[str] = None
    sign_in_count: int = 0
    is_pro: bool = False
    plan: Optional[str] = None
    subscription_status: Optional[str] = None
    subscription_started: Optional[str] = None
    subscription_ends: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    amount_paid: Optional[float] = None
    currency: Optional[str] = None


class SubscriptionSummary(BaseModel):
    user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    plan: str
    status: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    interval: Optional[str] = None  # month, year
    created_at: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method: Optional[str] = None


class DashboardStats(BaseModel):
    total_users: int
    pro_users: int
    free_users: int
    new_users_today: int
    new_users_week: int
    active_subscriptions: int
    total_feedbacks: int
    feedbacks_today: int
    # News & Pipeline stats
    articles_today: int = 0
    viral_count: int = 0
    scripts_generated: int = 0
    sources_active: int = 0
    last_pipeline_run: Optional[str] = None
    llm_provider: str = "openai"
    data_warnings: List[str] = []


class FeedbackSummary(BaseModel):
    id: str
    type: str
    subject: Optional[str]
    message: str
    user_email: Optional[str]
    rating: Optional[int]
    platform: Optional[str]
    status: str
    created_at: str


class AIQuotaUpdate(BaseModel):
    """Request to update AI quota for a user."""
    user_id: str
    provider: str  # "openai" or "gemini" or "all"
    action: str  # "disable_limit", "enable_limit", "reset", "set_limit"
    new_limit: Optional[int] = None  # Only for "set_limit" action


# ===================================================================
# Admin Key Verification (centralized in admin_auth.py)
# ===================================================================

from admin_auth import verify_admin, require_admin


# ===================================================================
# Supabase Integration (READ-ONLY)
# ===================================================================

async def get_supabase_users() -> List[Dict[str, Any]]:
    """
    Fetch ALL users from Supabase Auth (READ-ONLY) with pagination.
    Uses the service role key to list all users.
    Supabase returns max 50 users per page by default.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.warning("Supabase credentials not configured for admin")
        return []

    all_users = []
    page = 1
    per_page = 1000  # Supabase allows up to 1000 per page

    try:
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{SUPABASE_URL}/auth/v1/admin/users",
                    headers={
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "apikey": SUPABASE_SERVICE_KEY,
                    },
                    params={
                        "page": page,
                        "per_page": per_page,
                    },
                    timeout=15.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    users = data.get("users", [])
                    all_users.extend(users)

                    # If we got fewer users than per_page, we've reached the end
                    if len(users) < per_page:
                        break
                    page += 1
                else:
                    logger.error(f"Supabase users fetch failed: {response.status_code}")
                    break

        logger.info(f"Fetched {len(all_users)} total users from Supabase")
        return all_users

    except Exception as e:
        logger.error(f"Error fetching Supabase users: {e}")
        return all_users  # Return whatever we've collected so far
