"""
MarketGPS v13.1 - Glassmorphism Dark Dashboard + Landing + Supabase Auth + Stripe Billing
Premium Fintech Design with Professional Trading Interface.
"""
from app.ui.filters import (
    render_top_bar, render_category_pills, render_period_selector,
    render_explorer_filters, render_pagination
)
from app.ui.cards import (
    render_score_gauge, render_pillar_bars, render_kpi_cards,
    render_data_badges, render_asset_row_v2, render_candlestick_chart,
    get_score_color_single, get_semantic_label, get_logo_html,
    render_asset_detail_section
)
from app.ui.sidebar import render_sidebar_v2
from app.ui.glassmorphism import inject_glassmorphism_css
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from core.config import get_config
from core.compliance import sanitize_text
from storage.sqlite_store import SQLiteStore
from app.auth_pages import render_signup, render_login
from app.landing import render_full_landing_page
from app.company_info import get_company_description, get_company_sector
from app.auth import AuthManager, save_avatar, is_logged_in, logout, get_current_user_id
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import new UI components

# Supabase Auth imports (new system)
try:
    from auth.supabase_client import SupabaseAuth
    from auth.session import SessionManager, get_current_user
    from auth.gating import EntitlementChecker, check_usage_limit
    SUPABASE_AUTH_ENABLED = bool(os.environ.get("SUPABASE_URL"))
except ImportError:
    SUPABASE_AUTH_ENABLED = False

# Legacy auth imports (fallback)

# Page configuration - MUST be first
st.set_page_config(
    page_title="MarketGPS",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================
# CSS INJECTION - Glassmorphism Dark Theme
# ============================================

def inject_premium_css():
    """Inject CSS - now delegates to glassmorphism module."""
    inject_glassmorphism_css()


# ============================================
# DATA LOADING FUNCTIONS
# ============================================
@st.cache_resource
def get_sqlite_store():
    """Get SQLite store singleton with schema initialization."""
    config = get_config()
    store = SQLiteStore(str(config.storage.sqlite_path))
    # Ensure all tables exist (especially auth tables)
    store.ensure_schema()
    return store


@st.cache_resource
def get_auth_manager():
    return AuthManager(get_sqlite_store())


@st.cache_data(ttl=30)
def load_top_assets(asset_type: str = "All", limit: int = 30, market_scope: str = "US_EU", market_filter: str = "ALL") -> List[Dict]:
    """Load top scored assets with optional filters."""
    store = get_sqlite_store()

    type_filter = None if asset_type in ("All", "Tous") else asset_type

    # Get assets
    assets = store.get_top_scored_assets(
        market_scope=market_scope,
        asset_type=type_filter,
        limit=limit * 2  # Get more to filter locally
    )

    # Apply market filter locally (US vs EU)
    if market_filter and market_filter not in ("ALL", "Tous"):
        if market_filter == "US":
            assets = [a for a in assets if a.get(
                'market_code', '').startswith('US')]
        elif market_filter == "EU":
            assets = [a for a in assets if not a.get('market_code', '').startswith(
                'US') and a.get('market_scope') == 'US_EU']

    return assets[:limit]


@st.cache_data(ttl=60)
def load_asset_detail(asset_id: str) -> Optional[Dict]:
    """Load detailed asset information."""
    store = get_sqlite_store()
    return store.get_asset_detail(asset_id)


@st.cache_data(ttl=60)
def get_asset_counts(market_scope: str = "US_EU") -> Dict[str, int]:
    """Get count of assets by type."""
    store = get_sqlite_store()
    return store.count_by_type(market_scope)


@st.cache_data(ttl=60)
def get_scope_counts() -> Dict[str, int]:
    """Get count by market scope."""
    store = get_sqlite_store()
    return store.count_by_scope()


@st.cache_data(ttl=300)
def get_landing_metrics(scope: str = "US_EU") -> Dict:
    """Get landing page metrics."""
    store = get_sqlite_store()
    return store.get_landing_metrics(scope)


def load_price_history(asset_id: str, market_scope: str = "US_EU") -> Optional[pd.DataFrame]:
    """Load price history from Parquet."""
    config = get_config()

    ticker = asset_id
    for suffix in ['.US', '_US', '.EU', '_EU', '.PA', '.XETRA', '.LSE', '.JSE']:
        ticker = ticker.replace(suffix, '')

    for bars_dir in [config.storage.parquet_dir / market_scope.lower() / "bars_daily",
                     config.storage.parquet_dir / "bars_daily"]:
        if not bars_dir.exists():
            continue
        for pq_file in bars_dir.glob(f"{ticker}*.parquet"):
            try:
                df = pd.read_parquet(pq_file)
                if df is not None and not df.empty:
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.set_index('date')
                    return df
            except:
                continue
    return None


def get_current_price(asset: Dict, asset_id: str = None, market_scope: str = "US_EU") -> Optional[float]:
    """
    Get current price for an asset.
    Tries: 1) last_price from scores_latest, 2) last close from Parquet data.

    Returns:
        float: Current price or None if not available
    """
    # Try from asset dict first (from scores_latest)
    last_price = asset.get('last_price')
    if last_price and last_price > 0:
        return float(last_price)

    # Fallback: get from Parquet
    if asset_id:
        df = load_price_history(asset_id, market_scope)
        if df is not None and not df.empty:
            df.columns = [c.lower() for c in df.columns]
            if 'close' in df.columns:
                return float(df['close'].iloc[-1])
            elif len(df.columns) > 0:
                # Fallback: use the last value of the first numeric column
                try:
                    return float(df.iloc[-1, 0])
                except:
                    pass

    return None


def format_price(price: Optional[float], currency: str = "USD") -> str:
    """Format price for display."""
    if price is None or price <= 0:
        return "—"

    if price < 1:
        return f"{price:.4f} {currency}"
    elif price < 100:
        return f"{price:.2f} {currency}"
    else:
        return f"{price:.2f} {currency}"


# ============================================
# ON-DEMAND SCORING
# ============================================
def fetch_and_score_asset(asset_id: str, user_id: str = "default") -> dict:
    """Fetch price data and calculate score."""
    store = get_sqlite_store()

    # Check quota
    if not store.can_calculate_score(user_id):
        return {'success': False, 'message': "Quota journalier atteint. Passez à Pro pour plus de calculs."}

    try:
        from providers import get_provider
        from pipeline.features import calculate_features
        from pipeline.scoring import ScoringEngine
        from storage.parquet_store import ParquetStore

        asset = load_asset_detail(asset_id)
        if not asset:
            return {'success': False, 'message': "Actif non trouvé"}

        ticker = asset.get('symbol', asset_id.split('.')[0])
        market_scope = asset.get('market_scope', 'US_EU')
        asset_type = asset.get('asset_type', 'EQUITY')
        exchange = asset_id.split('.')[-1] if '.' in asset_id else 'US'

        provider = get_provider("auto")

        with st.spinner(f"Téléchargement des données pour {ticker}..."):
            bars_df = provider.get_bars(f"{ticker}.{exchange}", days=504)

        if bars_df is None or bars_df.empty:
            return {'success': False, 'message': "Impossible de récupérer les données"}

        pq_store = ParquetStore(market_scope=market_scope)
        pq_store.save_bars(asset_id, bars_df)

        with st.spinner("Calcul des indicateurs..."):
            features = calculate_features(bars_df)

        if not features:
            return {'success': False, 'message': "Données insuffisantes"}

        engine = ScoringEngine()
        score_result = engine.calculate_score(
            features=features, asset_type=asset_type, fundamentals=None)

        with store._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO scores_latest 
                (asset_id, market_scope, score_total, score_momentum, score_safety, 
                 confidence, rsi, vol_annual, max_drawdown, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                asset_id, market_scope, score_result.get('score_total'),
                score_result.get('score_momentum'), score_result.get(
                    'score_safety'),
                score_result.get('confidence', 70), features.get('rsi'),
                features.get('volatility_annual'), features.get(
                    'max_drawdown_12m'),
            ))

        # Consume quota
        store.consume_calculation_quota(user_id)

        load_asset_detail.clear()
        return {'success': True, 'message': "Score calculé avec succès"}

    except Exception as e:
        return {'success': False, 'message': f"Erreur: {str(e)}"}


