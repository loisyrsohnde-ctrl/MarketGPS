"""
MarketGPS Prometheus Monitoring
Exposes /metrics endpoint for Grafana dashboards.
Uses prometheus_client library if available, graceful no-op fallback otherwise.
"""

import time
import re
from typing import Callable, Optional
from functools import wraps
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

# Try to import prometheus_client; graceful fallback if not available
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # No-op stubs for graceful fallback
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def observe(self, *args, **kwargs):
            pass
        def time(self):
            class NoOpTimer:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return NoOpTimer()

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def set(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass

    def generate_latest(*args, **kwargs):
        return b"# Prometheus client not installed\n"

    CONTENT_TYPE_LATEST = "text/plain; charset=utf-8"
    CollectorRegistry = None


# ═══════════════════════════════════════════════════════════════════════════════
# PROMETHEUS METRICS REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

if PROMETHEUS_AVAILABLE:
    registry = CollectorRegistry()
else:
    registry = None


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP REQUEST METRICS
# ═══════════════════════════════════════════════════════════════════════════════

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
    registry=registry if PROMETHEUS_AVAILABLE else None
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING METRICS
# ═══════════════════════════════════════════════════════════════════════════════

scoring_operations_total = Counter(
    'scoring_operations_total',
    'Total scoring operations',
    ['scope', 'asset_type', 'status'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)

scoring_duration_seconds = Histogram(
    'scoring_duration_seconds',
    'Scoring operation duration in seconds',
    ['scope'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE METRICS
# ═══════════════════════════════════════════════════════════════════════════════

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE METRICS
# ═══════════════════════════════════════════════════════════════════════════════

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# USER METRICS
# ═══════════════════════════════════════════════════════════════════════════════

active_users_gauge = Gauge(
    'active_users_gauge',
    'Current active users',
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# WEBHOOK METRICS
# ═══════════════════════════════════════════════════════════════════════════════

webhook_events_total = Counter(
    'webhook_events_total',
    'Total webhook events',
    ['event_type', 'status'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMIT METRICS
# ═══════════════════════════════════════════════════════════════════════════════

rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR METRICS
# ═══════════════════════════════════════════════════════════════════════════════

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type'],
    registry=registry if PROMETHEUS_AVAILABLE else None
)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_endpoint_path(path: str) -> str:
    """
    Normalize endpoint paths to prevent metric explosion.
    e.g., /api/assets/AAPL.US → /api/assets/{ticker}
    """
    # Replace UUID-like patterns
    path = re.sub(r'[a-f0-9\-]{36}', '{id}', path)

    # Replace numeric IDs (but not single digits at end)
    path = re.sub(r'/\d{2,}(?=/|$)', '/{id}', path)

    # Replace ticker patterns (e.g., AAPL.US, DANGOTE.NG)
    path = re.sub(r'/[A-Z0-9]+\.[A-Z]{2}(?=/|$)', '/{ticker}', path)

    return path


def record_scoring(scope: str, asset_type: str, status: str) -> None:
    """Record a scoring operation."""
    scoring_operations_total.labels(scope=scope, asset_type=asset_type, status=status).inc()


def record_scoring_duration(scope: str, duration: float) -> None:
    """Record scoring operation duration."""
    scoring_duration_seconds.labels(scope=scope).observe(duration)


def record_cache_hit(cache_type: str) -> None:
    """Record a cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record a cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_db_query(operation: str, table: str, duration: float) -> None:
    """Record a database query."""
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)


def record_webhook(event_type: str, status: str) -> None:
    """Record a webhook event."""
    webhook_events_total.labels(event_type=event_type, status=status).inc()


def record_rate_limit(endpoint: str) -> None:
    """Record a rate limit hit."""
    rate_limit_hits_total.labels(endpoint=endpoint).inc()


def record_api_error(endpoint: str, error_type: str) -> None:
    """Record an API error."""
    api_errors_total.labels(endpoint=endpoint, error_type=error_type).inc()


def set_active_users(count: int) -> None:
    """Set the number of active users."""
    active_users_gauge.set(count)


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

async def metrics_endpoint(request: Request) -> Response:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    if not PROMETHEUS_AVAILABLE:
        return PlainTextResponse(
            "# Prometheus client not installed\n",
            media_type="text/plain; charset=utf-8"
        )

    try:
        metrics_data = generate_latest(registry)
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        return PlainTextResponse(
            f"# Error generating metrics: {str(e)}\n",
            media_type="text/plain; charset=utf-8",
            status_code=500
        )


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for collecting HTTP metrics.
    Records request count, duration, and in-progress for every request.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and record metrics."""
        method = request.method
        path = request.url.path
        endpoint = normalize_endpoint_path(path)

        # Record in-progress request
        http_requests_in_progress.labels(method=method).inc()

        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            # Record error metric
            error_type = type(e).__name__
            record_api_error(endpoint, error_type)
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method).dec()

        return response
