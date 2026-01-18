"""
MarketGPS - Long-Term Institutional Scoring (5-20 years horizon)
ADD-ON module - does NOT replace existing scoring.

This module computes lt_score for institutional investors with:
- 5 pillars: Investability (20%), Quality (35%), Safety (20%), Value (15%), Momentum (10%)
- Institutional caps to prevent illiquid/microcap inflation
- Confidence scoring based on data availability
- Quantile normalization (winsorized p1/p99)

Target: US_EU scope only.
"""
import json
import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass, field

from core.utils import get_logger, safe_float

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════

# Pillar weights (must sum to 1.0)
PILLAR_WEIGHTS = {
    "investability": 0.20,
    "quality": 0.35,
    "safety": 0.20,
    "value": 0.15,
    "momentum": 0.10,
}

# Institutional caps thresholds
CAP_ADV_VERY_LOW = 250_000       # USD - very low liquidity
CAP_ADV_LOW = 1_000_000          # USD - low liquidity
CAP_MARKET_CAP_MICRO = 50_000_000  # USD - microcap threshold
CAP_PRICE_PENNY = 1.0            # USD - penny stock
CAP_COVERAGE_LOW = 0.60          # 60% data coverage

# Cap score limits
SCORE_MAX_VERY_LOW_LIQ = 55
SCORE_MAX_LOW_LIQ = 70
SCORE_MAX_PENNY = 60
SCORE_MAX_LOW_COVERAGE = 65
SCORE_MAX_LOW_CONFIDENCE = 65

# Confidence thresholds
CONFIDENCE_PENALTY_THRESHOLD = 0.40
CONFIDENCE_PENALTY_MULTIPLIER = 0.85

# Fundamental fields for coverage calculation
FUNDAMENTAL_FIELDS = [
    "pe_ratio", "forward_pe", "profit_margin", "operating_margin",
    "roe", "roa", "revenue_growth", "earnings_growth",
    "debt_to_equity", "current_ratio", "market_cap"
]