# ============================================
# WATCHLIST FUNCTIONS
# ============================================
def get_watchlist(user_id: str = "default") -> List[str]:
    store = get_sqlite_store()
    with store._get_conn() as conn:
        return [row[0] for row in conn.execute(
            "SELECT asset_id FROM watchlist WHERE user_id = ?", (user_id,)
        ).fetchall()]


def add_to_watchlist(asset_id: str, ticker: str, market_code: str = 'US', user_id: str = "default"):
    store = get_sqlite_store()
    with store._get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (asset_id, ticker, market_code, user_id) VALUES (?, ?, ?, ?)",
            (asset_id, ticker, market_code, user_id)
        )


def remove_from_watchlist(asset_id: str, user_id: str = "default"):
    store = get_sqlite_store()
    with store._get_conn() as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE asset_id = ? AND user_id = ?", (asset_id, user_id))


# ============================================
# CHART COMPONENTS
# ============================================
def render_gauge_chart(score: float) -> go.Figure:
    """Create semi-circle gauge."""
    if score is None:
        score = 0

    color = "#10B981" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "/100", 'font': {'size': 42,
                                           'color': '#FFFFFF', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': 'rgba(255,255,255,0.08)',
            'borderwidth': 0,
        }
    ))

    fig.update_layout(
        height=180,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Inter'}
    )
    return fig


