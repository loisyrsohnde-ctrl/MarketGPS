"""
Authentication flow tests for MarketGPS.

Tests the full auth pipeline:
- Token verification
- User ID extraction
- Auth-required vs optional behavior
- Cache functionality
"""

import os
import sys
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestTokenVerification:
    """Test Supabase token verification."""

    def test_invalid_token_rejected(self):
        """Invalid JWT should return None."""
        from security import verify_supabase_token

        result = verify_supabase_token("not-a-valid-jwt-token")
        assert result is None

    def test_empty_token_rejected(self):
        """Empty string should return None."""
        from security import verify_supabase_token

        result = verify_supabase_token("")
        assert result is None

    def test_malformed_jwt_rejected(self):
        """Malformed JWT (wrong structure) should return None."""
        from security import verify_supabase_token

        # JWT should have 3 parts separated by dots
        result = verify_supabase_token("header.payload")
        assert result is None

    def test_expired_jwt_rejected(self):
        """Expired JWT should return None."""
        from security import verify_supabase_token

        # Create an expired token (if we have a secret)
        jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
        if not jwt_secret:
            pytest.skip("SUPABASE_JWT_SECRET not configured")

        from jose import jwt as jose_jwt
        import time

        payload = {
            "sub": "test-user-id",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "aud": "authenticated",
        }
        expired_token = jose_jwt.encode(payload, jwt_secret, algorithm="HS256")
        result = verify_supabase_token(expired_token)
        assert result is None


class TestUserIdExtraction:
    """Test user ID resolution from requests."""

    def test_no_auth_in_dev_returns_fallback(self):
        """Without auth header in dev mode, should return fallback."""
        from security import get_user_id_from_request

        # Ensure we're NOT in production mode
        old_env = os.environ.get("ENV")
        old_auth = os.environ.get("AUTH_REQUIRED")
        try:
            os.environ.pop("ENV", None)
            os.environ.pop("AUTH_REQUIRED", None)
            os.environ.pop("APP_ENV", None)

            result = get_user_id_from_request(None, fallback_user_id="test_user")
            assert result == "test_user"
        finally:
            if old_env:
                os.environ["ENV"] = old_env
            if old_auth:
                os.environ["AUTH_REQUIRED"] = old_auth

    def test_invalid_auth_format_in_dev(self):
        """Invalid auth format in dev should return fallback."""
        from security import get_user_id_from_request

        old_env = os.environ.get("ENV")
        try:
            os.environ.pop("ENV", None)
            os.environ.pop("AUTH_REQUIRED", None)
            os.environ.pop("APP_ENV", None)

            result = get_user_id_from_request("InvalidFormat", fallback_user_id="fallback")
            assert result == "fallback"
        finally:
            if old_env:
                os.environ["ENV"] = old_env

    def test_no_auth_in_production_raises(self):
        """Without auth header in production, should raise 401."""
        from security import get_user_id_from_request
        from fastapi import HTTPException

        old_env = os.environ.get("ENV")
        try:
            os.environ["ENV"] = "production"

            with pytest.raises(HTTPException) as exc_info:
                get_user_id_from_request(None)
            assert exc_info.value.status_code == 401
        finally:
            if old_env:
                os.environ["ENV"] = old_env
            else:
                os.environ.pop("ENV", None)

    def test_invalid_token_in_production_raises(self):
        """Invalid token in production should raise 401."""
        from security import get_user_id_from_request
        from fastapi import HTTPException

        old_env = os.environ.get("ENV")
        try:
            os.environ["ENV"] = "production"

            with pytest.raises(HTTPException) as exc_info:
                get_user_id_from_request("Bearer invalid-token-here")
            assert exc_info.value.status_code == 401
        finally:
            if old_env:
                os.environ["ENV"] = old_env
            else:
                os.environ.pop("ENV", None)


class TestGetCurrentUserId:
    """Test the FastAPI dependency for user ID extraction."""

    def test_missing_auth_raises_401(self):
        """Missing Authorization header should raise 401."""
        from security import get_current_user_id
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(None)
        assert exc_info.value.status_code == 401

    def test_invalid_format_raises_401(self):
        """Non-Bearer format should raise 401."""
        from security import get_current_user_id
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id("Basic dXNlcjpwYXNz")
        assert exc_info.value.status_code == 401


class TestOptionalUserId:
    """Test optional auth dependency."""

    def test_no_auth_returns_none(self):
        """No auth header should return None."""
        from security import get_optional_user_id

        result = get_optional_user_id(None)
        assert result is None

    def test_invalid_token_returns_none(self):
        """Invalid token should return None (not raise)."""
        from security import get_optional_user_id

        result = get_optional_user_id("Bearer invalid-token")
        assert result is None


class TestIsAuthRequired:
    """Test environment-based auth enforcement."""

    def test_dev_mode_not_required(self):
        """Dev mode should not require auth."""
        from security import is_auth_required

        old_vals = {k: os.environ.pop(k, None) for k in ["AUTH_REQUIRED", "ENV", "APP_ENV"]}
        try:
            assert is_auth_required() is False
        finally:
            for k, v in old_vals.items():
                if v:
                    os.environ[k] = v

    def test_production_requires_auth(self):
        """Production mode should require auth."""
        from security import is_auth_required

        old_vals = {k: os.environ.pop(k, None) for k in ["AUTH_REQUIRED", "ENV", "APP_ENV"]}
        try:
            os.environ["ENV"] = "production"
            assert is_auth_required() is True
        finally:
            for k, v in old_vals.items():
                if v:
                    os.environ[k] = v
                elif k in os.environ:
                    del os.environ[k]

    def test_explicit_auth_required_flag(self):
        """AUTH_REQUIRED=true should enforce auth."""
        from security import is_auth_required

        old_vals = {k: os.environ.pop(k, None) for k in ["AUTH_REQUIRED", "ENV", "APP_ENV"]}
        try:
            os.environ["AUTH_REQUIRED"] = "true"
            assert is_auth_required() is True
        finally:
            for k, v in old_vals.items():
                if v:
                    os.environ[k] = v
                elif k in os.environ:
                    del os.environ[k]
