"""
Reset Password Page for MarketGPS
Handles password reset after clicking email link
"""

import streamlit as st
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.supabase_client import SupabaseAuth
from auth.session import SessionManager


def inject_auth_css():
    """Inject premium dark theme CSS."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background: #0A0A0A !important; }
    
    section[data-testid="stMain"] {
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            #0A0A0A !important;
    }
    
    section[data-testid="stMain"] > div {
        max-width: 480px !important;
        margin: 0 auto !important;
        padding: 60px 24px !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    div[data-testid="stTextInput"] input {
        background: rgba(10, 10, 10, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-size: 15px !important;
        padding: 14px 16px !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(16, 185, 129, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
    }
    
    div[data-testid="stTextInput"] label {
        color: #E5E7EB !important;
        font-weight: 500 !important;
    }
    
    button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stButton"] > button:not([kind="primary"]) {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #E5E7EB !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the page header."""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 48px;">
        <div style="
            width: 72px;
            height: 72px;
            background: linear-gradient(135deg, #10B981, #059669);
            border-radius: 18px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.25);
        ">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
            </svg>
        </div>
        <h1 style="
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 700;
            margin: 0 0 12px 0;
            font-family: 'Inter', sans-serif;
        ">Nouveau mot de passe</h1>
        <p style="
            color: #9CA3AF;
            font-size: 16px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Choisissez un nouveau mot de passe sécurisé</p>
    </div>
    """, unsafe_allow_html=True)


def page_reset_password():
    """Render reset password page."""
    st.set_page_config(
        page_title="Réinitialiser le mot de passe - MarketGPS",
        page_icon="🔐",
        layout="centered",
    )
    
    inject_auth_css()
    render_header()
    
    # Check for tokens in URL (from Supabase email link)
    query_params = st.query_params
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")
    token_type = query_params.get("type")
    
    # If we have tokens from URL, set the session
    if access_token and refresh_token:
        auth = SupabaseAuth()
        session_data = auth.get_session_from_url(access_token, refresh_token)
        
        if session_data:
            SessionManager.set_session(session_data)
            st.session_state.can_reset_password = True
            # Clear URL params
            st.query_params.clear()
            st.rerun()
    
    # Check if user can reset password
    if not st.session_state.get("can_reset_password") and not SessionManager.is_authenticated():
        st.error("⚠️ Lien invalide ou expiré. Veuillez demander un nouveau lien.")
        
        if st.button("Demander un nouveau lien", type="primary", use_container_width=True):
            st.session_state.view = "forgot-password"
            st.rerun()
        
        if st.button("← Retour à la connexion", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()
        return
    
    # Password reset form
    new_password = st.text_input(
        "Nouveau mot de passe",
        type="password",
        placeholder="Minimum 8 caractères",
        key="reset_new_password",
    )
    
    confirm_password = st.text_input(
        "Confirmer le mot de passe",
        type="password",
        placeholder="Retapez votre mot de passe",
        key="reset_confirm_password",
    )
    
    # Show password toggle
    show_pw = st.checkbox("Afficher les mots de passe", key="reset_show_pw")
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Submit button
    if st.button("Mettre à jour le mot de passe", type="primary", use_container_width=True, key="reset_submit"):
        if not new_password:
            st.error("Veuillez entrer un nouveau mot de passe.")
        elif len(new_password) < 8:
            st.error("Le mot de passe doit contenir au moins 8 caractères.")
        elif new_password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            auth = SupabaseAuth()
            success, message = auth.update_password(new_password)
            
            if success:
                st.success(message)
                st.session_state.can_reset_password = False
                st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")
                
                # Clear session and redirect to login
                SessionManager.clear_session()
                
                if st.button("Se connecter →", type="primary", use_container_width=True):
                    st.session_state.view = "login"
                    st.rerun()
            else:
                st.error(message)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    if st.button("← Retour à la connexion", use_container_width=True, key="reset_back"):
        st.session_state.can_reset_password = False
        SessionManager.clear_session()
        st.session_state.view = "login"
        st.rerun()


if __name__ == "__main__":
    page_reset_password()
