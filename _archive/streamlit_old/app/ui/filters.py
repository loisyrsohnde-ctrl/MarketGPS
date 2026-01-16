"""
MarketGPS - Filter Components
Category pills and top bar
"""
import streamlit as st
from typing import Optional, Callable


# ═══════════════════════════════════════════════════════════════════════════
# TOP BAR (Search + Icons + Avatar)
# ═══════════════════════════════════════════════════════════════════════════

def render_top_bar(
    on_search: Optional[Callable] = None,
    user_initial: str = "U",
    notifications: int = 3
):
    """
    Render the top bar with:
    - Page title
    - Search input
    - Message icon
    - Notification icon with badge
    - User avatar
    """
    
    col_title, col_search, col_icons = st.columns([1.5, 4, 2])
    
    with col_title:
        st.markdown('''
        <h1 style="font-size:26px;font-weight:700;color:#FFFFFF;margin:0;padding:8px 0;">
            Dashboard
        </h1>
        ''', unsafe_allow_html=True)
    
    with col_search:
        search_query = st.text_input(
            "Rechercher",
            placeholder="🔍 Rechercher un actif...",
            key="dashboard_search",
            label_visibility="collapsed"
        )
        if search_query and on_search:
            on_search(search_query)
    
    with col_icons:
        st.markdown(f'''
        <div class="top-bar-icons" style="display:flex;align-items:center;justify-content:flex-end;gap:12px;padding-top:6px;">
            <div class="top-bar-icon" title="Messages">
                ✉️
            </div>
            <div class="top-bar-icon" style="position:relative;" title="Notifications">
                🔔
                {f'<span class="notification-badge">{notifications}</span>' if notifications > 0 else ''}
            </div>
            <div class="avatar" title="Mon compte">
                {user_initial}
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    return search_query


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY PILLS
# ═══════════════════════════════════════════════════════════════════════════

def render_category_pills(
    current_market: str = "ALL",
    current_type: str = "All",
    on_filter_change: Optional[Callable] = None
):
    """
    Render compact category filters using selectboxes instead of many buttons.
    """
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        market_options = ["Tous", "🇺🇸 USA", "🇪🇺 Europe", "🌍 Afrique"]
        market_values = ["ALL", "US", "EU", "AFRICA"]
        current_idx = market_values.index(current_market) if current_market in market_values else 0
        
        selected_market = st.selectbox(
            "Région",
            market_options,
            index=current_idx,
            key="market_filter_select",
            label_visibility="collapsed"
        )
        
        new_market = market_values[market_options.index(selected_market)]
        if new_market != current_market:
            st.session_state.market_filter = new_market
            if new_market == 'AFRICA':
                st.session_state.market_scope = 'AFRICA'
            else:
                st.session_state.market_scope = 'US_EU'
            st.rerun()
    
    with col2:
        type_options = ["Tous", "📊 ETF", "📈 Actions", "💱 FX", "📄 Obligations"]
        type_values = ["All", "ETF", "EQUITY", "FX", "BOND"]
        current_type_idx = type_values.index(current_type) if current_type in type_values else 0
        
        selected_type = st.selectbox(
            "Type",
            type_options,
            index=current_type_idx,
            key="type_filter_select",
            label_visibility="collapsed"
        )
        
        new_type = type_values[type_options.index(selected_type)]
        if new_type != current_type:
            st.session_state.type_filter = new_type
            st.rerun()
    
    with col3:
        if st.button("📋 Explorer tous →", key="voir_plus_header", use_container_width=True):
            st.session_state.view = 'explorer'
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# PERIOD SELECTOR (for charts)
# ═══════════════════════════════════════════════════════════════════════════

def render_period_selector(current_period: str = "30d") -> str:
    """
    Render period selector for charts.
    Returns selected period: "30d", "1y", "5y", "10y"
    """
    
    periods = [
        ("30d", "30 jours"),
        ("1y", "1 an"),
        ("5y", "5 ans"),
        ("10y", "10 ans")
    ]
    
    cols = st.columns(len(periods))
    
    for idx, (period_key, period_label) in enumerate(periods):
        with cols[idx]:
            is_active = current_period == period_key
            btn_type = "primary" if is_active else "secondary"
            
            if st.button(period_label, key=f"period_{period_key}", use_container_width=True, type=btn_type):
                st.session_state.chart_range = period_key
                return period_key
    
    return current_period


# ═══════════════════════════════════════════════════════════════════════════
# EXPLORER FILTERS
# ═══════════════════════════════════════════════════════════════════════════

def render_explorer_filters(
    available_types: list,
    current_scope: str = "US_EU",
    current_type: str = "Tous",
    current_limit: int = 50,
    only_scored: bool = True
):
    """
    Render explorer page filters:
    - Region selector
    - Type selector
    - Display limit
    - Only scored checkbox
    - Search input
    """
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    
    with col1:
        scope_options = ["US_EU", "AFRICA"]
        scope_idx = scope_options.index(current_scope) if current_scope in scope_options else 0
        scope = st.selectbox(
            "Région",
            scope_options,
            index=scope_idx,
            format_func=lambda x: "🇺🇸🇪🇺 US/Europe" if x == "US_EU" else "🌍 Afrique",
            key="explorer_scope_select"
        )
    
    with col2:
        type_options = ["Tous"] + available_types
        type_idx = type_options.index(current_type) if current_type in type_options else 0
        asset_type = st.selectbox(
            "Type",
            type_options,
            index=type_idx,
            key="explorer_type_select"
        )
    
    with col3:
        limit_options = {"Top 10": 10, "Top 30": 30, "Top 50": 50, "Top 100": 100, "Tout": 0}
        limit_keys = list(limit_options.keys())
        # Find current limit key
        current_limit_key = next((k for k, v in limit_options.items() if v == current_limit), "Top 50")
        limit_idx = limit_keys.index(current_limit_key) if current_limit_key in limit_keys else 2
        
        limit_selection = st.selectbox(
            "Affichage",
            limit_keys,
            index=limit_idx,
            key="explorer_limit_select"
        )
        limit = limit_options[limit_selection]
    
    with col4:
        only_scored = st.checkbox(
            "Seulement scorés",
            value=only_scored,
            key="explorer_scored_check"
        )
    
    with col5:
        search = st.text_input(
            "Rechercher",
            placeholder="🔍 Ticker ou nom...",
            key="explorer_search"
        )
    
    return scope, asset_type, limit, only_scored, search


# ═══════════════════════════════════════════════════════════════════════════
# PAGINATION CONTROLS
# ═══════════════════════════════════════════════════════════════════════════

def render_pagination(current_page: int, total_pages: int, page_size: int = 50) -> int:
    """
    Render pagination controls.
    Returns new page number if changed.
    """
    if total_pages <= 1:
        return current_page
    
    cols = st.columns([1, 1, 2, 1, 1])
    
    with cols[0]:
        if st.button("⏮ Début", disabled=(current_page == 1), key="page_start"):
            return 1
    
    with cols[1]:
        if st.button("◀ Précédent", disabled=(current_page == 1), key="page_prev"):
            return max(1, current_page - 1)
    
    with cols[2]:
        st.markdown(f'''
        <div style="text-align:center;padding:8px;color:#94A3B8;font-size:13px;">
            Page {current_page} / {total_pages}
        </div>
        ''', unsafe_allow_html=True)
    
    with cols[3]:
        if st.button("Suivant ▶", disabled=(current_page >= total_pages), key="page_next"):
            return min(total_pages, current_page + 1)
    
    with cols[4]:
        if st.button("Fin ⏭", disabled=(current_page >= total_pages), key="page_end"):
            return total_pages
    
    return current_page
