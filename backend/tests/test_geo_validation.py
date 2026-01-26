"""
Tests for geo_validation module (PR6).

Run with:
    cd backend && python -m pytest tests/test_geo_validation.py -v
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from geo_validation import (
    GeoValidator,
    GeoValidationError,
    GeoValidationResult,
    GeoErrorCode,
    validate_asset,
    ALL_AFRICA_COUNTRIES,
    ALL_AFRICA_REGIONS,
    ALL_AFRICA_EXCHANGES,
    ALL_US_EU_EXCHANGES,
)


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGeoValidator:
    """Test GeoValidator class."""

    @pytest.fixture
    def validator(self):
        return GeoValidator()

    # ─────────────────────────────────────────────────────────────────────────
    # Valid Assets
    # ─────────────────────────────────────────────────────────────────────────

    def test_valid_us_eu_asset(self, validator):
        """Valid US_EU asset passes validation."""
        asset = {
            "asset_id": "NYSE:AAPL",
            "market_scope": "US_EU",
            "market_code": "US",
            "exchange": "NYSE",
        }
        result = validator.validate_asset(asset)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_africa_asset(self, validator):
        """Valid AFRICA asset passes validation."""
        asset = {
            "asset_id": "JSE:NPN",
            "market_scope": "AFRICA",
            "country": "ZA",
            "exchange": "JSE",
        }
        result = validator.validate_asset(asset)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_africa_asset_with_region(self, validator):
        """Valid AFRICA asset with region passes validation."""
        asset = {
            "asset_id": "JSE:SOL",
            "market_scope": "AFRICA",
            "region": "SOUTHERN",
            "country": "ZA",
            "exchange": "JSE",
        }
        result = validator.validate_asset(asset)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_nigeria_asset(self, validator):
        """Valid Nigerian asset passes validation."""
        asset = {
            "asset_id": "NGX:DANGCEM",
            "market_scope": "AFRICA",
            "region": "WEST",
            "country": "NG",
            "exchange": "NGX",
        }
        result = validator.validate_asset(asset)
        assert result.is_valid

    # ─────────────────────────────────────────────────────────────────────────
    # Missing Required Fields
    # ─────────────────────────────────────────────────────────────────────────

    def test_missing_market_scope(self, validator):
        """Missing market_scope fails validation."""
        asset = {
            "asset_id": "TEST:ABC",
            "exchange": "NYSE",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.MISSING_REQUIRED_FIELD for e in result.errors)

    def test_invalid_market_scope(self, validator):
        """Invalid market_scope fails validation."""
        asset = {
            "asset_id": "TEST:ABC",
            "market_scope": "INVALID",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.INVALID_SCOPE for e in result.errors)

    # ─────────────────────────────────────────────────────────────────────────
    # Cross-Scope Leaks
    # ─────────────────────────────────────────────────────────────────────────

    def test_africa_exchange_in_us_eu_scope(self, validator):
        """African exchange in US_EU scope is a cross-scope leak."""
        asset = {
            "asset_id": "JSE:TEST",
            "market_scope": "US_EU",
            "exchange": "JSE",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.CROSS_SCOPE_LEAK for e in result.errors)

    def test_us_exchange_in_africa_scope(self, validator):
        """US exchange in AFRICA scope is a cross-scope leak."""
        asset = {
            "asset_id": "NYSE:TEST",
            "market_scope": "AFRICA",
            "exchange": "NYSE",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.CROSS_SCOPE_LEAK for e in result.errors)

    def test_african_country_in_us_eu_warns(self, validator):
        """African country set for US_EU asset generates warning."""
        asset = {
            "asset_id": "NYSE:TEST",
            "market_scope": "US_EU",
            "exchange": "NYSE",
            "country": "ZA",  # South Africa in US_EU scope
        }
        result = validator.validate_asset(asset)
        # May be valid but with warning
        assert any(w.code == GeoErrorCode.CROSS_SCOPE_LEAK for w in result.warnings)

    # ─────────────────────────────────────────────────────────────────────────
    # AFRICA-Specific Validations
    # ─────────────────────────────────────────────────────────────────────────

    def test_invalid_africa_country(self, validator):
        """Invalid African country fails validation."""
        asset = {
            "asset_id": "JSE:TEST",
            "market_scope": "AFRICA",
            "country": "XX",  # Invalid country
            "exchange": "JSE",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.COUNTRY_NOT_IN_SCOPE for e in result.errors)

    def test_exchange_not_matching_country(self, validator):
        """Exchange not valid for country fails validation."""
        asset = {
            "asset_id": "NGX:TEST",
            "market_scope": "AFRICA",
            "country": "ZA",  # South Africa
            "exchange": "NGX",  # Nigerian exchange
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.EXCHANGE_NOT_FOR_COUNTRY for e in result.errors)

    def test_invalid_africa_region(self, validator):
        """Invalid African region fails validation."""
        asset = {
            "asset_id": "JSE:TEST",
            "market_scope": "AFRICA",
            "region": "INVALID_REGION",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.INVALID_REGION for e in result.errors)

    def test_country_not_in_region(self, validator):
        """Country not in specified region fails validation."""
        asset = {
            "asset_id": "JSE:TEST",
            "market_scope": "AFRICA",
            "region": "WEST",  # West Africa
            "country": "ZA",  # South Africa (SOUTHERN region)
            "exchange": "JSE",
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid
        assert any(e.code == GeoErrorCode.COUNTRY_NOT_IN_REGION for e in result.errors)

    # ─────────────────────────────────────────────────────────────────────────
    # Asset ID Exchange Extraction
    # ─────────────────────────────────────────────────────────────────────────

    def test_exchange_extracted_from_asset_id(self, validator):
        """Exchange is extracted from asset_id if not provided."""
        asset = {
            "asset_id": "JSE:NPN",
            "market_scope": "AFRICA",
            "country": "ZA",
            # No explicit exchange field
        }
        result = validator.validate_asset(asset)
        assert result.is_valid  # JSE extracted from asset_id matches ZA


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateAssetFunction:
    """Test the simple validate_asset function."""

    def test_valid_asset_returns_true(self):
        """Valid asset returns (True, [])."""
        asset = {
            "asset_id": "NYSE:AAPL",
            "market_scope": "US_EU",
            "exchange": "NYSE",
        }
        is_valid, errors = validate_asset(asset)
        assert is_valid is True
        assert errors == []

    def test_invalid_asset_returns_errors(self):
        """Invalid asset returns (False, [error messages])."""
        asset = {
            "asset_id": "JSE:TEST",
            "market_scope": "US_EU",  # Wrong scope for JSE
            "exchange": "JSE",
        }
        is_valid, errors = validate_asset(asset)
        assert is_valid is False
        assert len(errors) > 0
        # Check for any error about scope/exchange mismatch
        assert any("JSE" in e or "scope" in e.lower() or "African" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION RESULT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidationResult:
    """Test GeoValidationResult dataclass."""

    def test_to_dict(self):
        """to_dict returns proper structure."""
        error = GeoValidationError(
            code=GeoErrorCode.INVALID_SCOPE,
            message="Test error",
            field="market_scope",
        )
        result = GeoValidationResult(
            asset_id="TEST:ABC",
            is_valid=False,
            errors=[error],
        )

        d = result.to_dict()

        assert d["asset_id"] == "TEST:ABC"
        assert d["is_valid"] is False
        assert d["error_count"] == 1
        assert len(d["errors"]) == 1
        assert d["errors"][0]["code"] == GeoErrorCode.INVALID_SCOPE

    def test_valid_result_has_no_errors(self):
        """Valid result has empty errors list."""
        result = GeoValidationResult(
            asset_id="TEST:ABC",
            is_valid=True,
        )
        assert result.errors == []
        assert result.warnings == []


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstants:
    """Test geographic constants are complete."""

    def test_africa_countries_complete(self):
        """Key African countries are defined."""
        assert "ZA" in ALL_AFRICA_COUNTRIES  # South Africa
        assert "NG" in ALL_AFRICA_COUNTRIES  # Nigeria
        assert "KE" in ALL_AFRICA_COUNTRIES  # Kenya
        assert "EG" in ALL_AFRICA_COUNTRIES  # Egypt

    def test_africa_regions_complete(self):
        """All African regions are defined."""
        assert "SOUTHERN" in ALL_AFRICA_REGIONS
        assert "WEST" in ALL_AFRICA_REGIONS
        assert "EAST" in ALL_AFRICA_REGIONS
        assert "NORTH" in ALL_AFRICA_REGIONS

    def test_africa_exchanges_defined(self):
        """Key African exchanges are defined."""
        assert "JSE" in ALL_AFRICA_EXCHANGES  # South Africa
        assert "NGX" in ALL_AFRICA_EXCHANGES  # Nigeria
        assert "NSE" in ALL_AFRICA_EXCHANGES  # Kenya
        assert "EGX" in ALL_AFRICA_EXCHANGES  # Egypt

    def test_us_eu_exchanges_defined(self):
        """Key US/EU exchanges are defined."""
        assert "NYSE" in ALL_US_EU_EXCHANGES
        assert "NASDAQ" in ALL_US_EU_EXCHANGES

    def test_no_exchange_overlap(self):
        """African and US/EU exchanges don't overlap."""
        overlap = ALL_AFRICA_EXCHANGES & ALL_US_EU_EXCHANGES
        assert len(overlap) == 0, f"Overlapping exchanges: {overlap}"


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def validator(self):
        return GeoValidator()

    def test_empty_asset(self, validator):
        """Empty asset fails validation."""
        result = validator.validate_asset({})
        assert not result.is_valid

    def test_none_values(self, validator):
        """None values are handled gracefully."""
        asset = {
            "asset_id": "TEST:ABC",
            "market_scope": None,
            "exchange": None,
        }
        result = validator.validate_asset(asset)
        assert not result.is_valid

    def test_asset_without_exchange(self, validator):
        """Asset without exchange can still be validated."""
        asset = {
            "asset_id": "TEST",  # No exchange prefix
            "market_scope": "US_EU",
        }
        result = validator.validate_asset(asset)
        # Should not error on missing exchange (just can't validate it)
        # market_scope is valid, so should pass basic validation
        assert result.is_valid

    def test_case_sensitivity_market_scope(self, validator):
        """Market scope is case-sensitive."""
        asset = {
            "asset_id": "NYSE:TEST",
            "market_scope": "us_eu",  # lowercase
        }
        result = validator.validate_asset(asset)
        # Should fail because scope is case-sensitive
        assert not result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
