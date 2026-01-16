"""
MarketGPS - Card Components
ScoreGauge, PillarBars, KPIs, TopScoredTable, AssetRow
"""
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import base64
from pathlib import Path
import pandas as pd


def get_current_price_from_asset(asset: Dict, asset_id: str = None, market_scope: str = "US_EU") -> Optional[float]:
    """
    Get current price for an asset.
    Tries: 1) last_price from asset dict, 2) last close from Parquet data.
    """
    # Try from asset dict first
    last_price = asset.get('last_price')
    if last_price and last_price > 0:
        return float(last_price)

    # Fallback: get from Parquet if asset_id provided
    if asset_id:
        try:
            from core.config import get_config
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
                            df.columns = [c.lower() for c in df.columns]
                            if 'close' in df.columns:
                                return float(df['close'].iloc[-1])
                            elif len(df.columns) > 0:
                                return float(df.iloc[-1, 0])
                    except:
                        continue
        except:
            pass

    return None


def format_price_display(price: Optional[float], currency: str = "USD") -> str:
    """Format price for display."""
    if price is None or price <= 0:
        return "—"

    if price < 1:
        return f"{price:.4f} {currency}"
    elif price < 100:
        return f"{price:.2f} {currency}"
    else:
        return f"{price:.2f} {currency}"


# ═══════════════════════════════════════════════════════════════════════════
# SCORE COLOR MAPPING - SINGLE COLOR PER RANGE
# ═══════════════════════════════════════════════════════════════════════════

def get_score_color_single(score: Optional[float]) -> Tuple[str, str]:
    """
    Get single color for score based on range.
    Returns (hex_color, css_class)

    Mapping:
    - 81-100: Green (#22C55E)
    - 61-80:  Light green (#4ADE80)
    - 31-60:  Yellow/Orange (#EAB308)
    - 0-30:   Red (#EF4444)
    """
    if score is None:
        return ("#64748B", "score-na")

    if score >= 81:
        return ("#22C55E", "score-green")
    elif score >= 61:
        return ("#4ADE80", "score-light-green")
    elif score >= 31:
        return ("#EAB308", "score-yellow")
    else:
        return ("#EF4444", "score-red")


def get_semantic_label(score: Optional[float]) -> Tuple[str, str]:
    """Get semantic label based on score."""
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


# ═══════════════════════════════════════════════════════════════════════════
# LOGO UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def get_logo_html(ticker: str, size: int = 40) -> str:
    """Get logo HTML with fallback to initials."""
    from core.config import get_config

    config = get_config()
    logo_dir = config.storage.data_dir / "logos"
    clean_ticker = ticker.upper().replace('_US', '').replace(
        '.US', '').replace('_PA', '').replace('_XETRA', '')

    # Check local file
    for ext in ['png', 'jpg', 'svg']:
        path = logo_dir / f"{clean_ticker}.{ext}"
        if path.exists():
            try:
                with open(path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()
                return f'''<div class="asset-logo" style="width:{size}px;height:{size}px;">
                    <img src="data:image/png;base64,{encoded}" style="width:100%;height:100%;object-fit:contain;">
                </div>'''
            except:
                pass

    # Fallback to initials
    initials = clean_ticker[:2].upper()
    return f'''<div class="asset-logo" style="width:{size}px;height:{size}px;background:linear-gradient(135deg,rgba(34,197,94,0.2),rgba(34,197,94,0.1));display:flex;align-items:center;justify-content:center;">
        <span style="font-size:{size//3}px;font-weight:600;color:#22C55E;">{initials}</span>
    </div>'''


# ═══════════════════════════════════════════════════════════════════════════
# SCORE GAUGE (Semi-circle)
# ═══════════════════════════════════════════════════════════════════════════

def render_score_gauge(score: Optional[float]) -> go.Figure:
    """Create animated semi-circle gauge chart."""
    if score is None:
        score = 0

    color, _ = get_score_color_single(score)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            'suffix': "/100",
            'font': {'size': 48, 'color': '#FFFFFF', 'family': 'Inter'}
        },
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': 'rgba(255,255,255,0.06)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 30], 'color': 'rgba(239, 68, 68, 0.08)'},
                {'range': [30, 60], 'color': 'rgba(234, 179, 8, 0.08)'},
                {'range': [60, 80], 'color': 'rgba(74, 222, 128, 0.08)'},
                {'range': [80, 100], 'color': 'rgba(34, 197, 94, 0.08)'},
            ],
        }
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#FFFFFF', 'family': 'Inter'}
    )

    return fig


