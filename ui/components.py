"""
MarketGPS — UI Components
Composants réutilisables pour l'interface.
"""

import streamlit as st
from .theme import DesignTokens


def render_header(title: str = "MarketGPS", subtitle: str = ""):
    """Affiche le header de l'application."""
    st.markdown(f'''
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;">
        <div style="font-size:36px;">🧭</div>
        <div>
            <div class="gps-h1">{title}</div>
            <div style="font-size:13px;color:{DesignTokens.TEXT_MUTED};">{subtitle}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_footer():
    """Affiche le footer de conformité."""
    st.markdown(f'''
    <div class="gps-footer">
        <div class="gps-footer-text">
            Outil d'analyse statistique à but éducatif. Aucune information ne constitue un conseil en investissement.<br>
            Le capital est exposé au risque de marché. Les performances passées ne préjugent pas des performances futures.
        </div>
    </div>
    ''', unsafe_allow_html=True)


def ui_card(content: str, title: str = None):
    """Génère une card HTML."""
    header = f'<div style="font-weight:600;margin-bottom:12px;color:{DesignTokens.TEXT_PRIMARY};">{title}</div>' if title else ""
    return f'<div class="gps-card">{header}{content}</div>'


def ui_chip(text: str, variant: str = "neutral") -> str:
    """Génère un chip/badge."""
    return f'<span class="gps-chip gps-chip-{variant}">{text}</span>'


def ui_badge(variant: str = "success") -> str:
    """Génère un badge point."""
    return f'<span class="gps-badge gps-badge-{variant}"></span>'


def ui_metric_card(label: str, value: str, delta: str = None, variant: str = "default"):
    """Affiche une métrique dans une card."""
    delta_html = f'<div style="font-size:12px;color:{DesignTokens.ACCENT if delta and delta.startswith("+") else DesignTokens.WARNING};">{delta}</div>' if delta else ""
    st.markdown(f'''
    <div class="gps-card" style="text-align:center;">
        <div class="gps-label">{label}</div>
        <div class="gps-value">{value}</div>
        {delta_html}
    </div>
    ''', unsafe_allow_html=True)


def get_state_chip(state: str) -> str:
    """Retourne le chip HTML pour un état de marché."""
    if "haute" in state.lower():
        return ui_chip("↑ Extension haute", "high")
    elif "basse" in state.lower():
        return ui_chip("↓ Extension basse", "low")
    return ui_chip("⚖ Équilibre", "neutral")


def get_quality_badge(coverage: float) -> str:
    """Retourne le badge de qualité."""
    if coverage >= 0.98:
        return ui_badge("success")
    elif coverage >= 0.90:
        return ui_badge("warning")
    return ui_badge("danger")


def render_ticker_card(ticker_data: dict, selected: bool = False):
    """Affiche une card compacte de ticker."""
    state_chip = get_state_chip(ticker_data['state'])
    quality = get_quality_badge(ticker_data['coverage'])
    selected_class = "selected" if selected else ""
    
    return f'''
    <div class="gps-card-compact {selected_class}">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-weight:600;min-width:60px;color:{DesignTokens.TEXT_PRIMARY};">{ticker_data['ticker']}</span>
            {state_chip}
        </div>
        <div style="display:flex;align-items:center;gap:12px;">
            {quality}
            <span style="color:{DesignTokens.TEXT_SECONDARY};">{ticker_data['z_score']:+.2f}σ</span>
            <span style="font-weight:700;color:{DesignTokens.ACCENT};">{ticker_data['score']:.0f}</span>
        </div>
    </div>
    '''


def render_system_status(state, restricted: bool = False):
    """Affiche l'état du système."""
    if restricted:
        st.markdown(f'''
        <div class="gps-card" style="background:rgba(245,196,82,0.08);border-color:rgba(245,196,82,0.3);">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:18px;">📚</span>
                <div>
                    <div style="font-size:13px;font-weight:600;color:{DesignTokens.WARNING};">Mode restreint</div>
                    <div style="font-size:12px;color:{DesignTokens.TEXT_MUTED};">Univers limité (fichier universe_us.csv absent)</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Univers", state.universe_size)
    with c2:
        st.metric("Éligibles", state.eligible_count)
    with c3:
        st.metric("Pool", len(state.pool_members))
    with c4:
        from datetime import datetime
        st.metric("MAJ", datetime.now().strftime("%H:%M"))
