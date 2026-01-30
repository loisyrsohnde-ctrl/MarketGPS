"""
MarketGPS Real Estate - Canadian Tax Engine
Capital Cost Allowance (CCA) and Capital Gains calculations.

Key Features:
- CCA (Déduction pour amortissement) - optional but triggers recapture
- Half-year rule for first-year CCA
- 66.67% capital gains inclusion rate (2024+ for high amounts)
- Provincial tax rate variations
"""

from dataclasses import dataclass
from typing import Dict, Any
from .base_engine import (
    BaseTaxEngine,
    PropertyDetails,
    TaxSimulationResult,
    ExitSimulationResult,
    TaxJurisdiction
)


# Provincial tax rates (2024 highest bracket estimates)
PROVINCIAL_TAX_RATES = {
    "ON": 0.1316,  # Ontario
    "QC": 0.2575,  # Quebec
    "BC": 0.205,   # British Columbia
    "AB": 0.15,    # Alberta
    "SK": 0.145,   # Saskatchewan
    "MB": 0.174,   # Manitoba
    "NB": 0.195,   # New Brunswick
    "NS": 0.21,    # Nova Scotia
    "PE": 0.18,    # Prince Edward Island
    "NL": 0.183,   # Newfoundland and Labrador
    "DEFAULT": 0.15,
}

# Federal rates (2024)
FEDERAL_TOP_RATE = 0.33
CAPITAL_GAINS_INCLUSION_STANDARD = 0.50
CAPITAL_GAINS_INCLUSION_HIGH = 0.6667  # For gains over threshold


@dataclass
class CCAClass:
    """Capital Cost Allowance class definition."""
    class_number: int
    rate: float
    description: str
    declining_balance: bool = True  # Most CCA classes use declining balance


# Common CCA classes for real estate
CCA_CLASSES = {
    1: CCAClass(1, 0.04, "Most buildings acquired after 1987"),
    3: CCAClass(3, 0.05, "Buildings acquired before 1988"),
    6: CCAClass(6, 0.10, "Frame buildings, greenhouses"),
    8: CCAClass(8, 0.20, "Furniture, fixtures, appliances"),
    50: CCAClass(50, 0.55, "Computer equipment"),
}


