/**
 * MarketGPS Wealth Agent - Types TypeScript
 * Types pour l'Agent Patrimonial Intelligent
 */

// =============================================================================
// Geo-Context
// =============================================================================

export interface CurrencyConfig {
  code: string;
  symbol: string;
  position: 'before' | 'after';
  decimal_separator: string;
  thousands_separator: string;
}

export interface UnitConfig {
  system: 'metric' | 'imperial';
  area_unit: string;
  area_multiplier: number;
  distance_unit: string;
}

export interface TaxJurisdictionConfig {
  code: string;
  name: string;
  rental_income_tax_type: string;
  default_tax_rate: number;
  depreciation_available: boolean;
  special_regimes: string[];
}

export interface LocalTerminology {
  rental_income: string;
  net_operating_income: string;
  cap_rate: string;
  cash_flow: string;
  depreciation: string;
  capital_gains_tax: string;
  property_tax: string;
  rental_yield: string;
  tenant: string;
  landlord: string;
  lease: string;
  furnished_rental: string;
  unfurnished_rental: string;
  short_term_rental: string;
  mortgage: string;
  down_payment: string;
  notary_fees: string;
  stamp_duty: string;
  renovation_costs: string;
  energy_rating: string;
}

export interface MarketPulse {
  country: string;
  city: string | null;
  central_bank: string;
  central_bank_rate: number;
  rate_trend: 'up' | 'stable' | 'down';
  last_rate_change: string | null;
  next_rate_decision: string | null;
  avg_price_per_m2: number;
  price_trend_yoy: number;
  avg_rent_per_m2: number;
  rent_trend_yoy: number;
  avg_yield: number;
  vacancy_rate: number;
  days_on_market_avg: number;
  transaction_volume_trend: 'up' | 'stable' | 'down';
  updated_at: string;
}

export interface GeoContext {
  country: string;
  city: string | null;
  language: string;
  currency: CurrencyConfig;
  units: UnitConfig;
  tax_jurisdiction: TaxJurisdictionConfig;
  terminology: LocalTerminology;
  market_pulse: MarketPulse;
  detected_at: string;
  detection_method: 'ip' | 'browser' | 'user_choice';
  confidence: number;
}

// =============================================================================
// Opportunity Radar
// =============================================================================

export type PropertyType = 
  | 'apartment' 
  | 'house' 
  | 'studio' 
  | 'duplex' 
  | 'triplex' 
  | 'building' 
  | 'commercial' 
  | 'land' 
  | 'parking';

export type SignalType = 
  | 'price_drop' 
  | 'reactivated' 
  | 'long_listing' 
  | 'yield_anomaly' 
  | 'underpriced' 
  | 'zone_acceleration';

export type SignalPriority = 'critical' | 'high' | 'medium' | 'low';

export interface PriceChange {
  date: string;
  old_price: number;
  new_price: number;
  change_percent: number;
}

export interface NormalizedListing {
  id: string;
  source_id: string;
  source: string;
  
  // Location
  country: string;
  city: string;
  postal_code: string;
  neighborhood?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
  
  // Property
  property_type: PropertyType;
  surface_m2: number;
  rooms?: number;
  bedrooms?: number;
  bathrooms?: number;
  floor?: number;
  total_floors?: number;
  has_elevator?: boolean;
  has_balcony?: boolean;
  has_terrace?: boolean;
  has_parking?: boolean;
  has_garage?: boolean;
  has_garden?: boolean;
  orientation?: string;
  
  // Construction
  construction_year?: number;
  renovation_year?: number;
  building_condition: string;
  energy_rating?: string;
  ghg_rating?: string;
  
  // Price
  price: number;
  currency: string;
  price_per_m2: number;
  charges_monthly?: number;
  property_tax_annual?: number;
  
  // Rental
  is_rented: boolean;
  current_rent_monthly?: number;
  rental_yield_gross?: number;
  
  // Meta
  title: string;
  description: string;
  images: string[];
  url: string;
  agent_name?: string;
  agent_phone?: string;
  
  // Timestamps
  published_at?: string;
  updated_at?: string;
  scraped_at: string;
  
  // Signals
  days_on_market: number;
  price_changes: PriceChange[];
  is_reactivated: boolean;
  reactivation_count: number;
  
  // ProphetIA
  prophetia_score?: number;
  prophetia_yield?: number;
  prophetia_safety?: number;
  prophetia_growth?: number;
  prophetia_legal?: number;
}

export interface DealSignal {
  id: string;
  listing_id: string;
  signal_type: SignalType;
  priority: SignalPriority;
  detected_at: string;
  
  score_before?: number;
  score_after?: number;
  score_delta?: number;
  
  evidence: string[];
  confidence: number;
  
  summary: string;
  summary_long: string;
  risks: string[];
  next_steps: string[];
  
  expires_at?: string;
  is_read: boolean;
  is_dismissed: boolean;
}

export interface MarketStats {
  country: string;
  city: string;
  postal_code?: string;
  median_price_per_m2: number;
  p25_price_per_m2: number;
  p75_price_per_m2: number;
  price_trend_3m: number;
  median_rent_per_m2: number;
  avg_yield_gross: number;
  yield_std_dev: number;
  listings_count: number;
  new_listings_30d: number;
  transactions_count_qoq: number;
  avg_days_on_market: number;
  updated_at: string;
}

export interface Opportunity {
  listing: NormalizedListing;
  signals: DealSignal[];
  market_stats?: MarketStats;
}

