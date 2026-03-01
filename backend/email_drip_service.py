"""
Email Drip Onboarding Service for MarketGPS
Sends a 7-day onboarding sequence to new users via Resend API.

Schedule: J0 (immediate), J1, J2, J3, J4, J5, J7

Usage:
    # On signup: schedule the sequence
    schedule_drip_sequence(user_id, email, db)

    # Cron (every 15 min): process pending emails
    process_pending_drips(db)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://marketgps.online")


# ═══════════════════════════════════════════════════════════════════════════════
# DRIP SEQUENCE DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

DRIP_SEQUENCE = [
    {
        "step": 0,
        "delay_days": 0,
        "subject": "Bienvenue sur MarketGPS ! Votre premier score",
        "body_key": "welcome",
    },
    {
        "step": 1,
        "delay_days": 1,
        "subject": "Votre Morning Brief vous attend",
        "body_key": "morning_brief",
    },
    {
        "step": 2,
        "delay_days": 2,
        "subject": "Astuce : cr\u00e9ez votre watchlist",
        "body_key": "watchlist",
    },
    {
        "step": 3,
        "delay_days": 3,
        "subject": "D\u00e9couvrez les march\u00e9s africains",
        "body_key": "african_markets",
    },
    {
        "step": 4,
        "delay_days": 4,
        "subject": "Posez une question \u00e0 l\u2019IA Concierge",
        "body_key": "ai_concierge",
    },
    {
        "step": 5,
        "delay_days": 5,
        "subject": "Votre s\u00e9rie de jours commence !",
        "body_key": "streak",
    },
    {
        "step": 6,
        "delay_days": 7,
        "subject": "Passez Pro et d\u00e9bloquez tout MarketGPS",
        "body_key": "upgrade_pro",
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

def init_drip_tables(db):
    """Create the email_drip_queue table if not exists."""
    with db._get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS email_drip_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                sequence_step INTEGER NOT NULL,
                scheduled_at TEXT NOT NULL,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                UNIQUE(user_id, sequence_step)
            )
        """)
        conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULING
# ═══════════════════════════════════════════════════════════════════════════════

def schedule_drip_sequence(user_id: str, email: str, db):
    """Schedule the full 7-step drip sequence for a new user."""
    init_drip_tables(db)
    now = datetime.utcnow()

    with db._get_connection() as conn:
        for step_config in DRIP_SEQUENCE:
            scheduled_at = now + timedelta(days=step_config["delay_days"])
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO email_drip_queue
                    (user_id, email, sequence_step, scheduled_at, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (user_id, email, step_config["step"], scheduled_at.isoformat()))
            except Exception as e:
                logger.warning(f"Failed to schedule drip step {step_config['step']} for {user_id}: {e}")
        conn.commit()

    logger.info(f"Scheduled {len(DRIP_SEQUENCE)} drip emails for {user_id} ({email})")


