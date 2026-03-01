"""
MarketGPS Backend API v15.0
FastAPI server with institutional-grade middleware stack.

Middleware order (outermost → innermost):
  1. GlobalErrorHandlerMiddleware  – catches all unhandled exceptions
  2. RequestLoggingMiddleware      – structured JSON logging + X-Request-ID
  3. RateLimitMiddleware           – sliding-window per-IP rate limiting
  4. InputValidationMiddleware     – body size, query length, injection detection
  5. SecurityHeadersMiddleware     – OWASP security headers
  6. CORSMiddleware                – cross-origin resource sharing
"""

import os
import logging
import json
from typing import Optional
from contextlib import asynccontextmanager

# CRITICAL: Load environment variables BEFORE any other imports
# that might depend on them (SQLite path, etc.)
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory (where this file is located)
_env_file = Path(__file__).parent / ".env"
load_dotenv(_env_file)

# Validate environment variables early (before any service initialization)
from env_validator import validate_env
validate_env()

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Route imports
from api_routes import router as api_router
from user_routes import router as user_router
from barbell_routes import router as barbell_router
from strategies_routes import router as strategies_router
from backtest_routes import router as backtest_router
from news_routes import router as news_router
from billing_routes import router as billing_router
from feedback_routes import router as feedback_router
from admin_routes import router as admin_router
from news_admin_routes import router as news_admin_router
from real_estate_routes import router as real_estate_router
from wealth_routes import router as wealth_router
from concierge_routes import router as concierge_router
from notifications_routes import router as notifications_router
from portfolio_routes import router as portfolio_router
from gamification_routes import router as gamification_router
from viral_news_routes import router as viral_news_router
from admin_news_api import router as admin_news_router
from academy_routes import router as academy_router
from article_video_routes import router as article_video_router
# Optional admin add-on services (safe import - each loaded independently)
admin_search_router = None
admin_settings_router = None
admin_workflow_router = None
try:
    from admin_search_service import router as admin_search_router
except Exception as e:
    print(f"[WARNING] Admin search service failed to import: {e}")
try:
    from admin_settings_service import router as admin_settings_router
except Exception as e:
    print(f"[WARNING] Admin settings service failed to import: {e}")
try:
    from admin_workflow_service import router as admin_workflow_router
except Exception as e:
    print(f"[WARNING] Admin workflow service failed to import: {e}")

# Middleware imports (v15 institutional stack)
from middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    GlobalErrorHandlerMiddleware,
    InputValidationMiddleware,
)

