"""
Account Page for MarketGPS
User profile, subscription status, and settings
"""

import streamlit as st
import sys
import os
import httpx
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.session import SessionManager, require_auth
from auth.gating import EntitlementChecker
from auth.supabase_client import get_supabase_client


def inject_account_css():
    """Inject premium dark theme CSS for account page."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { background: #0A0A0A !important; }
    
    section[data-testid="stMain"] {
        background: 
            radial-gradient(ellipse at 20% 20%, rgba(16, 185, 129, 0.06) 0%, transparent 50%),
            #0A0A0A !important;
    }
    
    section[data-testid="stMain"] > div {
        max-width: 720px !important;
        margin: 0 auto !important;
        padding: 40px 24px !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Card styling */
    .account-card {
        background: rgba(18, 18, 18, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }
    
    .card-title {
        color: #FFFFFF;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
        font-family: 'Inter', sans-serif;
    }
    
    .status-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    .status-active {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-free {
        background: rgba(156, 163, 175, 0.15);
        color: #9CA3AF;
        border: 1px solid rgba(156, 163, 175, 0.3);
    }
    
    .status-canceled {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    div[data-testid="stTextInput"] input {
        background: rgba(10, 10, 10, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #FFFFFF !important;
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
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render page header."""
    st.markdown("""
    <div style="margin-bottom: 32px;">
        <h1 style="
            color: #FFFFFF;
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 8px 0;
            font-family: 'Inter', sans-serif;
        ">Mon Compte</h1>
        <p style="
            color: #9CA3AF;
            font-size: 16px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Gérez votre profil et votre abonnement</p>
    </div>
    """, unsafe_allow_html=True)


def render_profile_card():
    """Render profile information card."""
    email = SessionManager.get_email()
    user_id = SessionManager.get_user_id()
    
    # Get profile from Supabase
    client = get_supabase_client()
    try:
        response = client.table('profiles').select('*').eq('id', user_id).single().execute()
        profile = response.data
    except:
        profile = {}
    
    display_name = profile.get('display_name', '')
    
    st.markdown('<div class="account-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">👤 Profil</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #10B981, #059669);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            color: white;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
        ">{(display_name or email or 'U')[0].upper()}</div>
        """, unsafe_allow_html=True)
    
    with col2:
        new_name = st.text_input(
            "Nom d'affichage",
            value=display_name,
            key="account_display_name",
        )
        
        st.markdown(f"""
        <p style="color: #9CA3AF; font-size: 14px; margin: 8px 0 0 0;">
            📧 {email}
        </p>
        """, unsafe_allow_html=True)
    
    if st.button("Mettre à jour le profil", key="update_profile"):
        try:
            client.table('profiles').update({
                'display_name': new_name
            }).eq('id', user_id).execute()
            st.success("Profil mis à jour !")
        except Exception as e:
            st.error(f"Erreur: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_subscription_card():
    """Render subscription status card."""
    entitlements = EntitlementChecker.get_cached_entitlements()
    
    if not entitlements:
        st.warning("Impossible de charger les informations d'abonnement.")
        return
    
    # Determine badge class
    if entitlements.is_paid:
        badge_class = "status-active"
        badge_text = f"✓ {entitlements.plan}"
    elif entitlements.status == 'canceled':
        badge_class = "status-canceled"
        badge_text = "Annulé"
    else:
        badge_class = "status-free"
        badge_text = "FREE"
    
    st.markdown(f'''
    <div class="account-card">
        <div class="card-title">💎 Abonnement</div>
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
            <span class="status-badge {badge_class}">{badge_text}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Show details
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Requêtes aujourd'hui", f"{entitlements.daily_requests_used}/{entitlements.daily_requests_limit}")
    
    with col2:
        remaining = entitlements.daily_requests_remaining
        color = "#10B981" if remaining > 5 else "#F59E0B" if remaining > 0 else "#EF4444"
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="color: #9CA3AF; font-size: 14px;">Restantes</div>
            <div style="color: {color}; font-size: 24px; font-weight: 700;">{remaining}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if entitlements.current_period_end and entitlements.is_paid:
        try:
            end_date = datetime.fromisoformat(entitlements.current_period_end.replace('Z', '+00:00'))
            st.markdown(f"""
            <p style="color: #9CA3AF; font-size: 14px; margin-top: 16px;">
                Prochain renouvellement: {end_date.strftime('%d/%m/%Y')}
            </p>
            """, unsafe_allow_html=True)
        except:
            pass
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Action buttons
    if entitlements.is_paid:
        if st.button("Gérer mon abonnement", use_container_width=True, key="manage_subscription"):
            open_customer_portal()
    else:
        if st.button("Passer à Premium", type="primary", use_container_width=True, key="upgrade"):
            st.session_state.view = "billing"
            st.rerun()


def open_customer_portal():
    """Open Stripe Customer Portal."""
    backend_url = os.environ.get("BACKEND_API_BASE_URL", "http://localhost:8000")
    access_token = SessionManager.get_access_token()
    
    if not access_token:
        st.error("Session invalide. Veuillez vous reconnecter.")
        return
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{backend_url}/billing/portal-session",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10.0,
            )
            
            if response.status_code == 200:
                portal_url = response.json().get("portal_url")
                st.markdown(f"""
                <script>window.open("{portal_url}", "_blank");</script>
                <meta http-equiv="refresh" content="0; url={portal_url}">
                """, unsafe_allow_html=True)
                st.success("Redirection vers le portail Stripe...")
            else:
                st.error("Erreur lors de l'ouverture du portail.")
    except Exception as e:
        st.error(f"Erreur de connexion: {e}")


def render_logout_button():
    """Render logout button."""
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    
    if st.button("Se déconnecter", use_container_width=True, key="logout"):
        from auth.supabase_client import SupabaseAuth
        auth = SupabaseAuth()
        auth.sign_out()
        SessionManager.clear_session()
        EntitlementChecker.clear_cache()
        st.session_state.view = "landing"
        st.rerun()


@require_auth
def page_account():
    """Render account page."""
    st.set_page_config(
        page_title="Mon Compte - MarketGPS",
        page_icon="👤",
        layout="centered",
    )
    
    inject_account_css()
    render_header()
    render_profile_card()
    render_subscription_card()
    render_logout_button()
    
    # Back button
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if st.button("← Retour au dashboard", use_container_width=True, key="back_to_dashboard"):
        st.session_state.view = "dashboard"
        st.rerun()


if __name__ == "__main__":
    page_account()
