/**
 * MarketGPS Real Estate Types
 * Types for the Wealth Intelligence module
 */

export type AssetClass = 'EQUITY' | 'REAL_ESTATE' | 'CASH' | 'ETF' | 'CRYPTO';

export type TaxJurisdiction = 'FR' | 'US' | 'CA' | 'BE' | 'DE' | 'CH';

export type RiskProfile = 'conservative' | 'balanced' | 'aggressive';

export type BuildingCondition = 'excellent' | 'good' | 'fair' | 'poor';

export type TenantProtectionLevel = 'low' | 'moderate' | 'high';

export type EnergyRating = 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';

// =============================================================================
// Property Types
// =============================================================================

export interface PropertyInput {
  purchase_price: number;
  land_ratio?: number;
  furniture_value?: number;
  acquisition_costs?: number;
  annual_rent?: number;
  annual_charges?: number;
  annual_interests?: number;
  state_province?: string;
}

export interface PropertyMetrics {
  // Financial
  purchase_price: number;
  annual_rent: number;
  annual_expenses: number;
  financing_cost?: number;
  
  // Building
  year_built?: number;
  energy_rating?: EnergyRating;
  last_renovation_year?: number;
  building_condition?: BuildingCondition;
  
  // Location
  population_growth_5y?: number;
  employment_growth_5y?: number;
  new_infrastructure_nearby?: boolean;
  crime_index?: number;
  school_rating?: number;
  
  // Market
  days_on_market_avg?: number;
  price_to_rent_ratio?: number;
  vacancy_rate_area?: number;
  
  // Legal
  property_tax_rate?: number;
  rent_control?: boolean;
  tenant_protection_level?: TenantProtectionLevel;
  energy_regulation_risk?: boolean;
}

// =============================================================================
// Tax Simulation Types
// =============================================================================

export interface TaxSimulationRequest {
  property: PropertyInput;
  jurisdiction: TaxJurisdiction;
  marginal_tax_rate?: number;
  holding_years?: number;
  claim_cca?: boolean;
  is_commercial?: boolean;
}

export interface AnnualSummary {
  depreciation: number;
  taxable_income: number;
  tax_liability: number;
  cash_flow_net: number;
  effective_tax_rate: number;
  deferred_depreciation: number;
  metadata: Record<string, any>;
}

export interface CashFlowProjection {
  year: number;
  gross_rent: number;
  charges: number;
  interests: number;
  depreciation: number;
  taxable_income: number;
  tax_liability: number;
  cash_flow_net: number;
  deferred_depreciation_stock: number;
}

export interface RegimeComparison {
  years: number;
  reel: {
    cumulative_tax: number;
    cumulative_cashflow: number;
  };
  micro_bic: {
    cumulative_tax: number;
    cumulative_cashflow: number;
  };
  advantage_reel: number;
  recommendation: 'LMNP_REEL' | 'MICRO_BIC';
}

export interface TaxSimulationResponse {
  jurisdiction: TaxJurisdiction;
  annual_summary: AnnualSummary;
  projections: CashFlowProjection[];
  regime_comparison?: RegimeComparison;
}

// =============================================================================
// Exit Simulation Types
// =============================================================================

export interface ExitSimulationRequest {
  property: PropertyInput;
  jurisdiction: TaxJurisdiction;
  sale_price: number;
  holding_years: number;
  accumulated_depreciation?: number;
  marginal_tax_rate?: number;
}

export interface ExitSimulationResponse {
  jurisdiction: TaxJurisdiction;
  sale_price: number;
  capital_gain: number;
  recapture_amount: number;
  total_tax: number;
  net_proceeds: number;
  details: Record<string, any>;
}

// =============================================================================
// 1031 Exchange Types (US Only)
// =============================================================================

export interface Exchange1031Request {
  property: PropertyInput;
  sale_price: number;
  replacement_price: number;
  replacement_debt?: number;
  holding_years: number;
  accumulated_depreciation?: number;
  marginal_tax_rate?: number;
}

export interface Exchange1031Response {
  exchange_valid: boolean;
  standard_exit: {
    total_tax: number;
    net_proceeds: number;
  };
  with_1031: {
    boot_taxable: number;
    boot_tax: number;
    deferred_gain: number;
    deferred_tax: number;
    net_proceeds: number;
  };
  reinvestment_advantage: {
    additional_capital: number;
    new_property_basis: number;
  };
  deadlines: {
    identify_by_day: number;
    close_by_day: number;
  };
  recommendation: 'PROCEED_1031' | 'CONSIDER_STANDARD_SALE';
}

// =============================================================================
// ProphetIA Scoring Types
// =============================================================================

export interface ScoringRequest extends PropertyMetrics {
  risk_profile?: RiskProfile;
}

export interface ScoreBreakdown {
  yield: Record<string, number>;
  safety: Record<string, number>;
  growth: Record<string, number>;
  legal: Record<string, number>;
  weights: {
    yield: number;
    safety: number;
    growth: number;
    legal: number;
  };
}

export interface ProphetIAScore {
  total_score: number;
  rating: 'A+' | 'A' | 'B+' | 'B' | 'C' | 'D' | 'F';
  recommendation: 'STRONG_BUY' | 'BUY' | 'HOLD' | 'SELL' | 'STRONG_SELL';
  yield_score: number;
  safety_score: number;
  growth_score: number;
  legal_score: number;
  confidence: number;
  risk_flags: string[];
  opportunities: string[];
  breakdown: ScoreBreakdown;
}

// =============================================================================
// Wealth Summary Types
// =============================================================================

export interface WealthAsset {
  id: string;
  name: string;
  type: AssetClass;
  value: number;
  change24h?: number;
  gpsScore: number;
  region: string;
  jurisdiction?: TaxJurisdiction;
}

export interface WealthSummary {
  totalNetWorth: number;
  liquidAssets: number;
  tangibleAssets: number;
  overallRiskScore: number;
  portfolioYield: number;
}

export interface RealEstatePortfolio {
  total_real_estate_value: number;
  total_annual_cashflow: number;
  total_annual_tax_savings: number;
  portfolio_yield: number;
  properties: PropertySummary[];
}

export interface PropertySummary {
  purchase_price: number;
  jurisdiction: TaxJurisdiction;
  annual_cashflow: number;
  depreciation: number;
  effective_tax_rate: number;
}

// =============================================================================
// AI Audit Types
// =============================================================================

export interface AIAuditResult {
  id: string;
  property_id: string;
  audit_type: 'document' | 'vision' | 'legal';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// =============================================================================
// Jurisdiction Info
// =============================================================================

export interface JurisdictionInfo {
  code: TaxJurisdiction;
  name: string;
  regimes?: string[];
  features: string[];
  states_supported?: boolean;
  provinces_supported?: boolean;
}
