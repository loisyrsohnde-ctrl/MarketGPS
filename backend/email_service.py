"""
Email Service for MarketGPS
Handles transactional emails via Resend API

Emails sent:
- subscription_confirmed: After successful payment
- subscription_canceled: After cancellation
- payment_failed: After failed payment (optional)

Design:
- Idempotent: Uses stripe_events table to prevent duplicates
- Retry-safe: Logs failures, can be retried
- Low-cost: Resend free tier (3000 emails/month)
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "MarketGPS <noreply@marketgps.online>")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://app.marketgps.online")

# Feature flag: Enable/disable email sending
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "true").lower() in ("true", "1", "yes")


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

def get_subscription_confirmed_template(
    user_email: str,
    plan: str,
    amount: str,
    period_end: Optional[str] = None,
) -> Dict[str, str]:
    """
    Email template for successful subscription.
    """
    plan_display = "Pro Mensuel" if plan == "monthly" else "Pro Annuel"

    subject = f"Bienvenue dans MarketGPS {plan_display} !"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue dans MarketGPS</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #0a0a0a; color: #e5e5e5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #141414; border-radius: 16px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                                MarketGPS
                            </h1>
                            <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                Votre GPS des marchés financiers
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #ffffff; font-size: 24px; font-weight: 600;">
                                Bienvenue dans MarketGPS {plan_display} !
                            </h2>

                            <p style="margin: 0 0 20px; color: #a3a3a3; font-size: 16px; line-height: 1.6;">
                                Votre abonnement est maintenant actif. Vous avez accès à toutes les fonctionnalités Pro de MarketGPS.
                            </p>

                            <!-- Plan Details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1f1f1f; border-radius: 12px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <table width="100%" cellpadding="0" cellspacing="0">
                                            <tr>
                                                <td style="color: #a3a3a3; font-size: 14px;">Plan</td>
                                                <td style="color: #ffffff; font-size: 14px; text-align: right; font-weight: 600;">{plan_display}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding-top: 10px; color: #a3a3a3; font-size: 14px;">Montant</td>
                                                <td style="padding-top: 10px; color: #10b981; font-size: 14px; text-align: right; font-weight: 600;">{amount}</td>
                                            </tr>
                                            {f'''<tr>
                                                <td style="padding-top: 10px; color: #a3a3a3; font-size: 14px;">Prochain renouvellement</td>
                                                <td style="padding-top: 10px; color: #ffffff; font-size: 14px; text-align: right;">{period_end}</td>
                                            </tr>''' if period_end else ''}
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- Features -->
                            <p style="margin: 20px 0 10px; color: #ffffff; font-size: 16px; font-weight: 600;">
                                Ce qui est inclus :
                            </p>
                            <ul style="margin: 0; padding: 0 0 0 20px; color: #a3a3a3; font-size: 14px; line-height: 2;">
                                <li>Calculs de score illimités</li>
                                <li>Tous les indicateurs avancés</li>
                                <li>Export des données (CSV, Excel)</li>
                                <li>Liste de suivi illimitée</li>
                                <li>Alertes personnalisées</li>
                                <li>Support prioritaire</li>
                            </ul>

                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Accéder à mon Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 20px 0 0; color: #737373; font-size: 14px; line-height: 1.6;">
                                Vous recevrez également un reçu de paiement séparé de Stripe.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px; background-color: #0f0f0f; text-align: center; border-top: 1px solid #262626;">
                            <p style="margin: 0; color: #525252; font-size: 12px;">
                                Des questions ? Contactez-nous à <a href="mailto:support@marketgps.online" style="color: #10b981;">support@marketgps.online</a>
                            </p>
                            <p style="margin: 10px 0 0; color: #404040; font-size: 11px;">
                                MarketGPS - Votre GPS des marchés financiers
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    text = f"""
Bienvenue dans MarketGPS {plan_display} !

Votre abonnement est maintenant actif.

