"""
MarketGPS v12.0 - Premium Landing Page Module
Institutional-grade SaaS landing page with glassmorphism design.
"""
import streamlit as st
import base64
from pathlib import Path
from typing import Dict, Optional

from core.config import get_config


def load_image_base64(image_path: str) -> Optional[str]:
    """Load image and convert to base64 for CSS embedding."""
    path = Path(image_path)
    if path.exists():
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception:
            return None
    return None


def get_landing_css(world_map_b64: Optional[str] = None, market_bg_b64: Optional[str] = None) -> str:
    """Generate landing page CSS with optional background images."""
    
    # Hero background - world map with green glow points
    if market_bg_b64:
        hero_bg = f"""
            background-image: 
                linear-gradient(to bottom, rgba(8, 12, 16, 0.4) 0%, rgba(8, 12, 16, 0.6) 40%, rgba(8, 12, 16, 0.85) 100%),
                url('data:image/png;base64,{market_bg_b64}');
            background-size: cover;
            background-position: center top;
            background-repeat: no-repeat;
        """
    else:
        hero_bg = """
            background: linear-gradient(135deg, rgba(10, 10, 10, 0.98) 0%, rgba(10, 20, 30, 0.95) 50%, rgba(16, 185, 129, 0.12) 100%);
        """
    
    # Markets section background
    if world_map_b64:
        # Reuse hero image for markets section with different overlay
        markets_bg = f"""
            background-image: 
                linear-gradient(180deg, rgba(8, 12, 16, 0.92) 0%, rgba(10, 14, 20, 0.95) 100%),
                url('data:image/png;base64,{market_bg_b64}');
            background-size: cover;
            background-position: center;
        """
    elif world_map_b64:
        markets_bg = f"""
            background-image: 
                linear-gradient(180deg, rgba(10, 10, 10, 0.88) 0%, rgba(12, 18, 26, 0.92) 100%),
                url('data:image/png;base64,{world_map_b64}');
            background-size: cover;
            background-position: center;
        """
    else:
        markets_bg = """
            background: linear-gradient(180deg, rgba(10, 10, 10, 0.95) 0%, rgba(16, 24, 36, 0.92) 100%);
        """
    
    return f'''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        --bg-dark: #0A0A0A;
        --bg-card: rgba(18, 18, 18, 0.92);
        --bg-elevated: rgba(26, 26, 26, 0.95);
        --green: #10B981;
        --green-glow: rgba(16, 185, 129, 0.35);
        --green-dark: #059669;
        --yellow: #F59E0B;
        --red: #EF4444;
        --text-primary: #FFFFFF;
        --text-secondary: #E5E7EB;
        --text-muted: #9CA3AF;
        --text-dim: #6B7280;
        --border: rgba(255, 255, 255, 0.08);
        --border-green: rgba(16, 185, 129, 0.3);
    }}
    
    /* Global link reset for landing page */
    .landing-navbar a,
    .landing-hero a,
    .landing-footer a {{
        text-decoration: none !important;
        border-bottom: none !important;
    }}
    
    /* Landing Navbar */
    .landing-navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 32px;
        background: rgba(10, 10, 10, 0.85);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid var(--border);
        position: sticky;
        top: 0;
        z-index: 1000;
        gap: 24px;
        flex-wrap: nowrap;
    }}
    .landing-logo {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-shrink: 0;
    }}
    .landing-logo-icon {{
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--green), var(--green-dark));
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        color: white;
        box-shadow: 0 4px 20px var(--green-glow);
    }}
    .landing-logo-text {{
        font-size: 22px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }}
    .landing-nav-links {{
        display: flex;
        gap: 24px;
        flex: 1;
        justify-content: center;
    }}
    .landing-nav-link {{
        font-size: 14px;
        font-weight: 500;
        color: var(--text-muted);
        text-decoration: none !important;
        transition: color 0.2s;
        cursor: pointer;
        border-bottom: none !important;
    }}
    .landing-nav-link:hover {{
        color: var(--text-primary);
        text-decoration: none !important;
    }}
    .landing-nav-link:visited,
    .landing-nav-link:active,
    .landing-nav-link:focus {{
        text-decoration: none !important;
        color: var(--text-muted);
    }}
    .landing-nav-buttons {{
        display: flex;
        gap: 12px;
        align-items: center;
    }}
    
    /* Navbar HTML buttons */
    .nav-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 9px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
    }}
    .nav-btn-secondary {{
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: var(--text-secondary);
    }}
    .nav-btn-secondary:hover {{
        background: rgba(255, 255, 255, 0.1);
        color: var(--text-primary);
    }}
    .nav-btn-primary {{
        background: linear-gradient(135deg, var(--green), var(--green-dark));
        border: none;
        color: white;
        box-shadow: 0 4px 16px var(--green-glow);
    }}
    .nav-btn-primary:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 24px var(--green-glow);
    }}
    
    /* Hide Streamlit default padding */
    section[data-testid="stMain"] {{
        padding-top: 0 !important;
    }}
    
    /* Hero Section */
    .landing-hero {{
        {hero_bg}
        min-height: 85vh;
        padding: 80px 48px;
        display: flex;
        align-items: center;
        position: relative;
        overflow: hidden;
    }}
    .landing-hero::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at 80% 50%, rgba(16, 185, 129, 0.08) 0%, transparent 60%);
        pointer-events: none;
    }}
    .landing-hero::after {{
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 200px;
        background: linear-gradient(to top, var(--bg-dark), transparent);
        pointer-events: none;
    }}
    .hero-content {{
        flex: 1.2;
        max-width: 640px;
        z-index: 10;
    }}
    .hero-title {{
        font-size: 56px;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.08;
        margin-bottom: 28px;
        letter-spacing: -1.5px;
    }}
    .hero-title span {{
        color: var(--green);
    }}
    .hero-subtitle {{
        font-size: 19px;
        color: var(--text-muted);
        line-height: 1.7;
        margin-bottom: 44px;
        max-width: 520px;
    }}
    .hero-buttons {{
        display: flex;
        gap: 16px;
    }}
    .hero-card-container {{
        flex: 1;
        display: flex;
        justify-content: center;
        z-index: 10;
    }}
    
    /* Score Card */
    .score-card {{
        background: var(--bg-card);
        backdrop-filter: blur(24px);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 36px;
        width: 380px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4), 0 0 60px rgba(16, 185, 129, 0.08);
        transition: transform 0.3s, box-shadow 0.3s;
    }}
    .score-card:hover {{
        transform: translateY(-6px);
        box-shadow: 0 16px 60px rgba(0, 0, 0, 0.5), 0 0 80px rgba(16, 185, 129, 0.12);
    }}
    .score-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 28px;
    }}
    .score-card-ticker {{
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
    }}
    .score-card-name {{
        font-size: 14px;
        color: var(--text-muted);
    }}
    .score-gauge {{
        text-align: center;
        margin: 32px 0;
    }}
    .score-gauge svg {{
        width: 160px;
        height: 90px;
    }}
    .score-value {{
        font-size: 52px;
        font-weight: 800;
        color: var(--text-primary);
        margin-top: -24px;
    }}
    .score-value span {{
        font-size: 22px;
        color: var(--text-muted);
        font-weight: 500;
    }}
    
    /* Pillar Bars */
    .pillar-row {{
        display: flex;
        align-items: center;
        margin-bottom: 16px;
    }}
    .pillar-label {{
        width: 100px;
        font-size: 14px;
        color: var(--text-secondary);
        font-weight: 500;
    }}
    .pillar-bar {{
        flex: 1;
        height: 10px;
        background: rgba(255, 255, 255, 0.08);
        border-radius: 5px;
        overflow: hidden;
        margin: 0 16px;
    }}
    .pillar-fill {{
        height: 100%;
        background: linear-gradient(90deg, var(--green), var(--green-dark));
        border-radius: 5px;
        box-shadow: 0 0 12px var(--green-glow);
        transition: width 0.6s ease-out;
    }}
    .pillar-value {{
        width: 36px;
        text-align: right;
        font-size: 15px;
        font-weight: 600;
        color: var(--text-primary);
    }}
    
    /* Badges */
    .score-badges {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 24px;
    }}
    .score-badge {{
        padding: 8px 14px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 8px;
        font-size: 12px;
        font-weight: 500;
        color: var(--green);
    }}
    .score-badge.warning {{
        background: rgba(245, 158, 11, 0.12);
        border-color: rgba(245, 158, 11, 0.25);
        color: var(--yellow);
    }}
    
    /* Markets Section */
    .landing-markets {{
        {markets_bg}
        padding: 80px 48px;
        text-align: center;
        position: relative;
    }}
    .landing-markets::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%);
        pointer-events: none;
    }}
    .section-title {{
        font-size: 32px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 40px;
        position: relative;
    }}
    .market-pills {{
        display: flex;
        justify-content: center;
        gap: 14px;
        flex-wrap: wrap;
        position: relative;
    }}
    .market-pill {{
        padding: 14px 24px;
        background: rgba(30, 35, 45, 0.9);
        border: 1px solid var(--border);
        border-radius: 30px;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-secondary);
        transition: all 0.25s;
        cursor: pointer;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }}
    .market-pill:hover {{
        background: rgba(16, 185, 129, 0.15);
        border-color: var(--border-green);
        color: var(--green);
        transform: translateY(-3px);
        box-shadow: 0 6px 24px rgba(16, 185, 129, 0.2);
    }}
    
    /* Pricing Section */
    .landing-pricing {{
        padding: 100px 48px;
        background: var(--bg-dark);
    }}
    .pricing-grid {{
        display: flex;
        justify-content: center;
        gap: 32px;
        max-width: 900px;
        margin: 0 auto;
    }}
    .pricing-card {{
        flex: 1;
        max-width: 380px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 40px;
        text-align: center;
        transition: all 0.3s;
        position: relative;
    }}
    .pricing-card:hover {{
        border-color: var(--border-green);
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(16, 185, 129, 0.15);
    }}
    .pricing-card.featured {{
        border: 2px solid var(--green);
        box-shadow: 0 0 40px rgba(16, 185, 129, 0.2);
    }}
    .pricing-badge {{
        position: absolute;
        top: -14px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, var(--green), var(--green-dark));
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 16px var(--green-glow);
    }}
    .pricing-name {{
        font-size: 22px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
    }}
    .pricing-price {{
        font-size: 48px;
        font-weight: 800;
        color: var(--text-primary);
        margin-bottom: 8px;
    }}
    .pricing-price span {{
        font-size: 18px;
        color: var(--text-muted);
        font-weight: 500;
    }}
    .pricing-features {{
        list-style: none;
        padding: 0;
        margin: 32px 0;
        text-align: left;
    }}
    .pricing-features li {{
        padding: 12px 0;
        color: var(--text-secondary);
        font-size: 14px;
        border-bottom: 1px solid var(--border);
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .pricing-features li:last-child {{
        border-bottom: none;
    }}
    .pricing-features li::before {{
        content: '✓';
        color: var(--green);
        font-weight: 600;
    }}
    .pricing-features li.highlight {{
        color: var(--green);
        font-weight: 600;
    }}
    
    /* Buttons */
    .btn-primary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 16px 32px;
        background: linear-gradient(135deg, var(--green), var(--green-dark));
        color: white;
        font-size: 15px;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        transition: all 0.25s;
        box-shadow: 0 4px 20px var(--green-glow);
        text-decoration: none;
    }}
    .btn-primary:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 30px var(--green-glow);
    }}
    .btn-secondary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 16px 32px;
        background: transparent;
        color: var(--text-secondary);
        font-size: 15px;
        font-weight: 500;
        border-radius: 12px;
        border: 1px solid var(--border);
        cursor: pointer;
        transition: all 0.25s;
        text-decoration: none;
    }}
    .btn-secondary:hover {{
        background: rgba(255, 255, 255, 0.05);
        border-color: var(--text-muted);
        color: var(--text-primary);
    }}
    
    /* Footer */
    .landing-footer {{
        padding: 32px 48px;
        background: rgba(8, 8, 8, 0.98);
        border-top: 1px solid var(--border);
        text-align: center;
    }}
    .footer-disclaimer {{
        font-size: 12px;
        color: var(--text-dim);
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.6;
    }}
    
    /* Responsive */
    @media (max-width: 1024px) {{
        .landing-hero {{
            flex-direction: column;
            padding: 60px 24px;
            text-align: center;
        }}
        .hero-content {{
            max-width: 100%;
        }}
        .hero-title {{
            font-size: 40px;
        }}
        .hero-buttons {{
            justify-content: center;
        }}
        .hero-card-container {{
            margin-top: 48px;
        }}
        .pricing-grid {{
            flex-direction: column;
            align-items: center;
        }}
    }}
    </style>
    '''


