/**
 * usePortfolio Hook
 * 
 * React hook for portfolio data management.
 * Provides positions, summary, and loading states.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getPortfolioSummary,
  getPositions,
  getAccounts,
  hasPortfolioData,
  type PortfolioSummary,
  type PortfolioPosition,
  type PortfolioAccount,
} from '@/lib/api-portfolio';

interface UsePortfolioResult {
  // Data
  summary: PortfolioSummary | null;
  positions: PortfolioPosition[];
  accounts: PortfolioAccount[];
  
  // State
  isLoading: boolean;
  isEmpty: boolean;
  error: Error | null;
  
  // Actions
  refresh: () => Promise<void>;
}

export function usePortfolio(): UsePortfolioResult {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [positions, setPositions] = useState<PortfolioPosition[]>([]);
  const [accounts, setAccounts] = useState<PortfolioAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [summaryData, positionsData, accountsData] = await Promise.all([
        getPortfolioSummary(),
        getPositions(),
        getAccounts(),
      ]);

      setSummary(summaryData);
      setPositions(positionsData);
      setAccounts(accountsData);
      setIsEmpty(summaryData.position_count === 0);
    } catch (e) {
      console.error('Failed to load portfolio:', e);
      setError(e instanceof Error ? e : new Error('Failed to load portfolio'));
      setIsEmpty(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    summary,
    positions,
    accounts,
    isLoading,
    isEmpty,
    error,
    refresh,
  };
}

/**
 * Quick check if user has any portfolio data
 */
export function useHasPortfolio(): {
  hasData: boolean | null;
  isChecking: boolean;
} {
  const [hasData, setHasData] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    hasPortfolioData()
      .then(setHasData)
      .catch(() => setHasData(false))
      .finally(() => setIsChecking(false));
  }, []);

  return { hasData, isChecking };
}

export default usePortfolio;
