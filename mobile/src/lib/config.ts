/**
 * MarketGPS Mobile - Configuration
 */

export const Config = {
  // API
  API_URL: process.env.EXPO_PUBLIC_API_URL || 'https://api.marketgps.online',
  
  // Supabase
  SUPABASE_URL: process.env.EXPO_PUBLIC_SUPABASE_URL || '',
  SUPABASE_ANON_KEY: process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '',
  
  // Stripe
  STRIPE_PUBLISHABLE_KEY: process.env.EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY || '',
  
  // Web URLs
  WEB_URL: process.env.EXPO_PUBLIC_WEB_URL || 'https://app.marketgps.online',
  
  // App
  APP_SCHEME: 'marketgps',
  
  // Feature Flags
  ENABLE_OFFLINE_MODE: true,
  ENABLE_BIOMETRIC_AUTH: true,
  
  // Cache TTL (in ms)
  CACHE_TTL: {
    ASSETS: 5 * 60 * 1000,      // 5 minutes
    WATCHLIST: 2 * 60 * 1000,   // 2 minutes
    NEWS: 10 * 60 * 1000,       // 10 minutes
    STRATEGIES: 5 * 60 * 1000,  // 5 minutes
    USER: 1 * 60 * 1000,        // 1 minute
  },
} as const;

// Market Scopes
export const MARKET_SCOPES = {
  US_EU: 'US_EU',
  AFRICA: 'AFRICA',
} as const;

export type MarketScope = keyof typeof MARKET_SCOPES;

// Africa Regions
export const AFRICA_REGIONS = {
  NORTH: { name: 'Afrique du Nord', countries: ['MA', 'DZ', 'TN', 'EG', 'LY'] },
  WEST: { name: 'Afrique de l\'Ouest', countries: ['NG', 'GH', 'SN', 'CI', 'BF', 'ML', 'NE', 'TG', 'BJ'] },
  CENTRAL: { name: 'Afrique Centrale', countries: ['CM', 'GA', 'CG', 'TD', 'CF', 'GQ', 'CD'] },
  EAST: { name: 'Afrique de l\'Est', countries: ['KE', 'TZ', 'UG', 'RW', 'ET'] },
  SOUTH: { name: 'Afrique Australe', countries: ['ZA', 'AO', 'MZ', 'ZW', 'NA', 'BW'] },
} as const;

// Asset Types
export const ASSET_TYPES = ['EQUITY', 'ETF', 'BOND', 'FX', 'CRYPTO', 'COMMODITY'] as const;
export type AssetType = typeof ASSET_TYPES[number];

// Score Colors - Synced with web (frontend/styles/globals.css)
export const SCORE_COLORS = {
  excellent: '#22C55E', // --score-green
  good: '#4ADE80',      // --score-light-green
  average: '#F59E0B',   // --score-yellow
  poor: '#F97316',      // orange
  bad: '#EF4444',       // --score-red
  neutral: '#8A9690',   // for null scores
} as const;

export function getScoreColor(score: number | null): string {
  if (score === null) return SCORE_COLORS.neutral;
  if (score >= 80) return SCORE_COLORS.excellent;
  if (score >= 60) return SCORE_COLORS.good;
  if (score >= 40) return SCORE_COLORS.average;
  if (score >= 20) return SCORE_COLORS.poor;
  return SCORE_COLORS.bad;
}

export function getScoreLabel(score: number | null): string {
  if (score === null) return 'N/A';
  if (score >= 80) return 'Excellent';
  if (score >= 60) return 'Bon';
  if (score >= 40) return 'Moyen';
  if (score >= 20) return 'Faible';
  return 'Risqué';
}
