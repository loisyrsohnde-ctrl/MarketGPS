/**
 * MarketGPS Mobile - API Client
 * Typed API client for all backend endpoints
 */

import { Config } from './config';
import { getAccessToken } from './supabase';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface Asset {
  asset_id: string;
  symbol: string;
  name: string;
  asset_type: string;
  market_scope: string;
  exchange?: string;
  country?: string;
  score_total: number | null;
  score_value?: number | null;
  score_momentum?: number | null;
  score_safety?: number | null;
  last_price?: number | null;
  pct_change_1d?: number | null;
  vol_annual?: number | null;
  rsi?: number | null;
  state_label?: string | null;
  updated_at?: string;
}

export interface AssetDetail extends Asset {
  pe_ratio?: number | null;
  dividend_yield?: number | null;
  market_cap?: number | null;
  max_drawdown?: number | null;
  sharpe_ratio?: number | null;
  zscore?: number | null;
  confidence?: number | null;
  liquidity_tier?: string | null;
  horizon_years?: number | null;
  score_institutional?: number | null;
}

export interface ChartDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistItem {
  ticker: string;
  added_at: string;
  notes?: string;
  asset?: Asset;
}

export interface NewsArticle {
  id: number;
  slug: string;
  title: string;
  excerpt?: string;
  content_md?: string;
  tldr?: string[];
  tags?: string[];
  country?: string;
  image_url?: string;
  source_name: string;
  source_url?: string;
  published_at?: string;
  category?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  // Scoring fields
  engagement_score?: number;
  is_breaking_news?: boolean;
  importance_level?: 'high' | 'medium' | 'low';
  // Saved status
  is_saved?: boolean;
}

export interface BreakingNewsResponse {
  data: NewsArticle[];
  count: number;
  has_breaking: boolean;
}

export interface AppNotification {
  id: string;
  type: 'score_drop' | 'score_surge' | 'rebalance' | 'news_impact' | 'morning_brief' | 'opportunity' | 'alert' | 'system' | 'breaking_news';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  dismissed: boolean;
  data?: {
    article_id?: number;
    slug?: string;
    source?: string;
    country?: string;
    category?: string;
    ticker?: string;
  };
  actions?: Array<{
    label: string;
    action: string;
    primary?: boolean;
  }>;
}

export interface StrategyTemplate {
  id: number;
  slug: string;
  name: string;
  description: string;
  category: string;
  risk_level: string;
  horizon_years: number;
  rebalance_frequency: string;
  structure: {
    blocks: Array<{
      name: string;
      label: string;
      weight: number;
      description: string;
    }>;
  };
}

export interface SubscriptionStatus {
  user_id: string;
  plan: 'free' | 'monthly' | 'annual';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'inactive';
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  is_active: boolean;
  grace_period_remaining_hours: number | null;
}

export interface BarbellPortfolio {
  id: string;
  name: string;
  risk_profile: string;
  market_scope: string;
  core_assets: Array<{ ticker: string; weight: number; asset?: Asset }>;
  satellite_assets: Array<{ ticker: string; weight: number; asset?: Asset }>;
  created_at: string;
  updated_at?: string;
}

export interface UserStrategy {
  id: string;
  name: string;
  description?: string;
  template_slug?: string;
  blocks: Array<{ name: string; label: string; weight: number; description?: string }>;
  risk_level?: string;
  horizon_years?: number;
  created_at: string;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page?: number;
  page_size?: number;
  limit?: number;
  offset?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Portfolio Types
// ═══════════════════════════════════════════════════════════════════════════

export interface PortfolioAccount {
  id: string;
  name: string;
  broker?: string;
  account_type: 'brokerage' | 'ira' | 'roth_ira' | '401k' | 'pea' | 'cto' | 'other';
  currency: string;
  is_default: boolean;
  created_at: string;
  updated_at?: string;
}

export interface PortfolioPosition {
  id: string;
  account_id: string;
  ticker: string;
  quantity: number;
  avg_cost: number;
  current_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
  asset?: Asset;
  created_at: string;
  updated_at?: string;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_pct: number;
  currency: string;
  accounts_count: number;
  positions_count: number;
  top_holdings: Array<{
    ticker: string;
    name: string;
    weight: number;
    pnl_pct: number;
  }>;
  allocation_by_type: Record<string, number>;
  last_updated: string;
}

export interface PortfolioTransaction {
  id: string;
  account_id: string;
  ticker: string;
  type: 'buy' | 'sell' | 'dividend' | 'deposit' | 'withdrawal';
  quantity: number;
  price: number;
  total_amount: number;
  fees?: number;
  notes?: string;
  transaction_date: string;
  created_at: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════════════════════

interface FetchOptions extends RequestInit {
  token?: string | null;
  timeout?: number;
}

class APIClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = Config.API_URL) {
    this.baseUrl = baseUrl;
  }
  
