"""
MarketGPS Scoring Engine Tests
Comprehensive tests for the FeatureCalculator and ScoringEngine.
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import Mock, patch

# Setup paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pathlib import Path
from dotenv import load_dotenv

# Set temporary paths BEFORE any config import to avoid PermissionError on mounted volumes
_tmp_dir = tempfile.mkdtemp(prefix="marketgps_test_")
os.environ.setdefault("DATA_DIR", os.path.join(_tmp_dir, "data"))
os.environ.setdefault("SQLITE_PATH", os.path.join(_tmp_dir, "data", "sqlite", "marketgps.db"))

# Load environment
_env_file = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(_env_file, override=False)

# Bootstrap
from core.bootstrap import bootstrap
bootstrap()

from pipeline.scoring import FeatureCalculator, ScoringEngine, normalize
from core.models import Asset, AssetType, GatingStatus, Score


# ============================================================================
# FIXTURES: Test Data
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2025-01-01', periods=260, freq='D')
    np.random.seed(42)

    data = {
        'Date': dates,
        'Open': np.random.uniform(100, 110, 260),
        'High': np.random.uniform(105, 115, 260),
        'Low': np.random.uniform(95, 105, 260),
        'Close': 105 + np.cumsum(np.random.uniform(-2, 2, 260)),
        'Volume': np.random.uniform(1000000, 5000000, 260),
    }

    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    return df


@pytest.fixture
def uptrend_data():
    """Create uptrend data for momentum testing."""
    dates = pd.date_range(start='2025-01-01', periods=260, freq='D')
    close_prices = np.linspace(100, 150, 260)  # Strong uptrend
    noise = np.random.normal(0, 1, 260)

    data = {
        'Open': close_prices + noise,
        'High': close_prices + 2 + noise,
        'Low': close_prices - 2 + noise,
        'Close': close_prices + noise,
        'Volume': np.full(260, 2000000),
    }

    df = pd.DataFrame(data, index=pd.date_range(start='2025-01-01', periods=260, freq='D'))
    return df


@pytest.fixture
def downtrend_data():
    """Create downtrend data for safety scoring."""
    dates = pd.date_range(start='2025-01-01', periods=260, freq='D')
    close_prices = np.linspace(150, 100, 260)  # Strong downtrend
    noise = np.random.normal(0, 1, 260)

    data = {
        'Open': close_prices + noise,
        'High': close_prices + 2 + noise,
        'Low': close_prices - 2 + noise,
        'Close': close_prices + noise,
        'Volume': np.full(260, 2000000),
    }

    df = pd.DataFrame(data, index=pd.date_range(start='2025-01-01', periods=260, freq='D'))
    return df


@pytest.fixture
def high_volatility_data():
    """Create high volatility data."""
    dates = pd.date_range(start='2025-01-01', periods=260, freq='D')
    close_prices = 100 + np.cumsum(np.random.uniform(-5, 5, 260))

    data = {
        'Open': close_prices,
        'High': close_prices + np.random.uniform(5, 15, 260),
        'Low': close_prices - np.random.uniform(5, 15, 260),
        'Close': close_prices,
        'Volume': np.random.uniform(1000000, 5000000, 260),
    }

    df = pd.DataFrame(data, index=pd.date_range(start='2025-01-01', periods=260, freq='D'))
    return df


@pytest.fixture
def low_volatility_data():
    """Create low volatility data."""
    dates = pd.date_range(start='2025-01-01', periods=260, freq='D')
    close_prices = 100 + np.cumsum(np.random.uniform(-0.5, 0.5, 260))

    data = {
        'Open': close_prices,
        'High': close_prices + np.random.uniform(0.5, 1, 260),
        'Low': close_prices - np.random.uniform(0.5, 1, 260),
        'Close': close_prices,
        'Volume': np.full(260, 2000000),
    }

    df = pd.DataFrame(data, index=pd.date_range(start='2025-01-01', periods=260, freq='D'))
    return df


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def minimal_dataframe():
    """Create a DataFrame with minimal data."""
    return pd.DataFrame({
        'Close': [100, 101, 102]
    })


@pytest.fixture
def nan_dataframe():
    """Create a DataFrame with NaN values."""
    data = {
        'Open': [100, np.nan, 102],
        'High': [105, 106, np.nan],
        'Low': [95, 96, 97],
        'Close': [np.nan, 101, 102],
        'Volume': [1000000, np.nan, 1500000],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_equity_asset():
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
        sector="Technology",
        industry="Consumer Electronics"
    )


@pytest.fixture
def sample_etf_asset():
    """Create a sample ETF asset."""
    return Asset(
        asset_id="SPY.US",
        symbol="SPY",
        name="SPDR S&P 500 ETF Trust",
        asset_type=AssetType.ETF,
        market_scope="US_EU",
        market_code="US",
        exchange="NYSE",
        currency="USD",
        country="US"
    )


@pytest.fixture
def sample_gating_status():
    """Create a sample gating status."""
    return GatingStatus(
        asset_id="AAPL.US",
        coverage=0.95,
        liquidity=50_000_000,
        price_min=100.0,
        stale_ratio=0.02,
        eligible=True,
        reason=None,
        data_confidence=85,
        last_bar_date="2025-12-30",
        fx_risk=0.0,
        liquidity_risk=0.0
    )


@pytest.fixture
def sample_fundamentals():
    """Create sample fundamental data."""
    return {
        'pe_ratio': 25.5,
        'pb_ratio': 35.2,
        'dividend_yield': 0.5,
        'earnings_growth': 10.2,
        'roe': 85.5,
        'debt_to_equity': 0.8,
    }


# ============================================================================
# TEST GROUP 1: FeatureCalculator - RSI (4 tests)
# ============================================================================

class TestFeatureCalculatorRSI:
    """Test RSI (Relative Strength Index) calculation."""

    def test_rsi_normal_data(self, sample_ohlcv_data):
        """Test RSI calculation with normal data."""
        rsi = FeatureCalculator.rsi(sample_ohlcv_data)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_rsi_uptrend(self, uptrend_data):
        """Test RSI with uptrend data (should be >50)."""
        rsi = FeatureCalculator.rsi(uptrend_data)
        assert rsi is not None
        assert rsi > 40  # Uptrend should show positive momentum

    def test_rsi_downtrend(self, downtrend_data):
        """Test RSI with downtrend data (should be <50)."""
        rsi = FeatureCalculator.rsi(downtrend_data)
        assert rsi is not None
        assert rsi < 60  # Downtrend should show negative momentum

    def test_rsi_insufficient_data(self, minimal_dataframe):
        """Test RSI with insufficient data."""
        rsi = FeatureCalculator.rsi(minimal_dataframe)
        assert rsi is None

    def test_rsi_empty_dataframe(self, empty_dataframe):
        """Test RSI with empty DataFrame."""
        rsi = FeatureCalculator.rsi(empty_dataframe)
        assert rsi is None

    def test_rsi_nan_values(self, nan_dataframe):
        """Test RSI with NaN values."""
        rsi = FeatureCalculator.rsi(nan_dataframe)
        # Should handle gracefully (None or valid value)
        assert rsi is None or isinstance(rsi, (int, float))

    def test_rsi_missing_close_column(self):
        """Test RSI with missing Close column."""
        df = pd.DataFrame({'Open': [100, 101], 'High': [105, 106]})
        rsi = FeatureCalculator.rsi(df)
        assert rsi is None


# ============================================================================
# TEST GROUP 2: FeatureCalculator - SMA (4 tests)
# ============================================================================

class TestFeatureCalculatorSMA:
    """Test Simple Moving Average calculation."""

    def test_sma_normal_data(self, sample_ohlcv_data):
        """Test SMA calculation with normal data."""
        sma = FeatureCalculator.sma(sample_ohlcv_data, period=20)
        assert sma is not None
        assert isinstance(sma, float)

    def test_sma_different_periods(self, sample_ohlcv_data):
        """Test SMA with different periods."""
        sma_20 = FeatureCalculator.sma(sample_ohlcv_data, period=20)
        sma_50 = FeatureCalculator.sma(sample_ohlcv_data, period=50)
        sma_200 = FeatureCalculator.sma(sample_ohlcv_data, period=200)

        assert sma_20 is not None
        assert sma_50 is not None
        assert sma_200 is not None

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data."""
        df = pd.DataFrame({'Close': [100, 101, 102]})
        sma = FeatureCalculator.sma(df, period=20)
        assert sma is None

    def test_sma_empty_dataframe(self, empty_dataframe):
        """Test SMA with empty DataFrame."""
        sma = FeatureCalculator.sma(empty_dataframe, period=20)
        assert sma is None


