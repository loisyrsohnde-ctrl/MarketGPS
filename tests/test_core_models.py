"""
Unit Tests: Core Data Models
Tests for core.models module and all dataclass models.
"""

import pytest
import json
from datetime import datetime

from core.models import (
    AssetType, Asset, StateLabel, Score, ScoreBreakdown,
    GatingStatus, RotationState, WatchlistItem, PriorityQueueItem,
    ProQuota, ProTier, QueueStatus, Tier, SearchResult, PaginatedResult,
    ProviderHealth
)


class TestAssetType:
    """Tests for AssetType enumeration."""

    def test_asset_type_values(self):
        """Test all asset types are defined."""
        assert AssetType.EQUITY.value == "EQUITY"
        assert AssetType.ETF.value == "ETF"
        assert AssetType.CRYPTO.value == "CRYPTO"
        assert AssetType.BOND.value == "BOND"
        assert AssetType.FUND.value == "FUND"

    def test_asset_type_from_string_valid(self):
        """Test from_string with valid values."""
        assert AssetType.from_string("EQUITY") == AssetType.EQUITY
        assert AssetType.from_string("etf") == AssetType.ETF  # Case insensitive
        assert AssetType.from_string("CRYPTO") == AssetType.CRYPTO

    def test_asset_type_from_string_invalid(self):
        """Test from_string with invalid values returns UNKNOWN."""
        assert AssetType.from_string("INVALID") == AssetType.UNKNOWN
        assert AssetType.from_string("") == AssetType.UNKNOWN

    def test_asset_type_from_string_none(self):
        """Test from_string with None returns UNKNOWN."""
        assert AssetType.from_string(None) == AssetType.UNKNOWN

    def test_asset_type_display_names(self):
        """Test display names are in French/English."""
        assert "Actions" in AssetType.EQUITY.display_name or "EQUITY" in AssetType.EQUITY.display_name
        assert AssetType.CRYPTO.display_name == "Crypto"
        assert AssetType.FUND.display_name == "Fonds"

    def test_asset_type_value_pillar(self):
        """Test has_value_pillar property."""
        assert AssetType.EQUITY.has_value_pillar is True
        assert AssetType.FUND.has_value_pillar is True
        assert AssetType.ETF.has_value_pillar is False
        assert AssetType.CRYPTO.has_value_pillar is False

    def test_asset_type_fundamentals(self):
        """Test has_fundamentals property."""
        assert AssetType.EQUITY.has_fundamentals is True
        assert AssetType.ETF.has_fundamentals is True
        assert AssetType.CRYPTO.has_fundamentals is False


class TestAsset:
    """Tests for Asset dataclass."""

    def test_asset_creation_minimal(self):
        """Test creating asset with minimal fields."""
        asset = Asset(
            asset_id="AAPL.US",
            symbol="AAPL"
        )
        assert asset.asset_id == "AAPL.US"
        assert asset.symbol == "AAPL"
        assert asset.asset_type == AssetType.EQUITY

    def test_asset_creation_full(self, sample_asset):
        """Test creating asset with all fields."""
        assert sample_asset.asset_id == "AAPL.US"
        assert sample_asset.symbol == "AAPL"
        assert sample_asset.name == "Apple Inc."
        assert sample_asset.asset_type == AssetType.EQUITY

    def test_asset_defaults(self):
        """Test asset default values."""
        asset = Asset(asset_id="TEST.US", symbol="TEST")
        assert asset.market_scope == "US_EU"
        assert asset.market_code == "US"
        assert asset.currency == "USD"
        assert asset.active is True
        assert asset.tier == 2

    def test_asset_from_row(self):
        """Test creating asset from database row."""
        row = {
            "asset_id": "AAPL.US",
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "asset_type": "EQUITY",
            "market_scope": "US_EU",
            "market_code": "US",
            "exchange_code": "NASDAQ",
            "exchange": "NASDAQ",
            "currency": "USD",
            "country": "US",
            "active": 1,
            "tier": 1,
            "priority_level": 1
        }
        asset = Asset.from_row(row)
        assert asset.asset_id == "AAPL.US"
        assert asset.name == "Apple Inc."
        assert asset.active is True