export interface OpportunitySummary {
  total_opportunities: number;
  signals_by_type: Record<string, number>;
  high_priority_count: number;
  top_opportunities: Array<{
    listing: NormalizedListing;
    signal_count: number;
    top_signal: DealSignal | null;
  }>;
}

// =============================================================================
// Visual Inspector
// =============================================================================

export type OverallCondition = 'excellent' | 'good' | 'fair' | 'poor' | 'to_renovate';
export type PositioningLevel = 'luxury' | 'premium' | 'standard' | 'budget';

export interface DetectedElement {
  type: string;
  material?: string;
  brand?: string;
  condition: string;
  age_estimate?: string;
  notes?: string;
  confidence: number;
}

export interface RenovationEstimate {
  work_type: string;
  description: string;
  cost_low: number;
  cost_high: number;
  priority: 'required' | 'recommended' | 'optional';
  timeline_days?: number;
  confidence: number;
}

export interface VisualAnalysis {
  overall_condition: OverallCondition;
  condition_score: number;
  condition_confidence: number;
  condition_summary: string;
  
  elements: DetectedElement[];
  
  renovations: RenovationEstimate[];
  total_cost_low: number;
  total_cost_high: number;
  
  listed_positioning: PositioningLevel;
  actual_quality: PositioningLevel;
  mismatch_detected: boolean;
  estimated_overpricing_percent?: number;
  mismatch_evidence: string[];
  
  strengths: string[];
  weaknesses: string[];
  
  images_analyzed: number;
  analysis_timestamp: string;
  model_version: string;
}

// =============================================================================
// Pulse Feed
// =============================================================================

export type PulseCategory = 'regulation' | 'rates' | 'market' | 'local' | 'fiscal' | 'energy';
export type ImpactLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type ImpactType = 'positive' | 'negative' | 'neutral' | 'mixed';

export interface CentralBankRate {
  bank: string;
  bank_full_name: string;
  rate: number;
  previous_rate: number;
  trend: 'up' | 'stable' | 'down';
  last_change_date: string;
  next_decision_date?: string;
  change_amount: number;
  countries_affected: string[];
}

export interface PulseItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  source_url?: string;
  published_at: string;
  
  category: PulseCategory;
  countries_affected: string[];
  
  impact_level: ImpactLevel;
  impact_type: ImpactType;
  impact_description: string;
  
  affected_scores: Record<string, number>;
  
  user_action_required: boolean;
  recommended_actions: string[];
  
  is_read: boolean;
  is_bookmarked: boolean;
  expires_at?: string;
}

export interface PulseSummary {
  total_items: number;
  by_category: Record<string, number>;
  by_impact_level: Record<string, number>;
  action_required_count: number;
  central_bank_rates: CentralBankRate[];
  critical_items: PulseItem[];
  action_required_items: PulseItem[];
}

// =============================================================================
// Onboarding
// =============================================================================

export interface OnboardingAnswers {
  locations: string[];
  capital_available: number;
  investment_goal: 'income' | 'wealth';
  risk_profile?: 'conservative' | 'balanced' | 'aggressive';
}

export interface ActionPlanStep {
  step: number;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

export interface OnboardingResult {
  success: boolean;
  profile: {
    locations: string[];
    capital: number;
    goal: string;
    risk_profile: string;
  };
  opportunities: Opportunity[];
  watchlist: {
    name: string;
    description: string;
    criteria: Record<string, any>;
    status: string;
  };
  action_plan: ActionPlanStep[];
  market_pulse: MarketPulse[];
  next_steps: string[];
}

// =============================================================================
// Watchlist
// =============================================================================

export interface Watchlist {
  id: string;
  user_id: string;
  name: string;
  countries: string[];
  cities?: string[];
  property_types?: string[];
  price_min?: number;
  price_max?: number;
  yield_min?: number;
  score_min?: number;
  notify_email: boolean;
  notify_push: boolean;
  is_active: boolean;
  created_at: string;
  match_count: number;
}

export interface WatchlistCreate {
  name: string;
  countries: string[];
  cities?: string[];
  property_types?: string[];
  price_min?: number;
  price_max?: number;
  yield_min?: number;
  score_min?: number;
  notify_email?: boolean;
  notify_push?: boolean;
}

// =============================================================================
// ProphetIA Score
// =============================================================================

export interface ProphetIAScore {
  total_score: number;
  rating: string;
  recommendation: string;
  yield_score: number;
  safety_score: number;
  growth_score: number;
  legal_score: number;
  confidence: number;
  risk_flags: string[];
  opportunities: string[];
  breakdown: Record<string, any>;
}

// =============================================================================
// Demo Portfolio
// =============================================================================

export interface DemoProperty {
  id: string;
  name: string;
  city: string;
  country: string;
  type: string;
  surface_m2: number;
  purchase_price: number;
  current_value: number;
  acquisition_date: string;
  annual_rent: number;
  annual_expenses: number;
  annual_cashflow: number;
  yield_gross: number;
  yield_net: number;
  prophetia_score: number;
  energy_rating: string;
  status: string;
}

export interface DemoPortfolioSummary {
  total_value: number;
  total_invested: number;
  total_annual_rent: number;
  total_annual_cashflow: number;
  portfolio_yield_gross: number;
  portfolio_yield_net: number;
  weighted_score: number;
  countries: string[];
  properties_count: number;
}

export interface DemoPortfolio {
  properties: DemoProperty[];
  summary: DemoPortfolioSummary;
  alerts: Array<{
    type: string;
    severity: string;
    property_id: string;
    message: string;
  }>;
}
