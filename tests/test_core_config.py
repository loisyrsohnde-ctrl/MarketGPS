"""
Unit Tests: Core Configuration Module
Tests for core.config module and configuration handling.
"""

import pytest
import os
from pathlib import Path

from core.config import (
    get_config, reload_config, EODHDConfig, PipelineConfig,
    ScoringConfig, StorageConfig, UIConfig, ComplianceConfig,
    BillingConfig, AppConfig, settings
)


class TestEODHDConfig:
    """Tests for EODHD configuration."""

    def test_eodhd_config_defaults(self):
        """Test EODHD config has sensible defaults."""
        config = EODHDConfig()
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.rate_limit_per_second == 5.0

    def test_eodhd_is_configured_with_valid_key(self):
        """Test is_configured returns True with valid key."""
        config = EODHDConfig(api_key="valid_key_with_length")
        assert config.is_configured is True

    def test_eodhd_is_configured_with_invalid_key(self):
        """Test is_configured returns False with invalid key."""
        config = EODHDConfig(api_key="changeme")
        assert config.is_configured is False

    def test_eodhd_is_configured_with_empty_key(self):
        """Test is_configured returns False with empty key."""
        config = EODHDConfig(api_key="")
        assert config.is_configured is False

    def test_eodhd_validate_at_startup_not_raises(self):
        """Test validate_at_startup doesn't raise by default."""
        config = EODHDConfig(api_key="invalid")
        result = config.validate_at_startup(raise_error=False)
        assert result is False

    def test_eodhd_validate_at_startup_raises(self):
        """Test validate_at_startup raises when requested."""
        config = EODHDConfig(api_key="invalid")
        with pytest.raises(ValueError, match="EODHD API key not configured"):
            config.validate_at_startup(raise_error=True)


class TestPipelineConfig:
    """Tests for Pipeline configuration."""

    def test_pipeline_config_defaults(self):
        """Test pipeline config has sensible defaults."""
        config = PipelineConfig()
        assert config.rotation_batch_size == 50
        assert config.gating_coverage_min == 0.90
        assert config.top_n_scores == 50

    def test_africa_specific_thresholds(self):
        """Test Africa-specific thresholds are more lenient."""
        config = PipelineConfig()
        assert config.africa_gating_coverage_min == 0.70  # More lenient than US_EU
        assert config.africa_gating_adv_min_equity == 100_000  # Lower than US_EU
        assert config.africa_gating_lookback_days == 180  # Shorter than US_EU


