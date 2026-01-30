"""
MarketGPS Real Estate - French LMNP Tax Engine
Location Meublée Non Professionnelle (Régime Réel)

Key Features:
- Component-based depreciation (amortissement par composants)
- Depreciation cannot create a tax deficit (règle du déficit LMNP)
- Deferred depreciation stock (report des amortissements)
- 17.2% social contributions on rental income
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from .base_engine import (
    BaseTaxEngine,
    PropertyDetails,
    TaxSimulationResult,
    ExitSimulationResult,
    TaxJurisdiction
)


@dataclass
class DepreciationComponent:
    """A single depreciation component."""
    name: str
    share_of_building: float  # Percentage of building value
    duration_years: int
    
    def annual_amount(self, building_value: float) -> float:
        return (building_value * self.share_of_building) / self.duration_years


# Standard LMNP depreciation components (French accounting standards)
DEFAULT_COMPONENTS = [
    DepreciationComponent("gros_oeuvre", 0.50, 40),      # Structure
    DepreciationComponent("toiture", 0.10, 25),          # Roof
    DepreciationComponent("installations", 0.15, 20),     # Technical systems
    DepreciationComponent("agencements", 0.25, 15),       # Fixtures & finishes
]

FURNITURE_DURATION = 7  # Years for furniture depreciation


class FRLMNPEngine(BaseTaxEngine):
    """
    French LMNP (Location Meublée Non Professionnelle) Tax Engine.
    
    Implements the "régime réel" with component-based depreciation.
    The key rule: depreciation cannot create or increase a rental deficit.
    Unused depreciation is deferred indefinitely.
    """
    
    SOCIAL_CONTRIBUTIONS_RATE = 0.172  # 17.2% in 2024
    
    def __init__(
        self,
        property_details: PropertyDetails,
        components: List[DepreciationComponent] = None,
        furniture_duration: int = FURNITURE_DURATION
    ):
        super().__init__(property_details)
        self.components = components or DEFAULT_COMPONENTS
        self.furniture_duration = furniture_duration
        self._deferred_depreciation_stock = 0.0
    
    @property
    def jurisdiction(self) -> TaxJurisdiction:
        return TaxJurisdiction.FR
    
    @property
    def building_value(self) -> float:
        """Value of the building (excluding land)."""
        return self.property.purchase_price * (1 - self.property.land_ratio)
    
    def calculate_annual_depreciation(self) -> float:
        """
        Calculate total annual depreciation including:
        - Building components
        - Furniture
        - Acquisition costs (optional: can be expensed in year 1)
        """
        # Building depreciation (sum of all components)
        building_depreciation = sum(
            comp.annual_amount(self.building_value)
            for comp in self.components
        )
        
        # Furniture depreciation
        furniture_depreciation = (
            self.property.furniture_value / self.furniture_duration
            if self.property.furniture_value > 0 else 0
        )
        
        return building_depreciation + furniture_depreciation
    
    def calculate_component_breakdown(self) -> Dict[str, float]:
        """Get detailed breakdown of depreciation by component."""
        breakdown = {}
        
        for comp in self.components:
            breakdown[comp.name] = comp.annual_amount(self.building_value)
        
        if self.property.furniture_value > 0:
            breakdown["mobilier"] = (
                self.property.furniture_value / self.furniture_duration
            )
        
        breakdown["total"] = sum(breakdown.values())
        return breakdown
    
    def simulate_annual_tax(
        self,
        marginal_tax_rate: float,
        social_contributions_rate: float = None
    ) -> TaxSimulationResult:
        """
        Simulate annual tax under LMNP régime réel.
        
        The key LMNP rule: Depreciation can only reduce taxable income to zero,
        not create a deficit. Excess depreciation is deferred.
        """
        if social_contributions_rate is None:
            social_contributions_rate = self.SOCIAL_CONTRIBUTIONS_RATE
        
        # Step 1: Calculate pre-depreciation profit
        gross_rent = self.property.annual_rent
        deductible_charges = self.property.annual_charges
        deductible_interests = self.property.annual_interests
        
        pre_depreciation_profit = gross_rent - deductible_charges - deductible_interests
        
        # Step 2: Calculate available depreciation
        annual_depreciation = self.calculate_annual_depreciation()
        
        # Step 3: Apply LMNP deficit rule
        if pre_depreciation_profit > 0:
            # Depreciation can reduce profit to zero
            used_depreciation = min(pre_depreciation_profit, annual_depreciation)
            taxable_income = max(0, pre_depreciation_profit - used_depreciation)
            deferred_depreciation = annual_depreciation - used_depreciation
        else:
            # Deficit before depreciation: no depreciation can be used
            # Deficit is carried forward under BIC rules
            used_depreciation = 0
            taxable_income = 0  # Deficit, but reported as 0 for this calc
            deferred_depreciation = annual_depreciation
        
        # Step 4: Calculate taxes
        income_tax = taxable_income * marginal_tax_rate
        social_tax = taxable_income * social_contributions_rate
        total_tax = income_tax + social_tax
        
        # Step 5: Calculate net cash flow
        # Cash flow = Rent - Charges - Interests - Taxes
        # (Depreciation is non-cash)
        cash_flow_before_tax = gross_rent - deductible_charges - deductible_interests
        cash_flow_net = cash_flow_before_tax - total_tax
        
        effective_rate = (total_tax / gross_rent * 100) if gross_rent > 0 else 0
        
        return TaxSimulationResult(
            jurisdiction=self.jurisdiction,
            annual_depreciation=annual_depreciation,
            taxable_income=taxable_income,
            tax_liability=total_tax,
            cash_flow_net=cash_flow_net,
            deferred_depreciation=deferred_depreciation,
            effective_tax_rate=effective_rate,
            metadata={
                "used_depreciation": used_depreciation,
                "pre_depreciation_profit": pre_depreciation_profit,
                "income_tax": income_tax,
                "social_contributions": social_tax,
                "regime": "LMNP_REEL",
            }
        )
    
    def simulate_micro_bic(
        self,
        marginal_tax_rate: float,
        social_contributions_rate: float = None
    ) -> TaxSimulationResult:
        """
        Simulate tax under Micro-BIC regime for comparison.
        50% flat deduction on gross rent.
        """
        if social_contributions_rate is None:
            social_contributions_rate = self.SOCIAL_CONTRIBUTIONS_RATE
        
        gross_rent = self.property.annual_rent
        taxable_income = gross_rent * 0.50  # 50% abatement
        
        income_tax = taxable_income * marginal_tax_rate
        social_tax = taxable_income * social_contributions_rate
        total_tax = income_tax + social_tax
        
        # Cash flow under micro-BIC (no deduction for actual charges)
        actual_charges = self.property.annual_charges + self.property.annual_interests
        cash_flow_net = gross_rent - actual_charges - total_tax
        
        return TaxSimulationResult(
            jurisdiction=self.jurisdiction,
            annual_depreciation=0,  # No depreciation in micro-BIC
            taxable_income=taxable_income,
            tax_liability=total_tax,
            cash_flow_net=cash_flow_net,
            deferred_depreciation=0,
            effective_tax_rate=(total_tax / gross_rent * 100) if gross_rent > 0 else 0,
            metadata={
                "regime": "MICRO_BIC",
                "abatement_rate": 0.50,
            }
        )
    
    def compare_regimes(
        self,
        marginal_tax_rate: float,
        years: int = 10
    ) -> Dict[str, Any]:
        """
        Compare LMNP Réel vs Micro-BIC over multiple years.
        Returns cumulative analysis.
        """
        reel_total_tax = 0
        micro_total_tax = 0
        reel_total_cashflow = 0
        micro_total_cashflow = 0
        
        for _ in range(years):
            reel = self.simulate_annual_tax(marginal_tax_rate)
            micro = self.simulate_micro_bic(marginal_tax_rate)
            
            reel_total_tax += reel.tax_liability
            micro_total_tax += micro.tax_liability
            reel_total_cashflow += reel.cash_flow_net
            micro_total_cashflow += micro.cash_flow_net
        
        advantage = micro_total_tax - reel_total_tax
        
        return {
            "years": years,
            "reel": {
                "cumulative_tax": reel_total_tax,
                "cumulative_cashflow": reel_total_cashflow,
            },
            "micro_bic": {
                "cumulative_tax": micro_total_tax,
                "cumulative_cashflow": micro_total_cashflow,
            },
            "advantage_reel": advantage,
            "recommendation": "LMNP_REEL" if advantage > 0 else "MICRO_BIC",
        }
    
    def simulate_exit(
        self,
        sale_price: float,
        holding_years: int,
        accumulated_depreciation: float,
        marginal_tax_rate: float
    ) -> ExitSimulationResult:
        """
        Simulate sale of LMNP property.
        
        In France, LMNP sales are subject to:
        - Capital gains tax on the plus-value
        - Possible recapture if sold within certain timeframes
        - Abatements based on holding period (after 5 years)
        """
        purchase_price = self.property.purchase_price
        acquisition_costs = self.property.acquisition_costs
        
        # Gross capital gain
        total_cost = purchase_price + acquisition_costs
        gross_gain = sale_price - total_cost
        
        # Apply French holding period abatements
        # After 22 years: full exemption for income tax
        # After 30 years: full exemption for social contributions
        if holding_years >= 22:
            ir_abatement = 1.0
        elif holding_years >= 6:
            ir_abatement = 0.06 * (holding_years - 5)  # 6% per year after year 5
        else:
            ir_abatement = 0.0
        
        if holding_years >= 30:
            ps_abatement = 1.0
        elif holding_years >= 6:
            ps_abatement = 0.0165 * (holding_years - 5)  # 1.65% per year after year 5
        else:
            ps_abatement = 0.0
        
        taxable_gain_ir = max(0, gross_gain * (1 - min(1, ir_abatement)))
        taxable_gain_ps = max(0, gross_gain * (1 - min(1, ps_abatement)))
        
        # Apply flat rates
        income_tax = taxable_gain_ir * 0.19  # 19% flat rate
        social_tax = taxable_gain_ps * self.SOCIAL_CONTRIBUTIONS_RATE
        
        # Additional surtax for large gains (over 50k€)
        if gross_gain > 50000:
            surtax = (gross_gain - 50000) * 0.06
            income_tax += surtax
        
        total_tax = income_tax + social_tax
        net_proceeds = sale_price - total_tax
        
        return ExitSimulationResult(
            jurisdiction=self.jurisdiction,
            sale_price=sale_price,
            capital_gain=gross_gain,
            recapture_amount=0,  # No formal recapture in French LMNP
            total_tax_on_exit=total_tax,
            net_proceeds=net_proceeds,
            tax_deferred=0,
            metadata={
                "income_tax": income_tax,
                "social_contributions": social_tax,
                "ir_abatement_rate": ir_abatement,
                "ps_abatement_rate": ps_abatement,
                "holding_years": holding_years,
            }
        )