class TestScore:
    """Tests for Score dataclass."""

    def test_score_creation_minimal(self):
        """Test creating score with minimal fields."""
        score = Score(asset_id="AAPL.US")
        assert score.asset_id == "AAPL.US"
        assert score.is_calculated is False

    def test_score_creation_full(self, sample_score):
        """Test creating score with all fields."""
        assert sample_score.asset_id == "AAPL.US"
        assert sample_score.score_total == 71.0
        assert sample_score.is_calculated is True

    def test_score_is_calculated_false(self):
        """Test is_calculated returns False when score_total is None."""
        score = Score(asset_id="TEST.US", score_total=None)
        assert score.is_calculated is False

    def test_score_is_calculated_true(self):
        """Test is_calculated returns True when score_total is set."""
        score = Score(asset_id="TEST.US", score_total=75.0)
        assert score.is_calculated is True

    def test_score_from_row(self):
        """Test creating score from database row."""
        row = {
            "asset_id": "AAPL.US",
            "score_total": 71.0,
            "score_value": 65.0,
            "score_momentum": 75.0,
            "score_safety": 70.0,
            "confidence": 85,
            "state_label": "Équilibre",
            "rsi": 55.0,
            "json_breakdown": None
        }
        score = Score.from_row(row)
        assert score.score_total == 71.0
        assert score.confidence == 85

    def test_score_with_invalid_state_label(self):
        """Test score handles invalid state label."""
        row = {
            "asset_id": "TEST.US",
            "state_label": "INVALID"
        }
        score = Score.from_row(row)
        assert score.state_label == StateLabel.NA


class TestScoreBreakdown:
    """Tests for ScoreBreakdown dataclass."""

    def test_score_breakdown_creation(self):
        """Test creating score breakdown."""
        breakdown = ScoreBreakdown(
            version="1.0",
            scoring_date="2026-01-15",
            weights={"value": 0.3, "momentum": 0.4, "safety": 0.3}
        )
        assert breakdown.version == "1.0"
        assert breakdown.scoring_date == "2026-01-15"

    def test_score_breakdown_to_json(self):
        """Test serializing breakdown to JSON."""
        breakdown = ScoreBreakdown(
            version="1.0",
            weights={"value": 0.3, "momentum": 0.4}
        )
        json_str = breakdown.to_json()
        data = json.loads(json_str)
        assert data["version"] == "1.0"
        assert data["weights"]["value"] == 0.3

    def test_score_breakdown_from_json(self):
        """Test deserializing breakdown from JSON."""
        json_str = json.dumps({
            "version": "1.0",
            "weights": {"value": 0.3, "momentum": 0.4},
            "features": {"pe_ratio": 25.5}
        })
        breakdown = ScoreBreakdown.from_json(json_str)
        assert breakdown.version == "1.0"
        assert breakdown.weights["value"] == 0.3

    def test_score_breakdown_from_empty_json(self):
        """Test deserializing empty JSON returns defaults."""
        breakdown = ScoreBreakdown.from_json("")
        assert breakdown.version == "1.0"
        assert breakdown.weights == {}

    def test_score_breakdown_from_invalid_json(self):
        """Test deserializing invalid JSON returns defaults."""
        breakdown = ScoreBreakdown.from_json("invalid json")
        assert breakdown.version == "1.0"


class TestGatingStatus:
    """Tests for GatingStatus dataclass."""

    def test_gating_status_creation(self, sample_gating_status):
        """Test creating gating status."""
        assert sample_gating_status.asset_id == "AAPL.US"
        assert sample_gating_status.eligible is True
        assert sample_gating_status.coverage == 0.98

    def test_gating_status_from_row(self):
        """Test creating gating status from database row."""
        row = {
            "asset_id": "AAPL.US",
            "coverage": 0.98,
            "liquidity": 50_000_000,
            "eligible": 1,
            "data_confidence": 95
        }
        status = GatingStatus.from_row(row)
        assert status.coverage == 0.98
        assert status.eligible is True

    def test_gating_status_handles_none_values(self):
        """Test gating status handles None and null values."""
        row = {
            "asset_id": "TEST.US",
            "coverage": None,
            "liquidity": None,
            "eligible": 0
        }
        status = GatingStatus.from_row(row)
        assert status.coverage == 0.0
        assert status.liquidity == 0.0


class TestRotationState:
    """Tests for RotationState dataclass."""

    def test_rotation_state_creation(self, sample_rotation_state):
        """Test creating rotation state."""
        assert sample_rotation_state.asset_id == "AAPL.US"
        assert sample_rotation_state.in_top50 is True
        assert sample_rotation_state.refresh_count == 25

    def test_rotation_state_from_row(self):
        """Test creating rotation state from database row."""
        row = {
            "asset_id": "AAPL.US",
            "priority_level": 1,
            "in_top50": 1,
            "refresh_count": 25
        }
        state = RotationState.from_row(row)
        assert state.priority_level == 1
        assert state.in_top50 is True


class TestWatchlistItem:
    """Tests for WatchlistItem dataclass."""

    def test_watchlist_item_creation(self, sample_watchlist_item):
        """Test creating watchlist item."""
        assert sample_watchlist_item.asset_id == "AAPL.US"
        assert sample_watchlist_item.user_id == "test_user_123"
        assert sample_watchlist_item.alert_price_above == 190.0

    def test_watchlist_item_from_row(self):
        """Test creating watchlist item from database row."""
        row = {
            "asset_id": "AAPL.US",
            "user_id": "user_123",
            "notes": "Monitor",
            "alert_price_above": 190.0,
            "symbol": "AAPL",
            "asset_type": "EQUITY"
        }
        item = WatchlistItem.from_row(row)
        assert item.asset_id == "AAPL.US"
        assert item.symbol == "AAPL"
        assert item.asset_type == AssetType.EQUITY


