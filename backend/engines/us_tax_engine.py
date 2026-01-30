"""
MarketGPS Real Estate - US Tax Engine
Federal + State tax calculations for real estate investments.

Key Features:
- MACRS depreciation (27.5 years residential, 39 years commercial)
- Section 1031 Exchange simulation (tax-deferred exchange)
- Depreciation Recapture (Section 1250)
- State-specific tax rates
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from .base_engine import (
    BaseTaxEngine,
    PropertyDetails,
    TaxSimulationResult,
    ExitSimulationResult,
    TaxJurisdiction
)


# State tax rates (2024 estimates)
STATE_TAX_RATES = {
    "CA": 0.133,   # California (highest bracket)
    "NY": 0.109,   # New York
    "TX": 0.0,     # Texas (no state income tax)
    "FL": 0.0,     # Florida (no state income tax)
    "WA": 0.0,     # Washington (no state income tax)
    "NV": 0.0,     # Nevada (no state income tax)
    "IL": 0.0495,  # Illinois (flat rate)
    "PA": 0.0307,  # Pennsylvania (flat rate)
    "OH": 0.04,    # Ohio
    "GA": 0.055,   # Georgia
    "NC": 0.0525,  # North Carolina (flat rate)
    "NJ": 0.1075,  # New Jersey
    "AZ": 0.025,   # Arizona (flat rate)
    "CO": 0.044,   # Colorado (flat rate)
    "DEFAULT": 0.05,  # Default assumption
}


@dataclass
class Property1031Params:
    """Parameters for 1031 Exchange simulation."""
    replacement_price: float
    replacement_debt: float = 0.0
    days_to_identify: int = 45  # IRS deadline
    days_to_close: int = 180   # IRS deadline


class USTaxEngine(BaseTaxEngine):
    """
    US Federal + State Tax Engine for Real Estate.
    
    Implements:
    - MACRS depreciation (27.5 years for residential)
    - Passive loss rules
    - Section 1031 Like-Kind Exchange
    - Depreciation Recapture (capped at 25%)
    """
    
    RESIDENTIAL_DEPRECIATION_YEARS = 27.5
    COMMERCIAL_DEPRECIATION_YEARS = 39.0
    RECAPTURE_RATE = 0.25  # Section 1250 unrecaptured gain rate
    LTCG_RATE = 0.20  # Long-term capital gains (top bracket)
    NIIT_RATE = 0.038  # Net Investment Income Tax (3.8%)
    
    def __init__(
        self,
        property_details: PropertyDetails,
        is_commercial: bool = False,
        state: str = "DEFAULT"
    ):
        super().__init__(property_details)
        self.is_commercial = is_commercial
        self.state = state.upper()
        self.depreciation_years = (
            self.COMMERCIAL_DEPRECIATION_YEARS if is_commercial
            else self.RESIDENTIAL_DEPRECIATION_YEARS
        )
    
    @property
    def jurisdiction(self) -> TaxJurisdiction:
        return TaxJurisdiction.US
    
    @property
    def state_tax_rate(self) -> float:
        return STATE_TAX_RATES.get(self.state, STATE_TAX_RATES["DEFAULT"])
    
    @property
    def building_value(self) -> float:
        """Value of the building (excluding land)."""
        return self.property.purchase_price * (1 - self.property.land_ratio)
    
    def calculate_annual_depreciation(self) -> float:
        """
        Calculate MACRS straight-line depreciation.
        Note: First and last year use mid-month convention.
        """
        return self.building_value / self.depreciation_years
    
    def simulate_annual_tax(
        self,
        marginal_tax_rate: float,
        social_contributions_rate: float = 0.0  # Not applicable in US
    ) -> TaxSimulationResult:
        """
        Simulate annual federal + state tax liability.
        
        US rental income is generally considered "passive income"
        subject to passive loss rules.
        """
        gross_rent = self.property.annual_rent
        depreciation = self.calculate_annual_depreciation()
        
        # Deductible expenses
        deductible = (
            self.property.annual_charges +  # Property tax, insurance, maintenance
            self.property.annual_interests +  # Mortgage interest
            depreciation  # Non-cash deduction
        )
        
        # Net rental income (can be negative = passive loss)
        net_rental_income = gross_rent - deductible
        
        # Passive loss rules: losses can only offset passive income
        # For high earners, passive losses are suspended
        # Simplified: assume losses can be used (or are carried forward)
        taxable_income = max(0, net_rental_income)
        
        # Federal tax on rental income (ordinary income rates)
        federal_tax = taxable_income * marginal_tax_rate
        
        # Net Investment Income Tax (NIIT) - 3.8% for high earners
        # Applies if MAGI > $200k single / $250k married
        niit = taxable_income * self.NIIT_RATE
        
        # State tax
        state_tax = taxable_income * self.state_tax_rate
        
        total_tax = federal_tax + niit + state_tax
        
        # Cash flow (rent - actual cash outflows - taxes)
        cash_flow_before_tax = (
            gross_rent - 
            self.property.annual_charges - 
            self.property.annual_interests
        )
        cash_flow_net = cash_flow_before_tax - total_tax
        
        passive_loss = max(0, -net_rental_income)
        
        return TaxSimulationResult(
            jurisdiction=self.jurisdiction,
            annual_depreciation=depreciation,
            taxable_income=taxable_income,
            tax_liability=total_tax,
            cash_flow_net=cash_flow_net,
            deferred_depreciation=0,  # US uses suspended passive losses instead
            effective_tax_rate=(total_tax / gross_rent * 100) if gross_rent > 0 else 0,
            metadata={
                "federal_tax": federal_tax,
                "state_tax": state_tax,
                "niit": niit,
                "state": self.state,
                "passive_loss_suspended": passive_loss,
                "net_rental_income": net_rental_income,
            }
        )
    
    def simulate_exit(
        self,
        sale_price: float,
        holding_years: int,
        accumulated_depreciation: float,
        marginal_tax_rate: float
    ) -> ExitSimulationResult:
        """
        Simulate sale with depreciation recapture.
        
        When selling, accumulated depreciation is "recaptured" and taxed
        at a maximum rate of 25% (Section 1250 unrecaptured gain).
        """
        purchase_price = self.property.purchase_price
        acquisition_costs = self.property.acquisition_costs
        
        # Adjusted basis = Cost - Accumulated Depreciation
        original_basis = purchase_price + acquisition_costs
        adjusted_basis = original_basis - accumulated_depreciation
        
        # Total gain
        total_gain = sale_price - adjusted_basis
        
        if total_gain <= 0:
            # Loss - no taxes
            return ExitSimulationResult(
                jurisdiction=self.jurisdiction,
                sale_price=sale_price,
                capital_gain=total_gain,
                recapture_amount=0,
                total_tax_on_exit=0,
                net_proceeds=sale_price,
                tax_deferred=0,
                metadata={"result": "loss", "loss_amount": abs(total_gain)}
            )
        
        # Split gain into components:
        # 1. Depreciation Recapture (taxed at 25% max)
        # 2. Remaining capital gain (taxed at LTCG rates)
        
        recapture_gain = min(accumulated_depreciation, total_gain)
        capital_gain = max(0, total_gain - recapture_gain)
        
        # Calculate taxes
        recapture_tax = recapture_gain * self.RECAPTURE_RATE
        ltcg_tax = capital_gain * self.LTCG_RATE
        niit_tax = total_gain * self.NIIT_RATE
        state_tax = total_gain * self.state_tax_rate
        
        total_tax = recapture_tax + ltcg_tax + niit_tax + state_tax
        net_proceeds = sale_price - total_tax
        
        return ExitSimulationResult(
            jurisdiction=self.jurisdiction,
            sale_price=sale_price,
            capital_gain=total_gain,
            recapture_amount=recapture_gain,
            total_tax_on_exit=total_tax,
            net_proceeds=net_proceeds,
            tax_deferred=0,
            metadata={
                "adjusted_basis": adjusted_basis,
                "recapture_tax": recapture_tax,
                "ltcg_tax": ltcg_tax,
                "niit_tax": niit_tax,
                "state_tax": state_tax,
                "accumulated_depreciation": accumulated_depreciation,
            }
        )
    
    def simulate_1031_exchange(
        self,
        sale_price: float,
        holding_years: int,
        accumulated_depreciation: float,
        replacement: Property1031Params,
        marginal_tax_rate: float
    ) -> Dict[str, Any]:
        """
        Simulate Section 1031 Like-Kind Exchange.
        
        Requirements for full tax deferral:
        - Replacement property must be equal or greater value
        - All proceeds must be reinvested
        - Must identify replacement within 45 days
        - Must close within 180 days
        - Cannot touch the cash (use Qualified Intermediary)
        """
        # First, calculate what taxes would be without 1031
        standard_exit = self.simulate_exit(
            sale_price, holding_years, accumulated_depreciation, marginal_tax_rate
        )
        
        # Calculate boot (taxable portion)
        cash_boot = max(0, sale_price - replacement.replacement_price)
        
        # Mortgage boot (debt relief without replacement debt)
        current_debt = self.property.purchase_price * 0.7  # Assume 70% LTV
        mortgage_boot = max(0, current_debt - replacement.replacement_debt)
        
        total_boot = cash_boot + mortgage_boot
        
        # Boot is taxable (pro-rata between recapture and capital gain)
        if total_boot > 0:
            boot_ratio = min(1, total_boot / standard_exit.capital_gain)
            taxable_recapture = standard_exit.recapture_amount * boot_ratio
            taxable_ltcg = (standard_exit.capital_gain - standard_exit.recapture_amount) * boot_ratio
            
            boot_tax = (
                taxable_recapture * self.RECAPTURE_RATE +
                taxable_ltcg * self.LTCG_RATE +
                total_boot * self.NIIT_RATE +
                total_boot * self.state_tax_rate
            )
        else:
            boot_tax = 0
        
        # Deferred gain
        deferred_gain = standard_exit.capital_gain - total_boot
        deferred_tax = standard_exit.total_tax_on_exit - boot_tax
        
        # New basis in replacement property
        # Basis = Replacement Price - Deferred Gain
        new_basis = replacement.replacement_price - deferred_gain
        
        # Calculate reinvestment power advantage
        reinvestment_power = deferred_tax  # Cash that stays invested
        
        return {
            "exchange_valid": replacement.replacement_price >= sale_price,
            "standard_exit": {
                "total_tax": standard_exit.total_tax_on_exit,
                "net_proceeds": standard_exit.net_proceeds,
            },
            "with_1031": {
                "boot_taxable": total_boot,
                "boot_tax": boot_tax,
                "deferred_gain": deferred_gain,
                "deferred_tax": deferred_tax,
                "net_proceeds": sale_price - boot_tax,
            },
            "reinvestment_advantage": {
                "additional_capital": reinvestment_power,
                "new_property_basis": new_basis,
            },
            "deadlines": {
                "identify_by_day": replacement.days_to_identify,
                "close_by_day": replacement.days_to_close,
            },
            "recommendation": (
                "PROCEED_1031" if deferred_tax > 5000 else "CONSIDER_STANDARD_SALE"
            )
        }
    
    def compare_with_without_1031(
        self,
        sale_price: float,
        replacement_price: float,
        holding_years: int,
        accumulated_depreciation: float,
        marginal_tax_rate: float,
        projection_years: int = 15
    ) -> Dict[str, Any]:
        """
        Compare wealth accumulation with and without 1031 exchanges
        over multiple cycles.
        """
        # Scenario A: Sell and pay taxes each time
        wealth_standard = sale_price
        accumulated_standard = accumulated_depreciation
        
        # Scenario B: 1031 Exchange continuously
        wealth_1031 = sale_price
        accumulated_1031 = accumulated_depreciation
        deferred_total = 0
        
        # Simulate over projection period
        for year in range(projection_years):
            # Assume 5% annual appreciation
            wealth_standard *= 1.05
            wealth_1031 *= 1.05
        
        # At end of period, calculate final tax impact
        exit_standard = self.simulate_exit(
            wealth_standard, projection_years, accumulated_standard, marginal_tax_rate
        )
        
        exit_1031 = self.simulate_exit(
            wealth_1031, projection_years, 
            accumulated_depreciation * (projection_years / holding_years),  # More depreciation
            marginal_tax_rate
        )
        
        return {
            "projection_years": projection_years,
            "standard_strategy": {
                "final_wealth": exit_standard.net_proceeds,
            },
            "1031_strategy": {
                "final_wealth": exit_1031.net_proceeds,
                "note": "Deferred taxes compound wealth",
            },
            "wealth_advantage_1031": exit_1031.net_proceeds - exit_standard.net_proceeds,
            "advantage_percentage": (
                (exit_1031.net_proceeds - exit_standard.net_proceeds) / 
                exit_standard.net_proceeds * 100
            ),
        }
