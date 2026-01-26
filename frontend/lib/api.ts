// ═══════════════════════════════════════════════════════════════════════════
// MARKETGPS - API Client
// This file wraps all API calls. Adapt endpoints to your backend.
// ═══════════════════════════════════════════════════════════════════════════

import { getApiBaseUrl } from './config';
import type {
  Asset,
  AssetDetail,
  TopScoredParams,
  SearchParams,
  ChartData,
  ChartPeriod,
  WatchlistItem,
  ScopeCounts,
  LandingMetrics,
  Subscription,
  PaginatedResponse,
} from '@/types';

// ─────────────────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE_URL = getApiBaseUrl();

// ─────────────────────────────────────────────────────────────────────────────
// Base Fetch Helper
// ─────────────────────────────────────────────────────────────────────────────

interface FetchOptions extends RequestInit {
  token?: string;
}

async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { token, ...fetchOptions } = options;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API Error: ${response.status}`);
  }
  
  return response.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Assets API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Get top scored assets
 * @endpoint GET /api/assets/top-scored
 */
export async function getTopScored(
  params: TopScoredParams = {},
  token?: string
): Promise<PaginatedResponse<Asset>> {
  const searchParams = new URLSearchParams();
  
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());
  if (params.market_scope) searchParams.append('market_scope', params.market_scope);
  if (params.asset_type) searchParams.append('asset_type', params.asset_type);
  if (params.market_filter) searchParams.append('market_filter', params.market_filter);
  
  const query = searchParams.toString();
  const endpoint = `/api/assets/top-scored${query ? `?${query}` : ''}`;
  
  return apiFetch<PaginatedResponse<Asset>>(endpoint, { token });
}

/**
 * Parameters for institutional ranking endpoint
 */
export interface TopScoredInstitutionalParams {
  limit?: number;
  offset?: number;
  market_scope?: 'US_EU' | 'AFRICA';
  asset_type?: string | null;
  min_liquidity_tier?: 'A' | 'B' | 'C' | null;
  exclude_flagged?: boolean;
  min_horizon_years?: number | null;
}

/**
 * Get top scored assets ranked by score_institutional (ADD-ON v2.0)
 * @endpoint GET /api/assets/top-scored-institutional
 */
export async function getTopScoredInstitutional(
  params: TopScoredInstitutionalParams = {},
  token?: string
): Promise<PaginatedResponse<Asset> & { ranking_mode: 'institutional'; filters_applied: Record<string, any> }> {
  const searchParams = new URLSearchParams();
  
  if (params.limit) searchParams.append('limit', params.limit.toString());
  if (params.offset) searchParams.append('offset', params.offset.toString());
  if (params.market_scope) searchParams.append('market_scope', params.market_scope);
  if (params.asset_type) searchParams.append('asset_type', params.asset_type);
  if (params.min_liquidity_tier) searchParams.append('min_liquidity_tier', params.min_liquidity_tier);
  if (params.exclude_flagged) searchParams.append('exclude_flagged', 'true');
  if (params.min_horizon_years) searchParams.append('min_horizon_years', params.min_horizon_years.toString());
  
  const query = searchParams.toString();
  const endpoint = `/api/assets/top-scored-institutional${query ? `?${query}` : ''}`;
  
  return apiFetch(endpoint, { token });
}

/**
 * Search assets
 * @endpoint GET /api/assets/search
 */
export async function searchAssets(
  params: SearchParams,
  token?: string
): Promise<Asset[]> {
  const searchParams = new URLSearchParams();
  searchParams.append('q', params.q);
  
  if (params.market_scope) searchParams.append('market_scope', params.market_scope);
  if (params.limit) searchParams.append('limit', params.limit.toString());
  
  const endpoint = `/api/assets/search?${searchParams.toString()}`;
  
  return apiFetch<Asset[]>(endpoint, { token });
}

/**
 * Get asset details
 * @endpoint GET /api/assets/{ticker}
 */
export async function getAssetDetails(
  ticker: string,
  token?: string
): Promise<AssetDetail> {
  return apiFetch<AssetDetail>(`/api/assets/${ticker}`, { token });
}

/**
 * Get asset chart data
 * @endpoint GET /api/assets/{ticker}/chart
 */
export async function getAssetChart(
  ticker: string,
  period: ChartPeriod = '30d',
  token?: string
): Promise<ChartData> {
  return apiFetch<ChartData>(`/api/assets/${ticker}/chart?period=${period}`, { token });
}

// ─────────────────────────────────────────────────────────────────────────────
// Watchlist API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Get user's watchlist
 * @endpoint GET /api/watchlist
 */
export async function getWatchlist(
  userId: string = 'default',
  marketScope?: string
): Promise<WatchlistItem[]> {
  const params = new URLSearchParams();
  params.append('user_id', userId);
  if (marketScope) params.append('market_scope', marketScope);
  return apiFetch<WatchlistItem[]>(`/api/watchlist?${params.toString()}`);
}

/**
 * Add asset to watchlist
 * @endpoint POST /api/watchlist
 */
export async function addToWatchlist(
  ticker: string,
  userId: string = 'default',
  marketScope: string = 'US_EU',
  notes?: string
): Promise<{ status: string; ticker: string }> {
  const params = new URLSearchParams();
  params.append('user_id', userId);
  return apiFetch(`/api/watchlist?${params.toString()}`, {
    method: 'POST',
    body: JSON.stringify({
      ticker,
      market_scope: marketScope,
      notes,
    }),
  });
}

/**
 * Remove asset from watchlist
 * @endpoint DELETE /api/watchlist/{ticker}
 */
export async function removeFromWatchlist(
  ticker: string,
  userId: string = 'default'
): Promise<{ status: string; ticker: string }> {
  const params = new URLSearchParams();
  params.append('user_id', userId);
  return apiFetch(`/api/watchlist/${ticker}?${params.toString()}`, {
    method: 'DELETE',
  });
}

/**
 * Check if asset is in watchlist
 * @endpoint GET /api/watchlist/check/{ticker}
 */
export async function checkInWatchlist(
  ticker: string,
  userId: string = 'default'
): Promise<{ in_watchlist: boolean }> {
  const params = new URLSearchParams();
  params.append('user_id', userId);
  return apiFetch(`/api/watchlist/check/${ticker}?${params.toString()}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Metrics API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Get scope counts
 * @endpoint GET /api/metrics/counts
 */