def cancel_pending_drips(user_id: str, db):
    """Cancel all pending drip emails (e.g., when user upgrades to Pro)."""
    init_drip_tables(db)
    with db._get_connection() as conn:
        conn.execute("""
            UPDATE email_drip_queue
            SET status = 'cancelled'
            WHERE user_id = ? AND status = 'pending'
        """, (user_id,))
        conn.commit()
    logger.info(f"Cancelled pending drips for {user_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

def process_pending_drips(db):
    """Process all pending drip emails whose scheduled_at <= now."""
    init_drip_tables(db)
    now = datetime.utcnow().isoformat()

    with db._get_connection() as conn:
        rows = conn.execute("""
            SELECT id, user_id, email, sequence_step
            FROM email_drip_queue
            WHERE status = 'pending' AND scheduled_at <= ?
            ORDER BY scheduled_at ASC
            LIMIT 50
        """, (now,)).fetchall()

    sent_count = 0
    for row in rows:
        drip_id = row["id"]
        email = row["email"]
        step = row["sequence_step"]

        success = _send_drip_email(email, step)

        with db._get_connection() as conn:
            if success:
                conn.execute("""
                    UPDATE email_drip_queue
                    SET status = 'sent', sent_at = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), drip_id))
                sent_count += 1
            else:
                conn.execute("""
                    UPDATE email_drip_queue
                    SET status = 'failed'
                    WHERE id = ?
                """, (drip_id,))
            conn.commit()

    if sent_count > 0:
        logger.info(f"Sent {sent_count}/{len(rows)} drip emails")


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL SENDING
# ═══════════════════════════════════════════════════════════════════════════════

def _send_drip_email(to_email: str, step: int) -> bool:
    """Send a single drip email using Resend."""
    step_config = next((s for s in DRIP_SEQUENCE if s["step"] == step), None)
    if not step_config:
        logger.error(f"Unknown drip step: {step}")
        return False

    subject = step_config["subject"]
    html = _get_drip_html(step_config["body_key"])
    text = _get_drip_text(step_config["body_key"])

    try:
        from email_service import send_email
        return send_email(
            to=to_email,
            subject=subject,
            html=html,
            text=text,
            tags=[{"name": "category", "value": f"drip-j{step}"}],
        )
    except Exception as e:
        logger.error(f"Failed to send drip email step {step} to {to_email}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

def _email_wrapper(title: str, content: str) -> str:
    """Wrap content in the MarketGPS email template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#0a0a0a;color:#e5e5e5;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 20px;"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#141414;border-radius:16px;overflow:hidden;">
<tr><td style="background:linear-gradient(135deg,#10b981,#059669);padding:30px;text-align:center;">
<h1 style="margin:0;color:#fff;font-size:24px;">MarketGPS</h1>
<p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">{title}</p>
</td></tr>
<tr><td style="padding:32px;">{content}</td></tr>
<tr><td style="padding:20px 32px;border-top:1px solid #2a2a2a;text-align:center;">
<p style="margin:0;color:#666;font-size:12px;">MarketGPS — Votre GPS des march\u00e9s financiers</p>
<p style="margin:8px 0 0;"><a href="{FRONTEND_URL}" style="color:#10b981;text-decoration:none;font-size:12px;">marketgps.online</a></p>
</td></tr>
</table></td></tr></table></body></html>"""


def _cta_button(text: str, url: str) -> str:
    return f'<a href="{url}" style="display:inline-block;padding:14px 28px;background:#10b981;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:16px;margin:16px 0;">{text}</a>'


DRIP_TEMPLATES = {
    "welcome": {
        "title": "Bienvenue !",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Bienvenue sur MarketGPS !</h2>
<p style="color:#ccc;line-height:1.6;">Vous venez de rejoindre la communaut\u00e9 d\u2019investisseurs qui utilisent l\u2019IA pour prendre de meilleures d\u00e9cisions.</p>
<p style="color:#ccc;line-height:1.6;"><strong style="color:#10b981;">Votre premi\u00e8re mission :</strong> consultez le score d\u2019un actif qui vous int\u00e9resse.</p>
{_cta_button("Voir mon premier score", f"{FRONTEND_URL}/dashboard")}
<p style="color:#888;font-size:13px;margin-top:20px;">Tapez n\u2019importe quel ticker (AAPL, MSFT, SONATEL...) pour obtenir une analyse compl\u00e8te.</p>
""",
        "text": "Bienvenue sur MarketGPS ! Consultez votre premier score sur {}/dashboard".format(FRONTEND_URL),
    },
    "morning_brief": {
        "title": "Votre briefing du jour",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Le Morning Brief vous attend</h2>
<p style="color:#ccc;line-height:1.6;">Chaque matin, MarketGPS pr\u00e9pare un briefing personnalis\u00e9 avec :</p>
<ul style="color:#ccc;line-height:1.8;padding-left:20px;">
<li>L\u2019\u00e9tat de votre portefeuille</li>
<li>Les opportunit\u00e9s du jour</li>
<li>L\u2019actualit\u00e9 financi\u00e8re africaine</li>
</ul>
{_cta_button("Voir mon briefing", f"{FRONTEND_URL}/morning-brief")}
""",
        "text": "Votre Morning Brief est pr\u00eat ! Consultez-le sur {}/morning-brief".format(FRONTEND_URL),
    },
    "watchlist": {
        "title": "Votre watchlist",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Cr\u00e9ez votre watchlist</h2>
<p style="color:#ccc;line-height:1.6;">Suivez vos actifs favoris et recevez des alertes quand leur score change.</p>
<p style="color:#ccc;line-height:1.6;">Ajoutez simplement un actif en cliquant sur l\u2019\u00e9toile depuis n\u2019importe quelle page de score.</p>
{_cta_button("G\u00e9rer ma watchlist", f"{FRONTEND_URL}/watchlist")}
""",
        "text": "Cr\u00e9ez votre watchlist sur {}/watchlist".format(FRONTEND_URL),
    },
    "african_markets": {
        "title": "March\u00e9s africains",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">D\u00e9couvrez les march\u00e9s africains</h2>
<p style="color:#ccc;line-height:1.6;">MarketGPS couvre la <strong style="color:#10b981;">BRVM</strong> (Abidjan), le <strong style="color:#10b981;">JSE</strong> (Johannesburg) et le <strong style="color:#10b981;">NGX</strong> (Lagos).</p>
<p style="color:#ccc;line-height:1.6;">Explorez les actifs africains avec le m\u00eame scoring que les march\u00e9s US et europ\u00e9ens.</p>
{_cta_button("Explorer les march\u00e9s africains", f"{FRONTEND_URL}/news")}
""",
        "text": "D\u00e9couvrez les march\u00e9s africains sur MarketGPS : BRVM, JSE, NGX.",
    },
    "ai_concierge": {
        "title": "IA Concierge",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Posez une question \u00e0 l\u2019IA</h2>
<p style="color:#ccc;line-height:1.6;">Vous avez <strong style="color:#10b981;">3 messages gratuits</strong> avec notre IA Concierge.</p>
<p style="color:#ccc;line-height:1.6;">Demandez-lui n\u2019importe quoi : \u00ab Quel est le meilleur ETF africain ? \u00bb, \u00ab Analyse SONATEL \u00bb, \u00ab Comment diversifier mon portefeuille ? \u00bb</p>
{_cta_button("Parler \u00e0 l\u2019IA", f"{FRONTEND_URL}/dashboard")}
<p style="color:#888;font-size:13px;margin-top:20px;">Les abonn\u00e9s Pro ont un acc\u00e8s illimit\u00e9 \u00e0 l\u2019IA.</p>
""",
        "text": "Posez une question \u00e0 l\u2019IA Concierge de MarketGPS (3 messages gratuits).",
    },
    "streak": {
        "title": "Gamification",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Votre s\u00e9rie de jours commence !</h2>
<p style="color:#ccc;line-height:1.6;">Consultez un score chaque jour pour maintenir votre s\u00e9rie et gagner des bonus XP.</p>
<ul style="color:#ccc;line-height:1.8;padding-left:20px;">
<li>3 jours : bonus +10%</li>
<li>7 jours : bonus +25%</li>
<li>30 jours : bonus +100% !</li>
</ul>
{_cta_button("Maintenir ma s\u00e9rie", f"{FRONTEND_URL}/morning-brief")}
""",
        "text": "Maintenez votre s\u00e9rie de jours sur MarketGPS pour gagner des bonus XP !",
    },
    "upgrade_pro": {
        "title": "Passez Pro",
        "content": lambda: f"""
<h2 style="color:#fff;font-size:20px;margin:0 0 16px;">Pr\u00eat \u00e0 passer au niveau sup\u00e9rieur ?</h2>
<p style="color:#ccc;line-height:1.6;">Apr\u00e8s une semaine sur MarketGPS, vous avez d\u00e9couvert le scoring, le Morning Brief, et l\u2019IA.</p>
<p style="color:#ccc;line-height:1.6;">Avec <strong style="color:#10b981;">MarketGPS Pro</strong>, d\u00e9bloquez :</p>
<ul style="color:#ccc;line-height:1.8;padding-left:20px;">
<li>D\u00e9tail des piliers de score (Value, Momentum, Safety)</li>
<li>IA Concierge illimit\u00e9e</li>
<li>Import CSV de portefeuille</li>
<li>Strat\u00e9gies personnalis\u00e9es</li>
<li>Briefing personnalis\u00e9 complet</li>
</ul>
<p style="color:#10b981;font-size:18px;font-weight:700;margin:16px 0;">\u00c0 partir de 9,99\u20ac/mois</p>
{_cta_button("Passer Pro maintenant", f"{FRONTEND_URL}/pricing")}
""",
        "text": "Passez \u00e0 MarketGPS Pro pour 9,99\u20ac/mois. D\u00e9bloquez les piliers de score, l\u2019IA illimit\u00e9e, et bien plus.",
    },
}


def _get_drip_html(body_key: str) -> str:
    template = DRIP_TEMPLATES.get(body_key)
    if not template:
        return ""
    return _email_wrapper(template["title"], template["content"]())


def _get_drip_text(body_key: str) -> str:
    template = DRIP_TEMPLATES.get(body_key)
    if not template:
        return ""
    return template["text"]
