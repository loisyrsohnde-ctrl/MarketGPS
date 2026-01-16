"""
MarketGPS - Quality & Liquidity Adjustments (US_EU only)
PATCH: Apply penalties to scores for illiquid/small cap assets.

This module provides utilities to:
1. Compute investability metrics (ADV_USD, zero_volume_ratio, stale_ratio, coverage)
2. Apply quality/liquidity penalties to raw scores

USAGE: Only applied to US_EU market scope to prevent small caps/illiquid assets
from getting inflated scores based purely on price momentum without considering
data quality and investability.
"""
import pandas as pd
import numpy as np
import json
from typing import Dict, Tuple, Optional

# ═══════════════════════════════════════════════════════════════════════════
# THRESHOLDS US_EU (constants - can be moved to calibration_params later)
# ═══════════════════════════════════════════════════════════════════════════

MIN_COVERAGE = 0.85
TARGET_ADV = 2_000_000  # USD - target average daily dollar volume
MIN_ADV_HARD = 250_000  # USD - hard minimum for any decent score
MAX_STALE = 0.10  # 10% stale days max
MAX_ZERO_VOL = 0.05  # 5% zero volume days max
ALPHA = 1.6  # Confidence multiplier exponent
PENALTY_MAX = 35  # Maximum liquidity penalty points


def compute_investability_metrics(
    df: pd.DataFrame,
    expected_days: int = 504
) -> Dict[str, float]:
    """
    Compute investability metrics from OHLCV DataFrame.
    
    Metrics:
    - adv_usd: Average Daily Dollar Volume (mean(close * volume) over last 60 days)
    - zero_volume_ratio: Percentage of days with zero volume (last 60 days)
    - stale_ratio: Percentage of days where close price didn't change (last 60 days)
    - coverage: Number of valid bars / expected days
    
    Args:
        df: OHLCV DataFrame with columns: Close, Volume (or lowercase equivalents)
        expected_days: Expected number of trading days (default 504 = ~2 years)
    
    Returns:
        Dict with keys: adv_usd, zero_volume_ratio, stale_ratio, coverage
        All values are floats, 0.0 if data insufficient
    """
    if df is None or df.empty:
        return {
            "adv_usd": 0.0,
            "zero_volume_ratio": 1.0,
            "stale_ratio": 1.0,
            "coverage": 0.0
        }
    
    # Normalize column names (handle both cases)
    df = df.copy()
    df.columns = [c.capitalize() if isinstance(c, str) else c for c in df.columns]
    
    # Ensure we have Close and Volume
    if "Close" not in df.columns or "Volume" not in df.columns:
        return {
            "adv_usd": 0.0,
            "zero_volume_ratio": 1.0,
            "stale_ratio": 1.0,
            "coverage": 0.0
        }
    
    # Use last 60 days for liquidity/staleness metrics
    window = 60
    recent = df.tail(window).copy()
    
    # 1. ADV_USD: Average Daily Dollar Volume
    adv_usd = 0.0
    if not recent.empty:
        try:
            dollar_vol = recent["Close"] * recent["Volume"]
            adv_usd = float(dollar_vol.mean()) if pd.notna(dollar_vol.mean()) else 0.0
        except Exception:
            adv_usd = 0.0
    
    # 2. Zero volume ratio
    zero_volume_ratio = 0.0
    if not recent.empty and "Volume" in recent.columns:
        try:
            zero_count = (recent["Volume"] == 0).sum()
            zero_volume_ratio = float(zero_count / len(recent)) if len(recent) > 0 else 1.0
        except Exception:
            zero_volume_ratio = 1.0
    
    # 3. Stale ratio: days where close didn't change (or changed < 1e-6)
    stale_ratio = 0.0
    if len(recent) >= 2:
        try:
            close = recent["Close"].dropna()
            if len(close) >= 2:
                # Count unchanged or nearly unchanged
                pct_change = close.pct_change().abs()
                stale_count = (pct_change < 1e-6).sum()
                stale_ratio = float(stale_count / (len(close) - 1)) if len(close) > 1 else 0.0
        except Exception:
            stale_ratio = 0.0
    
    # 4. Coverage: valid bars / expected days
    coverage = 0.0
    try:
        valid_bars = len(df.dropna(subset=["Close"]))
        coverage = min(1.0, float(valid_bars / expected_days)) if expected_days > 0 else 0.0
    except Exception:
        coverage = 0.0
    
    return {
        "adv_usd": round(adv_usd, 2),
        "zero_volume_ratio": round(zero_volume_ratio, 4),
        "stale_ratio": round(stale_ratio, 4),
        "coverage": round(coverage, 4)
    }