export async function getScopeCounts(): Promise<ScopeCounts> {
  return apiFetch<ScopeCounts>('/api/metrics/counts');
}

/**
 * Asset type count response
 */
export interface AssetTypeCount {
  count: number;
  avgScore: number;
}

/**
 * Get asset counts by type (includes unscored assets)
 * @endpoint GET /api/metrics/asset-type-counts
 */
export async function getAssetTypeCounts(
  marketScope?: string
): Promise<Record<string, AssetTypeCount>> {
  const params = new URLSearchParams();
  if (marketScope) params.append('market_scope', marketScope);
  const query = params.toString();
  return apiFetch<Record<string, AssetTypeCount>>(
    `/api/metrics/asset-type-counts${query ? `?${query}` : ''}`
  );
}

/**
 * Get landing page metrics
 * @endpoint GET /api/metrics/landing
 */
export async function getLandingMetrics(): Promise<LandingMetrics> {
  return apiFetch<LandingMetrics>('/api/metrics/landing');
}

/**
 * Dynamic counts v2 response (PR4)
 */
export interface CountsV2Response {
  total: number;
  breakdown: {
    scored: number;
    unscored: number;
  };
  filters: {
    market_scope: string | null;
    asset_type: string | null;
    country: string | null;
    region: string | null;
    only_scored: boolean | null;
  };
  by_scope?: Record<string, { total: number; scored: number }>;
  by_asset_type?: Record<string, { total: number; scored: number; avgScore: number | null }>;
  by_region?: Record<string, { total: number; scored: number }>;
}

/**
 * Parameters for dynamic counts v2
 */
export interface CountsV2Params {
  market_scope?: 'US_EU' | 'AFRICA';
  asset_type?: string;
  country?: string;
  region?: string;
  only_scored?: boolean;
}

/**
 * Get dynamic asset counts with flexible filtering (PR4)
 * @endpoint GET /api/metrics/counts/v2
 */
export async function getCountsV2(params: CountsV2Params = {}): Promise<CountsV2Response> {
  const searchParams = new URLSearchParams();

  if (params.market_scope) searchParams.append('market_scope', params.market_scope);
  if (params.asset_type) searchParams.append('asset_type', params.asset_type);
  if (params.country) searchParams.append('country', params.country);
  if (params.region) searchParams.append('region', params.region);
  if (params.only_scored !== undefined) searchParams.append('only_scored', String(params.only_scored));

  const query = searchParams.toString();
  return apiFetch<CountsV2Response>(`/api/metrics/counts/v2${query ? `?${query}` : ''}`);
}

