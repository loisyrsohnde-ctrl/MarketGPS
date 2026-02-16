"""
Example integration of RateLimitMiddleware into FastAPI application.

This file demonstrates how to integrate the rate limiting middleware
into an existing FastAPI application (main.py).

Copy relevant sections into your main.py file.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import the rate limiting middleware
from middleware import RateLimitMiddleware, RateLimitTier


def setup_rate_limiting(app: FastAPI) -> RateLimitMiddleware:
    """
    Set up rate limiting middleware for the FastAPI application.

    This should be called early in the application initialization,
    before other middleware is added.

    Args:
        app: FastAPI application instance

    Returns:
        RateLimitMiddleware instance for additional configuration
    """
    # Initialize rate limiting middleware
    # Configuration is read from environment variables
    rate_limiter = RateLimitMiddleware(
        app,
        enabled=True,  # Can also be controlled via RATE_LIMIT_ENABLED env var
        default_limit=120,  # Can also be controlled via RATE_LIMIT_DEFAULT env var
        window_size=60,  # Can also be controlled via RATE_LIMIT_WINDOW env var
        cleanup_interval=300,  # Can also be controlled via RATE_LIMIT_CLEANUP_INTERVAL env var
    )

    # Register custom tiers beyond the defaults
    # (defaults are AUTH, SEARCH, BACKTEST, WRITE)

    # Example: Add a stricter tier for internal admin endpoints
    rate_limiter.register_tier(
        RateLimitTier(
            name="admin",
            requests_per_minute=50,
            patterns=["/api/admin/", "/admin/"],
        )
    )

    # Example: Add a more lenient tier for data export endpoints
    rate_limiter.register_tier(
        RateLimitTier(
            name="exports",
            requests_per_minute=20,
            patterns=["/api/export/", "/api/download/"],
        )
    )

    # Example: Add a very strict tier for sensitive operations
    rate_limiter.register_tier(
        RateLimitTier(
            name="sensitive",
            requests_per_minute=5,
            patterns=["/api/user/profile/delete", "/api/account/close"],
        )
    )

    return rate_limiter


def setup_admin_endpoints(app: FastAPI, rate_limiter: RateLimitMiddleware) -> None:
    """
    Set up admin endpoints to monitor rate limiting metrics.

    These endpoints should be protected by authentication in production.

    Args:
        app: FastAPI application instance
        rate_limiter: RateLimitMiddleware instance
    """

    @app.get("/api/admin/metrics/rate-limit")
    async def get_rate_limit_metrics():
        """
        Get current rate limiting metrics.

        Protected endpoint - should require admin authentication.
        Returns comprehensive statistics about rate limiting activity.
        """
        return {
            "service": "rate-limiter",
            "metrics": rate_limiter.get_metrics(),
        }

    @app.post("/api/admin/rate-limit/reset")
    async def reset_rate_limit_metrics():
        """
        Reset all rate limiting metrics.

        Protected endpoint - should require admin authentication.
        Useful for testing and resetting after maintenance.
        """
        rate_limiter.reset_metrics()
        return {"status": "metrics_reset", "timestamp": str(rate_limiter.get_metrics())}

    @app.get("/api/admin/rate-limit/config")
    async def get_rate_limit_config():
        """
        Get current rate limiting configuration.

        Protected endpoint - should require admin authentication.
        Shows all registered tiers and their limits.
        """
        tiers = {}
        for name, tier in rate_limiter.limiter.tiers.items():
            tiers[name] = {
                "name": tier.name,
                "requests_per_minute": tier.requests_per_minute,
                "patterns": tier.patterns,
            }

        return {
            "enabled": rate_limiter.enabled,
            "default_limit": rate_limiter.limiter.default_limit,
            "window_size": rate_limiter.limiter.window_size,
            "cleanup_interval": rate_limiter.limiter.cleanup_interval,
            "tiers": tiers,
        }


# ============================================================================
# Example usage in main.py
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with rate limiting.

    This is how to integrate into your existing main.py.
    """
    app = FastAPI(
        title="MarketGPS API",
        description="Institutional-grade market analysis platform",
        version="1.0.0",
    )

    # Set up rate limiting FIRST (before other middleware)
    # This ensures rate limiting is evaluated early in the request chain
    rate_limiter = setup_rate_limiting(app)

    # Add other middleware after rate limiting
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8080",
            "https://marketgps.io",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "127.0.0.1",
            "marketgps.io",
            "*.marketgps.io",
        ],
    )

    # Set up admin endpoints for monitoring
    setup_admin_endpoints(app, rate_limiter)

    # Health check endpoint (never rate limited)
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "markerGPS-api",
            "rate_limiting": "enabled" if rate_limiter.enabled else "disabled",
        }

    # Your existing routes would go here
    # @app.get("/api/assets/search")
    # @app.post("/api/backtest/run")
    # etc.

    return app


# ============================================================================
# Environment Variables Reference
# ============================================================================

"""
Set these environment variables to configure rate limiting:

# Enable/disable rate limiting globally
RATE_LIMIT_ENABLED=true

# Default rate limit for unmatched endpoints (requests per minute)
RATE_LIMIT_DEFAULT=120

# Rate limit window in seconds (typically 60)
RATE_LIMIT_WINDOW=60

# How often to clean up stale entries (seconds, typically 300)
RATE_LIMIT_CLEANUP_INTERVAL=300

# Tier-specific rate limits (requests per minute)
RATE_LIMIT_AUTH=10          # /api/auth/*, /billing/*
RATE_LIMIT_SEARCH=60        # /api/assets/search
RATE_LIMIT_BACKTEST=5       # /api/backtest/*
RATE_LIMIT_WRITE=30         # POST/PUT/DELETE endpoints

Example .env file:
---
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=120
RATE_LIMIT_WINDOW=60
RATE_LIMIT_CLEANUP_INTERVAL=300
RATE_LIMIT_AUTH=10
RATE_LIMIT_SEARCH=60
RATE_LIMIT_BACKTEST=5
RATE_LIMIT_WRITE=30
---
"""

# ============================================================================
# Testing the Rate Limiter
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    app = create_app()

    # Run with: python RATE_LIMITER_INTEGRATION_EXAMPLE.py
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for testing
    )

    # Test endpoints:
    # 1. Health check: curl http://localhost:8000/health
    # 2. Check metrics: curl http://localhost:8000/api/admin/metrics/rate-limit
    # 3. Check config: curl http://localhost:8000/api/admin/rate-limit/config
    # 4. Simulate rate limit by hitting an endpoint 120+ times in 60 seconds
