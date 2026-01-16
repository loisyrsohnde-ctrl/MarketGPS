"""
Auth Pages - Premium Fintech Dark Theme
========================================
Modern, glassmorphism-based authentication pages for MarketGPS.
Follows institutional fintech design standards.
Supports both legacy SQLite auth and new Supabase Auth.
"""

import streamlit as st
from typing import Tuple, Optional
import os
import sys
import base64
from pathlib import Path

# Add parent for auth module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
print(f"[DEBUG] Loaded .env from: {env_path}")

# Check if Supabase is configured
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

# Debug: Print Supabase status
print(f"[DEBUG] SUPABASE_URL set: {bool(SUPABASE_URL)}")
print(f"[DEBUG] SUPABASE_ANON_KEY set: {bool(SUPABASE_ANON_KEY)}")
print(f"[DEBUG] SUPABASE_ENABLED: {SUPABASE_ENABLED}")

if SUPABASE_ENABLED:
    try:
        from auth.supabase_client import SupabaseAuth
        from auth.session import SessionManager
        print("[DEBUG] Supabase modules imported successfully")
    except ImportError as e:
        print(f"[DEBUG] Failed to import Supabase modules: {e}")
        SUPABASE_ENABLED = False


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════
TOKENS = {
    "bg_primary": "#0A0A0A",
    "bg_card": "rgba(17, 24, 39, 0.55)",
    "bg_input": "rgba(10, 10, 10, 0.65)",
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    "border_input": "rgba(255, 255, 255, 0.10)",
    "border_focus": "rgba(16, 185, 129, 0.55)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#E5E7EB",
    "text_muted": "#9CA3AF",
    "placeholder": "rgba(229, 231, 235, 0.55)",
    "accent": "#10B981",
    "accent_dark": "#059669",
    "glow": "rgba(16, 185, 129, 0.18)",
    "error": "#EF4444",
    "success": "#10B981",
}


def _load_bg_image() -> Optional[str]:
    """Load background image as base64 if exists."""
    bg_path = "assets/landing/market_bg.png"
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None


