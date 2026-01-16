"""
MarketGPS Dashboard v2.0 - Professional Trading Dashboard
Matches the design mockup with full sidebar, search, and detailed panels.
"""
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.compliance import sanitize_text
from storage.sqlite_store import SQLiteStore


# ============================================
# CSS - Professional Dark Trading Theme
# ============================================
def inject_dashboard_css():
    st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --bg-primary: #0D0F12;
        --bg-secondary: #13161B;
        --bg-card: #1A1D24;
        --bg-elevated: #22262F;
        --accent-green: #22C55E;
        --accent-green-dim: rgba(34, 197, 94, 0.15);
        --accent-yellow: #EAB308;
        --accent-red: #EF4444;
        --text-primary: #FFFFFF;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --border-color: rgba(255, 255, 255, 0.08);
        --border-active: rgba(34, 197, 94, 0.4);
    }
    
    /* Reset and Base */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu, footer, header {display: none !important;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    
    /* Main container */
    .main .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color) !important;
        width: 260px !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
    }
    
    /* Sidebar Logo */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 20px 24px;
        border-bottom: 1px solid var(--border-color);
    }
    .sidebar-logo-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    .sidebar-logo-text {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    /* Sidebar Navigation */
    .sidebar-nav {
        padding: 16px 12px;
    }
    .sidebar-nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-radius: 10px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
        margin-bottom: 4px;
        font-size: 14px;
        font-weight: 500;
    }
    .sidebar-nav-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-primary);
    }
    .sidebar-nav-item.active {
        background: var(--accent-green-dim);
        color: var(--accent-green);
    }
    .sidebar-nav-item .icon {
        font-size: 18px;
        width: 24px;
        text-align: center;
    }
    
    .sidebar-section-title {
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 16px 16px 8px;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        text-align: left !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        justify-content: flex-start !important;
        transition: all 0.2s !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-primary) !important;
    }
    
    /* ========== TOP BAR ========== */
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border-color);
    }
    .top-bar-left {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .top-bar-title {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
    }
    .top-bar-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    /* Search box */
    .search-box {
        display: flex;
        align-items: center;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 10px 16px;
        min-width: 320px;
        transition: all 0.2s;
    }
    .search-box:focus-within {
        border-color: var(--accent-green);
        box-shadow: 0 0 0 3px var(--accent-green-dim);
    }
    .search-box input {
        background: transparent;
        border: none;
        color: var(--text-primary);
        font-size: 14px;
        outline: none;
        width: 100%;
        margin-left: 10px;
    }
    .search-box input::placeholder {
        color: var(--text-muted);
    }
    
    /* Top bar icons */
    .top-bar-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
        color: var(--text-secondary);
        font-size: 18px;
    }
    .top-bar-icon:hover {
        background: var(--bg-elevated);
        color: var(--text-primary);
    }
    .top-bar-icon.notification {
        position: relative;
    }
    .notification-badge {
        position: absolute;
        top: -2px;
        right: -2px;
        width: 18px;
        height: 18px;
        background: var(--accent-red);
        border-radius: 50%;
        font-size: 10px;
        font-weight: 600;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Profile avatar */
    .profile-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid var(--accent-green);
    }
    .profile-avatar img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    
    /* ========== MAIN CONTENT ========== */
    .main-content {
        display: flex;
        padding: 24px;
        gap: 24px;
        min-height: calc(100vh - 80px);
    }
    
    /* ========== ASSET TABLE ========== */
    .assets-panel {
        flex: 1;
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        overflow: hidden;
    }
    .assets-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
        border-bottom: 1px solid var(--border-color);
    }
    .assets-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* Table header */
    .table-header {
        display: grid;
        grid-template-columns: 2fr 0.8fr 0.8fr 1.2fr 0.5fr;
        padding: 12px 24px;
        background: var(--bg-secondary);
        font-size: 12px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Asset row */
    .asset-row {
        display: grid;
        grid-template-columns: 2fr 0.8fr 0.8fr 1.2fr 0.5fr;
        align-items: center;
        padding: 16px 24px;
        border-bottom: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.2s;
    }
    .asset-row:hover {
        background: rgba(255, 255, 255, 0.02);
    }
    .asset-row.selected {
        background: var(--accent-green-dim);
        border-left: 3px solid var(--accent-green);
    }
    
    .asset-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .asset-logo {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        overflow: hidden;
        background: var(--bg-elevated);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .asset-logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    .asset-logo-placeholder {
        font-size: 14px;
        font-weight: 700;
        color: var(--accent-green);
    }
    .asset-ticker {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* Score cell */
    .score-cell {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .score-badge {
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
    }
    .score-badge.high {
        background: rgba(34, 197, 94, 0.15);
        color: var(--accent-green);
    }
    .score-badge.medium {
        background: rgba(234, 179, 8, 0.15);
        color: var(--accent-yellow);
    }
    .score-badge.low {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
    }
    
    /* Semantic label */
    .semantic-label {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        text-align: center;
    }
    .semantic-label.dynamic { background: rgba(34, 197, 94, 0.15); color: #22C55E; }
    .semantic-label.elevated { background: rgba(59, 130, 246, 0.15); color: #3B82F6; }
    .semantic-label.stable { background: rgba(168, 162, 158, 0.15); color: #A8A29E; }
    .semantic-label.weak { background: rgba(239, 68, 68, 0.15); color: #EF4444; }
    
    /* Check icon */
    .check-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: var(--accent-green);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 14px;
    }
    
    /* ========== DETAIL PANEL ========== */
    .detail-panel {
        width: 420px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    
    /* Score card */
    .score-card {
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        padding: 24px;
    }
    .score-gauge-container {
        display: flex;
        gap: 24px;
    }
    .score-gauge {
        flex: 1;
    }
    .score-pillars {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 16px;
    }
    .pillar-row {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .pillar-label {
        width: 90px;
        font-size: 14px;
        color: var(--text-secondary);
    }
    .pillar-bar {
        flex: 1;
        height: 10px;
        background: var(--bg-elevated);
        border-radius: 5px;
        overflow: hidden;
    }
    .pillar-fill {
        height: 100%;
        background: var(--accent-green);
        border-radius: 5px;
        transition: width 0.5s ease;
    }
    .pillar-value {
        width: 35px;
        text-align: right;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* Data badges */
    .data-badges {
        display: flex;
        gap: 10px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    .data-badge {
        padding: 6px 12px;
        background: var(--bg-elevated);
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
        border: 1px solid var(--border-color);
    }
    .data-badge.success {
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    
    /* Chart card */
    .chart-card {
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        padding: 20px;
    }
    .chart-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
    }
    .chart-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .period-selector {
        display: flex;
        gap: 8px;
    }
    .period-btn {
        padding: 6px 12px;
        background: var(--bg-elevated);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-size: 12px;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s;
    }
    .period-btn:hover, .period-btn.active {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    
    /* Metrics cards */
    .metrics-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
    }
    .metric-card {
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 16px 20px;
    }
    .metric-label {
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 18px;
        font-weight: 700;
        color: var(--text-primary);
    }
    .metric-value.green { color: var(--accent-green); }
    .metric-bar {
        height: 4px;
        background: var(--bg-elevated);
        border-radius: 2px;
        margin-top: 8px;
        overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%;
        background: var(--accent-green);
        border-radius: 2px;
    }
    
    /* ========== VOIR PLUS BUTTON ========== */
    .voir-plus-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 14px 24px;
        background: var(--bg-elevated);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        margin: 16px 24px 24px;
    }
    .voir-plus-btn:hover {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    
    /* Streamlit overrides */
    div[data-testid="stTextInput"] input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 3px var(--accent-green-dim) !important;
    }
    
    /* Hide default streamlit buttons styling in main area */
    .main .stButton > button {
        background: var(--bg-elevated) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-secondary) !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    .main .stButton > button:hover {
        background: var(--accent-green-dim) !important;
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
    }
    .main .stButton > button[kind="primary"] {
        background: var(--accent-green) !important;
        border-color: var(--accent-green) !important;
        color: white !important;
    }
    </style>
    ''', unsafe_allow_html=True)


# ============================================
# DATA FUNCTIONS
# ============================================
@st.cache_resource
def get_store():
    config = get_config()
    store = SQLiteStore(str(config.storage.sqlite_path))
    store.ensure_schema()
    return store


@st.cache_data(ttl=60)
def load_top_assets(market_scope: str = "US_EU", asset_type: str = None, limit: int = 50) -> List[Dict]:
    store = get_store()
    return store.get_top_scored_assets(market_scope, asset_type, limit)


@st.cache_data(ttl=60)
def load_asset_detail(asset_id: str) -> Optional[Dict]:
    store = get_store()
    return store.get_asset_detail(asset_id)


@st.cache_data(ttl=60)
def search_assets(query: str, market_scope: str = "US_EU") -> List[Dict]:
    store = get_store()
    return store.search_assets(query, market_scope, limit=20)


def load_price_history(asset_id: str, market_scope: str = "US_EU") -> Optional[pd.DataFrame]:
    config = get_config()
    ticker = asset_id.split('.')[0] if '.' in asset_id else asset_id
    
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


# ============================================
# UI HELPERS
# ============================================
def get_logo_base64(ticker: str) -> Optional[str]:
    config = get_config()
    logo_dir = config.storage.data_dir / "logos"
    clean_ticker = ticker.upper().replace('_US', '').replace('.US', '').replace('_EU', '').replace('.EU', '')
    
    for ext in ['png', 'jpg', 'svg']:
        path = logo_dir / f"{clean_ticker}.{ext}"
        if path.exists():
            try:
                with open(path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except:
                pass
    return None


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


def get_score_class(score: float) -> str:
    if score is None:
        return "medium"
    if score >= 70:
        return "high"
    elif score >= 40:
        return "medium"
    return "low"


# ============================================
# CHART COMPONENTS
# ============================================
def render_gauge_chart(score: float) -> go.Figure:
    if score is None:
        score = 0
    
    color = "#22C55E" if score >= 70 else "#EAB308" if score >= 40 else "#EF4444"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "/100", 'font': {'size': 36, 'color': '#FFFFFF', 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': 'rgba(255,255,255,0.08)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': 'rgba(239,68,68,0.1)'},
                {'range': [40, 70], 'color': 'rgba(234,179,8,0.1)'},
                {'range': [70, 100], 'color': 'rgba(34,197,94,0.1)'}
            ]
        }
    ))
    
    fig.update_layout(
        height=160,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Inter'}
    )
    return fig


def render_candlestick_chart(df: pd.DataFrame, days: int = 30) -> go.Figure:
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Données non disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(color="#64748B", size=14)
        )
        fig.update_layout(
            height=200,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(26,29,36,0.9)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    df = df.tail(days).copy()
    df.columns = [c.lower() for c in df.columns]
    
    if all(c in df.columns for c in ['open', 'high', 'low', 'close']):
        fig = go.Figure(go.Candlestick(
            x=df.index,
            open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            increasing_line_color='#22C55E', decreasing_line_color='#64748B',
            increasing_fillcolor='#22C55E', decreasing_fillcolor='#64748B'
        ))
    else:
        close_col = 'close' if 'close' in df.columns else df.columns[0]
        fig = go.Figure(go.Scatter(
            x=df.index, y=df[close_col],
            mode='lines', line=dict(color='#22C55E', width=2),
            fill='tozeroy', fillcolor='rgba(34, 197, 94, 0.1)'
        ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=10, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(26,29,36,0.9)',
        showlegend=False,
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            tickfont=dict(color='#64748B', size=10),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            side='right',
            tickfont=dict(color='#64748B', size=10)
        )
    )
    return fig


# ============================================
# SIDEBAR
# ============================================
def render_sidebar():
    with st.sidebar:
        # Logo
        st.markdown('''
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">◉</div>
            <div class="sidebar-logo-text">MarketGPS</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section-title">Navigation</div>', unsafe_allow_html=True)
        
        # Navigation buttons
        col1 = st.container()
        with col1:
            if st.button("📊  Dashboard", key="nav_dash", use_container_width=True):
                st.session_state.current_page = "dashboard"
                st.rerun()
            
            if st.button("🔍  Explorer", key="nav_explore", use_container_width=True):
                st.session_state.current_page = "explorer"
                st.rerun()
            
            if st.button("⭐  Liste de suivi", key="nav_watchlist", use_container_width=True):
                st.session_state.current_page = "watchlist"
                st.rerun()
            
            if st.button("📈  Marchés", key="nav_markets", use_container_width=True):
                st.session_state.current_page = "markets"
                st.rerun()
        
        st.markdown('<div class="sidebar-section-title">Paramètres</div>', unsafe_allow_html=True)
        
        if st.button("⚙️  Paramètres", key="nav_settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
        
        if st.button("🎨  Thème", key="nav_theme", use_container_width=True):
            pass
        
        if st.button("❓  Aide", key="nav_help", use_container_width=True):
            pass
        
        st.markdown("<br>" * 3, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section-title">Compte</div>', unsafe_allow_html=True)
        
        if st.button("👤  Mon profil", key="nav_profile", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
        
        if st.button("🚪  Déconnexion", key="nav_logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()


# ============================================
# TOP BAR
# ============================================
def render_top_bar():
    # Search functionality
    search_col, spacer, actions_col = st.columns([3, 4, 2])
    
    with search_col:
        search_query = st.text_input(
            "Rechercher",
            placeholder="🔍 Rechercher un actif...",
            key="search_input",
            label_visibility="collapsed"
        )
        
        if search_query:
            results = search_assets(search_query, st.session_state.get('market_scope', 'US_EU'))
            if results:
                st.session_state.search_results = results
    
    with actions_col:
        st.markdown('''
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;padding-top:8px;">
            <div class="top-bar-icon">✉️</div>
            <div class="top-bar-icon notification">
                🔔
                <span class="notification-badge">3</span>
            </div>
            <div class="profile-avatar" style="width:36px;height:36px;background:#22C55E;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-weight:600;">
                C
            </div>
        </div>
        ''', unsafe_allow_html=True)


# ============================================
# ASSET TABLE
# ============================================
def render_asset_table(assets: List[Dict]):
    st.markdown('''
    <div class="assets-header">
        <div class="assets-title">Top scorés</div>
    </div>
    <div class="table-header">
        <div>Ticker</div>
        <div style="text-align:center;">Spora</div>
        <div style="text-align:center;">Score</div>
        <div style="text-align:center;">Semantique</div>
        <div></div>
    </div>
    ''', unsafe_allow_html=True)
    
    for i, asset in enumerate(assets[:10]):
        ticker = asset.get('symbol', '')
        score = asset.get('score_total')
        spora = int(score) if score else 0  # Simplified spora
        score_display = int(score) if score else "—"
        semantic_label, semantic_class = get_semantic_label(score)
        score_class = get_score_class(score)
        
        logo_b64 = get_logo_base64(ticker)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="{ticker}">' if logo_b64 else f'<span class="asset-logo-placeholder">{ticker[:2]}</span>'
        
        is_selected = st.session_state.get('selected_asset_id') == asset.get('asset_id')
        selected_class = "selected" if is_selected else ""
        
        st.markdown(f'''
        <div class="asset-row {selected_class}" onclick="void(0)">
            <div class="asset-info">
                <div class="asset-logo">{logo_html}</div>
                <span class="asset-ticker">{ticker}</span>
            </div>
            <div class="score-cell">{spora}</div>
            <div class="score-cell">
                <span class="score-badge {score_class}">{score_display}</span>
            </div>
            <div class="score-cell">
                <span class="semantic-label {semantic_class}">{semantic_label}</span>
            </div>
            <div class="score-cell">
                <div class="check-icon">✓</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Button to select asset (hidden visually but functional)
        if st.button(f"Voir {ticker}", key=f"select_{asset.get('asset_id')}", use_container_width=True):
            st.session_state.selected_asset_id = asset.get('asset_id')
            st.rerun()
    
    # Voir plus button
    if st.button("Voir plus", key="voir_plus", use_container_width=True):
        st.session_state.current_page = "explorer"
        st.rerun()


# ============================================
# DETAIL PANEL
# ============================================
def render_detail_panel(asset_id: str):
    asset = load_asset_detail(asset_id)
    
    if not asset:
        st.warning("Sélectionnez un actif")
        return
    
    ticker = asset.get('symbol', '')
    score = asset.get('score_total') or 0
    value = asset.get('score_value') or 0
    momentum = asset.get('score_momentum') or 0
    safety = asset.get('score_safety') or 0
    coverage = asset.get('coverage') or 0
    liquidity = asset.get('liquidity') or 0
    fx_risk = asset.get('fx_risk') or 0
    market_scope = asset.get('market_scope', 'US_EU')
    
    # Score card with gauge and pillars
    st.markdown('<div class="score-card">', unsafe_allow_html=True)
    
    col_gauge, col_pillars = st.columns([1, 1])
    
    with col_gauge:
        fig = render_gauge_chart(score)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col_pillars:
        st.markdown(f'''
        <div class="score-pillars">
            <div class="pillar-row">
                <span class="pillar-label">Valeur</span>
                <div class="pillar-bar"><div class="pillar-fill" style="width:{value}%;"></div></div>
                <span class="pillar-value">{int(value)}</span>
            </div>
            <div class="pillar-row">
                <span class="pillar-label">Momentum</span>
                <div class="pillar-bar"><div class="pillar-fill" style="width:{momentum}%;"></div></div>
                <span class="pillar-value">{int(momentum)}</span>
            </div>
            <div class="pillar-row">
                <span class="pillar-label">Sécurité</span>
                <div class="pillar-bar"><div class="pillar-fill" style="width:{safety}%;"></div></div>
                <span class="pillar-value">{int(safety)}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # Data quality badges
    coverage_ok = coverage >= 80
    liquidity_ok = liquidity >= 50
    fx_ok = fx_risk <= 30
    
    st.markdown(f'''
    <div class="data-badges">
        <span class="data-badge {"success" if coverage_ok else ""}">{"✓ " if coverage_ok else ""}Données OK</span>
        <span class="data-badge {"success" if liquidity_ok else ""}">{"✓ " if liquidity_ok else ""}Liquidité</span>
        <span class="data-badge {"success" if fx_ok else ""}">{"✓ " if fx_ok else ""}Risque FX</span>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chart card
    st.markdown('''
    <div class="chart-card">
        <div class="chart-header">
            <div class="chart-title">📈 Actif</div>
            <div class="period-selector">
                <span class="period-btn active">Derniers 30 jours</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    df = load_price_history(asset_id, market_scope)
    fig = render_candlestick_chart(df, 30)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Metrics grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Couverture données</div>
            <div class="metric-value green">{int(coverage)}%</div>
            <div class="metric-bar"><div class="metric-bar-fill" style="width:{coverage}%;"></div></div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Risque FX</div>
            <div class="metric-value">{"Faible" if fx_risk <= 30 else "Modéré" if fx_risk <= 60 else "Élevé"}</div>
            <div class="metric-bar"><div class="metric-bar-fill" style="width:{100-fx_risk}%;background:{"#22C55E" if fx_risk <= 30 else "#EAB308" if fx_risk <= 60 else "#EF4444"};"></div></div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        liquidity_label = "Élevée" if liquidity >= 70 else "Moyenne" if liquidity >= 40 else "Faible"
        st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">Liquidité</div>
            <div class="metric-value green">{liquidity_label}</div>
            <div class="metric-bar"><div class="metric-bar-fill" style="width:{liquidity}%;"></div></div>
        </div>
        ''', unsafe_allow_html=True)


# ============================================
# MAIN DASHBOARD
# ============================================
def render_dashboard():
    render_sidebar()
    
    # Top bar
    st.markdown('<h1 style="font-size:24px;font-weight:700;color:#FFFFFF;margin:0 0 24px;">Dashboard</h1>', unsafe_allow_html=True)
    
    render_top_bar()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main content
    market_scope = st.session_state.get('market_scope', 'US_EU')
    assets = load_top_assets(market_scope, None, 50)
    
    # Initialize selected asset
    if not st.session_state.get('selected_asset_id') and assets:
        st.session_state.selected_asset_id = assets[0].get('asset_id')
    
    col_table, col_detail = st.columns([1.2, 1])
    
    with col_table:
        st.markdown('<div class="assets-panel">', unsafe_allow_html=True)
        render_asset_table(assets)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_detail:
        st.markdown('<div class="detail-panel">', unsafe_allow_html=True)
        if st.session_state.get('selected_asset_id'):
            render_detail_panel(st.session_state.selected_asset_id)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# MAIN
# ============================================
def main():
    st.set_page_config(
        page_title="MarketGPS - Dashboard",
        page_icon="◉",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"
    if 'market_scope' not in st.session_state:
        st.session_state.market_scope = "US_EU"
    if 'selected_asset_id' not in st.session_state:
        st.session_state.selected_asset_id = None
    
    inject_dashboard_css()
    render_dashboard()


if __name__ == "__main__":
    main()
