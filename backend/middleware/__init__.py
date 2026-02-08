"""
Professional-grade middleware modules for MarketGPS backend.

This package provides:
- webhook_guard: Stripe webhook replay attack prevention
- input_validator: Request validation and injection prevention
- request_logger: Structured JSON logging with request tracking
- error_handler: Centralized exception handling with correlation
- rate_limiter: Sliding window rate limiting with configurable tiers
"""

from .webhook_guard import (
    WebhookGuard,
    get_webhook_guard,
    verify_webhook_not_replayed,
    is_event_processed,
    mark_event_processed,
    cleanup_old_events,
)
from .input_validator import InputValidationMiddleware
from .request_logger import RequestLoggingMiddleware
from .error_handler import GlobalErrorHandlerMiddleware, ErrorHandlerConfig
from .rate_limiter import (
    RateLimitMiddleware,
    RateLimiter,
    RateLimitTier,
    RateLimitMetrics,
)

__all__ = [
    "WebhookGuard",
    "get_webhook_guard",
    "verify_webhook_not_replayed",
    "is_event_processed",
    "mark_event_processed",
    "cleanup_old_events",
    "InputValidationMiddleware",
    "RequestLoggingMiddleware",
    "GlobalErrorHandlerMiddleware",
    "ErrorHandlerConfig",
    "RateLimitMiddleware",
    "RateLimiter",
    "RateLimitTier",
    "RateLimitMetrics",
]
