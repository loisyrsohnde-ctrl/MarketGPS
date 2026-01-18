"""
Tests for Institutional Guard (pipeline/institutional_guard.py)

Test Cases:
1. Small cap illiquid asset (ADV 200k) with high score_total -> capped at 55
2. Large cap institutional asset (ADV 20M) -> no penalty
3. Stale price / zero volume -> data quality flag + cap
4. Liquidity tier classification (A/B/C/D)
5. Recommended horizon calculation
"""

import pytest
from unittest.mock import MagicMock, patch
from pipeline.institutional_guard import (
    InstitutionalGuard,
    InstitutionalAssessment,
    InstitutionalThresholds,
    THRESHOLDS
)


class TestLiquidityTiers:
    """Test liquidity tier classification."""
    
    def test_tier_a_institutional(self):
        """ADV >= $5M should be Tier A."""
        guard = InstitutionalGuard(store=MagicMock())
        
        tier, penalty, cap = guard._assess_liquidity(5_000_000)
        assert tier == "A"
        assert penalty == 0.0
        assert cap == 100.0
        
    def test_tier_a_high_liquidity(self):
        """ADV $20M should be Tier A."""
        guard = InstitutionalGuard(store=MagicMock())
        
        tier, penalty, cap = guard._assess_liquidity(20_000_000)
        assert tier == "A"
        assert penalty == 0.0
        
    def test_tier_b_good_liquidity(self):
        """$1M <= ADV < $5M should be Tier B."""
        guard = InstitutionalGuard(store=MagicMock())
        
        tier, penalty, cap = guard._assess_liquidity(2_500_000)
        assert tier == "B"
        assert penalty == 5.0
        assert cap == 90.0
        
    def test_tier_c_limited_liquidity(self):
        """$500K <= ADV < $1M should be Tier C."""
        guard = InstitutionalGuard(store=MagicMock())
        
        tier, penalty, cap = guard._assess_liquidity(700_000)
        assert tier == "C"
        assert penalty == 20.0
        assert cap == 70.0
        
    def test_tier_d_illiquid(self):
        """ADV < $500K should be Tier D."""
        guard = InstitutionalGuard(store=MagicMock())
        
        tier, penalty, cap = guard._assess_liquidity(200_000)
        assert tier == "D"
        assert penalty == 45.0
        assert cap == 55.0


class TestScoreInstitutional:
    """Test score_institutional calculation."""
    
    def test_small_cap_high_score_capped(self):
        """Small cap with ADV 200k and score_total 90 -> score_institutional <= 55."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "TEST.US",
            "score_total": 90.0,
            "liquidity": 200_000,  # ADV 200k = Tier D
            "coverage": 0.95,
            "stale_ratio": 0.05,
            "zero_volume_ratio": 0.02,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.score_total == 90.0
        assert assessment.score_institutional <= 55.0  # Capped by Tier D
        assert assessment.liquidity_tier == "D"
        assert assessment.liquidity_flag == True
        assert assessment.liquidity_penalty >= 45.0
        
    def test_large_cap_good_score_no_penalty(self):
        """Large cap with ADV 20M and score_total 80 -> score_institutional ~80."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "AAPL.US",
            "score_total": 80.0,
            "liquidity": 20_000_000,  # ADV 20M = Tier A
            "coverage": 0.98,
            "stale_ratio": 0.02,
            "zero_volume_ratio": 0.01,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.score_total == 80.0
        assert assessment.score_institutional >= 75.0  # Minimal penalty
        assert assessment.liquidity_tier == "A"
        assert assessment.liquidity_flag == False
        assert assessment.liquidity_penalty == 0.0
        
    def test_medium_cap_moderate_penalty(self):
        """Medium cap with ADV 2M and score_total 75 -> moderate penalty."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "MID.US",
            "score_total": 75.0,
            "liquidity": 2_000_000,  # ADV 2M = Tier B
            "coverage": 0.92,
            "stale_ratio": 0.04,
            "zero_volume_ratio": 0.02,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.liquidity_tier == "B"
        assert assessment.score_institutional <= 90.0  # Tier B cap
        assert assessment.score_institutional >= 65.0  # Not too penalized
        assert assessment.liquidity_flag == False


class TestDataQuality:
    """Test data quality assessment."""
    
    def test_stale_price_flagged(self):
        """Stale price (>7 days or high ratio) should be flagged."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "STALE.US",
            "score_total": 85.0,
            "liquidity": 10_000_000,  # Tier A
            "coverage": 0.95,
            "stale_ratio": 0.20,  # High stale ratio
            "zero_volume_ratio": 0.03,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.stale_price_flag == True
        assert assessment.data_quality_flag == True
        assert assessment.score_institutional <= 55.0  # Stale price cap
        
    def test_low_coverage_flagged(self):
        """Low coverage (<80%) should be flagged."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "LOWCOV.US",
            "score_total": 80.0,
            "liquidity": 8_000_000,  # Tier A
            "coverage": 0.65,  # Low coverage
            "stale_ratio": 0.03,
            "zero_volume_ratio": 0.02,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.data_quality_flag == True
        assert assessment.score_institutional <= 65.0  # Low coverage cap
        
    def test_high_zero_volume_penalized(self):
        """High zero volume ratio (>10%) should be penalized."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "ZEROVO.US",
            "score_total": 85.0,
            "liquidity": 6_000_000,  # Tier A
            "coverage": 0.90,
            "stale_ratio": 0.05,
            "zero_volume_ratio": 0.15,  # High zero volume
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.data_quality_flag == True
        assert assessment.score_institutional < assessment.score_total


