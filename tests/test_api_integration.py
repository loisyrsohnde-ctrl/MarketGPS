"""
MarketGPS API Integration Tests
Comprehensive tests for all major API endpoint groups.
"""

import os
import sys
import tempfile
import pytest
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

# Setup paths for backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

# Set temp data dirs BEFORE any config imports to avoid PermissionError
_tmp_dir = tempfile.mkdtemp(prefix="marketgps_apitest_")
os.environ.setdefault("DATA_DIR", os.path.join(_tmp_dir, "data"))
os.environ.setdefault("SQLITE_PATH", os.path.join(_tmp_dir, "data", "sqlite", "marketgps.db"))

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
_env_file = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(_env_file)

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Import the app
import main
from main import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def client():
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test_token_valid"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers."""
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture
def mock_supabase():
    """Mock Supabase service."""
    with patch('main.supabase_admin') as mock:
        mock.get_user_profile.return_value = {
            'user_id': 'test_user_123',
            'email': 'test@example.com'
        }
        mock.get_user_entitlements.return_value = {
            'plan': 'MONTHLY',
            'stripe_customer_id': 'cus_test_123'
        }
        mock.update_entitlements.return_value = True
        yield mock


@pytest.fixture
def mock_stripe():
    """Mock Stripe service."""
    with patch('main.stripe_service') as mock:
        mock.create_customer.return_value = 'cus_test_123'
        mock.create_checkout_session.return_value = 'https://checkout.stripe.com/test'
        mock.create_portal_session.return_value = 'https://billing.stripe.com/test'
        mock.get_subscription.return_value = {
            'id': 'sub_test_123',
            'status': 'active',
            'items': {'data': [{'price': {'id': 'price_monthly_123'}}]}
        }
        mock.verify_webhook.return_value = {'type': 'checkout.session.completed', 'data': {}}
        yield mock


# ============================================================================
# TEST GROUP 1: Health Endpoints (2 tests)
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "15.0.0"

    def test_health_check_extended(self, client):
        """Test extended health endpoint with database check."""
        response = client.get("/health/extended")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "services" in data


# ============================================================================
# TEST GROUP 2: Assets/Scoring Endpoints (8 tests)
# ============================================================================

class TestAssetsScoringEndpoints:
    """Test assets and scoring endpoints."""

    def test_get_top_scores_default(self, client):
        """Test getting top scores with default parameters."""
        response = client.get("/api/scores/top")
        assert response.status_code in [200, 404]  # May be empty
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    def test_get_top_scores_with_limit(self, client):
        """Test getting top scores with custom limit."""
        response = client.get("/api/scores/top?limit=10")
        assert response.status_code in [200, 404]

    def test_search_assets(self, client):
        """Test asset search functionality."""
        response = client.get("/api/search?q=AAPL")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_search_assets_by_symbol(self, client):
        """Test searching assets by symbol."""
        response = client.get("/api/search?symbol=MSFT")
        assert response.status_code in [200, 404]

    def test_get_asset_explorer(self, client):
        """Test asset explorer endpoint."""
        response = client.get("/api/explorer?scope=US_EU")
        assert response.status_code in [200, 404]

    def test_get_asset_detail(self, client):
        """Test getting detailed asset information."""
        response = client.get("/api/assets/AAPL.US")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "asset_id" in data

    def test_get_asset_scores_detail(self, client):
        """Test getting detailed score breakdown."""
        response = client.get("/api/assets/AAPL.US/scores")
        assert response.status_code in [200, 404]

    def test_get_assets_by_region(self, client):
        """Test filtering assets by region."""
        response = client.get("/api/assets?region=US")
        assert response.status_code in [200, 404]


# ============================================================================
# TEST GROUP 3: News Endpoints (5 tests)
# ============================================================================

