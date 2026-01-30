"""
MarketGPS Real Estate - ProphetIA Scoring Engine
Unified 0-100 scoring system for real estate investments.

Score Formula:
Score = (W1 × S_Yield) + (W2 × S_Safety) + (W3 × S_Growth) + (W4 × S_Legal)

Where:
- S_Yield: Financial performance (cap rate, cash-on-cash return)
- S_Safety: Building quality, neighborhood resilience
- S_Growth: Economic dynamism (jobs, infrastructure)
- S_Legal: Regulatory environment, tax burden
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import math


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class ScoreWeights:
    """Weights for ProphetIA scoring components."""
    yield_weight: float = 0.35
    safety_weight: float = 0.25
    growth_weight: float = 0.25
    legal_weight: float = 0.15
    
    def __post_init__(self):
        total = (
            self.yield_weight + 
            self.safety_weight + 
            self.growth_weight + 
            self.legal_weight
        )
        if not math.isclose(total, 1.0, rel_tol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    @classmethod
    def for_profile(cls, profile: RiskProfile) -> "ScoreWeights":
        """Get weights optimized for a risk profile."""
        if profile == RiskProfile.CONSERVATIVE:
            return cls(yield_weight=0.25, safety_weight=0.40, 
                      growth_weight=0.15, legal_weight=0.20)
        elif profile == RiskProfile.AGGRESSIVE:
            return cls(yield_weight=0.45, safety_weight=0.15,
                      growth_weight=0.30, legal_weight=0.10)
        else:  # BALANCED
            return cls()


@dataclass
class PropertyMetrics:
    """Input metrics for ProphetIA scoring."""
    # Financial metrics
    purchase_price: float
    annual_rent: float
    annual_expenses: float  # All operating expenses
    financing_cost: float = 0.0  # Annual debt service
    
    # Building metrics
    year_built: int = 2000
    energy_rating: str = "C"  # A-G scale
    last_renovation_year: Optional[int] = None
    building_condition: str = "good"  # excellent/good/fair/poor
    
    # Location metrics
    population_growth_5y: float = 0.0  # Percentage
    employment_growth_5y: float = 0.0
    new_infrastructure_nearby: bool = False
    crime_index: float = 50.0  # 0-100 (lower is safer)
    school_rating: float = 5.0  # 1-10 scale
    
    # Market metrics
    days_on_market_avg: float = 60.0
    price_to_rent_ratio: float = 20.0
    vacancy_rate_area: float = 0.05
    
    # Legal/Regulatory
    property_tax_rate: float = 0.01
    rent_control: bool = False
    tenant_protection_level: str = "moderate"  # low/moderate/high
    energy_regulation_risk: bool = False  # e.g., rental bans for low DPE


@dataclass 
class ProphetIAScore:
    """Complete ProphetIA scoring result."""
    total_score: float
    yield_score: float
    safety_score: float
    growth_score: float
    legal_score: float
    
    confidence: int  # 0-100
    risk_flags: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    breakdown: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def rating(self) -> str:
        """Convert score to letter rating."""
        if self.total_score >= 85:
            return "A+"
        elif self.total_score >= 75:
            return "A"
        elif self.total_score >= 65:
            return "B+"
        elif self.total_score >= 55:
            return "B"
        elif self.total_score >= 45:
            return "C"
        elif self.total_score >= 35:
            return "D"
        else:
            return "F"
    
    @property
    def recommendation(self) -> str:
        """Investment recommendation based on score."""
        if self.total_score >= 75:
            return "STRONG_BUY"
        elif self.total_score >= 60:
            return "BUY"
        elif self.total_score >= 45:
            return "HOLD"
        elif self.total_score >= 30:
            return "SELL"
        else:
            return "STRONG_SELL"


class ProphetIAScoring:
    """
    ProphetIA Real Estate Scoring Engine.
    
    Produces a unified 0-100 score combining:
    - Yield: Financial performance
    - Safety: Asset quality and resilience
    - Growth: Market dynamics
    - Legal: Regulatory environment
    """
    
    # Benchmark values for scoring
    BENCHMARKS = {
        "cap_rate_excellent": 0.08,  # 8%
        "cap_rate_good": 0.06,
        "cap_rate_poor": 0.03,
        "cash_on_cash_excellent": 0.12,
        "cash_on_cash_good": 0.08,
        "vacancy_excellent": 0.02,
        "vacancy_poor": 0.10,
        "days_on_market_excellent": 30,
        "days_on_market_poor": 120,
    }
    
    def __init__(
        self,
        weights: ScoreWeights = None,
        jurisdiction: str = "US"
    ):
        self.weights = weights or ScoreWeights()
        self.jurisdiction = jurisdiction
    
    def calculate_yield_score(self, metrics: PropertyMetrics) -> tuple[float, Dict]:
        """
        Calculate yield score (0-100) based on financial metrics.
        
        Components:
        - Cap Rate (40%)
        - Cash-on-Cash Return (30%)
        - Vacancy Risk (30%)
        """
        breakdown = {}
        
        # Cap Rate = NOI / Purchase Price
        noi = metrics.annual_rent - metrics.annual_expenses
        cap_rate = noi / metrics.purchase_price if metrics.purchase_price > 0 else 0
        breakdown["cap_rate"] = cap_rate
        
        # Score cap rate (0-100)
        if cap_rate >= self.BENCHMARKS["cap_rate_excellent"]:
            cap_score = 100
        elif cap_rate >= self.BENCHMARKS["cap_rate_good"]:
            cap_score = 70 + 30 * (cap_rate - self.BENCHMARKS["cap_rate_good"]) / (
                self.BENCHMARKS["cap_rate_excellent"] - self.BENCHMARKS["cap_rate_good"]
            )
        elif cap_rate >= self.BENCHMARKS["cap_rate_poor"]:
            cap_score = 30 + 40 * (cap_rate - self.BENCHMARKS["cap_rate_poor"]) / (
                self.BENCHMARKS["cap_rate_good"] - self.BENCHMARKS["cap_rate_poor"]
            )
        else:
            cap_score = 30 * cap_rate / self.BENCHMARKS["cap_rate_poor"]
        
        breakdown["cap_rate_score"] = cap_score
        
        # Cash-on-Cash Return (if financed)
        cash_flow = noi - metrics.financing_cost
        down_payment = metrics.purchase_price * 0.25  # Assume 25% down
        coc_return = cash_flow / down_payment if down_payment > 0 else cap_rate
        breakdown["cash_on_cash"] = coc_return
        
        if coc_return >= self.BENCHMARKS["cash_on_cash_excellent"]:
            coc_score = 100
        elif coc_return >= self.BENCHMARKS["cash_on_cash_good"]:
            coc_score = 70 + 30 * (coc_return - self.BENCHMARKS["cash_on_cash_good"]) / (
                self.BENCHMARKS["cash_on_cash_excellent"] - self.BENCHMARKS["cash_on_cash_good"]
            )
        else:
            coc_score = max(0, 70 * coc_return / self.BENCHMARKS["cash_on_cash_good"])
        
        breakdown["cash_on_cash_score"] = coc_score
        
        # Vacancy Risk Score
        vacancy = metrics.vacancy_rate_area
        if vacancy <= self.BENCHMARKS["vacancy_excellent"]:
            vacancy_score = 100
        elif vacancy >= self.BENCHMARKS["vacancy_poor"]:
            vacancy_score = 20
        else:
            vacancy_score = 100 - 80 * (vacancy - self.BENCHMARKS["vacancy_excellent"]) / (
                self.BENCHMARKS["vacancy_poor"] - self.BENCHMARKS["vacancy_excellent"]
            )
        
        breakdown["vacancy_score"] = vacancy_score
        
        # Weighted yield score
        yield_score = (
            cap_score * 0.40 +
            coc_score * 0.30 +
            vacancy_score * 0.30
        )
        
        return min(100, max(0, yield_score)), breakdown
    
    def calculate_safety_score(self, metrics: PropertyMetrics) -> tuple[float, Dict]:
        """
        Calculate safety score (0-100) based on asset quality.
        
        Components:
        - Building Age & Condition (35%)
        - Energy Rating (25%)
        - Neighborhood Safety (25%)
        - Liquidity (15%)
        """
        breakdown = {}
        current_year = 2024
        
        # Building age and condition
        age = current_year - metrics.year_built
        renovation_age = (
            current_year - metrics.last_renovation_year 
            if metrics.last_renovation_year else age
        )
        effective_age = min(age, renovation_age)
        
        condition_multiplier = {
            "excellent": 1.2,
            "good": 1.0,
            "fair": 0.7,
            "poor": 0.4,
        }.get(metrics.building_condition.lower(), 1.0)
        
        # Score building (newer and better condition = higher score)
        if effective_age <= 5:
            building_base = 95
        elif effective_age <= 15:
            building_base = 80
        elif effective_age <= 30:
            building_base = 60
        elif effective_age <= 50:
            building_base = 40
        else:
            building_base = 25
        
        building_score = min(100, building_base * condition_multiplier)
        breakdown["building_score"] = building_score
        breakdown["effective_age"] = effective_age
        
        # Energy rating score
        energy_scores = {
            "A": 100, "B": 85, "C": 70, "D": 55,
            "E": 40, "F": 25, "G": 10
        }
        energy_score = energy_scores.get(metrics.energy_rating.upper(), 50)
        
        # Penalty for energy regulation risk
        if metrics.energy_regulation_risk and metrics.energy_rating.upper() in ["E", "F", "G"]:
            energy_score *= 0.5
        
        breakdown["energy_score"] = energy_score
        
        # Neighborhood safety (inverse of crime index)
        safety_score = max(0, 100 - metrics.crime_index)
        breakdown["neighborhood_safety"] = safety_score
        
        # Liquidity (days on market)
        dom = metrics.days_on_market_avg
        if dom <= self.BENCHMARKS["days_on_market_excellent"]:
            liquidity_score = 100
        elif dom >= self.BENCHMARKS["days_on_market_poor"]:
            liquidity_score = 30
        else:
            liquidity_score = 100 - 70 * (dom - self.BENCHMARKS["days_on_market_excellent"]) / (
                self.BENCHMARKS["days_on_market_poor"] - self.BENCHMARKS["days_on_market_excellent"]
            )
        
        breakdown["liquidity_score"] = liquidity_score
        
        # Weighted safety score
        safety_total = (
            building_score * 0.35 +
            energy_score * 0.25 +
            safety_score * 0.25 +
            liquidity_score * 0.15
        )
        
        return min(100, max(0, safety_total)), breakdown
    
    def calculate_growth_score(self, metrics: PropertyMetrics) -> tuple[float, Dict]:
        """
        Calculate growth score (0-100) based on market dynamics.
        
        Components:
        - Population Growth (35%)
        - Employment Growth (35%)
        - Infrastructure Development (20%)
        - School Quality (10%)
        """
        breakdown = {}
        
        # Population growth score
        pop_growth = metrics.population_growth_5y
        if pop_growth >= 0.10:
            pop_score = 100
        elif pop_growth >= 0.05:
            pop_score = 70 + 30 * (pop_growth - 0.05) / 0.05
        elif pop_growth >= 0:
            pop_score = 50 + 20 * pop_growth / 0.05
        else:
            pop_score = max(0, 50 + 50 * pop_growth / 0.05)
        
        breakdown["population_growth_score"] = pop_score
        
        # Employment growth score
        emp_growth = metrics.employment_growth_5y
        if emp_growth >= 0.15:
            emp_score = 100
        elif emp_growth >= 0.08:
            emp_score = 70 + 30 * (emp_growth - 0.08) / 0.07
        elif emp_growth >= 0:
            emp_score = 50 + 20 * emp_growth / 0.08
        else:
            emp_score = max(0, 50 + 50 * emp_growth / 0.10)
        
        breakdown["employment_growth_score"] = emp_score
        
        # Infrastructure bonus
        infra_score = 80 if metrics.new_infrastructure_nearby else 50
        breakdown["infrastructure_score"] = infra_score
        
        # School quality (1-10 scale to 0-100)
        school_score = min(100, metrics.school_rating * 10)
        breakdown["school_score"] = school_score
        
        # Weighted growth score
        growth_total = (
            pop_score * 0.35 +
            emp_score * 0.35 +
            infra_score * 0.20 +
            school_score * 0.10
        )
        
        return min(100, max(0, growth_total)), breakdown
    
    def calculate_legal_score(self, metrics: PropertyMetrics) -> tuple[float, Dict]:
        """
        Calculate legal/regulatory score (0-100).
        
        Components:
        - Property Tax Burden (40%)
        - Tenant Protection Level (35%)
        - Rent Control Risk (25%)
        """
        breakdown = {}
        
        # Property tax score (lower is better)
        tax_rate = metrics.property_tax_rate
        if tax_rate <= 0.005:
            tax_score = 100
        elif tax_rate <= 0.01:
            tax_score = 80 + 20 * (0.01 - tax_rate) / 0.005
        elif tax_rate <= 0.02:
            tax_score = 50 + 30 * (0.02 - tax_rate) / 0.01
        elif tax_rate <= 0.03:
            tax_score = 30 + 20 * (0.03 - tax_rate) / 0.01
        else:
            tax_score = max(0, 30 * (0.05 - tax_rate) / 0.02)
        
        breakdown["property_tax_score"] = tax_score
        
        # Tenant protection score (investor perspective - less protection = higher score)
        protection_scores = {
            "low": 90,
            "moderate": 65,
            "high": 40,
        }
        protection_score = protection_scores.get(
            metrics.tenant_protection_level.lower(), 60
        )
        breakdown["tenant_protection_score"] = protection_score
        
        # Rent control penalty
        if metrics.rent_control:
            rent_control_score = 30
            protection_score *= 0.8  # Additional penalty
        else:
            rent_control_score = 90
        
        breakdown["rent_control_score"] = rent_control_score
        
        # Weighted legal score
        legal_total = (
            tax_score * 0.40 +
            protection_score * 0.35 +
            rent_control_score * 0.25
        )
        
        return min(100, max(0, legal_total)), breakdown
    
    def identify_flags(self, metrics: PropertyMetrics, scores: Dict) -> tuple[List[str], List[str]]:
        """Identify risk flags and opportunities."""
        flags = []
        opportunities = []
        
        # Risk flags
        if metrics.energy_rating.upper() in ["F", "G"]:
            flags.append("CRITICAL: Low energy rating may ban rentals in EU")
        
        if metrics.vacancy_rate_area > 0.08:
            flags.append("HIGH: Area vacancy rate above 8%")
        
        if metrics.crime_index > 70:
            flags.append("HIGH: Crime index significantly above average")
        
        if metrics.rent_control:
            flags.append("MODERATE: Rent control limits income growth")
        
        if metrics.building_condition.lower() == "poor":
            flags.append("HIGH: Building condition requires major investment")
        
        if metrics.property_tax_rate > 0.025:
            flags.append("MODERATE: High property tax burden")
        
        # Opportunities
        if metrics.new_infrastructure_nearby:
            opportunities.append("New infrastructure may boost values")
        
        if metrics.population_growth_5y > 0.08:
            opportunities.append("Strong population growth supports demand")
        
        if metrics.school_rating > 8:
            opportunities.append("Top schools attract premium tenants")
        
        if scores.get("cap_rate", 0) > 0.07:
            opportunities.append("Above-average cap rate")
        
        if metrics.energy_rating.upper() in ["A", "B"]:
            opportunities.append("Excellent energy rating future-proofs asset")
        
        return flags, opportunities
    
    def calculate_confidence(self, metrics: PropertyMetrics) -> int:
        """
        Calculate confidence level based on data completeness.
        """
        confidence = 60  # Base confidence
        
        # Boost for complete financial data
        if metrics.annual_rent > 0 and metrics.annual_expenses > 0:
            confidence += 15
        
        # Boost for location data
        if metrics.crime_index != 50:  # Non-default value
            confidence += 5
        if metrics.population_growth_5y != 0:
            confidence += 5
        if metrics.employment_growth_5y != 0:
            confidence += 5
        
        # Boost for building data
        if metrics.last_renovation_year:
            confidence += 5
        if metrics.energy_rating.upper() != "C":  # Non-default
            confidence += 5
        
        return min(100, confidence)
    
    def score(self, metrics: PropertyMetrics) -> ProphetIAScore:
        """
        Calculate complete ProphetIA score for a property.
        """
        # Calculate component scores
        yield_score, yield_breakdown = self.calculate_yield_score(metrics)
        safety_score, safety_breakdown = self.calculate_safety_score(metrics)
        growth_score, growth_breakdown = self.calculate_growth_score(metrics)
        legal_score, legal_breakdown = self.calculate_legal_score(metrics)
        
        # Calculate weighted total
        total_score = (
            yield_score * self.weights.yield_weight +
            safety_score * self.weights.safety_weight +
            growth_score * self.weights.growth_weight +
            legal_score * self.weights.legal_weight
        )
        
        # Identify flags and opportunities
        all_breakdowns = {**yield_breakdown, **safety_breakdown, **growth_breakdown}
        risk_flags, opportunities = self.identify_flags(metrics, all_breakdowns)
        
        # Calculate confidence
        confidence = self.calculate_confidence(metrics)
        
        return ProphetIAScore(
            total_score=round(total_score, 1),
            yield_score=round(yield_score, 1),
            safety_score=round(safety_score, 1),
            growth_score=round(growth_score, 1),
            legal_score=round(legal_score, 1),
            confidence=confidence,
            risk_flags=risk_flags,
            opportunities=opportunities,
            breakdown={
                "yield": yield_breakdown,
                "safety": safety_breakdown,
                "growth": growth_breakdown,
                "legal": legal_breakdown,
                "weights": {
                    "yield": self.weights.yield_weight,
                    "safety": self.weights.safety_weight,
                    "growth": self.weights.growth_weight,
                    "legal": self.weights.legal_weight,
                }
            }
        )
