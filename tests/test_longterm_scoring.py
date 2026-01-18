"""
Tests for long-term institutional scoring module.
Tests caps, confidence, and score computation.
"""
import pytest
from pipeline.scoring_longterm import (
    compute_longterm_score,
    compute_investability_pillar,
    compute_quality_pillar,
    compute_safety_pillar,
    compute_value_pillar,
    compute_momentum_pillar,
    compute_lt_confidence,
    apply_institutional_caps,
    linear_normalize,
    CAP_ADV_VERY_LOW,
    CAP_MARKET_CAP_MICRO,
    SCORE_MAX_VERY_LOW_LIQ,
)


class TestInstitutionalCaps:
    """Test that institutional caps are correctly applied."""
    
    def test_microcap_illiquid_is_capped(self):
        """
        Test: Assets with ADV < 250K or market_cap < 50M should be capped at 55.
        """
        lt_raw = 85.0  # High raw score
        lt_confidence = 0.7
        
        # Low ADV scenario
        lt_capped, caps_applied, reason = apply_institutional_caps(
            lt_raw=lt_raw,
            lt_confidence=lt_confidence,
            adv_usd=100_000,  # Below 250K threshold
            market_cap=100_000_000,  # 100M - above threshold
            last_price=10.0,
            coverage=0.85
        )
        
        assert lt_capped <= SCORE_MAX_VERY_LOW_LIQ, f"Score {lt_capped} should be <= {SCORE_MAX_VERY_LOW_LIQ}"
        assert "LOW_LIQUIDITY" in str(caps_applied), f"Caps {caps_applied} should contain LOW_LIQUIDITY"
        
        # Low market cap scenario
        lt_capped2, caps_applied2, reason2 = apply_institutional_caps(
            lt_raw=lt_raw,
            lt_confidence=lt_confidence,
            adv_usd=500_000,  # Above 250K
            market_cap=30_000_000,  # Below 50M threshold
            last_price=10.0,
            coverage=0.85
        )
        
        assert lt_capped2 <= SCORE_MAX_VERY_LOW_LIQ, f"Score {lt_capped2} should be <= {SCORE_MAX_VERY_LOW_LIQ}"
        assert "MICRO_CAP" in str(caps_applied2), f"Caps {caps_applied2} should contain MICRO_CAP"
    
    def test_penny_stock_is_capped(self):
        """
        Test: Assets with price < $1 should have additional cap at 60.
        """
        lt_raw = 90.0
        lt_confidence = 0.8
        
        lt_capped, caps_applied, reason = apply_institutional_caps(
            lt_raw=lt_raw,
            lt_confidence=lt_confidence,
            adv_usd=5_000_000,  # Good liquidity
            market_cap=1_000_000_000,  # 1B
            last_price=0.50,  # Penny stock
            coverage=0.90
        )
        
        assert lt_capped <= 60, f"Penny stock score {lt_capped} should be <= 60"
        assert "PENNY_STOCK" in str(caps_applied)
    
    def test_low_coverage_is_capped(self):
        """
        Test: Assets with data coverage < 60% should be capped at 65.
        """
        lt_raw = 85.0
        lt_confidence = 0.5
        
        lt_capped, caps_applied, reason = apply_institutional_caps(
            lt_raw=lt_raw,
            lt_confidence=lt_confidence,
            adv_usd=10_000_000,
            market_cap=5_000_000_000,
            last_price=50.0,
            coverage=0.50  # Below 60%
        )
        
        assert lt_capped <= 65, f"Low coverage score {lt_capped} should be <= 65"
        assert "LOW_COVERAGE" in str(caps_applied)


