/**
 * MarketGPS Real Estate API Client
 * API functions for real estate tax simulations and scoring
 */

import { getApiBaseUrl } from './config';
import type {
  TaxSimulationRequest,
  TaxSimulationResponse,
  ExitSimulationRequest,
  ExitSimulationResponse,
  Exchange1031Request,
  Exchange1031Response,
  ScoringRequest,
  ProphetIAScore,
  RealEstatePortfolio,
  PropertyInput,
  JurisdictionInfo,
} from '@/types/wealth';

const API_BASE = getApiBaseUrl();

/**
 * Simulate annual tax liability and cash flow projections
 */
export async function simulateAnnualTax(
  request: TaxSimulationRequest
): Promise<TaxSimulationResponse> {
  const response = await fetch(`${API_BASE}/api/real-estate/simulate/annual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Tax simulation failed');
  }
  
  return response.json();
}

/**
 * Simulate property sale with capital gains and recapture
 */
export async function simulateExit(
  request: ExitSimulationRequest
): Promise<ExitSimulationResponse> {
  const response = await fetch(`${API_BASE}/api/real-estate/simulate/exit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Exit simulation failed');
  }
  
  return response.json();
}

/**
 * Simulate Section 1031 Like-Kind Exchange (US only)
 */
export async function simulate1031Exchange(
  request: Exchange1031Request
): Promise<Exchange1031Response> {
  const response = await fetch(`${API_BASE}/api/real-estate/simulate/1031-exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || '1031 Exchange simulation failed');
  }
  
  return response.json();
}

/**
 * Calculate ProphetIA score for a property
 */
export async function calculateScore(
  request: ScoringRequest
): Promise<ProphetIAScore> {
  const response = await fetch(`${API_BASE}/api/real-estate/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'ProphetIA scoring failed');
  }
  
  return response.json();
}

/**
 * Get supported tax jurisdictions
 */
export async function getJurisdictions(): Promise<{ jurisdictions: JurisdictionInfo[] }> {
  const response = await fetch(`${API_BASE}/api/real-estate/jurisdictions`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch jurisdictions');
  }
  
  return response.json();
}

/**
 * Get unified wealth summary for real estate portfolio
 */
export async function getWealthSummary(
  properties: PropertyInput[],
  jurisdictions: string[],
  marginalTaxRate: number = 0.30
): Promise<RealEstatePortfolio> {
  const response = await fetch(`${API_BASE}/api/real-estate/wealth/summary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      properties,
      jurisdictions,
      marginal_tax_rate: marginalTaxRate,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Wealth summary failed');
  }
  
  return response.json();
}

/**
 * Format currency for display
 */
export function formatCurrency(
  value: number,
  currency: string = 'USD',
  locale: string = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format percentage for display
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Get color class for ProphetIA score
 */
export function getScoreColor(score: number): string {
  if (score >= 75) return 'text-emerald-400';
  if (score >= 60) return 'text-green-400';
  if (score >= 45) return 'text-yellow-400';
  if (score >= 30) return 'text-orange-400';
  return 'text-red-400';
}

/**
 * Get color class for rating
 */
export function getRatingColor(rating: string): string {
  if (rating.startsWith('A')) return 'bg-emerald-500/20 text-emerald-400';
  if (rating.startsWith('B')) return 'bg-green-500/20 text-green-400';
  if (rating === 'C') return 'bg-yellow-500/20 text-yellow-400';
  if (rating === 'D') return 'bg-orange-500/20 text-orange-400';
  return 'bg-red-500/20 text-red-400';
}

/**
 * Get jurisdiction display name
 */
export function getJurisdictionName(code: string): string {
  const names: Record<string, string> = {
    FR: 'France',
    US: 'United States',
    CA: 'Canada',
    BE: 'Belgium',
    DE: 'Germany',
    CH: 'Switzerland',
  };
  return names[code] || code;
}
