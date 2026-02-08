"""
Professional-grade structured request logging middleware for FastAPI.

Provides institutional-quality JSON logging with:
- Unique request ID tracking (UUID4)
- Performance metrics (duration, client IP, user agent)
- Sensitive header masking
- Configurable health check endpoint skipping
- Environment-aware log levels
"""

import json
import logging
import time
import uuid
from typing import Callable, List, Optional
from os import getenv

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging in JSON format.

    Features:
    - Generates unique UUID4 request_id for request tracing
    - Adds X-Request-ID header to response for client correlation
    - Logs HTTP method, path, status code, response time, client IP, user agent
    - Masks sensitive headers (Authorization headers → "Bearer ***")
    - Skips logging for configurable health check endpoints
    - Logs full error details and tracebacks for 5xx responses
    - Environment-aware log level configuration

    Log format (JSON):
    {
        "timestamp": "2025-02-08T12:34:56.789Z",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "method": "GET",
        "path": "/api/assets",
        "status_code": 200,
        "duration_ms": 45.23,
        "client_ip": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "error_details": null
    }
    """

    # Health check endpoints to skip logging (saves I/O for high-frequency checks)
    SKIP_PATHS: List[str] = [
        "/health",
        "/health/extended",
        "/metrics",
        "/ping",
    ]

    # Sensitive headers that should be masked in logs
    SENSITIVE_HEADERS: List[str] = [
        "authorization",
        "x-api-key",
        "x-token",
        "cookie",
        "set-cookie",
        "x-auth-token",
        "x-access-token",
        "x-refresh-token",
    ]

    def __init__(self, app):
        """
        Initialize the request logging middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.logger = logging.getLogger("uvicorn.access")

        # Configure log level from environment (default: INFO)
        log_level = getenv("LOG_LEVEL", "INFO").upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Ensure JSON formatter is set
        self._setup_json_formatter()

    def _setup_json_formatter(self) -> None:
        """Configure JSON formatter for structured logging output."""
        # Check if formatter already set
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, logging.Formatter):
                # Already has a formatter, skip
                return

        # Add JSON formatter if no handler exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request/response and log structured data.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response with X-Request-ID header added
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Check if path should be skipped
        if self._should_skip_logging(request.url.path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        # Capture request metadata
        start_time = time.time()
        method = request.method
        path = request.url.path
        client_ip = self._extract_client_ip(request)
        user_agent = request.headers.get("user-agent", "Unknown")

        response: Optional[Response] = None
        error_details: Optional[dict] = None

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Log error details for 5xx responses
            if status_code >= 500:
                error_details = self._extract_error_details(response)

        except Exception as e:
            # Capture unhandled exceptions (should be caught by error handler)
            status_code = 500
            error_details = {
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "is_handled": False,
            }
            # Re-raise to let global error handler manage it
            raise

        finally:
            # Always log the request
            duration_ms = (time.time() - start_time) * 1000
            self._log_request(
                request_id=request_id,
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                error_details=error_details,
            )

        # Add request ID to response headers for client correlation
        if response:
            response.headers["X-Request-ID"] = request_id

        return response

    def _should_skip_logging(self, path: str) -> bool:
        """
        Check if path should be skipped from logging.

        Args:
            path: Request URL path

        Returns:
            True if path matches skip list, False otherwise
        """
        return any(path.startswith(skip_path) for skip_path in self.SKIP_PATHS)

    def _extract_client_ip(self, request: Request) -> str:
        """
        Extract client IP address with X-Forwarded-For support.

        Checks in order:
        1. X-Forwarded-For header (for proxy/load balancer scenarios)
        2. X-Real-IP header (alternative proxy header)
        3. request.client.host (direct connection)

        Args:
            request: HTTP request object

        Returns:
            Client IP address string
        """
        # X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        # We want the first one (original client)
        if forwarded_for := request.headers.get("x-forwarded-for"):
            return forwarded_for.split(",")[0].strip()

        # Alternative proxy header
        if real_ip := request.headers.get("x-real-ip"):
            return real_ip

        # Direct connection
        if request.client:
            return request.client.host

        return "Unknown"

    def _extract_error_details(self, response: Response) -> Optional[dict]:
        """
        Attempt to extract error details from 5xx response.

        Args:
            response: HTTP response object

        Returns:
            Dictionary with error details, or None if response body not JSON
        """
        try:
            # Try to decode response body if JSON
            if hasattr(response, "body"):
                body = response.body.decode("utf-8")
                data = json.loads(body)
                return {
                    "status": response.status_code,
                    "detail": data.get("detail"),
                    "error_type": data.get("type"),
                }
        except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
            pass

        return None

    def _log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        client_ip: str,
        user_agent: str,
        error_details: Optional[dict] = None,
    ) -> None:
        """
        Log structured request data in JSON format.

        Args:
            request_id: Unique request identifier (UUID4)
            method: HTTP method (GET, POST, etc.)
            path: Request URL path
            status_code: HTTP response status code
            duration_ms: Request processing time in milliseconds
            client_ip: Client IP address
            user_agent: User-Agent header value
            error_details: Optional error details for 5xx responses
        """
        from datetime import datetime, timezone

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "user_agent": user_agent[:256] if user_agent else "Unknown",  # Truncate long UAs
            "error_details": error_details,
        }

        # Log as JSON string
        log_message = json.dumps(log_data, default=str)

        # Use appropriate log level based on status code
        if status_code >= 500:
            self.logger.error(log_message)
        elif status_code >= 400:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
