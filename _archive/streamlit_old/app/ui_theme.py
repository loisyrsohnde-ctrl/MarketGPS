"""
MarketGPS UI Theme Module
Premium 2026 Institutional Design System
"""

import streamlit as st
from pathlib import Path
from typing import Dict, Optional

# ============================================
# Design Tokens
# ============================================

class TOKENS:
    # Background Colors
    BG_PRIMARY = "#0B0F14"
    BG_SECONDARY = "#0F1623"
    BG_SURFACE = "#141B27"
    BG_ELEVATED = "#1A2332"
    BG_HOVER = "#1E2A3B"
    
    # Text Colors - HIGH CONTRAST (lisibilité garantie)
    TEXT_PRIMARY = "rgba(255, 255, 255, 0.95)"   # Blanc quasi-pur
    TEXT_SECONDARY = "rgba(255, 255, 255, 0.82)" # Blanc très lisible
    TEXT_TERTIARY = "rgba(255, 255, 255, 0.68)"  # Blanc lisible pour labels
    TEXT_MUTED = "rgba(255, 255, 255, 0.55)"     # Blanc pour texte secondaire
    
    # Score Bucket Colors (SINGLE COLOR per bucket - NO GRADIENT)
    SCORE_EXCELLENT = "#2EA043"      # 90-100
    SCORE_VERY_GOOD = "#3FB950"      # 80-89
    SCORE_GOOD = "#D29922"           # 65-79
    SCORE_FAIR = "#F0883E"           # 50-64
    SCORE_ALERT = "#F85149"          # 35-49
    SCORE_RISK = "#B42318"           # 0-34
    
    # Accent Colors
    ACCENT_GREEN = "#2EA043"
    ACCENT_GREEN_HOVER = "#3FB950"
    ACCENT_AMBER = "#D29922"
    ACCENT_ORANGE = "#F0883E"
    ACCENT_RED = "#F85149"
    ACCENT_RED_DARK = "#B42318"
    ACCENT_BLUE = "#58A6FF"
    
    # Borders
    BORDER_DEFAULT = "rgba(255, 255, 255, 0.08)"
    BORDER_HOVER = "rgba(255, 255, 255, 0.15)"
    BORDER_SELECTED = "#2EA043"
    
    # Spacing
    SPACE_XS = "4px"
    SPACE_SM = "8px"
    SPACE_MD = "12px"
    SPACE_LG = "16px"
    SPACE_XL = "24px"
    
    # Border Radius
    RADIUS_SM = "8px"
    RADIUS_MD = "12px"
    RADIUS_LG = "16px"
    RADIUS_XL = "20px"
    RADIUS_FULL = "999px"


# ============================================
# Score Bucket Function (CRITICAL)
# ============================================

def score_bucket(score: Optional[float]) -> Dict[str, str]:
    """
    Get color and label for a score bucket.
    Returns SINGLE solid color - NO GRADIENT.
    
    Args:
        score: Score value 0-100 or None
        
    Returns:
        Dict with 'color' and 'label' keys
    """
    if score is None:
        return {"color": TOKENS.TEXT_MUTED, "label": "N/A"}
    
    score = float(score)
    
    if score >= 90:
        return {"color": TOKENS.SCORE_EXCELLENT, "label": "Excellent"}
    elif score >= 80:
        return {"color": TOKENS.SCORE_VERY_GOOD, "label": "Très bon"}
    elif score >= 65:
        return {"color": TOKENS.SCORE_GOOD, "label": "Bon"}
    elif score >= 50:
        return {"color": TOKENS.SCORE_FAIR, "label": "Correct"}
    elif score >= 35:
        return {"color": TOKENS.SCORE_ALERT, "label": "Alerte"}
    else:
        return {"color": TOKENS.SCORE_RISK, "label": "Risque"}


