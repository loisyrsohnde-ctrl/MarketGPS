"""
Auth Callback Page for MarketGPS
Handles redirect after email confirmation
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.supabase_client import SupabaseAuth
from auth.session import SessionManager


def inject_callback_css():
    """Inject minimal CSS for callback page."""
    st.markdown("""
    <style>
    .stApp { background: #0A0A0A !important; }
    
    section[data-testid="stMain"] {
        background: #0A0A0A !important;
    }
    
    section[data-testid="stMain"] > div {
        max-width: 480px !important;
        margin: 0 auto !important;
        padding: 100px 24px !important;
        text-align: center;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def page_auth_callback():
    """Handle auth callback from Supabase."""
    st.set_page_config(
        page_title="Confirmation - MarketGPS",
        page_icon="✓",
        layout="centered",
    )
    
    inject_callback_css()
    SessionManager.init_session()
    
    # Get tokens from URL
    query_params = st.query_params
    
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")
    token_type = query_params.get("type")
    error = query_params.get("error")
    error_description = query_params.get("error_description")
    
    # Handle errors
    if error:
        st.markdown("""
        <div style="text-align: center;">
            <div style="
                width: 80px;
                height: 80px;
                background: rgba(239, 68, 68, 0.15);
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 24px;
            ">
                <span style="font-size: 40px;">❌</span>
            </div>
            <h1 style="color: #EF4444; font-size: 28px; margin-bottom: 12px;">Erreur</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.error(error_description or error)
        
        if st.button("Retour à la connexion", type="primary", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()
        return
    
    # Handle successful confirmation
    if access_token and refresh_token:
        auth = SupabaseAuth()
        session_data = auth.get_session_from_url(access_token, refresh_token)
        
        if session_data:
            SessionManager.set_session(session_data)
            
            # Clear URL params
            st.query_params.clear()
            
            st.markdown("""
            <div style="text-align: center;">
                <div style="
                    width: 80px;
                    height: 80px;
                    background: rgba(16, 185, 129, 0.15);
                    border-radius: 50%;
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 24px;
                ">
                    <span style="font-size: 40px;">✓</span>
                </div>
                <h1 style="color: #10B981; font-size: 28px; margin-bottom: 12px; font-family: 'Inter', sans-serif;">
                    Email confirmé !
                </h1>
                <p style="color: #9CA3AF; font-size: 16px; margin-bottom: 32px;">
                    Votre compte est maintenant actif
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Accéder à l'application →", type="primary", use_container_width=True):
                st.session_state.view = "dashboard"
                st.rerun()
            
            # Auto-redirect after 3 seconds
            st.markdown("""
            <script>
                setTimeout(function() {
                    window.location.href = '/?view=dashboard';
                }, 3000);
            </script>
            <p style="color: #6B7280; font-size: 14px; margin-top: 24px;">
                Redirection automatique dans 3 secondes...
            </p>
            """, unsafe_allow_html=True)
        else:
            st.error("Impossible de récupérer la session. Veuillez vous connecter manuellement.")
            
            if st.button("Se connecter", type="primary", use_container_width=True):
                st.session_state.view = "login"
                st.rerun()
    else:
        # No tokens - show loading or redirect
        st.markdown("""
        <div style="text-align: center;">
            <div style="
                width: 80px;
                height: 80px;
                background: rgba(16, 185, 129, 0.15);
                border-radius: 50%;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 24px;
            ">
                <span style="font-size: 40px;">⏳</span>
            </div>
            <h1 style="color: #FFFFFF; font-size: 28px; margin-bottom: 12px;">
                Vérification en cours...
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("Si la page ne se charge pas, cliquez ci-dessous.")
        
        if st.button("Retour à la connexion", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()


if __name__ == "__main__":
    page_auth_callback()