def render_landing_navbar() -> str:
    """Render the landing page navbar HTML with working anchor links."""
    return '<div class="landing-navbar"><div class="landing-logo"><div class="landing-logo-icon">◉</div><span class="landing-logo-text">MarketGPS</span></div><div class="landing-nav-links"><a href="#markets-section" class="landing-nav-link">Marchés</a><a href="#pricing-section" class="landing-nav-link">Tarifs</a><a href="#security-section" class="landing-nav-link">Sécurité</a><a href="#footer-section" class="landing-nav-link">Support</a></div><div class="landing-nav-buttons"></div></div>'


def render_score_card(metrics: Dict) -> str:
    """Render the score card with real data from DB."""
    top_asset = metrics.get("top_asset")
    
    if top_asset:
        ticker = top_asset.get("symbol", "AAPL")
        name = top_asset.get("name", "Apple Inc.")[:25]
        score = int(top_asset.get("score_total", 0) or 0)
        value_score = int(top_asset.get("score_value", 0) or 0)
        momentum_score = int(top_asset.get("score_momentum", 0) or 0)
        safety_score = int(top_asset.get("score_safety", 0) or 0)
        coverage = float(top_asset.get("coverage", 0) or 0)
        liquidity = float(top_asset.get("liquidity", 0) or 0)
        fx_risk = float(top_asset.get("fx_risk", 0) or 0)
    else:
        # Fallback / demo data
        ticker, name, score = "—", "Données en cours de synchronisation", 0
        value_score, momentum_score, safety_score = 0, 0, 0
        coverage, liquidity, fx_risk = 0, 0, 0
    
    # Determine gauge color
    gauge_color = "#10B981" if score >= 60 else "#F59E0B" if score >= 40 else "#EF4444"
    
    # Display values
    score_display = str(score) if score > 0 else "—"
    value_display = str(value_score) if value_score > 0 else "—"
    momentum_display = str(momentum_score) if momentum_score > 0 else "—"
    safety_display = str(safety_score) if safety_score > 0 else "—"
    
    # Badges based on real data
    badges_html = ""
    if coverage > 0.9:
        badges_html += '<span class="score-badge">Données OK</span>'
    elif coverage > 0:
        badges_html += '<span class="score-badge warning">Données partielles</span>'
    
    if liquidity > 100000:
        badges_html += '<span class="score-badge">Liquidité</span>'
    elif liquidity > 0:
        badges_html += '<span class="score-badge warning">Liquidité faible</span>'
    
    if fx_risk < 0.3:
        badges_html += '<span class="score-badge">Devise stable</span>'
    elif fx_risk > 0:
        badges_html += '<span class="score-badge warning">Risque FX</span>'
    
    if not badges_html and score == 0:
        badges_html = '<span class="score-badge warning">Synchronisation en cours...</span>'
    
    # Build HTML without indentation to avoid Streamlit code block detection
    html = f'<div class="score-card">'
    html += f'<div class="score-card-header"><span class="score-card-ticker">{ticker}</span><span class="score-card-name">— {name}</span></div>'
    
    # Score gauge section
    html += f'<div style="text-align:center;margin:32px 0;">'
    html += f'<div style="font-size:64px;font-weight:800;color:{gauge_color};">{score_display}</div>'
    html += f'<div style="font-size:18px;color:#9CA3AF;margin-top:-8px;">/100</div>'
    html += f'<div style="width:120px;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;margin:16px auto 0;">'
    html += f'<div style="width:{score}%;height:100%;background:{gauge_color};border-radius:3px;"></div>'
    html += f'</div></div>'
    
    # Pillar bars
    html += f'<div style="margin-top:28px;">'
    html += f'<div class="pillar-row"><span class="pillar-label">Valeur</span><div class="pillar-bar"><div class="pillar-fill" style="width:{value_score}%;"></div></div><span class="pillar-value">{value_display}</span></div>'
    html += f'<div class="pillar-row"><span class="pillar-label">Momentum</span><div class="pillar-bar"><div class="pillar-fill" style="width:{momentum_score}%;"></div></div><span class="pillar-value">{momentum_display}</span></div>'
    html += f'<div class="pillar-row"><span class="pillar-label">Sécurité</span><div class="pillar-bar"><div class="pillar-fill" style="width:{safety_score}%;"></div></div><span class="pillar-value">{safety_display}</span></div>'
    html += f'</div>'
    
    # Badges
    html += f'<div class="score-badges">{badges_html}</div>'
    html += f'</div>'
    
    return html


