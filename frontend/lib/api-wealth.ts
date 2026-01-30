/**
 * MarketGPS Wealth Agent - API Client
 * Client pour l'Agent Patrimonial Intelligent
 */

import { getApiBaseUrl } from './config';
import type {
  GeoContext,
  MarketPulse,
  Opportunity,
  OpportunitySummary,
  VisualAnalysis,
  PulseItem,
  PulseSummary,
  CentralBankRate,
  OnboardingAnswers,
  OnboardingResult,
  Watchlist,
  WatchlistCreate,
  ProphetIAScore,
  DemoPortfolio,
} from '@/types/wealth-agent';

const API_BASE = getApiBaseUrl();

// =============================================================================
// Helpers
// =============================================================================

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }
  
  return response.json();
}

// =============================================================================
// Geo-Context API
// =============================================================================

export async function getGeoContext(
  country?: string,
  language?: string
): Promise<GeoContext> {
  const params = new URLSearchParams();
  if (country) params.set('country', country);
  if (language) params.set('language', language);
  
  const query = params.toString();
  return fetchApi<GeoContext>(`/api/wealth/geo-context${query ? `?${query}` : ''}`);
}

export async function getSupportedCountries(): Promise<Array<{
  code: string;
  name: string;
  currency: string;
  tax_regimes: string[];
}>> {
  return fetchApi('/api/wealth/geo-context/countries');
}

export async function getMarketPulse(
  country: string,
  city?: string
): Promise<MarketPulse> {
  const params = city ? `?city=${encodeURIComponent(city)}` : '';
  return fetchApi<MarketPulse>(`/api/wealth/geo-context/market-pulse/${country}${params}`);
}

// =============================================================================
// Opportunity Radar API
// =============================================================================

export interface OpportunityFilters {
  countries?: string[];
  cities?: string[];
  price_min?: number;
  price_max?: number;
  yield_min?: number;
  score_min?: number;
  signals_only?: boolean;
  limit?: number;
}

export async function getOpportunities(
  filters: OpportunityFilters = {}
): Promise<{ opportunities: Opportunity[]; total: number }> {
  return fetchApi('/api/wealth/opportunities', {
    method: 'POST',
    body: JSON.stringify({
      countries: filters.countries || ['FR'],
      cities: filters.cities,
      price_min: filters.price_min,
      price_max: filters.price_max,
      yield_min: filters.yield_min,
      score_min: filters.score_min,
      signals_only: filters.signals_only || false,
      limit: filters.limit || 50,
    }),
  });
}

export async function getOpportunitiesSummary(
  countries: string[] = ['FR']
): Promise<OpportunitySummary> {
  const params = `countries=${countries.join(',')}`;
  return fetchApi<OpportunitySummary>(`/api/wealth/opportunities/summary?${params}`);
}

export async function getOpportunityDetail(
  listingId: string
): Promise<Opportunity> {
  return fetchApi<Opportunity>(`/api/wealth/opportunities/${listingId}`);
}

// =============================================================================
// Visual Inspector API
// =============================================================================

export interface VisualInspectorRequest {
  image_urls: string[];
  country?: string;
  surface_m2?: number;
  listed_price?: number;
  listed_positioning?: string;
}

export async function analyzeImages(
  request: VisualInspectorRequest
): Promise<VisualAnalysis> {
  return fetchApi('/api/wealth/visual-inspector', {
    method: 'POST',
    body: JSON.stringify({
      image_urls: request.image_urls,
      country: request.country || 'FR',
      surface_m2: request.surface_m2,
      listed_price: request.listed_price,
      listed_positioning: request.listed_positioning,
    }),
  });
}

export async function getRenovationCosts(
  country: string
): Promise<{ country: string; costs: Record<string, [number, number]>; currency: string }> {
  return fetchApi(`/api/wealth/visual-inspector/renovation-costs/${country}`);
}

// =============================================================================
// Pulse Feed API
// =============================================================================

export interface PulseFilters {
  countries?: string[];
  categories?: string[];
  impact_levels?: string[];
  limit?: number;
  offset?: number;
}

export async function getPulseItems(
  filters: PulseFilters = {}
): Promise<{ items: PulseItem[]; total: number }> {
  return fetchApi('/api/wealth/pulse', {
    method: 'POST',
    body: JSON.stringify({
      countries: filters.countries,
      categories: filters.categories,
      impact_levels: filters.impact_levels,
      limit: filters.limit || 20,
      offset: filters.offset || 0,
    }),
  });
}

export async function getPulseSummary(
  countries?: string[]
): Promise<PulseSummary> {
  const params = countries ? `?countries=${countries.join(',')}` : '';
  return fetchApi<PulseSummary>(`/api/wealth/pulse/summary${params}`);
}