def render_candlestick_chart(df: pd.DataFrame, days: int = 30) -> go.Figure:
    """Create candlestick chart.

    Args:
        df: DataFrame with price history
        days: Number of days to show (default 30)
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(height=200, paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(26,26,26,0.9)')
        return fig

    df = df.tail(days).copy()
    df.columns = [c.lower() for c in df.columns]

    if all(c in df.columns for c in ['open', 'high', 'low', 'close']):
        fig = go.Figure(go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            increasing_line_color='#10B981', decreasing_line_color='#6B7280',
            increasing_fillcolor='#10B981', decreasing_fillcolor='#6B7280'
        ))
    else:
        close_col = 'close' if 'close' in df.columns else df.columns[0]
        fig = go.Figure(go.Scatter(
            x=df.index, y=df[close_col],
            mode='lines', line=dict(color='#10B981', width=2),
            fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
        ))

    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=10, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,26,26,0.9)',
        showlegend=False,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', tickfont=dict(
            color='#9CA3AF', size=10), rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', side='right',
                   tickfont=dict(color='#9CA3AF', size=10))
    )
    return fig


# ============================================
# UI HELPERS
# ============================================
def get_logo_path(ticker: str) -> Optional[str]:
    config = get_config()
    logo_dir = config.storage.data_dir / "logos"
    clean_ticker = ticker.upper().replace('_US', '').replace('.US', '')

    for ext in ['png', 'jpg', 'svg']:
        path = logo_dir / f"{clean_ticker}.{ext}"
        if path.exists():
            return str(path)
    return None


def get_logo_html(ticker: str, size: int = 36) -> str:
    logo_path = get_logo_path(ticker)
    initials = ticker[:2].upper()

    if logo_path:
        try:
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/png;base64,{encoded}" style="width:{size}px;height:{size}px;border-radius:10px;object-fit:contain;background:#0A0A0A;">'
        except:
            pass

    return f'''<div style="width:{size}px;height:{size}px;border-radius:10px;
                background:linear-gradient(135deg,rgba(16,185,129,0.2),rgba(16,185,129,0.1));
                display:flex;align-items:center;justify-content:center;
                font-size:{size//3}px;font-weight:600;color:#10B981;">{initials}</div>'''


def get_score_bar_class(score: float) -> str:
    if score is None:
        return ""
    if score >= 70:
        return "score-bar-green"
    elif score >= 40:
        return "score-bar-yellow"
    else:
        return "score-bar-red"


# ============================================
# RENDER FUNCTIONS
# ============================================
def get_semantic_label(score: float) -> tuple:
    """Return (label, css_class) based on score."""
    if score is None:
        return ("N/A", "stable")
    if score >= 75:
        return ("Dynamique", "dynamic")
    elif score >= 60:
        return ("Élevée", "elevated")
    elif score >= 40:
        return ("Stable", "stable")
    else:
        return ("Faible", "weak")


def get_score_badge_class(score: float) -> str:
    """Return CSS class for score badge."""
    if score is None:
        return "medium"
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    return "low"


def render_asset_row(asset: Dict, is_selected: bool = False) -> bool:
    """Render an asset row with Spora/Score/Semantique columns."""
    ticker = asset.get('ticker', asset.get('symbol', ''))
    score = asset.get('score_total')
    spora = int(score) if score else 0
    score_display = int(score) if score else "—"
    semantic_label, semantic_class = get_semantic_label(score)
    score_class = get_score_badge_class(score)
    selected_class = "selected" if is_selected else ""

    st.markdown(f'''
    <div class="asset-row {selected_class}">
        <div class="asset-info">
            <div class="asset-logo">{get_logo_html(ticker, 40)}</div>
            <span class="asset-ticker">{ticker}</span>
        </div>
        <div style="text-align:center;font-weight:600;color:#FFFFFF;">{spora}</div>
        <div style="text-align:center;">
            <span class="score-badge {score_class}">{score_display}</span>
            </div>
        <div style="text-align:center;">
            <span class="semantic-label {semantic_class}">{semantic_label}</span>
        </div>
        <div style="text-align:center;">
            <div style="width:24px;height:24px;border-radius:50%;background:#22C55E;display:inline-flex;align-items:center;justify-content:center;color:white;font-size:14px;">✓</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    return st.button("Voir", key=f"select_{asset.get('asset_id')}", use_container_width=True)


def render_detail_panel(asset_id: str, user_id: str = "default"):
    """Render detailed asset panel with Score, Pillars, Chart, Description and Metrics."""
    asset = load_asset_detail(asset_id)

    if not asset:
        st.warning("Actif non trouvé")
        return

    ticker = asset.get('symbol', '')
    name = asset.get('name', ticker)
    score = asset.get('score_total')
    momentum = asset.get('score_momentum') or 0
    safety = asset.get('score_safety') or 0
    value = asset.get('score_value') or 0
    coverage = asset.get('coverage', 0) or 0
    liquidity = asset.get('liquidity', 0) or 0
    fx_risk = asset.get('fx_risk', 0) or 0
    market_scope = asset.get('market_scope', 'US_EU')
    currency = asset.get('currency', 'USD')

    # Get current price using utility function
    last_price = get_current_price(asset, asset_id, market_scope)
    price_display = format_price(last_price, currency)

    # ═══════════════════════════════════════════════════════════════════════════
    # HEADER: Ticker, Name, Price
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(f'''
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,0.08);">
        <div style="display:flex;align-items:center;gap:16px;">
            {get_logo_html(ticker, 56)}
            <div>
                <div style="font-size:28px;font-weight:700;color:#FFFFFF;">{ticker}</div>
                <div style="font-size:14px;color:#9CA3AF;">{sanitize_text(name[:50] if name else '')}</div>
                <div style="margin-top:6px;">
                    <span style="font-size:11px;padding:4px 10px;background:rgba(16,185,129,0.15);color:#10B981;border-radius:6px;font-weight:500;">{asset.get('asset_type', '')}</span>
                    <span style="font-size:11px;color:#6B7280;margin-left:8px;">{asset.get('market_code', '')}</span>
                </div>
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:32px;font-weight:700;color:#10B981;">{price_display}</div>
            <div style="font-size:12px;color:#6B7280;text-transform:uppercase;margin-top:4px;">Prix actuel</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORE GAUGE + PILLARS
    # ═══════════════════════════════════════════════════════════════════════════
    col_gauge, col_pillars = st.columns([1, 1])

    with col_gauge:
        if score is not None:
            fig = render_score_gauge(score)
            st.plotly_chart(fig, use_container_width=True,
                            config={'displayModeBar': False})
        else:
            st.markdown('''
            <div style="text-align:center;padding:40px;background:rgba(22,34,28,0.8);border-radius:12px;">
                <div style="font-size:48px;color:#64748B;">—</div>
                <div style="font-size:14px;color:#94A3B8;">Score non calculé</div>
            </div>
            ''', unsafe_allow_html=True)

            store = get_sqlite_store()
            is_pro = store.is_pro_user(user_id)
            can_calc = store.can_calculate_score(user_id)

            if is_pro and can_calc:
                if st.button("Calculer le score", key=f"calc_{asset_id}", type="primary", use_container_width=True):
                    result = fetch_and_score_asset(asset_id, user_id)
                    if result['success']:
                        st.success("Score calculé !")
                        st.rerun()
                    else:
                        st.error(result['message'])
            elif not is_pro:
                st.info("Passez à Pro pour calculer les scores")
            else:
                st.warning("Quota journalier atteint")

    with col_pillars:
        render_pillar_bars(value, momentum, safety)

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA QUALITY BADGES
    # ═══════════════════════════════════════════════════════════════════════════
    render_data_badges(coverage, liquidity, fx_risk)

    # ═══════════════════════════════════════════════════════════════════════════
    # ASSET DESCRIPTION (from company_info)
    # ═══════════════════════════════════════════════════════════════════════════
    description = get_company_description(ticker)
    if description:
        st.markdown(f'''
        <div class="asset-description">
            <strong style="color:#FFFFFF;">À propos de {name}</strong><br><br>
            {description}
        </div>
        ''', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHART SECTION WITH PERIOD SELECTOR
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown('''
    <div style="display:flex;align-items:center;justify-content:space-between;margin:24px 0 12px;">
        <span style="font-size:16px;font-weight:600;color:#FFFFFF;display:flex;align-items:center;gap:8px;">
            📈 Évolution du prix
        </span>
    </div>
    ''', unsafe_allow_html=True)

    # Period selector
    current_period = st.session_state.get('chart_range', '30d')
    new_period = render_period_selector(current_period)
    if new_period != current_period:
        st.session_state.chart_range = new_period

    # Calculate days based on period
    period_days = {"30d": 30, "1y": 252, "5y": 1260,
                   "10y": 2520}.get(current_period, 30)

    df = load_price_history(asset_id, market_scope)
    if df is not None and not df.empty:
        fig = render_candlestick_chart(df, days=period_days)
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': False})
    else:
        st.markdown('''
        <div style="background:rgba(22,34,28,0.8);border-radius:12px;padding:40px;text-align:center;">
            <div style="color:#94A3B8;">Graphique non disponible</div>
        </div>
        ''', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # KPI CARDS (Couverture, Liquidité, Risque FX)
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown('<br>', unsafe_allow_html=True)
    render_kpi_cards(coverage, liquidity, fx_risk)

    # ═══════════════════════════════════════════════════════════════════════════
    # EXTERNAL LINKS (Yahoo Finance, Google Finance, Actualités)
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(f'''
    <div class="external-links">
        <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" class="external-link">
            📊 Yahoo Finance
        </a>
        <a href="https://www.google.com/finance/quote/{ticker}" target="_blank" class="external-link">
            🔍 Google Finance
        </a>
        <a href="https://www.google.com/search?q={ticker}+news&tbm=nws" target="_blank" class="external-link">
            📰 Actualités
        </a>
    </div>
    ''', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHLIST ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════
    watchlist = get_watchlist(user_id)
    if asset_id in watchlist:
        if st.button("⭐ Retirer de la liste de suivi", key=f"wl_remove_{asset_id}", use_container_width=True):
            remove_from_watchlist(asset_id, user_id)
            st.rerun()
    else:
        if st.button("☆ Ajouter à la liste de suivi", key=f"wl_add_{asset_id}", use_container_width=True, type="primary"):
            add_to_watchlist(asset_id, ticker, asset.get(
                'market_code', 'US'), user_id)
            st.rerun()


# ============================================
# LANDING PAGE
# ============================================
def page_landing():
    """Public landing page - Premium SaaS style."""
    # Get real metrics from database
    metrics = get_landing_metrics("US_EU")
    # Render the full premium landing page from the landing module
    render_full_landing_page(metrics)


# ============================================
# AUTH PAGES (delegated to auth_pages module)
# ============================================
def page_login():
    """Login page - Premium Fintech Dark Theme."""
    auth = get_auth_manager()
    render_login(auth)


def page_signup():
    """Signup page - Premium Fintech Dark Theme."""
    auth = get_auth_manager()
    store = get_sqlite_store()
    render_signup(auth, store)


def page_profile():
    """Profile page."""
    user_id = st.session_state.get('user_id', 'default')

    if user_id == 'default':
        st.warning("Connectez-vous pour accéder à votre profil")
        if st.button("Se connecter"):
            st.session_state.view = 'login'
            st.rerun()
        return

    store = get_sqlite_store()
    profile = store.get_user_profile(user_id)
    subscription = store.get_subscription(user_id)

    st.markdown('<h1 style="font-size:28px;font-weight:700;color:#FFFFFF;margin-bottom:24px;">Mon Profil</h1>',
                unsafe_allow_html=True)

    if st.button("← Retour au tableau de bord", key="profile_back"):
        st.session_state.view = 'dashboard'
        st.rerun()

    col1, col2 = st.columns([1, 2])

    with col1:
        # Avatar
        avatar_path = profile.get('avatar_path') if profile else None
        if avatar_path and Path(avatar_path).exists():
            try:
                with open(avatar_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                st.markdown(f'''
                <div style="text-align:center;">
                    <img src="data:image/png;base64,{encoded}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #10B981;">
                </div>
                ''', unsafe_allow_html=True)
            except:
                st.markdown('''
                <div style="width:120px;height:120px;margin:0 auto;border-radius:50%;background:linear-gradient(135deg,#10B981,#059669);display:flex;align-items:center;justify-content:center;">
                    <span style="font-size:48px;color:white;">👤</span>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div style="width:120px;height:120px;margin:0 auto;border-radius:50%;background:linear-gradient(135deg,#10B981,#059669);display:flex;align-items:center;justify-content:center;">
                <span style="font-size:48px;color:white;">👤</span>
            </div>
            ''', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Changer l'avatar", type=[
                                         'png', 'jpg', 'jpeg'], key="avatar_upload")
        if uploaded_file:
            avatar_path = save_avatar(user_id, uploaded_file)
            if avatar_path:
                store.update_user_profile(user_id, avatar_path=avatar_path)
                st.success("Avatar mis à jour !")
                st.rerun()

    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        display_name = st.text_input("Nom d'affichage", value=profile.get(
            'display_name', '') if profile else '', key="profile_name")

        if st.button("Enregistrer", key="profile_save", type="primary"):
            store.update_user_profile(user_id, display_name=display_name)
            st.success("Profil mis à jour !")

        st.markdown(
            "<hr style='border-color:rgba(255,255,255,0.1);margin:20px 0;'>", unsafe_allow_html=True)

        # Subscription info
        plan = subscription.get('plan', 'free')
        status = subscription.get('status', 'active')
        quota_used = subscription.get('daily_quota_used', 0)
        quota_limit = subscription.get('daily_quota_limit', 3)

        plan_display = {
            'free': 'Gratuit',
            'monthly_9_99': 'Pro Mensuel',
            'yearly_50': 'Pro Annuel'
        }.get(plan, plan)

        st.markdown(f'''
        <div style="margin-bottom:16px;">
            <span style="font-size:12px;color:#9CA3AF;text-transform:uppercase;">Abonnement</span>
            <div style="font-size:20px;font-weight:600;color:#FFFFFF;">{plan_display}</div>
            <div style="font-size:14px;color:#10B981;">Statut : {status}</div>
        </div>
        <div style="margin-bottom:16px;">
            <span style="font-size:12px;color:#9CA3AF;text-transform:uppercase;">Quota journalier</span>
            <div style="font-size:16px;color:#FFFFFF;">{quota_used} / {quota_limit} calculs utilisés</div>
        </div>
        ''', unsafe_allow_html=True)

        if plan == 'free':
            if st.button("Passer à Pro", key="upgrade_pro", type="primary", use_container_width=True):
                st.session_state.view = 'pricing'
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Se déconnecter", key="logout_btn"):
        logout()
        st.session_state.view = 'landing'
        st.rerun()


def page_pricing():
    """Pricing page for logged-in users."""
    user_id = st.session_state.get('user_id', 'default')
    store = get_sqlite_store()

    st.markdown('<h1 style="text-align:center;font-size:32px;font-weight:700;color:#FFFFFF;margin-bottom:40px;">Choisissez votre plan</h1>', unsafe_allow_html=True)

    if st.button("← Retour", key="pricing_back"):
        st.session_state.view = 'dashboard'
        st.rerun()

    col1, col2, col3 = st.columns([1, 1.2, 1.2])

    with col2:
        st.markdown('''
        <div class="pricing-card">
            <h3 style="font-size:20px;font-weight:600;color:#FFFFFF;margin-bottom:16px;">Mensuel</h3>
            <div style="font-size:42px;font-weight:700;color:#FFFFFF;">9,99 €<span style="font-size:16px;color:#9CA3AF;">/mois</span></div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Souscrire au plan mensuel", key="activate_monthly", use_container_width=True):
            store.set_subscription(user_id, 'monthly_9_99', 'active')
            st.session_state.is_pro = True
            st.success("Abonnement activé !")
            st.rerun()

    with col3:
        st.markdown('''
        <div class="pricing-card featured">
            <div class="pricing-badge">Meilleure offre</div>
            <h3 style="font-size:20px;font-weight:600;color:#FFFFFF;margin-bottom:16px;margin-top:8px;">Annuel</h3>
            <div style="font-size:42px;font-weight:700;color:#FFFFFF;">50 €<span style="font-size:16px;color:#9CA3AF;">/an</span></div>
        </div>
        ''', unsafe_allow_html=True)
        if st.button("Souscrire au plan annuel", key="activate_yearly", type="primary", use_container_width=True):
            store.set_subscription(user_id, 'yearly_50', 'active')
            st.session_state.is_pro = True
            st.success("Abonnement activé !")
            st.rerun()


# ============================================
# DASHBOARD & EXPLORER PAGES
# ============================================
def render_markets_header():
    """Render the markets covered header with premium badges."""
    current_market = st.session_state.get('market_filter', 'ALL')
    current_type = st.session_state.get('type_filter', 'All')

    st.markdown('''
    <div style="background:linear-gradient(180deg, rgba(8,12,18,0.98) 0%, rgba(12,18,28,0.95) 100%);
                border-radius:20px;padding:24px 32px 16px;margin-bottom:16px;position:relative;overflow:hidden;
                border:1px solid rgba(16,185,129,0.12);">
        <h2 style="font-size:18px;font-weight:600;color:#FFFFFF;text-align:center;margin:0 0 16px 0;">
            Marchés couverts
        </h2>
    </div>
    ''', unsafe_allow_html=True)

    all_filters = [
        ("usa", "🇺🇸 USA", "market", "US"),
        ("europe", "🇪🇺 Europe", "market", "EU"),
        ("afrique", "🌍 Afrique", "market", "AFRICA"),
        ("etf", "📊 ETF", "type", "ETF"),
        ("actions", "📈 Actions", "type", "EQUITY"),
        ("fx", "💱 FX", "type", "FX"),
        ("obligations", "📄 Obligations", "type", "BOND"),
    ]

    col1, col2, col3, col4, col5, col6, col7 = st.columns(
        [1.2, 1.2, 1.2, 1, 1.2, 0.8, 1.5])
    columns = [col1, col2, col3, col4, col5, col6, col7]

    for idx, (key, label, filter_type, value) in enumerate(all_filters):
        with columns[idx]:
            if filter_type == "market":
                is_active = current_market == value
            else:
                is_active = current_type == value

            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"filter_{key}", use_container_width=True, type=btn_type):
                if filter_type == "market":
                    if current_market == value:
                        st.session_state.market_filter = 'ALL'
                    else:
                        st.session_state.market_filter = value
                        if value == 'AFRICA':
                            st.session_state.market_scope = 'AFRICA'
                        else:
                            st.session_state.market_scope = 'US_EU'
                else:
                    if current_type == value:
                        st.session_state.type_filter = 'All'
                    else:
                        st.session_state.type_filter = value
                load_top_assets.clear()
                st.rerun()


# ============================================
# NEW SUPABASE AUTH PAGES
# ============================================

def page_forgot_password():
    """Forgot password page - Supabase Auth."""
    if not SUPABASE_AUTH_ENABLED:
        st.warning(
            "Supabase Auth non configuré. Définissez SUPABASE_URL dans .env")
        if st.button("← Retour"):
            st.session_state.view = "login"
            st.rerun()
        return

    # Inline implementation for forgot password
    auth = SupabaseAuth()

    st.markdown("""
    <div style="max-width: 400px; margin: 60px auto; text-align: center;">
        <h1 style="color: #FFFFFF; font-size: 28px; margin-bottom: 16px;">Mot de passe oublié</h1>
        <p style="color: #9CA3AF; margin-bottom: 32px;">Entrez votre email pour recevoir un lien de réinitialisation</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Adresse email", key="forgot_email")

        if st.button("Envoyer le lien", type="primary", use_container_width=True):
            if email and "@" in email:
                success, msg = auth.reset_password_request(email)
                st.success(msg)
            else:
                st.error("Veuillez entrer un email valide.")

        if st.button("← Retour", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()


def page_reset_password():
    """Reset password page - Supabase Auth."""
    if not SUPABASE_AUTH_ENABLED:
        st.warning("Supabase Auth non configuré.")
        return

    auth = SupabaseAuth()

    # Check for tokens in URL
    query_params = st.query_params
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")

    if access_token and refresh_token:
        session_data = auth.get_session_from_url(access_token, refresh_token)
        if session_data:
            SessionManager.set_session(session_data)
            st.session_state.can_reset = True
            st.query_params.clear()

    st.markdown("""
    <div style="max-width: 400px; margin: 60px auto; text-align: center;">
        <h1 style="color: #FFFFFF; font-size: 28px; margin-bottom: 16px;">Nouveau mot de passe</h1>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        new_pw = st.text_input("Nouveau mot de passe",
                               type="password", key="new_pw")
        confirm_pw = st.text_input(
            "Confirmer", type="password", key="confirm_pw")

        if st.button("Mettre à jour", type="primary", use_container_width=True):
            if len(new_pw) < 8:
                st.error("Minimum 8 caractères.")
            elif new_pw != confirm_pw:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                success, msg = auth.update_password(new_pw)
                if success:
                    st.success(msg)
                    SessionManager.clear_session()
                else:
                    st.error(msg)

        if st.button("← Connexion", use_container_width=True):
            st.session_state.view = "login"
            st.rerun()


def page_auth_callback():
    """Auth callback page - handles email confirmation."""
    query_params = st.query_params
    access_token = query_params.get("access_token")
    refresh_token = query_params.get("refresh_token")
    error = query_params.get("error")

    if error:
        st.error(f"Erreur: {query_params.get('error_description', error)}")
        if st.button("← Connexion"):
            st.session_state.view = "login"
            st.rerun()
        return

    if access_token and refresh_token and SUPABASE_AUTH_ENABLED:
        auth = SupabaseAuth()
        session_data = auth.get_session_from_url(access_token, refresh_token)

        if session_data:
            SessionManager.set_session(session_data)
            st.query_params.clear()
            st.success("✓ Email confirmé ! Redirection...")
            st.session_state.view = "dashboard"
            st.rerun()

    st.info("Vérification en cours...")


def page_account():
    """Account page - profile and subscription management."""
    if not SUPABASE_AUTH_ENABLED or not SessionManager.is_authenticated():
        page_profile()
        return

    st.markdown("<h1 style='color:#FFFFFF;'>Mon Compte</h1>",
                unsafe_allow_html=True)

    email = SessionManager.get_email()
    user_id = SessionManager.get_user_id()

    st.markdown(f"**Email:** {email}")
    st.markdown(f"**ID:** {user_id[:8]}...")

    # Get entitlements
    entitlements = EntitlementChecker.get_cached_entitlements()
    if entitlements:
        st.markdown(f"**Plan:** {entitlements.plan}")
        st.markdown(f"**Statut:** {entitlements.status}")
        st.markdown(
            f"**Requêtes:** {entitlements.daily_requests_used}/{entitlements.daily_requests_limit}")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Gérer l'abonnement", use_container_width=True):
            st.session_state.view = "billing"
            st.rerun()

    with col2:
        if st.button("Se déconnecter", use_container_width=True):
            auth = SupabaseAuth()
            auth.sign_out()
            SessionManager.clear_session()
            EntitlementChecker.clear_cache()
            st.session_state.view = "landing"
            st.rerun()

    if st.button("← Dashboard"):
        st.session_state.view = "dashboard"
        st.rerun()


def page_billing():
    """Billing page - Stripe subscription management."""
    if not SUPABASE_AUTH_ENABLED:
        page_pricing()
        return

    if not SessionManager.is_authenticated():
        st.warning("Veuillez vous connecter.")
        if st.button("Se connecter"):
            st.session_state.view = "login"
            st.rerun()
        return

    # Check success/cancel
    if st.query_params.get("success") == "1":
        st.success("🎉 Paiement réussi ! Votre abonnement est actif.")
        EntitlementChecker.clear_cache()
    elif st.query_params.get("canceled") == "1":
        st.warning("Paiement annulé.")

    st.markdown("<h1 style='color:#FFFFFF; text-align:center;'>Choisissez votre plan</h1>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:rgba(18,18,18,0.9);border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;text-align:center;">
            <h3 style="color:#FFFFFF;">Mensuel</h3>
            <div style="color:#10B981;font-size:36px;font-weight:700;">9,99€</div>
            <div style="color:#9CA3AF;">par mois</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("S'abonner Mensuel", use_container_width=True, key="sub_m"):
            start_stripe_checkout("monthly")

    with col2:
        st.markdown("""
        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:16px;padding:24px;text-align:center;">
            <div style="color:#10B981;font-size:12px;font-weight:600;">MEILLEURE OFFRE</div>
            <h3 style="color:#FFFFFF;">Annuel</h3>
            <div style="color:#10B981;font-size:36px;font-weight:700;">99,99€</div>
            <div style="color:#9CA3AF;">par an (économisez 58%)</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("S'abonner Annuel", type="primary", use_container_width=True, key="sub_y"):
            start_stripe_checkout("yearly")

    if st.button("← Retour"):
        st.session_state.view = "dashboard"
        st.rerun()


def start_stripe_checkout(plan: str):
    """Initiate Stripe checkout session."""
    import httpx

    backend_url = os.environ.get(
        "BACKEND_API_BASE_URL", "http://localhost:8000")
    access_token = SessionManager.get_access_token()
    app_url = os.environ.get("APP_BASE_URL", "http://localhost:8501")

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{backend_url}/billing/checkout-session",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "plan": plan,
                    "success_url": f"{app_url}/?view=billing&success=1",
                    "cancel_url": f"{app_url}/?view=billing&canceled=1",
                },
                timeout=15.0,
            )

            if response.status_code == 200:
                checkout_url = response.json().get("checkout_url")
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={checkout_url}">', unsafe_allow_html=True)
                st.info(
                    f"Redirection... [Cliquez ici]({checkout_url}) si nécessaire.")
            else:
                st.error(f"Erreur: {response.text}")
    except Exception as e:
        st.error(f"Erreur de connexion: {e}")