class TestRecommendedHorizon:
    """Test recommended investment horizon calculation."""
    
    def test_tier_a_long_horizon(self):
        """Tier A with good data -> 10 year horizon."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "AAPL.US",
            "score_total": 85.0,
            "liquidity": 50_000_000,
            "coverage": 0.98,
            "stale_ratio": 0.02,
            "zero_volume_ratio": 0.01,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.min_recommended_horizon_years == 10
        
    def test_tier_d_short_horizon(self):
        """Tier D -> 1 year horizon only."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "MICRO.US",
            "score_total": 70.0,
            "liquidity": 100_000,  # Very illiquid
            "coverage": 0.85,
            "stale_ratio": 0.05,
            "zero_volume_ratio": 0.03,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert assessment.min_recommended_horizon_years == 1
        assert assessment.liquidity_tier == "D"
        
    def test_data_quality_reduces_horizon(self):
        """Data quality issues should reduce horizon."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "BADDAT.US",
            "score_total": 80.0,
            "liquidity": 10_000_000,  # Tier A
            "coverage": 0.70,  # Low coverage
            "stale_ratio": 0.03,
            "zero_volume_ratio": 0.02,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        # With data quality issues, horizon should be capped at 5
        assert assessment.min_recommended_horizon_years <= 5


class TestDataQualityScore:
    """Test data quality score calculation."""
    
    def test_perfect_data_quality(self):
        """Perfect data should score 100."""
        guard = InstitutionalGuard(store=MagicMock())
        
        score = guard._calculate_data_quality_score(
            coverage=0.98,
            stale_ratio=0.02,
            zero_volume_ratio=0.01,
            stale_days=0
        )
        
        assert score >= 95.0
        
    def test_poor_data_quality(self):
        """Poor data should score low."""
        guard = InstitutionalGuard(store=MagicMock())
        
        score = guard._calculate_data_quality_score(
            coverage=0.60,
            stale_ratio=0.25,
            zero_volume_ratio=0.15,
            stale_days=10
        )
        
        assert score < 50.0


class TestExplanation:
    """Test explanation generation."""
    
    def test_explanation_contains_penalties(self):
        """Explanation should list applied penalties."""
        guard = InstitutionalGuard(store=MagicMock())
        
        asset_data = {
            "asset_id": "TEST.US",
            "score_total": 90.0,
            "liquidity": 300_000,  # Tier D
            "coverage": 0.75,  # Low
            "stale_ratio": 0.05,
            "zero_volume_ratio": 0.02,
            "last_bar_date": "2026-01-18"
        }
        
        assessment = guard.assess_asset(asset_data)
        
        assert "Liquidity Tier D" in assessment.explanation
        assert len(assessment.penalties_applied) > 0


class TestToDbDict:
    """Test conversion to database dict."""
    
    def test_to_db_dict_structure(self):
        """to_db_dict should return correct structure."""
        assessment = InstitutionalAssessment(
            asset_id="TEST.US",
            score_total=90.0,
            score_institutional=55.0,
            liquidity_tier="D",
            liquidity_penalty=45.0,
            liquidity_flag=True,
            adv_usd=200_000,
            market_cap=None,
            data_quality_score=80.0,
            data_quality_flag=False,
            stale_price_flag=False,
            coverage=0.95,
            stale_ratio=0.05,
            zero_volume_ratio=0.02,
            min_recommended_horizon_years=1,
            explanation="Test explanation",
            penalties_applied=["Test penalty"],
            caps_applied=["Test cap"]
        )
        
        db_dict = assessment.to_db_dict()
        
        assert db_dict["score_institutional"] == 55.0
        assert db_dict["liquidity_tier"] == "D"
        assert db_dict["liquidity_flag"] == 1
        assert db_dict["data_quality_flag"] == 0
        assert db_dict["min_recommended_horizon_years"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
