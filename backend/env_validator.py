"""
MarketGPS - Environment Variable Validator

Validates that all required environment variables are set at startup.
In production (ENV=production), missing critical variables cause a fatal error.
In development, warnings are logged but the app still starts.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

# Variables required in ALL environments
REQUIRED_ALWAYS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
]

# Variables required in production only
REQUIRED_PRODUCTION = [
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_JWT_SECRET",
    "ADMIN_KEY",
    "INTERNAL_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
]

# Variables that should never have default/placeholder values in production
MUST_NOT_BE_PLACEHOLDER = {
    "ADMIN_KEY": ["marketgps-admin-2024", "admin", "changeme", "secret"],
    "INTERNAL_API_KEY": ["mgps-internal-pipeline-2026", "changeme", "secret"],
}


def is_production() -> bool:
    """Check if we're running in production."""
    env = os.environ.get("ENV", "").lower()
    app_env = os.environ.get("APP_ENV", "").lower()
    return env in ("prod", "production") or app_env in ("prod", "production")


def validate_env() -> bool:
    """
    Validate environment variables.

    Returns True if all checks pass.
    In production, raises SystemExit on critical failures.
    In development, logs warnings and returns True.
    """
    errors = []
    warnings = []
    prod = is_production()

    # Check always-required variables
    for var in REQUIRED_ALWAYS:
        value = os.environ.get(var, "")
        if not value:
            errors.append(f"Missing required variable: {var}")

    # Check production-required variables
    if prod:
        for var in REQUIRED_PRODUCTION:
            value = os.environ.get(var, "")
            if not value:
                errors.append(f"Missing production variable: {var}")
    else:
        for var in REQUIRED_PRODUCTION:
            value = os.environ.get(var, "")
            if not value:
                warnings.append(f"Missing variable (optional in dev): {var}")

    # Check for placeholder values in production
    if prod:
        for var, placeholders in MUST_NOT_BE_PLACEHOLDER.items():
            value = os.environ.get(var, "")
            if value.lower() in [p.lower() for p in placeholders]:
                errors.append(
                    f"{var} has a placeholder value - set a secure value in production"
                )

    # Report
    for w in warnings:
        logger.warning(f"[ENV] {w}")

    if errors:
        for e in errors:
            logger.error(f"[ENV] {e}")

        if prod:
            logger.critical(
                "[ENV] Fatal: Missing required environment variables in production. "
                "Set all required variables and restart."
            )
            sys.exit(1)
        else:
            logger.warning(
                f"[ENV] {len(errors)} issue(s) found - acceptable in development mode"
            )

    if not errors and not warnings:
        logger.info("[ENV] All environment variables validated successfully")

    return len(errors) == 0