// ─────────────────────────────────────────────────────────────────────────────
// Billing API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Create Stripe checkout session
 * @endpoint POST /api/billing/checkout-session
 */
export async function createCheckoutSession(
  plan: 'monthly' | 'yearly',
  token: string
): Promise<{ checkout_url: string }> {
  const successUrl = `${window.location.origin}/settings/billing?success=1`;
  const cancelUrl = `${window.location.origin}/settings/billing?canceled=1`;
  
  return apiFetch('/api/billing/checkout-session', {
    method: 'POST',
    body: JSON.stringify({
      plan,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
    token,
  });
}

/**
 * Get current subscription (legacy endpoint)
 * @endpoint GET /api/billing/subscription
 */
export async function getSubscription(token: string): Promise<Subscription> {
  return apiFetch<Subscription>('/api/billing/subscription', { token });
}

/**
 * Subscription status response (v13)
 */
export interface SubscriptionStatus {
  user_id: string;
  plan: 'free' | 'monthly' | 'annual';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'inactive';
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_active: boolean;
  grace_period_remaining_hours: number | null;
}

/**
 * Get my subscription status (v13)
 * @endpoint GET /api/billing/me
 */
export async function getMySubscription(token: string): Promise<SubscriptionStatus> {
  return apiFetch<SubscriptionStatus>('/api/billing/me', { token });
}

/**
 * Create Stripe portal session
 * @endpoint POST /api/billing/portal-session
 */
export async function createPortalSession(token: string): Promise<{ url: string }> {
  return apiFetch<{ url: string }>('/api/billing/portal-session', {
    method: 'POST',
    token,
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Export all functions
// ─────────────────────────────────────────────────────────────────────────────

export const api = {
  // Assets
  getTopScored,
  searchAssets,
  getAssetDetails,
  getAssetChart,
  // Watchlist
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  checkInWatchlist,
  // Metrics
  getScopeCounts,
  getAssetTypeCounts,
  getLandingMetrics,
  getCountsV2,
  // Billing
  createCheckoutSession,
  getSubscription,
  getMySubscription,
  createPortalSession,
};

export default api;

// ─────────────────────────────────────────────────────────────────────────────
// On-Demand Scoring API (NEW - Hybrid Architecture)
// ─────────────────────────────────────────────────────────────────────────────

export interface OnDemandScoreResult {
  asset_id: string;
  symbol: string;
  name: string;
  asset_type: string;
  market_scope: string;
  score_total: number | null;
  score_value: number | null;
  score_momentum: number | null;
  score_safety: number | null;
  confidence: number | null;
  rsi: number | null;
  zscore: number | null;
  vol_annual: number | null;
  max_drawdown: number | null;
  last_price: number | null;
  state_label: string | null;
  updated_at: string;
  from_cache: boolean;
  quota_used: boolean;
  quota_remaining?: number;
}

export interface QuotaStatus {
  plan: string;
  daily_used: number;
  daily_limit: number;
  remaining: number;
  is_pro: boolean;
  is_annual: boolean;
  can_score: boolean;
}

export interface UniverseMetrics {
  total_assets: number;
  scored_assets: number;
  tier1_assets: number;
  markets_covered: number;
  exchanges_covered: number;
  by_scope: Record<string, number>;
  by_type: Record<string, number>;
  scoring_coverage: number;
}

/**
 * Calculate score for an asset on-demand
 * @endpoint POST /api/assets/{ticker}/score
 */
export async function calculateScoreOnDemand(
  ticker: string,
  force: boolean = false,
  token?: string
): Promise<OnDemandScoreResult> {
  const params = new URLSearchParams();
  if (force) params.append('force', 'true');
  
  const query = params.toString();
  const endpoint = `/api/assets/${ticker}/score${query ? `?${query}` : ''}`;
  
  return apiFetch<OnDemandScoreResult>(endpoint, {
    method: 'POST',
    token,
  });
}

/**
 * Get current user quota status
 * @endpoint GET /api/user/quota
 */
export async function getUserQuota(token?: string): Promise<QuotaStatus> {
  return apiFetch<QuotaStatus>('/api/user/quota', { token });
}

/**
 * Get comprehensive universe metrics
 * @endpoint GET /api/metrics/universe
 */
export async function getUniverseMetrics(): Promise<UniverseMetrics> {
  return apiFetch<UniverseMetrics>('/api/metrics/universe');
}

// Update the api object with new functions
Object.assign(api, {
  calculateScoreOnDemand,
  getUserQuota,
  getUniverseMetrics,
});
