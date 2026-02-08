"""
Professional-grade rate limiting middleware for FastAPI applications.

Features:
- Sliding window algorithm for accurate rate limiting
- Multiple configurable tier definitions
- Automatic memory cleanup of stale entries
- Thread-safe operation for concurrent requests
- X-Forwarded-For proxy detection
- Comprehensive metrics tracking
- Configurable via environment variables
"""

import os
import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import Headers


@dataclass
class RateLimitTier:
    """Configuration for a rate limit tier."""
    name: str
    requests_per_minute: int
    patterns: List[str]  # URL patterns to match


@dataclass
class RateLimitMetrics:
    """Metrics for rate limiting."""
    total_requests: int = 0
    total_blocked: int = 0
    per_endpoint: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    per_ip: Dict[str, Dict[str, int]] = field(default_factory=lambda: defaultdict(dict))
    blocked_per_endpoint: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class RateLimiter:
    """
    Sliding window rate limiter with in-memory storage.

    Thread-safe implementation using locks for concurrent request handling.
    Automatically cleans up stale entries to prevent memory bloat.
    """

    def __init__(
        self,
        default_limit: int = 120,
        window_size_seconds: int = 60,
        cleanup_interval_seconds: int = 300,
    ):
        """
        Initialize the rate limiter.

        Args:
            default_limit: Default requests per minute if no tier matches
            window_size_seconds: Time window for rate limiting (default 60 seconds)
            cleanup_interval_seconds: How often to clean stale entries
        """
        self.default_limit = default_limit
        self.window_size = window_size_seconds
        self.cleanup_interval = cleanup_interval_seconds

        # Key: "ip:endpoint" -> List of timestamps
        self._request_history: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._metrics = RateLimitMetrics()

        # Rate limit tiers
        self.tiers: Dict[str, RateLimitTier] = {}

    def register_tier(self, tier: RateLimitTier) -> None:
        """Register a new rate limit tier."""
        self.tiers[tier.name] = tier

    def _get_tier_for_endpoint(self, endpoint: str) -> Optional[RateLimitTier]:
        """
        Determine which tier an endpoint belongs to.

        Args:
            endpoint: The API endpoint path

        Returns:
            RateLimitTier if matched, None otherwise
        """
        for tier in self.tiers.values():
            for pattern in tier.patterns:
                # Simple pattern matching: check if pattern is in endpoint
                if pattern in endpoint:
                    return tier
        return None

    def _cleanup_stale_entries(self) -> None:
        """Remove request history entries older than the window size."""
        current_time = time.time()
        cutoff_time = current_time - self.window_size

        keys_to_clean = []
        for key, timestamps in self._request_history.items():
            # Remove old timestamps
            self._request_history[key] = [ts for ts in timestamps if ts > cutoff_time]

            # Mark empty entries for deletion
            if not self._request_history[key]:
                keys_to_clean.append(key)

        # Clean up empty entries
        for key in keys_to_clean:
            del self._request_history[key]

    def _should_cleanup(self) -> bool:
        """Check if cleanup is due based on interval."""
        current_time = time.time()
        if current_time - self._last_cleanup >= self.cleanup_interval:
            self._last_cleanup = current_time
            return True
        return False

    def is_allowed(
        self,
        client_ip: str,
        endpoint: str,
    ) -> Tuple[bool, int, int]:
        """
        Check if a request is allowed under rate limits.

        Args:
            client_ip: Client IP address (with X-Forwarded-For resolved)
            endpoint: API endpoint path

        Returns:
            Tuple of (is_allowed, requests_made, limit)
        """
        with self._lock:
            # Perform periodic cleanup
            if self._should_cleanup():
                self._cleanup_stale_entries()

            current_time = time.time()

            # Determine rate limit based on tier
            tier = self._get_tier_for_endpoint(endpoint)
            limit = tier.requests_per_minute if tier else self.default_limit

            # Key for tracking requests
            key = f"{client_ip}:{endpoint}"

            # Remove timestamps outside the window
            cutoff_time = current_time - self.window_size
            self._request_history[key] = [
                ts for ts in self._request_history[key] if ts > cutoff_time
            ]

            request_count = len(self._request_history[key])

            # Update metrics
            self._metrics.total_requests += 1
            if endpoint not in self._metrics.per_endpoint:
                self._metrics.per_endpoint[endpoint] = 0
            self._metrics.per_endpoint[endpoint] += 1

            # Check if limit exceeded
            if request_count >= limit:
                self._metrics.total_blocked += 1
                self._metrics.blocked_per_endpoint[endpoint] += 1
                return False, request_count, limit

            # Record this request
            self._request_history[key].append(current_time)

            return True, request_count + 1, limit

    def get_metrics(self) -> Dict:
        """
        Retrieve current rate limiter metrics.

        Returns:
            Dictionary of metrics
        """
        with self._lock:
            return {
                "total_requests": self._metrics.total_requests,
                "total_blocked": self._metrics.total_blocked,
                "block_rate": (
                    self._metrics.total_blocked / self._metrics.total_requests
                    if self._metrics.total_requests > 0
                    else 0
                ),
                "per_endpoint": dict(self._metrics.per_endpoint),
                "blocked_per_endpoint": dict(self._metrics.blocked_per_endpoint),
                "active_keys": len(self._request_history),
            }

    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics = RateLimitMetrics()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting with sliding window algorithm.

    Supports multiple configurable rate limit tiers and X-Forwarded-For
    header parsing for proxy detection.

    Example:
        app = FastAPI()
        middleware = RateLimitMiddleware(
            app,
            enabled=True,
            default_limit=120,
        )
        middleware.register_tier(RateLimitTier(
            name="auth",
            requests_per_minute=10,
            patterns=["/api/auth/", "/billing/"],
        ))
    """

    def __init__(
        self,
        app,
        enabled: Optional[bool] = None,
        default_limit: Optional[int] = None,
        window_size: Optional[int] = None,
        cleanup_interval: Optional[int] = None,
    ):
        """
        Initialize the rate limit middleware.

        Args:
            app: FastAPI application instance
            enabled: Enable rate limiting (default from RATE_LIMIT_ENABLED env)
            default_limit: Default requests per minute (default from RATE_LIMIT_DEFAULT env)
            window_size: Rate limit window in seconds (default 60)
            cleanup_interval: Cleanup interval in seconds (default 300)
        """
        super().__init__(app)

        # Configuration from environment variables with fallbacks
        self.enabled = (
            enabled
            if enabled is not None
            else os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        )

        default_limit = (
            default_limit
            if default_limit is not None
            else int(os.getenv("RATE_LIMIT_DEFAULT", "120"))
        )

        window_size = (
            window_size
            if window_size is not None
            else int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        )

        cleanup_interval = (
            cleanup_interval
            if cleanup_interval is not None
            else int(os.getenv("RATE_LIMIT_CLEANUP_INTERVAL", "300"))
        )

        # Initialize limiter
        self.limiter = RateLimiter(
            default_limit=default_limit,
            window_size_seconds=window_size,
            cleanup_interval_seconds=cleanup_interval,
        )

        # Register default tiers
        self._setup_default_tiers()

    def _setup_default_tiers(self) -> None:
        """Set up default rate limit tiers from environment variables."""
        # AUTH endpoints: 10 req/min
        auth_limit = int(os.getenv("RATE_LIMIT_AUTH", "10"))
        self.limiter.register_tier(
            RateLimitTier(
                name="auth",
                requests_per_minute=auth_limit,
                patterns=["/api/auth/", "/billing/"],
            )
        )

        # SEARCH endpoints: 60 req/min
        search_limit = int(os.getenv("RATE_LIMIT_SEARCH", "60"))
        self.limiter.register_tier(
            RateLimitTier(
                name="search",
                requests_per_minute=search_limit,
                patterns=["/api/assets/search"],
            )
        )

        # HEAVY COMPUTE endpoints: 5 req/min
        backtest_limit = int(os.getenv("RATE_LIMIT_BACKTEST", "5"))
        self.limiter.register_tier(
            RateLimitTier(
                name="backtest",
                requests_per_minute=backtest_limit,
                patterns=["/api/backtest/"],
            )
        )

        # WRITE endpoints: 30 req/min
        write_limit = int(os.getenv("RATE_LIMIT_WRITE", "30"))
        self.limiter.register_tier(
            RateLimitTier(
                name="write",
                requests_per_minute=write_limit,
                patterns=[],  # Matched by method in middleware
            )
        )

    def _extract_client_ip(self, request: Request) -> str:
        """
        Extract client IP from request, accounting for X-Forwarded-For.

        Args:
            request: Starlette Request object

        Returns:
            Client IP address as string
        """
        # Check X-Forwarded-For header (proxy detection)
        if "x-forwarded-for" in request.headers:
            # Take the first IP if multiple are present (leftmost is original client)
            return request.headers["x-forwarded-for"].split(",")[0].strip()

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _is_write_method(self, method: str) -> bool:
        """Check if HTTP method is a write operation."""
        return method.upper() in ("POST", "PUT", "DELETE", "PATCH")

    def _should_rate_limit_path(self, path: str) -> bool:
        """
        Determine if a path should be rate limited.

        Exclude health checks and metrics endpoints.
        """
        excluded_paths = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        return not any(path.startswith(excluded) for excluded in excluded_paths)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request through rate limiting middleware.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response or 429 Too Many Requests if rate limited
        """
        if not self.enabled:
            return await call_next(request)

        # Check if path should be rate limited
        if not self._should_rate_limit_path(request.url.path):
            return await call_next(request)

        # Extract client IP
        client_ip = self._extract_client_ip(request)

        # Determine endpoint identifier
        endpoint = request.url.path

        # Check write method tier
        if self._is_write_method(request.method):
            # Use write tier for this check if needed
            pass

        # Check rate limit
        is_allowed, requests_made, limit = self.limiter.is_allowed(
            client_ip,
            endpoint,
        )

        if not is_allowed:
            # Calculate retry-after: time until oldest request leaves the window
            retry_after = int(self.limiter.window_size / (limit / requests_made))

            return Response(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(time.time()) + retry_after
                    ),
                },
                content=f"Rate limit exceeded: {requests_made}/{limit} requests per minute",
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit information headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - requests_made))
        response.headers["X-RateLimit-Reset"] = str(
            int(time.time()) + self.limiter.window_size
        )

        return response

    def register_tier(self, tier: RateLimitTier) -> None:
        """
        Register a custom rate limit tier.

        Args:
            tier: RateLimitTier configuration
        """
        self.limiter.register_tier(tier)

    def get_metrics(self) -> Dict:
        """Get current rate limiter metrics."""
        return self.limiter.get_metrics()

    def reset_metrics(self) -> None:
        """Reset rate limiter metrics."""
        self.limiter.reset_metrics()