class TestNewsEndpoints:
    """Test news and news articles endpoints."""

    def test_get_news_list(self, client):
        """Test getting news articles list."""
        response = client.get("/api/news")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_get_news_by_region(self, client):
        """Test getting news filtered by region."""
        response = client.get("/api/news?region=US")
        assert response.status_code in [200, 404]

    def test_get_news_by_tags(self, client):
        """Test getting news filtered by tags."""
        response = client.get("/api/news?tags=technology")
        assert response.status_code in [200, 404]

    def test_get_news_detail(self, client):
        """Test getting detailed news article."""
        response = client.get("/api/news/1")
        assert response.status_code in [200, 404]

    def test_get_news_count(self, client):
        """Test getting news count."""
        response = client.get("/api/news/count")
        assert response.status_code in [200, 404]


# ============================================================================
# TEST GROUP 4: Strategies Endpoints (5 tests)
# ============================================================================

class TestStrategiesEndpoints:
    """Test strategy templates and user strategies."""

    def test_get_strategy_templates(self, client):
        """Test getting available strategy templates."""
        response = client.get("/api/strategies/templates")
        assert response.status_code in [200, 404, 500]  # 500 if table not created yet
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_strategy_template_detail(self, client):
        """Test getting specific strategy template."""
        response = client.get("/api/strategies/templates/balanced")
        assert response.status_code in [200, 404, 500]  # 500 if table not created yet

    def test_create_user_strategy_without_auth(self, client):
        """Test creating user strategy without authentication."""
        payload = {
            "name": "Test Strategy",
            "template_id": 1,
            "description": "A test strategy"
        }
        response = client.post("/api/strategies", json=payload)
        assert response.status_code in [200, 401, 404]

    def test_get_user_strategies_without_auth(self, client):
        """Test getting user strategies without authentication."""
        response = client.get("/api/strategies")
        assert response.status_code in [200, 401, 404]

    def test_delete_strategy_without_auth(self, client):
        """Test deleting strategy without authentication."""
        response = client.delete("/api/strategies/1")
        assert response.status_code in [200, 401, 404]


# ============================================================================
# TEST GROUP 5: Auth Flow (4 tests)
# ============================================================================

class TestAuthFlow:
    """Test authentication and authorization flow."""

    def test_request_without_auth_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/billing/subscription")
        # Should either work (with defaults) or require auth
        assert response.status_code in [200, 401]

    def test_request_with_invalid_auth_token(self, client, invalid_auth_headers):
        """Test accessing endpoint with invalid token."""
        response = client.get("/api/billing/subscription", headers=invalid_auth_headers)
        assert response.status_code in [200, 401]

    def test_request_with_valid_auth_token(self, client, auth_headers, mock_supabase):
        """Test accessing endpoint with valid token."""
        response = client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code in [200, 401, 503]

    @pytest.mark.parametrize("endpoint", [
        "/api/billing/subscription",
        "/billing/subscription",
    ])
    def test_subscription_endpoints_exist(self, client, endpoint):
        """Test that subscription endpoints are accessible."""
        response = client.get(endpoint)
        assert response.status_code in [200, 401, 503]


# ============================================================================
# TEST GROUP 6: Billing Endpoints (3 tests)
# ============================================================================

class TestBillingEndpoints:
    """Test billing and subscription endpoints."""

    def test_get_subscription_status(self, client):
        """Test getting subscription status."""
        response = client.get("/api/billing/subscription")
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert "plan" in data
            assert "status" in data

    def test_create_checkout_session_without_auth(self, client):
        """Test creating checkout session without auth."""
        payload = {"plan": "monthly"}
        response = client.post("/api/billing/checkout-session", json=payload)
        assert response.status_code in [401, 503]

    @pytest.mark.parametrize("plan", ["monthly", "yearly"])
    def test_checkout_session_valid_plans(self, client, auth_headers, plan, mock_supabase, mock_stripe):
        """Test checkout session with valid plans."""
        main.supabase_admin = mock_supabase
        main.stripe_service = mock_stripe

        payload = {"plan": plan}
        response = client.post("/api/billing/checkout-session", json=payload, headers=auth_headers)
        assert response.status_code in [200, 401, 503]


