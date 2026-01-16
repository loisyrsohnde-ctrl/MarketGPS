"""
Supabase Admin Client for MarketGPS Backend
Uses SERVICE_ROLE_KEY for privileged operations
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

from supabase import create_client, Client

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Client:
    """
    Get a Supabase client with service role privileges.
    USE WITH CAUTION - bypasses RLS.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables"
        )
    
    return create_client(url, key)


class SupabaseAdmin:
    """
    Admin operations on Supabase using service role.
    Only used by backend for webhook processing.
    """
    
    def __init__(self):
        self.client = get_supabase_admin_client()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by ID.
        """
        try:
            response = self.client.table('profiles').select('*').eq('id', user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Get profile error: {e}")
            return None
    
    def get_user_entitlements(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user entitlements by user ID.
        """
        try:
            response = self.client.table('entitlements').select('*').eq('user_id', user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Get entitlements error: {e}")
            return None
    
    def update_entitlements(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update user entitlements.
        Used by Stripe webhooks to sync subscription status.
        """
        try:
            # Convert Unix timestamp to ISO format if present
            if 'current_period_end' in updates and isinstance(updates['current_period_end'], int):
                from datetime import datetime
                updates['current_period_end'] = datetime.utcfromtimestamp(
                    updates['current_period_end']
                ).isoformat()
            
            response = self.client.table('entitlements').update(updates).eq('user_id', user_id).execute()
            
            if response.data:
                logger.info(f"Updated entitlements for user: {user_id}")
                return True
            else:
                logger.warning(f"No entitlements found for user: {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Update entitlements error: {e}")
            return False
    
    def find_user_by_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        """
        Find user ID by Stripe customer ID.
        """
        try:
            response = self.client.table('entitlements').select('user_id').eq(
                'stripe_customer_id', stripe_customer_id
            ).single().execute()
            
            if response.data:
                return response.data['user_id']
            return None
            
        except Exception as e:
            logger.error(f"Find user by Stripe customer error: {e}")
            return None
    
    def create_entitlements_if_missing(self, user_id: str) -> bool:
        """
        Create entitlements record if it doesn't exist.
        Fallback in case trigger didn't fire.
        """
        try:
            existing = self.get_user_entitlements(user_id)
            if existing:
                return True
            
            response = self.client.table('entitlements').insert({
                'user_id': user_id,
                'plan': 'FREE',
                'status': 'active',
                'daily_requests_limit': 10,
                'daily_requests_used': 0,
            }).execute()
            
            if response.data:
                logger.info(f"Created entitlements for user: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Create entitlements error: {e}")
            return False
