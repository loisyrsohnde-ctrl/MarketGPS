"""
Tests for asset_query module.

PR3: Validates centralized query builder logic.

Run with:
    cd backend && python -m pytest tests/test_asset_query.py -v
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asset_query import (
    AssetFilters,
    AssetQueryBuilder,
    MarketScope,
    AFRICA_REGIONS,
    AFRICA_COUNTRY_EXCHANGES,
    get_countries_for_region,
    get_region_for_country,
    get_exchanges_for_country,
    validate_geographic_hierarchy,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FILTER VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAssetFiltersValidation:
    """Test AssetFilters validation logic."""

    def test_default_filters_are_valid(self):
        """Default filters should be valid."""
        filters = AssetFilters()
        assert filters.is_valid()
        assert filters.market_scope == "US_EU"
        assert filters.only_scored is True

    def test_valid_us_eu_scope(self):
        """US_EU scope with valid market_code."""
        filters = AssetFilters(market_scope="US_EU", market_code="US")
        assert filters.is_valid()

        filters = AssetFilters(market_scope="US_EU", market_code="EU")
        assert filters.is_valid()

    def test_invalid_market_code_for_us_eu(self):
        """Invalid market_code for US_EU scope."""
        filters = AssetFilters(market_scope="US_EU", market_code="ZA")
        errors = filters.validate()
        assert len(errors) > 0
        assert "Invalid market_code" in errors[0]

    def test_market_code_invalid_for_africa(self):
        """market_code should not be used with AFRICA scope."""
        filters = AssetFilters(market_scope="AFRICA", market_code="US")
        errors = filters.validate()
        assert len(errors) > 0
        assert "only valid for US_EU" in errors[0]

    def test_valid_africa_region(self):
        """Valid AFRICA region."""
        filters = AssetFilters(market_scope="AFRICA", region="SOUTHERN")
        assert filters.is_valid()

        filters = AssetFilters(market_scope="AFRICA", region="WEST")
        assert filters.is_valid()

    def test_invalid_region_for_us_eu(self):
        """Region should not be used with US_EU scope."""
        filters = AssetFilters(market_scope="US_EU", region="SOUTHERN")
        errors = filters.validate()
        assert len(errors) > 0
        assert "only valid for AFRICA" in errors[0]

    def test_invalid_region_name(self):
        """Invalid region name for AFRICA."""
        filters = AssetFilters(market_scope="AFRICA", region="INVALID")
        errors = filters.validate()
        assert len(errors) > 0
        assert "Invalid region" in errors[0]

    def test_valid_africa_country(self):
        """Valid AFRICA country."""
        filters = AssetFilters(market_scope="AFRICA", country="ZA")
        assert filters.is_valid()

        filters = AssetFilters(market_scope="AFRICA", country="NG")
        assert filters.is_valid()

    def test_invalid_africa_country(self):
        """Invalid country for AFRICA scope."""
        filters = AssetFilters(market_scope="AFRICA", country="XX")
        errors = filters.validate()
        assert len(errors) > 0
        assert "Invalid AFRICA country" in errors[0]

    def test_country_region_consistency(self):
        """Country must belong to specified region."""
        # ZA is in SOUTHERN
        filters = AssetFilters(market_scope="AFRICA", region="SOUTHERN", country="ZA")
        assert filters.is_valid()

        # NG is in WEST, not SOUTHERN
        filters = AssetFilters(market_scope="AFRICA", region="SOUTHERN", country="NG")
        errors = filters.validate()
        assert len(errors) > 0
        assert "not in region" in errors[0]

    def test_valid_liquidity_tiers(self):
        """Valid liquidity tier values."""
        for tier in ["A", "B", "C", "D"]:
            filters = AssetFilters(min_liquidity_tier=tier)
            assert filters.is_valid()

    def test_invalid_liquidity_tier(self):
        """Invalid liquidity tier."""
        filters = AssetFilters(min_liquidity_tier="X")
        errors = filters.validate()
        assert len(errors) > 0
        assert "Invalid liquidity_tier" in errors[0]


# ═══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHIC UTILITY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGeographicUtilities:
    """Test geographic utility functions."""

    def test_get_countries_for_region(self):
        """Get countries for region."""
        southern = get_countries_for_region("SOUTHERN")
        assert "ZA" in southern
        assert "BW" in southern

        west = get_countries_for_region("WEST")
        assert "NG" in west
        assert "GH" in west

        # Invalid region returns empty list
        invalid = get_countries_for_region("INVALID")
        assert invalid == []

    def test_get_region_for_country(self):
        """Get region for country."""
        assert get_region_for_country("ZA") == "SOUTHERN"
        assert get_region_for_country("NG") == "WEST"
        assert get_region_for_country("KE") == "EAST"
        assert get_region_for_country("EG") == "NORTH"

        # Invalid country returns None
        assert get_region_for_country("XX") is None

    def test_get_exchanges_for_country(self):
        """Get exchanges for country."""
        assert "JSE" in get_exchanges_for_country("ZA")
        assert "NGX" in get_exchanges_for_country("NG")
        assert "NSE" in get_exchanges_for_country("KE")

        # Invalid country returns empty list
        assert get_exchanges_for_country("XX") == []

    def test_validate_geographic_hierarchy(self):
        """Test hierarchy validation function."""
        # Valid
        valid, error = validate_geographic_hierarchy("AFRICA", "SOUTHERN", "ZA")
        assert valid is True
        assert error is None

        # Invalid: country not in region
        valid, error = validate_geographic_hierarchy("AFRICA", "SOUTHERN", "NG")
        assert valid is False
        assert error is not None


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY BUILDER CONDITION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestQueryBuilderConditions:
    """Test query condition building (without database)."""

    class MockStore:
        """Mock store for testing query building."""
        pass

    def test_build_conditions_market_scope(self):
        """Test market_scope condition building."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(market_scope="US_EU")

        conditions, params = builder._build_conditions(filters)

        assert "u.market_scope = ?" in conditions
        assert "US_EU" in params

    def test_build_conditions_market_code(self):
        """Test market_code condition building."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(market_scope="US_EU", market_code="US")

        conditions, params = builder._build_conditions(filters)

        assert "u.market_code = ?" in conditions
        assert "US" in params

    def test_build_conditions_only_scored(self):
        """Test only_scored condition building."""
        builder = AssetQueryBuilder(self.MockStore())

        # With only_scored=True
        filters = AssetFilters(only_scored=True)
        conditions, params = builder._build_conditions(filters)
        assert "s.score_total IS NOT NULL" in conditions

        # With only_scored=False
        filters = AssetFilters(only_scored=False)
        conditions, params = builder._build_conditions(filters)
        assert "s.score_total IS NOT NULL" not in conditions

    def test_build_conditions_asset_type(self):
        """Test asset_type condition building."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(asset_type="EQUITY")

        conditions, params = builder._build_conditions(filters)

        assert "u.asset_type = ?" in conditions
        assert "EQUITY" in params

    def test_build_conditions_query_search(self):
        """Test text search condition building."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(query="AAPL", only_scored=False)

        conditions, params = builder._build_conditions(filters)

        assert any("LIKE" in c for c in conditions)
        assert "%AAPL%" in params

    def test_build_conditions_country(self):
        """Test country condition building (exchange pattern)."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(market_scope="AFRICA", country="ZA", only_scored=False)

        conditions, params = builder._build_conditions(filters)

        # Should have exchange pattern condition
        assert any("LIKE" in c for c in conditions)
        assert "JSE:%" in params

    def test_build_conditions_region(self):
        """Test region condition building (expands to exchanges)."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(market_scope="AFRICA", region="SOUTHERN", only_scored=False)

        conditions, params = builder._build_conditions(filters)

        # Should have multiple exchange patterns for all countries in region
        assert "JSE:%" in params  # ZA

    def test_build_conditions_institutional(self):
        """Test institutional filter conditions."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(
            institutional_only=True,
            min_liquidity_tier="B",
            exclude_flagged=True,
        )

        conditions, params = builder._build_conditions(filters)

        assert "s.score_institutional IS NOT NULL" in conditions
        assert any("liquidity_tier IN" in c for c in conditions)
        assert any("flagged" in c for c in conditions)

    def test_build_conditions_score_range(self):
        """Test score range conditions."""
        builder = AssetQueryBuilder(self.MockStore())
        filters = AssetFilters(min_score=50.0, max_score=90.0)

        conditions, params = builder._build_conditions(filters)

        assert "s.score_total >= ?" in conditions
        assert "s.score_total <= ?" in conditions
        assert 50.0 in params
        assert 90.0 in params