def render_hero_section(metrics: Dict) -> str:
    """Render the hero section HTML."""
    score_card = render_score_card(metrics)
    
    # Build HTML without deep indentation to avoid Streamlit interpreting as code
    html = '<div class="landing-hero">'
    html += '<div class="hero-content">'
    html += '<h1 class="hero-title">Le score <span>/100</span> qui rend<br>les marchés lisibles.</h1>'
    html += '<p class="hero-subtitle">Des notes claires. Des explications simples.<br>Des données de niveau institutionnel — sans bruit.</p>'
    html += '<div class="hero-buttons" id="hero-cta-buttons"></div>'
    html += '</div>'
    html += f'<div class="hero-card-container">{score_card}</div>'
    html += '</div>'
    
    return html


def render_markets_section() -> str:
    """Render the markets covered section."""
    markets = [
        ("🇺🇸", "USA"),
        ("🇪🇺", "Europe"),
        ("🌍", "Afrique"),
        ("📊", "ETF"),
        ("📈", "Actions"),
        ("💱", "FX"),
        ("📄", "Obligations"),
    ]
    
    pills_html = "".join([
        f'<div class="market-pill">{emoji} {name}</div>'
        for emoji, name in markets
    ])
    
    return f'<div class="landing-markets" id="section-markets"><h2 class="section-title">Marchés couverts</h2><div class="market-pills">{pills_html}</div></div>'


