"""
MarketGPS Real Estate - Base Tax Engine
Abstract base class for all jurisdiction-specific tax engines.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class TaxJurisdiction(str, Enum):
    FR = "FR"  # France
    BE = "BE"  # Belgium
    DE = "DE"  # Germany
    CH = "CH"  # Switzerland
    US = "US"  # United States
    CA = "CA"  # Canada


@dataclass
class PropertyDetails:
    """Core property information for tax calculations."""
    purchase_price: float
    land_ratio: float = 0.20  # Default 20% for land (non-depreciable)
    furniture_value: float = 0.0
    acquisition_costs: float = 0.0  # Notary fees, etc.
    annual_rent: float = 0.0
    annual_charges: float = 0.0  # Property tax, insurance, maintenance
    annual_interests: float = 0.0  # Loan interests
    province_state: Optional[str] = None  # For US/CA state taxes


@dataclass
class TaxSimulationResult:
    """Unified result structure for all tax engines."""
    jurisdiction: TaxJurisdiction
    annual_depreciation: float
    taxable_income: float
    tax_liability: float
    cash_flow_net: float
    deferred_depreciation: float = 0.0
    effective_tax_rate: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExitSimulationResult:
    """Result structure for property sale simulations."""
    jurisdiction: TaxJurisdiction
    sale_price: float
    capital_gain: float
    recapture_amount: float  # Depreciation recapture (US/CA)
    total_tax_on_exit: float
    net_proceeds: float
    tax_deferred: float = 0.0  # For 1031 Exchange scenarios
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTaxEngine(ABC):
    """
    Abstract base class for jurisdiction-specific tax calculation engines.
    All engines must implement these methods to ensure consistency.
    """
    
    def __init__(self, property_details: PropertyDetails):
        self.property = property_details
        self._validate_inputs()
    
    def _validate_inputs(self):
        """Basic validation for property details."""
        if self.property.purchase_price <= 0:
            raise ValueError("Purchase price must be positive")
        if not 0 <= self.property.land_ratio <= 1:
            raise ValueError("Land ratio must be between 0 and 1")
    
    @property
    @abstractmethod
    def jurisdiction(self) -> TaxJurisdiction:
        """Return the jurisdiction this engine handles."""
        pass
    
    @abstractmethod
    def calculate_annual_depreciation(self) -> float:
        """Calculate the annual depreciation/amortization amount."""
        pass
    
    @abstractmethod
    def simulate_annual_tax(
        self,
        marginal_tax_rate: float,
        social_contributions_rate: float = 0.0
    ) -> TaxSimulationResult:
        """
        Simulate annual tax liability.
        
        Args:
            marginal_tax_rate: User's marginal income tax rate (0.0 to 1.0)
            social_contributions_rate: Additional social charges (France: 17.2%)
        
        Returns:
            TaxSimulationResult with detailed breakdown
        """
        pass
    
    @abstractmethod
    def simulate_exit(
        self,
        sale_price: float,
        holding_years: int,
        accumulated_depreciation: float,
        marginal_tax_rate: float
    ) -> ExitSimulationResult:
        """
        Simulate tax implications of selling the property.
        
        Args:
            sale_price: Expected sale price
            holding_years: Number of years property was held
            accumulated_depreciation: Total depreciation claimed
            marginal_tax_rate: User's marginal tax rate at exit
        
        Returns:
            ExitSimulationResult with detailed breakdown
        """
        pass
    
    def project_cashflow(
        self,
        years: int,
        marginal_tax_rate: float,
        social_contributions_rate: float = 0.0,
        rent_growth_rate: float = 0.02,
        expense_growth_rate: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        Project cash flow over multiple years.
        
        Returns:
            List of annual projections with detailed breakdowns
        """
        projections = []
        current_rent = self.property.annual_rent
        current_charges = self.property.annual_charges
        current_interests = self.property.annual_interests
        accumulated_deferred = 0.0
        
        for year in range(1, years + 1):
            # Update property values for this year
            original_rent = self.property.annual_rent
            original_charges = self.property.annual_charges
            original_interests = self.property.annual_interests
            
            self.property.annual_rent = current_rent
            self.property.annual_charges = current_charges
            self.property.annual_interests = current_interests
            
            # Calculate tax for this year
            result = self.simulate_annual_tax(
                marginal_tax_rate, 
                social_contributions_rate
            )
            
            accumulated_deferred += result.deferred_depreciation
            
            projections.append({
                "year": year,
                "gross_rent": current_rent,
                "charges": current_charges,
                "interests": current_interests,
                "depreciation": result.annual_depreciation,
                "taxable_income": result.taxable_income,
                "tax_liability": result.tax_liability,
                "cash_flow_net": result.cash_flow_net,
                "deferred_depreciation_stock": accumulated_deferred,
            })
            
            # Restore original values
            self.property.annual_rent = original_rent
            self.property.annual_charges = original_charges
            self.property.annual_interests = original_interests
            
            # Apply growth rates for next year
            current_rent *= (1 + rent_growth_rate)
            current_charges *= (1 + expense_growth_rate)
            # Interests typically decrease with loan amortization
            current_interests *= 0.97  # ~3% decrease per year
        
        return projections
