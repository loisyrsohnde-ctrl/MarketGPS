"""
MarketGPS Scoring Specifications.
Normalization functions and scoring parameters.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import math


def normalize(
    value: float,
    min_target: float,
    max_target: float,
    invert: bool = False,
    clamp_result: bool = True
) -> float:
    """
    Normalize a value to 0-100 scale.
    
    Args:
        value: Raw value to normalize
        min_target: Minimum target (maps to 0 or 100 if inverted)
        max_target: Maximum target (maps to 100 or 0 if inverted)
        invert: If True, higher values get lower scores
        clamp_result: If True, clamp result to 0-100
        
    Returns:
        Normalized score (0-100)
    """
    if value is None or math.isnan(value) or math.isinf(value):
        return 50.0  # Neutral default for missing data
    
    if max_target == min_target:
        return 50.0
    
    # Linear interpolation
    normalized = (value - min_target) / (max_target - min_target) * 100
    
    if invert:
        normalized = 100 - normalized
    
    if clamp_result:
        normalized = max(0.0, min(100.0, normalized))
    
    return normalized


def normalize_rsi(rsi: float) -> float:
    """
    Normalize RSI with optimal zone (40-70).
    
    RSI 55 (midpoint of 40-70) = 100 (best)
    RSI 30 or 80 = 0 (worst)
    """
    if rsi is None or math.isnan(rsi):
        return 50.0
    
    # Optimal zone: 40-70, with 55 being perfect
    optimal_mid = 55.0
    optimal_range = 15.0  # Half of 40-70 range
    
    # Distance from optimal
    distance = abs(rsi - optimal_mid)
    
    # Penalize extremes more heavily
    if rsi > 80 or rsi < 30:
        return max(0.0, 30.0 - (distance - 25) * 2)
    
    # Linear interpolation within reasonable zone
    score = max(0.0, 100.0 - (distance / optimal_range) * 50)
    
    return min(100.0, score)


@dataclass
class ScoringBounds:
    """Bounds for score normalization."""
    min_val: float
    max_val: float
    invert: bool = False
    description: str = ""


@dataclass
class ScoringSpecs:
    """
    Scoring specifications and bounds.
    
    Mode A (MVP): Fixed bounds
    Mode B (v1.1): Percentile-based (architecture ready)
    """
    
    # Momentum metrics bounds
    momentum_bounds: Dict[str, ScoringBounds] = field(default_factory=lambda: {
        "rsi": ScoringBounds(30, 70, False, "RSI optimal zone"),
        "price_vs_sma200_pct": ScoringBounds(-20, 20, False, "% above/below SMA200"),
        "momentum_12m": ScoringBounds(-30, 50, False, "12-month return %"),
        "momentum_3m": ScoringBounds(-20, 30, False, "3-month return %"),
    })
    
    # Safety metrics bounds
    safety_bounds: Dict[str, ScoringBounds] = field(default_factory=lambda: {
        "volatility_annual": ScoringBounds(10, 60, True, "Annualized volatility %"),
        "max_drawdown": ScoringBounds(-50, 0, False, "Max drawdown % (closer to 0 is better)"),
        "adv_usd": ScoringBounds(500_000, 50_000_000, False, "Average dollar volume"),
    })
    
    # Value metrics bounds (Equity only)
    value_bounds: Dict[str, ScoringBounds] = field(default_factory=lambda: {
        "pe_ratio": ScoringBounds(5, 50, True, "P/E ratio (lower is better)"),
        "profit_margin": ScoringBounds(0, 30, False, "Profit margin %"),
        "roe": ScoringBounds(0, 30, False, "Return on equity %"),
        "revenue_growth": ScoringBounds(-10, 40, False, "Revenue growth %"),
    })
    
    # Confidence thresholds
    confidence_coverage_weight: float = 0.35
    confidence_freshness_weight: float = 0.25
    confidence_liquidity_weight: float = 0.20
    confidence_fundamentals_weight: float = 0.20
    
    # Score penalty threshold
    low_confidence_threshold: int = 70
    low_confidence_penalty: float = 0.90  # Multiply score by this
    
    @classmethod
    def get_default(cls) -> "ScoringSpecs":
        """Get default scoring specifications."""
        return cls()
    
    def normalize_metric(
        self,
        metric_name: str,
        value: float,
        category: str = "momentum"
    ) -> Optional[float]:
        """
        Normalize a metric value using stored bounds.
        
        Args:
            metric_name: Name of the metric
            value: Raw value
            category: 'momentum', 'safety', or 'value'
            
        Returns:
            Normalized score (0-100) or None if metric unknown
        """
        bounds_map = {
            "momentum": self.momentum_bounds,
            "safety": self.safety_bounds,
            "value": self.value_bounds,
        }
        
        bounds_dict = bounds_map.get(category)
        if not bounds_dict or metric_name not in bounds_dict:
            return None
        
        bounds = bounds_dict[metric_name]
        
        # Special handling for RSI
        if metric_name == "rsi":
            return normalize_rsi(value)
        
        return normalize(value, bounds.min_val, bounds.max_val, bounds.invert)
    
    def compute_confidence(
        self,
        coverage: float,
        freshness_days: int,
        adv_usd: float,
        has_fundamentals: bool,
        asset_type: str = "EQUITY"
    ) -> int:
        """
        Compute data confidence score.
        
        Args:
            coverage: Data coverage ratio (0-1)
            freshness_days: Days since last data point
            adv_usd: Average dollar volume
            has_fundamentals: Whether fundamentals are available
            asset_type: Asset type for weight adjustment
            
        Returns:
            Confidence score (0-100)
        """
        # Coverage component (0-100)
        coverage_score = min(100, coverage * 100)
        
        # Freshness component (0-100)
        if freshness_days <= 1:
            freshness_score = 100
        elif freshness_days <= 3:
            freshness_score = 80
        elif freshness_days <= 7:
            freshness_score = 50
        else:
            freshness_score = max(0, 30 - freshness_days)
        
        # Liquidity component (0-100)
        liquidity_score = normalize(adv_usd, 100_000, 10_000_000, False)
        
        # Fundamentals component
        if asset_type == "EQUITY":
            fundamentals_score = 100 if has_fundamentals else 30
            fund_weight = self.confidence_fundamentals_weight
        else:
            fundamentals_score = 100  # N/A for non-equity
            fund_weight = 0
        
        # Renormalize weights if fundamentals not applicable
        if fund_weight == 0:
            total_other = (
                self.confidence_coverage_weight +
                self.confidence_freshness_weight +
                self.confidence_liquidity_weight
            )
            cov_w = self.confidence_coverage_weight / total_other
            fresh_w = self.confidence_freshness_weight / total_other
            liq_w = self.confidence_liquidity_weight / total_other
        else:
            cov_w = self.confidence_coverage_weight
            fresh_w = self.confidence_freshness_weight
            liq_w = self.confidence_liquidity_weight
        
        # Weighted average
        confidence = (
            coverage_score * cov_w +
            freshness_score * fresh_w +
            liquidity_score * liq_w +
            fundamentals_score * fund_weight
        )
        
        return int(min(100, max(0, confidence)))
    
    def apply_confidence_penalty(
        self,
        score: float,
        confidence: int
    ) -> float:
        """
        Apply penalty to score if confidence is low.
        
        Args:
            score: Raw score (0-100)
            confidence: Confidence score (0-100)
            
        Returns:
            Adjusted score
        """
        if confidence < self.low_confidence_threshold:
            return score * self.low_confidence_penalty
        return score