export async function getCentralBankRates(
  countries?: string[]
): Promise<CentralBankRate[]> {
  const params = countries ? `?countries=${countries.join(',')}` : '';
  return fetchApi<CentralBankRate[]>(`/api/wealth/pulse/rates${params}`);
}

export async function calculatePortfolioImpact(
  pulseItemId: string,
  portfolioProperties: Array<{ id: string; country: string }>
): Promise<{
  pulse_item_id: string;
  estimated_cashflow_impact_annual: number;
  estimated_value_impact_percent: number;
  affected_properties: string[];
  affected_properties_count: number;
  impact_breakdown: string;
  mitigation_steps: string[];
}> {
  return fetchApi('/api/wealth/pulse/portfolio-impact', {
    method: 'POST',
    body: JSON.stringify({
      pulse_item_id: pulseItemId,
      portfolio_properties: portfolioProperties,
    }),
  });
}

// =============================================================================
// Onboarding API
// =============================================================================

export async function completeOnboarding(
  answers: OnboardingAnswers
): Promise<OnboardingResult> {
  return fetchApi('/api/wealth/onboarding', {
    method: 'POST',
    body: JSON.stringify(answers),
  });
}

export async function getDemoPortfolio(): Promise<DemoPortfolio> {
  return fetchApi<DemoPortfolio>('/api/wealth/onboarding/demo-portfolio');
}

// =============================================================================
// Scoring API
// =============================================================================

export interface PropertyScoreRequest {
  purchase_price: number;
  annual_rent: number;
  annual_expenses: number;
  financing_cost?: number;
  year_built?: number;
  energy_rating?: string;
  building_condition?: string;
  vacancy_rate?: number;
  property_tax_rate?: number;
  rent_control?: boolean;
  risk_profile?: string;
  country?: string;
}

export async function scoreProperty(
  request: PropertyScoreRequest
): Promise<ProphetIAScore> {
  return fetchApi('/api/wealth/score', {
    method: 'POST',
    body: JSON.stringify({
      purchase_price: request.purchase_price,
      annual_rent: request.annual_rent,
      annual_expenses: request.annual_expenses,
      financing_cost: request.financing_cost || 0,
      year_built: request.year_built || 2000,
      energy_rating: request.energy_rating || 'C',
      building_condition: request.building_condition || 'good',
      vacancy_rate: request.vacancy_rate || 0.05,
      property_tax_rate: request.property_tax_rate || 0.01,
      rent_control: request.rent_control || false,
      risk_profile: request.risk_profile || 'balanced',
      country: request.country || 'FR',
    }),
  });
}

// =============================================================================
// Watchlist API
// =============================================================================

export async function createWatchlist(
  watchlist: WatchlistCreate,
  userId?: string
): Promise<{ success: boolean; watchlist: Watchlist }> {
  const params = userId ? `?user_id=${userId}` : '';
  return fetchApi(`/api/wealth/watchlist${params}`, {
    method: 'POST',
    body: JSON.stringify(watchlist),
  });
}

export async function getWatchlists(
  userId?: string
): Promise<Watchlist[]> {
  const params = userId ? `?user_id=${userId}` : '';
  return fetchApi<Watchlist[]>(`/api/wealth/watchlist${params}`);
}

export async function deleteWatchlist(
  watchlistId: string
): Promise<{ success: boolean }> {
  return fetchApi(`/api/wealth/watchlist/${watchlistId}`, {
    method: 'DELETE',
  });
}

export async function getWatchlistMatches(
  watchlistId: string
): Promise<{ watchlist: Watchlist; matches: Opportunity[]; match_count: number }> {
  return fetchApi(`/api/wealth/watchlist/${watchlistId}/matches`);
}

// =============================================================================
// Live Data API (Real-time sources)
// =============================================================================

export interface LiveNewsItem {
  id: string;
  title: string;
  summary: string;
  content?: string;
  source: string;
  source_url?: string;
  published_at: string;
  category: string;
  impact_level: string;
  impact_type: string;
  countries_affected: string[];
  keywords: string[];
  author?: string;
  image_url?: string;
}

export interface MarketStats {
  country: string;
  city?: string;
  avg_price_per_m2: number;
  price_trend_yoy: number;
  avg_rent_per_m2: number;
  rent_trend_yoy: number;
  avg_yield: number;
  vacancy_rate: number;
  days_on_market_avg: number;
  transaction_volume_trend: string;
  source: string;
  fetched_at: string;
}

/**
 * Get live news from real RSS feeds and NewsAPI
 */