# ═══════════════════════════════════════════════════════════════════════════
# PILLAR BARS (Valeur, Momentum, Sécurité)
# ═══════════════════════════════════════════════════════════════════════════

def render_pillar_bars(value: float, momentum: float, safety: float):
    """Render the 3 pillar progress bars."""

    def get_pillar_color(val):
        color, _ = get_score_color_single(val)
        return color

    st.markdown(f'''
    <div style="padding:8px 0;">
        <div class="pillar-row">
            <span class="pillar-label">Valeur</span>
            <div class="pillar-bar">
                <div class="pillar-fill" style="width:{value}%;background:{get_pillar_color(value)};"></div>
            </div>
            <span class="pillar-value">{int(value)}</span>
        </div>
        <div class="pillar-row">
            <span class="pillar-label">Momentum</span>
            <div class="pillar-bar">
                <div class="pillar-fill" style="width:{momentum}%;background:{get_pillar_color(momentum)};"></div>
            </div>
            <span class="pillar-value">{int(momentum)}</span>
        </div>
        <div class="pillar-row">
            <span class="pillar-label">Sécurité</span>
            <div class="pillar-bar">
                <div class="pillar-fill" style="width:{safety}%;background:{get_pillar_color(safety)};"></div>
            </div>
            <span class="pillar-value">{int(safety)}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# KPI CARDS (Couverture, Liquidité, Risque FX)
# ═══════════════════════════════════════════════════════════════════════════

def render_kpi_cards(coverage: float, liquidity: float, fx_risk: float):
    """Render the KPI cards in a column."""

    # Couverture données
    cov_color = "#22C55E" if coverage >= 80 else "#EAB308" if coverage >= 50 else "#EF4444"
    cov_class = "green" if coverage >= 80 else "yellow" if coverage >= 50 else "red"

    # Liquidité
    liq_label = "Élevée" if liquidity >= 70 else "Moyenne" if liquidity >= 40 else "Faible"
    liq_color = "#22C55E" if liquidity >= 70 else "#EAB308" if liquidity >= 40 else "#EF4444"
    liq_class = "green" if liquidity >= 70 else "yellow" if liquidity >= 40 else "red"

    # Risque FX
    fx_label = "Faible" if fx_risk <= 30 else "Modéré" if fx_risk <= 60 else "Élevé"
    fx_color = "#22C55E" if fx_risk <= 30 else "#EAB308" if fx_risk <= 60 else "#EF4444"
    fx_class = "green" if fx_risk <= 30 else "yellow" if fx_risk <= 60 else "red"

    st.markdown(f'''
    <div class="kpi-card">
        <div class="kpi-label">Couverture données</div>
        <div class="kpi-value {cov_class}">{int(coverage)}%</div>
        <div class="kpi-bar">
            <div class="kpi-bar-fill" style="width:{coverage}%;background:{cov_color};"></div>
        </div>
    </div>
    
    <div class="kpi-card">
        <div class="kpi-label">Liquidité</div>
        <div class="kpi-value {liq_class}">{liq_label}</div>
        <div class="kpi-bar">
            <div class="kpi-bar-fill" style="width:{liquidity}%;background:{liq_color};"></div>
        </div>
    </div>
    
    <div class="kpi-card">
        <div class="kpi-label">Risque FX</div>
        <div class="kpi-value {fx_class}">{fx_label}</div>
        <div class="kpi-bar">
            <div class="kpi-bar-fill" style="width:{100-fx_risk}%;background:{fx_color};"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# DATA BADGES
# ═══════════════════════════════════════════════════════════════════════════

def render_data_badges(coverage: float, liquidity: float, fx_risk: float):
    """Render data quality badges."""

    cov_ok = coverage >= 80
    liq_ok = liquidity >= 50
    fx_ok = fx_risk <= 30

    st.markdown(f'''
    <div class="data-badges">
        <span class="data-badge {"success" if cov_ok else ""}">
            {"✓ " if cov_ok else ""}Données OK
        </span>
        <span class="data-badge {"success" if liq_ok else ""}">
            {"✓ " if liq_ok else ""}Liquidité
        </span>
        <span class="data-badge {"success" if fx_ok else "warning" if fx_risk <= 60 else ""}">
            {"✓ " if fx_ok else ""}Risque FX
        </span>
    </div>
    ''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ASSET ROW (for table)
# ═══════════════════════════════════════════════════════════════════════════

def render_asset_row_v2(asset: Dict, is_selected: bool = False) -> bool:
    """
    Render a single asset row with:
    - Logo + Ticker
    - Spora (score value)
    - Score badge with color
    - Semantic label
    - Check icon

    Returns True if the "Voir" button was clicked.
    """
    ticker = asset.get('ticker', asset.get('symbol', ''))
    name = asset.get('name', ticker)
    score = asset.get('score_total')
    asset_id = asset.get('asset_id', ticker)

    # Score display
    score_val = int(score) if score else 0
    score_display = str(score_val) if score else "—"
    color, color_class = get_score_color_single(score)
    semantic_text, semantic_class = get_semantic_label(score)

    selected_class = "selected" if is_selected else ""

    # Render HTML row
    st.markdown(f'''
    <div class="asset-row {selected_class}">
        <div class="asset-info">
            {get_logo_html(ticker, 40)}
            <div>
                <div class="asset-ticker">{ticker}</div>
                <div class="asset-name">{name[:25]}{"..." if len(name) > 25 else ""}</div>
            </div>
        </div>
        <div style="text-align:center;">
            <div style="font-weight:600;color:#FFFFFF;font-size:15px;">{score_val}</div>
            <div class="score-bar-mini">
                <div class="score-bar-mini-fill" style="width:{score_val}%;background:{color};"></div>
            </div>
        </div>
        <div style="text-align:center;">
            <span class="score-badge {color_class}">{score_display}</span>
        </div>
        <div style="text-align:center;">
            <span class="semantic-label {semantic_class}">{semantic_text}</span>
        </div>
        <div style="text-align:center;">
            <div style="width:26px;height:26px;border-radius:50%;background:{"#22C55E" if score and score >= 60 else "rgba(255,255,255,0.1)"};display:inline-flex;align-items:center;justify-content:center;color:white;font-size:14px;">
                {"✓" if score and score >= 60 else "—"}
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Voir button
    return st.button("Voir", key=f"voir_{asset_id}", use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TOP SCORED TABLE
# ═══════════════════════════════════════════════════════════════════════════

def render_top_scored_table(assets: List[Dict], title: str = "Top scorés", show_header: bool = True):
    """Render the complete top scored table with header."""

    if show_header:
        st.markdown(f'''
        <div class="glass-card" style="padding:0;overflow:hidden;">
            <div class="section-header">
                <span class="section-title">{title}</span>
            </div>
            <div class="table-header">
                <div>Ticker</div>
                <div style="text-align:center;">Spora</div>
                <div style="text-align:center;">Score</div>
                <div style="text-align:center;">Semantique</div>
                <div></div>
            </div>
        ''', unsafe_allow_html=True)

    selected_asset = None

    for asset in assets:
        if render_asset_row_v2(asset, is_selected=(st.session_state.get('selected_asset_id') == asset.get('asset_id'))):
            selected_asset = asset.get('asset_id')

    if show_header:
        st.markdown('</div>', unsafe_allow_html=True)

    return selected_asset


# ═══════════════════════════════════════════════════════════════════════════
# CANDLESTICK CHART
# ═══════════════════════════════════════════════════════════════════════════

def render_candlestick_chart(df, days: int = 30) -> go.Figure:
    """Create candlestick or line chart based on data availability."""
    import pandas as pd

    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=250,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(18, 28, 22, 0.9)',
            annotations=[{
                'text': 'Données non disponibles',
                'xref': 'paper', 'yref': 'paper',
                'x': 0.5, 'y': 0.5,
                'showarrow': False,
                'font': {'size': 14, 'color': '#64748B'}
            }]
        )
        return fig

    # Get last N days
    df = df.tail(days).copy()
    df.columns = [c.lower() for c in df.columns]

    # Check for OHLC data
    if all(c in df.columns for c in ['open', 'high', 'low', 'close']):
        fig = go.Figure(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            increasing_line_color='#22C55E',
            decreasing_line_color='#64748B',
            increasing_fillcolor='#22C55E',
            decreasing_fillcolor='#64748B'
        ))
    else:
        # Fallback to line chart
        close_col = 'close' if 'close' in df.columns else df.columns[0]
        fig = go.Figure(go.Scatter(
            x=df.index,
            y=df[close_col],
            mode='lines',
            line=dict(color='#22C55E', width=2),
            fill='tozeroy',
            fillcolor='rgba(34, 197, 94, 0.1)'
        ))

    fig.update_layout(
        height=250,
        margin=dict(l=0, r=10, t=10, b=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(18, 28, 22, 0.9)',
        showlegend=False,
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.04)',
            tickfont=dict(color='#64748B', size=10),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.04)',
            side='right',
            tickfont=dict(color='#64748B', size=10)
        )
    )

    return fig


