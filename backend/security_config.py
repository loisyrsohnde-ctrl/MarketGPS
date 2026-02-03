"""
Security Configuration for MarketGPS Backend
Centralized management of CORS, headers, and security settings
"""

import os
from typing import List

# ============================================================================
# CORS Configuration
# ============================================================================

DEFAULT_ALLOWED_ORIGINS: List[str] = [
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

# Allowed HTTP methods
ALLOWED_METHODS: List[str] = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

# Allowed headers in requests
ALLOWED_REQUEST_HEADERS: List[str] = [
    "Content-Type",
    "Authorization",
    "Accept",
    "Origin",
    "X-Requested-With",
    "X-CSRF-Token",
    "Stripe-Signature",
]

# Headers to expose to clients
EXPOSED_HEADERS: List[str] = [
    "Content-Range",
    "X-Content-Range",
    "X-Total-Count",
]

# Preflight cache duration in seconds
CORS_MAX_AGE: int = 3600  # 1 hour

# ============================================================================
# Security Headers Configuration
# ============================================================================

# X-Content-Type-Options: Prevents MIME type sniffing (nosniff recommended)
CONTENT_TYPE_OPTIONS: str = "nosniff"

# X-Frame-Options: Prevent clickjacking (DENY, SAMEORIGIN, or ALLOW-FROM)
# DENY: Prevents page from being displayed in a frame at all
FRAME_OPTIONS: str = "DENY"

# X-XSS-Protection: Legacy header for older browser XSS filters
# Format: "1; mode=block" enables filter and blocks page if XSS detected
XSS_PROTECTION: str = "1; mode=block"

# Strict-Transport-Security: Enforce HTTPS
# max-age: Time in seconds HSTS is enforced (1 year = 31536000)
# includeSubDomains: Apply policy to all subdomains
# preload: Allow inclusion in HSTS preload list (optional, requires special submission)
HSTS_HEADER: str = "max-age=31536000; includeSubDomains"

# Content-Security-Policy: Restrict resource loading to prevent XSS/injection
# default-src 'self': Only allow resources from same origin by default
# script-src: Allow scripts from same origin
# style-src: Allow styles from same origin and unsafe-inline (for Streamlit)
# img-src: Allow images from same origin, data URIs, and HTTPS
# connect-src: Allow connections to same origin and HTTPS endpoints
# frame-ancestors 'none': Prevent embedding in frames
CSP_HEADER: str = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

# Referrer-Policy: Control what referrer information is sent
# strict-origin-when-cross-origin: Send origin for same-site, nothing for cross-site
REFERRER_POLICY: str = "strict-origin-when-cross-origin"

# Permissions-Policy: Control which browser features can be used
# Format: "feature=(allowlist)"
PERMISSIONS_POLICY: str = (
    "accelerometer=(), "
    "camera=(), "
    "geolocation=(), "
    "gyroscope=(), "
    "magnetometer=(), "
    "microphone=(), "
    "payment=(), "
    "usb=()"
)


def get_allowed_origins() -> List[str]:
    """
    Get list of allowed CORS origins.
    Combines default origins with any specified in CORS_ORIGINS environment variable.

    Environment Variable:
        CORS_ORIGINS: Comma-separated list of additional allowed origins
        Example: "https://custom.domain.com,https://another.domain.com"

    Returns:
        List of allowed origin URLs
    """
    origins = DEFAULT_ALLOWED_ORIGINS.copy()

    # Add extra origins from environment variable (comma-separated)
    env_origins = os.environ.get("CORS_ORIGINS", "")
    if env_origins:
        extra_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
        origins.extend(extra_origins)

    # Remove duplicates while preserving order
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)

    return unique_origins
