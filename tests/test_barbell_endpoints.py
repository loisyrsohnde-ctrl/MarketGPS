"""
Tests for Barbell Strategy API endpoints.
Run with: pytest tests/test_barbell_endpoints.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestBarbellHealth:
    """Test barbell health endpoint."""
    
    def test_health_returns_200(self, client):
        response = client.get("/api/barbell/health")
        assert response.status_code == 200
        
    def test_health_returns_status(self, client):
        response = client.get("/api/barbell/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "barbell"


class TestAllocationRatios:
    """Test allocation ratios endpoint."""
    
    def test_ratios_returns_profiles(self, client):
        response = client.get("/api/barbell/allocation-ratios")
        assert response.status_code == 200
        data = response.json()
        assert "profiles" in data
        assert len(data["profiles"]) == 3
        
    def test_ratios_contains_conservative(self, client):
        response = client.get("/api/barbell/allocation-ratios")
        data = response.json()
        profile_names = [p["name"] for p in data["profiles"]]
        assert "conservative" in profile_names
        assert "moderate" in profile_names
        assert "aggressive" in profile_names


class TestCoreCandidates:
    """Test core candidates endpoint."""
    
    def test_candidates_returns_list(self, client):
        response = client.get("/api/barbell/candidates/core?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        assert "total" in data
        
    def test_candidates_respects_limit(self, client):
        response = client.get("/api/barbell/candidates/core?limit=3")
        data = response.json()
        assert len(data["candidates"]) <= 3
        
    def test_candidates_pagination(self, client):
        response1 = client.get("/api/barbell/candidates/core?limit=5&offset=0")
        response2 = client.get("/api/barbell/candidates/core?limit=5&offset=5")
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Should have different assets (if enough data)
        if data1["total"] > 5:
            ids1 = {c["asset_id"] for c in data1["candidates"]}
            ids2 = {c["asset_id"] for c in data2["candidates"]}
            assert ids1 != ids2
            
    def test_candidates_search_filter(self, client):
        response = client.get("/api/barbell/candidates/core?q=ETF&limit=10")
        # Should not error
        assert response.status_code == 200


class TestSatelliteCandidates:
    """Test satellite candidates endpoint."""
    
    def test_candidates_returns_list(self, client):
        response = client.get("/api/barbell/candidates/satellite?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "candidates" in data
        
    def test_candidates_has_satellite_score(self, client):
        response = client.get("/api/barbell/candidates/satellite?limit=5")
        data = response.json()
        if data["candidates"]:
            assert "satellite_score" in data["candidates"][0]


class TestSimulation:
    """Test simulation endpoint."""
    
    def test_simulation_requires_compositions(self, client):
        response = client.post("/api/barbell/simulate", json={
            "compositions": [],
            "period_years": 5,
            "rebalance_frequency": "yearly",
            "initial_capital": 10000
        })
        assert response.status_code == 400
        
    def test_simulation_validates_weights(self, client):
        response = client.post("/api/barbell/simulate", json={
            "compositions": [
                {"asset_id": "AAPL_US", "weight": 0.3, "block": "core"},
                {"asset_id": "MSFT_US", "weight": 0.3, "block": "satellite"}
            ],
            "period_years": 5,
            "rebalance_frequency": "yearly",
            "initial_capital": 10000
        })
        # Total weight is 60%, should reject
        assert response.status_code == 400
        
    def test_simulation_validates_period(self, client):
        response = client.post("/api/barbell/simulate", json={
            "compositions": [
                {"asset_id": "AAPL_US", "weight": 1.0, "block": "core"}
            ],
            "period_years": 3,  # Invalid: must be 5, 10, or 20
            "rebalance_frequency": "yearly",
            "initial_capital": 10000
        })
        assert response.status_code == 400
        
    def test_simulation_returns_result(self, client):
        response = client.post("/api/barbell/simulate", json={
            "compositions": [
                {"asset_id": "AAPL_US", "weight": 0.5, "block": "core"},
                {"asset_id": "MSFT_US", "weight": 0.5, "block": "satellite"}
            ],
            "period_years": 5,
            "rebalance_frequency": "yearly",
            "initial_capital": 10000,
            "market_scope": "US_EU"
        })
        assert response.status_code == 200
        data = response.json()
        # Should have metrics or warnings
        assert "cagr" in data or "error" in data
        assert "warnings" in data


class TestPortfolios:
    """Test portfolio CRUD endpoints."""
    
    def test_list_portfolios(self, client):
        response = client.get("/api/barbell/portfolios?user_id=default_user")
        assert response.status_code == 200
        data = response.json()
        assert "portfolios" in data
        
    def test_create_portfolio(self, client):
        response = client.post("/api/barbell/portfolios?user_id=test_user", json={
            "name": "Test Portfolio",
            "description": "Test description",
            "risk_profile": "moderate",
            "core_ratio": 0.75,
            "satellite_ratio": 0.25,
            "items": [
                {"asset_id": "AAPL_US", "block": "core", "weight": 0.5}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # Cleanup
        portfolio_id = data["id"]
        client.delete(f"/api/barbell/portfolios/{portfolio_id}")
        
    def test_get_portfolio_not_found(self, client):
        response = client.get("/api/barbell/portfolios/nonexistent_id")
        assert response.status_code == 404


class TestSuggest:
    """Test suggestion endpoint."""
    
    def test_suggest_returns_portfolio(self, client):
        response = client.get("/api/barbell/suggest?risk_profile=moderate")
        assert response.status_code == 200
        data = response.json()
        assert "core_assets" in data
        assert "satellite_assets" in data
        assert "rationale" in data
        
    def test_suggest_different_profiles(self, client):
        conservative = client.get("/api/barbell/suggest?risk_profile=conservative")
        aggressive = client.get("/api/barbell/suggest?risk_profile=aggressive")
        
        c_data = conservative.json()
        a_data = aggressive.json()
        
        # Conservative should have higher core weight
        c_core_weight = sum(a["weight"] for a in c_data["core_assets"])
        a_core_weight = sum(a["weight"] for a in a_data["core_assets"])
        
        assert c_core_weight > a_core_weight


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