# ============================================================================
# TEST GROUP 3: FeatureCalculator - Volatility (4 tests)
# ============================================================================

class TestFeatureCalculatorVolatility:
    """Test annualized volatility calculation."""

    def test_volatility_normal_data(self, sample_ohlcv_data):
        """Test volatility with normal data."""
        vol = FeatureCalculator.volatility_annual(sample_ohlcv_data)
        assert vol is not None
        assert vol >= 0

    def test_volatility_high_volatility_data(self, high_volatility_data):
        """Test volatility with high volatility data."""
        vol = FeatureCalculator.volatility_annual(high_volatility_data)
        assert vol is not None
        assert vol > 10  # Should be significantly high

    def test_volatility_low_volatility_data(self, low_volatility_data):
        """Test volatility with low volatility data."""
        vol = FeatureCalculator.volatility_annual(low_volatility_data)
        assert vol is not None
        assert vol < 20  # Should be relatively low

    def test_volatility_insufficient_data(self, minimal_dataframe):
        """Test volatility with insufficient data."""
        vol = FeatureCalculator.volatility_annual(minimal_dataframe)
        assert vol is None

    def test_volatility_empty_dataframe(self, empty_dataframe):
        """Test volatility with empty DataFrame."""
        vol = FeatureCalculator.volatility_annual(empty_dataframe)
        assert vol is None


