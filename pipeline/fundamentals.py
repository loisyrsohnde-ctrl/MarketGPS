"""
MarketGPS Fundamentals Module.
Fundamental data processing and validation.
"""
from typing import Dict, Optional, List
from dataclasses import dataclass

from core.utils import get_logger, safe_float
from providers.base import Fundamentals

logger = get_logger(__name__)


@dataclass
class FundamentalQuality:
    """Quality assessment for fundamental data."""
    is_complete: bool = False
    coverage_pct: float = 0.0
    missing_fields: List[str] = None
    anomalies: List[str] = None
    
    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []
        if self.anomalies is None:
            self.anomalies = []


class FundamentalsProcessor:
    """
    Processor for fundamental data.
    
    Validates, normalizes, and assesses quality of fundamental data.
    """
    
    # Key fields for completeness check
    KEY_FIELDS = ["pe_ratio", "profit_margin", "roe"]
    
    # All fields for coverage
    ALL_FIELDS = [
        "pe_ratio", "forward_pe", "profit_margin", "operating_margin",
        "roe", "roa", "revenue_growth", "earnings_growth",
        "debt_to_equity", "current_ratio", "market_cap"
    ]
    
    # Reasonable bounds for validation
    BOUNDS = {
        "pe_ratio": (0, 500),
        "forward_pe": (0, 500),
        "profit_margin": (-1, 1),
        "operating_margin": (-1, 1),
        "roe": (-2, 2),
        "roa": (-1, 1),
        "revenue_growth": (-1, 5),
        "earnings_growth": (-5, 10),
        "debt_to_equity": (0, 50),
        "current_ratio": (0, 20),
        "market_cap": (0, float("inf")),
    }
    
    @classmethod
    def validate(cls, fundamentals: Fundamentals) -> Fundamentals:
        """
        Validate and clean fundamental data.
        
        Args:
            fundamentals: Raw fundamentals
            
        Returns:
            Validated fundamentals with outliers clamped
        """
        if fundamentals is None:
            return None
        
        data = fundamentals.to_dict()
        
        for field, (min_val, max_val) in cls.BOUNDS.items():
            if field in data and data[field] is not None:
                value = safe_float(data[field])
                if value < min_val or value > max_val:
                    logger.debug(f"Clamping {field}: {value} -> within [{min_val}, {max_val}]")
                    data[field] = max(min_val, min(max_val, value))
        
        return Fundamentals(**data)
    
    @classmethod
    def assess_quality(cls, fundamentals: Optional[Fundamentals]) -> FundamentalQuality:
        """
        Assess quality of fundamental data.
        
        Args:
            fundamentals: Fundamentals to assess
            
        Returns:
            Quality assessment
        """
        if fundamentals is None:
            return FundamentalQuality(
                is_complete=False,
                coverage_pct=0.0,
                missing_fields=cls.ALL_FIELDS.copy()
            )
        
        data = fundamentals.to_dict()
        
        # Check key fields
        missing_key = [f for f in cls.KEY_FIELDS if data.get(f) is None]
        is_complete = len(missing_key) == 0
        
        # Calculate coverage
        missing = [f for f in cls.ALL_FIELDS if data.get(f) is None]
        available = len(cls.ALL_FIELDS) - len(missing)
        coverage = available / len(cls.ALL_FIELDS) * 100
        
        # Check for anomalies
        anomalies = []
        
        # PE should be positive for profitable companies
        if data.get("pe_ratio") is not None:
            pe = data["pe_ratio"]
            if pe < 0:
                anomalies.append(f"Negative P/E ({pe:.1f})")
            elif pe > 100:
                anomalies.append(f"Very high P/E ({pe:.1f})")
        
        # Profit margin sanity check
        if data.get("profit_margin") is not None:
            margin = data["profit_margin"]
            if margin > 0.5:
                anomalies.append(f"Very high profit margin ({margin:.1%})")
            elif margin < -0.5:
                anomalies.append(f"Very negative profit margin ({margin:.1%})")
        
        return FundamentalQuality(
            is_complete=is_complete,
            coverage_pct=coverage,
            missing_fields=missing,
            anomalies=anomalies
        )
    
    @classmethod
    def merge_fundamentals(
        cls,
        primary: Optional[Fundamentals],
        secondary: Optional[Fundamentals]
    ) -> Optional[Fundamentals]:
        """
        Merge fundamentals from multiple sources.
        Primary takes precedence, secondary fills gaps.
        """
        if primary is None:
            return secondary
        if secondary is None:
            return primary
        
        primary_data = primary.to_dict()
        secondary_data = secondary.to_dict()
        
        # Fill gaps from secondary
        for field in cls.ALL_FIELDS:
            if primary_data.get(field) is None and secondary_data.get(field) is not None:
                primary_data[field] = secondary_data[field]
        
        return Fundamentals(**primary_data)