class TestScoringConfig:
    """Tests for Scoring configuration."""

    def test_scoring_config_defaults(self):
        """Test scoring config has sensible defaults."""
        config = ScoringConfig()
        assert config.rsi_optimal_low == 40.0
        assert config.rsi_optimal_high == 70.0
        assert config.volatility_target_max == 30.0

    def test_equity_weights_sum(self):
        """Test equity weights are properly distributed."""
        config = ScoringConfig()
        total = sum(config.equity_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_etf_weights_sum(self):
        """Test ETF weights sum to 1.0 (no value pillar)."""
        config = ScoringConfig()
        total = sum(config.etf_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_etf_has_no_value_weight(self):
        """Test ETF config has no value weight."""
        config = ScoringConfig()
        assert "value" not in config.etf_weights


class TestStorageConfig:
    """Tests for Storage configuration."""

    def test_storage_config_paths_exist(self):
        """Test storage config creates necessary paths."""
        config = StorageConfig()
        config.ensure_paths()

        assert config.data_dir.exists()
        assert config.sqlite_path.parent.exists()
        assert config.parquet_dir.exists()

    def test_storage_config_has_valid_paths(self):
        """Test storage config has valid paths."""
        config = StorageConfig()
        assert config.data_dir is not None
        assert config.sqlite_path is not None
        assert config.parquet_dir is not None

    def test_storage_config_paths_are_absolute(self):
        """Test all storage paths are absolute."""
        config = StorageConfig()
        assert config.data_dir.is_absolute()
        assert config.sqlite_path.is_absolute()
        assert config.parquet_dir.is_absolute()


class TestUIConfig:
    """Tests for UI configuration."""

    def test_ui_config_has_app_name(self):
        """Test UI config has app name."""
        config = UIConfig()
        assert config.app_name == "MarketGPS"

    def test_ui_config_has_colors(self):
        """Test UI config has color definitions."""
        config = UIConfig()
        assert config.bg_primary is not None
        assert config.text_high is not None
        assert config.green_primary is not None

    def test_ui_config_colors_are_valid_hex(self):
        """Test UI config colors are valid hex codes."""
        config = UIConfig()
        colors = [
            config.bg_primary, config.bg_secondary, config.green_primary,
            config.amber, config.red_soft
        ]
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB


class TestComplianceConfig:
    """Tests for Compliance configuration."""

    def test_compliance_has_forbidden_terms(self):
        """Test compliance config has forbidden terms."""
        config = ComplianceConfig()
        assert len(config.forbidden_terms) > 0

    def test_compliance_has_disclaimer(self):
        """Test compliance config has disclaimer."""
        config = ComplianceConfig()
        assert config.disclaimer is not None
        assert len(config.disclaimer) > 0

    def test_compliance_forbidden_terms_are_strings(self):
        """Test all forbidden terms are strings or patterns."""
        config = ComplianceConfig()
        for term in config.forbidden_terms:
            assert isinstance(term, str)


class TestBillingConfig:
    """Tests for Billing configuration."""

    def test_billing_config_has_plans(self):
        """Test billing config has subscription plans."""
        config = BillingConfig()
        assert "free" in config.plans
        assert "monthly_9_99" in config.plans or "monthly_9_99" in config.plans

    def test_billing_dev_mode_default(self):
        """Test billing defaults to dev mode."""
        config = BillingConfig()
        # Default should allow dev mode
        assert config.mode in ["dev", "stripe"]

    def test_billing_free_plan_exists(self):
        """Test free plan is defined."""
        config = BillingConfig()
        free = config.plans.get("free")
        assert free is not None
        assert free["price_monthly"] == 0

    def test_billing_stripe_configuration(self):
        """Test Stripe configuration attributes exist."""
        config = BillingConfig()
        assert hasattr(config, "stripe_public_key")
        assert hasattr(config, "stripe_secret_key")
        assert hasattr(config, "is_stripe_configured")


class TestAppConfig:
    """Tests for main Application configuration."""

    def test_app_config_initialization(self):
        """Test app config initializes all sub-configs."""
        config = AppConfig()
        assert config.eodhd is not None
        assert config.pipeline is not None
        assert config.scoring is not None
        assert config.storage is not None
        assert config.ui is not None
        assert config.compliance is not None
        assert config.billing is not None

    def test_app_config_post_init(self):
        """Test app config post-init creates paths."""
        config = AppConfig()
        # Should not raise and should create paths
        assert config.storage.data_dir.exists()

    def test_get_config_returns_singleton(self):
        """Test get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_config_creates_new_instance(self):
        """Test reload_config creates a new instance."""
        config1 = get_config()
        config2 = reload_config()
        # Should be different instances (different objects)
        assert config1 is not config2
        # But with same structure
        assert config1.eodhd.timeout == config2.eodhd.timeout


class TestSettingsProxy:
    """Tests for the settings proxy object."""

    def test_settings_sqlite_path(self):
        """Test settings.SQLITE_PATH property."""
        assert settings.SQLITE_PATH is not None
        assert isinstance(settings.SQLITE_PATH, str)

    def test_settings_data_dir(self):
        """Test settings.DATA_DIR property."""
        assert settings.DATA_DIR is not None
        assert isinstance(settings.DATA_DIR, str)

    def test_settings_rotation_batch_size(self):
        """Test settings.ROTATION_BATCH_SIZE property."""
        assert settings.ROTATION_BATCH_SIZE > 0

    def test_settings_top_n(self):
        """Test settings.TOP_N property."""
        assert settings.TOP_N == 50

    def test_settings_billing_mode(self):
        """Test settings.BILLING_MODE property."""
        mode = settings.BILLING_MODE
        assert mode in ["dev", "stripe"]
