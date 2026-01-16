"""
Billing Page for MarketGPS
Subscription plans and Stripe checkout
"""

import streamlit as st
import sys
import os
import httpx
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth.session import SessionManager, require_auth
from auth.gating import EntitlementChecker


def inject_billing_css():
    """Inject premium dark theme CSS for billing page."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    .stApp { background: #0A0A0A !important; }
    
    section[data-testid="stMain"] {
        background: 
            radial-gradient(ellipse at 50% 0%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
            #0A0A0A !important;
    }
    
    section[data-testid="stMain"] > div {
        max-width: 900px !important;
        margin: 0 auto !important;
        padding: 40px 24px !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Pricing card */
    .pricing-card {
        background: rgba(18, 18, 18, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .pricing-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.1);
    }
    
    .pricing-card.featured {
        border-color: rgba(16, 185, 129, 0.5);
        background: linear-gradient(180deg, rgba(16, 185, 129, 0.08) 0%, rgba(18, 18, 18, 0.9) 100%);
    }
    
    .plan-badge {
        display: inline-block;
        padding: 4px 12px;
        background: linear-gradient(135deg, #10B981, #059669);
        border-radius: 20px;
        color: white;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 16px;
    }
    
    .plan-name {
        color: #FFFFFF;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }
    
    .plan-price {
        color: #10B981;
        font-size: 48px;
        font-weight: 800;
        margin-bottom: 4px;
        font-family: 'Inter', sans-serif;
    }
    
    .plan-price-suffix {
        color: #9CA3AF;
        font-size: 16px;
        margin-bottom: 24px;
    }
    
    .plan-feature {
        color: #E5E7EB;
        font-size: 15px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-family: 'Inter', sans-serif;
    }
    
    .plan-feature:last-child {
        border-bottom: none;
    }
    
    .plan-feature-icon {
        color: #10B981;
        margin-right: 8px;
    }
    
    button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 14px 24px !important;
    }
    
    button[kind="primary"]:hover {
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3) !important;
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
    """Render page header."""
    # Check for success/canceled params
    query_params = st.query_params
    
    if query_params.get("success") == "1":
        st.success("🎉 Paiement réussi ! Votre abonnement est maintenant actif.")
        EntitlementChecker.clear_cache()
    elif query_params.get("canceled") == "1":
        st.warning("Paiement annulé. Vous pouvez réessayer quand vous voulez.")
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 48px;">
        <h1 style="
            color: #FFFFFF;
            font-size: 36px;
            font-weight: 800;
            margin: 0 0 12px 0;
            font-family: 'Inter', sans-serif;
        ">Choisissez votre plan</h1>
        <p style="
            color: #9CA3AF;
            font-size: 18px;
            margin: 0;
            font-family: 'Inter', sans-serif;
        ">Débloquez l'accès complet aux données institutionnelles</p>
    </div>
    """, unsafe_allow_html=True)


def render_pricing_cards():
    """Render pricing comparison cards."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="pricing-card">
            <div class="plan-name">Mensuel</div>
            <div class="plan-price">9,99€</div>
            <div class="plan-price-suffix">par mois</div>
            <div style="margin: 24px 0;">
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> 200 calculs/jour</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Tous les marchés (US, EU, Afrique)</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Watchlist personnalisée</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Alertes personnalisées</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Historique complet</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Export CSV</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("S'abonner au Mensuel", use_container_width=True, key="subscribe_monthly"):
            start_checkout("monthly")
    
    with col2:
        st.markdown("""
        <div class="pricing-card featured">
            <div class="plan-badge">💎 MEILLEURE OFFRE</div>
            <div class="plan-name">Annuel</div>
            <div class="plan-price">50€</div>
            <div class="plan-price-suffix">par an <span style="color: #10B981;">(économisez 58%)</span></div>
            <div style="margin: 24px 0;">
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> 200 calculs/jour</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Tous les marchés (US, EU, Afrique)</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Watchlist personnalisée</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Alertes personnalisées</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Historique complet</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Export CSV</div>
                <div class="plan-feature"><span class="plan-feature-icon">✓</span> Support prioritaire</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("S'abonner à l'Annuel", type="primary", use_container_width=True, key="subscribe_yearly"):
            start_checkout("yearly")


