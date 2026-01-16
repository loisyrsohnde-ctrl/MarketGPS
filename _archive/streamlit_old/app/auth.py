"""
MarketGPS v12.0 - Authentication Module
Secure password hashing and user authentication.
"""
import hashlib
import secrets
import re
from typing import Optional, Tuple
from pathlib import Path

from core.config import get_config, get_logger
from storage.sqlite_store import SQLiteStore

logger = get_logger(__name__)

# Password requirements
MIN_PASSWORD_LENGTH = 8
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def hash_password(password: str) -> str:
    """
    Hash password using PBKDF2-SHA256.
    Returns format: pbkdf2:sha256:iterations$salt$hash
    """
    salt = secrets.token_hex(16)
    iterations = 260000
    
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    )
    
    return f"pbkdf2:sha256:{iterations}${salt}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        if not password_hash.startswith('pbkdf2:sha256:'):
            return False
        
        parts = password_hash.split('$')
        if len(parts) != 3:
            return False
        
        header = parts[0]  # pbkdf2:sha256:iterations
        salt = parts[1]
        stored_hash = parts[2]
        
        iterations = int(header.split(':')[2])
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        
        return secrets.compare_digest(key.hex(), stored_hash)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    if not email:
        return False, "L'email est requis"
    
    email = email.strip().lower()
    
    if not EMAIL_REGEX.match(email):
        return False, "Format d'email invalide"
    
    return True, email


def validate_password(password: str, confirm_password: str = None) -> Tuple[bool, str]:
    """Validate password strength."""
    if not password:
        return False, "Le mot de passe est requis"
    
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Le mot de passe doit contenir au moins {MIN_PASSWORD_LENGTH} caractères"
    
    if confirm_password is not None and password != confirm_password:
        return False, "Les mots de passe ne correspondent pas"
    
    return True, ""


class AuthManager:
    """Authentication manager for MarketGPS."""
    
    def __init__(self, store: SQLiteStore = None):
        """Initialize auth manager."""
        if store is None:
            config = get_config()
            store = SQLiteStore(str(config.storage.sqlite_path))
        self._store = store
    
    def signup(self, email: str, password: str, confirm_password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Register a new user.
        Returns (success, message, user_id)
        """
        # Validate email
        valid, result = validate_email(email)
        if not valid:
            return False, result, None
        email = result
        
        # Validate password
        valid, message = validate_password(password, confirm_password)
        if not valid:
            return False, message, None
        
        # Check if email exists
        existing = self._store.get_user_by_email(email)
        if existing:
            return False, "Un compte existe déjà avec cet email", None
        
        # Create user
        password_hash = hash_password(password)
        user_id = self._store.create_user(email, password_hash)
        
        if not user_id:
            return False, "Erreur lors de la création du compte", None
        
        logger.info(f"New user registered: {email}")
        return True, "Compte créé avec succès", user_id
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Authenticate user.
        Returns (success, message, user_dict)
        """
        # Validate email format
        valid, result = validate_email(email)
        if not valid:
            return False, result, None
        email = result
        
        if not password:
            return False, "Le mot de passe est requis", None
        
        # Get user
        user = self._store.get_user_by_email(email)
        if not user:
            return False, "Email ou mot de passe incorrect", None
        
        # Verify password
        if not verify_password(password, user.get('password_hash', '')):
            return False, "Email ou mot de passe incorrect", None
        
        # Update last login
        self._store.update_last_login(user['user_id'])
        
        # Get profile
        profile = self._store.get_user_profile(user['user_id'])
        
        logger.info(f"User logged in: {email}")
        return True, "Connexion réussie", {
            "user_id": user['user_id'],
            "email": user['email'],
            "display_name": profile.get('display_name') if profile else email.split('@')[0],
            "avatar_path": profile.get('avatar_path') if profile else None,
            "plan": profile.get('plan', 'free') if profile else 'free',
            "subscription_status": profile.get('subscription_status', 'active') if profile else 'active'
        }
    
    def get_user_info(self, user_id: str) -> Optional[dict]:
        """Get full user info for session."""
        user = self._store.get_user_by_id(user_id)
        if not user:
            return None
        
        profile = self._store.get_user_profile(user_id)
        subscription = self._store.get_subscription(user_id)
        
        return {
            "user_id": user_id,
            "email": user['email'],
            "display_name": profile.get('display_name') if profile else user['email'].split('@')[0],
            "avatar_path": profile.get('avatar_path') if profile else None,
            "plan": subscription.get('plan', 'free'),
            "subscription_status": subscription.get('status', 'active'),
            "daily_quota_used": subscription.get('daily_quota_used', 0),
            "daily_quota_limit": subscription.get('daily_quota_limit', 3),
            "is_pro": subscription.get('plan') in ('monthly_9_99', 'yearly_50') and subscription.get('status') == 'active'
        }
    
    def is_authenticated(self, user_id: str) -> bool:
        """Check if user_id is valid and active."""
        if not user_id or user_id == 'default':
            return False
        user = self._store.get_user_by_id(user_id)
        return user is not None and user.get('is_active', 0) == 1


def save_avatar(user_id: str, uploaded_file) -> Optional[str]:
    """
    Save uploaded avatar file.
    Returns the path to saved file or None on error.
    """
    config = get_config()
    avatars_dir = config.storage.data_dir / "uploads" / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Determine extension
        filename = uploaded_file.name.lower()
        if filename.endswith('.png'):
            ext = '.png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            ext = '.jpg'
        else:
            ext = '.png'
        
        # Save file
        avatar_path = avatars_dir / f"{user_id}{ext}"
        with open(avatar_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"Saved avatar for {user_id}: {avatar_path}")
        return str(avatar_path)
    except Exception as e:
        logger.error(f"Failed to save avatar: {e}")
        return None


def get_current_user_id() -> str:
    """Get current user ID from session state (Streamlit)."""
    import streamlit as st
    return st.session_state.get('user_id', 'default')


def is_logged_in() -> bool:
    """Check if user is logged in (Streamlit)."""
    import streamlit as st
    user_id = st.session_state.get('user_id')
    return user_id is not None and user_id != 'default'


def logout():
    """Logout current user (Streamlit)."""
    import streamlit as st
    keys_to_clear = ['user_id', 'user_info', 'is_pro']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
