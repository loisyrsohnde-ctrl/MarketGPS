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
 * Get current subscription
 * @endpoint GET /api/billing/subscription
 */
export async function getSubscription(token: string): Promise<Subscription> {
  return apiFetch<Subscription>('/api/billing/subscription', { token });
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
  // Billing
  createCheckoutSession,
  getSubscription,
};

export default api;
