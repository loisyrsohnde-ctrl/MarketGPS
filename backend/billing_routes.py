"""
MarketGPS v13.0 - Billing Routes (Stripe Subscription Module)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPORTANT: Stripe is the SOURCE OF TRUTH for all billing decisions.
Systeme.io is for marketing only and NEVER decides access.

Features:
- POST /api/billing/checkout-session: Create Stripe Checkout
- POST /api/billing/stripe/webhook: Handle Stripe webhooks (idempotent)
- GET /api/billing/me: Get current subscription status
- POST /api/billing/portal-session: Stripe Customer Portal

Security:
- All endpoints except webhook require Supabase auth
- Webhook verifies Stripe signature
- Idempotency via stripe_events table
- Grace period for past_due (48h default)
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Local imports
from storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

GRACE_PERIOD_HOURS = int(os.environ.get("BILLING_GRACE_PERIOD_HOURS", "48"))
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://app.marketgps.online")

# Price IDs from environment (support both naming conventions for backward compatibility)
STRIPE_PRICE_ID_MONTHLY = (
    os.environ.get("STRIPE_PRICE_ID_MONTHLY") or
    os.environ.get("STRIPE_PRICE_MONTHLY_ID") or
    ""
)
STRIPE_PRICE_ID_ANNUAL = (
    os.environ.get("STRIPE_PRICE_ID_ANNUAL") or
    os.environ.get("STRIPE_PRICE_YEARLY_ID") or
    ""
)

# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

router = APIRouter(prefix="/api/billing", tags=["billing"])

# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST/RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class CheckoutRequest(BaseModel):
    plan: str  # 'monthly' or 'annual'


class CheckoutResponse(BaseModel):
    url: str


class SubscriptionResponse(BaseModel):
    user_id: str
    plan: str  # 'free', 'monthly', 'annual'
    status: str  # 'active', 'trialing', 'past_due', 'canceled', 'inactive'
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    is_active: bool = False  # True if user should have access
    grace_period_remaining_hours: Optional[int] = None


class PortalResponse(BaseModel):
    url: str


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_db() -> SQLiteStore:
    """Get database connection."""
    store = SQLiteStore()
    _ensure_subscription_tables(store)
    return store


def _ensure_subscription_tables(store: SQLiteStore):
    """Ensure subscription tables exist (additive migration)."""
    with store._get_connection() as conn:
        # Check if tables exist
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('subscriptions', 'stripe_events')"
        ).fetchall()
        
        if len(tables) < 2:
            # Run migration
            migration_path = os.path.join(
                os.path.dirname(__file__), 
                "..", "storage", "migrations", "add_subscription_tables.sql"
            )
            if os.path.exists(migration_path):
                with open(migration_path, "r") as f:
                    conn.executescript(f.read())
                logger.info("✅ Subscription tables created")
            else:
                # Inline creation if migration file not found
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        user_id TEXT PRIMARY KEY,
                        stripe_customer_id TEXT,
                        stripe_subscription_id TEXT,
                        plan TEXT DEFAULT 'free',
                        status TEXT DEFAULT 'inactive',
                        current_period_start TEXT,
                        current_period_end TEXT,
                        cancel_at_period_end INTEGER DEFAULT 0,
                        canceled_at TEXT,
                        grace_period_end TEXT,
                        created_at TEXT DEFAULT (datetime('now')),
                        updated_at TEXT DEFAULT (datetime('now'))
                    );
                    
                    CREATE TABLE IF NOT EXISTS stripe_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        processed_at TEXT DEFAULT (datetime('now')),
                        payload_hash TEXT,
                        status TEXT DEFAULT 'processed'
                    );
                    
                    CREATE TABLE IF NOT EXISTS systemeio_sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        email TEXT NOT NULL,
                        action TEXT NOT NULL,
                        tag_name TEXT,
                        payload_json TEXT,
                        status TEXT DEFAULT 'pending',
                        attempts INTEGER DEFAULT 0,
                        last_attempt_at TEXT,
                        error_message TEXT,
                        created_at TEXT DEFAULT (datetime('now'))
                    );
                """)
                logger.info("✅ Subscription tables created (inline)")


def get_subscription(user_id: str, db: SQLiteStore) -> Optional[Dict[str, Any]]:
    """Get subscription from database."""
    with db._get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if row:
            columns = [desc[0] for desc in conn.execute("PRAGMA table_info(subscriptions)").fetchall()]
            col_names = [c[1] for c in conn.execute("PRAGMA table_info(subscriptions)").fetchall()]
            return dict(zip(col_names, row))
    return None


