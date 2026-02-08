"""
Input Validation Middleware - Request Validation and Injection Prevention

This module provides a Starlette BaseHTTPMiddleware for validating:
- Request size limits (query strings, request bodies, URL paths)
- Common injection patterns (SQL injection, XSS)
- Clear error responses with validation failure logging
"""

import os
import logging
import re
from typing import Callable, Optional
from urllib.parse import unquote

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send, Message

logger = logging.getLogger(__name__)


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware for validating and sanitizing incoming requests.

    Enforces limits on:
    - Query string length (default: 2048 chars)
    - Request body size (default: 1 MB, 5 MB for file uploads)
    - URL path length (default: 512 chars)

    Detects and blocks common injection patterns:
    - SQL injection attempts
    - Cross-site scripting (XSS) attempts
    """

    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",  # SQL comments
        r"('|\")\s*(OR|AND)\s*('|\")?",  # OR/AND operators with quotes
        r"(\bOR\b.*=.*)",  # OR 1=1 style attacks
        r"(;\s*(DROP|DELETE|UPDATE))",  # Chained commands
    ]

    # Common XSS patterns
    XSS_INJECTION_PATTERNS = [
        r"(<|%3C)(script|svg|iframe|img|body|style)(\s|%20|>|%3E)",
        r"(javascript:|on\w+\s*=)",  # javascript: protocol and event handlers
        r"(<|%3C)iframe",  # iframes
        r"(&lt;|<)script(>|&gt;)",  # script tags
    ]

    def __init__(self, app: ASGIApp):
        """
        Initialize the validation middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

        # Load configuration from environment with defaults
        self.max_query_string_length = int(
            os.getenv("MAX_QUERY_STRING_LENGTH", 2048)
        )
        self.max_request_body_size = int(
            os.getenv("MAX_REQUEST_BODY_SIZE", 1048576)  # 1 MB
        )
        self.max_file_upload_size = int(
            os.getenv("MAX_FILE_UPLOAD_SIZE", 5242880)  # 5 MB
        )
        self.max_url_path_length = int(
            os.getenv("MAX_URL_PATH_LENGTH", 512)
        )

        # Compile regex patterns for performance
        self.sql_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.SQL_INJECTION_PATTERNS
        ]
        self.xss_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.XSS_INJECTION_PATTERNS
        ]

        logger.info(
            f"InputValidationMiddleware initialized with limits: "
            f"query={self.max_query_string_length}, "
            f"body={self.max_request_body_size}, "
            f"upload={self.max_file_upload_size}, "
            f"path={self.max_url_path_length}"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Main middleware dispatch function.

        Validates request before passing to the application.

        Args:
            request: The incoming request
            call_next: The next middleware/handler

        Returns:
            JSONResponse: Either the next handler's response or a 400 error
        """
        # Validate URL path length
        path = request.url.path
        if len(path) > self.max_url_path_length:
            logger.warning(
                f"URL path exceeds maximum length: "
                f"{len(path)} > {self.max_url_path_length}, "
                f"path={path}, client={request.client}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "detail": f"URL path exceeds maximum length of {self.max_url_path_length} characters"
                }
            )

        # Validate query string length
        query_string = request.url.query
        if len(query_string) > self.max_query_string_length:
            logger.warning(
                f"Query string exceeds maximum length: "
                f"{len(query_string)} > {self.max_query_string_length}, "
                f"client={request.client}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "detail": f"Query string exceeds maximum length of {self.max_query_string_length} characters"
                }
            )

        # Validate query parameters for injection patterns
        injection_error = self._validate_query_params(request)
        if injection_error:
            logger.warning(
                f"Injection pattern detected in query parameters: "
                f"{injection_error}, client={request.client}"
            )
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "detail": injection_error
                }
            )

        # Determine if this is a file upload endpoint
        is_file_upload = self._is_file_upload_endpoint(request)
        max_body_size = (
            self.max_file_upload_size if is_file_upload else self.max_request_body_size
        )

        # Validate request body size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > max_body_size:
                    size_limit_mb = max_body_size / (1024 * 1024)
                    logger.warning(
                        f"Request body exceeds maximum size: "
                        f"{content_length} > {max_body_size}, "
                        f"endpoint={request.url.path}, "
                        f"client={request.client}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Bad Request",
                            "detail": f"Request body exceeds maximum size of {size_limit_mb:.1f} MB"
                        }
                    )
            except ValueError:
                logger.warning(
                    f"Invalid content-length header: {content_length}, "
                    f"client={request.client}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Bad Request",
                        "detail": "Invalid content-length header"
                    }
                )

        # Validate JSON body for injection patterns (if applicable)
        if request.method in ["POST", "PUT", "PATCH"]:
            if "application/json" in request.headers.get("content-type", ""):
                injection_error = await self._validate_json_body(request)
                if injection_error:
                    logger.warning(
                        f"Injection pattern detected in request body: "
                        f"{injection_error}, endpoint={request.url.path}, "
                        f"client={request.client}"
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "Bad Request",
                            "detail": injection_error
                        }
                    )

        # Proceed to the next handler
        response = await call_next(request)
        return response

    def _validate_query_params(self, request: Request) -> Optional[str]:
        """
        Check query parameters for injection patterns.

        Args:
            request: The incoming request

        Returns:
            Optional[str]: Error message if pattern found, None otherwise
        """
        params = request.query_params
        for key, value in params.items():
            # Decode URL-encoded values
            decoded_value = unquote(value)

            # Check for SQL injection
            for pattern in self.sql_patterns:
                if pattern.search(decoded_value):
                    return f"Potential SQL injection detected in parameter '{key}'"

            # Check for XSS
            for pattern in self.xss_patterns:
                if pattern.search(decoded_value):
                    return f"Potential XSS injection detected in parameter '{key}'"

        return None

    async def _validate_json_body(self, request: Request) -> Optional[str]:
        """
        Check JSON request body for injection patterns.

        Args:
            request: The incoming request

        Returns:
            Optional[str]: Error message if pattern found, None otherwise
        """
        try:
            body = await request.json()
            return self._check_json_value_recursive(body)
        except Exception as e:
            logger.debug(f"Could not parse JSON body for validation: {e}")
            return None

    def _check_json_value_recursive(
        self, value: any, field_name: str = "root"
    ) -> Optional[str]:
        """
        Recursively check JSON values for injection patterns.

        Args:
            value: The value to check
            field_name: The name of the field (for error messages)

        Returns:
            Optional[str]: Error message if pattern found, None otherwise
        """
        if isinstance(value, str):
            decoded_value = unquote(value)

            # Check for SQL injection
            for pattern in self.sql_patterns:
                if pattern.search(decoded_value):
                    return f"Potential SQL injection detected in field '{field_name}'"

            # Check for XSS
            for pattern in self.xss_patterns:
                if pattern.search(decoded_value):
                    return f"Potential XSS injection detected in field '{field_name}'"

        elif isinstance(value, dict):
            for key, val in value.items():
                result = self._check_json_value_recursive(val, field_name=key)
                if result:
                    return result

        elif isinstance(value, list):
            for idx, item in enumerate(value):
                result = self._check_json_value_recursive(item, field_name=f"{field_name}[{idx}]")
                if result:
                    return result

        return None

    @staticmethod
    def _is_file_upload_endpoint(request: Request) -> bool:
        """
        Determine if the endpoint is for file uploads.

        Args:
            request: The incoming request

        Returns:
            bool: True if this appears to be a file upload endpoint
        """
        # Check content-type
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type:
            return True

        # Check path patterns
        path = request.url.path.lower()
        upload_keywords = ["upload", "file", "media", "attachment", "image"]
        return any(keyword in path for keyword in upload_keywords)