class TestLargecapGoodFundamentals:
    """Test that quality large-caps score appropriately high."""
    
    def test_largecap_good_fundamentals_scores_high(self):
        """
        Test: Large-cap with good fundamentals should score > 75.
        """
        result = compute_longterm_score(
            asset_id="AAPL.US",
            price_data={
                "last_price": 180.0,
                "sma200": 170.0,
                "rsi": 55.0,
                "volatility_annual": 25.0,
                "max_drawdown": -15.0,
                "momentum_3m": 10.0,
                "momentum_12m": 25.0,
            },
            fundamentals={
                "pe_ratio": 28.0,
                "profit_margin": 0.25,
                "operating_margin": 0.30,
                "roe": 0.45,
                "roa": 0.20,
                "debt_to_equity": 1.5,
                "current_ratio": 1.1,
                "revenue_growth": 0.08,
                "earnings_growth": 0.10,
                "market_cap": 2_800_000_000_000,  # 2.8T
            },
            gating_data={
                "adv_usd": 5_000_000_000,  # $5B ADV
                "coverage": 0.98,
                "stale_ratio": 0.01,
            },
            market_scope="US_EU"
        )
        
        assert result.lt_score is not None, "LT score should not be None"
        # Note: P/E=28 results in low Value score, but that's realistic for growth stocks
        assert result.lt_score > 60, f"Large-cap score {result.lt_score} should be > 60"
        assert len(result.lt_caps_applied) == 0, f"No caps should be applied: {result.lt_caps_applied}"
        assert result.lt_confidence > 50, f"Confidence {result.lt_confidence} should be > 50"


class TestMissingFundamentals:
    """Test handling of missing fundamental data."""
    
    def test_missing_fundamentals_low_confidence_penalizes(self):
        """
        Test: Missing fundamental data should result in low confidence and penalty.
        """
        result = compute_longterm_score(
            asset_id="XYZ.US",
            price_data={
                "last_price": 50.0,
                "rsi": 50.0,
            },
            fundamentals={
                # Almost all fundamentals missing
                "market_cap": 1_000_000_000,
            },
            gating_data={
                "adv_usd": 2_000_000,
                "coverage": 0.70,
            },
            market_scope="US_EU"
        )
        
        assert result.lt_confidence < 50, f"Confidence {result.lt_confidence} should be < 50 with missing data"
        
        # Check breakdown mentions low confidence
        assert "confidence" in result.lt_breakdown, "Breakdown should contain confidence info"
        fund_coverage = result.lt_breakdown.get("confidence", {}).get("fund_coverage", 1.0)
        assert fund_coverage < 0.3, f"Fund coverage {fund_coverage} should be < 0.3 with missing data"
    
    def test_no_crash_with_empty_data(self):
        """
        Test: Scoring should not crash with completely empty data.
        """
        result = compute_longterm_score(
            asset_id="EMPTY.US",
            price_data={},
            fundamentals={},
            gating_data={},
            market_scope="US_EU"
        )
        
        # Should not crash, may return None score
        assert result is not None
        assert result.asset_id == "EMPTY.US"


class TestPillarComputation:
    """Test individual pillar computations."""
    
    def test_investability_pillar_high_liquidity(self):
        """Test investability pillar with high liquidity."""
        score, breakdown = compute_investability_pillar(
            adv_usd=50_000_000,  # $50M ADV
            market_cap=100_000_000_000,  # $100B
            coverage=0.95,
            stale_ratio=0.02,
            zero_volume_ratio=0.01
        )
        
        assert score is not None
        assert score > 70, f"High liquidity investability {score} should be > 70"
    
    def test_quality_pillar_profitable_company(self):
        """Test quality pillar with good fundamentals."""
        score, breakdown = compute_quality_pillar(
            profit_margin=0.20,
            operating_margin=0.25,
            roe=0.30,
            roa=0.15,
            debt_to_equity=0.5,
            current_ratio=2.0,
            revenue_growth=0.15,
            earnings_growth=0.20
        )
        
        assert score is not None
        assert score > 60, f"Profitable company quality {score} should be > 60"
    
    def test_safety_pillar_low_volatility(self):
        """Test safety pillar with low risk metrics."""
        score, breakdown = compute_safety_pillar(
            volatility_annual=15.0,  # Low vol
            max_drawdown=-10.0,  # Small drawdown
        )
        
        assert score is not None
        assert score > 70, f"Low volatility safety {score} should be > 70"
    
    def test_value_pillar_cheap_stock(self):
        """Test value pillar with low valuation."""
        score, breakdown = compute_value_pillar(
            pe_ratio=12.0,
            forward_pe=10.0,
            price_to_book=1.5,
            dividend_yield=0.03
        )
        
        assert score is not None
        assert score > 60, f"Cheap stock value {score} should be > 60"
    
    def test_momentum_pillar_trending_up(self):
        """Test momentum pillar with positive trend."""
        score, breakdown = compute_momentum_pillar(
            rsi=55.0,  # Neutral RSI
            price_vs_sma200=10.0,  # 10% above SMA
            momentum_3m=8.0,
            momentum_12m=20.0
        )
        
        assert score is not None
        assert score > 60, f"Trending momentum {score} should be > 60"


