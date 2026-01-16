"""
Signup Page for MarketGPS
Premium dark theme with email confirmation
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
    
    .stApp {
        background: #0A0A0A !important;
    }
    
    section[data-testid="stMain"] {
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
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
    
    button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 14px 24px !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    button[kind="primary"]:hover {
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3) !important;
    }
    
    div[data-testid="stButton"] > button:not([kind="primary"]) {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #E5E7EB !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
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
        ">Créer un compte</h1>
        <p style="
            color: #9CA3AF;
            font-size: 16px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Accédez aux données institutionnelles MarketGPS</p>
    </div>
    """, unsafe_allow_html=True)


def page_signup():
    """Render the signup page."""
    st.set_page_config(
        page_title="Inscription - MarketGPS",
        page_icon="🚀",
        layout="centered",
    )
    
    inject_auth_css()
    SessionManager.init_session()
    
    # Redirect if already logged in
    if SessionManager.is_authenticated():
        st.session_state.view = "dashboard"
        st.rerun()
    
    render_header()
    
    # Show selected plan if any
    selected_plan = st.session_state.get("selected_plan")
    if selected_plan:
        plan_info = {
            "monthly_9_99": "Plan Mensuel - 9,99 €/mois",
            "yearly_50": "Plan Annuel - 50 €/an (économisez 58%)",
        }
        st.info(f"📦 {plan_info.get(selected_plan, selected_plan)}")
    
    # Signup form
    email = st.text_input(
        "Adresse email",
        placeholder="vous@exemple.com",
        key="signup_email",
    )
    
    display_name = st.text_input(
        "Nom d'affichage (optionnel)",
        placeholder="Votre nom ou pseudo",
        key="signup_name",
    )
    
    password = st.text_input(
        "Mot de passe",
        type="password",
        placeholder="Minimum 8 caractères",
        key="signup_password",
    )
    
    # Show password toggle
    show_pw = st.checkbox("Afficher le mot de passe", key="signup_show_pw")
    
    confirm_password = st.text_input(
        "Confirmer le mot de passe",
        type="password" if not show_pw else "default",
        placeholder="Retapez votre mot de passe",
        key="signup_confirm",
    )
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Signup button
    if st.button("Créer mon compte", type="primary", use_container_width=True, key="signup_submit"):
        # Validation
        if not email or not password:
            st.error("Veuillez remplir tous les champs obligatoires.")
        elif len(password) < 8:
            st.error("Le mot de passe doit contenir au moins 8 caractères.")
        elif password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        elif "@" not in email or "." not in email:
            st.error("Veuillez entrer une adresse email valide.")
        else:
            auth = SupabaseAuth()
            success, message, user_data = auth.sign_up(
                email=email,
                password=password,
                display_name=display_name or None,
            )
            
            if success:
                st.success(message)
                st.info("📧 Vérifiez votre boîte de réception et cliquez sur le lien de confirmation.")
                
                # Store email for later
                st.session_state.pending_email = email
            else:
                st.error(message)
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Secondary actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Retour", use_container_width=True, key="signup_back"):
            st.session_state.view = "landing"
            st.rerun()
    
    with col2:
        if st.button("Déjà inscrit ?", use_container_width=True, key="signup_to_login"):
            st.session_state.view = "login"
            st.rerun()
    
    # Terms
    st.markdown("""
    <div style="
        text-align: center;
        margin-top: 32px;
        color: #6B7280;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
        line-height: 1.6;
    ">
        En créant un compte, vous acceptez nos 
        <a href="#" style="color: #9CA3AF; text-decoration: underline;">Conditions d'utilisation</a>
        et notre
        <a href="#" style="color: #9CA3AF; text-decoration: underline;">Politique de confidentialité</a>
    </div>
    """, unsafe_allow_html=True)


# Run the page
if __name__ == "__main__":
    page_signup()