def render_pricing_section() -> str:
    """Render the pricing section."""
    html = '<div class="landing-pricing" id="section-pricing">'
    html += '<h2 class="section-title" style="text-align:center;margin-bottom:60px;">Tarifs</h2>'
    html += '<div class="pricing-grid">'
    
    # Monthly plan
    html += '<div class="pricing-card" id="pricing-monthly">'
    html += '<h3 class="pricing-name">Mensuel</h3>'
    html += '<div class="pricing-price">9,99 €<span>/mois</span></div>'
    html += '<ul class="pricing-features">'
    html += '<li>200 calculs/jour</li>'
    html += '<li>Tous les marchés</li>'
    html += '<li>Alertes personnalisées</li>'
    html += '<li>Historique complet</li>'
    html += '</ul>'
    html += '<div id="btn-subscribe-monthly"></div>'
    html += '</div>'
    
    # Yearly plan
    html += '<div class="pricing-card featured" id="pricing-yearly">'
    html += '<div class="pricing-badge">Meilleure offre</div>'
    html += '<h3 class="pricing-name">Annuel</h3>'
    html += '<div class="pricing-price">50 €<span>/an</span></div>'
    html += '<ul class="pricing-features">'
    html += '<li>200 calculs/jour</li>'
    html += '<li>Tous les marchés</li>'
    html += '<li>Alertes personnalisées</li>'
    html += '<li>Historique complet</li>'
    html += '<li>Support prioritaire</li>'
    html += '<li class="highlight">Économisez 58%</li>'
    html += '</ul>'
    html += '<div id="btn-subscribe-yearly"></div>'
    html += '</div>'
    
    html += '</div></div>'
    return html