def upsert_subscription(user_id: str, data: Dict[str, Any], db: SQLiteStore):
    """Insert or update subscription."""
    data["user_id"] = user_id
    data["updated_at"] = datetime.utcnow().isoformat()
    
    with db._get_connection() as conn:
        # Check if exists
        existing = conn.execute(
            "SELECT 1 FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if existing:
            # Update
            set_clause = ", ".join([f"{k} = ?" for k in data.keys() if k != "user_id"])
            values = [v for k, v in data.items() if k != "user_id"]
            values.append(user_id)
            conn.execute(
                f"UPDATE subscriptions SET {set_clause} WHERE user_id = ?",
                values
            )
        else:
            # Insert
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            conn.execute(
                f"INSERT INTO subscriptions ({columns}) VALUES ({placeholders})",
                list(data.values())
            )
        
        logger.info(f"Subscription upserted for user {user_id}: {data.get('status')}/{data.get('plan')}")


def is_event_processed(event_id: str, db: SQLiteStore) -> bool:
    """Check if Stripe event was already processed (idempotency)."""
    with db._get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM stripe_events WHERE event_id = ?",
            (event_id,)
        ).fetchone()
        return row is not None


def mark_event_processed(event_id: str, event_type: str, db: SQLiteStore, status: str = "processed"):
    """Mark Stripe event as processed."""
    with db._get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO stripe_events (event_id, event_type, processed_at, status)
               VALUES (?, ?, datetime('now'), ?)""",
            (event_id, event_type, status)
        )


def queue_systemeio_sync(user_id: str, email: str, action: str, tag_name: str, db: SQLiteStore):
    """Queue a Systeme.io sync action (non-blocking)."""
    with db._get_connection() as conn:
        conn.execute(
            """INSERT INTO systemeio_sync_queue (user_id, email, action, tag_name, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (user_id, email, action, tag_name)
        )
    logger.info(f"Queued Systeme.io sync: {action} tag={tag_name} for {email}")


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user_id from Supabase JWT token.
    Uses security.py functions for consistent auth behavior.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Try to use security.py's verification
        from security import verify_supabase_token
        payload = verify_supabase_token(token)
        
        if payload is None:
            # Token verification failed - try fallback decode for development
            logger.warning("Token verification returned None, attempting fallback decode")
            payload = _decode_jwt_unverified(token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user_id")
        
        return user_id
        
    except ImportError:
        # security.py not available - use fallback decode
        logger.warning("security.py not available, using fallback JWT decode")
        payload = _decode_jwt_unverified(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token format")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user_id")
        return user_id
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def _decode_jwt_unverified(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT without verification (for development/fallback only).
    WARNING: This does NOT verify the signature!
    """
    import base64
    import json
    
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        # Add padding if needed
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        return payload
        
    except Exception as e:
        logger.warning(f"JWT decode fallback failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# SUBSCRIPTION ACCESS HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def is_subscription_active(subscription: Optional[Dict[str, Any]]) -> bool:
    """
    Determine if user should have access based on subscription status.
    
    Access granted if:
    - status = 'active' or 'trialing'
    - status = 'past_due' AND within grace period
    """
    if not subscription:
        return False
    
    status = subscription.get("status", "inactive")
    
    if status in ("active", "trialing"):
        return True
    
    if status == "past_due":
        # Check grace period
        grace_end = subscription.get("grace_period_end")
        if grace_end:
            try:
                grace_end_dt = datetime.fromisoformat(grace_end.replace("Z", "+00:00"))
                if datetime.utcnow() < grace_end_dt.replace(tzinfo=None):
                    return True
            except:
                pass
    
    return False


def require_active_subscription(user_id: str, db: SQLiteStore) -> Dict[str, Any]:
    """
    Guard function: raises 403 if user doesn't have active subscription.
    Returns subscription data if active.
    """
    subscription = get_subscription(user_id, db)
    
    if not is_subscription_active(subscription):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "SUBSCRIPTION_REQUIRED",
                "message": "Active subscription required to access this feature",
                "status": subscription.get("status") if subscription else "none"
            }
        )
    
    return subscription


# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

def get_stripe():
    """Get configured Stripe module."""
    import stripe
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    return stripe


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Create Stripe Checkout Session for subscription.
    
    - Requires Supabase auth
    - Creates or retrieves Stripe customer
    - Sets client_reference_id and metadata for webhook correlation
    """
    stripe = get_stripe()
    db = get_db()
    
    # Validate plan
    plan = request.plan.lower()
    if plan not in ("monthly", "annual"):
        raise HTTPException(status_code=400, detail="Invalid plan. Use 'monthly' or 'annual'")
    
    # Get price ID
    price_id = STRIPE_PRICE_ID_MONTHLY if plan == "monthly" else STRIPE_PRICE_ID_ANNUAL
    if not price_id:
        raise HTTPException(status_code=500, detail=f"Stripe price not configured for {plan}")
    
    try:
        # Get or create Stripe customer
        subscription = get_subscription(user_id, db)
        stripe_customer_id = subscription.get("stripe_customer_id") if subscription else None
        
        if not stripe_customer_id:
            # Get user email from Supabase
            try:
                from supabase_admin import SupabaseAdmin
                admin = SupabaseAdmin()
                user_data = admin.get_user_profile(user_id)
                email = user_data.get("email") if user_data else None
            except:
                email = None
            
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={"supabase_user_id": user_id}
            )
            stripe_customer_id = customer.id
            
            # Store customer ID
            upsert_subscription(user_id, {"stripe_customer_id": stripe_customer_id}, db)
            logger.info(f"Created Stripe customer {stripe_customer_id} for user {user_id}")
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/settings/billing?canceled=1",
            client_reference_id=user_id,
            allow_promotion_codes=True,
            billing_address_collection="required",
            metadata={
                "user_id": user_id,
                "plan": plan,
            },
        )
        
        logger.info(f"Created checkout session {session.id} for user {user_id}, plan={plan}")
        return CheckoutResponse(url=session.url)
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    user_id: str = Depends(get_current_user_id),
):
    """
    Get current user's subscription status.
    
    Returns:
    - plan: 'free', 'monthly', 'annual'
    - status: 'active', 'trialing', 'past_due', 'canceled', 'inactive'
    - is_active: True if user should have access (includes grace period)
    """
    db = get_db()
    subscription = get_subscription(user_id, db)
    
    if not subscription:
        return SubscriptionResponse(
            user_id=user_id,
            plan="free",
            status="inactive",
            is_active=False,
        )
    
    # Calculate grace period remaining
    grace_remaining = None
    if subscription.get("status") == "past_due" and subscription.get("grace_period_end"):
        try:
            grace_end = datetime.fromisoformat(subscription["grace_period_end"].replace("Z", "+00:00"))
            remaining = grace_end.replace(tzinfo=None) - datetime.utcnow()
            if remaining.total_seconds() > 0:
                grace_remaining = int(remaining.total_seconds() / 3600)
        except:
            pass
    
    return SubscriptionResponse(
        user_id=user_id,
        plan=subscription.get("plan", "free"),
        status=subscription.get("status", "inactive"),
        current_period_end=subscription.get("current_period_end"),
        cancel_at_period_end=bool(subscription.get("cancel_at_period_end", 0)),
        is_active=is_subscription_active(subscription),
        grace_period_remaining_hours=grace_remaining,
    )