# Configure structured logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
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
    Creates user_strategies, user_strategy_compositions, and gamification tables if missing.
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

            # Create gamification tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_gamification (
                    user_id TEXT PRIMARY KEY,
                    total_points INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_streak INTEGER DEFAULT 0,
                    longest_streak INTEGER DEFAULT 0,
                    last_activity_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_badges (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    badge_id TEXT NOT NULL,
                    earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, badge_id),
                    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_objectives (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    objective_type TEXT NOT NULL DEFAULT 'weekly',
                    title TEXT NOT NULL,
                    description TEXT,
                    action TEXT NOT NULL,
                    target INTEGER NOT NULL,
                    current INTEGER DEFAULT 0,
                    points_reward INTEGER NOT NULL,
                    expires_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_actions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    metadata_json TEXT,
                    points_earned INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
                )
            """)

            # Create gamification indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_badges_badge_id ON user_badges(badge_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_objectives_user_id ON user_objectives(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_objectives_type ON user_objectives(objective_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_objectives_completed ON user_objectives(completed_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_date ON user_actions(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_actions_user_date ON user_actions(user_id, created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_gamification_points ON user_gamification(total_points DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_gamification_level ON user_gamification(current_level DESC)")

            conn.commit()

        logger.info("✅ All required tables verified/created (including gamification)")

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


import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting MarketGPS Backend API...")

    # Initialize database schema on startup
    try:
        from db_init import initialize_database
        initialize_database()
        logger.info("✓ Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

    # Run seed in background to not block startup
    asyncio.create_task(run_startup_seed())

    yield
    logger.info("Shutting down MarketGPS Backend API...")

async def run_startup_seed():
    """Wrapper to run seed in async loop"""
    await asyncio.sleep(5)  # Wait for server to be fully up
    try:
        # Run synchronous seed function in thread pool
        await asyncio.to_thread(startup_seed)
    except Exception as e:
        logger.error(f"Background seed failed: {e}")


# Create FastAPI app
app = FastAPI(
    title="MarketGPS API",
    description=(
        "Institutional-grade financial intelligence platform.\n\n"
        "MarketGPS provides quantitative scoring, portfolio analytics, "
        "strategy building, and market news — all behind a secure, "
        "rate-limited API with Supabase JWT authentication.\n\n"
        "## Authentication\n"
        "Most endpoints require a **Bearer** token obtained from Supabase Auth. "
        "Pass it via the `Authorization: Bearer <token>` header.\n\n"
        "## Rate Limits\n"
        "Free tier: **10 requests/day** | Pro tier: **200 requests/day**\n\n"
        "## Base URL\n"
        "`https://api.marketgps.online`"
    ),
    version="15.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "Server health and readiness checks"},
        {"name": "Assets", "description": "Asset search, scores, explorer, and market data"},
        {"name": "Strategies", "description": "Investment strategy templates and compositions"},
        {"name": "Barbell Strategy", "description": "Barbell portfolio construction (core + satellite)"},
        {"name": "Portfolio", "description": "Portfolio accounts, positions, and CSV import"},
        {"name": "News", "description": "Market news articles and sentiment"},
        {"name": "Billing", "description": "Stripe checkout, portal, and subscription management"},
        {"name": "Users", "description": "User profile and preferences"},
        {"name": "Notifications", "description": "User alerts and notification preferences"},
        {"name": "Gamification", "description": "Points, badges, streaks, and leaderboards"},
        {"name": "AI Concierge", "description": "AI-powered investment assistant"},
        {"name": "Backtest", "description": "Historical strategy backtesting"},
        {"name": "Feedback", "description": "User feedback and feature requests"},
        {"name": "Admin Dashboard", "description": "Admin-only endpoints (requires X-Admin-Key)"},
        {"name": "Admin News", "description": "Admin news pipeline management"},
    ],
    contact={
        "name": "MarketGPS Team",
        "url": "https://marketgps.online",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Import security configuration
from security_config import (
    get_allowed_origins,
    ALLOWED_METHODS,
    ALLOWED_REQUEST_HEADERS,
    EXPOSED_HEADERS,
    CORS_MAX_AGE,
    CONTENT_TYPE_OPTIONS,
    FRAME_OPTIONS,
    XSS_PROTECTION,
    HSTS_HEADER,
    CSP_HEADER,
    REFERRER_POLICY,
    PERMISSIONS_POLICY,
)

# Get CORS configuration
ALLOWED_ORIGINS = get_allowed_origins()

# ============================================================================
# Middleware Stack (order: last added = outermost = runs first)
# ============================================================================

# 6. CORS (innermost - runs last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_REQUEST_HEADERS,
    expose_headers=EXPOSED_HEADERS,
    max_age=CORS_MAX_AGE,
)


# 5. Security Headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP-compliant security headers for all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = CONTENT_TYPE_OPTIONS
        response.headers["X-Frame-Options"] = FRAME_OPTIONS
        response.headers["X-XSS-Protection"] = XSS_PROTECTION
        response.headers["Strict-Transport-Security"] = HSTS_HEADER
        response.headers["Content-Security-Policy"] = CSP_HEADER
        response.headers["Referrer-Policy"] = REFERRER_POLICY
        response.headers["Permissions-Policy"] = PERMISSIONS_POLICY
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 4. Input Validation (body size, query length, injection detection)
app.add_middleware(InputValidationMiddleware)

# 3. Rate Limiting (sliding window per-IP)
app.add_middleware(RateLimitMiddleware)

# 2. Structured Request Logging (JSON format + X-Request-ID)
app.add_middleware(RequestLoggingMiddleware)

# 1. Global Error Handler (outermost - catches everything)
app.add_middleware(GlobalErrorHandlerMiddleware)

# Include API routes for assets/scores/watchlist
app.include_router(api_router)
app.include_router(user_router)
app.include_router(barbell_router)  # Barbell strategy module (ADD-ON)
app.include_router(strategies_router)  # Strategies module (ADD-ON)
app.include_router(backtest_router)  # Backtesting module (ADD-ON)
app.include_router(news_router)  # News/Actualités module (ADD-ON)
app.include_router(billing_router)  # Stripe billing module v13 (ADD-ON)
app.include_router(feedback_router)  # Feedback system (ADD-ON)
app.include_router(admin_router)  # Admin dashboard (READ-ONLY, ADD-ON)
app.include_router(news_admin_router)  # News scraping admin (ADD-ON)
app.include_router(real_estate_router)  # Real Estate module (ADD-ON)
app.include_router(wealth_router)  # Wealth Agent module (ADD-ON)
app.include_router(concierge_router)  # AI Concierge module (ADD-ON)
app.include_router(gamification_router)  # Gamification system (ADD-ON)
app.include_router(notifications_router)  # Notifications & Alerts (ADD-ON)
app.include_router(portfolio_router)  # Portfolio Sync (ADD-ON) - Read-only, no trading
app.include_router(viral_news_router)  # Viral news & video scripts (ADD-ON)
app.include_router(admin_news_router)  # Unified admin news API (ADD-ON)
app.include_router(academy_router)  # Academy video streaming + admin (ADD-ON)
app.include_router(article_video_router)  # Article video upload + streaming
# Admin add-on services (conditionally loaded)
if admin_search_router:
    app.include_router(admin_search_router)
if admin_settings_router:
    app.include_router(admin_settings_router)
if admin_workflow_router:
    app.include_router(admin_workflow_router)


# ============================================================================
# Request/Response Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    version: str


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint. Returns 200 if the server is running."""
    return {"status": "healthy", "version": "15.0.0"}