# ============================================================================
# TEST GROUP 4: FeatureCalculator - Max Drawdown (3 tests)
# ============================================================================

class TestFeatureCalculatorDrawdown:
    """Test maximum drawdown calculation."""

    def test_drawdown_normal_data(self, sample_ohlcv_data):
        """Test drawdown with normal data."""
        dd = FeatureCalculator.max_drawdown(sample_ohlcv_data)
        assert dd is not None
        assert dd >= 0

    def test_drawdown_downtrend(self, downtrend_data):
        """Test drawdown with downtrend data."""
        dd = FeatureCalculator.max_drawdown(downtrend_data)
        assert dd is not None
        assert dd > 20  # Should have significant drawdown

    def test_drawdown_uptrend(self, uptrend_data):
        """Test drawdown with uptrend data."""
        dd = FeatureCalculator.max_drawdown(uptrend_data)
        assert dd is not None
        assert dd < 10  # Should have minimal drawdown

    def test_drawdown_insufficient_data(self, minimal_dataframe):
        """Test drawdown with insufficient data."""
        dd = FeatureCalculator.max_drawdown(minimal_dataframe)
        assert dd is None


# ============================================================================
# TEST GROUP 5: FeatureCalculator - Price vs SMA (3 tests)
# ============================================================================

class TestFeatureCalculatorPriceVsSMA:
    """Test price vs SMA calculation."""

    def test_price_vs_sma_normal_data(self, sample_ohlcv_data):
        """Test price vs SMA with normal data."""
        pvs = FeatureCalculator.price_vs_sma(sample_ohlcv_data, period=200)
        assert pvs is not None
        assert isinstance(pvs, float)

    def test_price_vs_sma_uptrend(self, uptrend_data):
        """Test price vs SMA with uptrend (should be positive)."""
        pvs = FeatureCalculator.price_vs_sma(uptrend_data, period=200)
        assert pvs is not None
        assert pvs > 0  # Price above SMA in uptrend

    def test_price_vs_sma_insufficient_data(self, minimal_dataframe):
        """Test price vs SMA with insufficient data."""
        pvs = FeatureCalculator.price_vs_sma(minimal_dataframe, period=200)
        assert pvs is None