def render_footer() -> str:
    """Render the footer with contact info, links and disclaimer."""
    footer_html = '<div class="landing-footer" id="footer-section" style="padding: 60px 48px 40px; background: #0A0A0A; border-top: 1px solid rgba(255,255,255,0.08);">'
    footer_html += '<div style="max-width: 1200px; margin: 0 auto;">'
    # Grid container
    footer_html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 48px; margin-bottom: 48px;">'
    # Logo column
    footer_html += '<div><div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="width: 36px; height: 36px; background: linear-gradient(135deg, #10B981, #059669); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-size: 16px;">◉</div><span style="font-size: 20px; font-weight: 700; color: #fff;">MarketGPS</span></div><p style="color: #9CA3AF; font-size: 14px; line-height: 1.7; max-width: 280px; margin: 0;">Plateforme d\'analyse financière institutionnelle. Scores quantitatifs, données en temps réel.</p><div style="display: flex; gap: 12px; margin-top: 20px;"><a href="https://twitter.com" target="_blank" style="width: 36px; height: 36px; background: rgba(255,255,255,0.06); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9CA3AF; text-decoration: none;">𝕏</a><a href="https://linkedin.com" target="_blank" style="width: 36px; height: 36px; background: rgba(255,255,255,0.06); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #9CA3AF; text-decoration: none;">in</a></div></div>'
    # Product column
    footer_html += '<div><h4 style="color: #fff; font-size: 14px; font-weight: 600; margin: 0 0 20px; text-transform: uppercase; letter-spacing: 0.5px;">Produit</h4><a href="#markets-section" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Marchés couverts</a><a href="#pricing-section" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Tarifs</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Documentation API</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Changelog</a></div>'
    # Support column
    footer_html += '<div><h4 style="color: #fff; font-size: 14px; font-weight: 600; margin: 0 0 20px; text-transform: uppercase; letter-spacing: 0.5px;">Support</h4><a href="mailto:support@marketgps.io" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">support@marketgps.io</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Centre d\'aide</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">FAQ</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Statut services</a></div>'
    # Legal column
    footer_html += '<div><h4 style="color: #fff; font-size: 14px; font-weight: 600; margin: 0 0 20px; text-transform: uppercase; letter-spacing: 0.5px;">Légal</h4><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Conditions d\'utilisation</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Politique de confidentialité</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Mentions légales</a><a href="#" style="display: block; color: #9CA3AF; font-size: 14px; margin-bottom: 12px; text-decoration: none;">Cookies</a></div>'
    footer_html += '</div>'
    # Bottom bar
    footer_html += '<div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;"><p style="color: #6B7280; font-size: 13px; margin: 0;">© 2026 MarketGPS. Tous droits réservés.</p><p style="color: #6B7280; font-size: 12px; margin: 0; max-width: 600px; text-align: right;">Outil d\'analyse statistique et éducatif. Capital à risque. Les performances passées ne garantissent pas le futur.</p></div>'
    footer_html += '</div></div>'
    return footer_html