export async function getLiveNews(options: {
  countries?: string[];
  categories?: string[];
  limit?: number;
} = {}): Promise<{ items: LiveNewsItem[]; total: number; sources: string[]; live: boolean }> {
  const params = new URLSearchParams();
  if (options.countries?.length) params.set('countries', options.countries.join(','));
  if (options.categories?.length) params.set('categories', options.categories.join(','));
  if (options.limit) params.set('limit', options.limit.toString());
  
  return fetchApi(`/api/wealth/live/news?${params.toString()}`);
}

/**
 * Get live market statistics from official sources
 */
export async function getLiveMarketStats(
  country: string,
  city?: string
): Promise<MarketStats> {
  const params = city ? `?city=${encodeURIComponent(city)}` : '';
  return fetchApi<MarketStats>(`/api/wealth/live/market-stats?country=${country}${params}`);
}

/**
 * Get list of cities with market data
 */
export async function getAvailableCities(country: string): Promise<{ country: string; cities: string[] }> {
  return fetchApi(`/api/wealth/live/market-stats/cities?country=${country}`);
}

/**
 * Get list of countries with market data
 */
export async function getAvailableCountries(): Promise<{ countries: string[] }> {
  return fetchApi('/api/wealth/live/market-stats/countries');
}

/**
 * Get documentation of data sources
 */
export async function getDataSources(): Promise<{
  central_bank_rates: { description: string; sources: Array<{ name: string; url: string; coverage: string[] }> };
  real_estate_news: { description: string; sources: Array<{ name: string; type: string; coverage: string[] }> };
  market_statistics: { description: string; sources: Array<{ name: string; coverage: string[] }> };
  visual_analysis: { description: string; sources: Array<{ name: string; type: string }> };
}> {
  return fetchApi('/api/wealth/data-sources');
}

// =============================================================================
// Formatters
// =============================================================================

export function formatCurrency(
  amount: number,
  currency: string = 'EUR',
  locale: string = 'fr-FR'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPercent(
  value: number,
  decimals: number = 1
): string {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

export function formatArea(
  m2: number,
  unit: 'metric' | 'imperial' = 'metric'
): string {
  if (unit === 'imperial') {
    const sqft = m2 * 10.764;
    return `${Math.round(sqft).toLocaleString()} sq ft`;
  }
  return `${m2.toLocaleString()} m²`;
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 65) return 'text-green-400';
  if (score >= 50) return 'text-yellow-400';
  if (score >= 35) return 'text-orange-400';
  return 'text-red-400';
}

export function getSignalIcon(signalType: string): string {
  const icons: Record<string, string> = {
    price_drop: '📉',
    reactivated: '🔄',
    long_listing: '⏳',
    yield_anomaly: '💰',
    underpriced: '🎯',
    zone_acceleration: '🚀',
  };
  return icons[signalType] || '📌';
}

export function getSignalLabel(signalType: string): string {
  const labels: Record<string, string> = {
    price_drop: 'Baisse de prix',
    reactivated: 'Annonce réactivée',
    long_listing: 'Longue durée',
    yield_anomaly: 'Yield anormal',
    underpriced: 'Sous-coté',
    zone_acceleration: 'Zone dynamique',
  };
  return labels[signalType] || signalType;
}

export function getPriorityColor(priority: string): string {
  const colors: Record<string, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };
  return colors[priority] || 'bg-gray-500';
}

export function getImpactColor(level: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-400',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    low: 'text-green-400',
    info: 'text-blue-400',
  };
  return colors[level] || 'text-gray-400';
}

export function getConditionLabel(condition: string): string {
  const labels: Record<string, string> = {
    excellent: 'Excellent',
    good: 'Bon',
    fair: 'Correct',
    poor: 'Mauvais',
    to_renovate: 'À rénover',
  };
  return labels[condition] || condition;
}

export function getEnergyRatingColor(rating: string): string {
  const colors: Record<string, string> = {
    A: 'bg-green-500',
    B: 'bg-lime-500',
    C: 'bg-yellow-500',
    D: 'bg-orange-400',
    E: 'bg-orange-500',
    F: 'bg-red-400',
    G: 'bg-red-600',
  };
  return colors[rating?.toUpperCase()] || 'bg-gray-500';
}

export function formatTimeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const hours = Math.floor(diff / 3600000);
  
  if (hours < 1) return 'À l\'instant';
  if (hours < 24) return `Il y a ${hours}h`;
  
  const days = Math.floor(hours / 24);
  if (days < 7) return `Il y a ${days}j`;
  
  const weeks = Math.floor(days / 7);
  return `Il y a ${weeks} sem.`;
}
