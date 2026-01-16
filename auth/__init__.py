"""
MarketGPS Authentication Module
Using Supabase Auth for secure authentication
"""

from .supabase_client import get_supabase_client, SupabaseAuth
from .session import SessionManager, require_auth, get_current_user
from .gating import EntitlementChecker, require_paid, check_usage_limit

__all__ = [
    'get_supabase_client',
    'SupabaseAuth',
    'SessionManager',
    'require_auth',
    'get_current_user',
    'EntitlementChecker',
    'require_paid',
    'check_usage_limit',
]
