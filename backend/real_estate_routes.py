"""
MarketGPS Real Estate API Routes
Unified API for real estate analysis, tax simulations, and ProphetIA scoring.
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from engines.base_engine import PropertyDetails, TaxJurisdiction
from engines.fr_lmnp_engine import FRLMNPEngine
from engines.us_tax_engine import USTaxEngine, Property1031Params
from engines.ca_tax_engine import CanadaTaxEngine
from engines.prophetia_scoring import (
    ProphetIAScoring,
    PropertyMetrics,
    ScoreWeights,
    RiskProfile
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/real-estate", tags=["real-estate"])


# =============================================================================
# Request/Response Models
# =============================================================================

class PropertyInput(BaseModel):
    """Input model for property details."""
    purchase_price: float = Field(..., gt=0, description="Purchase price")
    land_ratio: float = Field(0.20, ge=0, le=1, description="Land portion (non-depreciable)")
    furniture_value: float = Field(0, ge=0, description="Furniture value (for LMNP)")
    acquisition_costs: float = Field(0, ge=0, description="Notary fees, etc.")
    annual_rent: float = Field(0, ge=0, description="Annual gross rent")
    annual_charges: float = Field(0, ge=0, description="Annual operating expenses")
    annual_interests: float = Field(0, ge=0, description="Annual loan interest")
    state_province: Optional[str] = Field(None, description="State/Province code (e.g., CA, QC)")


class TaxSimulationRequest(BaseModel):
    """Request for tax simulation."""
    property: PropertyInput
    jurisdiction: str = Field(..., description="Tax jurisdiction: FR, US, CA")
    marginal_tax_rate: float = Field(0.30, ge=0, le=0.6, description="Marginal tax rate")
    holding_years: int = Field(10, ge=1, le=50, description="Projection period")
    # LMNP specific
    claim_cca: bool = Field(True, description="Whether to claim CCA/depreciation")
    # US specific
    is_commercial: bool = Field(False, description="Commercial property (39y depreciation)")


class TaxSimulationResponse(BaseModel):
    """Response for tax simulation."""
    jurisdiction: str
    annual_summary: Dict[str, Any]
    projections: List[Dict[str, Any]]
    regime_comparison: Optional[Dict[str, Any]] = None


class ExitSimulationRequest(BaseModel):
    """Request for property sale simulation."""
    property: PropertyInput
    jurisdiction: str
    sale_price: float = Field(..., gt=0)
    holding_years: int = Field(..., ge=1)
    accumulated_depreciation: float = Field(0, ge=0)
    marginal_tax_rate: float = Field(0.30, ge=0, le=0.6)


class ExitSimulationResponse(BaseModel):
    """Response for exit simulation."""
    jurisdiction: str
    sale_price: float
    capital_gain: float
    recapture_amount: float
    total_tax: float
    net_proceeds: float
    details: Dict[str, Any]


class Exchange1031Request(BaseModel):
    """Request for 1031 Exchange simulation."""
    property: PropertyInput
    sale_price: float = Field(..., gt=0)
    replacement_price: float = Field(..., gt=0)
    replacement_debt: float = Field(0, ge=0)
    holding_years: int = Field(..., ge=1)
    accumulated_depreciation: float = Field(0, ge=0)
    marginal_tax_rate: float = Field(0.30)


class ScoringRequest(BaseModel):
    """Request for ProphetIA scoring."""
    # Financial
    purchase_price: float = Field(..., gt=0)
    annual_rent: float = Field(..., gt=0)
    annual_expenses: float = Field(0, ge=0)
    financing_cost: float = Field(0, ge=0)
    
    # Building
    year_built: int = Field(2000)
    energy_rating: str = Field("C")
    last_renovation_year: Optional[int] = None
    building_condition: str = Field("good")
    
    # Location
    population_growth_5y: float = Field(0.0)
    employment_growth_5y: float = Field(0.0)
    new_infrastructure_nearby: bool = Field(False)
    crime_index: float = Field(50.0)
    school_rating: float = Field(5.0)
    
    # Market
    days_on_market_avg: float = Field(60.0)
    price_to_rent_ratio: float = Field(20.0)
    vacancy_rate_area: float = Field(0.05)
    
    # Legal
    property_tax_rate: float = Field(0.01)
    rent_control: bool = Field(False)
    tenant_protection_level: str = Field("moderate")
    energy_regulation_risk: bool = Field(False)
    
    # Scoring preferences
    risk_profile: str = Field("balanced")


class ScoringResponse(BaseModel):
    """Response for ProphetIA scoring."""
    total_score: float
    rating: str
    recommendation: str
    yield_score: float
    safety_score: float
    growth_score: float
    legal_score: float
    confidence: int
    risk_flags: List[str]
    opportunities: List[str]
    breakdown: Dict[str, Any]


class WealthSummaryRequest(BaseModel):
    """Request for unified wealth summary."""
    properties: List[PropertyInput]
    jurisdictions: List[str]
    marginal_tax_rate: float = Field(0.30)


class WealthSummaryResponse(BaseModel):
    """Unified wealth response combining stocks and real estate."""
    total_real_estate_value: float
    total_annual_cashflow: float
    total_annual_tax_savings: float
    portfolio_yield: float
    properties: List[Dict[str, Any]]


# =============================================================================
# Helper Functions
# =============================================================================

def _create_property_details(prop: PropertyInput) -> PropertyDetails:
    """Convert API input to PropertyDetails."""
    return PropertyDetails(
        purchase_price=prop.purchase_price,
        land_ratio=prop.land_ratio,
        furniture_value=prop.furniture_value,
        acquisition_costs=prop.acquisition_costs,
        annual_rent=prop.annual_rent,
        annual_charges=prop.annual_charges,
        annual_interests=prop.annual_interests,
        province_state=prop.state_province,
    )


def _get_tax_engine(jurisdiction: str, property_details: PropertyDetails, **kwargs):
    """Factory function to get the appropriate tax engine."""
    jurisdiction = jurisdiction.upper()
    
    if jurisdiction == "FR":
        return FRLMNPEngine(property_details)
    elif jurisdiction == "US":
        state = property_details.province_state or "DEFAULT"
        is_commercial = kwargs.get("is_commercial", False)
        return USTaxEngine(property_details, is_commercial=is_commercial, state=state)
    elif jurisdiction == "CA":
        province = property_details.province_state or "ON"
        return CanadaTaxEngine(property_details, province=province)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported jurisdiction: {jurisdiction}. Use FR, US, or CA."
        )


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/simulate/annual", response_model=TaxSimulationResponse)
async def simulate_annual_tax(request: TaxSimulationRequest):
    """
    Simulate annual tax liability and cash flow projections.
    
    Supports:
    - FR: LMNP Régime Réel with component depreciation
    - US: MACRS depreciation with passive loss rules
    - CA: CCA with optional claiming
    """
    try:
        property_details = _create_property_details(request.property)
        engine = _get_tax_engine(
            request.jurisdiction,
            property_details,
            is_commercial=request.is_commercial
        )
        
        # Calculate annual simulation
        if request.jurisdiction.upper() == "CA":
            annual_result = engine.simulate_annual_tax(
                request.marginal_tax_rate,
                claim_cca=request.claim_cca
            )
        else:
            annual_result = engine.simulate_annual_tax(request.marginal_tax_rate)
        
        # Generate multi-year projections
        projections = engine.project_cashflow(
            years=request.holding_years,
            marginal_tax_rate=request.marginal_tax_rate
        )
        
        # Get regime comparison (FR only)
        regime_comparison = None
        if request.jurisdiction.upper() == "FR":
            regime_comparison = engine.compare_regimes(
                request.marginal_tax_rate,
                years=request.holding_years
            )
        
        return TaxSimulationResponse(
            jurisdiction=request.jurisdiction.upper(),
            annual_summary={
                "depreciation": annual_result.annual_depreciation,
                "taxable_income": annual_result.taxable_income,
                "tax_liability": annual_result.tax_liability,
                "cash_flow_net": annual_result.cash_flow_net,
                "effective_tax_rate": annual_result.effective_tax_rate,
                "deferred_depreciation": annual_result.deferred_depreciation,
                "metadata": annual_result.metadata,
            },
            projections=projections,
            regime_comparison=regime_comparison,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tax simulation error: {e}")
        raise HTTPException(status_code=500, detail="Tax simulation failed")


@router.post("/simulate/exit", response_model=ExitSimulationResponse)
async def simulate_exit(request: ExitSimulationRequest):
    """
    Simulate property sale with capital gains and depreciation recapture.
    """
    try:
        property_details = _create_property_details(request.property)
        engine = _get_tax_engine(request.jurisdiction, property_details)
        
        result = engine.simulate_exit(
            sale_price=request.sale_price,
            holding_years=request.holding_years,
            accumulated_depreciation=request.accumulated_depreciation,
            marginal_tax_rate=request.marginal_tax_rate,
        )
        
        return ExitSimulationResponse(
            jurisdiction=request.jurisdiction.upper(),
            sale_price=result.sale_price,
            capital_gain=result.capital_gain,
            recapture_amount=result.recapture_amount,
            total_tax=result.total_tax_on_exit,
            net_proceeds=result.net_proceeds,
            details=result.metadata,
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Exit simulation error: {e}")
        raise HTTPException(status_code=500, detail="Exit simulation failed")


@router.post("/simulate/1031-exchange")
async def simulate_1031_exchange(request: Exchange1031Request):
    """
    Simulate Section 1031 Like-Kind Exchange (US only).
    
    Compare tax-deferred exchange vs standard sale.
    """
    try:
        property_details = _create_property_details(request.property)
        state = request.property.state_province or "DEFAULT"
        
        engine = USTaxEngine(property_details, state=state)
        
        replacement = Property1031Params(
            replacement_price=request.replacement_price,
            replacement_debt=request.replacement_debt,
        )
        
        result = engine.simulate_1031_exchange(
            sale_price=request.sale_price,
            holding_years=request.holding_years,
            accumulated_depreciation=request.accumulated_depreciation,
            replacement=replacement,
            marginal_tax_rate=request.marginal_tax_rate,
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"1031 Exchange simulation error: {e}")
        raise HTTPException(status_code=500, detail="1031 simulation failed")


@router.post("/score", response_model=ScoringResponse)
async def calculate_prophetia_score(request: ScoringRequest):
    """
    Calculate ProphetIA score (0-100) for a property.
    
    The score combines:
    - Yield: Financial performance (cap rate, cash-on-cash)
    - Safety: Building quality, neighborhood
    - Growth: Market dynamics (population, employment)
    - Legal: Regulatory environment
    """
    try:
        # Parse risk profile
        try:
            profile = RiskProfile(request.risk_profile.lower())
        except ValueError:
            profile = RiskProfile.BALANCED
        
        weights = ScoreWeights.for_profile(profile)
        scoring_engine = ProphetIAScoring(weights=weights)
        
        metrics = PropertyMetrics(
            purchase_price=request.purchase_price,
            annual_rent=request.annual_rent,
            annual_expenses=request.annual_expenses,
            financing_cost=request.financing_cost,
            year_built=request.year_built,
            energy_rating=request.energy_rating,
            last_renovation_year=request.last_renovation_year,
            building_condition=request.building_condition,
            population_growth_5y=request.population_growth_5y,
            employment_growth_5y=request.employment_growth_5y,
            new_infrastructure_nearby=request.new_infrastructure_nearby,
            crime_index=request.crime_index,
            school_rating=request.school_rating,
            days_on_market_avg=request.days_on_market_avg,
            price_to_rent_ratio=request.price_to_rent_ratio,
            vacancy_rate_area=request.vacancy_rate_area,
            property_tax_rate=request.property_tax_rate,
            rent_control=request.rent_control,
            tenant_protection_level=request.tenant_protection_level,
            energy_regulation_risk=request.energy_regulation_risk,
        )
        
        score = scoring_engine.score(metrics)
        
        return ScoringResponse(
            total_score=score.total_score,
            rating=score.rating,
            recommendation=score.recommendation,
            yield_score=score.yield_score,
            safety_score=score.safety_score,
            growth_score=score.growth_score,
            legal_score=score.legal_score,
            confidence=score.confidence,
            risk_flags=score.risk_flags,
            opportunities=score.opportunities,
            breakdown=score.breakdown,
        )
    
    except Exception as e:
        logger.error(f"ProphetIA scoring error: {e}")
        raise HTTPException(status_code=500, detail="Scoring failed")


@router.get("/jurisdictions")
async def list_jurisdictions():
    """
    List supported tax jurisdictions with details.
    """
    return {
        "jurisdictions": [
            {
                "code": "FR",
                "name": "France",
                "regimes": ["LMNP_REEL", "MICRO_BIC"],
                "features": [
                    "Component-based depreciation",
                    "Deferred depreciation stock",
                    "17.2% social contributions",
                ],
            },
            {
                "code": "US",
                "name": "United States",
                "states_supported": True,
                "features": [
                    "MACRS depreciation (27.5y/39y)",
                    "Section 1031 Exchange",
                    "Depreciation recapture (25% max)",
                    "State-specific tax rates",
                ],
            },
            {
                "code": "CA",
                "name": "Canada",
                "provinces_supported": True,
                "features": [
                    "CCA classes (Class 1: 4%)",
                    "Half-year rule",
                    "66.67% capital gains inclusion (2024+)",
                    "CCA recapture on sale",
                    "GST/HST rebate for new builds",
                ],
            },
        ]
    }


@router.post("/wealth/summary", response_model=WealthSummaryResponse)
async def get_wealth_summary(request: WealthSummaryRequest):
    """
    Get unified wealth summary combining all properties.
    
    This endpoint aggregates real estate holdings for the
    Wealth Intelligence Dashboard.
    """
    try:
        total_value = 0
        total_cashflow = 0
        total_tax_savings = 0
        properties_data = []
        
        for prop, jurisdiction in zip(request.properties, request.jurisdictions):
            property_details = _create_property_details(prop)
            engine = _get_tax_engine(jurisdiction, property_details)
            
            annual = engine.simulate_annual_tax(request.marginal_tax_rate)
            
            total_value += prop.purchase_price
            total_cashflow += annual.cash_flow_net
            total_tax_savings += annual.annual_depreciation * request.marginal_tax_rate
            
            properties_data.append({
                "purchase_price": prop.purchase_price,
                "jurisdiction": jurisdiction,
                "annual_cashflow": annual.cash_flow_net,
                "depreciation": annual.annual_depreciation,
                "effective_tax_rate": annual.effective_tax_rate,
            })
        
        portfolio_yield = (total_cashflow / total_value * 100) if total_value > 0 else 0
        
        return WealthSummaryResponse(
            total_real_estate_value=total_value,
            total_annual_cashflow=total_cashflow,
            total_annual_tax_savings=total_tax_savings,
            portfolio_yield=round(portfolio_yield, 2),
            properties=properties_data,
        )
    
    except Exception as e:
        logger.error(f"Wealth summary error: {e}")
        raise HTTPException(status_code=500, detail="Wealth summary failed")