class CanadaTaxEngine(BaseTaxEngine):
    """
    Canadian Tax Engine for Real Estate Investments.
    
    Key considerations:
    - CCA is optional but triggers recapture on sale
    - CCA cannot create or increase a rental loss
    - Capital gains have tiered inclusion rates (2024+)
    - GST/HST considerations for new builds
    """
    
    def __init__(
        self,
        property_details: PropertyDetails,
        province: str = "ON",
        cca_class: int = 1,
        is_first_year: bool = False
    ):
        super().__init__(property_details)
        self.province = province.upper()
        self.cca_class = CCA_CLASSES.get(cca_class, CCA_CLASSES[1])
        self.is_first_year = is_first_year
        self._accumulated_cca = 0.0
        self._ucc = self.building_value  # Undepreciated Capital Cost
    
    @property
    def jurisdiction(self) -> TaxJurisdiction:
        return TaxJurisdiction.CA
    
    @property
    def provincial_rate(self) -> float:
        return PROVINCIAL_TAX_RATES.get(self.province, PROVINCIAL_TAX_RATES["DEFAULT"])
    
    @property
    def combined_marginal_rate(self) -> float:
        """Combined federal + provincial top marginal rate."""
        return FEDERAL_TOP_RATE + self.provincial_rate
    
    @property
    def building_value(self) -> float:
        """Value of the building (excluding land)."""
        return self.property.purchase_price * (1 - self.property.land_ratio)
    
    def calculate_annual_depreciation(self) -> float:
        """
        Calculate CCA for the year.
        Uses declining balance method with half-year rule.
        """
        if self._ucc <= 0:
            return 0
        
        base_cca = self._ucc * self.cca_class.rate
        
        # Half-year rule: only 50% CCA in first year of acquisition
        if self.is_first_year:
            return base_cca / 2
        
        return base_cca
    
    def calculate_max_cca(self, net_income_before_cca: float) -> float:
        """
        Calculate maximum claimable CCA.
        CCA cannot create or increase a rental loss.
        """
        if net_income_before_cca <= 0:
            return 0
        
        theoretical_cca = self.calculate_annual_depreciation()
        return min(theoretical_cca, net_income_before_cca)
    
    def simulate_annual_tax(
        self,
        marginal_tax_rate: float = None,
        social_contributions_rate: float = 0.0,  # Not applicable in CA
        claim_cca: bool = True
    ) -> TaxSimulationResult:
        """
        Simulate annual tax with optional CCA claim.
        
        The CCA toggle allows users to see impact of claiming vs not claiming.
        """
        if marginal_tax_rate is None:
            marginal_tax_rate = self.combined_marginal_rate
        
        gross_rent = self.property.annual_rent
        
        # Calculate net income before CCA
        deductible_expenses = (
            self.property.annual_charges +
            self.property.annual_interests
        )
        
        net_income_before_cca = gross_rent - deductible_expenses
        
        # Calculate CCA if claiming
        if claim_cca and net_income_before_cca > 0:
            cca_claimed = self.calculate_max_cca(net_income_before_cca)
        else:
            cca_claimed = 0
        
        taxable_income = max(0, net_income_before_cca - cca_claimed)
        
        # Calculate tax (combined federal + provincial)
        total_tax = taxable_income * marginal_tax_rate
        
        # Cash flow
        cash_flow_before_tax = gross_rent - deductible_expenses
        cash_flow_net = cash_flow_before_tax - total_tax
        
        # Track CCA for recapture calculations
        unused_cca = self.calculate_annual_depreciation() - cca_claimed
        
        return TaxSimulationResult(
            jurisdiction=self.jurisdiction,
            annual_depreciation=cca_claimed,
            taxable_income=taxable_income,
            tax_liability=total_tax,
            cash_flow_net=cash_flow_net,
            deferred_depreciation=unused_cca,
            effective_tax_rate=(total_tax / gross_rent * 100) if gross_rent > 0 else 0,
            metadata={
                "cca_claimed": cca_claimed,
                "cca_available": self.calculate_annual_depreciation(),
                "cca_class": self.cca_class.class_number,
                "province": self.province,
                "net_income_before_cca": net_income_before_cca,
                "marginal_rate": marginal_tax_rate,
            }
        )
    
    def simulate_exit(
        self,
        sale_price: float,
        holding_years: int,
        accumulated_cca: float,
        marginal_tax_rate: float = None
    ) -> ExitSimulationResult:
        """
        Simulate sale with CCA recapture and capital gains.
        
        Recapture: If sale price > UCC, recapture is added to income (100% taxable)
        Capital Gain: Gain above original cost, partially included in income
        """
        if marginal_tax_rate is None:
            marginal_tax_rate = self.combined_marginal_rate
        
        purchase_price = self.property.purchase_price
        original_building_cost = self.building_value
        ucc = original_building_cost - accumulated_cca  # Undepreciated Capital Cost
        
        # Allocate sale price between land and building
        sale_building = sale_price * (1 - self.property.land_ratio)
        sale_land = sale_price * self.property.land_ratio
        
        # Calculate recapture
        # Recapture occurs when sale price > UCC (up to original cost)
        if sale_building > ucc:
            recapture = min(accumulated_cca, sale_building - ucc)
        else:
            recapture = 0
        
        # Calculate capital gain
        total_original_cost = purchase_price + self.property.acquisition_costs
        
        if sale_price > total_original_cost:
            capital_gain = sale_price - total_original_cost
        else:
            capital_gain = 0
        
        # Determine inclusion rate
        # 2024+: 50% for first $250k, 66.67% above (for individuals)
        threshold = 250000
        if capital_gain <= threshold:
            inclusion_rate = CAPITAL_GAINS_INCLUSION_STANDARD
        else:
            # Blended rate
            gain_at_50 = threshold
            gain_at_67 = capital_gain - threshold
            taxable_gain = (
                gain_at_50 * CAPITAL_GAINS_INCLUSION_STANDARD +
                gain_at_67 * CAPITAL_GAINS_INCLUSION_HIGH
            )
            inclusion_rate = taxable_gain / capital_gain if capital_gain > 0 else 0.50
        
        taxable_capital_gain = capital_gain * inclusion_rate
        
        # Calculate taxes
        recapture_tax = recapture * marginal_tax_rate  # 100% included
        capital_gains_tax = taxable_capital_gain * marginal_tax_rate
        
        total_tax = recapture_tax + capital_gains_tax
        net_proceeds = sale_price - total_tax
        
        return ExitSimulationResult(
            jurisdiction=self.jurisdiction,
            sale_price=sale_price,
            capital_gain=capital_gain,
            recapture_amount=recapture,
            total_tax_on_exit=total_tax,
            net_proceeds=net_proceeds,
            tax_deferred=0,
            metadata={
                "ucc_at_sale": ucc,
                "accumulated_cca": accumulated_cca,
                "recapture_tax": recapture_tax,
                "capital_gains_tax": capital_gains_tax,
                "inclusion_rate": inclusion_rate,
                "province": self.province,
            }
        )
    
    def compare_cca_strategies(
        self,
        years: int = 10,
        marginal_tax_rate: float = None,
        expected_sale_price: float = None
    ) -> Dict[str, Any]:
        """
        Compare claiming vs not claiming CCA over the holding period.
        
        Key insight: CCA provides tax deferral, not elimination.
        All CCA is eventually recaptured on sale.
        """
        if marginal_tax_rate is None:
            marginal_tax_rate = self.combined_marginal_rate
        
        if expected_sale_price is None:
            # Assume 3% annual appreciation
            expected_sale_price = self.property.purchase_price * (1.03 ** years)
        
        # Strategy A: Claim maximum CCA each year
        total_tax_with_cca = 0
        accumulated_cca = 0
        temp_ucc = self.building_value
        
        for year in range(years):
            self._ucc = temp_ucc
            self.is_first_year = (year == 0)
            
            result = self.simulate_annual_tax(
                marginal_tax_rate=marginal_tax_rate,
                claim_cca=True
            )
            total_tax_with_cca += result.tax_liability
            cca_claimed = result.metadata["cca_claimed"]
            accumulated_cca += cca_claimed
            temp_ucc -= cca_claimed
        
        # Exit with CCA
        exit_with_cca = self.simulate_exit(
            expected_sale_price, years, accumulated_cca, marginal_tax_rate
        )
        total_with_cca = total_tax_with_cca + exit_with_cca.total_tax_on_exit
        
        # Strategy B: Never claim CCA
        self._ucc = self.building_value  # Reset
        total_tax_without_cca = 0
        
        for year in range(years):
            self.is_first_year = (year == 0)
            result = self.simulate_annual_tax(
                marginal_tax_rate=marginal_tax_rate,
                claim_cca=False
            )
            total_tax_without_cca += result.tax_liability
        
        # Exit without CCA (no recapture)
        exit_without_cca = self.simulate_exit(
            expected_sale_price, years, 0, marginal_tax_rate
        )
        total_without_cca = total_tax_without_cca + exit_without_cca.total_tax_on_exit
        
        # Calculate present value advantage (assuming 5% discount rate)
        discount_rate = 0.05
        pv_savings_from_cca = sum(
            (self.calculate_annual_depreciation() * marginal_tax_rate) / ((1 + discount_rate) ** year)
            for year in range(1, years + 1)
        )
        
        return {
            "holding_years": years,
            "with_cca": {
                "annual_taxes_paid": total_tax_with_cca,
                "exit_tax": exit_with_cca.total_tax_on_exit,
                "total_lifetime_tax": total_with_cca,
                "accumulated_cca": accumulated_cca,
                "recapture_on_exit": exit_with_cca.recapture_amount,
            },
            "without_cca": {
                "annual_taxes_paid": total_tax_without_cca,
                "exit_tax": exit_without_cca.total_tax_on_exit,
                "total_lifetime_tax": total_without_cca,
            },
            "analysis": {
                "total_tax_difference": total_without_cca - total_with_cca,
                "pv_of_tax_deferral": pv_savings_from_cca,
                "recommendation": (
                    "CLAIM_CCA" if pv_savings_from_cca > 1000 
                    else "EVALUATE_CASE_BY_CASE"
                ),
            }
        }
    
    def calculate_gst_hst_rebate(
        self,
        is_new_build: bool,
        gst_hst_paid: float,
        fair_market_rent: float
    ) -> Dict[str, float]:
        """
        Calculate GST/HST New Housing Rebate for rental properties.
        
        For new builds purchased for rental, investors may qualify
        for a rebate of part of the GST/HST paid.
        """
        if not is_new_build:
            return {"rebate": 0, "note": "Only applies to new builds"}
        
        # Simplified calculation (actual rules are more complex)
        # Federal GST portion rebate (max 36% of GST, phased out above $350k)
        gst_rate = 0.05
        gst_portion = gst_hst_paid * (gst_rate / 0.13)  # Assuming 13% HST
        
        max_rebate = gst_portion * 0.36
        
        # Phase-out above $350k (for $450k+, no rebate)
        if self.property.purchase_price > 450000:
            rebate = 0
        elif self.property.purchase_price > 350000:
            phase_out = (self.property.purchase_price - 350000) / 100000
            rebate = max_rebate * (1 - phase_out)
        else:
            rebate = max_rebate
        
        return {
            "gst_hst_paid": gst_hst_paid,
            "estimated_rebate": rebate,
            "net_tax_cost": gst_hst_paid - rebate,
            "impact_on_acb": -rebate,  # Reduces Adjusted Cost Base
        }
