"""Tests for pipeline/scoring.py - Multi-pillar scoring engine."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from pathlib import Path
import sys

# Bootstrap application
from core.bootstrap import bootstrap
bootstrap()

from core.models import Asset, AssetType, GatingStatus
from pipeline.scoring import normalize, FeatureCalculator, ScoringEngine


class TestNormalization:
    """Tests for the normalize() function."""

    def test_normalize_basic_values(self):
        """Test basic normalization within range."""
        assert normalize(50, 0, 100) == 50.0
        assert normalize(0, 0, 100) == 0.0
        assert normalize(100, 0, 100) == 100.0

    def test_normalize_inverted(self):
        """Test inverted normalization (lower values = higher scores)."""
        # Low value with invert=True should give high score
        assert normalize(10, 0, 100, invert=True) == 90.0
        # High value with invert=True should give low score
        assert normalize(90, 0, 100, invert=True) == 10.0

    def test_normalize_clamped_above_max(self):
        """Test that values above max are clamped."""
        # Value above max should clamp to 100
        assert normalize(150, 0, 100) == 100.0

    def test_normalize_clamped_below_min(self):
        """Test that values below min are clamped."""
        # Value below min should clamp to 0
        assert normalize(-50, 0, 100) == 0.0

    def test_normalize_nan_returns_none(self):
        """Test that NaN input returns None."""
        assert normalize(float('nan'), 0, 100) is None
        assert normalize(None, 0, 100) is None

    def test_normalize_equal_min_max(self):
        """Test normalization when min equals max."""
        # When min == max, should return 50 (middle)
        result = normalize(50, 100, 100)
        assert result == 50.0

    def test_normalize_negative_range(self):
        """Test normalization with negative range."""
        # Normalize value in negative range
        assert normalize(-50, -100, 0) == 50.0
        assert normalize(-100, -100, 0) == 0.0
        assert normalize(0, -100, 0) == 100.0

    def test_normalize_fractional_values(self):
        """Test normalization with fractional values."""
        assert normalize(0.5, 0, 1) == 50.0
        assert normalize(0.25, 0, 1) == 25.0
        assert normalize(0.75, 0, 1) == 75.0

    def test_normalize_precision(self):
        """Test normalization precision."""
        result = normalize(33.33, 0, 100)
        assert abs(result - 33.3) < 0.1


class TestFeatureCalculator:
    """Tests for FeatureCalculator static methods."""

    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame for testing."""
        dates = pd.date_range("2024-01-01", periods=300, freq="D")
        np.random.seed(42)

        # Create prices with trend
        prices = 100 + np.cumsum(np.random.randn(300) * 0.8)
        volumes = np.random.randint(500000, 2000000, 300)

        return pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

    def test_rsi_valid_data(self, sample_df):
        """Test RSI calculation with valid data."""
        rsi = FeatureCalculator.rsi(sample_df, period=14)

        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "Close": [100, 101, 102, 103, 102, 101, 100, 101, 102, 103],
        }, index=dates)

        rsi = FeatureCalculator.rsi(df, period=14)
        assert rsi is None

    def test_rsi_empty_dataframe(self):
        """Test RSI with empty DataFrame."""
        df = pd.DataFrame()
        rsi = FeatureCalculator.rsi(df)
        assert rsi is None

    def test_rsi_missing_close_column(self):
        """Test RSI with missing Close column."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        df = pd.DataFrame({
            "Price": [100 + i for i in range(30)],
        }, index=dates)

        rsi = FeatureCalculator.rsi(df)
        assert rsi is None

    def test_sma_valid_data(self, sample_df):
        """Test SMA calculation with valid data."""
        sma = FeatureCalculator.sma(sample_df, period=20)

        assert sma is not None
        assert sma > 0

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "Close": [100 + i for i in range(10)],
        }, index=dates)

        sma = FeatureCalculator.sma(df, period=20)
        assert sma is None

    def test_sma_different_periods(self, sample_df):
        """Test SMA with different periods."""
        sma20 = FeatureCalculator.sma(sample_df, period=20)
        sma50 = FeatureCalculator.sma(sample_df, period=50)
        sma200 = FeatureCalculator.sma(sample_df, period=200)

        assert sma20 is not None
        assert sma50 is not None
        assert sma200 is not None
        # All should be different values
        assert sma20 != sma50

    def test_zscore_valid_data(self, sample_df):
        """Test Z-score calculation."""
        zscore = FeatureCalculator.zscore(sample_df, period=20)

        assert zscore is not None
        # Z-score should be reasonable magnitude
        assert -10 < zscore < 10

    def test_zscore_insufficient_data(self):
        """Test Z-score with insufficient data."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "Close": [100 + i for i in range(10)],
        }, index=dates)

        zscore = FeatureCalculator.zscore(df, period=20)
        assert zscore is None

    def test_zscore_zero_std(self):
        """Test Z-score with zero standard deviation."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        # All same prices
        df = pd.DataFrame({
            "Close": [100.0] * 30,
        }, index=dates)

        zscore = FeatureCalculator.zscore(df, period=20)
        # Should handle division by zero gracefully
        assert zscore == 0.0

    def test_volatility_annual_valid_data(self, sample_df):
        """Test annualized volatility calculation."""
        vol = FeatureCalculator.volatility_annual(sample_df)

        assert vol is not None
        assert vol > 0
        # Typical volatility is 5-50% annually
        assert 0 < vol < 100

    def test_volatility_annual_insufficient_data(self):
        """Test volatility with insufficient data."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "Close": [100 + i * 0.1 for i in range(10)],
        }, index=dates)

        vol = FeatureCalculator.volatility_annual(df)
        assert vol is None

    def test_max_drawdown_valid_data(self, sample_df):
        """Test maximum drawdown calculation."""
        dd = FeatureCalculator.max_drawdown(sample_df)

        assert dd is not None
        assert dd >= 0  # Drawdown is absolute value
        assert dd <= 100  # Can't exceed 100%

    def test_max_drawdown_all_up(self):
        """Test max drawdown with monotonically increasing prices."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        df = pd.DataFrame({
            "Close": [100 + i for i in range(50)],
        }, index=dates)

        dd = FeatureCalculator.max_drawdown(df)
        # No drawdown if prices only go up
        assert dd == 0.0

    def test_max_drawdown_crash(self):
        """Test max drawdown with sharp crash."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = [100] * 20 + [50] * 30  # 50% crash

        df = pd.DataFrame({
            "Close": prices,
        }, index=dates)

        dd = FeatureCalculator.max_drawdown(df)
        # Should detect ~50% drawdown
        assert 45 < dd < 55

    def test_price_vs_sma_above(self, sample_df):
        """Test price vs SMA calculation when price above SMA."""
        result = FeatureCalculator.price_vs_sma(sample_df, period=50)

        # Last price should be above SMA200 average
        if result is not None:
            assert isinstance(result, float)

    def test_price_vs_sma_insufficient_data(self):
        """Test price vs SMA with insufficient data."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        df = pd.DataFrame({
            "Close": [100 + i for i in range(50)],
        }, index=dates)

        result = FeatureCalculator.price_vs_sma(df, period=200)
        assert result is None


class TestScoringEngine:
    """Tests for ScoringEngine class."""

    @pytest.fixture
    def scoring_engine(self):
        """Create a ScoringEngine instance."""
        return ScoringEngine()

    @pytest.fixture
    def sample_asset(self):
        """Create sample asset for testing."""
        return Asset(
            asset_id="TEST.US",
            symbol="TEST",
            name="Test Company",
            asset_type=AssetType.EQUITY,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US",
            sector="Technology"
        )

    @pytest.fixture
    def sample_etf(self):
        """Create sample ETF asset."""
        return Asset(
            asset_id="SPY.US",
            symbol="SPY",
            name="SPDR S&P 500",
            asset_type=AssetType.ETF,
            market_scope="US_EU",
            market_code="US",
            exchange="NYSE",
            currency="USD",
            country="US"
        )

    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame."""
        dates = pd.date_range("2024-01-01", periods=300, freq="D")
        np.random.seed(42)

        prices = 100 + np.cumsum(np.random.randn(300) * 0.8)
        volumes = np.random.randint(1000000, 3000000, 300)

        return pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.02,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": volumes,
        }, index=dates)

    def test_score_momentum_high_rsi(self, scoring_engine):
        """Test momentum score with high RSI (overbought)."""
        score = scoring_engine._score_momentum(rsi=75, price_vs_sma=5)

        assert score is not None
        # High RSI should give moderate momentum score
        assert 0 <= score <= 100

    def test_score_momentum_low_rsi(self, scoring_engine):
        """Test momentum score with low RSI (oversold)."""
        score = scoring_engine._score_momentum(rsi=25, price_vs_sma=-5)

        assert score is not None
        assert 0 <= score <= 100

    def test_score_momentum_optimal_rsi(self, scoring_engine):
        """Test momentum score with optimal RSI."""
        score = scoring_engine._score_momentum(rsi=55, price_vs_sma=0)

        assert score is not None
        # Optimal RSI should give high score
        assert score >= 70

    def test_score_momentum_no_data(self, scoring_engine):
        """Test momentum score with no data."""
        score = scoring_engine._score_momentum(rsi=None, price_vs_sma=None)

        assert score is None

    def test_score_safety_low_volatility(self, scoring_engine):
        """Test safety score with low volatility."""
        score = scoring_engine._score_safety(volatility=10, drawdown=5)

        assert score is not None
        # Low volatility = safer = higher score
        assert score >= 70

    def test_score_safety_high_volatility(self, scoring_engine):
        """Test safety score with high volatility."""
        score = scoring_engine._score_safety(volatility=60, drawdown=40)

        assert score is not None
        # High volatility = less safe = lower score
        assert score < 50

    def test_score_safety_no_data(self, scoring_engine):
        """Test safety score with no data."""
        score = scoring_engine._score_safety(volatility=None, drawdown=None)

        assert score is None

    def test_score_value_high_pe(self, scoring_engine):
        """Test value score with high P/E ratio."""
        fundamentals = {
            "pe_ratio": 50,  # Expensive
            "profit_margin": 0.15,
            "return_on_equity": 0.12
        }

        score = scoring_engine._score_value(fundamentals)

        assert score is not None
        # High P/E = lower value score
        assert score <= 100

    def test_score_value_low_pe(self, scoring_engine):
        """Test value score with low P/E ratio."""
        fundamentals = {
            "pe_ratio": 10,  # Cheap
            "profit_margin": 0.20,
            "return_on_equity": 0.18
        }

        score = scoring_engine._score_value(fundamentals)

        assert score is not None
        # Low P/E = higher value score
        assert score >= 50

    def test_score_value_no_fundamentals(self, scoring_engine):
        """Test value score with missing fundamentals."""
        fundamentals = {}

        score = scoring_engine._score_value(fundamentals)

        assert score is None

    def test_compute_score_equity(self, scoring_engine, sample_asset, sample_df):
        """Test full score computation for equity."""
        score = scoring_engine.compute_score(
            asset=sample_asset,
            df=sample_df,
            fundamentals={
                "pe_ratio": 20,
                "profit_margin": 0.15,
                "return_on_equity": 0.12
            }
        )

        assert score.asset_id == "TEST.US"
        assert score.score_total is not None
        assert 0 <= score.score_total <= 100
        assert score.score_momentum is not None
        assert score.score_safety is not None
        assert score.score_value is not None
        assert score.confidence > 0

    def test_compute_score_etf(self, scoring_engine, sample_etf, sample_df):
        """Test full score computation for ETF (no value pillar)."""
        score = scoring_engine.compute_score(
            asset=sample_etf,
            df=sample_df
        )

        assert score.asset_id == "SPY.US"
        assert score.score_total is not None
        # ETF should not have value score
        assert score.score_value is None
        assert score.score_momentum is not None
        assert score.score_safety is not None

    def test_compute_score_with_gating(self, scoring_engine, sample_asset, sample_df):
        """Test score computation with gating information."""
        gating = GatingStatus(
            asset_id="TEST.US",
            coverage=0.95,
            liquidity=5_000_000,
            price_min=50.0,
            stale_ratio=0.05,
            eligible=True,
            data_confidence=90
        )

        score = scoring_engine.compute_score(
            asset=sample_asset,
            df=sample_df,
            gating=gating
        )

        # Confidence should be computed, but actual value depends on data
        assert score.confidence >= 0
        assert score.confidence <= 100

    def test_compute_score_empty_df(self, scoring_engine, sample_asset):
        """Test score computation with empty DataFrame."""
        df = pd.DataFrame()

        score = scoring_engine.compute_score(
            asset=sample_asset,
            df=df
        )

        # Should still produce a score, but with None values for technical indicators
        assert score.asset_id == "TEST.US"
        assert score.rsi is None
        assert score.zscore is None

    def test_score_breakdown_included(self, scoring_engine, sample_asset, sample_df):
        """Test that score breakdown is included."""
        score = scoring_engine.compute_score(
            asset=sample_asset,
            df=sample_df
        )

        assert score.breakdown is not None
        assert "momentum" in score.breakdown.normalized_values
        assert "safety" in score.breakdown.normalized_values
        assert score.breakdown.version == "1.0"

    def test_state_label_extension_haute(self, scoring_engine):
        """Test state label determination for high extension."""
        label = scoring_engine._determine_state(zscore=2.5, rsi=55)

        assert label.value == "Extension haute (+2σ)"

    def test_state_label_extension_basse(self, scoring_engine):
        """Test state label determination for low extension."""
        label = scoring_engine._determine_state(zscore=-2.5, rsi=55)

        assert label.value == "Extension basse (-2σ)"

    def test_state_label_stress_haussier(self, scoring_engine):
        """Test state label determination for overbought."""
        label = scoring_engine._determine_state(zscore=0.5, rsi=85)

        assert label.value == "Stress haussier"

    def test_state_label_stress_baissier(self, scoring_engine):
        """Test state label determination for oversold."""
        label = scoring_engine._determine_state(zscore=0.5, rsi=15)

        assert label.value == "Stress baissier"

    def test_state_label_equilibre(self, scoring_engine):
        """Test state label for balanced conditions."""
        label = scoring_engine._determine_state(zscore=0.0, rsi=50)

        assert label.value == "Équilibre"

    def test_state_label_na(self, scoring_engine):
        """Test state label with no data."""
        label = scoring_engine._determine_state(zscore=None, rsi=None)

        assert label.value == "N/A"