def render_full_landing_page(metrics: Dict) -> None:
    """Render the complete landing page in Streamlit."""
    config = get_config()
    
    # Try to load background images
    landing_dir = config.storage.data_dir.parent / "assets" / "landing"
    world_map_b64 = load_image_base64(str(landing_dir / "world_map.png"))
    market_bg_b64 = load_image_base64(str(landing_dir / "market_bg.png"))
    
    # Inject CSS
    st.markdown(get_landing_css(world_map_b64, market_bg_b64), unsafe_allow_html=True)
    
    # Render navbar with buttons inside HTML (using URL params for navigation)
    navbar_html = '''
    <div class="landing-navbar">
        <div class="landing-logo">
            <div class="landing-logo-icon">◉</div>
            <span class="landing-logo-text">MarketGPS</span>
        </div>
        <div class="landing-nav-links">
            <a href="#markets-section" class="landing-nav-link">Marchés</a>
            <a href="#pricing-section" class="landing-nav-link">Tarifs</a>
            <a href="#footer-section" class="landing-nav-link">Support</a>
        </div>
        <div class="landing-nav-buttons">
            <a href="?view=login" class="nav-btn nav-btn-secondary">Connexion</a>
            <a href="?view=signup" class="nav-btn nav-btn-primary">S'inscrire</a>
        </div>
    </div>
    '''
    st.markdown(navbar_html, unsafe_allow_html=True)
    
    # Check URL params for view changes
    query_params = st.query_params
    if "view" in query_params:
        requested_view = query_params.get("view")
        if requested_view in ["login", "signup", "dashboard"]:
            st.session_state.view = requested_view
            st.query_params.clear()
            st.rerun()
    
    # Hero section
    st.markdown(render_hero_section(metrics), unsafe_allow_html=True)
    
    # Hero CTA buttons
    col1, col2, col3, col4, col5 = st.columns([2, 1.2, 1.2, 1, 2])
    
    with col2:
        if st.button("Créer un compte", key="hero_signup", type="primary", use_container_width=True):
            st.session_state.view = 'signup'
            st.rerun()
    
    with col3:
        if st.button("Voir une démo", key="hero_demo", use_container_width=True):
            st.session_state.view = 'dashboard'
            st.session_state.user_id = 'default'
            st.rerun()
    
    # Markets section
    st.markdown(render_markets_section(), unsafe_allow_html=True)
    
    # Pricing section
    st.markdown(render_pricing_section(), unsafe_allow_html=True)
    
    # Pricing buttons
    col1, col2, col3 = st.columns([1, 1.2, 1.2])
    
    with col2:
        if st.button("S'abonner au plan mensuel", key="sub_monthly", use_container_width=True):
            st.session_state.view = 'signup'
            st.session_state.selected_plan = 'monthly_9_99'
            st.rerun()
    
    with col3:
        if st.button("S'abonner au plan annuel", key="sub_yearly", type="primary", use_container_width=True):
            st.session_state.view = 'signup'
            st.session_state.selected_plan = 'yearly_50'
            st.rerun()
    
    # Footer
    st.markdown(render_footer(), unsafe_allow_html=True)