@app.get("/health/extended", tags=["Health"])
async def health_check_extended():
    """
    Extended health check with database connectivity and service status.
    Returns asset/news counts and service availability flags.
    """
    from storage.sqlite_store import SQLiteStore
    
    result = {
        "status": "healthy",
        "version": "15.0.0",
        "timestamp": datetime.utcnow().isoformat() if 'datetime' in dir() else None,
        "database": {"connected": False},
        "services": {
            "stripe": stripe_service is not None,
            "supabase": supabase_admin is not None,
        },
    }
    
    try:
        from datetime import datetime
        result["timestamp"] = datetime.utcnow().isoformat()
        
        db = SQLiteStore()
        with db._get_conn() as conn:
            # Test connection
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            result["database"]["connected"] = True
            
            # Quick counts
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM universe WHERE active=1")
                result["database"]["active_assets"] = cursor.fetchone()[0]
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error counting active assets: {e}")
            
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM scores_latest WHERE score_total IS NOT NULL")
                result["database"]["scored_assets"] = cursor.fetchone()[0]
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error counting scored assets: {e}")
            
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM news_articles")
                result["database"]["news_articles"] = cursor.fetchone()[0]
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                logger.debug(f"Error counting news articles: {e}")
                result["database"]["news_articles"] = 0
                
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        result["database"]["error"] = "connection_failed"
    
    return result


# ============================================================================
# Billing: All billing endpoints are handled by billing_routes.py
# Webhook URL: POST /api/billing/stripe/webhook
# Checkout:    POST /api/billing/checkout-session
# Status:      GET  /api/billing/me
# Portal:      POST /api/billing/portal-session
# ============================================================================


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