def page_dashboard():
    """Main dashboard page - Premium Glassmorphism Trading Interface (Matching mockup layout)."""
    user_id = st.session_state.get('user_id', 'default')

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPACT TOP BAR: Search + Filters in one row
    # ═══════════════════════════════════════════════════════════════════════════
    col_search, col_market, col_type, col_explore = st.columns([3, 1, 1, 1])

    with col_search:
        search_query = st.text_input(
            "Rechercher",
            placeholder="🔍 Rechercher un actif...",
            key="dashboard_search_compact",
            label_visibility="collapsed"
        )

    current_market = st.session_state.get('market_filter', 'ALL')
    current_type = st.session_state.get('type_filter', 'All')

    with col_market:
        market_options = ["Tous", "🇺🇸 USA", "🇪🇺 Europe", "🌍 Afrique"]
        market_values = ["ALL", "US", "EU", "AFRICA"]
        market_idx = market_values.index(
            current_market) if current_market in market_values else 0
        new_market_display = st.selectbox(
            "Région", market_options, index=market_idx, key="mkt_sel", label_visibility="collapsed")
        new_market = market_values[market_options.index(new_market_display)]
        if new_market != current_market:
            st.session_state.market_filter = new_market
            st.session_state.market_scope = 'AFRICA' if new_market == 'AFRICA' else 'US_EU'
            st.rerun()

    with col_type:
        type_options = ["Tous", "ETF", "Actions", "FX", "Obligations"]
        type_values = ["All", "ETF", "EQUITY", "FX", "BOND"]
        type_idx = type_values.index(
            current_type) if current_type in type_values else 0
        new_type_display = st.selectbox(
            "Type", type_options, index=type_idx, key="typ_sel", label_visibility="collapsed")
        new_type = type_values[type_options.index(new_type_display)]
        if new_type != current_type:
            st.session_state.type_filter = new_type
            st.rerun()

    with col_explore:
        if st.button("Explorer →", key="explore_btn", use_container_width=True):
            st.session_state.view = 'explorer'
            st.rerun()

    # Handle search
    if search_query:
        store = get_sqlite_store()
        market_scope = st.session_state.get('market_scope', 'US_EU')
        search_results = store.search_assets(
            search_query, market_scope, limit=20)
        if search_results:
            st.session_state.search_results = search_results

    # ═══════════════════════════════════════════════════════════════════════════
    # DETERMINE SCOPE AND LOAD ASSETS
    # ═══════════════════════════════════════════════════════════════════════════
    market_scope = st.session_state.get('market_scope', 'US_EU')
    type_filter = st.session_state.get('type_filter', 'All')
    market_filter = st.session_state.get('market_filter', 'ALL')

    if market_filter == 'AFRICA':
        market_scope = 'AFRICA'
    elif market_filter in ('US', 'EU'):
        market_scope = 'US_EU'

    # Use search results or load top assets
    if search_query and st.session_state.get('search_results'):
        assets = st.session_state.search_results
    else:
        assets = load_top_assets(type_filter, 50, market_scope, market_filter)

    if not assets:
        st.info(
            "Aucun actif trouvé avec un score. Utilisez l'Explorer pour voir tous les actifs.")
        return

    # Get selected asset details for the right panel
    selected_id = st.session_state.get('selected_asset_id')
    if not selected_id and assets:
        selected_id = assets[0].get('asset_id')
        st.session_state.selected_asset_id = selected_id

    selected_asset = load_asset_detail(selected_id) if selected_id else None

    # ═══════════════════════════════════════════════════════════════════════════
    # HORIZONTAL ASSET LIST + DETAILS BELOW
    # ═══════════════════════════════════════════════════════════════════════════

    st.markdown("### 🏆 Top scorés")

    # Display assets as horizontal buttons
    asset_cols = st.columns(min(len(assets[:8]), 8))
    for idx, asset in enumerate(assets[:8]):
        with asset_cols[idx]:
            asset_id = asset.get('asset_id')
            ticker = asset.get('symbol', asset.get('ticker', 'N/A'))
            score = asset.get('score_total', 0) or 0
            is_selected = st.session_state.get('selected_asset_id') == asset_id

            btn_type = "primary" if is_selected else "secondary"
            if st.button(f"{ticker}\n{int(score)}", key=f"sel_{asset_id}", use_container_width=True, type=btn_type):
                st.session_state.selected_asset_id = asset_id
                st.rerun()

    voir_col1, voir_col2 = st.columns([3, 1])
    with voir_col2:
        if st.button("Voir plus →", key="voir_plus_table", use_container_width=True):
            st.session_state.view = 'explorer'
            st.rerun()

    st.markdown("---")

    # Selected asset details section
    if selected_asset:
        score = selected_asset.get('score_total', 0) or 0
        value = selected_asset.get('score_value', 0) or 0
        momentum = selected_asset.get('score_momentum', 0) or 0
        safety = selected_asset.get('score_safety', 0) or 0
        ticker = selected_asset.get(
            'symbol', selected_asset.get('ticker', 'Actif'))
        coverage = selected_asset.get(
            'coverage', 0) or selected_asset.get('data_coverage', 0) or 0
        liquidity = selected_asset.get('liquidity', 0) or 0

        # Header with asset name and score
        head_col1, head_col2 = st.columns([2, 1])
        with head_col1:
            st.markdown(f"## {ticker}")
        with head_col2:
            st.markdown(
                f'<div style="text-align:right;"><span style="background:#22C55E;color:white;padding:10px 24px;border-radius:24px;font-weight:700;font-size:28px;">{int(score)}/100</span></div>', unsafe_allow_html=True)

        # Metrics in a single row
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.metric("📈 Valeur", f"{int(value)}")
        with m2:
            st.metric("🚀 Momentum", f"{int(momentum)}")
        with m3:
            st.metric("🛡️ Sécurité", f"{int(safety)}")
        with m4:
            st.metric("📊 Couverture", f"{int(coverage)}%")
        with m5:
            liq_label = 'Élevée' if isinstance(
                liquidity, (int, float)) and liquidity > 0.7 else 'Moy.'
            st.metric("💧 Liquidité", liq_label)
        with m6:
            st.metric("💱 Risque FX", "Faible")
    else:
        st.info("Sélectionnez un actif pour voir les détails")

    # Chart section removed - simplified layout shows KPIs inline above

    # ═══════════════════════════════════════════════════════════════════════════
    # ROW 3: ASSET DETAIL SECTION (Description + Features + News + Watchlist)
    # ═══════════════════════════════════════════════════════════════════════════
    if selected_asset:
        def handle_watchlist_add(asset_id):
            """Handle adding asset to watchlist."""
            try:
                ticker = selected_asset.get(
                    'symbol', selected_asset.get('ticker', ''))
                market_code = selected_asset.get('market_code', 'US')
                add_to_watchlist(asset_id, ticker, market_code, user_id)
                st.success(f"{ticker} ajouté à votre liste de suivi!")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")

        render_asset_detail_section(
            asset=selected_asset,
            user_id=user_id,
            on_watchlist_change=handle_watchlist_add
        )