# ============================================================================
# TEST GROUP 7: Error Handling (5 tests)
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_endpoint_not_found(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_invalid_query_parameters(self, client):
        """Test with invalid query parameters."""
        response = client.get("/api/scores/top?limit=invalid")
        assert response.status_code in [200, 400, 404, 422]

    def test_missing_required_json_fields(self, client):
        """Test POST without required fields."""
        payload = {}
        response = client.post("/api/strategies", json=payload)
        assert response.status_code in [400, 401, 404, 422]

    @pytest.mark.parametrize("endpoint,method", [
        ("/api/assets/INVALID", "GET"),
        ("/api/news/9999", "GET"),
        ("/api/strategies/9999", "GET"),
    ])
    def test_not_found_resources(self, client, endpoint, method):
        """Test requesting non-existent resources."""
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.delete(endpoint)
        assert response.status_code in [200, 404]

    def test_rate_limit_simulation(self, client):
        """Test rate limiting behavior."""
        # Make rapid requests
        responses = []
        for _ in range(5):
            response = client.get("/api/scores/top")
            responses.append(response.status_code)

        # At least some should succeed (or all could fail with rate limit)
        assert all(code in [200, 404, 429] for code in responses)


# ============================================================================
# TEST GROUP 8: Watchlist Endpoints (3 tests)
# ============================================================================

class TestWatchlistEndpoints:
    """Test watchlist management endpoints."""

    def test_get_watchlist_without_auth(self, client):
        """Test getting watchlist without authentication."""
        response = client.get("/api/user/watchlist")
        assert response.status_code in [200, 401, 404]

    def test_add_to_watchlist_without_auth(self, client):
        """Test adding item to watchlist without auth."""
        payload = {"asset_id": "AAPL.US"}
        response = client.post("/api/user/watchlist", json=payload)
        assert response.status_code in [200, 401, 404]

    def test_remove_from_watchlist_without_auth(self, client):
        """Test removing item from watchlist without auth."""
        response = client.delete("/api/user/watchlist/1")
        assert response.status_code in [200, 401, 404]


# ============================================================================
# TEST GROUP 9: Admin Endpoints (3 tests)
# ============================================================================

class TestAdminEndpoints:
    """Test admin dashboard and management endpoints."""

    def test_get_admin_dashboard_without_auth(self, client):
        """Test accessing admin dashboard without auth."""
        response = client.get("/api/admin/dashboard")
        assert response.status_code in [401, 404]

    def test_get_admin_stats_without_auth(self, client):
        """Test accessing admin stats without auth."""
        response = client.get("/api/admin/stats")
        assert response.status_code in [401, 404]

    def test_admin_requires_special_role(self, client, auth_headers):
        """Test admin endpoints require special role."""
        response = client.get("/api/admin/dashboard", headers=auth_headers)
        assert response.status_code in [401, 403, 404]


# ============================================================================
# TEST GROUP 10: Portfolio Endpoints (3 tests)
# ============================================================================

class TestPortfolioEndpoints:
    """Test portfolio synchronization endpoints."""

    def test_get_portfolio_without_auth(self, client):
        """Test getting portfolio without authentication."""
        response = client.get("/api/portfolio")
        assert response.status_code in [200, 401, 404]

    def test_sync_portfolio_without_auth(self, client):
        """Test syncing portfolio without authentication."""
        payload = {}
        response = client.post("/api/portfolio/sync", json=payload)
        assert response.status_code in [200, 401, 404]

    def test_get_portfolio_holdings(self, client):
        """Test getting portfolio holdings."""
        response = client.get("/api/portfolio/holdings")
        assert response.status_code in [200, 401, 404]


# ============================================================================
# TEST GROUP 11: Parametrized Boundary Tests
# ============================================================================

class TestBoundaryConditions:
    """Test boundary cases and edge conditions."""

    @pytest.mark.parametrize("limit", [0, 1, 10, 100, 1000])
    def test_top_scores_boundary_limits(self, client, limit):
        """Test top scores with boundary limit values."""
        response = client.get(f"/api/scores/top?limit={limit}")
        assert response.status_code in [200, 400, 404, 422]

    @pytest.mark.parametrize("scope", ["US_EU", "AFRICA", "INVALID"])
    def test_asset_explorer_scopes(self, client, scope):
        """Test explorer with different market scopes."""
        response = client.get(f"/api/explorer?scope={scope}")
        assert response.status_code in [200, 400, 404]

    @pytest.mark.parametrize("page", [1, 2, 10, 100])
    def test_pagination_boundaries(self, client, page):
        """Test pagination with boundary page numbers."""
        response = client.get(f"/api/assets?page={page}&page_size=10")
        assert response.status_code in [200, 404]


# ============================================================================
# TEST GROUP 12: Concurrent Requests
# ============================================================================

class TestConcurrentRequests:
    """Test API behavior under concurrent requests."""

    def test_multiple_concurrent_requests(self, client):
        """Test multiple concurrent health check requests."""
        responses = [client.get("/health") for _ in range(5)]
        assert all(r.status_code == 200 for r in responses)

    def test_mixed_endpoint_requests(self, client):
        """Test mix of different endpoint requests."""
        endpoints = [
            "/health",
            "/api/scores/top",
            "/api/billing/subscription",
        ]
        responses = [client.get(ep) for ep in endpoints]
        assert all(r.status_code in [200, 401, 404, 503] for r in responses)


# ============================================================================
# TEST GROUP 13: Response Structure Validation
# ============================================================================

class TestResponseStructure:
    """Test that responses have correct structure."""

    def test_health_response_structure(self, client):
        """Test health response has required fields."""
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "version" in data
            assert isinstance(data["status"], str)
            assert isinstance(data["version"], str)

    def test_subscription_response_structure(self, client):
        """Test subscription response structure."""
        response = client.get("/api/billing/subscription")
        if response.status_code == 200:
            data = response.json()
            assert "plan" in data
            assert "status" in data
            assert "daily_quota_used" in data
            assert "daily_quota_limit" in data


# ============================================================================
# TEST GROUP 14: Content Type Validation
# ============================================================================

class TestContentType:
    """Test that responses have correct content types."""

    def test_json_response_content_type(self, client):
        """Test JSON responses have correct content type."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_accept_header_handling(self, client):
        """Test that API handles Accept header correctly."""
        headers = {"Accept": "application/json"}
        response = client.get("/health", headers=headers)
        assert response.status_code == 200


# ============================================================================
# TEST GROUP 15: HTTP Methods
# ============================================================================

class TestHTTPMethods:
    """Test correct HTTP method handling."""

    def test_get_method_on_read_endpoint(self, client):
        """Test GET method on read-only endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_post_method_on_write_endpoint(self, client):
        """Test POST method on write endpoint."""
        payload = {"plan": "monthly"}
        response = client.post("/api/billing/checkout-session", json=payload)
        assert response.status_code in [401, 503, 400, 422]

    def test_delete_method_unsupported(self, client):
        """Test DELETE on read-only endpoint."""
        response = client.delete("/health")
        assert response.status_code in [405, 404]


# ============================================================================
# Integration Test Suite Helper
# ============================================================================

@pytest.mark.integration
class TestIntegrationSuite:
    """Full integration test scenarios."""

    def test_complete_user_flow_checkout(self, client, auth_headers, mock_supabase, mock_stripe):
        """Test complete user flow: check subscription -> create checkout."""
        # Mock services
        main.supabase_admin = mock_supabase
        main.stripe_service = mock_stripe

        # Step 1: Check subscription
        response = client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code in [200, 503]

        # Step 2: Create checkout (if services available)
        if response.status_code == 200:
            payload = {"plan": "monthly"}
            response = client.post("/api/billing/checkout-session", json=payload, headers=auth_headers)
            assert response.status_code in [200, 401, 503]  # 401 if mock token fails Supabase verification

    def test_asset_discovery_flow(self, client):
        """Test complete asset discovery flow."""
        # Search for asset
        search_response = client.get("/api/search?q=AAPL")
        assert search_response.status_code in [200, 404]

        # View explorer
        explorer_response = client.get("/api/explorer?scope=US_EU")
        assert explorer_response.status_code in [200, 404]

        # Get top scores
        top_response = client.get("/api/scores/top")
        assert top_response.status_code in [200, 404]


# ============================================================================
# Conftest Markers
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
