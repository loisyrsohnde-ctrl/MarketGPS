"""
Global error handling middleware for FastAPI with request correlation.

Provides production-grade exception handling with:
- Automatic request_id correlation across error boundary
- Environment-aware response details (prod vs dev)
- Specific exception handling (HTTPException, ValidationError, etc.)
- Full server-side error logging and traceback capture
- Standardized error response format
"""

import json
import logging
import traceback
from typing import Any, Callable, Optional, Type
from os import getenv

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from sqlalchemy.exc import OperationalError
from pydantic import ValidationError


class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for centralized exception handling with production safety.

    Behavior:
    - Development (ENV != 'production'):
        Returns full error details, stack traces, and debugging info
    - Production (ENV == 'production'):
        Returns generic "Internal server error" message for 5xx errors
        Client receives request_id for support correlation
    - Always logs full traceback server-side for debugging
    - Correlates errors with request_id from request logging middleware
    - Handles specific exceptions with appropriate status codes:
        - HTTPException: Pass through (framework exceptions)
        - ValidationError: 422 Unprocessable Entity
        - OperationalError: 503 Service Unavailable (database issues)
        - Unhandled: 500 Internal Server Error

    Error response format:
    {
        "status": "error",
        "message": "Error description",
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "detail": {...},  # Only in development
        "traceback": "..."  # Only in development
    }
    """

    def __init__(self, app):
        """
        Initialize the global error handler middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

        # Detect environment
        self.is_production = getenv("ENV", "development").lower() == "production"

        if self.is_production:
            self.logger.info("Global error handler running in PRODUCTION mode")
        else:
            self.logger.info("Global error handler running in DEVELOPMENT mode (verbose errors)")

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """
        Process request and catch unhandled exceptions.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response or error response

        Raises:
            Exceptions are caught and handled here (not re-raised)
        """
        # Try to get request_id from request state (set by RequestLoggingMiddleware)
        request_id = getattr(request.state, "request_id", None)

        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # FastAPI HTTPExceptions should pass through
            # (they're used for intentional client errors like 401, 404, etc.)
            self.logger.debug(
                f"HTTPException caught: {e.status_code} - {e.detail} "
                f"(request_id: {request_id})"
            )
            raise

        except ValidationError as e:
            # Pydantic validation errors → 422 Unprocessable Entity
            self.logger.warning(
                f"Validation error (request_id: {request_id}): {e.json()}"
            )
            return self._error_response(
                status_code=422,
                message="Request validation failed",
                request_id=request_id,
                detail={
                    "errors": e.errors(),
                    "error_count": len(e.errors()),
                },
            )

        except OperationalError as e:
            # Database connectivity issues → 503 Service Unavailable
            self.logger.error(
                f"Database operational error (request_id: {request_id}): {str(e)}",
                exc_info=True,
            )
            return self._error_response(
                status_code=503,
                message="Service temporarily unavailable",
                request_id=request_id,
                detail={
                    "reason": "Database connection error",
                    "error_type": "OperationalError",
                } if not self.is_production else None,
            )

        except Exception as e:
            # Unhandled exceptions → 500 Internal Server Error
            error_type = type(e).__name__
            error_message = str(e)
            tb_str = traceback.format_exc()

            # Always log full traceback server-side
            self.logger.error(
                f"Unhandled exception (request_id: {request_id}): {error_type} - {error_message}\n{tb_str}"
            )

            # In development, return detailed error info
            if not self.is_production:
                return self._error_response(
                    status_code=500,
                    message=f"Internal server error: {error_message}",
                    request_id=request_id,
                    detail={
                        "error_type": error_type,
                        "error_message": error_message,
                    },
                    traceback=tb_str,
                )

            # In production, return generic message
            return self._error_response(
                status_code=500,
                message="Internal server error",
                request_id=request_id,
            )

    def _error_response(
        self,
        status_code: int,
        message: str,
        request_id: Optional[str] = None,
        detail: Optional[dict] = None,
        traceback: Optional[str] = None,
    ) -> JSONResponse:
        """
        Create a standardized error response.

        Args:
            status_code: HTTP status code (400, 500, 503, etc.)
            message: Error message (always shown to client)
            request_id: Unique request identifier for correlation
            detail: Additional error details (only shown in development)
            traceback: Full stack trace (only shown in development)

        Returns:
            JSONResponse with error details
        """
        response_data = {
            "status": "error",
            "message": message,
            "request_id": request_id,
        }

        # Only include detailed information in development
        if not self.is_production:
            if detail:
                response_data["detail"] = detail
            if traceback:
                response_data["traceback"] = traceback

        return JSONResponse(
            status_code=status_code,
            content=response_data,
        )


class ErrorHandlerConfig:
    """
    Configuration helper for error handler setup.

    Usage:
    from middleware.error_handler import ErrorHandlerConfig

    app.add_middleware(GlobalErrorHandlerMiddleware)
    # or with configuration:
    app.add_middleware(GlobalErrorHandlerMiddleware, config=ErrorHandlerConfig(...))
    """

    def __init__(
        self,
        is_production: bool = False,
        include_traceback_in_dev: bool = True,
        include_validation_errors: bool = True,
        log_level: str = "ERROR",
    ):
        """
        Initialize error handler configuration.

        Args:
            is_production: Whether to run in production mode (hides error details)
            include_traceback_in_dev: Include stack traces in development responses
            include_validation_errors: Include validation error details in responses
            log_level: Logging level for error handler
        """
        self.is_production = is_production
        self.include_traceback_in_dev = include_traceback_in_dev
        self.include_validation_errors = include_validation_errors
        self.log_level = log_level