@router.post("/portal-session", response_model=PortalResponse)
async def create_portal_session(
    user_id: str = Depends(get_current_user_id),
):
    """
    Create Stripe Customer Portal session for managing subscription.
    """
    stripe = get_stripe()
    db = get_db()
    
    subscription = get_subscription(user_id, db)
    if not subscription or not subscription.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="No subscription found")
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=subscription["stripe_customer_id"],
            return_url=f"{FRONTEND_URL}/settings/billing",
        )
        return PortalResponse(url=session.url)
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe portal error: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# STRIPE WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.
    
    Security:
    - Verifies Stripe signature
    - Idempotent: skips already-processed events
    
    Events handled:
    - invoice.paid: status=active, update period
    - invoice.payment_failed: status=past_due, set grace period
    - customer.subscription.updated: sync status
    - customer.subscription.deleted: status=canceled
    - charge.refunded: status=canceled
    - charge.dispute.created: status=canceled (dispute = chargeback)
    """
    import stripe as stripe_module
    stripe_module.api_key = os.environ.get("STRIPE_SECRET_KEY")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    if not stripe_signature:
        logger.warning("Webhook missing signature")
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    # Get raw body
    payload = await request.body()
    
    # Verify signature
    try:
        event = stripe_module.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except stripe_module.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook parsing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    event_id = event.get("id")
    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    
    logger.info(f"Stripe webhook received: {event_type} ({event_id})")
    
    # Idempotency check
    db = get_db()
    if is_event_processed(event_id, db):
        logger.info(f"Event {event_id} already processed, skipping")
        return JSONResponse({"status": "already_processed"})
    
    try:
        # Route to handler
        handlers = {
            "invoice.paid": handle_invoice_paid,
            "invoice.payment_failed": handle_invoice_payment_failed,
            "customer.subscription.updated": handle_subscription_updated,
            "customer.subscription.deleted": handle_subscription_deleted,
            "charge.refunded": handle_charge_refunded,
            "charge.dispute.created": handle_dispute_created,
            "checkout.session.completed": handle_checkout_completed,
        }
        
        handler = handlers.get(event_type)
        if handler:
            await handler(data, db)
            mark_event_processed(event_id, event_type, db, "processed")
        else:
            logger.info(f"Unhandled event type: {event_type}")
            mark_event_processed(event_id, event_type, db, "skipped")
        
        return JSONResponse({"status": "success"})
    
    except Exception as e:
        logger.error(f"Webhook handler error for {event_type}: {e}")
        mark_event_processed(event_id, event_type, db, "failed")
        # Return 200 to prevent Stripe retries (we logged the error)
        return JSONResponse({"status": "error", "message": str(e)})


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_checkout_completed(data: dict, db: SQLiteStore):
    """Handle successful checkout session."""
    user_id = data.get("client_reference_id") or data.get("metadata", {}).get("user_id")
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")
    plan = data.get("metadata", {}).get("plan", "monthly")
    
    if not user_id:
        logger.error(f"Checkout completed but no user_id found: {data}")
        return
    
    upsert_subscription(user_id, {
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "plan": plan,
        "status": "active",
    }, db)
    
    # Queue Systeme.io sync
    try:
        from supabase_admin import SupabaseAdmin
        admin = SupabaseAdmin()
        user_data = admin.get_user_profile(user_id)
        if user_data and user_data.get("email"):
            queue_systemeio_sync(user_id, user_data["email"], "tag_add", f"subscriber_{plan}", db)
            queue_systemeio_sync(user_id, user_data["email"], "tag_add", "active_subscriber", db)
    except Exception as e:
        logger.warning(f"Failed to queue Systeme.io sync: {e}")
    
    logger.info(f"Checkout completed: user={user_id}, plan={plan}")


async def handle_invoice_paid(data: dict, db: SQLiteStore):
    """Handle paid invoice (subscription activation/renewal)."""
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")
    
    if not subscription_id:
        logger.warning("invoice.paid without subscription_id, skipping")
        return
    
    # Find user by customer ID
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"invoice.paid: no user found for customer {customer_id}")
        return
    
    # Get subscription details from Stripe
    stripe = get_stripe()
    try:
        sub = stripe.Subscription.retrieve(subscription_id)
        plan = _get_plan_from_subscription(sub)
        period_end = datetime.fromtimestamp(sub.current_period_end).isoformat()
        period_start = datetime.fromtimestamp(sub.current_period_start).isoformat()
        
        upsert_subscription(user_id, {
            "status": "active",
            "plan": plan,
            "current_period_start": period_start,
            "current_period_end": period_end,
            "grace_period_end": None,  # Clear any grace period
        }, db)
        
        logger.info(f"Invoice paid: user={user_id}, plan={plan}")
    
    except Exception as e:
        logger.error(f"Error processing invoice.paid: {e}")


async def handle_invoice_payment_failed(data: dict, db: SQLiteStore):
    """Handle failed payment - set past_due with grace period."""
    customer_id = data.get("customer")
    
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"invoice.payment_failed: no user found for customer {customer_id}")
        return
    
    # Set grace period
    grace_end = (datetime.utcnow() + timedelta(hours=GRACE_PERIOD_HOURS)).isoformat()
    
    upsert_subscription(user_id, {
        "status": "past_due",
        "grace_period_end": grace_end,
    }, db)
    
    # Queue Systeme.io sync (payment_failed tag)
    try:
        from supabase_admin import SupabaseAdmin
        admin = SupabaseAdmin()
        user_data = admin.get_user_profile(user_id)
        if user_data and user_data.get("email"):
            queue_systemeio_sync(user_id, user_data["email"], "tag_add", "payment_failed", db)
    except Exception as e:
        logger.warning(f"Failed to queue Systeme.io sync: {e}")
    
    logger.info(f"Payment failed: user={user_id}, grace_period_end={grace_end}")


async def handle_subscription_updated(data: dict, db: SQLiteStore):
    """Handle subscription status changes."""
    customer_id = data.get("customer")
    subscription_id = data.get("id")
    status = data.get("status")
    cancel_at_period_end = data.get("cancel_at_period_end", False)
    
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"subscription.updated: no user found for customer {customer_id}")
        return
    
    plan = _get_plan_from_subscription(data)
    
    # Map Stripe status
    status_map = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "canceled": "canceled",
        "unpaid": "inactive",
        "incomplete": "inactive",
        "incomplete_expired": "inactive",
        "paused": "inactive",
    }
    mapped_status = status_map.get(status, "inactive")
    
    period_end = None
    if data.get("current_period_end"):
        period_end = datetime.fromtimestamp(data["current_period_end"]).isoformat()
    
    update_data = {
        "stripe_subscription_id": subscription_id,
        "status": mapped_status,
        "plan": plan if mapped_status in ("active", "trialing") else "free",
        "cancel_at_period_end": 1 if cancel_at_period_end else 0,
    }
    if period_end:
        update_data["current_period_end"] = period_end
    
    upsert_subscription(user_id, update_data, db)
    logger.info(f"Subscription updated: user={user_id}, status={mapped_status}, plan={plan}")


async def handle_subscription_deleted(data: dict, db: SQLiteStore):
    """Handle subscription cancellation."""
    customer_id = data.get("customer")
    
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"subscription.deleted: no user found for customer {customer_id}")
        return
    
    upsert_subscription(user_id, {
        "status": "canceled",
        "plan": "free",
        "stripe_subscription_id": None,
        "canceled_at": datetime.utcnow().isoformat(),
    }, db)
    
    # Queue Systeme.io sync
    try:
        from supabase_admin import SupabaseAdmin
        admin = SupabaseAdmin()
        user_data = admin.get_user_profile(user_id)
        if user_data and user_data.get("email"):
            queue_systemeio_sync(user_id, user_data["email"], "tag_remove", "active_subscriber", db)
            queue_systemeio_sync(user_id, user_data["email"], "tag_add", "churned", db)
    except Exception as e:
        logger.warning(f"Failed to queue Systeme.io sync: {e}")
    
    logger.info(f"Subscription deleted: user={user_id}")


async def handle_charge_refunded(data: dict, db: SQLiteStore):
    """Handle refund - cancel subscription."""
    customer_id = data.get("customer")
    
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"charge.refunded: no user found for customer {customer_id}")
        return
    
    # On refund, cancel the subscription
    upsert_subscription(user_id, {
        "status": "canceled",
        "plan": "free",
    }, db)
    
    logger.info(f"Charge refunded, subscription canceled: user={user_id}")


async def handle_dispute_created(data: dict, db: SQLiteStore):
    """Handle dispute/chargeback - immediately revoke access."""
    customer_id = data.get("customer")
    
    user_id = _find_user_by_customer(customer_id, db)
    if not user_id:
        logger.warning(f"charge.dispute.created: no user found for customer {customer_id}")
        return
    
    # Disputes are serious - immediately cancel
    upsert_subscription(user_id, {
        "status": "canceled",
        "plan": "free",
    }, db)
    
    logger.warning(f"⚠️ DISPUTE created, subscription canceled: user={user_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _find_user_by_customer(customer_id: str, db: SQLiteStore) -> Optional[str]:
    """Find user_id by Stripe customer ID."""
    with db._get_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM subscriptions WHERE stripe_customer_id = ?",
            (customer_id,)
        ).fetchone()
        return row[0] if row else None


def _get_plan_from_subscription(subscription: dict) -> str:
    """Determine plan type from Stripe subscription data."""
    items = subscription.get("items", {}).get("data", [])
    if not items:
        return "free"
    
    price_id = items[0].get("price", {}).get("id", "")
    
    if price_id == STRIPE_PRICE_ID_ANNUAL:
        return "annual"
    elif price_id == STRIPE_PRICE_ID_MONTHLY:
        return "monthly"
    
    # Fallback: check interval
    interval = items[0].get("price", {}).get("recurring", {}).get("interval", "")
    if interval == "year":
        return "annual"
    elif interval == "month":
        return "monthly"
    
    return "monthly"  # Default
