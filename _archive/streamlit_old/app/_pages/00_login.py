"""
Login Page for MarketGPS
Premium dark theme with glassmorphism
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.supabase_client import SupabaseAuth
from auth.session import SessionManager


def inject_auth_css():
    """Inject premium dark theme CSS for auth pages."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Page background */
    .stApp {
        background: #0A0A0A !important;
    }
    
    section[data-testid="stMain"] {
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
            #0A0A0A !important;
    }
    
    /* Center content */
    section[data-testid="stMain"] > div {
        max-width: 480px !important;
        margin: 0 auto !important;
        padding: 60px 24px !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Form inputs */
    div[data-testid="stTextInput"] input {
        background: rgba(10, 10, 10, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
        font-size: 15px !important;
        padding: 14px 16px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(16, 185, 129, 0.5) !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
    }
    
    div[data-testid="stTextInput"] input::placeholder {
        color: rgba(156, 163, 175, 0.7) !important;
    }
    
    div[data-testid="stTextInput"] label {
        color: #E5E7EB !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Primary button */
    button[kind="primary"], button[data-testid="stButton"][kind="primary"] > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 14px 24px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="primary"]:hover {
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Secondary button */
    button[kind="secondary"], div[data-testid="stButton"] > button:not([kind="primary"]) {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #E5E7EB !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Alerts */
    div[data-testid="stAlert"] {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 12px !important;
        color: #10B981 !important;
    }
    
    .stAlert > div {
        color: #E5E7EB !important;
    }
    
    /* Error alert */
    div[data-baseweb="notification"][kind="negative"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the page header with logo."""
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
                <circle cx="12" cy="12" r="10"/>
                <circle cx="12" cy="12" r="3"/>
                <line x1="12" y1="2" x2="12" y2="5"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
                <line x1="2" y1="12" x2="5" y2="12"/>
                <line x1="19" y1="12" x2="22" y2="12"/>
            </svg>
        </div>
        <h1 style="
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 700;
            margin: 0 0 12px 0;
            font-family: 'Inter', sans-serif;
        ">Connexion</h1>
        <p style="
            color: #9CA3AF;
            font-size: 16px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Accédez à votre compte MarketGPS</p>
    </div>
    """, unsafe_allow_html=True)


def page_login():
    """Render the login page."""
    st.set_page_config(
        page_title="Connexion - MarketGPS",
        page_icon="🔐",
        layout="centered",
    )
    
    inject_auth_css()
    SessionManager.init_session()
    
    # Redirect if already logged in
    if SessionManager.is_authenticated():
        st.session_state.view = "dashboard"
        st.rerun()
    
    render_header()
    
    # Login form
    email = st.text_input(
        "Adresse email",
        placeholder="vous@exemple.com",
        key="login_email",
    )
    
    password = st.text_input(
        "Mot de passe",
        type="password",
        placeholder="Votre mot de passe",
        key="login_password",
    )
    
    # Show password toggle
    show_password = st.checkbox("Afficher le mot de passe", key="login_show_pw")
    if show_password:
        st.text_input(
            "Mot de passe (visible)",
            value=st.session_state.get("login_password", ""),
            key="login_password_visible",
            disabled=True,
        )
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Login button
    if st.button("Se connecter", type="primary", use_container_width=True, key="login_submit"):
        if not email or not password:
            st.error("Veuillez remplir tous les champs.")
        else:
            auth = SupabaseAuth()
            success, message, session_data = auth.sign_in(email, password)
            
            if success and session_data:
                SessionManager.set_session(session_data)
                st.success(message)
                st.session_state.view = "dashboard"
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Secondary actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Retour", use_container_width=True, key="login_back"):
            st.session_state.view = "landing"
            st.rerun()
    
    with col2:
        if st.button("Créer un compte", use_container_width=True, key="login_to_signup"):
            st.session_state.view = "signup"
            st.rerun()
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Forgot password link
    st.markdown("""
    <div style="text-align: center;">
        <a href="?view=forgot-password" style="
            color: #9CA3AF;
            text-decoration: none;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
        ">Mot de passe oublié ?</a>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Mot de passe oublié ?", key="login_forgot", use_container_width=True):
        st.session_state.view = "forgot-password"
        st.rerun()


# Run the page
if __name__ == "__main__":
    page_login()