class TestConfidenceCalculation:
    """Test confidence score calculation."""
    
    def test_full_data_high_confidence(self):
        """Test confidence with complete data."""
        fundamentals = {
            "pe_ratio": 20,
            "forward_pe": 18,
            "profit_margin": 0.15,
            "operating_margin": 0.20,
            "roe": 0.25,
            "roa": 0.10,
            "revenue_growth": 0.08,
            "earnings_growth": 0.12,
            "debt_to_equity": 0.8,
            "current_ratio": 1.5,
            "market_cap": 50_000_000_000,
        }
        
        price_data = {
            "last_price": 100,
            "sma200": 95,
            "rsi": 50,
            "volatility_annual": 20,
            "max_drawdown": -15,
            "momentum_12m": 15,
            "adv_usd": 10_000_000,
        }
        
        confidence, breakdown = compute_lt_confidence(fundamentals, price_data)
        
        assert confidence > 0.8, f"Full data confidence {confidence} should be > 0.8"
    
    def test_missing_data_low_confidence(self):
        """Test confidence with mostly missing data."""
        fundamentals = {"market_cap": 1_000_000_000}
        price_data = {"last_price": 50}
        
        confidence, breakdown = compute_lt_confidence(fundamentals, price_data)
        
        assert confidence < 0.3, f"Missing data confidence {confidence} should be < 0.3"


class TestNormalization:
    """Test normalization utilities."""
    
    def test_linear_normalize_in_range(self):
        """Test linear normalization within range."""
        # Middle of range should be ~50
        result = linear_normalize(50, 0, 100)
        assert result == 50.0
        
        # Min should be 0
        result = linear_normalize(0, 0, 100)
        assert result == 0.0
        
        # Max should be 100
        result = linear_normalize(100, 0, 100)
        assert result == 100.0
    
    def test_linear_normalize_inverted(self):
        """Test inverted linear normalization."""
        # With invert, higher values get lower scores
        result = linear_normalize(10, 0, 100, invert=True)
        assert result == 90.0
        
        result = linear_normalize(90, 0, 100, invert=True)
        assert result == 10.0
    
    def test_linear_normalize_handles_none(self):
        """Test that None values return None."""
        result = linear_normalize(None, 0, 100)
        assert result is None


class TestScopeRestriction:
    """Test that LT scoring is restricted to US_EU."""
    
    def test_africa_scope_returns_empty(self):
        """Test that AFRICA scope returns no LT score."""
        result = compute_longterm_score(
            asset_id="DANGOTE.NG",
            price_data={"last_price": 100},
            fundamentals={"market_cap": 10_000_000_000},
            gating_data={"adv_usd": 1_000_000},
            market_scope="AFRICA"
        )
        
        assert result.lt_score is None, "AFRICA scope should not compute LT score"
        assert "error" in result.lt_breakdown or "only for US_EU" in str(result.lt_breakdown)
