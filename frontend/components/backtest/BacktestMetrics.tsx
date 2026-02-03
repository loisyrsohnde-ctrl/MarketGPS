/**
 * BacktestMetrics Component
 * Display key performance metrics from backtest results
 */

import React from 'react';
import { BacktestResult } from '@/types/backtest';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Target,
  AlertCircle,
  Award,
} from 'lucide-react';

interface BacktestMetricsProps {
  result: BacktestResult;
}

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  tooltip?: string;
  isPositive?: boolean;
  icon?: React.ReactNode;
  benchmark?: string | number;
}

/**
 * Individual metric card component
 */
function MetricCard({
  label,
  value,
  unit = '',
  tooltip,
  isPositive,
  icon,
  benchmark,
}: MetricCardProps) {
  const getColor = () => {
    if (isPositive === undefined) return 'text-gray-900 dark:text-gray-100';
    return isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  };

  const getBgColor = () => {
    if (isPositive === undefined) return 'bg-gray-50 dark:bg-gray-900';
    return isPositive
      ? 'bg-green-50 dark:bg-green-950'
      : 'bg-red-50 dark:bg-red-950';
  };

  return (
    <div
      className={`p-4 rounded-lg border border-gray-200 dark:border-gray-700 ${getBgColor()}`}
      title={tooltip}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            {label}
          </p>
          <p className={`text-lg font-bold ${getColor()}`}>
            {value}
            {unit && <span className="text-sm ml-1">{unit}</span>}
          </p>
          {benchmark && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              Benchmark: {benchmark}
            </p>
          )}
        </div>
        {icon && (
          <div className={`${getColor()} opacity-60`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * BacktestMetrics Component
 */
export function BacktestMetrics({ result }: BacktestMetricsProps) {
  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatNumber = (value: number) => {
    return value.toFixed(2);
  };

  const alphaIsPositive = result.alpha > 0;
  const maxDdIsNegative = result.max_drawdown_pct < 0;

  return (
    <div className="space-y-6">
      {/* Performance Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4" />
          Performance
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <MetricCard
            label="Total Return"
            value={formatPercent(result.total_return_pct)}
            isPositive={result.total_return_pct > 0}
            benchmark={formatPercent(result.benchmark_return_pct)}
            icon={<Award className="w-4 h-4" />}
            tooltip="Total gain/loss from initial investment"
          />
          <MetricCard
            label="Annualized Return"
            value={formatPercent(result.annualized_return_pct)}
            isPositive={result.annualized_return_pct > 0}
            benchmark={formatPercent(result.benchmark_annualized_return_pct)}
            icon={<BarChart3 className="w-4 h-4" />}
            tooltip="Average yearly return (CAGR)"
          />
          <MetricCard
            label="Alpha"
            value={formatPercent(result.alpha)}
            isPositive={alphaIsPositive}
            unit="vs benchmark"
            tooltip="Excess return vs benchmark (outperformance)"
          />
        </div>
      </div>

      {/* Risk Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Risk Metrics
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <MetricCard
            label="Volatility (Annual)"
            value={formatPercent(result.volatility_annual_pct)}
            benchmark={formatPercent(result.benchmark_volatility_pct)}
            tooltip="Standard deviation of daily returns"
          />
          <MetricCard
            label="Max Drawdown"
            value={formatPercent(result.max_drawdown_pct)}
            isPositive={maxDdIsNegative}
            tooltip="Largest peak-to-trough decline"
          />
          <MetricCard
            label="Sharpe Ratio"
            value={formatNumber(result.sharpe_ratio)}
            isPositive={result.sharpe_ratio > 1}
            tooltip="Risk-adjusted return (higher is better, >1 is good)"
          />
          <MetricCard
            label="Sortino Ratio"
            value={formatNumber(result.sortino_ratio)}
            isPositive={result.sortino_ratio > 1}
            tooltip="Return per unit of downside risk"
          />
        </div>
      </div>

      {/* Win Rate Section */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <Target className="w-4 h-4" />
          Win Rate
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetricCard
            label="Win Rate"
            value={formatNumber(result.win_rate_pct)}
            unit="%"
            isPositive={result.win_rate_pct > 50}
            tooltip="Percentage of periods with positive returns"
          />
          <MetricCard
            label="Best / Worst Period"
            value={`${formatPercent(result.best_period_pct)} / ${formatPercent(result.worst_period_pct)}`}
            tooltip={`Best month: ${result.best_month}, Worst month: ${result.worst_month}`}
          />
          <MetricCard
            label="Winning Periods"
            value={result.winning_periods}
            isPositive={true}
          />
          <MetricCard
            label="Losing Periods"
            value={result.losing_periods}
            isPositive={false}
          />
        </div>
      </div>

      {/* Final Values */}
      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Final Portfolio Value
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <MetricCard
            label="Portfolio Value"
            value={`$${result.final_portfolio_value.toFixed(2)}`}
            isPositive={result.final_portfolio_value > 10000}
            tooltip="Ending portfolio value"
          />
          <MetricCard
            label="Benchmark Value"
            value={`$${result.final_benchmark_value.toFixed(2)}`}
            tooltip={`Ending value of ${result.benchmark} benchmark`}
          />
        </div>
      </div>

      {/* Summary */}
      <div className="p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>Backtest Summary:</strong> Tested from {result.start_date} to{' '}
          {result.end_date} ({result.data_points} data points) using {result.benchmark}{' '}
          as benchmark.
        </p>
      </div>
    </div>
  );
}

export default BacktestMetrics;
