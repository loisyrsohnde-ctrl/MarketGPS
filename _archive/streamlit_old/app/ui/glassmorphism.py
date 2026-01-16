"""
MarketGPS - Glassmorphism Dark Theme CSS
Dark background + translucent green overlay cards
"""
import streamlit as st


def inject_glassmorphism_css():
    """Inject the premium glassmorphism dark theme CSS."""
    st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ═══════════════════════════════════════════════════════════════════════════
       CSS VARIABLES - DARK GLASSMORPHISM
       ═══════════════════════════════════════════════════════════════════════════ */
    :root {
        /* Background colors */
        --bg-primary: #0b0f0d;
        --bg-secondary: #0d1210;
        --bg-card: rgba(16, 24, 20, 0.85);
        --bg-card-hover: rgba(20, 32, 26, 0.92);
        --bg-elevated: rgba(22, 34, 28, 0.9);
        
        /* Glassmorphism */
        --glass-bg: rgba(18, 28, 22, 0.75);
        --glass-border: rgba(34, 197, 94, 0.12);
        --glass-blur: 12px;
        
        /* Accent colors */
        --accent-green: #22C55E;
        --accent-green-dim: rgba(34, 197, 94, 0.15);
        --accent-green-glow: rgba(34, 197, 94, 0.25);
        --accent-teal: #14B8A6;
        --accent-yellow: #EAB308;
        --accent-orange: #F97316;
        --accent-red: #EF4444;
        
        /* Text colors */
        --text-primary: #FFFFFF;
        --text-secondary: #94A3B8;
        --text-muted: #64748B;
        --text-dim: #475569;
        
        /* Border colors */
        --border-subtle: rgba(255, 255, 255, 0.06);
        --border-normal: rgba(255, 255, 255, 0.10);
        --border-active: rgba(34, 197, 94, 0.4);
        
        /* Spacing */
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       BASE STYLES
       ═══════════════════════════════════════════════════════════════════════════ */
    .stApp {
        background: linear-gradient(180deg, var(--bg-primary) 0%, #0a0e0c 100%) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header {display: none !important;}
    .stDeployButton {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    
    /* Main content - FORCE SCROLLING */
    .main, .main .block-container {
        padding: 24px 24px 120px !important;
        max-width: 100% !important;
        overflow-y: scroll !important;
        height: auto !important;
        min-height: 100vh !important;
    }
    
    /* Streamlit main containers - force scroll */
    section[data-testid="stMain"],
    section[data-testid="stMainBlockContainer"],
    .stMainBlockContainer,
    [data-testid="stVerticalBlockBorderWrapper"] {
        overflow-y: scroll !important;
        overflow-x: hidden !important;
        height: auto !important;
        max-height: none !important;
    }
    
    /* App root - ensure scroll is visible */
    .stApp, .stApp > div, .stApp > div > div {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: 100vh !important;
    }
    
    /* Remove any fixed heights that block scroll */
    section[data-testid="stAppViewBlockContainer"],
    .st-emotion-cache-z5fcl4 {
        overflow: auto !important;
        height: auto !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       FORCE COLUMNS SIDE BY SIDE
       ═══════════════════════════════════════════════════════════════════════════ */
    [data-testid="column"] {
        min-width: 0 !important;
        overflow: visible !important;
    }
    
    /* Ensure flex row for columns */
    .stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 16px !important;
        overflow: visible !important;
    }
    
    /* Dashboard two-column main layout */
    .dashboard-main-columns {
        display: grid !important;
        grid-template-columns: 1fr 2fr !important;
        gap: 24px !important;
        min-height: 400px;
    }
    
    .dashboard-left-panel {
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Force main content to use full width */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Constrain sidebar width */
    section[data-testid="stSidebar"] {
        width: 220px !important;
        min-width: 220px !important;
        max-width: 220px !important;
    }
    
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
    }
    
    .dashboard-right-panel {
        min-width: 500px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       SIDEBAR - GLASSMORPHISM
       ═══════════════════════════════════════════════════════════════════════════ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, #090c0a 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 0 !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        padding: 12px 16px !important;
        border-radius: var(--radius-md) !important;
        text-align: left !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        justify-content: flex-start !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--accent-green-dim) !important;
        color: var(--text-primary) !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       GLASSMORPHISM CARDS
       ═══════════════════════════════════════════════════════════════════════════ */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(var(--glass-blur));
        -webkit-backdrop-filter: blur(var(--glass-blur));
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-xl);
        padding: 24px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }
    .glass-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(34, 197, 94, 0.3), transparent);
    }
    
    .glass-card-sm {
        background: var(--glass-bg);
        backdrop-filter: blur(8px);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 16px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       TOP BAR
       ═══════════════════════════════════════════════════════════════════════════ */
    .top-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid var(--border-subtle);
    }
    
    .top-bar-search {
        flex: 1;
        max-width: 500px;
        margin: 0 24px;
    }
    
    .top-bar-icons {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .top-bar-icon {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 18px;
        transition: all 0.2s;
        position: relative;
    }
    .top-bar-icon:hover {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
    }
    
    .notification-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        width: 18px;
        height: 18px;
        background: var(--accent-red);
        border-radius: 50%;
        font-size: 10px;
        font-weight: 700;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--accent-green), var(--accent-teal));
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 600;
        font-size: 16px;
        border: 2px solid var(--accent-green);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       CATEGORY PILLS
       ═══════════════════════════════════════════════════════════════════════════ */
    .category-pills {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    
    .category-pill {
        padding: 8px 16px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid var(--border-subtle);
        background: var(--bg-elevated);
        color: var(--text-secondary);
    }
    .category-pill:hover {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
        color: var(--text-primary);
    }
    .category-pill.active {
        background: var(--accent-green);
        border-color: var(--accent-green);
        color: white;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       TABLE STYLES
       ═══════════════════════════════════════════════════════════════════════════ */
    .table-header {
        display: grid;
        grid-template-columns: 2.5fr 1fr 1fr 1.2fr 0.8fr;
        padding: 12px 20px;
        background: var(--bg-secondary);
        font-size: 11px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        border-bottom: 1px solid var(--border-subtle);
    }
    
    .asset-row {
        display: grid;
        grid-template-columns: 2.5fr 1fr 1fr 1.2fr 0.8fr;
        align-items: center;
        padding: 14px 20px;
        background: var(--bg-elevated);
        border-bottom: 1px solid var(--border-subtle);
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .asset-row:hover {
        background: var(--bg-card-hover);
    }
    .asset-row.selected {
        background: var(--accent-green-dim);
        border-left: 3px solid var(--accent-green);
    }
    .asset-row:last-child {
        border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    }
    
    .asset-info {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .asset-logo {
        width: 40px;
        height: 40px;
        border-radius: var(--radius-md);
        overflow: hidden;
        background: var(--bg-card);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--border-subtle);
    }
    .asset-logo img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    
    .asset-ticker {
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }
    .asset-name {
        font-size: 12px;
        color: var(--text-muted);
        max-width: 150px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       SCORE BADGES - SINGLE COLOR PER RANGE
       ═══════════════════════════════════════════════════════════════════════════ */
    .score-badge {
        padding: 6px 14px;
        border-radius: var(--radius-sm);
        font-size: 14px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 45px;
    }
    /* 81-100: Green */
    .score-badge.score-green {
        background: rgba(34, 197, 94, 0.15);
        color: #22C55E;
    }
    /* 61-80: Light green */
    .score-badge.score-light-green {
        background: rgba(74, 222, 128, 0.15);
        color: #4ADE80;
    }
    /* 31-60: Yellow/Orange */
    .score-badge.score-yellow {
        background: rgba(234, 179, 8, 0.15);
        color: #EAB308;
    }
    /* 0-30: Red */
    .score-badge.score-red {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
    }
    
    /* Score bar in table */
    .score-bar-mini {
        width: 100%;
        height: 6px;
        background: var(--border-subtle);
        border-radius: 3px;
        overflow: hidden;
        margin-top: 4px;
    }
    .score-bar-mini-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
    
    /* Semantic labels */
    .semantic-label {
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .semantic-label.dynamic { background: rgba(34, 197, 94, 0.12); color: #22C55E; }
    .semantic-label.elevated { background: rgba(59, 130, 246, 0.12); color: #60A5FA; }
    .semantic-label.stable { background: rgba(156, 163, 175, 0.12); color: #9CA3AF; }
    .semantic-label.weak { background: rgba(239, 68, 68, 0.12); color: #EF4444; }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       PILLAR BARS (Valeur / Momentum / Sécurité)
       ═══════════════════════════════════════════════════════════════════════════ */
    .pillar-row {
        display: flex;
        align-items: center;
        margin-bottom: 14px;
    }
    .pillar-label {
        width: 90px;
        font-size: 14px;
        color: var(--text-secondary);
        font-weight: 500;
    }
    .pillar-bar {
        flex: 1;
        height: 10px;
        background: var(--border-subtle);
        border-radius: 5px;
        overflow: hidden;
        margin: 0 12px;
    }
    .pillar-fill {
        height: 100%;
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
    
    /* ═══════════════════════════════════════════════════════════════════════════
       KPI CARDS (Couverture, Liquidité, Risque FX)
       ═══════════════════════════════════════════════════════════════════════════ */
    .kpi-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: var(--radius-lg);
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .kpi-label {
        font-size: 12px;
        color: var(--text-muted);
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .kpi-value {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
    }
    .kpi-value.green { color: var(--accent-green); }
    .kpi-value.yellow { color: var(--accent-yellow); }
    .kpi-value.red { color: var(--accent-red); }
    
    .kpi-bar {
        height: 4px;
        background: var(--border-subtle);
        border-radius: 2px;
        margin-top: 10px;
        overflow: hidden;
    }
    .kpi-bar-fill {
        height: 100%;
        border-radius: 2px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       DATA BADGES (Données OK, Liquidité, Risque FX)
       ═══════════════════════════════════════════════════════════════════════════ */
    .data-badges {
        display: flex;
        gap: 10px;
        margin-top: 16px;
        flex-wrap: wrap;
    }
    .data-badge {
        padding: 6px 14px;
        background: var(--bg-elevated);
        border-radius: var(--radius-sm);
        font-size: 12px;
        font-weight: 500;
        color: var(--text-secondary);
        border: 1px solid var(--border-subtle);
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .data-badge.success {
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    .data-badge.warning {
        border-color: var(--accent-yellow);
        color: var(--accent-yellow);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       BUTTONS
       ═══════════════════════════════════════════════════════════════════════════ */
    .stButton > button {
        background: var(--bg-elevated) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--accent-green-dim) !important;
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
    }
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--accent-green) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: #1ea550 !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       INPUTS
       ═══════════════════════════════════════════════════════════════════════════ */
    div[data-testid="stTextInput"] input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: var(--text-muted) !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent-green) !important;
        box-shadow: 0 0 0 3px var(--accent-green-dim) !important;
    }
    
    /* Select boxes */
    div[data-testid="stSelectbox"] > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: var(--radius-md) !important;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       CHARTS (Plotly)
       ═══════════════════════════════════════════════════════════════════════════ */
    .js-plotly-plot .plotly .modebar {display: none !important;}
    
    /* ═══════════════════════════════════════════════════════════════════════════
       SCROLLBAR
       ═══════════════════════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar {width: 6px; height: 6px;}
    ::-webkit-scrollbar-track {background: transparent;}
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.1);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.2);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       FOOTER
       ═══════════════════════════════════════════════════════════════════════════ */
    .app-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 12px 24px;
        background: var(--bg-primary);
        border-top: 1px solid var(--border-subtle);
        text-align: center;
        font-size: 11px;
        color: var(--text-dim);
        z-index: 1000;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       SECTION HEADERS
       ═══════════════════════════════════════════════════════════════════════════ */
    .section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       ASSET DESCRIPTION
       ═══════════════════════════════════════════════════════════════════════════ */
    .asset-description {
        background: var(--bg-elevated);
        border-radius: var(--radius-md);
        padding: 16px;
        margin: 16px 0;
        font-size: 14px;
        line-height: 1.6;
        color: var(--text-secondary);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       EXTERNAL LINKS
       ═══════════════════════════════════════════════════════════════════════════ */
    .external-links {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .external-link {
        padding: 8px 14px;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        color: var(--text-secondary);
        text-decoration: none;
        font-size: 12px;
        font-weight: 500;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
    }
    .external-link:hover {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       PAGINATION
       ═══════════════════════════════════════════════════════════════════════════ */
    .pagination {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin: 20px 0;
    }
    .pagination-btn {
        padding: 8px 16px;
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        color: var(--text-secondary);
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .pagination-btn:hover:not(:disabled) {
        background: var(--accent-green-dim);
        border-color: var(--accent-green);
        color: var(--accent-green);
    }
    .pagination-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .pagination-info {
        padding: 8px 16px;
        color: var(--text-muted);
        font-size: 13px;
    }
    
    /* ═══════════════════════════════════════════════════════════════════════════
       FORCE SIDEBAR ALWAYS VISIBLE
       ═══════════════════════════════════════════════════════════════════════════ */
    /* Hide the collapse button */
    button[data-testid="stSidebarCollapseButton"],
    button[kind="header"],
    section[data-testid="stSidebar"] button[kind="header"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    
    /* Force sidebar to always be expanded */
    section[data-testid="stSidebar"] {
        transform: none !important;
        width: 220px !important;
        min-width: 220px !important;
    }
    
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 220px !important;
        min-width: 220px !important;
        margin-left: 0 !important;
        transform: none !important;
    }
    
    /* Ensure sidebar content is always visible */
    section[data-testid="stSidebar"] > div:first-child {
        width: 220px !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    </style>
    
    <script>
    // Force sidebar to stay open permanently
    (function() {
        function forceSidebarOpen() {
            // Find sidebar element
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar) {
                // Force expanded state
                sidebar.setAttribute('aria-expanded', 'true');
                sidebar.style.width = '220px';
                sidebar.style.minWidth = '220px';
                sidebar.style.transform = 'none';
                sidebar.style.marginLeft = '0';
            }
            
            // Hide collapse buttons
            const collapseButtons = document.querySelectorAll(
                'button[data-testid="stSidebarCollapseButton"], ' +
                'button[kind="header"], ' +
                'button[aria-label="Close sidebar"]'
            );
            collapseButtons.forEach(btn => {
                btn.style.display = 'none';
                btn.style.visibility = 'hidden';
            });
        }
        
        // Run on load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', forceSidebarOpen);
        } else {
            forceSidebarOpen();
        }
        
        // Run periodically to catch any Streamlit re-renders
        setInterval(forceSidebarOpen, 500);
        
        // Also observe for changes
        const observer = new MutationObserver(forceSidebarOpen);
        observer.observe(document.body, { 
            childList: true, 
            subtree: true, 
            attributes: true,
            attributeFilter: ['aria-expanded', 'style']
        });
    })();
    </script>
    ''', unsafe_allow_html=True)
