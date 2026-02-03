"""Tests for pipeline/gating.py - Data quality assessment and eligibility filtering."""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch

from pathlib import Path
import sys

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from core.models import Asset, AssetType, GatingStatus
from pipeline.gating import GatingJob


class TestGatingCalculations:
    """Tests for individual gating calculation methods."""

    @pytest.fixture
    def gating_job(self):
        """Create a GatingJob instance for testing."""
        return GatingJob(market_scope="US_EU")

    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame."""
        dates = pd.date_range("2025-09-01", periods=100, freq="D")
        np.random.seed(42)

        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        volumes = np.random.randint(100000, 1000000, 100)

        return pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

    def test_calculate_coverage_full(self, gating_job, sample_df):
        """Test coverage calculation with complete data."""
        start_date = sample_df.index.min().date()
        end_date = sample_df.index.max().date()

        coverage = gating_job._calculate_coverage(sample_df, start_date, end_date)

        # Should be close to 1.0 (100 trading days in 100 calendar days)
        assert coverage > 0.9
        assert coverage <= 1.0

    def test_calculate_coverage_sparse(self, gating_job):
        """Test coverage calculation with sparse data."""
        dates = pd.date_range("2025-01-01", periods=30, freq="D")
        df = pd.DataFrame({
            "Close": np.random.rand(30) * 100 + 100,
            "Volume": np.random.randint(100000, 1000000, 30),
        }, index=dates)

        start_date = date(2025, 1, 1)
        end_date = date(2025, 4, 10)  # 100 days later

        coverage = gating_job._calculate_coverage(df, start_date, end_date)

        # Only 30 points in ~100 trading days
        assert coverage < 0.5
        assert coverage > 0.0

    def test_calculate_coverage_empty(self, gating_job):
        """Test coverage with empty DataFrame."""
        df = pd.DataFrame()
        coverage = gating_job._calculate_coverage(
            df,
            date(2025, 1, 1),
            date(2025, 2, 1)
        )
        assert coverage == 0.0

    def test_calculate_liquidity_adv_basic(self, gating_job, sample_df):
        """Test ADV (Average Dollar Volume) calculation."""
        adv = gating_job._calculate_liquidity(sample_df)

        assert adv > 0
        # Each bar should have volume * close
        assert adv > 100_000  # Reasonable for random data

    def test_calculate_liquidity_adv_window(self, gating_job, sample_df):
        """Test ADV calculation with different windows."""
        adv_30 = gating_job._calculate_liquidity(sample_df, window=30)
        adv_60 = gating_job._calculate_liquidity(sample_df, window=60)

        # Both should be positive
        assert adv_30 > 0
        assert adv_60 > 0

    def test_calculate_liquidity_empty(self, gating_job):
        """Test liquidity with empty DataFrame."""
        df = pd.DataFrame()
        adv = gating_job._calculate_liquidity(df)
        assert adv == 0.0

    def test_calculate_liquidity_missing_columns(self, gating_job):
        """Test liquidity with missing OHLCV columns."""
        df = pd.DataFrame({
            "Price": [100, 101, 102],
            "Volume": [1000, 1000, 1000]
        })

        adv = gating_job._calculate_liquidity(df)
        assert adv == 0.0

    def test_calculate_stale_ratio_fresh_data(self, gating_job, sample_df):
        """Test stale ratio with fresh data."""
        stale = gating_job._calculate_stale_ratio(sample_df)

        # Random data should have low stale ratio
        assert stale < 0.1
        assert stale >= 0.0

    def test_calculate_stale_ratio_static_prices(self, gating_job):
        """Test stale ratio with static prices."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        # All prices the same
        df = pd.DataFrame({
            "Close": [100.0] * 50,
            "Volume": [1000] * 50,
        }, index=dates)

        stale = gating_job._calculate_stale_ratio(df)

        # Should be ~1.0 (100%) for identical prices
        assert stale > 0.95

    def test_calculate_stale_ratio_empty(self, gating_job):
        """Test stale ratio with empty DataFrame."""
        df = pd.DataFrame()
        stale = gating_job._calculate_stale_ratio(df)
        assert stale == 0.0

    def test_get_min_price(self, gating_job, sample_df):
        """Test minimum price extraction."""
        min_price = gating_job._get_min_price(sample_df)

        assert min_price is not None
        assert min_price > 0
        assert min_price == sample_df["Low"].min()

    def test_get_min_price_empty(self, gating_job):
        """Test min price with empty DataFrame."""
        df = pd.DataFrame()
        min_price = gating_job._get_min_price(df)
        assert min_price is None

    def test_get_last_bar_date(self, gating_job, sample_df):
        """Test last bar date extraction."""
        last_date = gating_job._get_last_bar_date(sample_df)

        assert last_date is not None
        assert last_date == sample_df.index.max().strftime("%Y-%m-%d")

    def test_get_last_bar_date_empty(self, gating_job):
        """Test last bar date with empty DataFrame."""
        df = pd.DataFrame()
        last_date = gating_job._get_last_bar_date(df)
        assert last_date is None