def inject_auth_css():
    """
    Inject complete CSS for auth pages.
    Targets all Streamlit/BaseWeb components properly.
    """
    bg_image = _load_bg_image()
    
    # Background style
    if bg_image:
        bg_style = f"""
            background-image: 
                radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
                linear-gradient(180deg, rgba(10, 10, 10, 0.92) 0%, rgba(10, 10, 10, 0.98) 100%),
                url('data:image/png;base64,{bg_image}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        bg_style = """
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%),
                linear-gradient(135deg, #0A0A0A 0%, #0F0F0F 50%, #0A0A0A 100%);
        """
    
    st.markdown(f'''
    <style>
    /* ═══════════════════════════════════════════════════════════════════════
       PREMIUM FINTECH AUTH PAGES - COMPLETE CSS OVERRIDE
       Target: Streamlit + BaseWeb components
    ═══════════════════════════════════════════════════════════════════════ */
    
    /* ─── PAGE BACKGROUND ─────────────────────────────────────────────────── */
    .stApp {{
        {bg_style}
    }}
    
    /* Hide Streamlit chrome */
    #MainMenu, footer, header, .stDeployButton {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* ─── MAIN CONTAINER ──────────────────────────────────────────────────── */
    section[data-testid="stMain"] > div {{
        max-width: 520px !important;
        margin: 0 auto !important;
        padding: 40px 24px !important;
    }}
    
    /* ─── FORM CARD (glassmorphism) ───────────────────────────────────────── */
    .auth-card {{
        background: {TOKENS["bg_card"]};
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid {TOKENS["border_subtle"]};
        border-radius: 22px;
        padding: 32px;
        margin: 24px 0;
    }}
    
    /* ─── TEXT INPUT CONTAINER ────────────────────────────────────────────── */
    div[data-testid="stTextInput"] {{
        margin-bottom: 16px !important;
    }}
    
    div[data-testid="stTextInput"] > div {{
        background: transparent !important;
    }}
    
    /* ─── INPUT LABELS ────────────────────────────────────────────────────── */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] > label,
    .stTextInput label {{
        color: {TOKENS["text_secondary"]} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        margin-bottom: 8px !important;
    }}
    
    /* ─── INPUT FIELDS ────────────────────────────────────────────────────── */
    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input,
    .stTextInput input {{
        background: {TOKENS["bg_input"]} !important;
        border: 1px solid {TOKENS["border_input"]} !important;
        border-radius: 14px !important;
        color: {TOKENS["text_primary"]} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 15px !important;
        padding: 14px 16px !important;
        height: 52px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-sizing: border-box !important;
    }}
    
    /* Input wrapper - remove white backgrounds */
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {{
        background: transparent !important;
        border: none !important;
    }}
    
    /* Inner input container */
    div[data-baseweb="input"] > div {{
        background: transparent !important;
        border: none !important;
    }}
    
    /* ─── INPUT FOCUS STATE ───────────────────────────────────────────────── */
    div[data-testid="stTextInput"] input:focus,
    div[data-baseweb="input"] input:focus,
    .stTextInput input:focus {{
        border-color: {TOKENS["border_focus"]} !important;
        box-shadow: 0 0 0 3px {TOKENS["glow"]} !important;
        outline: none !important;
        background: rgba(10, 10, 10, 0.8) !important;
    }}
    
    /* ─── PLACEHOLDERS ────────────────────────────────────────────────────── */
    div[data-testid="stTextInput"] input::placeholder,
    div[data-baseweb="input"] input::placeholder,
    .stTextInput input::placeholder {{
        color: {TOKENS["placeholder"]} !important;
        opacity: 1 !important;
    }}
    
    /* ─── PASSWORD TOGGLE BUTTON (eye icon) ───────────────────────────────── */
    /* Hide the default eye icon completely */
    div[data-testid="stTextInput"] button,
    div[data-baseweb="input"] button {{
        display: none !important;
    }}
    
    /* ─── CHECKBOX (for password toggle) ──────────────────────────────────── */
    div[data-testid="stCheckbox"] {{
        margin-top: 8px !important;
        margin-bottom: 16px !important;
    }}
    
    div[data-testid="stCheckbox"] label {{
        color: {TOKENS["text_muted"]} !important;
        font-size: 13px !important;
        font-weight: 400 !important;
    }}
    
    div[data-testid="stCheckbox"] label span {{
        color: {TOKENS["text_muted"]} !important;
    }}
    
    /* Checkbox input styling */
    div[data-testid="stCheckbox"] input[type="checkbox"] {{
        accent-color: {TOKENS["accent"]} !important;
    }}
    
    /* ─── PRIMARY BUTTON ──────────────────────────────────────────────────── */
    div[data-testid="stButton"] button[kind="primary"],
    .stButton button[kind="primary"] {{
        background: linear-gradient(135deg, {TOKENS["accent"]} 0%, {TOKENS["accent_dark"]} 100%) !important;
        border: none !important;
        border-radius: 16px !important;
        color: {TOKENS["text_primary"]} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        height: 52px !important;
        padding: 0 24px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25) !important;
    }}
    
    div[data-testid="stButton"] button[kind="primary"]:hover,
    .stButton button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.35) !important;
    }}
    
    /* ─── SECONDARY BUTTON ────────────────────────────────────────────────── */
    div[data-testid="stButton"] button[kind="secondary"],
    .stButton button[kind="secondary"] {{
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid {TOKENS["border_subtle"]} !important;
        border-radius: 14px !important;
        color: {TOKENS["text_secondary"]} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        height: 46px !important;
        padding: 0 20px !important;
        transition: all 0.2s ease !important;
    }}
    
    div[data-testid="stButton"] button[kind="secondary"]:hover,
    .stButton button[kind="secondary"]:hover {{
        background: rgba(255, 255, 255, 0.10) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }}
    
    /* ─── FORM CONTAINER ──────────────────────────────────────────────────── */
    div[data-testid="stForm"] {{
        background: transparent !important;
        border: none !important;
    }}
    
    /* ─── ALERT MESSAGES ──────────────────────────────────────────────────── */
    div[data-testid="stAlert"] {{
        background: rgba(16, 185, 129, 0.08) !important;
        border: 1px solid rgba(16, 185, 129, 0.25) !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
    }}
    
    div[data-testid="stAlert"] p {{
        color: {TOKENS["text_secondary"]} !important;
    }}
    
    /* Error alert */
    div[data-testid="stAlert"][data-baseweb="notification"] {{
        background: rgba(239, 68, 68, 0.08) !important;
        border: 1px solid rgba(239, 68, 68, 0.25) !important;
    }}
    
    /* ─── LINKS ───────────────────────────────────────────────────────────── */
    a {{
        color: {TOKENS["text_muted"]} !important;
        text-decoration: none !important;
        border-bottom: 1px solid rgba(156, 163, 175, 0.3) !important;
        transition: all 0.15s ease !important;
    }}
    
    a:hover {{
        color: {TOKENS["text_secondary"]} !important;
        border-bottom-color: {TOKENS["text_secondary"]} !important;
    }}
    
    /* ─── DIVIDER ─────────────────────────────────────────────────────────── */
    hr {{
        border: none !important;
        border-top: 1px solid {TOKENS["border_subtle"]} !important;
        margin: 24px 0 !important;
    }}
    
    /* ─── COLUMNS SPACING ─────────────────────────────────────────────────── */
    div[data-testid="stHorizontalBlock"] {{
        gap: 12px !important;
    }}
    
    </style>
    ''', unsafe_allow_html=True)


def _render_header(title: str, subtitle: str):
    """Render auth page header with logo and titles."""
    html = f'''<div style="text-align: center; padding: 48px 0 32px;"><div style="width: 56px; height: 56px; margin: 0 auto 28px; background: linear-gradient(135deg, {TOKENS["accent"]} 0%, {TOKENS["accent_dark"]} 100%); border-radius: 16px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 40px rgba(16, 185, 129, 0.35);"><svg width="26" height="26" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="4" stroke="white" stroke-width="2"/><circle cx="12" cy="12" r="9" stroke="white" stroke-width="1.5" stroke-dasharray="2 4"/></svg></div><h1 style="font-family: Inter, -apple-system, sans-serif; font-size: 36px; font-weight: 700; color: {TOKENS["text_primary"]}; margin: 0 0 12px 0; letter-spacing: -0.02em; line-height: 1.2;">{title}</h1><p style="font-family: Inter, -apple-system, sans-serif; font-size: 16px; color: {TOKENS["text_muted"]}; margin: 0; font-weight: 400;">{subtitle}</p></div>'''
    st.markdown(html, unsafe_allow_html=True)


def _render_footer_terms():
    """Render footer with terms and privacy links."""
    html = f'<p style="text-align: center; font-family: Inter, sans-serif; font-size: 12px; color: {TOKENS["text_muted"]}; margin-top: 32px; line-height: 1.8; opacity: 0.8;">En créant un compte, vous acceptez nos<br><a href="#" style="color: {TOKENS["text_muted"]};">Conditions d\'utilisation</a> et notre <a href="#" style="color: {TOKENS["text_muted"]};">Politique de confidentialité</a></p>'
    st.markdown(html, unsafe_allow_html=True)


def render_signup(auth_manager=None, sqlite_store=None) -> None:
    """
    Render the signup page with premium fintech design.
    Uses Supabase Auth if configured, falls back to legacy SQLite auth.
    
    Args:
        auth_manager: Legacy AuthManager instance (optional)
        sqlite_store: Legacy SQLiteStore instance (optional)
    """
    inject_auth_css()
    
    _render_header(
        title="Créer un compte",
        subtitle="Accédez aux données institutionnelles MarketGPS"
    )
    
    # Use st.form to ensure all values are submitted together
    with st.form("signup_form"):
        # Form fields
        form_email = st.text_input(
            "Adresse email",
            placeholder="vous@exemple.com"
        )
        
        form_password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Minimum 8 caractères"
        )
        
        form_confirm = st.text_input(
            "Confirmer le mot de passe",
            type="password",
            placeholder="Retapez votre mot de passe"
        )
        
        # Selected plan info
        selected_plan = st.session_state.get('selected_plan')
        if selected_plan:
            plan_name = "Pro Mensuel — 9,99€/mois" if selected_plan == "monthly_9_99" else "Pro Annuel — 50€/an"
            plan_html = f'<div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.20); border-radius: 12px; padding: 14px 18px; margin: 20px 0; display: flex; align-items: center; gap: 12px;"><svg width="18" height="18" fill="{TOKENS["accent"]}" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/></svg><span style="color: {TOKENS["text_secondary"]}; font-size: 14px; font-family: Inter, sans-serif;">Plan sélectionné : <strong style="color: {TOKENS["text_primary"]};">{plan_name}</strong></span></div>'
            st.markdown(plan_html, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        # Submit button inside form
        submitted = st.form_submit_button("Créer mon compte", type="primary", use_container_width=True)
    
    # Process form submission
    if submitted:
        form_email = form_email.strip() if form_email else ""
        
        if not form_email or not form_password or not form_confirm:
            st.error("Veuillez remplir tous les champs")
        elif len(form_password) < 8:
            st.error("Le mot de passe doit contenir au moins 8 caractères")
        elif form_password != form_confirm:
            st.error("Les mots de passe ne correspondent pas")
        elif "@" not in form_email or "." not in form_email:
            st.error("Veuillez entrer une adresse email valide")
        else:
            # Force Supabase signup - import fresh to avoid caching issues
            try:
                from dotenv import load_dotenv
                from pathlib import Path
                import os
                
                # Load .env file
                env_path = Path(__file__).parent.parent / ".env"
                load_dotenv(env_path, override=True)
                
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_ANON_KEY")
                
                if not url or not key:
                    st.error("Configuration Supabase manquante. Vérifiez le fichier .env")
                else:
                    from supabase import create_client
                    
                    client = create_client(url, key)
                    
                    # Attempt signup
                    response = client.auth.sign_up({
                        "email": form_email,
                        "password": form_password,
                        "options": {
                            "email_redirect_to": "http://localhost:8501/auth/callback"
                        }
                    })
                    
                    if response.user:
                        if response.user.email_confirmed_at is None:
                            st.success("Compte créé ! Vérifiez votre email pour confirmer votre inscription.")
                            st.info("📧 Vérifiez votre boîte de réception et cliquez sur le lien de confirmation.")
                        else:
                            st.success("Compte créé et confirmé !")
                            st.session_state.user_id = str(response.user.id)
                            st.session_state.view = 'dashboard'
                            st.rerun()
                    else:
                        st.error("Échec de la création du compte.")
                        
            except Exception as e:
                error_msg = str(e)
                if "already registered" in error_msg.lower():
                    st.error("Cet email est déjà utilisé.")
                elif "password" in error_msg.lower():
                    st.error("Le mot de passe doit contenir au moins 6 caractères.")
                else:
                    st.error(f"Erreur: {error_msg}")
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Footer buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Retour", key="signup_back", use_container_width=True):
            st.session_state.view = 'landing'
            st.rerun()
    with col2:
        if st.button("Déjà inscrit ?", key="signup_to_login", use_container_width=True):
            st.session_state.view = 'login'
            st.rerun()
    
    _render_footer_terms()


def render_login(auth_manager=None) -> None:
    """
    Render the login page with premium fintech design.
    Uses Supabase Auth if configured, falls back to legacy SQLite auth.
    
    Args:
        auth_manager: Legacy AuthManager instance (optional)
    """
    inject_auth_css()
    
    _render_header(
        title="Connexion",
        subtitle="Accédez à votre espace MarketGPS"
    )
    
    # Use st.form to ensure all fields are submitted together
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Adresse email",
            placeholder="vous@exemple.com"
        )
        
        password = st.text_input(
            "Mot de passe",
            type="password",
            placeholder="Votre mot de passe"
        )
        
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
        
        if submitted:
            form_email = email.strip() if email else ""
            form_password = password if password else ""
            
            if not form_email or not form_password:
                st.error("Veuillez remplir tous les champs")
            else:
                # Force Supabase login
                try:
                    from dotenv import load_dotenv
                    from pathlib import Path
                    import os
                    
                    # Load .env file
                    env_path = Path(__file__).parent.parent / ".env"
                    load_dotenv(env_path, override=True)
                    
                    url = os.environ.get("SUPABASE_URL")
                    key = os.environ.get("SUPABASE_ANON_KEY")
                    
                    if not url or not key:
                        st.error("Configuration Supabase manquante.")
                    else:
                        from supabase import create_client
                        
                        client = create_client(url, key)
                        
                        response = client.auth.sign_in_with_password({
                            "email": form_email,
                            "password": form_password
                        })
                        
                        if response.user and response.session:
                            st.session_state.user_id = str(response.user.id)
                            st.session_state.user_email = response.user.email
                            st.session_state.access_token = response.session.access_token
                            st.session_state.view = 'dashboard'
                            st.success("Connexion réussie !")
                            st.rerun()
                        else:
                            st.error("Échec de la connexion.")
                            
                except Exception as e:
                    error_msg = str(e)
                    if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
                        st.error("Email ou mot de passe incorrect.")
                    elif "not confirmed" in error_msg.lower():
                        st.error("Veuillez confirmer votre email avant de vous connecter.")
                    else:
                        st.error(f"Erreur: {error_msg}")
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Footer buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Retour", key="login_back", use_container_width=True):
            st.session_state.view = 'landing'
            st.rerun()
    with col2:
        if st.button("Créer un compte", key="login_to_signup", use_container_width=True):
            st.session_state.view = 'signup'
            st.rerun()
    
    # Forgot password link
    if SUPABASE_ENABLED:
        if st.button("Mot de passe oublié ?", key="login_forgot", use_container_width=True):
            st.session_state.view = 'forgot-password'
            st.rerun()
    else:
        st.markdown(f'<p style="text-align: center; margin-top: 24px;"><a href="#" style="color: {TOKENS["text_muted"]}; font-size: 13px; font-family: Inter, sans-serif;">Mot de passe oublié ?</a></p>', unsafe_allow_html=True)
