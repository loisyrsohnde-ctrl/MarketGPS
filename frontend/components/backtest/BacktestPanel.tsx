/**
 * BacktestPanel Component
 * Main panel for configuring and running backtests
 */

import React, { useState, useEffect } from 'react';
import { Loader2, Play, X } from 'lucide-react';
import { BacktestConfig, CompositionItem, BacktestPreset, BenchmarkInfo } from '@/types/backtest';
import { useBacktest } from '@/hooks/useBacktest';
import BacktestMetrics from './BacktestMetrics';
import EquityCurveChart from './EquityCurveChart';

export interface BacktestPanelProps {
  strategyId: string;
  compositions: CompositionItem[];
  onClose?: () => void;
}

/**
 * BacktestPanel Component
 */
export function BacktestPanel({
  strategyId,
  compositions,
  onClose,
}: BacktestPanelProps) {
  const [config, setConfig] = useState<Partial<BacktestConfig>>({
    strategy_id: strategyId,
    initial_capital: 10000,
    rebalance_frequency: 'monthly',
    benchmark: 'SPY',
    compositions: compositions,
  });

  const {
    isLoading,
    error,
    result,
    presets,
    benchmarks,
    frequencies,
    runBacktest,
    loadMetadata,
    clear,
    clearError,
  } = useBacktest();

  // Load metadata on mount
  useEffect(() => {
    loadMetadata();
  }, [loadMetadata]);

  // Handle backtest execution
  const handleRunBacktest = async () => {
    if (!config.rebalance_frequency || !config.benchmark) {
      return;
    }

    const fullConfig: BacktestConfig = {
      strategy_id: config.strategy_id || strategyId,
      initial_capital: config.initial_capital || 10000,
      rebalance_frequency: config.rebalance_frequency as any,
      benchmark: config.benchmark,
      compositions: config.compositions || compositions,
      start_date: config.start_date,
      end_date: config.end_date,
    };

    await runBacktest(fullConfig);
  };

  // Handle preset selection
  const handlePresetSelect = (preset: BacktestPreset) => {
    const endDate = new Date();
    let startDate = new Date();

    if (preset.start_offset_years) {
      startDate.setFullYear(startDate.getFullYear() - preset.start_offset_years);
    } else if (preset.start_date) {
      startDate = new Date(preset.start_date);
    }

    setConfig((prev) => ({
      ...prev,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
    }));
  };

  return (
    <div className="space-y-6">
      {/* Configuration Panel */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Backtest Your Strategy
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          )}
        </div>

        {/* Presets */}
        {presets.length > 0 && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Quick Presets
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => handlePresetSelect(preset)}
                  className="px-3 py-2 text-sm font-medium rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-blue-950 hover:border-blue-500 dark:hover:border-blue-500 transition text-gray-700 dark:text-gray-300"
                  title={preset.description}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Configuration Form */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Initial Capital */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Initial Capital ($)
            </label>
            <input
              type="number"
              min="100"
              max="10000000"
              value={config.initial_capital || 10000}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  initial_capital: parseFloat(e.target.value) || 10000,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
            />
          </div>

          {/* Benchmark */}
          {benchmarks.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Benchmark
              </label>
              <select
                value={config.benchmark || 'SPY'}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    benchmark: e.target.value,
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
              >
                {benchmarks.map((bench) => (
                  <option key={bench.id} value={bench.id}>
                    {bench.name} ({bench.asset_class})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Rebalance Frequency */}
          {frequencies.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Rebalancing Frequency
              </label>
              <select
                value={config.rebalance_frequency || 'monthly'}
                onChange={(e) =>
                  setConfig((prev) => ({
                    ...prev,
                    rebalance_frequency: e.target.value as any,
                  }))
                }
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
              >
                {frequencies.map((freq) => (
                  <option key={freq.id} value={freq.id}>
                    {freq.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Start Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={config.start_date || ''}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  start_date: e.target.value,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
            />
          </div>

          {/* End Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={config.end_date || ''}
              onChange={(e) =>
                setConfig((prev) => ({
                  ...prev,
                  end_date: e.target.value,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition"
            />
          </div>
        </div>

        {/* Composition Summary */}
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Portfolio Allocation:</strong>{' '}
            {compositions
              .map((c) => `${c.ticker} (${(c.weight * 100).toFixed(0)}%)`)
              .join(', ')}
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg flex justify-between items-start">
            <p className="text-sm text-red-900 dark:text-red-100">{error}</p>
            <button
              onClick={clearError}
              className="ml-2 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Run Button */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={handleRunBacktest}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running Backtest...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Backtest
              </>
            )}
          </button>
          {result && (
            <button
              onClick={clear}
              className="px-4 py-3 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-lg transition"
            >
              Clear Results
            </button>
          )}
        </div>
      </div>

      {/* Results Display */}
      {result && (
        <div className="space-y-6">
          <EquityCurveChart result={result} />
          <BacktestMetrics result={result} />
        </div>
      )}
    </div>
  );
}

export default BacktestPanel;