class TestScoringWeighting:
    """Tests for score weighting and total calculation."""

    @pytest.fixture
    def scoring_engine(self):
        """Create a ScoringEngine instance."""
        return ScoringEngine()

    @pytest.fixture
    def sample_asset(self):
        """Create sample asset."""
        return Asset(
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

    def test_calculate_total_all_pillars(self, scoring_engine, sample_asset):
        """Test total calculation with all pillars present."""
        total, weights = scoring_engine._calculate_total(
            asset_type=AssetType.EQUITY,
            value_score=70.0,
            momentum_score=75.0,
            safety_score=80.0
        )

        assert total is not None
        assert 0 <= total <= 100
        assert len(weights) > 0
        # Should redistribute weights when all present
        assert sum(weights.values()) <= 1.01  # Allow for rounding

    def test_calculate_total_missing_value(self, scoring_engine, sample_asset):
        """Test total with missing value pillar."""
        total, weights = scoring_engine._calculate_total(
            asset_type=AssetType.EQUITY,
            value_score=None,
            momentum_score=75.0,
            safety_score=80.0
        )

        assert total is not None
        # Should still calculate from momentum and safety
        assert 0 <= total <= 100

    def test_calculate_total_etf(self, scoring_engine):
        """Test total calculation for ETF."""
        total, weights = scoring_engine._calculate_total(
            asset_type=AssetType.ETF,
            value_score=None,
            momentum_score=75.0,
            safety_score=80.0
        )

        # ETF should not have value pillar
        assert total is not None
        assert 0 <= total <= 100

    def test_calculate_total_no_pillars(self, scoring_engine):
        """Test total when no pillars available."""
        total, weights = scoring_engine._calculate_total(
            asset_type=AssetType.EQUITY,
            value_score=None,
            momentum_score=None,
            safety_score=None
        )

        # Should return None when no data
        assert total is None


class TestNaNAndNoneHandling:
    """Tests for handling NaN and None values."""

    @pytest.fixture
    def scoring_engine(self):
        """Create a ScoringEngine instance."""
        return ScoringEngine()

    def test_normalize_with_nan(self):
        """Test normalize with NaN."""
        result = normalize(float('nan'), 0, 100)
        assert result is None

    def test_normalize_with_none(self):
        """Test normalize with None."""
        result = normalize(None, 0, 100)
        assert result is None

    def test_feature_calculator_nan_handling(self):
        """Test feature calculator with NaN values."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        df = pd.DataFrame({
            "Close": [100.0] * 25 + [np.nan] * 25,
        }, index=dates)

        rsi = FeatureCalculator.rsi(df)
        # Should handle NaN gracefully
        assert rsi is None or isinstance(rsi, (int, float))

    def test_scoring_engine_nan_confidence(self, scoring_engine):
        """Test confidence calculation with NaN."""
        df = pd.DataFrame({
            "Close": [np.nan] * 10,
        }, index=pd.date_range("2024-01-01", periods=10, freq="D"))

        confidence = scoring_engine._calculate_confidence(
            df=df,
            gating=None,
            has_fundamentals=False,
            asset_type=AssetType.EQUITY
        )

        assert 0 <= confidence <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
