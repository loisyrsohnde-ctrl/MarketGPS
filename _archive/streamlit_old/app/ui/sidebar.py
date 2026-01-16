"""
MarketGPS - Sidebar Component
Professional dark theme with toggle functionality
"""
import streamlit as st
from typing import Dict, Optional
import os


def render_sidebar_v2(
    scope_counts: Dict[str, int],
    user_info: Optional[Dict] = None,
    is_authenticated: bool = False
):
    """
    Render the redesigned sidebar with:
    - Logo
    - Navigation (Dashboard, Explorer, Liste de suivi, Marchés)
    - Marchés (US/Europe, Afrique) with counts
    - Paramètres (Toggle, Thème, Aide)
    - Compte (Profil, Déconnexion)
    """
    
    # Check if Supabase auth is enabled
    try:
        from auth.supabase_client import SupabaseAuth
        from auth.session import SessionManager
        from auth.gating import EntitlementChecker
        SUPABASE_AUTH_ENABLED = bool(os.environ.get("SUPABASE_URL"))
    except ImportError:
        SUPABASE_AUTH_ENABLED = False
        SessionManager = None
        EntitlementChecker = None
    
    with st.sidebar:
        # ═══════════════════════════════════════════════════════════════════════════
        # LOGO SECTION
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="display:flex;align-items:center;gap:12px;padding:20px 16px 24px;border-bottom:1px solid rgba(255,255,255,0.06);">
            <div style="width:42px;height:42px;background:linear-gradient(135deg,#22C55E 0%,#16A34A 100%);border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(34,197,94,0.3);">
                <span style="font-size:20px;color:white;">◉</span>
            </div>
            <div style="font-size:20px;font-weight:700;color:#FFFFFF;letter-spacing:-0.5px;">MarketGPS</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # ═══════════════════════════════════════════════════════════════════════════
        # NAVIGATION
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.8px;padding:20px 16px 10px;">
            Navigation
        </div>
        ''', unsafe_allow_html=True)
        
        current_view = st.session_state.get('view', 'dashboard')
        
        # Dashboard
        if st.button(
            "📊  Dashboard",
            key="nav_dashboard",
            use_container_width=True,
            type="primary" if current_view == "dashboard" else "secondary"
        ):
            st.session_state.view = 'dashboard'
            st.rerun()
        
        # Explorer
        if st.button(
            "🔍  Explorer",
            key="nav_explorer",
            use_container_width=True,
            type="primary" if current_view == "explorer" else "secondary"
        ):
            st.session_state.view = 'explorer'
            st.rerun()
        
        # Liste de suivi
        if st.button(
            "⭐  Liste de suivi",
            key="nav_watchlist",
            use_container_width=True,
            type="primary" if current_view == "watchlist" else "secondary"
        ):
            st.session_state.view = 'watchlist'
            st.rerun()
        
        # Marchés
        if st.button("📈  Marchés", key="nav_markets", use_container_width=True):
            pass  # Future feature
        
        # ═══════════════════════════════════════════════════════════════════════════
        # MARCHÉS SECTION
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.8px;padding:28px 16px 10px;">
            Marchés
        </div>
        ''', unsafe_allow_html=True)
        
        us_eu_count = scope_counts.get('US_EU', 0)
        africa_count = scope_counts.get('AFRICA', 0)
        current_scope = st.session_state.get('market_scope', 'US_EU')
        
        # US / Europe
        if st.button(
            f"🇺🇸🇪🇺  US / Europe ({us_eu_count:,})",
            key="scope_useu",
            use_container_width=True,
            type="primary" if current_scope == "US_EU" else "secondary"
        ):
            st.session_state.market_scope = 'US_EU'
            st.session_state.market_filter = 'ALL'
            st.rerun()
        
        # Afrique
        if st.button(
            f"🌍  Afrique ({africa_count:,})",
            key="scope_africa",
            use_container_width=True,
            type="primary" if current_scope == "AFRICA" else "secondary"
        ):
            st.session_state.market_scope = 'AFRICA'
            st.session_state.market_filter = 'ALL'
            st.rerun()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # PARAMÈTRES
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.8px;padding:28px 16px 10px;">
            Paramètres
        </div>
        ''', unsafe_allow_html=True)
        
        # Toggle sidebar visibility option (stored in session_state)
        sidebar_visible = st.session_state.get('sidebar_visible', True)
        toggle_label = "👁️  Cacher le menu" if sidebar_visible else "👁️  Afficher le menu"
        if st.button(toggle_label, key="toggle_sidebar", use_container_width=True):
            st.session_state.sidebar_visible = not sidebar_visible
            # Note: Streamlit can't truly hide sidebar programmatically, 
            # but we can use this state for future JS integration
        
        if st.button("🎨  Thème", key="nav_theme", use_container_width=True):
            pass  # Future feature
        
        if st.button("❓  Aide", key="nav_help", use_container_width=True):
            pass  # Future feature
        
        # ═══════════════════════════════════════════════════════════════════════════
        # COMPTE
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.8px;padding:28px 16px 10px;">
            Compte
        </div>
        ''', unsafe_allow_html=True)
        
        is_supabase_auth = SUPABASE_AUTH_ENABLED and SessionManager and SessionManager.is_authenticated()
        is_legacy_auth = st.session_state.get('user_id') is not None and st.session_state.get('user_id') != 'default'
        
        if is_supabase_auth or is_legacy_auth:
            if is_supabase_auth:
                if st.button("👤  Mon compte", key="nav_account", use_container_width=True):
                    st.session_state.view = 'account'
                    st.rerun()
                
                if st.button("💎  Abonnement", key="nav_billing", use_container_width=True):
                    st.session_state.view = 'billing'
                    st.rerun()
                
                if st.button("🚪  Déconnexion", key="nav_logout", use_container_width=True):
                    auth = SupabaseAuth()
                    auth.sign_out()
                    SessionManager.clear_session()
                    EntitlementChecker.clear_cache()
                    st.session_state.view = 'landing'
                    st.rerun()
            else:
                # Legacy auth
                if st.button("👤  Profil", key="nav_profile", use_container_width=True):
                    st.session_state.view = 'profile'
                    st.rerun()
                
                if st.button("🚪  Déconnexion", key="nav_logout_legacy", use_container_width=True):
                    from app.auth import logout
                    logout()
                    st.session_state.view = 'landing'
                    st.rerun()
        else:
            if st.button("🔑  Se connecter", key="nav_login_side", use_container_width=True):
                st.session_state.view = 'login'
                st.rerun()
        
        # ═══════════════════════════════════════════════════════════════════════════
        # VERSION FOOTER
        # ═══════════════════════════════════════════════════════════════════════════
        st.markdown('''
        <div style="position:absolute;bottom:20px;left:16px;right:16px;text-align:center;">
            <div style="font-size:10px;color:#475569;">MarketGPS v13.1</div>
        </div>
        ''', unsafe_allow_html=True)