def start_checkout(plan: str):
    """Start Stripe Checkout session."""
    backend_url = os.environ.get("BACKEND_API_BASE_URL", "http://localhost:8000")
    access_token = SessionManager.get_access_token()
    app_base_url = os.environ.get("APP_BASE_URL", "http://localhost:8501")
    
    if not access_token:
        st.error("Veuillez vous connecter pour vous abonner.")
        return
    
    try:
        with st.spinner("Redirection vers le paiement sécurisé..."):
            with httpx.Client() as client:
                response = client.post(
                    f"{backend_url}/billing/checkout-session",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "plan": plan,
                        "success_url": f"{app_base_url}/billing?success=1",
                        "cancel_url": f"{app_base_url}/billing?canceled=1",
                    },
                    timeout=15.0,
                )
                
                if response.status_code == 200:
                    checkout_url = response.json().get("checkout_url")
                    
                    # Redirect to Stripe
                    st.markdown(f"""
                    <script>window.location.href = "{checkout_url}";</script>
                    <meta http-equiv="refresh" content="0; url={checkout_url}">
                    <p style="color: #9CA3AF; text-align: center;">
                        Redirection en cours... 
                        <a href="{checkout_url}" style="color: #10B981;">Cliquez ici</a> si la page ne se charge pas.
                    </p>
                    """, unsafe_allow_html=True)
                else:
                    error_detail = response.json().get("detail", "Erreur inconnue")
                    st.error(f"Erreur: {error_detail}")
                    
    except httpx.ConnectError:
        st.error("Impossible de contacter le serveur de paiement. Réessayez plus tard.")
    except Exception as e:
        st.error(f"Erreur: {e}")


def render_current_plan():
    """Show current plan status if subscribed."""
    entitlements = EntitlementChecker.get_cached_entitlements()
    
    if entitlements and entitlements.is_paid:
        st.markdown(f"""
        <div style="
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-bottom: 32px;
        ">
            <div style="color: #10B981; font-size: 16px; font-weight: 600;">
                ✓ Vous êtes abonné au plan {entitlements.plan}
            </div>
            <div style="color: #9CA3AF; font-size: 14px; margin-top: 8px;">
                Accès complet à toutes les fonctionnalités
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Gérer mon abonnement", use_container_width=True, key="manage_billing"):
            from app.pages._04_account import open_customer_portal
            open_customer_portal()


def render_free_comparison():
    """Show FREE vs PAID comparison."""
    st.markdown("""
    <div style="margin-top: 48px;">
        <h3 style="color: #FFFFFF; text-align: center; margin-bottom: 24px; font-family: 'Inter', sans-serif;">
            Comparaison FREE vs PREMIUM
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    comparison_data = [
        ("Calculs par jour", "10", "200"),
        ("Marchés US & EU", "✓", "✓"),
        ("Marchés Afrique", "✗", "✓"),
        ("Watchlist", "✗", "✓"),
        ("Alertes", "✗", "✓"),
        ("Export CSV", "✗", "✓"),
        ("Support", "Standard", "Prioritaire"),
    ]
    
    st.markdown("""
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <th style="text-align: left; padding: 12px; color: #9CA3AF;">Fonctionnalité</th>
                <th style="text-align: center; padding: 12px; color: #9CA3AF;">FREE</th>
                <th style="text-align: center; padding: 12px; color: #10B981;">PREMIUM</th>
            </tr>
        </thead>
        <tbody>
    """, unsafe_allow_html=True)
    
    for feature, free_val, premium_val in comparison_data:
        free_color = "#EF4444" if free_val == "✗" else "#E5E7EB"
        premium_color = "#10B981" if premium_val == "✓" else "#E5E7EB"
        
        st.markdown(f"""
        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
            <td style="padding: 12px; color: #E5E7EB;">{feature}</td>
            <td style="padding: 12px; text-align: center; color: {free_color};">{free_val}</td>
            <td style="padding: 12px; text-align: center; color: {premium_color};">{premium_val}</td>
        </tr>
        """, unsafe_allow_html=True)
    
    st.markdown("</tbody></table>", unsafe_allow_html=True)


@require_auth
def page_billing():
    """Render billing page."""
    st.set_page_config(
        page_title="Tarifs - MarketGPS",
        page_icon="💎",
        layout="centered",
    )
    
    inject_billing_css()
    render_header()
    render_current_plan()
    render_pricing_cards()
    render_free_comparison()
    
    # Back button
    st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
    if st.button("← Retour", use_container_width=True, key="back"):
        st.session_state.view = "dashboard"
        st.rerun()


if __name__ == "__main__":
    page_billing()