Plan: {plan_display}
Montant: {amount}
{f"Prochain renouvellement: {period_end}" if period_end else ""}

Ce qui est inclus:
- Calculs de score illimités
- Tous les indicateurs avancés
- Export des données (CSV, Excel)
- Liste de suivi illimitée
- Alertes personnalisées
- Support prioritaire

Accéder à votre dashboard: {FRONTEND_URL}/dashboard

---
MarketGPS - Votre GPS des marchés financiers
Support: support@marketgps.online
"""

    return {
        "to": user_email,
        "subject": subject,
        "html": html,
        "text": text,
    }


def get_subscription_canceled_template(
    user_email: str,
    access_until: Optional[str] = None,
) -> Dict[str, str]:
    """
    Email template for subscription cancellation.
    """
    subject = "Votre abonnement MarketGPS a été annulé"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0a0a0a; color: #e5e5e5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #141414; border-radius: 16px; overflow: hidden;">
                    <tr>
                        <td style="background-color: #1f1f1f; padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">MarketGPS</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #ffffff; font-size: 22px;">
                                Votre abonnement a été annulé
                            </h2>

                            <p style="margin: 0 0 20px; color: #a3a3a3; font-size: 16px; line-height: 1.6;">
                                Nous avons bien pris en compte votre demande d'annulation.
                            </p>

                            {f'''<p style="margin: 0 0 20px; color: #fbbf24; font-size: 16px; line-height: 1.6;">
                                Vous conservez l'accès à toutes les fonctionnalités Pro jusqu'au <strong>{access_until}</strong>.
                            </p>''' if access_until else ''}

                            <p style="margin: 0 0 20px; color: #a3a3a3; font-size: 16px; line-height: 1.6;">
                                Vous pouvez vous réabonner à tout moment depuis votre espace personnel.
                            </p>

                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{FRONTEND_URL}/settings/billing" style="display: inline-block; background-color: #262626; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 16px;">
                                            Gérer mon abonnement
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #0f0f0f; text-align: center;">
                            <p style="margin: 0; color: #525252; font-size: 12px;">
                                Support: <a href="mailto:support@marketgps.online" style="color: #10b981;">support@marketgps.online</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    text = f"""
Votre abonnement MarketGPS a été annulé

Nous avons bien pris en compte votre demande d'annulation.

{f"Vous conservez l'accès jusqu'au {access_until}." if access_until else ""}

Vous pouvez vous réabonner à tout moment: {FRONTEND_URL}/settings/billing

---
MarketGPS - Support: support@marketgps.online
"""

    return {
        "to": user_email,
        "subject": subject,
        "html": html,
        "text": text,
    }


def get_payment_failed_template(
    user_email: str,
    amount: Optional[str] = None,
) -> Dict[str, str]:
    """
    Email template for failed payment.
    """
    subject = "Problème avec votre paiement MarketGPS"

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0a0a0a; color: #e5e5e5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #141414; border-radius: 16px; overflow: hidden;">
                    <tr>
                        <td style="background-color: #dc2626; padding: 40px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">MarketGPS</h1>
                            <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9);">Action requise</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #ffffff; font-size: 22px;">
                                Votre paiement n'a pas abouti
                            </h2>

                            <p style="margin: 0 0 20px; color: #a3a3a3; font-size: 16px; line-height: 1.6;">
                                Nous n'avons pas pu traiter votre paiement{f" de {amount}" if amount else ""}.
                            </p>

                            <p style="margin: 0 0 20px; color: #a3a3a3; font-size: 16px; line-height: 1.6;">
                                Pour maintenir votre accès Pro, veuillez mettre à jour vos informations de paiement.
                            </p>

                            <table width="100%" cellpadding="0" cellspacing="0" style="margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{FRONTEND_URL}/settings/billing" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-size: 16px; font-weight: 600;">
                                            Mettre à jour mon paiement
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #0f0f0f; text-align: center;">
                            <p style="margin: 0; color: #525252; font-size: 12px;">
                                Besoin d'aide ? <a href="mailto:support@marketgps.online" style="color: #10b981;">support@marketgps.online</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    text = f"""
