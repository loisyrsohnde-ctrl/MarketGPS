"""
MarketGPS Backend API
FastAPI server for Stripe webhooks and billing endpoints
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from api_routes import router as api_router
from user_routes import router as user_router
from barbell_routes import router as barbell_router
from strategies_routes import router as strategies_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services (optional - only for billing)
stripe_service = None
supabase_admin = None

try:
    from stripe_service import StripeService
    from supabase_admin import SupabaseAdmin
    from security import verify_supabase_token, get_current_user_id
    stripe_service = StripeService()
    supabase_admin = SupabaseAdmin()
    logger.info("Stripe and Supabase services initialized")
except Exception as e:
    logger.warning(f"Billing services not available: {e}")
    logger.info("Running in data-only mode (no billing endpoints)")


def ensure_tables_exist():
    """
    Ensure all required tables exist in the database.
    Creates user_strategies and user_strategy_compositions if missing.
    """
    try:
        from storage.sqlite_store import SQLiteStore
        store = SQLiteStore()
        
        with store._get_connection() as conn:
            # Create user_strategies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default',
                    template_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (template_id) REFERENCES strategy_templates(id)
                )
            """)
            
            # Create user_strategy_compositions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_strategy_compositions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_strategy_id INTEGER NOT NULL,
                    instrument_ticker TEXT NOT NULL,
                    block_name TEXT NOT NULL DEFAULT 'custom',
                    weight REAL NOT NULL DEFAULT 0.0,
                    fit_score REAL,
                    FOREIGN KEY (user_strategy_id) REFERENCES user_strategies(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_strategies_user ON user_strategies(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_compositions_strategy ON user_strategy_compositions(user_strategy_id)")
            
            # Also ensure strategy_templates exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'balanced',
                    risk_level TEXT DEFAULT 'moderate',
                    horizon_years INTEGER DEFAULT 10,
                    rebalance_frequency TEXT DEFAULT 'annual',
                    structure_json TEXT,
                    scope TEXT DEFAULT 'US_EU',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
        
        logger.info("✅ All required tables verified/created")
        
    except Exception as e:
        logger.error(f"Error ensuring tables exist: {e}")


def startup_seed():
    """
    Seed demo data if database is empty.
    Ensures the dashboard is never empty on first deployment.
    Also ensures strategy templates are ALWAYS present.
    """
    try:
        # First, ensure all tables exist
        ensure_tables_exist()
        
        from storage.sqlite_store import SQLiteStore
        from core.models import Asset, Score, AssetType
        from datetime import datetime
        import random
        
        store = SQLiteStore()
        
        # ALWAYS ensure strategy templates exist (even if DB has data)
        # This is called via _ensure_strategy_tables in SQLiteStore.__init__
        # but we double-check here to guarantee templates are never missing
        store._ensure_strategy_tables()
        logger.info("✅ Strategy templates verified/seeded")
        
        # Check if we have any scored assets
        with store._get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL").fetchone()[0]
            
            if count > 0:
                logger.info(f"Database has {count} scored assets - no seeding needed")
                return
        
        logger.info("Database empty - seeding demo data for initial display...")
        
        # Demo assets (mix of US and EU blue chips)
        demo_assets = [
            ("AAPL.US", "AAPL", "Apple Inc.", "EQUITY", "US"),
            ("MSFT.US", "MSFT", "Microsoft Corp", "EQUITY", "US"),
            ("GOOGL.US", "GOOGL", "Alphabet Inc", "EQUITY", "US"),
            ("AMZN.US", "AMZN", "Amazon.com Inc", "EQUITY", "US"),
            ("NVDA.US", "NVDA", "NVIDIA Corp", "EQUITY", "US"),
            ("META.US", "META", "Meta Platforms", "EQUITY", "US"),
            ("TSLA.US", "TSLA", "Tesla Inc", "EQUITY", "US"),
            ("JPM.US", "JPM", "JPMorgan Chase", "EQUITY", "US"),
            ("V.US", "V", "Visa Inc", "EQUITY", "US"),
            ("JNJ.US", "JNJ", "Johnson & Johnson", "EQUITY", "US"),
            ("SPY.US", "SPY", "SPDR S&P 500 ETF", "ETF", "US"),
            ("QQQ.US", "QQQ", "Invesco QQQ Trust", "ETF", "US"),
            ("TLT.US", "TLT", "iShares 20+ Treasury", "ETF", "US"),
            ("MC.PA", "MC", "LVMH Moët Hennessy", "EQUITY", "EU"),
            ("SAP.XETRA", "SAP", "SAP SE", "EQUITY", "EU"),
            ("ASML.NL", "ASML", "ASML Holding", "EQUITY", "EU"),
            ("SIE.XETRA", "SIE", "Siemens AG", "EQUITY", "EU"),
            ("TTE.PA", "TTE", "TotalEnergies", "EQUITY", "EU"),
            ("OR.PA", "OR", "L'Oréal SA", "EQUITY", "EU"),
            ("AIR.PA", "AIR", "Airbus SE", "EQUITY", "EU"),
        ]
        
        with store._get_connection() as conn:
            for asset_id, symbol, name, asset_type, market_code in demo_assets:
                # Insert asset
                conn.execute("""
                    INSERT OR IGNORE INTO universe 
                    (asset_id, symbol, name, asset_type, market_scope, market_code, active, tier)
                    VALUES (?, ?, ?, ?, 'US_EU', ?, 1, 1)
                """, (asset_id, symbol, name, asset_type, market_code))
                
                # Generate realistic demo score
                base_score = random.uniform(55, 90)
                value = random.uniform(45, 85) if asset_type == "EQUITY" else None
                momentum = random.uniform(40, 80)
                safety = random.uniform(50, 85)
                confidence = random.randint(70, 95)
                
                conn.execute("""
                    INSERT OR REPLACE INTO scores_latest
                    (asset_id, score_total, score_value, score_momentum, score_safety, 
                     confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (asset_id, round(base_score, 1), 
                      round(value, 1) if value else None,
                      round(momentum, 1), round(safety, 1), confidence))
                
                # Insert gating status as eligible
                conn.execute("""
                    INSERT OR REPLACE INTO gating_status
                    (asset_id, eligible, coverage, liquidity, data_confidence, updated_at)
                    VALUES (?, 1, 0.95, 50000000, 85, datetime('now'))
                """, (asset_id,))
        
        logger.info(f"Seeded {len(demo_assets)} demo assets for initial display")
        
    except Exception as e:
        logger.warning(f"Demo seeding failed (non-critical): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting MarketGPS Backend API...")
    
    # Seed demo data if database is empty
    startup_seed()
    
    yield
    logger.info("Shutting down MarketGPS Backend API...")


# Create FastAPI app
app = FastAPI(
    title="MarketGPS API",
    description="Backend API for billing and webhooks",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
# Default allowed origins (includes localhost for development)
DEFAULT_ORIGINS = [
    # Production domains - MarketGPS
    "https://marketgps.online",
    "https://app.marketgps.online",
    "https://api.marketgps.online",
    # Legacy domains - Afristocks
    "https://afristocks.eu",
    "https://app.afristocks.eu",
    # Local development
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# Allow additional origins via environment variable (comma-separated)
env_origins = os.environ.get("CORS_ORIGINS", "")
extra_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
ALLOWED_ORIGINS = list(set(DEFAULT_ORIGINS + extra_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes for assets/scores/watchlist
app.include_router(api_router)
app.include_router(user_router)
app.include_router(barbell_router)  # Barbell strategy module (ADD-ON)
app.include_router(strategies_router)  # Strategies module (ADD-ON)


# ============================================================================
# Request/Response Models
# ============================================================================

class CheckoutRequest(BaseModel):
    plan: str  # 'monthly' or 'yearly'
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class HealthResponse(BaseModel):
    status: str
    version: str


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# ============================================================================
# Billing Endpoints (Require Auth) - Only available if services are configured
# ============================================================================

def get_current_user_id_safe():
    """Placeholder for user_id dependency when security module not loaded."""
    return "anonymous"


@app.post("/billing/checkout-session", response_model=CheckoutResponse)
@app.post("/api/billing/checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
):
    """
    Create a Stripe Checkout Session for subscription.
    Requires valid Supabase access token.
    """
    if not stripe_service or not supabase_admin:
        raise HTTPException(
            status_code=503, detail="Billing services not configured")

    # Placeholder user_id - implement proper auth later
    user_id = "anonymous"

    try:
        # Get user email from Supabase
        user_data = supabase_admin.get_user_profile(user_id)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        email = user_data.get('email')

        # Get or create Stripe customer
        entitlements = supabase_admin.get_user_entitlements(user_id)
        stripe_customer_id = entitlements.get(
            'stripe_customer_id') if entitlements else None

        if not stripe_customer_id:
            stripe_customer_id = stripe_service.create_customer(email, user_id)
            # Store customer ID
            supabase_admin.update_entitlements(user_id, {
                'stripe_customer_id': stripe_customer_id
            })

        # Determine price ID based on plan
        if request.plan.lower() == 'monthly':
            price_id = os.environ.get('STRIPE_PRICE_MONTHLY_ID')
        elif request.plan.lower() == 'yearly':
            price_id = os.environ.get('STRIPE_PRICE_YEARLY_ID')
        else:
            raise HTTPException(
                status_code=400, detail="Invalid plan. Use 'monthly' or 'yearly'")

        if not price_id:
            raise HTTPException(
                status_code=500, detail="Stripe price not configured")

        # Create checkout session
        success_url = request.success_url or os.environ.get(
            'FRONTEND_SUCCESS_URL',
            'https://app.afristocks.eu/billing?success=1'
        )
        cancel_url = request.cancel_url or os.environ.get(
            'FRONTEND_CANCEL_URL',
            'https://app.afristocks.eu/billing?canceled=1'
        )

        checkout_url = stripe_service.create_checkout_session(
            customer_id=stripe_customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id,
        )

        return {"checkout_url": checkout_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout session error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create checkout session")


@app.post("/billing/portal-session", response_model=PortalResponse)
@app.post("/api/billing/portal-session", response_model=PortalResponse)
async def create_portal_session():
    """
    Create a Stripe Customer Portal session for managing subscription.
    Requires valid Supabase access token.
    """
    if not stripe_service or not supabase_admin:
        raise HTTPException(
            status_code=503, detail="Billing services not configured")

    # Placeholder user_id - implement proper auth later
    user_id = "anonymous"

    try:
        # Get Stripe customer ID
        entitlements = supabase_admin.get_user_entitlements(user_id)

        if not entitlements or not entitlements.get('stripe_customer_id'):
            raise HTTPException(
                status_code=400, detail="No subscription found")

        stripe_customer_id = entitlements['stripe_customer_id']

        return_url = os.environ.get(
            'FRONTEND_SUCCESS_URL',
            'https://app.afristocks.eu/billing'
        )

        portal_url = stripe_service.create_portal_session(
            customer_id=stripe_customer_id,
            return_url=return_url,
        )

        return {"portal_url": portal_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portal session error: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create portal session")


# ============================================================================
# Subscription Status Endpoint
# ============================================================================

class SubscriptionResponse(BaseModel):
    plan: str = "FREE"
    status: str = "active"
    daily_quota_used: int = 0
    daily_quota_limit: int = 10
    features: dict = {}


@app.get("/billing/subscription", response_model=SubscriptionResponse)
@app.get("/api/billing/subscription", response_model=SubscriptionResponse)
async def get_subscription():
    """
    Get current user's subscription status.
    Returns FREE plan with basic limits if not authenticated or no subscription.
    """
    return SubscriptionResponse(
        plan="FREE",
        status="active",
        daily_quota_used=0,
        daily_quota_limit=10,
        features={
            "markets": ["US", "EU"],
            "scopes": ["US_EU"],
            "export_enabled": False,
            "alerts_enabled": False,
        }
    )


# ============================================================================
# Stripe Webhook (Public but signature-verified)
# ============================================================================

@app.post("/billing/webhook")
@app.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events.
    Verifies signature and updates entitlements in Supabase.
    """
    if not stripe_service or not supabase_admin:
        raise HTTPException(
            status_code=503, detail="Billing services not configured")

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    # Get raw body
    payload = await request.body()

    # Verify and parse event
    event = stripe_service.verify_webhook(payload, stripe_signature)

    if not event:
        raise HTTPException(
            status_code=400, detail="Invalid webhook signature")

    event_type = event.get('type')
    data = event.get('data', {}).get('object', {})

    logger.info(f"Received Stripe event: {event_type}")

    try:
        if event_type == 'checkout.session.completed':
            await handle_checkout_completed(data)

        elif event_type == 'invoice.paid':
            await handle_invoice_paid(data)

        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(data)

        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_deleted(data)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        return JSONResponse({"status": "success"})

    except Exception as e:
        logger.error(f"Webhook handling error: {e}")
        # Return 200 to acknowledge receipt (prevent Stripe retries)
        return JSONResponse({"status": "error", "message": str(e)})


# ============================================================================
# Webhook Handlers
# ============================================================================

async def handle_checkout_completed(data: dict):
    """Handle successful checkout."""
    customer_id = data.get('customer')
    subscription_id = data.get('subscription')
    user_id = data.get('client_reference_id')

    if not user_id:
        # Try to find user by customer ID
        user_id = supabase_admin.find_user_by_stripe_customer(customer_id)

    if not user_id:
        logger.error(f"No user found for checkout: customer={customer_id}")
        return

    # Get subscription details
    subscription = stripe_service.get_subscription(subscription_id)
    if not subscription:
        logger.error(f"Subscription not found: {subscription_id}")
        return

    # Determine plan from price
    plan = _get_plan_from_subscription(subscription)

    # Update entitlements
    supabase_admin.update_entitlements(user_id, {
        'plan': plan,
        'status': 'active',
        'stripe_customer_id': customer_id,
        'stripe_subscription_id': subscription_id,
        'current_period_end': subscription.get('current_period_end'),
        'daily_requests_limit': 200,  # Paid users get 200/day
    })

    logger.info(f"Checkout completed: user={user_id}, plan={plan}")


async def handle_invoice_paid(data: dict):
    """Handle paid invoice (subscription renewal)."""
    customer_id = data.get('customer')
    subscription_id = data.get('subscription')

    user_id = supabase_admin.find_user_by_stripe_customer(customer_id)
    if not user_id:
        logger.warning(f"No user found for invoice: customer={customer_id}")
        return

    # Get subscription details
    subscription = stripe_service.get_subscription(subscription_id)
    if subscription:
        plan = _get_plan_from_subscription(subscription)

        supabase_admin.update_entitlements(user_id, {
            'plan': plan,
            'status': 'active',
            'current_period_end': subscription.get('current_period_end'),
        })

        logger.info(f"Invoice paid: user={user_id}")


async def handle_subscription_updated(data: dict):
    """Handle subscription update (plan change, status change)."""
    customer_id = data.get('customer')
    subscription_id = data.get('id')
    status = data.get('status')

    user_id = supabase_admin.find_user_by_stripe_customer(customer_id)
    if not user_id:
        logger.warning(
            f"No user found for subscription update: customer={customer_id}")
        return

    plan = _get_plan_from_subscription(data)

    # Map Stripe status to our status
    status_map = {
        'active': 'active',
        'past_due': 'past_due',
        'canceled': 'canceled',
        'unpaid': 'inactive',
        'incomplete': 'inactive',
        'incomplete_expired': 'inactive',
        'trialing': 'trialing',
    }
    mapped_status = status_map.get(status, 'inactive')

    # Update daily limit based on status
    daily_limit = 200 if mapped_status == 'active' else 10

    supabase_admin.update_entitlements(user_id, {
        'plan': plan if mapped_status == 'active' else 'FREE',
        'status': mapped_status,
        'stripe_subscription_id': subscription_id,
        'current_period_end': data.get('current_period_end'),
        'daily_requests_limit': daily_limit,
    })

    logger.info(
        f"Subscription updated: user={user_id}, status={mapped_status}")


async def handle_subscription_deleted(data: dict):
    """Handle subscription cancellation."""
    customer_id = data.get('customer')

    user_id = supabase_admin.find_user_by_stripe_customer(customer_id)
    if not user_id:
        logger.warning(
            f"No user found for subscription delete: customer={customer_id}")
        return

    # Downgrade to FREE
    supabase_admin.update_entitlements(user_id, {
        'plan': 'FREE',
        'status': 'canceled',
        'stripe_subscription_id': None,
        'current_period_end': None,
        'daily_requests_limit': 10,
    })

    logger.info(f"Subscription deleted: user={user_id}")


def _get_plan_from_subscription(subscription: dict) -> str:
    """Determine plan type from Stripe subscription."""
    items = subscription.get('items', {}).get('data', [])
    if not items:
        return 'FREE'

    price_id = items[0].get('price', {}).get('id', '')

    monthly_price_id = os.environ.get('STRIPE_PRICE_MONTHLY_ID', '')
    yearly_price_id = os.environ.get('STRIPE_PRICE_YEARLY_ID', '')

    if price_id == yearly_price_id:
        return 'YEARLY'
    elif price_id == monthly_price_id:
        return 'MONTHLY'
    else:
        # Check interval as fallback
        interval = items[0].get('price', {}).get(
            'recurring', {}).get('interval', '')
        if interval == 'year':
            return 'YEARLY'
        elif interval == 'month':
            return 'MONTHLY'

    return 'MONTHLY'  # Default


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Default port 8501 to match frontend config
    port = int(os.environ.get("PORT", 8501))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
