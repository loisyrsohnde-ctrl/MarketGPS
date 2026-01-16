"""
Feature Gating for MarketGPS
Controls access to premium features based on subscription plan
"""

import streamlit as st
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from functools import wraps

from .supabase_client import get_supabase_client
from .session import SessionManager


@dataclass
class Entitlements:
    """User entitlements data."""
    user_id: str
    plan: str  # FREE, MONTHLY, YEARLY
    status: str  # active, past_due, canceled, inactive
    daily_requests_limit: int
    daily_requests_used: int
    current_period_end: Optional[str]
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    
    @property
    def is_paid(self) -> bool:
        """Check if user has an active paid subscription."""
        return self.plan in ('MONTHLY', 'YEARLY') and self.status == 'active'
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active (including FREE)."""
        return self.status in ('active', 'trialing')
    
    @property
    def daily_requests_remaining(self) -> int:
        """Get remaining daily requests."""
        return max(0, self.daily_requests_limit - self.daily_requests_used)
    
    @property
    def can_make_request(self) -> bool:
        """Check if user can make another request."""
        return self.daily_requests_remaining > 0


class EntitlementChecker:
    """
    Check and manage user entitlements from Supabase.
    """
    
    # Feature flags - easy to modify
    FEATURES = {
        'africa_markets': {'requires_paid': True, 'description': 'Marchés Afrique'},
        'watchlist': {'requires_paid': True, 'description': 'Watchlist personnalisée'},
        'alerts': {'requires_paid': True, 'description': 'Alertes personnalisées'},
        'export_csv': {'requires_paid': True, 'description': 'Export CSV'},
        'api_access': {'requires_paid': True, 'description': 'Accès API'},
        'priority_support': {'requires_paid': True, 'description': 'Support prioritaire'},
        'historical_data': {'requires_paid': False, 'description': 'Données historiques'},
        'basic_scores': {'requires_paid': False, 'description': 'Scores de base'},
    }
    
    # Plan limits
    PLAN_LIMITS = {
        'FREE': {'daily_requests': 10, 'markets': ['US', 'EU']},
        'MONTHLY': {'daily_requests': 200, 'markets': ['US', 'EU', 'AFRICA']},
        'YEARLY': {'daily_requests': 200, 'markets': ['US', 'EU', 'AFRICA']},
    }
    
    @classmethod
    def get_entitlements(cls, user_id: str) -> Optional[Entitlements]:
        """
        Fetch user entitlements from Supabase.
        """
        try:
            client = get_supabase_client()
            
            response = client.table('entitlements').select('*').eq('user_id', user_id).single().execute()
            
            if response.data:
                return Entitlements(
                    user_id=response.data['user_id'],
                    plan=response.data.get('plan', 'FREE'),
                    status=response.data.get('status', 'active'),
                    daily_requests_limit=response.data.get('daily_requests_limit', 10),
                    daily_requests_used=response.data.get('daily_requests_used', 0),
                    current_period_end=response.data.get('current_period_end'),
                    stripe_customer_id=response.data.get('stripe_customer_id'),
                    stripe_subscription_id=response.data.get('stripe_subscription_id'),
                )
            return None
            
        except Exception as e:
            st.error(f"Erreur lors de la récupération des droits: {e}")
            return None
    
    @classmethod
    def get_cached_entitlements(cls) -> Optional[Entitlements]:
        """
        Get entitlements with caching in session state.
        Refreshes every 5 minutes.
        """
        import time
        
        cache_key = '_entitlements_cache'
        cache_time_key = '_entitlements_cache_time'
        cache_duration = 300  # 5 minutes
        
        user_id = SessionManager.get_user_id()
        if not user_id:
            return None
        
        # Check cache
        if cache_key in st.session_state and cache_time_key in st.session_state:
            if time.time() - st.session_state[cache_time_key] < cache_duration:
                return st.session_state[cache_key]
        
        # Fetch fresh data
        entitlements = cls.get_entitlements(user_id)
        
        if entitlements:
            st.session_state[cache_key] = entitlements
            st.session_state[cache_time_key] = time.time()
        
        return entitlements
    
    @classmethod
    def clear_cache(cls):
        """Clear entitlements cache."""
        if '_entitlements_cache' in st.session_state:
            del st.session_state['_entitlements_cache']
        if '_entitlements_cache_time' in st.session_state:
            del st.session_state['_entitlements_cache_time']
    
    @classmethod
    def can_access_feature(cls, feature: str) -> Tuple[bool, str]:
        """
        Check if user can access a specific feature.
        
        Returns: (allowed, reason)
        """
        if feature not in cls.FEATURES:
            return (True, "")
        
        feature_config = cls.FEATURES[feature]
        
        if not feature_config['requires_paid']:
            return (True, "")
        
        entitlements = cls.get_cached_entitlements()
        
        if not entitlements:
            return (False, "Veuillez vous connecter.")
        
        if entitlements.is_paid:
            return (True, "")
        
        return (
            False, 
            f"La fonctionnalité '{feature_config['description']}' nécessite un abonnement payant."
        )
    
    @classmethod
    def can_access_market(cls, market: str) -> Tuple[bool, str]:
        """
        Check if user can access a specific market.
        """
        entitlements = cls.get_cached_entitlements()
        
        if not entitlements:
            return (False, "Veuillez vous connecter.")
        
        allowed_markets = cls.PLAN_LIMITS.get(entitlements.plan, {}).get('markets', ['US', 'EU'])
        
        if market.upper() in [m.upper() for m in allowed_markets]:
            return (True, "")
        
        return (
            False,
            f"Le marché '{market}' nécessite un abonnement payant."
        )


def require_paid(feature: Optional[str] = None):
    """
    Decorator to require a paid subscription for a function/page.
    
    Usage:
        @require_paid()
        def premium_page():
            ...
        
        @require_paid(feature='africa_markets')
        def africa_page():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            entitlements = EntitlementChecker.get_cached_entitlements()
            
            if not entitlements:
                _show_login_prompt()
                st.stop()
            
            if feature:
                allowed, reason = EntitlementChecker.can_access_feature(feature)
                if not allowed:
                    _show_upgrade_prompt(reason)
                    st.stop()
            elif not entitlements.is_paid:
                _show_upgrade_prompt("Cette fonctionnalité nécessite un abonnement payant.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_usage_limit() -> Tuple[bool, int]:
    """
    Check if user has remaining daily requests.
    
    Returns: (can_continue, remaining_requests)
    """
    entitlements = EntitlementChecker.get_cached_entitlements()
    
    if not entitlements:
        return (False, 0)
    
    return (entitlements.can_make_request, entitlements.daily_requests_remaining)


def _show_login_prompt():
    """Show login prompt UI."""
    st.warning("⚠️ Veuillez vous connecter pour accéder à cette fonctionnalité.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Se connecter", type="primary", use_container_width=True, key="gate_login"):
            st.session_state.view = "login"
            st.rerun()


def _show_upgrade_prompt(reason: str):
    """Show upgrade prompt UI with premium design."""
    st.markdown("""
    <style>
    .upgrade-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 16px;
        padding: 32px;
        text-align: center;
        margin: 24px 0;
    }
    .upgrade-title {
        color: #10B981;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 12px;
    }
    .upgrade-reason {
        color: #E5E7EB;
        font-size: 16px;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="upgrade-box">
        <div class="upgrade-title">🚀 Passez à Premium</div>
        <div class="upgrade-reason">{reason}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Voir les tarifs", type="primary", use_container_width=True, key="gate_upgrade"):
            st.session_state.view = "billing"
            st.rerun()