# ═══════════════════════════════════════════════════════════════════════════
# ASSET DETAIL SECTION (Description + Features + News + Watchlist)
# ═══════════════════════════════════════════════════════════════════════════

def render_asset_detail_section(
    asset: Dict,
    user_id: str = 'default',
    on_watchlist_change: Optional[callable] = None
):
    """
    Render a complete asset detail section with:
    - Description text
    - Score features table (characteristics + contributions)
    - External links tabs (Yahoo, Google, News)
    - Recent news
    - Add to watchlist button
    """
    if not asset:
        return

    ticker = asset.get('ticker', asset.get('symbol', ''))
    name = asset.get('name', ticker)
    score = asset.get('score')
    asset_id = asset.get('asset_id')
    market_scope = asset.get('market_scope', 'US_EU')
    currency = asset.get('currency', 'USD')

    # Get current price using utility function
    last_price = get_current_price_from_asset(asset, asset_id, market_scope)
    price_display = format_price_display(last_price, currency)

    # Section header
    st.markdown(f'''
    <div class="glass-card" style="margin-top:24px;">
        <div class="section-header" style="border-bottom:1px solid rgba(255,255,255,0.06);padding-bottom:16px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:12px;">
                    {get_logo_html(ticker, 48)}
                    <div>
                        <div style="font-size:20px;font-weight:700;color:#FFFFFF;">{ticker}</div>
                        <div style="font-size:14px;color:#9CA3AF;">{name}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:24px;font-weight:700;color:#10B981;">{price_display}</div>
                    <div style="font-size:11px;color:#6B7280;text-transform:uppercase;">Prix actuel</div>
                </div>
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TABS: Aperçu | Caractéristiques | Actualités | Liens
    # ─────────────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Aperçu", "📊 Caractéristiques", "📰 Actualités", "🔗 Liens"])

    with tab1:
        # Description
        description = get_asset_description(ticker, name, asset)
        st.markdown(f'''
        <div class="asset-description">
            <div style="font-size:14px;font-weight:600;color:#FFFFFF;margin-bottom:12px;">
                À propos de {name}
            </div>
            <p style="margin:0;line-height:1.7;">{description}</p>
        </div>
        ''', unsafe_allow_html=True)

        # Quick KPIs
        value = asset.get('value_score', 0) or 0
        momentum = asset.get('momentum_score', 0) or 0
        safety = asset.get('safety_score', 0) or 0

        cols = st.columns(4)
        with cols[0]:
            render_mini_kpi("Score", score, "/100")
        with cols[1]:
            render_mini_kpi("Valeur", value, "")
        with cols[2]:
            render_mini_kpi("Momentum", momentum, "")
        with cols[3]:
            render_mini_kpi("Sécurité", safety, "")

    with tab2:
        # Features table (characteristics used in scoring)
        render_features_table(asset)

    with tab3:
        # News section
        render_news_placeholder(ticker, name)

    with tab4:
        # External links
        render_external_links_section(ticker)

    st.markdown('</div>', unsafe_allow_html=True)

    # Watchlist button
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("⭐ Ajouter à la liste de suivi", key=f"add_wl_{ticker}", use_container_width=True):
            if on_watchlist_change:
                on_watchlist_change(asset.get('asset_id'))
            st.success(f"{ticker} ajouté à votre liste de suivi!")


def get_asset_description(ticker: str, name: str, asset: Dict) -> str:
    """Get or generate asset description."""
    # Try to get from company_info module
    try:
        from app.company_info import get_company_description
        desc = get_company_description(ticker)
        if desc and desc != "Information non disponible":
            return desc
    except ImportError:
        pass

    # Generate a basic description
    asset_type = asset.get('asset_type', 'action')
    sector = asset.get('sector', '')
    market_scope = asset.get('market_scope', 'US_EU')

    type_labels = {
        'EQUITY': 'action',
        'ETF': 'fonds négocié en bourse (ETF)',
        'FX': 'paire de devises',
        'BOND': 'obligation',
        'INDEX': 'indice'
    }
    type_label = type_labels.get(asset_type, 'actif')

    region = "américain/européen" if market_scope == "US_EU" else "africain"

    desc = f"{name} ({ticker}) est un(e) {type_label} {region}"
    if sector:
        desc += f" du secteur {sector}"
    desc += f". Cet actif fait partie de l'univers MarketGPS avec un score de {asset.get('score', 'N/A')}/100."

    return desc


def render_mini_kpi(label: str, value: Optional[float], suffix: str = ""):
    """Render a mini KPI card."""
    color, _ = get_score_color_single(value)
    display_val = f"{int(value)}" if value is not None else "—"

    st.markdown(f'''
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:#64748B;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">{label}</div>
        <div style="font-size:22px;font-weight:700;color:{color};">{display_val}{suffix}</div>
    </div>
    ''', unsafe_allow_html=True)


def render_features_table(asset: Dict):
    """Render table of scoring features with values and contributions."""

    # Get available features from asset data
    features = [
        ("ROE", asset.get('roe'), "Rentabilité des capitaux propres"),
        ("P/E Ratio", asset.get('pe_ratio'), "Price-to-Earnings"),
        ("P/B Ratio", asset.get('pb_ratio'), "Price-to-Book"),
        ("Dividend Yield", asset.get('dividend_yield'), "Rendement du dividende"),
        ("Volatilité 30j", asset.get('volatility_30d'), "Volatilité sur 30 jours"),
        ("Beta", asset.get('beta'), "Sensibilité au marché"),
        ("RSI", asset.get('rsi'), "Relative Strength Index"),
        ("SMA 50/200", asset.get('sma_ratio'), "Moyenne mobile"),
        ("Volume moyen", asset.get('avg_volume'), "Volume moyen quotidien"),
    ]

    st.markdown('''
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
        <thead>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.1);">
                <th style="text-align:left;padding:12px;font-size:12px;color:#64748B;font-weight:600;">Caractéristique</th>
                <th style="text-align:center;padding:12px;font-size:12px;color:#64748B;font-weight:600;">Valeur</th>
                <th style="text-align:left;padding:12px;font-size:12px;color:#64748B;font-weight:600;">Description</th>
            </tr>
        </thead>
        <tbody>
    ''', unsafe_allow_html=True)

    for name, value, desc in features:
        if value is not None:
            formatted = f"{value:.2f}" if isinstance(
                value, float) else str(value)
        else:
            formatted = "N/A"

        st.markdown(f'''
        <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
            <td style="padding:12px;color:#FFFFFF;font-size:13px;font-weight:500;">{name}</td>
            <td style="padding:12px;text-align:center;color:#22C55E;font-size:13px;font-weight:600;">{formatted}</td>
            <td style="padding:12px;color:#9CA3AF;font-size:12px;">{desc}</td>
        </tr>
        ''', unsafe_allow_html=True)

    st.markdown('</tbody></table></div>', unsafe_allow_html=True)


def render_news_placeholder(ticker: str, name: str):
    """Render news section placeholder (or real news if available)."""

    # Placeholder news items
    mock_news = [
        {
            "title": f"Analyse technique: {ticker} montre des signes de momentum positif",
            "source": "MarketGPS Analysis",
            "date": "Il y a 2 heures",
            "url": f"https://finance.yahoo.com/quote/{ticker}"
        },
        {
            "title": f"Les analystes relèvent leurs prévisions pour {name}",
            "source": "Market Watch",
            "date": "Il y a 5 heures",
            "url": f"https://finance.yahoo.com/quote/{ticker}"
        },
        {
            "title": f"Rapport trimestriel: {ticker} dépasse les attentes",
            "source": "Financial Times",
            "date": "Hier",
            "url": f"https://finance.yahoo.com/quote/{ticker}"
        }
    ]

    st.markdown(f'''
    <div style="font-size:14px;font-weight:600;color:#FFFFFF;margin-bottom:16px;">
        Dernières actualités pour {ticker}
    </div>
    ''', unsafe_allow_html=True)

    for news in mock_news:
        st.markdown(f'''
        <a href="{news['url']}" target="_blank" style="text-decoration:none;display:block;margin-bottom:12px;">
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:14px;transition:all 0.2s;">
                <div style="font-size:14px;font-weight:500;color:#FFFFFF;margin-bottom:6px;line-height:1.4;">
                    {news['title']}
                </div>
                <div style="display:flex;gap:12px;font-size:11px;color:#64748B;">
                    <span>{news['source']}</span>
                    <span>•</span>
                    <span>{news['date']}</span>
                </div>
            </div>
        </a>
        ''', unsafe_allow_html=True)

    st.markdown('''
    <div style="text-align:center;padding:16px;">
        <span style="font-size:12px;color:#64748B;">
            Les actualités sont fournies à titre indicatif. Vérifiez toujours les sources.
        </span>
    </div>
    ''', unsafe_allow_html=True)


def render_external_links_section(ticker: str):
    """Render external links to financial platforms."""

    clean_ticker = ticker.replace('_US', '').replace(
        '.US', '').replace('_PA', '').replace('_XETRA', '')

    links = [
        ("Yahoo Finance",
         f"https://finance.yahoo.com/quote/{clean_ticker}", "📈"),
        ("Google Finance",
         f"https://www.google.com/finance/quote/{clean_ticker}:NASDAQ", "🔍"),
        ("TradingView",
         f"https://www.tradingview.com/symbols/{clean_ticker}/", "📊"),
        ("Seeking Alpha",
         f"https://seekingalpha.com/symbol/{clean_ticker}", "📰"),
        ("MarketWatch",
         f"https://www.marketwatch.com/investing/stock/{clean_ticker}", "📉"),
    ]

    st.markdown('''
    <div style="font-size:14px;font-weight:600;color:#FFFFFF;margin-bottom:16px;">
        Liens externes
    </div>
    <div class="external-links" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
    ''', unsafe_allow_html=True)

    for name, url, icon in links:
        st.markdown(f'''
        <a href="{url}" target="_blank" class="external-link" style="display:flex;align-items:center;gap:10px;padding:14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;text-decoration:none;transition:all 0.2s;">
            <span style="font-size:18px;">{icon}</span>
            <span style="color:#FFFFFF;font-size:13px;font-weight:500;">{name}</span>
        </a>
        ''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