# ═══════════════════════════════════════════════════════════════════════════════
# SORT COLUMN MAPPING TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSortColumnMapping:
    """Test sort column mapping."""

    class MockStore:
        pass

    def test_sort_column_mapping(self):
        """Test various sort column mappings."""
        builder = AssetQueryBuilder(self.MockStore())

        assert builder._map_sort_column("score_total") == "s.score_total"
        assert builder._map_sort_column("score") == "s.score_total"
        assert builder._map_sort_column("symbol") == "u.symbol"
        assert builder._map_sort_column("score_institutional") == "s.score_institutional"

        # Unknown column defaults to score_total
        assert builder._map_sort_column("unknown") == "s.score_total"


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstants:
    """Test module constants are correctly defined."""

    def test_africa_regions_complete(self):
        """All AFRICA regions are defined."""
        assert "SOUTHERN" in AFRICA_REGIONS
        assert "WEST" in AFRICA_REGIONS
        assert "EAST" in AFRICA_REGIONS
        assert "NORTH" in AFRICA_REGIONS

    def test_africa_exchanges_mapped(self):
        """Key African exchanges are mapped."""
        assert "ZA" in AFRICA_COUNTRY_EXCHANGES  # JSE
        assert "NG" in AFRICA_COUNTRY_EXCHANGES  # NGX
        assert "KE" in AFRICA_COUNTRY_EXCHANGES  # NSE
        assert "EG" in AFRICA_COUNTRY_EXCHANGES  # EGX

    def test_market_scope_enum(self):
        """MarketScope enum values."""
        assert MarketScope.US_EU.value == "US_EU"
        assert MarketScope.AFRICA.value == "AFRICA"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION SMOKE TEST (requires database)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "storage", "sqlite_store.py")),
    reason="Storage module not available"
)
class TestQueryBuilderIntegration:
    """Integration tests requiring actual database."""

    @pytest.fixture
    def store(self):
        """Create test store instance."""
        try:
            from storage.sqlite_store import SQLiteStore
            return SQLiteStore()
        except Exception:
            pytest.skip("Database not available")

    def test_search_us_eu_scored(self, store):
        """Search US_EU scored assets."""
        builder = AssetQueryBuilder(store)
        filters = AssetFilters(
            market_scope="US_EU",
            only_scored=True,
            limit=10,
        )

        results, total = builder.search(filters)

        assert isinstance(results, list)
        assert isinstance(total, int)
        # Results should have score_total if only_scored=True
        for r in results:
            if r.get("score_total") is not None:
                assert isinstance(r["score_total"], (int, float))

    def test_get_top_scored_convenience(self, store):
        """Test get_top_scored convenience method."""
        builder = AssetQueryBuilder(store)
        results = builder.get_top_scored(market_scope="US_EU", limit=5)

        assert isinstance(results, list)
        assert len(results) <= 5

    def test_explorer_with_pagination(self, store):
        """Test explorer with pagination."""
        builder = AssetQueryBuilder(store)

        # First page
        results1, total = builder.get_explorer(
            market_scope="US_EU",
            only_scored=False,
            limit=10,
            offset=0,
        )

        # Second page
        results2, _ = builder.get_explorer(
            market_scope="US_EU",
            only_scored=False,
            limit=10,
            offset=10,
        )

        # Should be different results (if enough data)
        if total > 10:
            ids1 = {r.get("asset_id") for r in results1}
            ids2 = {r.get("asset_id") for r in results2}
            assert ids1.isdisjoint(ids2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
