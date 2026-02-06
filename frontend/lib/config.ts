/**
 * MarketGPS - Configuration de l'Architecture Frontend
 * 
 * Stack Actuel : Next.js 13+ (App Router) + React 18 + TypeScript + Tailwind
 * Backend API : FastAPI (Python)
 * 
 * IMPORTANT: Streamlit est OBSOLÈTE et archivé dans _archive/streamlit_old/
 */

// Configuration API Backend
export function getApiBaseUrl(): string {
  // 1. Explicit environment variable (set at build time)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }

  // 2. Auto-detect production from window.location (client-side)
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'app.marketgps.online' || hostname === 'marketgps.online') {
      return 'https://api.marketgps.online';
    }
    if (hostname === 'app.afristocks.eu' || hostname === 'afristocks.eu') {
      return 'https://api.afristocks.eu';
    }
  }

  // 3. Server-side (SSR) production detection via NODE_ENV or container hostname
  if (typeof window === 'undefined' && process.env.NODE_ENV === 'production') {
    return 'https://api.marketgps.online';
  }

  // 4. Default for local development
  return 'http://localhost:8000';
}

export const API_CONFIG = {
  // À définir selon ton environnement
  BASE_URL: getApiBaseUrl(),
  
  // Endpoints principaux
  ENDPOINTS: {
    AUTH: '/auth',
    USERS: '/users',
    WATCHLIST: '/watchlist',
    INSTRUMENTS: '/instruments',
    ALERTS: '/alerts',
  },
  
  // Timeouts
  TIMEOUT: 30000,
  
  // Headers par défaut
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};

// Feature Flags
export const FEATURES = {
  WATCHLIST_ENABLED: true,
  ALERTS_ENABLED: true,
  ADVANCED_SEARCH: true,
  EXPORT_DATA: true,
};

// Thème
export const THEME = {
  PRIMARY_COLOR: '#0066cc',
  SECONDARY_COLOR: '#6B7280',
  SUCCESS_COLOR: '#10B981',
  ERROR_COLOR: '#EF4444',
};

export default {
  API_CONFIG,
  FEATURES,
  THEME,
};
