"""
MarketGPS — Theme Module
Design System "Premium Green" institutionnel.
"""

import streamlit as st


class DesignTokens:
    """Tokens de design."""
    BG_PRIMARY = "#0B0F19"
    BG_SECONDARY = "#0D1117"
    SURFACE = "rgba(255,255,255,0.04)"
    SURFACE_HOVER = "rgba(255,255,255,0.08)"
    BORDER = "rgba(255,255,255,0.08)"
    BORDER_HOVER = "rgba(46,204,113,0.4)"
    
    TEXT_PRIMARY = "rgba(255,255,255,0.92)"
    TEXT_SECONDARY = "rgba(255,255,255,0.74)"
    TEXT_MUTED = "rgba(255,255,255,0.45)"
    
    ACCENT = "#2ECC71"
    ACCENT_DEEP = "#0B3D2E"
    ACCENT_SOFT = "#A7F3D0"
    ACCENT_GLOW = "rgba(46,204,113,0.15)"
    
    WARNING = "#F5C452"
    DANGER = "#FF6B6B"


def inject_theme():
    """Injecte le thème CSS premium."""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        *, *::before, *::after {{ box-sizing: border-box; }}
        
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* Hide Streamlit chrome */
        header[data-testid="stHeader"], [data-testid="stToolbar"],
        .stDeployButton, #MainMenu, footer {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }}
        
        .stApp {{ background: linear-gradient(180deg, {DesignTokens.BG_PRIMARY} 0%, {DesignTokens.BG_SECONDARY} 100%); }}
        
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 1400px !important;
        }}
        
        /* Cards */
        .gps-card {{
            background: {DesignTokens.SURFACE};
            border: 1px solid {DesignTokens.BORDER};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            transition: all 180ms ease;
        }}
        
        .gps-card:hover {{
            background: {DesignTokens.SURFACE_HOVER};
            border-color: {DesignTokens.BORDER_HOVER};
            transform: translateY(-1px);
        }}
        
        .gps-card-compact {{
            background: {DesignTokens.SURFACE};
            border: 1px solid {DesignTokens.BORDER};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 150ms ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .gps-card-compact:hover {{
            background: {DesignTokens.SURFACE_HOVER};
            border-color: {DesignTokens.BORDER_HOVER};
        }}
        
        .gps-card-compact.selected {{
            border-color: {DesignTokens.ACCENT};
            background: rgba(46,204,113,0.08);
        }}
        
        /* Typography */
        .gps-h1 {{ font-size: 32px; font-weight: 700; color: {DesignTokens.TEXT_PRIMARY}; letter-spacing: -0.02em; }}
        .gps-h2 {{ font-size: 20px; font-weight: 600; color: {DesignTokens.TEXT_PRIMARY}; }}
        .gps-h3 {{ font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY}; }}
        .gps-label {{ font-size: 11px; font-weight: 500; color: {DesignTokens.TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; }}
        .gps-value {{ font-size: 24px; font-weight: 700; color: {DesignTokens.TEXT_PRIMARY}; font-variant-numeric: tabular-nums; }}
        
        /* Chips */
        .gps-chip {{
            display: inline-flex; align-items: center;
            padding: 4px 10px; border-radius: 100px;
            font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
        }}
        .gps-chip-accent {{ background: rgba(46,204,113,0.15); color: {DesignTokens.ACCENT_SOFT}; }}
        .gps-chip-warning {{ background: rgba(245,196,82,0.15); color: {DesignTokens.WARNING}; }}
        .gps-chip-neutral {{ background: {DesignTokens.SURFACE}; color: {DesignTokens.TEXT_SECONDARY}; border: 1px solid {DesignTokens.BORDER}; }}
        .gps-chip-high {{ background: rgba(46,204,113,0.15); color: {DesignTokens.ACCENT}; }}
        .gps-chip-low {{ background: rgba(96,165,250,0.15); color: #60A5FA; }}
        
        /* Badges */
        .gps-badge {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; }}
        .gps-badge-success {{ background: {DesignTokens.ACCENT}; }}
        .gps-badge-warning {{ background: {DesignTokens.WARNING}; }}
        .gps-badge-danger {{ background: {DesignTokens.DANGER}; }}
        
        /* Buttons */
        .stButton > button {{
            background: {DesignTokens.SURFACE} !important;
            border: 1px solid {DesignTokens.BORDER} !important;
            border-radius: 8px !important;
            color: {DesignTokens.TEXT_PRIMARY} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            padding: 10px 16px !important;
            transition: all 150ms ease !important;
        }}
        
        .stButton > button:hover {{
            background: {DesignTokens.SURFACE_HOVER} !important;
            border-color: {DesignTokens.ACCENT} !important;
            color: {DesignTokens.ACCENT} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetric"] {{
            background: {DesignTokens.SURFACE} !important;
            border: 1px solid {DesignTokens.BORDER} !important;
            border-radius: 12px !important;
            padding: 16px !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            font-size: 10px !important;
            color: {DesignTokens.TEXT_MUTED} !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
        }}
        
        [data-testid="stMetricValue"] {{
            font-size: 18px !important;
            font-weight: 700 !important;
            color: {DesignTokens.TEXT_PRIMARY} !important;
        }}
        
        /* Selectbox */
        [data-testid="stSelectbox"] > div > div {{
            background: {DesignTokens.SURFACE} !important;
            border: 1px solid {DesignTokens.BORDER} !important;
            border-radius: 8px !important;
            color: {DesignTokens.TEXT_PRIMARY} !important;
        }}
        
        /* Expander */
        [data-testid="stExpanderToggleIcon"] {{ display: none !important; }}
        
        .streamlit-expanderHeader {{
            background: {DesignTokens.SURFACE} !important;
            border: 1px solid {DesignTokens.BORDER} !important;
            border-radius: 8px !important;
        }}
        
        /* Link buttons */
        .stLinkButton > a {{
            background: {DesignTokens.SURFACE} !important;
            border: 1px solid {DesignTokens.BORDER} !important;
            border-radius: 8px !important;
            color: {DesignTokens.TEXT_SECONDARY} !important;
            font-size: 12px !important;
        }}
        
        .stLinkButton > a:hover {{
            border-color: {DesignTokens.ACCENT} !important;
            color: {DesignTokens.ACCENT} !important;
        }}
        
        /* Footer */
        .gps-footer {{
            margin-top: 32px; padding: 16px;
            border-top: 1px solid {DesignTokens.BORDER};
            text-align: center;
        }}
        
        .gps-footer-text {{
            font-size: 11px; color: {DesignTokens.TEXT_MUTED}; line-height: 1.6;
        }}
        
        /* Sidebar navigation */
        [data-testid="stSidebarNav"] {{
            background: transparent !important;
        }}
        
        [data-testid="stSidebarNav"] a {{
            color: {DesignTokens.TEXT_SECONDARY} !important;
            font-size: 13px !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            margin: 2px 8px !important;
        }}
        
        [data-testid="stSidebarNav"] a:hover {{
            background: {DesignTokens.SURFACE} !important;
            color: {DesignTokens.ACCENT} !important;
        }}
        
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(11,61,46,0.15) 0%, {DesignTokens.BG_PRIMARY} 30%) !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: {DesignTokens.BG_PRIMARY}; }}
        ::-webkit-scrollbar-thumb {{ background: {DesignTokens.BORDER}; border-radius: 3px; }}
    </style>
    """, unsafe_allow_html=True)
