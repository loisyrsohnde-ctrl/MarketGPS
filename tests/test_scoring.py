"""Tests for scoring engine."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scoring_specs import normalize, normalize_rsi, ScoringSpecs
from pipeline.features import Features, FeatureComputer
from pipeline.scoring import ScoringEngine
from providers.base import Fundamentals


class TestNormalization:
    """Tests for normalization functions."""
    
    def test_normalize_basic(self):
        """Test basic normalization."""
        # Middle value
        assert normalize(50, 0, 100) == 50
        
        # Min value
        assert normalize(0, 0, 100) == 0
        
        # Max value
        assert normalize(100, 0, 100) == 100
    
    def test_normalize_inverted(self):
        """Test inverted normalization."""
        # High value inverted = low score
        assert normalize(100, 0, 100, invert=True) == 0
        
        # Low value inverted = high score
        assert normalize(0, 0, 100, invert=True) == 100
    
    def test_normalize_clamped(self):
        """Test clamping to 0-100."""
        # Above max
        assert normalize(150, 0, 100) == 100
        
        # Below min
        assert normalize(-50, 0, 100) == 0
    
    def test_normalize_nan(self):
        """Test NaN handling."""
        assert normalize(float('nan'), 0, 100) == 50
        assert normalize(None, 0, 100) == 50
    
    def test_normalize_rsi_optimal(self):
        """Test RSI normalization optimal zone."""
        # Optimal value (55)
        score_optimal = normalize_rsi(55)
        assert score_optimal == 100
        
        # Within optimal zone
        score_50 = normalize_rsi(50)
        assert score_50 >= 80
        
        # Outside optimal
        score_85 = normalize_rsi(85)
        assert score_85 < 40
        
        score_25 = normalize_rsi(25)
        assert score_25 < 40


class TestScoringSpecs:
    """Tests for ScoringSpecs."""
    
    def test_default_specs(self):
        """Test default specifications."""
        specs = ScoringSpecs.get_default()
        
        assert "rsi" in specs.momentum_bounds
        assert "volatility_annual" in specs.safety_bounds
        assert "pe_ratio" in specs.value_bounds
    
    def test_compute_confidence(self):
        """Test confidence computation."""
        specs = ScoringSpecs.get_default()
        
        # High confidence
        conf_high = specs.compute_confidence(
            coverage=0.99,
            freshness_days=1,
            adv_usd=10_000_000,
            has_fundamentals=True,
            asset_type="EQUITY"
        )
        assert conf_high >= 80
        
        # Low confidence
        conf_low = specs.compute_confidence(
            coverage=0.50,
            freshness_days=30,
            adv_usd=100_000,
            has_fundamentals=False,
            asset_type="EQUITY"
        )
        assert conf_low < 50
    
    def test_confidence_penalty(self):
        """Test confidence penalty application."""
        specs = ScoringSpecs.get_default()
        
        # No penalty for high confidence
        score_high = specs.apply_confidence_penalty(80, 85)
        assert score_high == 80
        
        # Penalty for low confidence
        score_low = specs.apply_confidence_penalty(80, 50)
        assert score_low < 80


class TestFeatureComputer:
    """Tests for feature computation."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample OHLCV DataFrame."""
        dates = pd.date_range("2023-01-01", periods=300, freq="D")
        np.random.seed(42)
        
        prices = 100 + np.cumsum(np.random.randn(300) * 0.5)
        volumes = np.random.randint(100000, 1000000, 300)
        
        return pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": volumes,
        }, index=dates)
    
    def test_compute_all(self, sample_df):
        """Test computing all features."""
        computer = FeatureComputer()
        features = computer.compute_all(sample_df)
        
        assert features.last_price is not None
        assert features.sma20 is not None
        assert features.rsi is not None
        assert features.volatility_annual is not None
    
    def test_compute_empty_df(self):
        """Test with empty DataFrame."""
        computer = FeatureComputer()
        features = computer.compute_all(pd.DataFrame())
        
        assert features.last_price is None
        assert features.data_points == 0
    
    def test_adv_computation(self, sample_df):
        """Test ADV computation."""
        computer = FeatureComputer()
        adv = computer.compute_adv(sample_df)
        
        assert adv is not None
        assert adv > 0
    
    def test_state_label(self):
        """Test state label determination."""
        computer = FeatureComputer()
        
        assert computer.get_state_label(2.5) == "Extension haute (+2σ)"
        assert computer.get_state_label(-2.5) == "Extension basse (-2σ)"
        assert computer.get_state_label(0.5) == "Équilibre"
        assert computer.get_state_label(None) == "N/A"


class TestScoringEngine:
    """Tests for scoring engine."""
    
    def test_compute_score_basic(self):
        """Test basic score computation."""
        engine = ScoringEngine()
        
        features = Features(
            last_price=100,
            rsi=55,
            sma200=95,
            price_vs_sma200_pct=5,
            momentum_12m=10,
            momentum_3m=5,
            volatility_annual=20,
            max_drawdown=-10,
            coverage=0.98,
            data_points=252,
        )
        
        score = engine.compute_score(
            asset_id="EQUITY:TEST",
            features=features,
            asset_type="EQUITY"
        )
        
        assert score.asset_id == "EQUITY:TEST"
        assert score.score_total is not None
        assert 0 <= score.score_total <= 100
        assert score.score_momentum is not None
        assert score.score_safety is not None
    
    def test_compute_score_with_fundamentals(self):
        """Test score with fundamentals."""
        engine = ScoringEngine()
        
        features = Features(
            last_price=100,
            rsi=55,
            volatility_annual=20,
            coverage=0.98,
            data_points=252,
        )
        
        fundamentals = Fundamentals(
            pe_ratio=15,
            profit_margin=0.20,
            roe=0.15,
        )
        
        score = engine.compute_score(
            asset_id="EQUITY:TEST",
            features=features,
            fundamentals=fundamentals,
            asset_type="EQUITY"
        )
        
        assert score.score_value is not None
    
    def test_compute_score_etf(self):
        """Test score for ETF (no value pillar)."""
        engine = ScoringEngine()
        
        features = Features(
            last_price=100,
            rsi=55,
            volatility_annual=15,
            coverage=0.98,
            data_points=252,
        )
        
        score = engine.compute_score(
            asset_id="ETF:TEST",
            features=features,
            asset_type="ETF"
        )
        
        # Value should be None for ETF
        assert score.score_value is None
        # But total should still be computed
        assert score.score_total is not None
    
    def test_score_bounds(self):
        """Test scores are always within 0-100."""
        engine = ScoringEngine()
        
        # Extreme features
        features = Features(
            last_price=100,
            rsi=95,  # Very high
            volatility_annual=100,  # Very high
            max_drawdown=-80,  # Very bad
            coverage=0.5,
            data_points=100,
        )
        
        score = engine.compute_score(
            asset_id="EQUITY:TEST",
            features=features,
            asset_type="EQUITY"
        )
        
        if score.score_total:
            assert 0 <= score.score_total <= 100
        if score.score_momentum:
            assert 0 <= score.score_momentum <= 100
        if score.score_safety:
            assert 0 <= score.score_safety <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