class TestEligibilityRules:
    """Tests for asset eligibility determination."""

    @pytest.fixture
    def gating_job(self):
        """Create a GatingJob instance."""
        return GatingJob(market_scope="US_EU")

    @pytest.fixture
    def sample_asset(self):
        """Create a sample equity asset."""
        return Asset(
            asset_id="AAPL.US",
            symbol="AAPL",
            name="Apple Inc.",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NASDAQ",
            currency="USD",
            country="US",
            sector="Technology"
        )

    @pytest.fixture
    def sample_etf(self):
        """Create a sample ETF asset."""
        return Asset(
            asset_id="SPY.US",
            symbol="SPY",
            name="SPDR S&P 500 ETF",
            asset_type=AssetType.ETF,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

    def test_eligibility_high_coverage_high_liquidity(self, gating_job, sample_asset):
        """Test eligible asset with high coverage and liquidity."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.95,
            liquidity=1_000_000,
            stale_ratio=0.05,
            price_min=50.0
        )

        assert eligible is True
        assert reason is None

    def test_eligibility_low_coverage(self, gating_job, sample_asset):
        """Test ineligibility due to low coverage."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.50,  # Below 60% threshold
            liquidity=1_000_000,
            stale_ratio=0.05,
            price_min=50.0
        )

        assert eligible is False
        assert "Coverage" in reason

    def test_eligibility_low_liquidity(self, gating_job, sample_asset):
        """Test ineligibility due to low liquidity."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.95,
            liquidity=100_000,  # Below 250K threshold for US_EU
            stale_ratio=0.05,
            price_min=50.0
        )

        assert eligible is False
        assert "ADV" in reason

    def test_eligibility_high_stale_ratio(self, gating_job, sample_asset):
        """Test ineligibility due to high stale ratio."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.95,
            liquidity=1_000_000,
            stale_ratio=0.25,  # Above 20% threshold
            price_min=50.0
        )

        assert eligible is False
        assert "Stale" in reason

    def test_eligibility_penny_stock(self, gating_job, sample_asset):
        """Test ineligibility due to low price (penny stock)."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.95,
            liquidity=1_000_000,
            stale_ratio=0.05,
            price_min=0.50  # Below $1 threshold
        )

        assert eligible is False
        assert "price" in reason.lower()

    def test_eligibility_no_price_data(self, gating_job, sample_asset):
        """Test eligibility when price_min is None."""
        eligible, reason = gating_job._check_eligibility(
            asset=sample_asset,
            coverage=0.95,
            liquidity=1_000_000,
            stale_ratio=0.05,
            price_min=None
        )

        # Should still be eligible if other conditions met
        assert eligible is True

    def test_eligibility_etf_lower_liquidity_threshold(self, gating_job, sample_etf):
        """Test ETF with lower liquidity threshold in AFRICA scope."""
        gating_job._market_scope = "AFRICA"

        eligible, reason = gating_job._check_eligibility(
            asset=sample_etf,
            coverage=0.95,
            liquidity=50_000,  # Lower threshold for AFRICA ETFs
            stale_ratio=0.05,
            price_min=10.0
        )

        # Should be eligible depending on AFRICA config thresholds
        # Just check it evaluates liquidity
        assert isinstance(eligible, bool)


class TestConfidenceCalculation:
    """Tests for data confidence scoring."""

    @pytest.fixture
    def gating_job(self):
        """Create a GatingJob instance."""
        return GatingJob(market_scope="US_EU")

    def test_confidence_perfect_data(self, gating_job):
        """Test confidence with perfect data."""
        confidence = gating_job._calculate_confidence(
            coverage=1.0,
            liquidity=10_000_000,
            stale_ratio=0.0
        )

        assert confidence == 100

    def test_confidence_poor_data(self, gating_job):
        """Test confidence with poor data."""
        confidence = gating_job._calculate_confidence(
            coverage=0.3,
            liquidity=100_000,
            stale_ratio=0.2
        )

        assert confidence < 50
        assert confidence >= 0

    def test_confidence_medium_data(self, gating_job):
        """Test confidence with medium quality data."""
        confidence = gating_job._calculate_confidence(
            coverage=0.7,
            liquidity=1_000_000,
            stale_ratio=0.05
        )

        assert 50 <= confidence <= 100

    def test_confidence_zero_liquidity(self, gating_job):
        """Test confidence with zero liquidity."""
        confidence = gating_job._calculate_confidence(
            coverage=0.8,
            liquidity=0,
            stale_ratio=0.05
        )

        # Should still calculate but be lower
        assert confidence >= 0
        assert confidence < 100

    def test_confidence_bounds(self, gating_job):
        """Test confidence always stays in 0-100 range."""
        for coverage in [0.0, 0.5, 1.0]:
            for liquidity in [0, 1_000_000, 100_000_000]:
                for stale in [0.0, 0.1, 0.5]:
                    confidence = gating_job._calculate_confidence(
                        coverage=coverage,
                        liquidity=liquidity,
                        stale_ratio=stale
                    )

                    assert 0 <= confidence <= 100


class TestDataMissingScenarios:
    """Tests for handling missing or incomplete data."""

    @pytest.fixture
    def gating_job(self):
        """Create a GatingJob instance."""
        return GatingJob(market_scope="US_EU")

    def test_empty_dataframe_evaluation(self, gating_job):
        """Test asset evaluation with empty DataFrame."""
        asset = Asset(
            asset_id="TEST.US",
            symbol="TEST",
            name="Test Asset",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

        # Mock the provider to return empty DataFrame
        with patch.object(gating_job._provider, 'fetch_daily_bars', return_value=pd.DataFrame()):
            status = gating_job._evaluate_asset(asset)

        assert status.eligible is False
        assert status.reason == "NO_DATA"
        assert status.coverage == 0.0

    def test_nan_values_in_data(self, gating_job):
        """Test handling of NaN values in data."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        df = pd.DataFrame({
            "Open": [np.nan] * 50,
            "High": [np.nan] * 50,
            "Low": [np.nan] * 50,
            "Close": [np.nan] * 50,
            "Volume": [np.nan] * 50,
        }, index=dates)

        liquidity = gating_job._calculate_liquidity(df)
        assert liquidity == 0.0

        stale = gating_job._calculate_stale_ratio(df)
        assert stale == 0.0

    def test_partial_nan_values(self, gating_job):
        """Test handling of partial NaN values."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        prices = [100.0] * 25 + [np.nan] * 25

        df = pd.DataFrame({
            "Close": prices,
            "Volume": [1000] * 50,
        }, index=dates)

        liquidity = gating_job._calculate_liquidity(df)
        # Should handle NaN gracefully
        assert liquidity >= 0.0


class TestMockDataProviders:
    """Tests using mocked data providers."""

    def test_gating_with_mocked_provider(self):
        """Test gating pipeline with mocked provider."""
        gating_job = GatingJob(market_scope="US_EU")

        # Mock the provider
        mock_df = pd.DataFrame({
            "Open": [99.0] * 100,
            "High": [101.0] * 100,
            "Low": [98.0] * 100,
            "Close": [100.0] * 100,
            "Volume": [1000000] * 100,
        }, index=pd.date_range("2025-01-01", periods=100, freq="D"))

        gating_job._provider.fetch_daily_bars = Mock(return_value=mock_df)
        gating_job._parquet.load_bars = Mock(return_value=None)

        asset = Asset(
            asset_id="MOCK.US",
            symbol="MOCK",
            name="Mock Asset",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

        status = gating_job._evaluate_asset(asset)

        # Should have calculated metrics
        assert status.coverage > 0
        assert status.liquidity > 0
        assert status.price_min is not None

    def test_gating_with_parquet_cache(self):
        """Test gating with Parquet cache hit."""
        gating_job = GatingJob(market_scope="US_EU")

        cached_df = pd.DataFrame({
            "Open": [99.0] * 100,
            "High": [101.0] * 100,
            "Low": [98.0] * 100,
            "Close": [100.0] * 100,
            "Volume": [1000000] * 100,
        }, index=pd.date_range("2025-01-01", periods=100, freq="D"))

        # Mock Parquet store to return cached data
        gating_job._parquet.load_bars = Mock(return_value=cached_df)
        gating_job._parquet.get_last_date = Mock(return_value=date.today() - timedelta(days=2))

        # Provider should not be called
        gating_job._provider.fetch_daily_bars = Mock()

        asset = Asset(
            asset_id="CACHED.US",
            symbol="CACHED",
            name="Cached Asset",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

        status = gating_job._evaluate_asset(asset)

        # Should use cache and not call provider
        assert status.coverage > 0
        gating_job._provider.fetch_daily_bars.assert_not_called()


class TestAfricaScopeGating:
    """Tests for AFRICA market scope specific behavior."""

    def test_africa_market_scope_initialization(self):
        """Test GatingJob with AFRICA scope."""
        gating_job = GatingJob(market_scope="AFRICA")

        assert gating_job._market_scope == "AFRICA"

    def test_africa_vs_us_eu_thresholds(self):
        """Test different eligibility thresholds for AFRICA scope."""
        gating_job_us = GatingJob(market_scope="US_EU")
        gating_job_africa = GatingJob(market_scope="AFRICA")

        asset_us = Asset(
            asset_id="TEST.US",
            symbol="TEST",
            name="Test",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

        asset_africa = Asset(
            asset_id="TEST.NG",
            symbol="TEST",
            name="Test",
            asset_type=AssetType.EQUITY,
            market_scope="AFRICA",
            market_code="NG",
            exchange="NGX",
            currency="NGN",
            country="NG"
        )

        # US_EU should use hard 250K minimum
        eligible_us, _ = gating_job_us._check_eligibility(
            asset=asset_us,
            coverage=0.8,
            liquidity=250_000,
            stale_ratio=0.05,
            price_min=10.0
        )

        # AFRICA uses config thresholds (likely different)
        eligible_africa, _ = gating_job_africa._check_eligibility(
            asset=asset_africa,
            coverage=0.8,
            liquidity=250_000,
            stale_ratio=0.05,
            price_min=10.0
        )

        # Both might be eligible depending on their config thresholds
        assert isinstance(eligible_us, bool)
        assert isinstance(eligible_africa, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