Problème avec votre paiement MarketGPS

Nous n'avons pas pu traiter votre paiement{f" de {amount}" if amount else ""}.

Pour maintenir votre accès Pro, veuillez mettre à jour vos informations de paiement:
{FRONTEND_URL}/settings/billing

---
MarketGPS - Support: support@marketgps.online
"""

    return {
        "to": user_email,
        "subject": subject,
        "html": html,
        "text": text,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL SENDING
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(
    to: str,
    subject: str,
    html: str,
    text: str,
    tags: Optional[list] = None,
) -> bool:
    """
    Send email via Resend API.

    Returns True if sent successfully, False otherwise.
    Logs errors but doesn't raise exceptions.
    """
    if not EMAIL_ENABLED:
        logger.info(f"Email disabled, would send to {to}: {subject}")
        return True

    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, cannot send email")
        return False

    try:
        import httpx

        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
                "tags": tags or [],
            },
            timeout=10.0,
        )

        if response.status_code in (200, 201):
            data = response.json()
            logger.info(f"Email sent successfully to {to}, id={data.get('id')}")
            return True
        else:
            logger.error(f"Failed to send email to {to}: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending email to {to}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# HIGH-LEVEL EMAIL FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def send_subscription_confirmed_email(
    user_email: str,
    plan: str,
    amount_cents: int,
    currency: str = "eur",
    period_end_timestamp: Optional[int] = None,
) -> bool:
    """
    Send subscription confirmed email.

    Args:
        user_email: Customer email
        plan: 'monthly' or 'annual'
        amount_cents: Amount in cents (e.g., 999 for 9.99)
        currency: Currency code (e.g., 'eur')
        period_end_timestamp: Unix timestamp for next billing date

    Returns:
        True if sent successfully
    """
    # Format amount
    amount = f"{amount_cents / 100:.2f}".replace(".", ",") + " " + currency.upper()

    # Format period end
    period_end = None
    if period_end_timestamp:
        try:
            dt = datetime.fromtimestamp(period_end_timestamp)
            period_end = dt.strftime("%d/%m/%Y")
        except:
            pass

    template = get_subscription_confirmed_template(
        user_email=user_email,
        plan=plan,
        amount=amount,
        period_end=period_end,
    )

    return send_email(
        to=template["to"],
        subject=template["subject"],
        html=template["html"],
        text=template["text"],
        tags=[{"name": "type", "value": "subscription_confirmed"}],
    )


def send_subscription_canceled_email(
    user_email: str,
    access_until_timestamp: Optional[int] = None,
) -> bool:
    """
    Send subscription canceled email.
    """
    access_until = None
    if access_until_timestamp:
        try:
            dt = datetime.fromtimestamp(access_until_timestamp)
            access_until = dt.strftime("%d/%m/%Y")
        except:
            pass

    template = get_subscription_canceled_template(
        user_email=user_email,
        access_until=access_until,
    )

    return send_email(
        to=template["to"],
        subject=template["subject"],
        html=template["html"],
        text=template["text"],
        tags=[{"name": "type", "value": "subscription_canceled"}],
    )


def send_payment_failed_email(
    user_email: str,
    amount_cents: Optional[int] = None,
    currency: str = "eur",
) -> bool:
    """
    Send payment failed email.
    """
    amount = None
    if amount_cents:
        amount = f"{amount_cents / 100:.2f}".replace(".", ",") + " " + currency.upper()

    template = get_payment_failed_template(
        user_email=user_email,
        amount=amount,
    )

    return send_email(
        to=template["to"],
        subject=template["subject"],
        html=template["html"],
        text=template["text"],
        tags=[{"name": "type", "value": "payment_failed"}],
    )
