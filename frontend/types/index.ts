// ═══════════════════════════════════════════════════════════════════════════
// MARKETGPS - Type Definitions
// ═══════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// Asset Types
// ─────────────────────────────────────────────────────────────────────────────

export type AssetType = 'ETF' | 'EQUITY' | 'FX' | 'BOND' | 'OPTION' | 'FUTURE' | 'CRYPTO' | 'COMMODITY' | 'INDEX' | 'FUND';
export type MarketScope = 'US_EU' | 'AFRICA';
export type MarketFilter = 'US' | 'EU' | 'AFRICA' | 'ALL';

export interface Asset {
  asset_id: string;
  ticker: string;
  symbol: string;
  name: string;
  asset_type: AssetType;
  market_scope: MarketScope;
  market_code: string;
  // Scores
  score_total: number | null;
  score_value: number | null;
  score_momentum: number | null;
  score_safety: number | null;
  score_fx_risk?: number | null;
  score_liquidity_risk?: number | null;
  // Data quality metrics
  coverage: number | null;
  liquidity: number | null;
  fx_risk: number | null;
  liquidity_risk?: number | null;
  confidence?: number | null;
  // Technical indicators
  rsi?: number | null;
  vol_annual?: number | null;
  max_drawdown?: number | null;
  sma200?: number | null;
  last_price?: number | null;
  zscore?: number | null;
  state_label?: string | null;
  // Metadata
  currency?: string | null;
  // Timestamps
  updated_at: string;
  // Institutional Guard fields (ADD-ON v2.0)
  score_institutional?: number | null;
  liquidity_tier?: 'A' | 'B' | 'C' | 'D' | null;
  liquidity_flag?: boolean | null;
  liquidity_penalty?: number | null;
  data_quality_flag?: boolean | null;
  data_quality_score?: number | null;
  stale_price_flag?: boolean | null;
  min_recommended_horizon_years?: number | null;
  institutional_explanation?: string | null;
  adv_usd?: number | null;
}

// Institutional ranking mode type
export type RankingMode = 'total' | 'institutional';

export interface AssetDetail extends Asset {
  description?: string;
  sector?: string;
  industry?: string;
  currency?: string;
  exchange?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Chart Types
// ─────────────────────────────────────────────────────────────────────────────

export type ChartPeriod = '1d' | '1w' | '7d' | '30d' | '3m' | '6m' | '1y' | '5y' | '10y';

export interface ChartDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface ChartData {
  data: ChartDataPoint[];
}

// ─────────────────────────────────────────────────────────────────────────────
// API Response Types
// ─────────────────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

export interface TopScoredParams {
  limit?: number;
  offset?: number;
  market_scope?: MarketScope;
  asset_type?: AssetType | null;
  market_filter?: MarketFilter;
}

export interface SearchParams {
  q: string;
  market_scope?: MarketScope;
  limit?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// User Types
// ─────────────────────────────────────────────────────────────────────────────

export type PlanType = 'free' | 'monthly' | 'yearly';
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due';

export interface User {
  id: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
  plan: PlanType;
  daily_quota_used: number;
  daily_quota_limit: number;
  created_at: string;
}

export interface Subscription {
  plan: PlanType;
  status: SubscriptionStatus;
  current_period_end?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Watchlist Types
// ─────────────────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  asset_id?: string;
  ticker: string;
  symbol?: string;
  name?: string;
  asset_type?: AssetType;
  market_scope?: MarketScope;
  market_code?: string;
  score_total?: number | null;
  score_value?: number | null;
  score_momentum?: number | null;
  score_safety?: number | null;
  coverage?: number | null;
  liquidity?: number | null;
  fx_risk?: number | null;
  notes?: string | null;
  added_at?: string;
  updated_at?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Metrics Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ScopeCounts {
  US_EU: number;
  AFRICA: number;
}

export interface LandingMetrics {
  total_assets: number;
  avg_score: number;
  top_performer: Asset | null;
}

// ─────────────────────────────────────────────────────────────────────────────
// Score Helpers
// ─────────────────────────────────────────────────────────────────────────────

export type ScoreLevel = 'low' | 'medium' | 'high' | 'excellent';

export interface ScoreConfig {
  color: string;
  bgColor: string;
  label: string;
  cssClass: string;
}

export const getScoreConfig = (score: number | null): ScoreConfig => {
  // Null or undefined = not scored yet
  if (score === null || score === undefined) {
    return {
      color: 'var(--text-muted)',
      bgColor: 'var(--surface)',
      label: 'Non scoré',
      cssClass: 'score-badge-neutral',
    };
  }

  // Score of exactly 0 usually means not calculated
  if (score === 0) {
    return {
      color: 'var(--text-muted)',
      bgColor: 'var(--surface)',
      label: 'À calculer',
      cssClass: 'score-badge-neutral',
    };
  }

  if (score <= 30) {
    return {
      color: 'var(--score-red)',
      bgColor: 'rgba(239, 68, 68, 0.15)',
      label: 'Faible',
      cssClass: 'score-badge-red',
    };
  }
  
  if (score <= 60) {
    return {
      color: 'var(--score-yellow)',
      bgColor: 'rgba(245, 158, 11, 0.15)',
      label: 'Stable',
      cssClass: 'score-badge-yellow',
    };
  }
  
  if (score <= 75) {
    return {
      color: 'var(--score-light-green)',
      bgColor: 'rgba(74, 222, 128, 0.15)',
      label: 'Élevée',
      cssClass: 'score-badge-light-green',
    };
  }
  
  return {
    color: 'var(--score-green)',
    bgColor: 'rgba(34, 197, 94, 0.15)',
    label: 'Dynamique',
    cssClass: 'score-badge-green',
  };
};

export const getScoreColor = (score: number | null): string => {
  if (score === null) return '#64748B';
  if (score <= 30) return '#EF4444';
  if (score <= 60) return '#F59E0B';
  if (score <= 75) return '#4ADE80';
  return '#22C55E';
};