def page_explorer():
    """Enhanced Explorer page with full universe browsing."""
    user_id = st.session_state.get('user_id', 'default')
    store = get_sqlite_store()

    st.markdown('<h1 style="font-size:26px;font-weight:700;color:#FFFFFF;margin-bottom:20px;">Explorer</h1>',
                unsafe_allow_html=True)

    if st.button("← Retour au tableau de bord", key="back_dashboard"):
        st.session_state.view = 'dashboard'
        st.rerun()

    # Filters row
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

    with col1:
        scope_options = ["US_EU", "AFRICA"]
        scope_idx = 0 if st.session_state.get(
            'explorer_scope', 'US_EU') == "US_EU" else 1
        scope = st.selectbox("Région", scope_options,
                             index=scope_idx, key="explorer_scope_select")
        st.session_state.explorer_scope = scope

    with col2:
        # Get available asset types for this scope
        asset_types = ["Tous"] + store.get_asset_types_for_scope(scope)
        type_filter = st.selectbox("Type", asset_types, key="explorer_type")

    with col3:
        top_options = {"Top 10": 10, "Top 30": 30,
                       "Top 50": 50, "Top 100": 100, "Tout": 0}
        top_selection = st.selectbox("Affichage", list(
            top_options.keys()), index=2, key="explorer_top")
        limit = top_options[top_selection]

    with col4:
        only_scored = st.checkbox(
            "Seulement scorés", value=True, key="explorer_scored")

    with col5:
        search_query = st.text_input(
            "Rechercher", placeholder="Ticker ou nom...", key="explorer_search")

    # Pagination state
    page_size = 50 if limit == 0 else limit
    page = st.session_state.get('explorer_page', 1)

    # Fetch data
    type_filter_sql = None if type_filter == "Tous" else type_filter

    if limit > 0:
        # Top N mode - use simple query
        assets = store.get_top_scored_assets(scope, type_filter_sql, limit)
        if search_query:
            assets = [a for a in assets if search_query.upper() in a.get(
                'symbol', '').upper() or search_query.lower() in (a.get('name') or '').lower()]
        total = len(assets)
        total_pages = 1
    else:
        # Full universe mode - use paginated query
        assets, total = store.search_universe(
            market_scope=scope,
            asset_type=type_filter_sql,
            query=search_query if search_query else None,
            only_scored=only_scored,
            limit=page_size,
            offset=(page - 1) * page_size
        )
        total_pages = max(1, (total + page_size - 1) // page_size)

    # Stats
    st.markdown(f'''
    <div style="display:flex;gap:16px;margin:16px 0;">
        <span style="font-size:13px;color:#9CA3AF;">{total} actifs trouvés</span>
        <span style="font-size:13px;color:#6B7280;">|</span>
        <span style="font-size:13px;color:#9CA3AF;">Région: {scope}</span>
    </div>
    ''', unsafe_allow_html=True)

    # Pagination controls (only for "Tout" mode)
    if limit == 0 and total_pages > 1:
        nav_cols = st.columns([1, 1, 2, 1, 1])
        with nav_cols[0]:
            if st.button("Début", disabled=(page == 1), key="nav_start"):
                st.session_state.explorer_page = 1
                st.rerun()
        with nav_cols[1]:
            if st.button("Précédent", disabled=(page == 1), key="nav_prev"):
                st.session_state.explorer_page = max(1, page - 1)
                st.rerun()
        with nav_cols[2]:
            st.markdown(
                f'<div style="text-align:center;padding:8px;color:#9CA3AF;">Page {page} / {total_pages}</div>', unsafe_allow_html=True)
        with nav_cols[3]:
            if st.button("Suivant", disabled=(page >= total_pages), key="nav_next"):
                st.session_state.explorer_page = min(total_pages, page + 1)
                st.rerun()
        with nav_cols[4]:
            if st.button("Fin", disabled=(page >= total_pages), key="nav_end"):
                st.session_state.explorer_page = total_pages
                st.rerun()

    # Content
    col_left, col_right = st.columns([1, 1.2])

    with col_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        for asset in assets[:page_size]:
            asset_id = asset.get('asset_id')
            is_selected = st.session_state.get('selected_asset_id') == asset_id
            if render_asset_row(asset, is_selected):
                st.session_state.selected_asset_id = asset_id
                st.rerun()

        if not assets:
            st.markdown(
                '<div style="text-align:center;padding:40px;color:#9CA3AF;">Aucun actif trouvé</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        selected_id = st.session_state.get('selected_asset_id')
        if selected_id:
            render_detail_panel(selected_id, user_id)
        else:
            st.markdown('''
            <div style="text-align:center;padding:60px;">
                <div style="font-size:16px;color:#9CA3AF;">Sélectionnez un actif</div>
                <div style="font-size:13px;color:#6B7280;">pour afficher les détails</div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def page_watchlist():
    """Watchlist page."""
    user_id = st.session_state.get('user_id', 'default')

    st.markdown('<h1 style="font-size:26px;font-weight:700;color:#FFFFFF;margin-bottom:20px;">Liste de suivi</h1>', unsafe_allow_html=True)

    if st.button("← Retour", key="back_wl"):
        st.session_state.view = 'dashboard'
        st.rerun()

    watchlist = get_watchlist(user_id)

    if not watchlist:
        st.info("Votre liste de suivi est vide. Ajoutez des actifs depuis l'Explorer.")
        return

    col_left, col_right = st.columns([1, 1.2])

    with col_left:
        st.markdown(
            f'<div style="font-size:13px;color:#9CA3AF;margin-bottom:16px;">{len(watchlist)} actifs suivis</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        for asset_id in watchlist:
            asset = load_asset_detail(asset_id)
            if asset:
                if render_asset_row(asset, st.session_state.get('selected_asset_id') == asset_id):
                    st.session_state.selected_asset_id = asset_id
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if st.session_state.get('selected_asset_id'):
            render_detail_panel(st.session_state.get(
                'selected_asset_id'), user_id)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# SIDEBAR NAVIGATION
# ============================================
def render_sidebar():
    """Render sidebar - delegates to new sidebar module."""
    scope_counts = get_scope_counts()
    user_info = st.session_state.get('user_info', {})

    # Check authentication
    if SUPABASE_AUTH_ENABLED:
        is_auth = SessionManager.is_authenticated()
    else:
        is_auth = st.session_state.get('user_id') is not None

    render_sidebar_v2(
        scope_counts=scope_counts,
        user_info=user_info,
        is_authenticated=is_auth
    )


# ============================================
# MAIN APPLICATION
# ============================================
def main():
    # Initialize session state with new glassmorphism UI variables
    defaults = {
        'view': 'landing',
        'selected_asset_id': None,
        'market_scope': 'US_EU',
        'market_filter': 'ALL',
        'type_filter': 'All',
        'explorer_page': 1,
        'user_id': None,
        'is_authenticated': False,
        # New UI state variables
        'sidebar_visible': True,
        'chart_range': '30d',
        'user_initial': 'U',
        'search_results': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Initialize Supabase session if enabled
    if SUPABASE_AUTH_ENABLED:
        SessionManager.init_session()

    # Check URL params for view changes
    query_params = st.query_params

    # Demo mode for testing (bypass authentication)
    if query_params.get("demo") == "true":
        st.session_state.user_id = "demo_user_001"
        st.session_state.is_authenticated = True
        st.session_state.view = "dashboard"
        st.session_state.user_initial = "D"

    if "view" in query_params:
        requested_view = query_params.get("view")
        valid_views = ["landing", "login", "signup", "forgot-password", "reset-password",
                       "dashboard", "explorer", "account", "billing"]
        if requested_view in valid_views:
            st.session_state.view = requested_view
            st.query_params.clear()

    # Inject CSS
    inject_premium_css()

    # Get current view
    view = st.session_state.get('view', 'landing')

    # Check authentication (demo mode bypasses this)
    if st.session_state.get('user_id') == 'demo_user_001':
        is_auth = True
    elif SUPABASE_AUTH_ENABLED:
        is_auth = SessionManager.is_authenticated()
    else:
        is_auth = st.session_state.get('user_id') is not None

    # Show sidebar only for authenticated views
    auth_views = ['dashboard', 'explorer', 'watchlist',
                  'profile', 'pricing', 'account', 'billing']
    if view in auth_views and is_auth:
        render_sidebar()

    # Route to page
    if view == 'landing':
        page_landing()
    elif view == 'login':
        page_login()
    elif view == 'signup':
        page_signup()
    elif view == 'forgot-password':
        page_forgot_password()
    elif view == 'reset-password':
        page_reset_password()
    elif view == 'auth/callback':
        page_auth_callback()
    elif view == 'account':
        page_account()
    elif view == 'billing':
        page_billing()
    elif view == 'profile':
        page_profile()
    elif view == 'pricing':
        page_pricing()
    elif view == 'dashboard':
        page_dashboard()
    elif view == 'explorer':
        page_explorer()
    elif view == 'watchlist':
        page_watchlist()
    else:
        page_landing()

    # Footer for all pages (except landing which has its own)
    if view != 'landing':
        st.markdown('''
        <div style="position:fixed;bottom:0;left:0;right:0;padding:12px;background:#0A0A0A;border-top:1px solid rgba(255,255,255,0.08);text-align:center;font-size:11px;color:#6B7280;z-index:1000;">
            Outil d'analyse statistique et éducatif. Capital à risque. Les performances passées ne garantissent pas le futur.
        </div>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
