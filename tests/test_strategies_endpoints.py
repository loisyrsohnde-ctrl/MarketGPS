"""
Tests for Strategies API endpoints.
Run with: pytest tests/test_strategies_endpoints.py -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestStrategiesHealth:
    """Test strategies health endpoint."""
    
    def test_health_returns_200(self, client):
        response = client.get("/api/strategies/health")
        assert response.status_code == 200
        
    def test_health_returns_status(self, client):
        response = client.get("/api/strategies/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "strategies"


class TestTemplates:
    """Test strategy templates endpoints."""
    
    def test_list_templates(self, client):
        response = client.get("/api/strategies/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 6  # At least 6 default templates
        
    def test_templates_have_required_fields(self, client):
        response = client.get("/api/strategies/templates")
        data = response.json()
        if data:
            template = data[0]
            assert "id" in template
            assert "slug" in template
            assert "name" in template
            assert "structure" in template
            
    def test_get_barbell_template(self, client):
        response = client.get("/api/strategies/templates/barbell")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "barbell"
        assert "ultra_safe" in str(data["structure"])
        
    def test_get_permanent_template(self, client):
        response = client.get("/api/strategies/templates/permanent")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "permanent"
        assert data["risk_level"] == "low"
        # Should have 4 blocks (growth, deflation, inflation, liquidity)
        blocks = data["structure"].get("blocks", [])
        assert len(blocks) == 4
        
    def test_get_core_satellite_template(self, client):
        response = client.get("/api/strategies/templates/core_satellite")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "core_satellite"
        
    def test_template_not_found(self, client):
        response = client.get("/api/strategies/templates/nonexistent")
        assert response.status_code == 404
        
    def test_filter_by_category(self, client):
        response = client.get("/api/strategies/templates?category=balanced")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["category"] == "balanced"
            
    def test_filter_by_risk_level(self, client):
        response = client.get("/api/strategies/templates?risk_level=low")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["risk_level"] == "low"


class TestEligibleInstruments:
    """Test eligible instruments endpoint."""
    
    def test_get_eligible_for_growth(self, client):
        response = client.get("/api/strategies/eligible-instruments?block_type=growth")
        assert response.status_code == 200
        data = response.json()
        assert "instruments" in data
        assert "block_type" in data
        assert data["block_type"] == "growth"
        
    def test_get_eligible_for_ultra_safe(self, client):
        response = client.get("/api/strategies/eligible-instruments?block_type=ultra_safe")
        assert response.status_code == 200
        data = response.json()
        assert "instruments" in data
        
    def test_get_eligible_for_core(self, client):
        response = client.get("/api/strategies/eligible-instruments?block_type=core")
        assert response.status_code == 200
        
    def test_instruments_have_fit_score(self, client):
        response = client.get("/api/strategies/eligible-instruments?block_type=growth")
        data = response.json()
        if data["instruments"]:
            inst = data["instruments"][0]
            assert "fit_score" in inst
            assert "ticker" in inst
            assert "name" in inst
            assert "liquidity_badge" in inst
            
    def test_limit_respects_minimum(self, client):
        # Limit must be >= 5
        response = client.get("/api/strategies/eligible-instruments?block_type=growth&limit=3")
        assert response.status_code == 422  # Validation error


class TestSimulation:
    """Test simulation endpoint."""
    
    def test_simulation_requires_compositions(self, client):
        response = client.post("/api/strategies/simulate", json={
            "compositions": [],
            "period_years": 10,
            "initial_value": 10000,
            "rebalance_frequency": "annual"
        })
        # Should fail due to empty compositions or weight validation
        assert response.status_code in [400, 422]
        
    def test_simulation_validates_weights(self, client):
        response = client.post("/api/strategies/simulate", json={
            "compositions": [
                {"ticker": "AAPL", "block_name": "growth", "weight": 0.5}
            ],
            "period_years": 10,
            "initial_value": 10000,
            "rebalance_frequency": "annual"
        })
        # Total weight is 50%, should fail
        assert response.status_code == 422
        
    def test_simulation_validates_rebalance_frequency(self, client):
        response = client.post("/api/strategies/simulate", json={
            "compositions": [
                {"ticker": "AAPL", "block_name": "growth", "weight": 1.0}
            ],
            "period_years": 10,
            "initial_value": 10000,
            "rebalance_frequency": "weekly"  # Invalid
        })
        assert response.status_code == 422
        
    def test_valid_simulation_request(self, client):
        response = client.post("/api/strategies/simulate", json={
            "compositions": [
                {"ticker": "AAPL", "block_name": "growth", "weight": 0.5},
                {"ticker": "MSFT", "block_name": "growth", "weight": 0.5}
            ],
            "period_years": 10,
            "initial_value": 10000,
            "rebalance_frequency": "annual"
        })
        assert response.status_code == 200
        data = response.json()
        # Should have metrics or warnings
        assert "cagr" in data or "warnings" in data


class TestUserStrategies:
    """Test user strategies CRUD."""
    
    def test_list_user_strategies(self, client):
        response = client.get("/api/strategies/user?user_id=default")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_create_user_strategy(self, client):
        response = client.post(
            "/api/strategies/user?user_id=test_user",
            json={
                "name": "Test Strategy",
                "description": "Test description",
                "compositions": [
                    {"ticker": "AAPL", "block_name": "growth", "weight": 1.0}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        
        # Cleanup
        strategy_id = data["id"]
        client.delete(f"/api/strategies/user/{strategy_id}?user_id=test_user")
        
    def test_create_strategy_validates_weights(self, client):
        response = client.post(
            "/api/strategies/user?user_id=test_user",
            json={
                "name": "Invalid Strategy",
                "compositions": [
                    {"ticker": "AAPL", "block_name": "growth", "weight": 0.5}
                ]
            }
        )
        assert response.status_code == 400  # Weight validation
        
    def test_get_strategy_not_found(self, client):
        response = client.get("/api/strategies/user/99999?user_id=default")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