  private async fetch<T>(
    endpoint: string,
    options: FetchOptions = {}
  ): Promise<T> {
    const { token, timeout = 15000, ...fetchOptions } = options;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    };
    
    // Add auth token if available
    const authToken = token ?? await getAccessToken();
    if (authToken) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${authToken}`;
    }
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new APIError(
          error.detail || error.message || `API Error: ${response.status}`,
          response.status,
          error
        );
      }
      
      return response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof APIError) throw error;
      
      if ((error as Error).name === 'AbortError') {
        throw new APIError('Request timeout', 408);
      }
      
      throw new APIError((error as Error).message || 'Network error', 0);
    }
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Assets
  // ─────────────────────────────────────────────────────────────────────────
  
  async getTopScored(params: {
    limit?: number;
    offset?: number;
    market_scope?: string;
    asset_type?: string;
  } = {}): Promise<PaginatedResponse<Asset>> {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.offset) searchParams.append('offset', params.offset.toString());
    if (params.market_scope) searchParams.append('market_scope', params.market_scope);
    if (params.asset_type) searchParams.append('asset_type', params.asset_type);
    
    const query = searchParams.toString();
    return this.fetch(`/api/assets/top-scored${query ? `?${query}` : ''}`);
  }
  
  async searchAssets(q: string, market_scope?: string, limit = 20): Promise<Asset[]> {
    const params = new URLSearchParams({ q, limit: limit.toString() });
    if (market_scope) params.append('market_scope', market_scope);
    return this.fetch(`/api/assets/search?${params.toString()}`);
  }
  
  async getAssetDetails(ticker: string): Promise<AssetDetail> {
    return this.fetch(`/api/assets/${encodeURIComponent(ticker)}`);
  }
  
  async getAssetChart(ticker: string, period = '30d'): Promise<ChartDataPoint[]> {
    return this.fetch(`/api/assets/${encodeURIComponent(ticker)}/chart?period=${period}`);
  }
  
  async getExplorer(params: {
    market_scope?: string;
    asset_type?: string;
    country?: string;
    region?: string;
    query?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_desc?: boolean;
  } = {}): Promise<PaginatedResponse<Asset>> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, String(value));
    });
    const query = searchParams.toString();
    return this.fetch(`/api/assets/explorer${query ? `?${query}` : ''}`);
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Watchlist
  // ─────────────────────────────────────────────────────────────────────────
  
  async getWatchlist(market_scope?: string): Promise<WatchlistItem[]> {
    const params = new URLSearchParams();
    if (market_scope) params.append('market_scope', market_scope);
    const query = params.toString();
    return this.fetch(`/api/watchlist${query ? `?${query}` : ''}`);
  }
  
  async addToWatchlist(ticker: string, market_scope = 'US_EU'): Promise<{ status: string }> {
    return this.fetch('/api/watchlist', {
      method: 'POST',
      body: JSON.stringify({ ticker, market_scope }),
    });
  }
  
  async removeFromWatchlist(ticker: string): Promise<{ status: string }> {
    return this.fetch(`/api/watchlist/${encodeURIComponent(ticker)}`, {
      method: 'DELETE',
    });
  }
  
  async checkInWatchlist(ticker: string): Promise<{ in_watchlist: boolean }> {
    return this.fetch(`/api/watchlist/check/${encodeURIComponent(ticker)}`);
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Metrics
  // ─────────────────────────────────────────────────────────────────────────
  
  async getScopeCounts(): Promise<{ US_EU: number; AFRICA: number }> {
    return this.fetch('/api/metrics/counts');
  }
  
  async getMetricsLanding(market_scope = 'US_EU'): Promise<Record<string, any>> {
    return this.fetch(`/api/metrics/landing?market_scope=${market_scope}`);
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // News
  // ─────────────────────────────────────────────────────────────────────────
  
  async getNewsFeed(params: {
    page?: number;
    page_size?: number;
    country?: string;
    tag?: string;
  } = {}): Promise<PaginatedResponse<NewsArticle>> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params.country) searchParams.append('country', params.country);
    if (params.tag) searchParams.append('tag', params.tag);
    
    const query = searchParams.toString();
    return this.fetch(`/api/news${query ? `?${query}` : ''}`);
  }
  
  async getNewsArticle(slug: string): Promise<NewsArticle> {
    return this.fetch(`/api/news/${slug}`);
  }

  async getNewsRegions(): Promise<{ regions: Array<{ id: string; name: string; count: number }> }> {
    return this.fetch('/api/news/regions');
  }

  async getBreakingNews(params: {
    limit?: number;
    max_age_hours?: number;
  } = {}): Promise<BreakingNewsResponse> {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.max_age_hours) searchParams.append('max_age_hours', params.max_age_hours.toString());
    const query = searchParams.toString();
    return this.fetch(`/api/news/breaking${query ? `?${query}` : ''}`);
  }

  async getImportantNews(limit = 10): Promise<PaginatedResponse<NewsArticle>> {
    return this.fetch(`/api/news/important?limit=${limit}`);
  }

  async getSavedArticles(params: {
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<NewsArticle>> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.page_size) searchParams.append('page_size', params.page_size.toString());
    const query = searchParams.toString();
    return this.fetch(`/api/news/saved${query ? `?${query}` : ''}`);
  }

  async saveArticle(articleId: number): Promise<{ status: string }> {
    return this.fetch(`/api/news/${articleId}/save`, {
      method: 'POST',
    });
  }

  async unsaveArticle(articleId: number): Promise<{ status: string }> {
    return this.fetch(`/api/news/${articleId}/save`, {
      method: 'DELETE',
    });
  }

  async checkArticleSaved(articleId: number): Promise<{ is_saved: boolean }> {
    return this.fetch(`/api/news/check/${articleId}/saved`);
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Strategies
  // ─────────────────────────────────────────────────────────────────────────
  
  async getStrategyTemplates(): Promise<StrategyTemplate[]> {
    return this.fetch('/api/strategies/templates');
  }
  
  async getStrategyTemplate(slug: string): Promise<StrategyTemplate> {
    return this.fetch(`/api/strategies/templates/${slug}`);
  }
  
  async getEligibleInstruments(block_type: string, limit = 50): Promise<Asset[]> {
    return this.fetch(`/api/strategies/eligible-instruments?block_type=${block_type}&limit=${limit}`);
  }
  
  async simulateStrategy(params: {
    compositions: Array<{ ticker: string; weight: number; block_name: string }>;
    period_years?: number;
    initial_value?: number;
  }): Promise<Record<string, any>> {
    return this.fetch('/api/strategies/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // User Strategies CRUD
  async getUserStrategies(): Promise<UserStrategy[]> {
    return this.fetch('/api/strategies/user');
  }

  async createUserStrategy(data: {
    name: string;
    description?: string;
    template_slug?: string;
    blocks: Array<{ name: string; label: string; weight: number }>;
    risk_level?: string;
    horizon_years?: number;
  }): Promise<UserStrategy> {
    return this.fetch('/api/strategies/user', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateUserStrategy(strategyId: string, data: {
    name?: string;
    description?: string;
    blocks?: Array<{ name: string; label: string; weight: number }>;
  }): Promise<UserStrategy> {
    return this.fetch(`/api/strategies/user/${strategyId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteUserStrategy(strategyId: string): Promise<{ status: string }> {
    return this.fetch(`/api/strategies/user/${strategyId}`, {
      method: 'DELETE',
    });
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Barbell
  // ─────────────────────────────────────────────────────────────────────────
  
  async getBarbellSuggestion(params: {
    risk_profile?: string;
    market_scope?: string;
    core_count?: number;
    satellite_count?: number;
  } = {}): Promise<Record<string, any>> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, String(value));
    });
    const query = searchParams.toString();
    return this.fetch(`/api/barbell/suggest${query ? `?${query}` : ''}`);
  }
  
  async getCoreCandidates(limit = 50, market_scope = 'US_EU'): Promise<PaginatedResponse<Asset>> {
    return this.fetch(`/api/barbell/candidates/core?limit=${limit}&market_scope=${market_scope}`);
  }
  
  async getSatelliteCandidates(limit = 50, market_scope = 'US_EU'): Promise<PaginatedResponse<Asset>> {
    return this.fetch(`/api/barbell/candidates/satellite?limit=${limit}&market_scope=${market_scope}`);
  }

  // Saved Barbell Portfolios
  async getSavedBarbellPortfolios(): Promise<BarbellPortfolio[]> {
    return this.fetch('/api/barbell/portfolios');
  }

  async saveBarbellPortfolio(data: {
    name: string;
    risk_profile: string;
    market_scope: string;
    core_assets: Array<{ ticker: string; weight: number }>;
    satellite_assets: Array<{ ticker: string; weight: number }>;
  }): Promise<BarbellPortfolio> {
    return this.fetch('/api/barbell/portfolios', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateBarbellPortfolio(portfolioId: string, data: {
    name?: string;
    core_assets?: Array<{ ticker: string; weight: number }>;
    satellite_assets?: Array<{ ticker: string; weight: number }>;
  }): Promise<BarbellPortfolio> {
    return this.fetch(`/api/barbell/portfolios/${portfolioId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteBarbellPortfolio(portfolioId: string): Promise<{ status: string }> {
    return this.fetch(`/api/barbell/portfolios/${portfolioId}`, {
      method: 'DELETE',
    });
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Billing
  // ─────────────────────────────────────────────────────────────────────────
  
  async getSubscriptionStatus(): Promise<SubscriptionStatus> {
    // Use the same endpoint as web frontend (/users/entitlements)
    // and adapt the response to mobile's expected format
    try {
      const data = await this.fetch<{
        plan: string;
        status: string;
        dailyRequestsLimit?: number;
        current_period_end?: string | null;
      }>('/users/entitlements');
      
      // Map plan values to expected format
      const planMap: Record<string, 'free' | 'monthly' | 'annual'> = {
        'FREE': 'free',
        'MONTHLY': 'monthly',
        'YEARLY': 'annual',
        'ANNUAL': 'annual',
        'free': 'free',
        'monthly': 'monthly',
        'annual': 'annual',
        'yearly': 'annual',
      };
      
      const plan = planMap[data.plan] || 'free';
      const isActive = data.status === 'active' && plan !== 'free';
      
      return {
        user_id: '', // Will be filled by auth store if needed
        plan,
        status: (data.status as SubscriptionStatus['status']) || 'inactive',
        current_period_end: data.current_period_end || null,
        cancel_at_period_end: false,
        is_active: isActive,
        grace_period_remaining_hours: null,
      };
    } catch (error) {
      // Return default free plan on error
      console.warn('Failed to fetch subscription status, defaulting to free:', error);
      return {
        user_id: '',
        plan: 'free',
        status: 'active',
        current_period_end: null,
        cancel_at_period_end: false,
        is_active: false,
        grace_period_remaining_hours: null,
      };
    }
  }
  
  async createCheckoutSession(plan: 'monthly' | 'annual'): Promise<{ url: string }> {
    return this.fetch('/api/billing/checkout-session', {
      method: 'POST',
      body: JSON.stringify({ plan }),
    });
  }
  
  async createPortalSession(): Promise<{ url: string }> {
    return this.fetch('/api/billing/portal-session', {
      method: 'POST',
    });
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // User
  // ─────────────────────────────────────────────────────────────────────────
  
  async getUserProfile(): Promise<Record<string, any>> {
    return this.fetch('/users/profile');
  }
  
  async updateUserProfile(data: { displayName?: string }): Promise<Record<string, any>> {
    return this.fetch('/users/profile/update', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  async getNotificationSettings(): Promise<Record<string, any>> {
    return this.fetch('/users/notifications');
  }
  
  async updateNotificationSettings(settings: Record<string, boolean>): Promise<Record<string, any>> {
    return this.fetch('/users/notifications/update', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }
  
  async getUnreadNotificationsCount(): Promise<{ count: number }> {
    return this.fetch('/users/notifications/unread-count');
  }

  // ─────────────────────────────────────────────────────────────────────────
  // App Notifications (includes breaking news)
  // ─────────────────────────────────────────────────────────────────────────

  async getAppNotifications(params: {
    limit?: number;
    unread_only?: boolean;
  } = {}): Promise<{
    success: boolean;
    notifications: AppNotification[];
    total: number;
    unread_count: number;
  }> {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.unread_only) searchParams.append('unread_only', 'true');
    const query = searchParams.toString();
    return this.fetch(`/api/notifications${query ? `?${query}` : ''}`);
  }

  async markNotificationRead(notificationIds: string[]): Promise<{ success: boolean }> {
    return this.fetch('/api/notifications/read', {
      method: 'POST',
      body: JSON.stringify(notificationIds),
    });
  }

  async dismissNotification(notificationIds: string[]): Promise<{ success: boolean }> {
    return this.fetch('/api/notifications/dismiss', {
      method: 'POST',
      body: JSON.stringify(notificationIds),
    });
  }

  // ─────────────────────────────────────────────────────────────────────────
  // Portfolio
  // ─────────────────────────────────────────────────────────────────────────

  async getPortfolioSummary(): Promise<PortfolioSummary> {
    return this.fetch('/api/portfolio/summary');
  }

  // Accounts
  async getPortfolioAccounts(): Promise<PortfolioAccount[]> {
    return this.fetch('/api/portfolio/accounts');
  }

  async createPortfolioAccount(data: {
    name: string;
    broker?: string;
    account_type: string;
    currency?: string;
    is_default?: boolean;
  }): Promise<PortfolioAccount> {
    return this.fetch('/api/portfolio/accounts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePortfolioAccount(accountId: string, data: {
    name?: string;
    broker?: string;
    is_default?: boolean;
  }): Promise<PortfolioAccount> {
    return this.fetch(`/api/portfolio/accounts/${accountId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePortfolioAccount(accountId: string): Promise<{ status: string }> {
    return this.fetch(`/api/portfolio/accounts/${accountId}`, {
      method: 'DELETE',
    });
  }

  // Positions
  async getPortfolioPositions(accountId?: string): Promise<PortfolioPosition[]> {
    const params = accountId ? `?account_id=${accountId}` : '';
    return this.fetch(`/api/portfolio/positions${params}`);
  }

  async addPortfolioPosition(data: {
    account_id: string;
    ticker: string;
    quantity: number;
    avg_cost: number;
  }): Promise<PortfolioPosition> {
    return this.fetch('/api/portfolio/positions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updatePortfolioPosition(positionId: string, data: {
    quantity?: number;
    avg_cost?: number;
  }): Promise<PortfolioPosition> {
    return this.fetch(`/api/portfolio/positions/${positionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deletePortfolioPosition(positionId: string): Promise<{ status: string }> {
    return this.fetch(`/api/portfolio/positions/${positionId}`, {
      method: 'DELETE',
    });
  }

  // Transactions
  async getPortfolioTransactions(params: {
    account_id?: string;
    page?: number;
    page_size?: number;
  } = {}): Promise<PaginatedResponse<PortfolioTransaction>> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, String(value));
    });
    const query = searchParams.toString();
    return this.fetch(`/api/portfolio/transactions${query ? `?${query}` : ''}`);
  }

  async addPortfolioTransaction(data: {
    account_id: string;
    ticker: string;
    type: 'buy' | 'sell' | 'dividend';
    quantity: number;
    price: number;
    fees?: number;
    notes?: string;
    transaction_date: string;
  }): Promise<PortfolioTransaction> {
    return this.fetch('/api/portfolio/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Import
  async importPortfolioCSV(accountId: string, csvContent: string): Promise<{
    imported_count: number;
    errors: string[];
  }> {
    return this.fetch('/api/portfolio/import/csv', {
      method: 'POST',
      body: JSON.stringify({ account_id: accountId, csv_content: csvContent }),
    });
  }
}

// Custom error class
export class APIError extends Error {
  status: number;
  data?: any;
  
  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

// Export singleton instance
export const api = new APIClient();
export default api;