def compute_data_confidence(
    coverage: float,
    adv_usd: float,
    stale_ratio: float,
    zero_volume_ratio: float
) -> int:
    """
    Compute data confidence score (0-100) based on quality metrics.
    
    Formula:
    - base = 100
    - Penalty for low coverage: -40 max (linear from 0.85)
    - Penalty for low ADV: -35 max (linear from TARGET_ADV)
    - Penalty for high stale ratio: -25 max (linear from 0.05)
    - Penalty for high zero volume: -20 max (linear from 0.02)
    - Clamp to 5..100
    
    Args:
        coverage: Data coverage ratio (0-1)
        adv_usd: Average Daily Dollar Volume in USD
        stale_ratio: Ratio of stale price days (0-1)
        zero_volume_ratio: Ratio of zero volume days (0-1)
    
    Returns:
        Confidence score 0-100 (int)
    """
    base = 100.0
    
    # Coverage penalty (linear from 0.85)
    if coverage < MIN_COVERAGE:
        coverage_penalty = ((MIN_COVERAGE - coverage) / MIN_COVERAGE) * 40
    else:
        coverage_penalty = 0.0
    
    # ADV penalty (linear from TARGET_ADV)
    if adv_usd < TARGET_ADV:
        adv_penalty = ((TARGET_ADV - adv_usd) / TARGET_ADV) * 35
    else:
        adv_penalty = 0.0
    
    # Stale ratio penalty (linear from 0.05)
    if stale_ratio > 0.05:
        stale_penalty = min(25.0, ((stale_ratio - 0.05) / 0.95) * 25)
    else:
        stale_penalty = 0.0
    
    # Zero volume penalty (linear from 0.02)
    if zero_volume_ratio > 0.02:
        zero_vol_penalty = min(20.0, ((zero_volume_ratio - 0.02) / 0.98) * 20)
    else:
        zero_vol_penalty = 0.0
    
    confidence = base - coverage_penalty - adv_penalty - stale_penalty - zero_vol_penalty
    
    # Clamp to 5..100
    return int(round(max(5, min(100, confidence))))


def apply_quality_liquidity_adjustments(
    raw_score_total: Optional[float],
    gating_metrics: Dict[str, float],
    market_scope: str = "US_EU"
) -> Tuple[Optional[float], Dict[str, any]]:
    """
    Apply quality and liquidity adjustments to raw score.
    
    This function:
    1. Applies confidence multiplier: raw_score * (data_confidence/100)^ALPHA
    2. Applies liquidity penalty based on ADV_USD
    3. Applies hard caps based on quality thresholds
    
    Args:
        raw_score_total: Raw score from scoring engine (0-100)
        gating_metrics: Dict with keys: adv_usd, coverage, stale_ratio, zero_volume_ratio, data_confidence
        market_scope: Market scope (only US_EU is adjusted)
    
    Returns:
        Tuple of (final_score, debug_dict)
        debug_dict contains all intermediate calculations for transparency
    """
    # Only apply to US_EU
    if market_scope != "US_EU":
        return raw_score_total, {"adjusted": False, "reason": "Not US_EU"}
    
    if raw_score_total is None:
        return None, {"adjusted": False, "reason": "No raw score"}
    
    # Extract metrics
    adv_usd = gating_metrics.get("adv_usd", 0.0)
    coverage = gating_metrics.get("coverage", 0.0)
    stale_ratio = gating_metrics.get("stale_ratio", 0.0)
    zero_volume_ratio = gating_metrics.get("zero_volume_ratio", 0.0)
    data_confidence = gating_metrics.get("data_confidence", 50)
    
    # Build debug dict
    debug = {
        "raw_score_total": raw_score_total,
        "adv_usd": adv_usd,
        "coverage": coverage,
        "stale_ratio": stale_ratio,
        "zero_volume_ratio": zero_volume_ratio,
        "data_confidence": data_confidence,
        "caps_applied": []
    }
    
    # Step 1: Apply confidence multiplier
    confidence_multiplier = (data_confidence / 100.0) ** ALPHA
    score_after_confidence = raw_score_total * confidence_multiplier
    debug["confidence_multiplier"] = round(confidence_multiplier, 4)
    debug["score_after_confidence"] = round(score_after_confidence, 2)
    
    # Step 2: Apply liquidity penalty
    if adv_usd < TARGET_ADV:
        liquidity_penalty = ((TARGET_ADV - adv_usd) / TARGET_ADV) * PENALTY_MAX
    else:
        liquidity_penalty = 0.0
    
    score_after_penalty = score_after_confidence - liquidity_penalty
    debug["liquidity_penalty"] = round(liquidity_penalty, 2)
    debug["score_after_penalty"] = round(score_after_penalty, 2)
    
    # Step 3: Apply hard caps
    final_score = max(0.0, score_after_penalty)
    
    # Cap 1: Very low ADV
    if adv_usd < MIN_ADV_HARD:
        final_score = min(final_score, 60.0)
        debug["caps_applied"].append(f"ADV < {MIN_ADV_HARD:,} USD → cap at 60")
    
    # Cap 2: Low coverage
    if coverage < MIN_COVERAGE:
        final_score = min(final_score, 65.0)
        debug["caps_applied"].append(f"Coverage < {MIN_COVERAGE:.0%} → cap at 65")
    
    # Cap 3: High stale ratio
    if stale_ratio > MAX_STALE:
        final_score = min(final_score, 55.0)
        debug["caps_applied"].append(f"Stale ratio > {MAX_STALE:.0%} → cap at 55")
    
    # Cap 4: High zero volume ratio
    if zero_volume_ratio > MAX_ZERO_VOL:
        final_score = min(final_score, 55.0)
        debug["caps_applied"].append(f"Zero volume ratio > {MAX_ZERO_VOL:.0%} → cap at 55")
    
    # Clamp to 0-100
    final_score = max(0.0, min(100.0, final_score))
    debug["final_score_total"] = round(final_score, 2)
    
    return round(final_score, 1), debug
