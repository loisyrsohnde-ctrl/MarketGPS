"""
Forgot Password Page for MarketGPS
Sends password reset email via Supabase
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.supabase_client import SupabaseAuth


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
                <rect x="3" y="11" width="18" height="11" rx="2"/>
                <circle cx="12" cy="16" r="1"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
        </div>
        <h1 style="
            color: #FFFFFF;
            font-size: 32px;
            font-weight: 700;
            margin: 0 0 12px 0;
            font-family: 'Inter', sans-serif;
        ">Mot de passe oublié</h1>
        <p style="
            color: #9CA3AF;
            font-size: 16px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Entrez votre email pour recevoir un lien de réinitialisation</p>
    </div>
    """, unsafe_allow_html=True)


def page_forgot_password():
    """Render forgot password page."""
    st.set_page_config(
        page_title="Mot de passe oublié - MarketGPS",
        page_icon="🔐",
        layout="centered",
    )
    
    inject_auth_css()
    render_header()
    
    # Check if already sent
    if st.session_state.get("reset_email_sent"):
        st.success("📧 Email envoyé ! Vérifiez votre boîte de réception.")
        st.info("Cliquez sur le lien dans l'email pour réinitialiser votre mot de passe.")
        
        if st.button("← Retour à la connexion", use_container_width=True):
            st.session_state.reset_email_sent = False
            st.session_state.view = "login"
            st.rerun()
        return
    
    # Email input
    email = st.text_input(
        "Adresse email",
        placeholder="vous@exemple.com",
        key="forgot_email",
    )
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Submit button
    if st.button("Envoyer le lien", type="primary", use_container_width=True, key="forgot_submit"):
        if not email or "@" not in email:
            st.error("Veuillez entrer une adresse email valide.")
        else:
            auth = SupabaseAuth()
            success, message = auth.reset_password_request(email)
            
            if success:
                st.session_state.reset_email_sent = True
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Back button
    if st.button("← Retour à la connexion", use_container_width=True, key="forgot_back"):
        st.session_state.view = "login"
        st.rerun()


if __name__ == "__main__":
    page_forgot_password()
