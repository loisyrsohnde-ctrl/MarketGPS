"""
MarketGPS UI Components
Premium 2026 Institutional Design
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from core.compliance import sanitize_text, get_disclaimer
import hashlib
import urllib.parse


# ============================================
# Score Bucket Colors
# ============================================

SCORE_COLORS = {
    "excellent": "#2EA043",
    "very_good": "#3FB950",
    "good": "#D29922",
    "fair": "#F0883E",
    "alert": "#F85149",
    "risk": "#B42318",
    "na": "rgba(255, 255, 255, 0.38)"
}


def get_score_color(score: Optional[float]) -> str:
    """Get color for a score value."""
    if score is None:
        return SCORE_COLORS["na"]
    if score >= 90:
        return SCORE_COLORS["excellent"]
    elif score >= 80:
        return SCORE_COLORS["very_good"]
    elif score >= 65:
        return SCORE_COLORS["good"]
    elif score >= 50:
        return SCORE_COLORS["fair"]
    elif score >= 35:
        return SCORE_COLORS["alert"]
    else:
        return SCORE_COLORS["risk"]


def get_confidence_color(confidence: Optional[float]) -> str:
    """Get color for confidence value."""
    if confidence is None:
        return SCORE_COLORS["na"]
    if confidence >= 70:
        return SCORE_COLORS["excellent"]
    elif confidence >= 50:
        return SCORE_COLORS["good"]
    else:
        return SCORE_COLORS["alert"]


# ============================================
# Logo Utilities
# ============================================

# Company domain mappings for popular tickers
TICKER_DOMAINS = {
    # ============================================
    # US Tech
    # ============================================
    "AAPL": "apple.com",
    "MSFT": "microsoft.com",
    "GOOGL": "google.com",
    "GOOG": "google.com",
    "META": "meta.com",
    "AMZN": "amazon.com",
    "NVDA": "nvidia.com",
    "TSLA": "tesla.com",
    "AMD": "amd.com",
    "INTC": "intel.com",
    "CRM": "salesforce.com",
    "ADBE": "adobe.com",
    "CSCO": "cisco.com",
    "AVGO": "broadcom.com",
    "ACN": "accenture.com",
    # ============================================
    # US Finance
    # ============================================
    "JPM": "jpmorganchase.com",
    "V": "visa.com",
    "MA": "mastercard.com",
    "BAC": "bankofamerica.com",
    "WFC": "wellsfargo.com",
    "GS": "goldmansachs.com",
    "MS": "morganstanley.com",
    "BRK-B": "berkshirehathaway.com",
    "BRK.B": "berkshirehathaway.com",
    # ============================================
    # US Healthcare
    # ============================================
    "UNH": "unitedhealthgroup.com",
    "JNJ": "jnj.com",
    "PFE": "pfizer.com",
    "ABBV": "abbvie.com",
    "MRK": "merck.com",
    "LLY": "lilly.com",
    "TMO": "thermofisher.com",
    "ABT": "abbott.com",
    "DHR": "danaher.com",
    # ============================================
    # US Consumer
    # ============================================
    "WMT": "walmart.com",
    "PG": "pg.com",
    "KO": "coca-cola.com",
    "PEP": "pepsico.com",
    "COST": "costco.com",
    "HD": "homedepot.com",
    "MCD": "mcdonalds.com",
    "NKE": "nike.com",
    "DIS": "disney.com",
    # ============================================
    # US Energy
    # ============================================
    "XOM": "exxonmobil.com",
    "CVX": "chevron.com",
    # ============================================
    # US Telecom
    # ============================================
    "VZ": "verizon.com",
    "T": "att.com",
    # ============================================
    # US Utilities
    # ============================================
    "NEE": "nexteraenergy.com",
    # ============================================
    # ETFs - use provider logos
    # ============================================
    "SPY": "ssga.com",
    "VOO": "vanguard.com",
    "VTI": "vanguard.com",
    "QQQ": "invesco.com",
    "IWM": "ishares.com",
    "VEA": "vanguard.com",
    "VWO": "vanguard.com",
    "EFA": "ishares.com",
    "EEM": "ishares.com",
    "TLT": "ishares.com",
    "IEF": "ishares.com",
    "LQD": "ishares.com",
    "HYG": "ishares.com",
    "GLD": "ssga.com",
    "SLV": "ishares.com",
    "XLF": "ssga.com",
    "XLK": "ssga.com",
    "XLV": "ssga.com",
    "XLE": "ssga.com",
    "XLI": "ssga.com",
    # ============================================
    # FRANCE (Euronext Paris)
    # ============================================
    "MC": "lvmh.com",
    "OR": "loreal.com",
    "SAN": "sanofi.com",
    "AI": "airliquide.com",
    "BNP": "bnpparibas.com",
    "TTE": "totalenergies.com",
    "CAP": "capgemini.com",
    "DG": "vinci.com",
    "CS": "axa.com",
    "ORA": "orange.com",
    # ============================================
    # GERMANY (XETRA)
    # ============================================
    "SAP": "sap.com",
    "SIE": "siemens.com",
    "ALV": "allianz.com",
    "DTE": "telekom.com",
    "BAS": "basf.com",
    "BMW": "bmw.com",
    "ADS": "adidas.com",
    "VOW3": "volkswagen.com",
    "DBK": "db.com",
    # ============================================
    # UK (LSE)
    # ============================================
    "SHEL": "shell.com",
    "AZN": "astrazeneca.com",
    "HSBA": "hsbc.com",
    "ULVR": "unilever.com",
    "BP": "bp.com",
    "GSK": "gsk.com",
    "RIO": "riotinto.com",
    "LLOY": "lloydsbank.com",
    "VOD": "vodafone.com",
    "BARC": "barclays.com",
    # ============================================
    # SOUTH AFRICA (JSE)
    # ============================================
    "NPN": "naspers.com",
    "BTI": "bat.com",
    "AGL": "angloamerican.com",
    "SOL": "sasol.com",
    "SBK": "standardbank.com",
    "FSR": "firstrand.co.za",
    "MTN": "mtn.com",
    "BID": "bidcorp.com",
    "SHP": "shopriteholdings.co.za",
    "DSY": "discovery.co.za",
}


def get_logo_url(ticker: str, size: int = 64) -> str:
    """
    Get logo URL for a ticker.
    Checks local cache first, then falls back to Clearbit API.
    """
    from pathlib import Path
    
    ticker_upper = ticker.upper().replace("_US", "").replace(".", "-")
    
    # Check local cache first
    local_path = Path("data/logos") / f"{ticker_upper}.png"
    if local_path.exists():
        # Return as data URL for embedded display
        import base64
        try:
            with open(local_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
                return f"data:image/png;base64,{logo_data}"
        except Exception:
            pass
    
    # Fallback to Clearbit API
    domain = TICKER_DOMAINS.get(ticker_upper) or TICKER_DOMAINS.get(ticker.upper())
    if domain:
        return f"https://logo.clearbit.com/{domain}?size={size}"
    
    return ""


def get_logo_html(ticker: str, size: int = 40) -> str:
    """
    Get logo HTML - either from URL or placeholder.
    """
    logo_url = get_logo_url(ticker, size)
    initials = ticker[:2].upper() if len(ticker) >= 2 else ticker[0].upper()
    
    # Generate consistent color from ticker
    hash_val = int(hashlib.md5(ticker.encode()).hexdigest()[:6], 16)
    hue = hash_val % 360
    
    if logo_url:
        # Logo with fallback to placeholder
        return f'''<div style="
            width: {size}px;
            height: {size}px;
            min-width: {size}px;
            border-radius: 10px;
            background: linear-gradient(135deg, hsl({hue}, 25%, 18%), hsl({hue}, 25%, 22%));
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
        ">
            <img src="{logo_url}" 
                 alt="{ticker}" 
                 style="width: 100%; height: 100%; object-fit: contain; padding: 4px;"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
            />
            <span style="display: none; font-size: {size//3}px; font-weight: 600; color: rgba(255, 255, 255, 0.78);">{initials}</span>
        </div>'''
    else:
        # Placeholder with initials
        return f'''<div style="
            width: {size}px;
            height: {size}px;
            min-width: {size}px;
            border-radius: 10px;
            background: linear-gradient(135deg, hsl({hue}, 25%, 18%), hsl({hue}, 25%, 22%));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: {size//3}px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(255, 255, 255, 0.08);
        ">{initials}</div>'''


# ============================================
# Asset Card Component
# ============================================

def render_asset_card_html(
    ticker: str,
    name: str,
    asset_type: str,
    score: Optional[float],
    confidence: Optional[float],
    is_selected: bool = False
) -> str:
    """
    Render asset card HTML with inline styles and logo.
    Uses SINGLE color for score bar (no gradient).
    """
    safe_name = sanitize_text(name or ticker)[:35]  # Truncate long names
    safe_ticker = sanitize_text(ticker)
    
    # Get colors
    score_color = get_score_color(score)
    conf_color = get_confidence_color(confidence)
    
    # Calculate values
    score_width = min(100, max(0, float(score))) if score is not None else 0
    score_val = f"{int(score)}" if score is not None else "—"
    conf_val = f"{int(confidence)}%" if confidence is not None else "—"
    
    # Logo HTML
    logo_html = get_logo_html(ticker, 40)
    
    # Badge
    badge_class = "Action" if asset_type == "EQUITY" else asset_type
    badge_bg = "rgba(88, 166, 255, 0.15)" if asset_type == "EQUITY" else "rgba(46, 160, 67, 0.15)"
    badge_color = "#58A6FF" if asset_type == "EQUITY" else "#2EA043"
    
    # Card styling
    border_color = "#2EA043" if is_selected else "rgba(255, 255, 255, 0.08)"
    bg_color = "#1A2332" if is_selected else "#141B27"
    
    return f'''<div style="
        background: {bg_color};
        border: {"2px" if is_selected else "1px"} solid {border_color};
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 8px;
    ">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            {logo_html}
            <div style="flex: 1; min-width: 0; overflow: hidden;">
                <p style="
                    font-size: 15px;
                    font-weight: 600;
                    color: #FFFFFF;
                    margin: 0;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                ">{safe_name}</p>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                    <span style="font-size: 13px; color: rgba(255, 255, 255, 0.78);">{safe_ticker}</span>
                    <span style="
                        display: inline-flex;
                        padding: 2px 8px;
                        border-radius: 999px;
                        font-size: 10px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        background: {badge_bg};
                        color: {badge_color};
                    ">{badge_class}</span>
                </div>
            </div>
        </div>
        <div style="margin-top: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 11px; color: rgba(255, 255, 255, 0.56); text-transform: uppercase; letter-spacing: 0.5px;">Score</span>
                <span style="font-size: 18px; font-weight: 700; color: {score_color};">{score_val}</span>
            </div>
            <div style="height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; overflow: hidden;">
                <div style="height: 100%; width: {score_width}%; background: {score_color}; border-radius: 999px;"></div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 11px; color: rgba(255, 255, 255, 0.56);">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: {conf_color};"></span>
            <span>Confiance: {conf_val}</span>
        </div>
    </div>'''


def render_asset_card(
    ticker: str,
    name: str,
    asset_type: str,
    score: Optional[float],
    confidence: Optional[float],
    is_selected: bool,
    key: str
) -> bool:
    """
    Render an interactive asset card.
    Returns True if card was clicked.
    """
    card_html = render_asset_card_html(
        ticker=ticker,
        name=name,
        asset_type=asset_type,
        score=score,
        confidence=confidence,
        is_selected=is_selected
    )
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    button_label = "Sélectionné" if is_selected else "Sélectionner"
    return st.button(
        button_label,
        key=key,
        type="primary" if is_selected else "secondary",
        use_container_width=True
    )


# ============================================
# Detail Panel Components
# ============================================

def render_detail_header(
    ticker: str,
    name: str,
    asset_type: str,
    score: Optional[float],
    confidence: Optional[float]
) -> None:
    """Render detail panel header with logo."""
    safe_name = sanitize_text(name or ticker)
    safe_ticker = sanitize_text(ticker)
    score_color = get_score_color(score)
    score_val = "—" if score is None else f"{int(score)}"
    
    # Logo HTML (larger for detail panel)
    logo_html = get_logo_html(ticker, 56)
    
    # Badge
    badge_bg = "rgba(88, 166, 255, 0.15)" if asset_type == "EQUITY" else "rgba(46, 160, 67, 0.15)"
    badge_color = "#58A6FF" if asset_type == "EQUITY" else "#2EA043"
    badge_label = "Action" if asset_type == "EQUITY" else asset_type
    
    html = f'''<div style="display: flex; align-items: flex-start; gap: 16px; margin-bottom: 24px;">
        {logo_html}
        <div style="flex: 1; min-width: 0;">
            <h2 style="margin: 0 0 4px 0; font-size: 20px; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{safe_name}</h2>
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: rgba(255, 255, 255, 0.78);">{safe_ticker}</span>
                <span style="
                    display: inline-flex;
                    padding: 2px 8px;
                    border-radius: 999px;
                    font-size: 10px;
                    font-weight: 600;
                    text-transform: uppercase;
                    background: {badge_bg};
                    color: {badge_color};
                ">{badge_label}</span>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 28px; font-weight: 700; color: {score_color};">{score_val}</div>
            <div style="font-size: 12px; color: rgba(255, 255, 255, 0.56);">/100</div>
        </div>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)


def render_pillar_card(
    title: str,
    score: Optional[float],
    metrics: List[Dict[str, Any]]
) -> None:
    """Render a scoring pillar card."""
    score_color = get_score_color(score)
    score_val = "—" if score is None else f"{int(score)}"
    width = 0 if score is None else min(100, max(0, float(score)))
    
    # Build metrics HTML
    metrics_html = ""
    for m in metrics:
        value = m.get("value", "—")
        label = sanitize_text(m.get("label", ""))
        metrics_html += f'''<div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
            <span style="color: rgba(255, 255, 255, 0.78); font-size: 13px;">{label}</span>
            <span style="color: #FFFFFF; font-weight: 500;">{value}</span>
        </div>'''
    
    html = f'''<div style="background: #1A2332; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 16px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-weight: 600; color: #FFFFFF;">{sanitize_text(title)}</span>
            <span style="font-size: 18px; font-weight: 700; color: {score_color};">{score_val}</span>
        </div>
        <div style="height: 6px; background: rgba(255,255,255,0.08); border-radius: 999px; overflow: hidden;">
            <div style="height: 100%; width: {width}%; background: {score_color}; border-radius: 999px;"></div>
        </div>
        <div style="margin-top: 12px;">{metrics_html}</div>
    </div>'''
    st.markdown(html, unsafe_allow_html=True)


def render_external_links(ticker: str) -> None:
    """Render external links."""
    st.markdown(f'''<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px;">
        <a href="https://finance.yahoo.com/quote/{ticker}" target="_blank" rel="noopener" 
           style="padding: 8px 12px; background: #1A2332; border: 1px solid rgba(255, 255, 255, 0.08); 
                  border-radius: 12px; color: rgba(255, 255, 255, 0.78); text-decoration: none; 
                  font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
            Yahoo Finance
        </a>
        <a href="https://www.google.com/finance/quote/{ticker}" target="_blank" rel="noopener"
           style="padding: 8px 12px; background: #1A2332; border: 1px solid rgba(255, 255, 255, 0.08); 
                  border-radius: 12px; color: rgba(255, 255, 255, 0.78); text-decoration: none; 
                  font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
            Google Finance
        </a>
        <a href="https://www.tradingview.com/symbols/{ticker}" target="_blank" rel="noopener"
           style="padding: 8px 12px; background: #1A2332; border: 1px solid rgba(255, 255, 255, 0.08); 
                  border-radius: 12px; color: rgba(255, 255, 255, 0.78); text-decoration: none; 
                  font-size: 12px; display: inline-flex; align-items: center; gap: 6px;">
            TradingView
        </a>
    </div>''', unsafe_allow_html=True)


# ============================================
# Footer
# ============================================

def render_footer() -> str:
    """Render compliance footer."""
    disclaimer = get_disclaimer()
    return f'''<div style="
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #0F1623;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding: 10px 24px;
        font-size: 11px;
        color: rgba(255, 255, 255, 0.38);
        text-align: center;
        z-index: 100;
    ">{sanitize_text(disclaimer)}</div>'''


# ============================================
# Helper Components
# ============================================

def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    """Render a section header."""
    html = f'''<div style="margin: 24px 0 16px 0;">
        <h3 style="margin: 0; font-size: 16px; font-weight: 600; color: #FFFFFF;">{sanitize_text(title)}</h3>
        {f'<p style="margin: 4px 0 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.56);">{sanitize_text(subtitle)}</p>' if subtitle else ''}
    </div>'''
    st.markdown(html, unsafe_allow_html=True)


def render_empty_state(message: str = "Aucune donnée disponible") -> None:
    """Render an empty state message."""
    st.markdown(f'''<div style="text-align: center; padding: 48px 24px; color: rgba(255, 255, 255, 0.38);">
        <div style="font-size: 48px; margin-bottom: 16px;">—</div>
        <p style="margin: 0; font-size: 14px;">{sanitize_text(message)}</p>
    </div>''', unsafe_allow_html=True)


def render_loading_state() -> None:
    """Render a loading skeleton."""
    st.markdown('''<div style="padding: 24px; animation: pulse 1.5s ease-in-out infinite;">
        <div style="height: 20px; background: #1E2A3B; border-radius: 4px; margin-bottom: 12px; width: 60%;"></div>
        <div style="height: 14px; background: #1E2A3B; border-radius: 4px; margin-bottom: 8px; width: 80%;"></div>
        <div style="height: 8px; background: #1E2A3B; border-radius: 4px; width: 100%;"></div>
    </div>
    <style>@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }</style>''', unsafe_allow_html=True)


def render_metric(label: str, value: Any, delta: Optional[str] = None) -> None:
    """Render a metric with optional delta."""
    delta_color = "#2EA043" if delta and not delta.startswith("-") else "#F85149"
    delta_html = f'<span style="color: {delta_color}; font-size: 12px; margin-left: 8px;">{delta}</span>' if delta else ''
    
    st.markdown(f'''<div style="padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
        <div style="font-size: 12px; color: rgba(255, 255, 255, 0.56); margin-bottom: 4px;">{sanitize_text(label)}</div>
        <div style="font-size: 20px; font-weight: 600; color: #FFFFFF;">{value}{delta_html}</div>
    </div>''', unsafe_allow_html=True)


# ============================================
# Deprecated/Legacy exports for compatibility
# ============================================

def render_badge(asset_type: str) -> str:
    """Render an asset type badge (legacy)."""
    badge_bg = "rgba(88, 166, 255, 0.15)" if asset_type == "EQUITY" else "rgba(46, 160, 67, 0.15)"
    badge_color = "#58A6FF" if asset_type == "EQUITY" else "#2EA043"
    label = "Action" if asset_type == "EQUITY" else asset_type
    return f'<span style="display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: {badge_bg}; color: {badge_color};">{label}</span>'


def render_score_bar(score: Optional[float], label: str = "Score") -> str:
    """Render a score bar (legacy)."""
    score_color = get_score_color(score)
    width = min(100, max(0, float(score))) if score is not None else 0
    value = f"{int(score)}" if score is not None else "—"
    return f'''<div style="margin-top: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-size: 11px; color: rgba(255, 255, 255, 0.56); text-transform: uppercase;">{label}</span>
            <span style="font-size: 18px; font-weight: 700; color: {score_color};">{value}</span>
        </div>
        <div style="height: 8px; background: rgba(255, 255, 255, 0.08); border-radius: 999px; overflow: hidden;">
            <div style="height: 100%; width: {width}%; background: {score_color}; border-radius: 999px;"></div>
        </div>
    </div>'''


def render_confidence(confidence: Optional[float]) -> str:
    """Render confidence indicator (legacy)."""
    conf_color = get_confidence_color(confidence)
    conf_val = f"{int(confidence)}%" if confidence is not None else "—"
    return f'''<div style="display: flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 11px; color: rgba(255, 255, 255, 0.56);">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: {conf_color};"></span>
        <span>Confiance: {conf_val}</span>
    </div>'''


def get_logo_placeholder(ticker: str) -> str:
    """Get logo placeholder HTML (legacy)."""
    return get_logo_html(ticker, 40)
