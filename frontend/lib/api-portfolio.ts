/**
 * Portfolio API Client for MarketGPS
 * 
 * Handles portfolio sync, CSV import, and position management.
 * This is a READ-ONLY sync - no trading or order execution.
 */

import { API_CONFIG } from './config';

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

export interface PortfolioAccount {
  id: string;
  name: string;
  broker: string | null;
  account_type: string;
  currency: string;
  notes: string | null;
  created_at: string;
  last_sync_at: string | null;
  position_count: number;
  total_value: number;
}

export interface PortfolioPosition {
  id: string;
  account_id: string | null;
  account_name: string | null;
  symbol: string;
  isin: string | null;
  asset_id: string | null;
  name: string | null;
  quantity: number;
  avg_cost: number | null;
  current_price: number | null;
  current_value: number | null;
  pnl: number | null;
  pnl_percent: number | null;
  currency: string;
  asset_type: string;
  score: number | null;
  updated_at: string;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_percent: number;
  position_count: number;
  account_count: number;
  currency: string;
  allocation_by_type: Record<string, number>;
  allocation_by_sector: Record<string, number>;
  top_holdings: Array<{
    symbol: string;
    name: string | null;
    value: number;
    quantity: number;
    pnl: number;
    score: number | null;
  }>;
  last_sync_at: string | null;
}

export interface BrokerTemplate {
  id: string;
  name: string;
  description: string;
}

export interface CSVPreviewResult {
  filename: string;
  file_size: number;
  file_hash: string;
  encoding_detected: string;
  delimiter: string;
  headers: string[];
  row_count: number;
  sample_rows: Array<Record<string, string>>;
  suggested_mapping: {
    symbol_column?: string;
    quantity_column?: string;
    avg_cost_column?: string;
    name_column?: string;
    isin_column?: string;
  };
  template_applied: string | null;
}

export interface CSVImportResult {
  status: 'completed' | 'partial' | 'failed';
  run_id: string;
  rows_total: number;
  rows_imported: number;
  rows_skipped: number;
  rows_errors: number;
  errors: string[];
}

export interface SyncRun {
  id: string;
  source_type: string;
  status: string;
  rows_total: number;
  rows_imported: number;
  rows_skipped: number;
  rows_errors: number;
  started_at: string;
  completed_at: string | null;
}

export interface PositionCreateRequest {
  account_id?: string;
  symbol: string;
  isin?: string;
  name?: string;
  quantity: number;
  avg_cost?: number;
  currency?: string;
  asset_type?: string;
  notes?: string;
}

export interface AccountCreateRequest {
  name: string;
  broker?: string;
  account_type?: string;
  currency?: string;
  notes?: string;
}

// ═══════════════════════════════════════════════════════════════════════════════
// API CLIENT
// ═══════════════════════════════════════════════════════════════════════════════

const getAuthHeaders = async (): Promise<HeadersInit> => {
  // Get auth token from Supabase client (secure session management)
  if (typeof window !== 'undefined') {
    try {
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
      const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
      const supabase = createClient(supabaseUrl, supabaseKey);
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        return {
          'Authorization': `Bearer ${session.access_token}`,
        };
      }
    } catch {
      // Ignore session errors
    }
  }
  return {};
};

const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_CONFIG.BASE_URL}${endpoint}`;
  const headers = {
    ...API_CONFIG.DEFAULT_HEADERS,
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
    signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API Error: ${response.status} - ${error}`);
  }

  return response.json();
};

// ═══════════════════════════════════════════════════════════════════════════════
// EXPORTED API FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get legal disclaimer for portfolio sync
 */
export async function getDisclaimer(): Promise<{
  title: string;
  content: string;
  version: string;
  requires_acknowledgment: boolean;
}> {
  return apiRequest('/api/portfolio/disclaimer');
}

/**
 * List available broker CSV templates
 */
export async function getBrokerTemplates(): Promise<{ templates: BrokerTemplate[] }> {
  return apiRequest('/api/portfolio/templates');
}

/**
 * Get specific broker template configuration
 */
export async function getBrokerTemplate(templateId: string): Promise<BrokerTemplate & {
  mapping: Record<string, string>;
  delimiter: string;
  encoding: string;
}> {
  return apiRequest(`/api/portfolio/templates/${templateId}`);
}

/**
 * List user's portfolio accounts
 */
export async function getAccounts(): Promise<PortfolioAccount[]> {
  return apiRequest('/api/portfolio/accounts');
}

/**
 * Create a new portfolio account
 */
export async function createAccount(data: AccountCreateRequest): Promise<PortfolioAccount> {
  return apiRequest('/api/portfolio/accounts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a portfolio account
 */
export async function deleteAccount(accountId: string): Promise<{ status: string; id: string }> {
  return apiRequest(`/api/portfolio/accounts/${accountId}`, {
    method: 'DELETE',
  });
}

/**
 * List user's portfolio positions
 */
export async function getPositions(accountId?: string): Promise<PortfolioPosition[]> {
  const params = accountId ? `?account_id=${accountId}` : '';
  return apiRequest(`/api/portfolio/positions${params}`);
}

/**
 * Create or update a position
 */
export async function createPosition(data: PositionCreateRequest): Promise<PortfolioPosition> {
  return apiRequest('/api/portfolio/positions', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a position
 */
export async function deletePosition(positionId: string): Promise<{ status: string; id: string }> {
  return apiRequest(`/api/portfolio/positions/${positionId}`, {
    method: 'DELETE',
  });
}

/**
 * Get portfolio summary with aggregations
 */
export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  return apiRequest('/api/portfolio/summary');
}

/**
 * Preview CSV file before import
 */
export async function previewCSV(
  file: File,
  templateId?: string
): Promise<CSVPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (templateId) {
    formData.append('template_id', templateId);
  }

  const url = `${API_CONFIG.BASE_URL}/api/portfolio/import/csv/preview`;
  const headers = getAuthHeaders();

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`CSV Preview Error: ${error}`);
  }

  return response.json();
}

/**
 * Import positions from CSV file
 */
export async function importCSV(
  file: File,
  mapping: {
    symbol_column: string;
    quantity_column: string;
    avg_cost_column?: string;
    isin_column?: string;
    name_column?: string;
    currency_column?: string;
  },
  accountId?: string,
  templateId?: string
): Promise<CSVImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mapping', JSON.stringify(mapping));
  if (accountId) {
    formData.append('account_id', accountId);
  }
  if (templateId) {
    formData.append('template_id', templateId);
  }

  const url = `${API_CONFIG.BASE_URL}/api/portfolio/import/csv`;
  const headers = getAuthHeaders();

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`CSV Import Error: ${error}`);
  }

  return response.json();
}

/**
 * Get sync run history
 */
export async function getSyncRuns(limit: number = 20): Promise<SyncRun[]> {
  return apiRequest(`/api/portfolio/sync-runs?limit=${limit}`);
}

/**
 * Check if user has any portfolio data
 */
export async function hasPortfolioData(): Promise<boolean> {
  try {
    const summary = await getPortfolioSummary();
    return summary.position_count > 0;
  } catch {
    return false;
  }
}