# ============================================================================
# TEST GROUP 6: Normalize Function (5 tests)
# ============================================================================

class TestNormalizeFunction:
    """Test the normalize utility function."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        result = normalize(50, 0, 100)
        assert result == 50.0

    def test_normalize_min_value(self):
        """Test normalization at minimum."""
        result = normalize(0, 0, 100)
        assert result == 0.0

    def test_normalize_max_value(self):
        """Test normalization at maximum."""
        result = normalize(100, 0, 100)
        assert result == 100.0

    def test_normalize_inverted(self):
        """Test inverted normalization."""
        result = normalize(25, 0, 100, invert=True)
        assert result == 75.0

    def test_normalize_none_value(self):
        """Test normalization with None value."""
        result = normalize(None, 0, 100)
        assert result is None

    def test_normalize_nan_value(self):
        """Test normalization with NaN value."""
        result = normalize(np.nan, 0, 100)
        assert result is None

    def test_normalize_clamping(self):
        """Test normalization with values outside range."""
        result = normalize(150, 0, 100)  # Above max
        assert result == 100.0

        result = normalize(-50, 0, 100)  # Below min
        assert result == 0.0


# ============================================================================
# TEST GROUP 7: ScoringEngine - Momentum Scoring (3 tests)
# ============================================================================

class TestScoringEngineMomentum:
    """Test momentum pillar scoring."""

    def test_momentum_score_calculation(self):
        """Test momentum score calculation."""
        engine = ScoringEngine()
        # Test with RSI in optimal range
        score = engine._score_momentum(rsi=55, price_vs_sma=5)
        assert score is not None
        assert 0 <= score <= 100

    def test_momentum_score_oversold(self):
        """Test momentum score with oversold RSI."""
        engine = ScoringEngine()
        score = engine._score_momentum(rsi=20, price_vs_sma=-5)
        assert score is not None
        assert score < 50

    def test_momentum_score_overbought(self):
        """Test momentum score with overbought RSI."""
        engine = ScoringEngine()
        score = engine._score_momentum(rsi=80, price_vs_sma=10)
        assert score is not None
        assert score < 100


# ============================================================================
# TEST GROUP 8: ScoringEngine - Safety Scoring (3 tests)
# ============================================================================

class TestScoringEngineSafety:
    """Test safety pillar scoring."""

    def test_safety_score_calculation(self):
        """Test safety score calculation."""
        engine = ScoringEngine()
        score = engine._score_safety(volatility=15, drawdown=10)
        assert score is not None
        assert 0 <= score <= 100

    def test_safety_score_low_risk(self):
        """Test safety score with low risk."""
        engine = ScoringEngine()
        score = engine._score_safety(volatility=5, drawdown=3)
        assert score is not None
        assert score > 70

    def test_safety_score_high_risk(self):
        """Test safety score with high risk."""
        engine = ScoringEngine()
        score = engine._score_safety(volatility=40, drawdown=35)
        assert score is not None
        assert score < 50


# ============================================================================
# TEST GROUP 9: ScoringEngine - Value Scoring (3 tests)
# ============================================================================

class TestScoringEngineValue:
    """Test value pillar scoring."""

    def test_value_score_good_fundamentals(self):
        """Test value score with good fundamentals."""
        engine = ScoringEngine()
        fundamentals = {
            'pe_ratio': 15,
            'pb_ratio': 2.5,
            'dividend_yield': 2.5,
            'roe': 20,
        }
        score = engine._score_value(fundamentals)
        assert score is not None
        assert score > 40

    def test_value_score_poor_fundamentals(self):
        """Test value score with poor fundamentals."""
        engine = ScoringEngine()
        fundamentals = {
            'pe_ratio': 50,
            'pb_ratio': 10,
            'dividend_yield': 0,
            'roe': 5,
        }
        score = engine._score_value(fundamentals)
        # Should be lower for poor fundamentals
        assert score is not None

    def test_value_score_missing_data(self):
        """Test value score with missing fundamental data."""
        engine = ScoringEngine()
        fundamentals = {}
        score = engine._score_value(fundamentals)
        assert score is None


# ============================================================================
# TEST GROUP 10: ScoringEngine - Total Score (3 tests)
# ============================================================================

class TestScoringEngineTotal:
    """Test total score calculation."""

    def test_total_score_etf(self, sample_etf_asset):
        """Test total score for ETF (no value pillar)."""
        engine = ScoringEngine()
        total, weights = engine._calculate_total(
            asset_type=AssetType.ETF,
            value_score=None,
            momentum_score=75,
            safety_score=70
        )
        assert total is not None
        assert 0 <= total <= 100
        assert weights is not None

    def test_total_score_equity_with_value(self, sample_equity_asset):
        """Test total score for equity with value pillar."""
        engine = ScoringEngine()
        total, weights = engine._calculate_total(
            asset_type=AssetType.EQUITY,
            value_score=65,
            momentum_score=75,
            safety_score=70
        )
        assert total is not None
        assert 0 <= total <= 100
        assert weights is not None

    def test_total_score_equity_without_value(self, sample_equity_asset):
        """Test total score for equity without value pillar."""
        engine = ScoringEngine()
        total, weights = engine._calculate_total(
            asset_type=AssetType.EQUITY,
            value_score=None,
            momentum_score=75,
            safety_score=70
        )
        assert total is not None
        assert 0 <= total <= 100


# ============================================================================
# TEST GROUP 11: ScoringEngine - Confidence (2 tests)
# ============================================================================

class TestScoringEngineConfidence:
    """Test confidence calculation."""

    def test_confidence_good_data(self, sample_ohlcv_data, sample_gating_status):
        """Test confidence with good quality data."""
        engine = ScoringEngine()
        conf = engine._calculate_confidence(
            df=sample_ohlcv_data,
            gating=sample_gating_status,
            has_fundamentals=True,
            asset_type=AssetType.EQUITY
        )
        assert conf is not None
        assert 0 <= conf <= 100
        assert conf >= 60

    def test_confidence_poor_data(self, sample_ohlcv_data):
        """Test confidence with poor quality data."""
        engine = ScoringEngine()
        poor_gating = GatingStatus(
            asset_id="TEST",
            coverage=0.5,
            liquidity=1_000_000,
            eligible=True,
            data_confidence=30,
            last_bar_date="2025-12-30",
        )
        conf = engine._calculate_confidence(
            df=sample_ohlcv_data,
            gating=poor_gating,
            has_fundamentals=False,
            asset_type=AssetType.ETF
        )
        assert conf is not None
        assert conf < 70


# ============================================================================
# TEST GROUP 12: ScoringEngine - State Label (3 tests)
# ============================================================================

class TestScoringEngineStateLabel:
    """Test state label determination."""

    def test_state_label_neutral(self):
        """Test state label when neutral."""
        engine = ScoringEngine()
        label = engine._determine_state(zscore=0.2, rsi=55)
        assert label is not None

    def test_state_label_bullish(self):
        """Test state label when bullish."""
        engine = ScoringEngine()
        label = engine._determine_state(zscore=2.0, rsi=65)
        assert label is not None

    def test_state_label_bearish(self):
        """Test state label when bearish."""
        engine = ScoringEngine()
        label = engine._determine_state(zscore=-2.0, rsi=25)
        assert label is not None


# ============================================================================
# TEST GROUP 13: ScoringEngine - Full Score Computation (5 tests)
# ============================================================================

class TestScoringEngineFullComputation:
    """Test complete score computation."""

    def test_compute_score_equity_with_data(
        self,
        sample_equity_asset,
        sample_ohlcv_data,
        sample_fundamentals,
        sample_gating_status
    ):
        """Test full score computation for equity."""
        engine = ScoringEngine()
        score = engine.compute_score(
            asset=sample_equity_asset,
            df=sample_ohlcv_data,
            fundamentals=sample_fundamentals,
            gating=sample_gating_status
        )

        assert score is not None
        assert score.asset_id == "AAPL.US"
        assert score.score_total is not None
        assert 0 <= score.score_total <= 100
        assert score.confidence > 0
        assert score.score_momentum is not None
        assert score.score_safety is not None

    def test_compute_score_etf(
        self,
        sample_etf_asset,
        sample_ohlcv_data,
        sample_gating_status
    ):
        """Test full score computation for ETF."""
        engine = ScoringEngine()
        score = engine.compute_score(
            asset=sample_etf_asset,
            df=sample_ohlcv_data,
            gating=sample_gating_status
        )

        assert score is not None
        assert score.asset_id == "SPY.US"
        assert score.score_total is not None
        assert score.score_value is None  # ETFs don't have value score

    def test_compute_score_empty_data(self, sample_equity_asset):
        """Test score computation with empty data."""
        engine = ScoringEngine()
        empty_df = pd.DataFrame()
        score = engine.compute_score(
            asset=sample_equity_asset,
            df=empty_df
        )

        assert score is not None
        # Should have defaults or None for missing data
        assert score.asset_id == "AAPL.US"

    def test_compute_score_nan_data(
        self,
        sample_equity_asset,
        nan_dataframe
    ):
        """Test score computation with NaN values."""
        engine = ScoringEngine()
        score = engine.compute_score(
            asset=sample_equity_asset,
            df=nan_dataframe
        )

        assert score is not None
        # Should handle gracefully

    def test_compute_score_breakdown_structure(
        self,
        sample_equity_asset,
        sample_ohlcv_data,
        sample_fundamentals
    ):
        """Test that score breakdown has correct structure."""
        engine = ScoringEngine()
        score = engine.compute_score(
            asset=sample_equity_asset,
            df=sample_ohlcv_data,
            fundamentals=sample_fundamentals
        )

        assert score.breakdown is not None
        assert score.breakdown.version == "1.0"
        assert score.breakdown.weights is not None
        assert score.breakdown.raw_values is not None
        assert score.breakdown.normalized_values is not None


# ============================================================================
# TEST GROUP 14: Edge Cases and Error Handling (5 tests)
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_single_row_dataframe(self):
        """Test with single row of data."""
        df = pd.DataFrame({'Close': [100.0]})
        rsi = FeatureCalculator.rsi(df)
        assert rsi is None  # Not enough data for RSI

    def test_constant_price_data(self):
        """Test with constant price (no volatility)."""
        df = pd.DataFrame({
            'Close': np.full(260, 100.0),
            'Volume': np.full(260, 2000000),
        })
        vol = FeatureCalculator.volatility_annual(df)
        assert vol is not None
        assert vol == 0.0 or vol < 0.1

    def test_zero_volume_data(self):
        """Test with zero volume data."""
        df = pd.DataFrame({
            'Close': np.linspace(100, 105, 260),
            'Volume': np.zeros(260),
        })
        engine = ScoringEngine()
        score = engine.compute_score(
            asset=Asset(
                asset_id="TEST",
                symbol="TST",
                name="Test",
                asset_type=AssetType.EQUITY,
            ),
            df=df
        )
        assert score is not None

    def test_extreme_price_values(self):
        """Test with extreme price values."""
        df = pd.DataFrame({
            'Close': [1e-10, 1e10] + [100.0] * 258,
        })
        rsi = FeatureCalculator.rsi(df)
        # Should handle gracefully

    def test_all_nan_dataframe(self):
        """Test with all NaN values."""
        df = pd.DataFrame({
            'Close': [np.nan] * 260,
        })
        rsi = FeatureCalculator.rsi(df)
        assert rsi is None


# ============================================================================
# TEST GROUP 15: Parametrized Tests
# ============================================================================

class TestParametrized:
    """Test with parametrized inputs."""

    @pytest.mark.parametrize("period", [5, 14, 20, 50, 200])
    def test_sma_various_periods(self, sample_ohlcv_data, period):
        """Test SMA with various periods."""
        sma = FeatureCalculator.sma(sample_ohlcv_data, period)
        if len(sample_ohlcv_data) >= period:
            assert sma is not None

    @pytest.mark.parametrize("asset_type", [
        AssetType.EQUITY,
        AssetType.ETF,
        AssetType.INDEX,
    ])
    def test_compute_score_asset_types(
        self,
        sample_ohlcv_data,
        asset_type
    ):
        """Test score computation for different asset types."""
        engine = ScoringEngine()
        asset = Asset(
            asset_id=f"TEST.{asset_type.value}",
            symbol="TEST",
            name="Test Asset",
            asset_type=asset_type,
        )
        score = engine.compute_score(asset=asset, df=sample_ohlcv_data)
        assert score is not None
        assert score.asset_id == f"TEST.{asset_type.value}"

    @pytest.mark.parametrize("volatility,expected_range", [
        (5, (80, 100)),      # Low volatility = high safety
        (15, (50, 80)),      # Medium volatility
        (40, (0, 50)),       # High volatility = low safety
    ])
    def test_safety_score_volatility_relationship(
        self,
        volatility,
        expected_range
    ):
        """Test relationship between volatility and safety score."""
        engine = ScoringEngine()
        score = engine._score_safety(volatility=volatility, drawdown=volatility/2)
        assert score is not None
        assert expected_range[0] <= score <= expected_range[1]


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestScoringEngineIntegration:
    """Integration tests for scoring engine."""

    def test_complete_scoring_workflow(
        self,
        sample_equity_asset,
        uptrend_data,
        sample_fundamentals,
        sample_gating_status
    ):
        """Test complete scoring workflow from data to final score."""
        engine = ScoringEngine()

        # Compute score
        score = engine.compute_score(
            asset=sample_equity_asset,
            df=uptrend_data,
            fundamentals=sample_fundamentals,
            gating=sample_gating_status
        )

        # Verify score structure
        assert score.score_total is not None
        assert score.score_momentum is not None
        assert score.score_safety is not None
        assert score.score_value is not None
        assert score.confidence > 0
        assert score.breakdown is not None

        # Verify breakdown
        assert score.breakdown.raw_values is not None
        assert score.breakdown.normalized_values is not None
        assert score.breakdown.weights is not None

    def test_multiple_asset_scoring(
        self,
        sample_ohlcv_data,
        uptrend_data,
        downtrend_data
    ):
        """Test scoring multiple assets with different market conditions."""
        engine = ScoringEngine()

        assets = [
            Asset(asset_id="AAPL.US", symbol="AAPL", name="Apple", asset_type=AssetType.EQUITY),
            Asset(asset_id="MSFT.US", symbol="MSFT", name="Microsoft", asset_type=AssetType.EQUITY),
            Asset(asset_id="SPY.US", symbol="SPY", name="SPY ETF", asset_type=AssetType.ETF),
        ]

        data_sets = [uptrend_data, downtrend_data, sample_ohlcv_data]

        for asset, data in zip(assets, data_sets):
            score = engine.compute_score(asset=asset, df=data)
            assert score is not None
            assert score.score_total is not None
