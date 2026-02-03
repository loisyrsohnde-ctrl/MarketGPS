/**
 * useBacktest Hook
 * Management of backtest state and API interactions
 */

import { useState, useCallback } from 'react';
import {
  BacktestConfig,
  BacktestRequest,
  BacktestResult,
  BacktestPreset,
  BenchmarkInfo,
  RebalanceFrequency,
  CompositionItem,
} from '@/types/backtest';

interface BacktestState {
  isLoading: boolean;
  error: string | null;
  result: BacktestResult | null;
  presets: BacktestPreset[];
  benchmarks: BenchmarkInfo[];
  frequencies: RebalanceFrequency[];
}

const initialState: BacktestState = {
  isLoading: false,
  error: null,
  result: null,
  presets: [],
  benchmarks: [],
  frequencies: [],
};

/**
 * Hook to manage backtest state and API calls
 */
export function useBacktest() {
  const [state, setState] = useState<BacktestState>(initialState);

  /**
   * Run a backtest with the given configuration
   */
  const runBacktest = useCallback(
    async (config: BacktestConfig): Promise<BacktestResult | null> => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        // Convert compositions to API format
        const compositions = config.compositions.map((item) => ({
          [item.ticker]: item.weight,
        }));

        const request: BacktestRequest = {
          strategy_id: config.strategy_id,
          initial_capital: config.initial_capital,
          start_date: config.start_date,
          end_date: config.end_date,
          rebalance_frequency: config.rebalance_frequency,
          benchmark: config.benchmark,
          compositions,
        };

        const response = await fetch('/api/backtest/run', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(request),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Backtest failed');
        }

        const result: BacktestResult = await response.json();

        setState((prev) => ({
          ...prev,
          isLoading: false,
          result,
          error: null,
        }));

        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Unknown error';

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
          result: null,
        }));

        return null;
      }
    },
    []
  );

  /**
   * Load available backtest presets
   */
  const loadPresets = useCallback(async () => {
    try {
      const response = await fetch('/api/backtest/presets');
      if (!response.ok) throw new Error('Failed to load presets');

      const presets: BacktestPreset[] = await response.json();

      setState((prev) => ({
        ...prev,
        presets,
      }));

      return presets;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load presets';
      setState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
      return [];
    }
  }, []);

  /**
   * Load available benchmarks
   */
  const loadBenchmarks = useCallback(async () => {
    try {
      const response = await fetch('/api/backtest/benchmarks');
      if (!response.ok) throw new Error('Failed to load benchmarks');

      const benchmarks: BenchmarkInfo[] = await response.json();

      setState((prev) => ({
        ...prev,
        benchmarks,
      }));

      return benchmarks;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load benchmarks';
      setState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
      return [];
    }
  }, []);

  /**
   * Load available rebalance frequencies
   */
  const loadFrequencies = useCallback(async () => {
    try {
      const response = await fetch('/api/backtest/rebalance-frequencies');
      if (!response.ok) throw new Error('Failed to load frequencies');

      const frequencies: RebalanceFrequency[] = await response.json();

      setState((prev) => ({
        ...prev,
        frequencies,
      }));

      return frequencies;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load frequencies';
      setState((prev) => ({
        ...prev,
        error: errorMessage,
      }));
      return [];
    }
  }, []);

  /**
   * Load all backtest metadata (presets, benchmarks, frequencies)
   */
  const loadMetadata = useCallback(async () => {
    await Promise.all([loadPresets(), loadBenchmarks(), loadFrequencies()]);
  }, [loadPresets, loadBenchmarks, loadFrequencies]);

  /**
   * Clear the current result and error
   */
  const clear = useCallback(() => {
    setState((prev) => ({
      ...prev,
      result: null,
      error: null,
    }));
  }, []);

  /**
   * Clear only the error
   */
  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    // State
    isLoading: state.isLoading,
    error: state.error,
    result: state.result,
    presets: state.presets,
    benchmarks: state.benchmarks,
    frequencies: state.frequencies,

    // Actions
    runBacktest,
    loadPresets,
    loadBenchmarks,
    loadFrequencies,
    loadMetadata,
    clear,
    clearError,
  };
}

export type UseBacktestReturn = ReturnType<typeof useBacktest>;