def confidence_bucket(confidence: Optional[float]) -> Dict[str, str]:
    """
    Get color and label for confidence level.
    
    Args:
        confidence: Confidence value 0-100 or None
        
    Returns:
        Dict with 'color' and 'label' keys
    """
    if confidence is None:
        return {"color": TOKENS.TEXT_MUTED, "label": "N/A"}
    
    confidence = float(confidence)
    
    if confidence >= 70:
        return {"color": TOKENS.ACCENT_GREEN, "label": "Haute"}
    elif confidence >= 50:
        return {"color": TOKENS.ACCENT_AMBER, "label": "Moyenne"}
    else:
        return {"color": TOKENS.ACCENT_RED, "label": "Faible"}


# ============================================
# CSS Injection
# ============================================

def inject_theme():
    """Inject the complete theme CSS into Streamlit."""
    
    css = f"""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ============================================
       Global Overrides
       ============================================ */
    html, body, .stApp {{
        background-color: {TOKENS.BG_PRIMARY} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    /* Hide Streamlit native elements */
    #MainMenu, footer, header[data-testid="stHeader"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    
    /* Remove top padding */
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 80px !important;
        max-width: 1600px !important;
    }}
    
    /* Force white text everywhere */
    .stMarkdown, .stMarkdown p, .stMarkdown span,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    .stMarkdown div {{
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    /* ============================================
       Sidebar
       ============================================ */
    section[data-testid="stSidebar"] {{
        background-color: {TOKENS.BG_SECONDARY} !important;
        border-right: 1px solid {TOKENS.BORDER_DEFAULT} !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] label {{
        color: {TOKENS.TEXT_SECONDARY} !important;
    }}
    
    /* ============================================
       Buttons
       ============================================ */
    .stButton > button {{
        background: {TOKENS.BG_SURFACE} !important;
        border: 1px solid {TOKENS.BORDER_DEFAULT} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
        border-radius: {TOKENS.RADIUS_MD} !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }}
    
    .stButton > button:hover {{
        background: {TOKENS.BG_HOVER} !important;
        border-color: {TOKENS.BORDER_HOVER} !important;
    }}
    
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background: {TOKENS.ACCENT_GREEN} !important;
        border-color: {TOKENS.ACCENT_GREEN} !important;
    }}
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        background: {TOKENS.ACCENT_GREEN_HOVER} !important;
        border-color: {TOKENS.ACCENT_GREEN_HOVER} !important;
    }}
    
    /* ============================================
       Form Elements
       ============================================ */
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stTextInput"] input {{
        background: {TOKENS.BG_SURFACE} !important;
        border-color: {TOKENS.BORDER_DEFAULT} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
        border-radius: {TOKENS.RADIUS_MD} !important;
    }}
    
    [data-testid="stTextInput"] input:focus {{
        border-color: {TOKENS.ACCENT_GREEN} !important;
        box-shadow: 0 0 0 1px {TOKENS.ACCENT_GREEN} !important;
    }}
    
    [data-testid="stSelectbox"] label,
    [data-testid="stTextInput"] label {{
        color: {TOKENS.TEXT_SECONDARY} !important;
    }}
    
    /* ============================================
       Tabs - NO OVERLAP
       ============================================ */
    .stTabs {{
        margin-bottom: 16px !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px !important;
        background: transparent !important;
        flex-wrap: wrap !important;
        padding: 4px 0 !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: auto !important;
        padding: 10px 20px !important;
        background: {TOKENS.BG_SURFACE} !important;
        border: 1px solid {TOKENS.BORDER_DEFAULT} !important;
        border-radius: {TOKENS.RADIUS_MD} !important;
        color: {TOKENS.TEXT_SECONDARY} !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: {TOKENS.BG_HOVER} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {TOKENS.ACCENT_GREEN} !important;
        border-color: {TOKENS.ACCENT_GREEN} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {{
        display: none !important;
    }}
    
    /* ============================================
       Radio Buttons (Horizontal - styled as tabs)
       ============================================ */
    [data-testid="stRadio"] > div {{
        gap: 8px !important;
    }}
    
    /* Hide radio circles for horizontal layout */
    [data-testid="stRadio"][data-baseweb="radio-group"] > div > div {{
        flex-direction: row !important;
        gap: 8px !important;
    }}
    
    [data-testid="stRadio"] > div > label > div:first-child {{
        display: none !important;
    }}
    
    /* Style radio button labels as tab-like buttons */
    [data-testid="stRadio"] > div > label {{
        background: {TOKENS.BG_SURFACE} !important;
        border: 1px solid {TOKENS.BORDER_DEFAULT} !important;
        border-radius: {TOKENS.RADIUS_MD} !important;
        padding: 10px 20px !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        color: {TOKENS.TEXT_SECONDARY} !important;
        font-weight: 500 !important;
    }}
    
    [data-testid="stRadio"] > div > label:hover {{
        background: {TOKENS.BG_HOVER} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    /* Selected state */
    [data-testid="stRadio"] > div > label[data-baseweb="radio"]:has(input:checked),
    [data-testid="stRadio"] > div > label:has(input:checked) {{
        background: {TOKENS.ACCENT_GREEN} !important;
        border-color: {TOKENS.ACCENT_GREEN} !important;
        color: {TOKENS.TEXT_PRIMARY} !important;
    }}
    
    /* Hide the actual radio input visually */
    [data-testid="stRadio"] input[type="radio"] {{
        position: absolute !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    
    /* ============================================
       Cards Container - Stable Grid
       ============================================ */
    .gps-cards-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 16px;
        padding: 8px 0;
    }}
    
    /* ============================================
       Asset Card
       ============================================ */
    .gps-card {{
        background: {TOKENS.BG_SURFACE};
        border: 1px solid {TOKENS.BORDER_DEFAULT};
        border-radius: {TOKENS.RADIUS_LG};
        padding: 16px;
        transition: all 0.15s ease;
        overflow: hidden;
    }}
    
    .gps-card:hover {{
        border-color: {TOKENS.BORDER_HOVER};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}
    
    .gps-card.selected {{
        border-color: {TOKENS.BORDER_SELECTED};
        border-width: 2px;
        background: {TOKENS.BG_ELEVATED};
    }}
    
    /* Card Header */
    .gps-card-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }}
    
    /* Logo Circle */
    .gps-logo {{
        width: 40px;
        height: 40px;
        min-width: 40px;
        border-radius: {TOKENS.RADIUS_MD};
        background: linear-gradient(135deg, {TOKENS.BG_ELEVATED}, {TOKENS.BG_HOVER});
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        color: {TOKENS.TEXT_SECONDARY};
        border: 1px solid {TOKENS.BORDER_DEFAULT};
        overflow: hidden;
    }}
    
    .gps-logo img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    
    /* Card Info */
    .gps-card-info {{
        flex: 1;
        min-width: 0;
        overflow: hidden;
    }}
    
    .gps-card-name {{
        font-size: 15px;
        font-weight: 600;
        color: {TOKENS.TEXT_PRIMARY};
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
        margin: 0;
    }}
    
    .gps-card-meta {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 4px;
        font-size: 13px;
        color: {TOKENS.TEXT_SECONDARY};
    }}
    
    /* Badge */
    .gps-badge {{
        display: inline-flex;
        padding: 2px 8px;
        border-radius: {TOKENS.RADIUS_FULL};
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .gps-badge-equity {{
        background: rgba(88, 166, 255, 0.15);
        color: {TOKENS.ACCENT_BLUE};
    }}
    
    .gps-badge-etf {{
        background: rgba(46, 160, 67, 0.15);
        color: {TOKENS.ACCENT_GREEN};
    }}
    
    /* Score Section */
    .gps-score-section {{
        margin-top: 12px;
    }}
    
    .gps-score-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}
    
    .gps-score-label {{
        font-size: 11px;
        color: {TOKENS.TEXT_TERTIARY};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .gps-score-value {{
        font-size: 18px;
        font-weight: 700;
    }}
    
    /* Score Bar - SINGLE COLOR FILL */
    .gps-score-bar {{
        height: 8px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: {TOKENS.RADIUS_FULL};
        overflow: hidden;
    }}
    
    .gps-score-bar-fill {{
        height: 100%;
        border-radius: {TOKENS.RADIUS_FULL};
        transition: width 0.3s ease;
        /* NO GRADIENT - Single solid color */
    }}
    
    /* Confidence */
    .gps-confidence {{
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 8px;
        font-size: 11px;
        color: {TOKENS.TEXT_TERTIARY};
    }}
    
    .gps-confidence-dot {{
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }}
    
    /* ============================================
       Detail Panel - STICKY & PROFESSIONAL
       ============================================ */
    .gps-detail-panel {{
        background: {TOKENS.BG_SURFACE};
        border: 1px solid {TOKENS.BORDER_DEFAULT};
        border-radius: {TOKENS.RADIUS_XL};
        padding: 20px;
        position: sticky;
        top: 20px;
        max-height: calc(100vh - 120px);
        overflow-y: auto;
        overflow-x: hidden;
    }}
    
    .gps-detail-panel::-webkit-scrollbar {{
        width: 4px;
    }}
    
    .gps-detail-panel::-webkit-scrollbar-thumb {{
        background: {TOKENS.BG_HOVER};
        border-radius: 2px;
    }}
    
    /* ============================================
       MAIN LAYOUT - FORCE SIDE-BY-SIDE
       ============================================ */
    /* Target the main columns container to prevent stacking */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 16px !important;
        align-items: flex-start !important;
    }}
    
    /* Ensure columns stay side by side on wide screens */
    @media (min-width: 992px) {{
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex-shrink: 0 !important;
        }}
        
        /* Left column - asset cards */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:first-child {{
            flex: 1.5 !important;
            min-width: 0 !important;
        }}
        
        /* Right column - detail panel - fixed width */
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {{
            flex: 0 0 400px !important;
            max-width: 400px !important;
            min-width: 350px !important;
            position: sticky !important;
            top: 20px !important;
            align-self: flex-start !important;
        }}
    }}
    
    /* On larger screens, make detail panel wider */
    @media (min-width: 1400px) {{
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {{
            flex: 0 0 450px !important;
            max-width: 450px !important;
        }}
    }}
    
    /* On very large screens */
    @media (min-width: 1800px) {{
        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {{
            flex: 0 0 500px !important;
            max-width: 500px !important;
        }}
    }}
    
    /* ============================================
       Footer
       ============================================ */
    .gps-footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {TOKENS.BG_SECONDARY};
        border-top: 1px solid {TOKENS.BORDER_DEFAULT};
        padding: 10px 24px;
        font-size: 11px;
        color: {TOKENS.TEXT_MUTED};
        text-align: center;
        z-index: 100;
    }}
    
    /* ============================================
       Scrollbar
       ============================================ */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {TOKENS.BG_PRIMARY};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {TOKENS.BG_ELEVATED};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {TOKENS.BG_HOVER};
    }}
    
    /* ============================================
       Responsive
       ============================================ */
    
    /* Medium screens - adjust layout */
    @media (max-width: 991px) {{
        /* Stack columns on smaller screens */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}
        
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: 1 1 100% !important;
            max-width: 100% !important;
            min-width: 100% !important;
        }}
        
        /* Detail panel becomes a fixed bottom drawer on mobile */
        .gps-detail-panel {{
            position: fixed !important;
            bottom: 50px !important;
            left: 0 !important;
            right: 0 !important;
            top: auto !important;
            max-height: 60vh !important;
            border-radius: {TOKENS.RADIUS_XL} {TOKENS.RADIUS_XL} 0 0 !important;
            border-bottom: none !important;
            z-index: 50;
            box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4) !important;
        }}
    }}
    
    @media (max-width: 768px) {{
        .gps-cards-grid {{
            grid-template-columns: 1fr;
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            flex-direction: column;
            align-items: stretch;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            text-align: center;
        }}
        
        /* Smaller font sizes on mobile */
        .gps-card-name {{
            font-size: 14px !important;
        }}
        
        .gps-score-value {{
            font-size: 16px !important;
        }}
    }}
    
    /* ============================================
       Animation for smooth transitions
       ============================================ */
    .gps-detail-panel,
    .gps-card {{
        transition: all 0.2s ease-out;
    }}
    
    /* Fade in animation for detail panel */
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .gps-detail-panel {{
        animation: fadeInUp 0.25s ease-out;
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)
