"""
Supabase Client for MarketGPS Authentication
"""

import os
import logging
from typing import Optional, Tuple, Dict, Any
from functools import lru_cache

from supabase import create_client, Client
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Get a cached Supabase client instance.
    Uses ANON KEY for client-side operations.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables. "
            "Please set them in your .env file."
        )
    
    return create_client(url, key)


class SupabaseAuth:
    """
    Authentication wrapper for Supabase Auth operations.
    All auth operations go through Supabase - no local password storage.
    """
    
    def __init__(self):
        self.client = get_supabase_client()
        self.app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8501")
    
    def sign_up(
        self, 
        email: str, 
        password: str, 
        display_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Register a new user with email/password.
        Supabase will send a confirmation email.
        
        Returns: (success, message, user_data)
        """
        try:
            options = {}
            if display_name:
                options["data"] = {"display_name": display_name}
            
            # Email redirect after confirmation
            options["email_redirect_to"] = f"{self.app_base_url}/auth/callback"
            
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": options
            })
            
            if response.user:
                # Check if email confirmation is required
                if response.user.email_confirmed_at is None:
                    return (
                        True, 
                        "Compte créé ! Vérifiez votre email pour confirmer votre inscription.",
                        {"user_id": str(response.user.id), "email": email}
                    )
                else:
                    return (
                        True,
                        "Compte créé et confirmé !",
                        {"user_id": str(response.user.id), "email": email}
                    )
            else:
                return (False, "Échec de la création du compte.", None)
                
        except AuthApiError as e:
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                return (False, "Cet email est déjà utilisé.", None)
            elif "password" in error_msg.lower():
                return (False, "Le mot de passe doit contenir au moins 6 caractères.", None)
            else:
                logger.error(f"Signup error: {e}")
                return (False, f"Erreur: {error_msg}", None)
        except Exception as e:
            logger.error(f"Unexpected signup error: {e}")
            return (False, "Une erreur inattendue s'est produite.", None)
    
    def sign_in(
        self, 
        email: str, 
        password: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Sign in with email/password.
        
        Returns: (success, message, session_data)
        """
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user and response.session:
                return (
                    True,
                    "Connexion réussie !",
                    {
                        "user_id": str(response.user.id),
                        "email": response.user.email,
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at,
                    }
                )
            else:
                return (False, "Échec de la connexion.", None)
                
        except AuthApiError as e:
            error_msg = str(e)
            if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
                return (False, "Email ou mot de passe incorrect.", None)
            elif "not confirmed" in error_msg.lower():
                return (False, "Veuillez confirmer votre email avant de vous connecter.", None)
            else:
                logger.error(f"Sign in error: {e}")
                return (False, f"Erreur de connexion: {error_msg}", None)
        except Exception as e:
            logger.error(f"Unexpected sign in error: {e}")
            return (False, "Une erreur inattendue s'est produite.", None)
    
    def sign_out(self) -> Tuple[bool, str]:
        """
        Sign out the current user.
        """
        try:
            self.client.auth.sign_out()
            return (True, "Déconnexion réussie.")
        except Exception as e:
            logger.error(f"Sign out error: {e}")
            return (False, f"Erreur de déconnexion: {e}")
    
    def reset_password_request(self, email: str) -> Tuple[bool, str]:
        """
        Send a password reset email.
        """
        try:
            redirect_url = f"{self.app_base_url}/reset-password"
            
            self.client.auth.reset_password_email(
                email,
                options={"redirect_to": redirect_url}
            )
            
            return (
                True, 
                "Si cet email existe, vous recevrez un lien de réinitialisation."
            )
        except AuthApiError as e:
            logger.error(f"Password reset error: {e}")
            # Don't reveal if email exists or not
            return (
                True, 
                "Si cet email existe, vous recevrez un lien de réinitialisation."
            )
        except Exception as e:
            logger.error(f"Unexpected password reset error: {e}")
            return (False, "Une erreur s'est produite. Réessayez plus tard.")
    
    def update_password(self, new_password: str) -> Tuple[bool, str]:
        """
        Update the current user's password.
        User must be authenticated (via reset link).
        """
        try:
            self.client.auth.update_user({"password": new_password})
            return (True, "Mot de passe mis à jour avec succès !")
        except AuthApiError as e:
            error_msg = str(e)
            if "password" in error_msg.lower() and "weak" in error_msg.lower():
                return (False, "Le mot de passe est trop faible.")
            else:
                logger.error(f"Password update error: {e}")
                return (False, f"Erreur: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected password update error: {e}")
            return (False, "Une erreur inattendue s'est produite.")
    
    def get_session_from_url(self, access_token: str, refresh_token: str) -> Optional[Dict]:
        """
        Set session from URL tokens (after email confirmation/reset).
        """
        try:
            response = self.client.auth.set_session(access_token, refresh_token)
            if response.user and response.session:
                return {
                    "user_id": str(response.user.id),
                    "email": response.user.email,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                }
            return None
        except Exception as e:
            logger.error(f"Error setting session from URL: {e}")
            return None
    
    def refresh_session(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh the access token using refresh token.
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)
            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                }
            return None
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return None
    
    def get_user(self) -> Optional[Dict]:
        """
        Get the current authenticated user.
        """
        try:
            response = self.client.auth.get_user()
            if response.user:
                return {
                    "user_id": str(response.user.id),
                    "email": response.user.email,
                    "email_confirmed": response.user.email_confirmed_at is not None,
                    "created_at": str(response.user.created_at) if response.user.created_at else None,
                }
            return None
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