class TestProQuota:
    """Tests for ProQuota dataclass."""

    def test_pro_quota_creation(self, sample_pro_quota):
        """Test creating Pro quota."""
        assert sample_pro_quota.user_id == "test_user_123"
        assert sample_pro_quota.calculations_limit == 200
        assert sample_pro_quota.tier == ProTier.PRO

    def test_pro_quota_remaining(self):
        """Test remaining calculations calculation."""
        quota = ProQuota(
            calculations_used=50,
            calculations_limit=200
        )
        assert quota.remaining == 150

    def test_pro_quota_remaining_zero(self):
        """Test remaining is zero when limit reached."""
        quota = ProQuota(
            calculations_used=200,
            calculations_limit=200
        )
        assert quota.remaining == 0

    def test_pro_quota_remaining_negative(self):
        """Test remaining is zero when over limit."""
        quota = ProQuota(
            calculations_used=250,
            calculations_limit=200
        )
        assert quota.remaining == 0

    def test_pro_quota_usage_percent(self):
        """Test usage percentage calculation."""
        quota = ProQuota(
            calculations_used=100,
            calculations_limit=200
        )
        assert quota.usage_percent == 50.0

    def test_pro_quota_usage_percent_full(self):
        """Test usage percentage when full."""
        quota = ProQuota(
            calculations_used=200,
            calculations_limit=200
        )
        assert quota.usage_percent == 100.0

    def test_pro_quota_from_row(self):
        """Test creating Pro quota from database row."""
        row = {
            "user_id": "user_123",
            "calculations_used": 50,
            "calculations_limit": 200,
            "tier": "pro"
        }
        quota = ProQuota.from_row(row)
        assert quota.user_id == "user_123"
        assert quota.tier == ProTier.PRO


class TestStateLabel:
    """Tests for StateLabel enumeration."""

    def test_state_label_values(self):
        """Test state labels are defined."""
        assert StateLabel.EQUILIBRE.value == "Équilibre"
        assert StateLabel.EXTENSION_HAUTE.value == "Extension haute (+2σ)"
        assert StateLabel.NA.value == "N/A"

    def test_state_label_aliases(self):
        """Test state label aliases work."""
        assert StateLabel.EQUILIBRIUM == StateLabel.EQUILIBRE
        assert StateLabel.EXTENSION_HIGH == StateLabel.EXTENSION_HAUTE


class TestQueueStatus:
    """Tests for QueueStatus enumeration."""

    def test_queue_status_values(self):
        """Test queue statuses are defined."""
        assert QueueStatus.PENDING.value == "pending"
        assert QueueStatus.PROCESSING.value == "processing"
        assert QueueStatus.COMPLETED.value == "completed"


class TestPaginatedResult:
    """Tests for PaginatedResult dataclass."""

    def test_paginated_result_creation(self):
        """Test creating paginated result."""
        result = PaginatedResult(
            items=[1, 2, 3],
            total=30,
            page=1,
            page_size=10,
            total_pages=3
        )
        assert result.total == 30
        assert len(result.items) == 3

    def test_paginated_result_has_next(self):
        """Test has_next property."""
        result = PaginatedResult(
            items=[], total=30, page=1, page_size=10, total_pages=3
        )
        assert result.has_next is True

    def test_paginated_result_no_next(self):
        """Test has_next is False on last page."""
        result = PaginatedResult(
            items=[], total=30, page=3, page_size=10, total_pages=3
        )
        assert result.has_next is False

    def test_paginated_result_has_prev(self):
        """Test has_prev property."""
        result = PaginatedResult(
            items=[], total=30, page=2, page_size=10, total_pages=3
        )
        assert result.has_prev is True

    def test_paginated_result_no_prev(self):
        """Test has_prev is False on first page."""
        result = PaginatedResult(
            items=[], total=30, page=1, page_size=10, total_pages=3
        )
        assert result.has_prev is False


class TestProviderHealth:
    """Tests for ProviderHealth dataclass."""

    def test_provider_health_creation(self):
        """Test creating provider health."""
        health = ProviderHealth(
            provider="EODHD",
            status="healthy",
            latency_ms=150
        )
        assert health.provider == "EODHD"
        assert health.status == "healthy"
        assert health.latency_ms == 150

    def test_provider_health_degraded(self):
        """Test provider health degraded status."""
        health = ProviderHealth(
            provider="EODHD",
            status="degraded",
            message="Slow response times"
        )
        assert health.status == "degraded"
        assert health.message is not None

    def test_provider_health_down(self):
        """Test provider health down status."""
        health = ProviderHealth(
            provider="EODHD",
            status="down"
        )
        assert health.status == "down"
