"""
Session Management for MarketGPS
Handles Streamlit session state for authentication
"""

import streamlit as st
import time
from typing import Optional, Dict, Callable
from functools import wraps

from .supabase_client import SupabaseAuth


class SessionManager:
    """
    Manages user sessions in Streamlit using st.session_state.
    """
    
    SESSION_KEYS = [
        'user_id',
        'email', 
        'access_token',
        'refresh_token',
        'expires_at',
        'is_authenticated',
    ]
    
    @classmethod
    def init_session(cls):
        """Initialize session state keys if not present."""
        for key in cls.SESSION_KEYS:
            if key not in st.session_state:
                st.session_state[key] = None
        
        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False
    
    @classmethod
    def set_session(cls, session_data: Dict):
        """
        Store session data in Streamlit session state.
        """
        cls.init_session()
        
        st.session_state.user_id = session_data.get('user_id')
        st.session_state.email = session_data.get('email')
        st.session_state.access_token = session_data.get('access_token')
        st.session_state.refresh_token = session_data.get('refresh_token')
        st.session_state.expires_at = session_data.get('expires_at')
        st.session_state.is_authenticated = True
    
    @classmethod
    def clear_session(cls):
        """Clear all session data."""
        for key in cls.SESSION_KEYS:
            if key in st.session_state:
                st.session_state[key] = None
        st.session_state.is_authenticated = False
    
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if user is authenticated."""
        cls.init_session()
        return st.session_state.get('is_authenticated', False)
    
    @classmethod
    def get_user_id(cls) -> Optional[str]:
        """Get the current user's ID."""
        return st.session_state.get('user_id')
    
    @classmethod
    def get_email(cls) -> Optional[str]:
        """Get the current user's email."""
        return st.session_state.get('email')
    
    @classmethod
    def get_access_token(cls) -> Optional[str]:
        """Get the current access token."""
        return st.session_state.get('access_token')
    
    @classmethod
    def is_token_expired(cls) -> bool:
        """Check if the access token is expired or about to expire."""
        expires_at = st.session_state.get('expires_at')
        if not expires_at:
            return True
        
        # Consider expired if less than 5 minutes remaining
        return time.time() > (expires_at - 300)
    
    @classmethod
    def refresh_if_needed(cls) -> bool:
        """
        Refresh the session if the token is expired.
        Returns True if session is valid, False if refresh failed.
        """
        if not cls.is_authenticated():
            return False
        
        if not cls.is_token_expired():
            return True
        
        refresh_token = st.session_state.get('refresh_token')
        if not refresh_token:
            cls.clear_session()
            return False
        
        auth = SupabaseAuth()
        new_session = auth.refresh_session(refresh_token)
        
        if new_session:
            st.session_state.access_token = new_session['access_token']
            st.session_state.refresh_token = new_session['refresh_token']
            st.session_state.expires_at = new_session['expires_at']
            return True
        else:
            cls.clear_session()
            return False


def get_current_user() -> Optional[Dict]:
    """
    Get the current authenticated user info.
    Returns None if not authenticated.
    """
    SessionManager.init_session()
    
    if not SessionManager.is_authenticated():
        return None
    
    # Refresh token if needed
    if not SessionManager.refresh_if_needed():
        return None
    
    return {
        'user_id': SessionManager.get_user_id(),
        'email': SessionManager.get_email(),
    }


def require_auth(func: Callable = None, redirect_to: str = "login"):
    """
    Decorator to require authentication for a page/function.
    Redirects to login page if not authenticated.
    
    Usage:
        @require_auth
        def protected_page():
            st.write("Protected content")
    
    Or:
        @require_auth(redirect_to="signup")
        def protected_page():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            SessionManager.init_session()
            
            if not SessionManager.is_authenticated():
                st.warning("⚠️ Veuillez vous connecter pour accéder à cette page.")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("Se connecter", type="primary", use_container_width=True):
                        st.session_state.view = redirect_to
                        st.rerun()
                    
                    if st.button("Créer un compte", use_container_width=True):
                        st.session_state.view = "signup"
                        st.rerun()
                
                st.stop()
            
            # Refresh token if needed
            if not SessionManager.refresh_if_needed():
                st.warning("⚠️ Votre session a expiré. Veuillez vous reconnecter.")
                st.session_state.view = redirect_to
                st.rerun()
            
            return f(*args, **kwargs)
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator
