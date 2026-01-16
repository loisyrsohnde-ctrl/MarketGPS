"""
Tests for quality/liquidity adjustments (US_EU patch).
"""
import pytest
import pandas as pd
import numpy as np
from pipeline.quality_adjustments import (
    compute_investability_metrics,
    compute_data_confidence,
    apply_quality_liquidity_adjustments
)


def test_compute_investability_metrics_empty():
    """Test with empty DataFrame."""
    df = pd.DataFrame()
    metrics = compute_investability_metrics(df)
    
    assert metrics["adv_usd"] == 0.0
    assert metrics["zero_volume_ratio"] == 1.0
    assert metrics["stale_ratio"] == 1.0
    assert metrics["coverage"] == 0.0


def test_compute_investability_metrics_high_quality():
    """Test with high-quality liquid asset."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "Close": np.random.uniform(100, 200, 100),
        "Volume": np.random.uniform(1_000_000, 5_000_000, 100)
    }, index=dates)
    
    metrics = compute_investability_metrics(df)
    
    assert metrics["adv_usd"] > 100_000_000  # High ADV
    assert metrics["zero_volume_ratio"] < 0.01  # Very few zero volume days
    assert metrics["stale_ratio"] < 0.05  # Low stale ratio
    assert metrics["coverage"] > 0.0


def test_compute_investability_metrics_illiquid():
    """Test with illiquid asset (low volume, many stale days)."""
    dates = pd.date_range("2023-01-01", periods=100, freq="D")
    # Low volume, many zero volume days, many stale prices
    close_prices = [10.0] * 50 + [10.01] * 30 + [10.0] * 20  # Mostly stale
    volumes = [0] * 20 + [1000] * 80  # 20% zero volume
    
    df = pd.DataFrame({
        "Close": close_prices,
        "Volume": volumes
    }, index=dates)
    
    metrics = compute_investability_metrics(df)
    
    assert metrics["adv_usd"] < 50_000  # Low ADV
    assert metrics["zero_volume_ratio"] > 0.15  # High zero volume
    assert metrics["stale_ratio"] > 0.5  # High stale ratio


def test_compute_data_confidence_high_quality():
    """Test data confidence for high-quality asset."""
    confidence = compute_data_confidence(
        coverage=0.95,
        adv_usd=5_000_000,
        stale_ratio=0.02,
        zero_volume_ratio=0.01
    )
    
    assert confidence >= 90  # High confidence


def test_compute_data_confidence_low_quality():
    """Test data confidence for low-quality asset."""
    confidence = compute_data_confidence(
        coverage=0.70,  # Low coverage
        adv_usd=100_000,  # Low ADV
        stale_ratio=0.15,  # High stale
        zero_volume_ratio=0.10  # High zero volume
    )
    
    assert confidence < 50  # Low confidence


def test_apply_adjustments_high_quality():
    """Test adjustments for high-quality asset (minimal penalty)."""
    gating_metrics = {
        "adv_usd": 5_000_000,
        "coverage": 0.95,
        "stale_ratio": 0.02,
        "zero_volume_ratio": 0.01,
        "data_confidence": 95
    }
    
    final_score, debug = apply_quality_liquidity_adjustments(
        raw_score_total=85.0,
        gating_metrics=gating_metrics,
        market_scope="US_EU"
    )
    
    # Should be close to raw score (small penalty)
    assert final_score >= 80.0
    assert debug["raw_score_total"] == 85.0
    assert "liquidity_penalty" in debug


def test_apply_adjustments_illiquid():
    """Test adjustments for illiquid asset (significant penalty)."""
    gating_metrics = {
        "adv_usd": 150_000,  # Below MIN_ADV_HARD
        "coverage": 0.75,  # Below MIN_COVERAGE
        "stale_ratio": 0.15,  # Above MAX_STALE
        "zero_volume_ratio": 0.08,  # Above MAX_ZERO_VOL
        "data_confidence": 30
    }
    
    final_score, debug = apply_quality_liquidity_adjustments(
        raw_score_total=90.0,  # High raw score
        gating_metrics=gating_metrics,
        market_scope="US_EU"
    )
    
    # Should be significantly penalized
    assert final_score < 60.0  # Capped by multiple factors
    assert len(debug["caps_applied"]) > 0
    assert debug["final_score_total"] == final_score


def test_apply_adjustments_africa_ignored():
    """Test that adjustments are NOT applied to AFRICA scope."""
    gating_metrics = {
        "adv_usd": 100_000,
        "coverage": 0.70,
        "stale_ratio": 0.20,
        "zero_volume_ratio": 0.10,
        "data_confidence": 30
    }
    
    final_score, debug = apply_quality_liquidity_adjustments(
        raw_score_total=85.0,
        gating_metrics=gating_metrics,
        market_scope="AFRICA"
    )
    
    # Should return raw score unchanged
    assert final_score == 85.0
    assert debug["adjusted"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