# Price/technical fields for coverage calculation
PRICE_FIELDS = [
    "last_price", "sma200", "rsi", "volatility_annual", 
    "max_drawdown", "momentum_12m", "adv_usd"
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LTScoreResult:
    """Result of long-term score computation."""
    asset_id: str
    lt_score: Optional[float] = None
    lt_confidence: float = 0.0
    lt_breakdown: Dict[str, Any] = field(default_factory=dict)
    lt_caps_applied: List[str] = field(default_factory=list)
    lt_caps_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "asset_id": self.asset_id,
            "lt_score": self.lt_score,
            "lt_confidence": self.lt_confidence,
            "lt_breakdown": self.lt_breakdown,
            "lt_caps_applied": self.lt_caps_applied,
            "lt_caps_reason": self.lt_caps_reason
        }
    
    def breakdown_json(self) -> str:
        return json.dumps(self.lt_breakdown, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# NORMALIZATION UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """
    Winsorize series at percentiles to remove outliers.
    
    Args:
        series: Input series
        lower: Lower percentile (default 1%)
        upper: Upper percentile (default 99%)
    
    Returns:
        Winsorized series
    """
    if series.empty or series.isna().all():
        return series
    
    q_low = series.quantile(lower)
    q_high = series.quantile(upper)
    
    return series.clip(lower=q_low, upper=q_high)


def quantile_normalize(value: Optional[float], series: pd.Series, invert: bool = False) -> Optional[float]:
    """
    Normalize value to 0-100 scale based on its quantile position in series.
    
    Args:
        value: Value to normalize
        series: Reference series for quantile calculation
        invert: If True, lower values get higher scores
    
    Returns:
        Normalized score 0-100, or None if value is None
    """
    if value is None or pd.isna(value):
        return None
    
    if series.empty or series.isna().all():
        return 50.0  # Default to middle
    
    # Winsorize the series first
    clean_series = winsorize(series.dropna())
    
    if len(clean_series) == 0:
        return 50.0
    
    # Calculate percentile rank
    rank = (clean_series < value).sum() / len(clean_series) * 100
    
    if invert:
        rank = 100 - rank
    
    return round(min(100, max(0, rank)), 1)


def linear_normalize(
    value: Optional[float],
    min_val: float,
    max_val: float,
    invert: bool = False
) -> Optional[float]:
    """
    Linear normalization to 0-100 scale.
    
    Args:
        value: Value to normalize
        min_val: Minimum expected value (maps to 0 or 100 if inverted)
        max_val: Maximum expected value (maps to 100 or 0 if inverted)
        invert: If True, lower values get higher scores
    
    Returns:
        Normalized score 0-100, or None if value is None
    """
    if value is None or pd.isna(value):
        return None
    
    if max_val == min_val:
        return 50.0
    
    # Clamp value
    clamped = max(min_val, min(max_val, value))
    
    # Normalize to 0-1
    normalized = (clamped - min_val) / (max_val - min_val)
    
    # Scale to 0-100
    score = normalized * 100
    
    if invert:
        score = 100 - score
    
    return round(score, 1)


# ═══════════════════════════════════════════════════════════════════════════
# PILLAR COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

def compute_investability_pillar(
    adv_usd: Optional[float],
    market_cap: Optional[float],
    coverage: Optional[float],
    stale_ratio: Optional[float] = None,
    zero_volume_ratio: Optional[float] = None
) -> Tuple[Optional[float], Dict]:
    """
    Compute Investability pillar (I) - 20% weight.
    
    Measures: Can an institutional investor actually buy/sell this?
    
    Components:
    - ADV_USD score (40%): Higher liquidity = higher score
    - Market cap score (30%): Larger = more investable
    - Data coverage score (20%): More data = more reliable
    - Trading quality score (10%): Low stale/zero volume = better
    
    Returns:
        Tuple of (pillar_score, breakdown_dict)
    """
    breakdown = {
        "adv_usd": adv_usd,
        "market_cap": market_cap,
        "coverage": coverage,
        "stale_ratio": stale_ratio,
        "zero_volume_ratio": zero_volume_ratio,
    }
    
    scores = []
    weights = []
    
    # ADV score (log scale, $100K = 30, $1M = 60, $10M = 90, $100M = 100)
    if adv_usd is not None and adv_usd > 0:
        adv_log = np.log10(adv_usd)
        adv_score = linear_normalize(adv_log, 4.0, 8.0)  # 10K to 100M
        if adv_score is not None:
            scores.append(adv_score)
            weights.append(0.40)
            breakdown["adv_score"] = adv_score
    
    # Market cap score (log scale, $10M = 20, $1B = 60, $100B = 100)
    if market_cap is not None and market_cap > 0:
        mc_log = np.log10(market_cap)
        mc_score = linear_normalize(mc_log, 7.0, 11.0)  # 10M to 100B
        if mc_score is not None:
            scores.append(mc_score)
            weights.append(0.30)
            breakdown["market_cap_score"] = mc_score
    
    # Coverage score
    if coverage is not None:
        cov_score = linear_normalize(coverage, 0.5, 1.0)
        if cov_score is not None:
            scores.append(cov_score)
            weights.append(0.20)
            breakdown["coverage_score"] = cov_score
    
    # Trading quality score (inverted - lower stale/zero = better)
    quality_scores = []
    if stale_ratio is not None:
        stale_score = linear_normalize(stale_ratio, 0.0, 0.20, invert=True)
        if stale_score is not None:
            quality_scores.append(stale_score)
    if zero_volume_ratio is not None:
        zero_score = linear_normalize(zero_volume_ratio, 0.0, 0.10, invert=True)
        if zero_score is not None:
            quality_scores.append(zero_score)
    
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        scores.append(avg_quality)
        weights.append(0.10)
        breakdown["trading_quality_score"] = round(avg_quality, 1)
    
    if not scores:
        return None, breakdown
    
    # Weighted average
    total_weight = sum(weights)
    pillar_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    breakdown["pillar_score"] = round(pillar_score, 1)
    return round(pillar_score, 1), breakdown


def compute_quality_pillar(
    profit_margin: Optional[float],
    operating_margin: Optional[float],
    roe: Optional[float],
    roa: Optional[float],
    debt_to_equity: Optional[float],
    current_ratio: Optional[float],
    revenue_growth: Optional[float] = None,
    earnings_growth: Optional[float] = None
) -> Tuple[Optional[float], Dict]:
    """
    Compute Quality/Fundamentals pillar (Q) - 35% weight.
    
    Measures: Is this a well-run, profitable company?
    
    Components:
    - Profitability (40%): margins, ROE, ROA
    - Financial health (35%): leverage, liquidity
    - Growth (25%): revenue/earnings growth
    
    Returns:
        Tuple of (pillar_score, breakdown_dict)
    """
    breakdown = {
        "profit_margin": profit_margin,
        "operating_margin": operating_margin,
        "roe": roe,
        "roa": roa,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "revenue_growth": revenue_growth,
        "earnings_growth": earnings_growth,
    }
    
    # Profitability scores
    profitability_scores = []
    
    if profit_margin is not None:
        # Convert to percentage if needed
        pm = profit_margin * 100 if abs(profit_margin) < 1 else profit_margin
        pm_score = linear_normalize(pm, -10, 30)
        if pm_score is not None:
            profitability_scores.append(pm_score)
            breakdown["profit_margin_score"] = pm_score
    
    if operating_margin is not None:
        om = operating_margin * 100 if abs(operating_margin) < 1 else operating_margin
        om_score = linear_normalize(om, -5, 35)
        if om_score is not None:
            profitability_scores.append(om_score)
            breakdown["operating_margin_score"] = om_score
    
    if roe is not None:
        roe_pct = roe * 100 if abs(roe) < 1 else roe
        roe_score = linear_normalize(roe_pct, 0, 25)
        if roe_score is not None:
            profitability_scores.append(roe_score)
            breakdown["roe_score"] = roe_score
    
    if roa is not None:
        roa_pct = roa * 100 if abs(roa) < 1 else roa
        roa_score = linear_normalize(roa_pct, 0, 15)
        if roa_score is not None:
            profitability_scores.append(roa_score)
            breakdown["roa_score"] = roa_score
    
    # Financial health scores
    health_scores = []
    
    if debt_to_equity is not None:
        # Lower D/E is better (inverted)
        de_score = linear_normalize(debt_to_equity, 0, 3.0, invert=True)
        if de_score is not None:
            health_scores.append(de_score)
            breakdown["debt_to_equity_score"] = de_score
    
    if current_ratio is not None:
        # Optimal range 1.5-3.0
        if current_ratio < 1.0:
            cr_score = current_ratio * 50
        elif current_ratio <= 3.0:
            cr_score = 50 + (current_ratio - 1.0) * 25
        else:
            cr_score = max(60, 100 - (current_ratio - 3.0) * 10)
        health_scores.append(cr_score)
        breakdown["current_ratio_score"] = round(cr_score, 1)
    
    # Growth scores
    growth_scores = []
    
    if revenue_growth is not None:
        rg = revenue_growth * 100 if abs(revenue_growth) < 1 else revenue_growth
        rg_score = linear_normalize(rg, -10, 30)
        if rg_score is not None:
            growth_scores.append(rg_score)
            breakdown["revenue_growth_score"] = rg_score
    
    if earnings_growth is not None:
        eg = earnings_growth * 100 if abs(earnings_growth) < 1 else earnings_growth
        eg_score = linear_normalize(eg, -20, 40)
        if eg_score is not None:
            growth_scores.append(eg_score)
            breakdown["earnings_growth_score"] = eg_score
    
    # Combine components
    component_scores = []
    component_weights = []
    
    if profitability_scores:
        avg_prof = sum(profitability_scores) / len(profitability_scores)
        component_scores.append(avg_prof)
        component_weights.append(0.40)
        breakdown["profitability_avg"] = round(avg_prof, 1)
    
    if health_scores:
        avg_health = sum(health_scores) / len(health_scores)
        component_scores.append(avg_health)
        component_weights.append(0.35)
        breakdown["health_avg"] = round(avg_health, 1)
    
    if growth_scores:
        avg_growth = sum(growth_scores) / len(growth_scores)
        component_scores.append(avg_growth)
        component_weights.append(0.25)
        breakdown["growth_avg"] = round(avg_growth, 1)
    
    if not component_scores:
        return None, breakdown
    
    # Weighted average
    total_weight = sum(component_weights)
    pillar_score = sum(s * w for s, w in zip(component_scores, component_weights)) / total_weight
    
    breakdown["pillar_score"] = round(pillar_score, 1)
    return round(pillar_score, 1), breakdown


def compute_safety_pillar(
    volatility_annual: Optional[float],
    max_drawdown: Optional[float],
    beta: Optional[float] = None,
    sharpe_ratio: Optional[float] = None
) -> Tuple[Optional[float], Dict]:
    """
    Compute Safety/Risk pillar (S) - 20% weight.
    
    Measures: How risky is this investment?
    
    Components:
    - Volatility (40%): Lower is safer
    - Max drawdown (40%): Lower is safer
    - Beta (10%): Lower market correlation = diversification
    - Sharpe ratio (10%): Higher risk-adjusted return = better
    
    Returns:
        Tuple of (pillar_score, breakdown_dict)
    """
    breakdown = {
        "volatility_annual": volatility_annual,
        "max_drawdown": max_drawdown,
        "beta": beta,
        "sharpe_ratio": sharpe_ratio,
    }
    
    scores = []
    weights = []
    
    # Volatility score (inverted - lower vol = higher score)
    if volatility_annual is not None:
        vol_score = linear_normalize(volatility_annual, 5, 60, invert=True)
        if vol_score is not None:
            scores.append(vol_score)
            weights.append(0.40)
            breakdown["volatility_score"] = vol_score
    
    # Max drawdown score (inverted - lower DD = higher score)
    if max_drawdown is not None:
        dd = abs(max_drawdown)  # Ensure positive
        dd_score = linear_normalize(dd, 0, 50, invert=True)
        if dd_score is not None:
            scores.append(dd_score)
            weights.append(0.40)
            breakdown["drawdown_score"] = dd_score
    
    # Beta score (optional, inverted - lower beta = more defensive)
    if beta is not None:
        beta_score = linear_normalize(beta, 0.5, 2.0, invert=True)
        if beta_score is not None:
            scores.append(beta_score)
            weights.append(0.10)
            breakdown["beta_score"] = beta_score
    
    # Sharpe ratio score (optional)
    if sharpe_ratio is not None:
        sharpe_score = linear_normalize(sharpe_ratio, -0.5, 2.0)
        if sharpe_score is not None:
            scores.append(sharpe_score)
            weights.append(0.10)
            breakdown["sharpe_score"] = sharpe_score
    
    if not scores:
        return None, breakdown
    
    # Weighted average
    total_weight = sum(weights)
    pillar_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    breakdown["pillar_score"] = round(pillar_score, 1)
    return round(pillar_score, 1), breakdown


def compute_value_pillar(
    pe_ratio: Optional[float],
    forward_pe: Optional[float] = None,
    price_to_book: Optional[float] = None,
    dividend_yield: Optional[float] = None,
    sector: Optional[str] = None
) -> Tuple[Optional[float], Dict]:
    """
    Compute Value pillar (V) - 15% weight.
    
    Measures: Is this stock cheap relative to fundamentals?
    
    Components:
    - P/E ratio (50%): Lower is better (within reason)
    - Forward P/E (25%): Future valuation
    - P/B ratio (15%): Price to book
    - Dividend yield (10%): Income component
    
    Returns:
        Tuple of (pillar_score, breakdown_dict)
    """
    breakdown = {
        "pe_ratio": pe_ratio,
        "forward_pe": forward_pe,
        "price_to_book": price_to_book,
        "dividend_yield": dividend_yield,
        "sector": sector,
    }
    
    scores = []
    weights = []
    
    # P/E score (inverted - lower P/E = higher score, but avoid negative/very low)
    if pe_ratio is not None and pe_ratio > 0:
        # Optimal range 5-30, penalize extreme values
        if pe_ratio < 5:
            pe_score = 60 + (pe_ratio / 5) * 20  # Suspicious if too low
        elif pe_ratio <= 30:
            pe_score = linear_normalize(pe_ratio, 5, 30, invert=True)
        else:
            pe_score = max(0, 30 - (pe_ratio - 30))  # Penalize high P/E
        
        if pe_score is not None:
            scores.append(max(0, min(100, pe_score)))
            weights.append(0.50)
            breakdown["pe_score"] = round(pe_score, 1)
    
    # Forward P/E score
    if forward_pe is not None and forward_pe > 0:
        if forward_pe <= 25:
            fpe_score = linear_normalize(forward_pe, 5, 25, invert=True)
        else:
            fpe_score = max(0, 30 - (forward_pe - 25) * 2)
        
        if fpe_score is not None:
            scores.append(max(0, min(100, fpe_score)))
            weights.append(0.25)
            breakdown["forward_pe_score"] = round(fpe_score, 1)
    
    # Price to Book score
    if price_to_book is not None and price_to_book > 0:
        pb_score = linear_normalize(price_to_book, 0.5, 5.0, invert=True)
        if pb_score is not None:
            scores.append(pb_score)
            weights.append(0.15)
            breakdown["pb_score"] = pb_score
    
    # Dividend yield score
    if dividend_yield is not None:
        dy = dividend_yield * 100 if dividend_yield < 1 else dividend_yield
        dy_score = linear_normalize(dy, 0, 6)  # 0-6% range
        if dy_score is not None:
            scores.append(dy_score)
            weights.append(0.10)
            breakdown["dividend_score"] = dy_score
    
    if not scores:
        return None, breakdown
    
    # Weighted average
    total_weight = sum(weights)
    pillar_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    breakdown["pillar_score"] = round(pillar_score, 1)
    return round(pillar_score, 1), breakdown


def compute_momentum_pillar(
    rsi: Optional[float],
    price_vs_sma200: Optional[float],
    momentum_3m: Optional[float] = None,
    momentum_12m: Optional[float] = None
) -> Tuple[Optional[float], Dict]:
    """
    Compute Momentum pillar (M) - 10% weight.
    
    Measures: Is price trend favorable?
    
    Components:
    - RSI (30%): Optimal 40-70, penalize extremes
    - Price vs SMA200 (30%): Above SMA is positive
    - 3-month momentum (20%): Short-term trend
    - 12-month momentum (20%): Long-term trend
    
    Returns:
        Tuple of (pillar_score, breakdown_dict)
    """
    breakdown = {
        "rsi": rsi,
        "price_vs_sma200": price_vs_sma200,
        "momentum_3m": momentum_3m,
        "momentum_12m": momentum_12m,
    }
    
    scores = []
    weights = []
    
    # RSI score (optimal 40-70)
    if rsi is not None:
        if 40 <= rsi <= 70:
            rsi_score = 70 + (1 - abs(rsi - 55) / 15) * 30  # Peak at 55
        elif rsi < 40:
            rsi_score = max(20, rsi * 1.5)  # Oversold
        else:
            rsi_score = max(20, 100 - (rsi - 70) * 2)  # Overbought
        
        scores.append(rsi_score)
        weights.append(0.30)
        breakdown["rsi_score"] = round(rsi_score, 1)
    
    # Price vs SMA200 score
    if price_vs_sma200 is not None:
        sma_score = linear_normalize(price_vs_sma200, -30, 30)
        if sma_score is not None:
            scores.append(sma_score)
            weights.append(0.30)
            breakdown["sma200_score"] = sma_score
    
    # 3-month momentum
    if momentum_3m is not None:
        m3_score = linear_normalize(momentum_3m, -20, 30)
        if m3_score is not None:
            scores.append(m3_score)
            weights.append(0.20)
            breakdown["momentum_3m_score"] = m3_score
    
    # 12-month momentum
    if momentum_12m is not None:
        m12_score = linear_normalize(momentum_12m, -30, 50)
        if m12_score is not None:
            scores.append(m12_score)
            weights.append(0.20)
            breakdown["momentum_12m_score"] = m12_score
    
    if not scores:
        return None, breakdown
    
    # Weighted average
    total_weight = sum(weights)
    pillar_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    breakdown["pillar_score"] = round(pillar_score, 1)
    return round(pillar_score, 1), breakdown


# ═══════════════════════════════════════════════════════════════════════════
# CONFIDENCE CALCULATION
# ═══════════════════════════════════════════════════════════════════════════

def compute_lt_confidence(
    fundamentals: Dict[str, Any],
    price_data: Dict[str, Any]
) -> Tuple[float, Dict]:
    """
    Compute lt_confidence based on data availability.
    
    Formula:
    coverage_fundamentals = nb_fund_fields_present / nb_fund_fields_total
    coverage_price = nb_price_fields_present / nb_price_fields_total
    lt_confidence = 0.6 * coverage_fundamentals + 0.4 * coverage_price
    
    Returns:
        Tuple of (confidence 0-1, breakdown_dict)
    """
    breakdown = {}
    
    # Fundamental coverage
    fund_present = sum(1 for f in FUNDAMENTAL_FIELDS 
                       if fundamentals.get(f) is not None and not pd.isna(fundamentals.get(f)))
    fund_coverage = fund_present / len(FUNDAMENTAL_FIELDS)
    breakdown["fund_fields_present"] = fund_present
    breakdown["fund_fields_total"] = len(FUNDAMENTAL_FIELDS)
    breakdown["fund_coverage"] = round(fund_coverage, 3)
    
    # Price coverage
    price_present = sum(1 for f in PRICE_FIELDS 
                        if price_data.get(f) is not None and not pd.isna(price_data.get(f)))
    price_coverage = price_present / len(PRICE_FIELDS)
    breakdown["price_fields_present"] = price_present
    breakdown["price_fields_total"] = len(PRICE_FIELDS)
    breakdown["price_coverage"] = round(price_coverage, 3)
    
    # Combined confidence
    lt_confidence = 0.6 * fund_coverage + 0.4 * price_coverage
    breakdown["lt_confidence"] = round(lt_confidence, 3)
    
    return lt_confidence, breakdown


# ═══════════════════════════════════════════════════════════════════════════
# INSTITUTIONAL CAPS
# ═══════════════════════════════════════════════════════════════════════════

def apply_institutional_caps(
    lt_raw: float,
    lt_confidence: float,
    adv_usd: Optional[float],
    market_cap: Optional[float],
    last_price: Optional[float],
    coverage: Optional[float]
) -> Tuple[float, List[str], Optional[str]]:
    """
    Apply institutional caps to prevent illiquid/microcap inflation.
    
    Caps:
    - ADV_60d < 250k USD OR market_cap < 50M => lt_score_max = 55
    - 250k <= ADV_60d < 1M => lt_score_max = 70
    - price < 1 USD => lt_score_max = min(lt_score_max, 60)
    - data_coverage < 0.6 => lt_score_max = min(lt_score_max, 65)
    - lt_confidence < 0.4 => lt_score *= 0.85 and lt_score_max = 65
    
    Returns:
        Tuple of (capped_score, caps_applied_list, reason_string)
    """
    caps_applied = []
    lt_score_max = 100.0
    lt_score = lt_raw
    
    # Cap 1: Very low liquidity or microcap
    if (adv_usd is not None and adv_usd < CAP_ADV_VERY_LOW) or \
       (market_cap is not None and market_cap < CAP_MARKET_CAP_MICRO):
        lt_score_max = min(lt_score_max, SCORE_MAX_VERY_LOW_LIQ)
        if adv_usd is not None and adv_usd < CAP_ADV_VERY_LOW:
            caps_applied.append(f"LOW_LIQUIDITY_ADV<{CAP_ADV_VERY_LOW/1000:.0f}K")
        if market_cap is not None and market_cap < CAP_MARKET_CAP_MICRO:
            caps_applied.append(f"MICRO_CAP<{CAP_MARKET_CAP_MICRO/1e6:.0f}M")
    
    # Cap 2: Low liquidity (but not very low)
    elif adv_usd is not None and adv_usd < CAP_ADV_LOW:
        lt_score_max = min(lt_score_max, SCORE_MAX_LOW_LIQ)
        caps_applied.append(f"LOW_LIQUIDITY_ADV<{CAP_ADV_LOW/1e6:.0f}M")
    
    # Cap 3: Penny stock
    if last_price is not None and last_price < CAP_PRICE_PENNY:
        lt_score_max = min(lt_score_max, SCORE_MAX_PENNY)
        caps_applied.append(f"PENNY_STOCK_PRICE<${CAP_PRICE_PENNY}")
    
    # Cap 4: Low data coverage
    if coverage is not None and coverage < CAP_COVERAGE_LOW:
        lt_score_max = min(lt_score_max, SCORE_MAX_LOW_COVERAGE)
        caps_applied.append(f"LOW_COVERAGE<{CAP_COVERAGE_LOW:.0%}")
    
    # Cap 5: Low confidence penalty
    if lt_confidence < CONFIDENCE_PENALTY_THRESHOLD:
        lt_score *= CONFIDENCE_PENALTY_MULTIPLIER
        lt_score_max = min(lt_score_max, SCORE_MAX_LOW_CONFIDENCE)
        caps_applied.append("LOW_CONFIDENCE")
    
    # Apply cap
    final_score = min(lt_score, lt_score_max)
    
    # Build reason string
    reason = None
    if caps_applied:
        reason = "; ".join(caps_applied)
    
    return round(final_score, 1), caps_applied, reason


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SCORING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def compute_longterm_score(
    asset_id: str,
    price_data: Dict[str, Any],
    fundamentals: Dict[str, Any],
    gating_data: Dict[str, Any],
    market_scope: str = "US_EU"
) -> LTScoreResult:
    """
    Compute long-term institutional score for an asset.
    
    Args:
        asset_id: Unique asset identifier
        price_data: Dict with price/technical fields (last_price, sma200, rsi, etc.)
        fundamentals: Dict with fundamental fields (pe_ratio, profit_margin, etc.)
        gating_data: Dict with gating fields (adv_usd, coverage, etc.)
        market_scope: Market scope (only US_EU supported)
    
    Returns:
        LTScoreResult with lt_score, lt_confidence, lt_breakdown, caps
    """
    result = LTScoreResult(asset_id=asset_id)
    
    # Only US_EU scope
    if market_scope != "US_EU":
        result.lt_breakdown = {"error": "LT scoring only for US_EU scope"}
        return result
    
    try:
        # Extract common fields
        adv_usd = gating_data.get("adv_usd") or gating_data.get("liquidity")
        market_cap = fundamentals.get("market_cap")
        coverage = gating_data.get("coverage")
        stale_ratio = gating_data.get("stale_ratio")
        zero_volume_ratio = gating_data.get("zero_volume_ratio")
        last_price = price_data.get("last_price")
        
        # Compute pillars
        pillar_scores = {}
        pillar_breakdowns = {}
        
        # I - Investability
        i_score, i_breakdown = compute_investability_pillar(
            adv_usd=adv_usd,
            market_cap=market_cap,
            coverage=coverage,
            stale_ratio=stale_ratio,
            zero_volume_ratio=zero_volume_ratio
        )
        pillar_scores["I"] = i_score
        pillar_breakdowns["investability"] = i_breakdown
        
        # Q - Quality
        q_score, q_breakdown = compute_quality_pillar(
            profit_margin=fundamentals.get("profit_margin"),
            operating_margin=fundamentals.get("operating_margin"),
            roe=fundamentals.get("roe") or fundamentals.get("return_on_equity"),
            roa=fundamentals.get("roa") or fundamentals.get("return_on_assets"),
            debt_to_equity=fundamentals.get("debt_to_equity"),
            current_ratio=fundamentals.get("current_ratio"),
            revenue_growth=fundamentals.get("revenue_growth"),
            earnings_growth=fundamentals.get("earnings_growth")
        )
        pillar_scores["Q"] = q_score
        pillar_breakdowns["quality"] = q_breakdown
        
        # S - Safety
        s_score, s_breakdown = compute_safety_pillar(
            volatility_annual=price_data.get("volatility_annual") or price_data.get("vol_annual"),
            max_drawdown=price_data.get("max_drawdown"),
            beta=price_data.get("beta"),
            sharpe_ratio=price_data.get("sharpe_ratio")
        )
        pillar_scores["S"] = s_score
        pillar_breakdowns["safety"] = s_breakdown
        
        # V - Value
        v_score, v_breakdown = compute_value_pillar(
            pe_ratio=fundamentals.get("pe_ratio"),
            forward_pe=fundamentals.get("forward_pe"),
            price_to_book=fundamentals.get("price_to_book"),
            dividend_yield=fundamentals.get("dividend_yield"),
            sector=fundamentals.get("sector")
        )
        pillar_scores["V"] = v_score
        pillar_breakdowns["value"] = v_breakdown
        
        # M - Momentum
        m_score, m_breakdown = compute_momentum_pillar(
            rsi=price_data.get("rsi"),
            price_vs_sma200=price_data.get("price_vs_sma200_pct") or price_data.get("price_vs_sma200"),
            momentum_3m=price_data.get("momentum_3m"),
            momentum_12m=price_data.get("momentum_12m")
        )
        pillar_scores["M"] = m_score
        pillar_breakdowns["momentum"] = m_breakdown
        
        # Compute confidence
        lt_confidence, conf_breakdown = compute_lt_confidence(fundamentals, price_data)
        result.lt_confidence = round(lt_confidence * 100, 1)  # Convert to 0-100
        
        # Compute raw score (weighted average of available pillars)
        available_pillars = {k: v for k, v in pillar_scores.items() if v is not None}
        
        if not available_pillars:
            result.lt_breakdown = {
                "error": "No pillars could be computed",
                "pillars": pillar_breakdowns,
                "confidence": conf_breakdown
            }
            return result
        
        # Compute weighted raw score
        pillar_map = {"I": "investability", "Q": "quality", "S": "safety", "V": "value", "M": "momentum"}
        total_weight = sum(PILLAR_WEIGHTS[pillar_map[k]] for k in available_pillars)
        
        lt_raw = sum(
            v * PILLAR_WEIGHTS[pillar_map[k]] 
            for k, v in available_pillars.items()
        ) / total_weight
        
        # Apply institutional caps
        lt_capped, caps_applied, caps_reason = apply_institutional_caps(
            lt_raw=lt_raw,
            lt_confidence=lt_confidence,
            adv_usd=adv_usd,
            market_cap=market_cap,
            last_price=last_price,
            coverage=coverage
        )
        
        # Build result
        result.lt_score = lt_capped
        result.lt_caps_applied = caps_applied
        result.lt_caps_reason = caps_reason
        
        result.lt_breakdown = {
            "version": "1.0",
            "lt_raw": round(lt_raw, 1),
            "lt_capped": lt_capped,
            "pillar_weights": PILLAR_WEIGHTS,
            "pillar_scores": {pillar_map[k]: v for k, v in available_pillars.items()},
            "pillars_available": list(available_pillars.keys()),
            "pillars_missing": [k for k in pillar_scores if k not in available_pillars],
            "confidence": conf_breakdown,
            "caps": {
                "applied": caps_applied,
                "reason": caps_reason,
                "score_before_cap": round(lt_raw, 1),
                "score_after_cap": lt_capped
            },
            "macro_overlay": {
                "enabled": False,
                "reason": "no reliable macro feed in repo"
            },
            "pillar_details": pillar_breakdowns
        }
        
        logger.debug(f"LT Score for {asset_id}: {lt_capped} (raw={lt_raw:.1f}, caps={caps_applied})")
        return result
        
    except Exception as e:
        logger.error(f"Failed to compute LT score for {asset_id}: {e}")
        result.lt_breakdown = {"error": str(e)}
        return result


def compute_longterm_score_batch(
    assets_data: List[Dict[str, Any]],
    market_scope: str = "US_EU"
) -> List[LTScoreResult]:
    """
    Compute long-term scores for a batch of assets.
    
    Args:
        assets_data: List of dicts with keys: asset_id, price_data, fundamentals, gating_data
        market_scope: Market scope
    
    Returns:
        List of LTScoreResult
    """
    results = []
    caps_count = 0
    
    for asset in assets_data:
        result = compute_longterm_score(
            asset_id=asset["asset_id"],
            price_data=asset.get("price_data", {}),
            fundamentals=asset.get("fundamentals", {}),
            gating_data=asset.get("gating_data", {}),
            market_scope=market_scope
        )
        results.append(result)
        
        if result.lt_caps_applied:
            caps_count += 1
    
    logger.info(f"LT Scoring batch: {len(results)} assets, {caps_count} capped ({caps_count/len(results)*100:.1f}%)")
    
    return results
