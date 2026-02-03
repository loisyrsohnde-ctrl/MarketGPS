/**
 * Backtest Types
 * Type definitions for backtesting functionality
 */

/**
 * Configuration for running a backtest
 */
export interface BacktestConfig {
  strategy_id: string;
  initial_capital: number;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  rebalance_frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  benchmark: string;
  compositions: CompositionItem[];
}

/**
 * A composition item representing an asset allocation
 */
export interface CompositionItem {
  ticker: string;
  weight: number; // 0-1
  block_name?: string;
}

/**
 * Backtest request to send to API
 */
export interface BacktestRequest {
  strategy_id: string;
  initial_capital: number;
  start_date?: string;
  end_date?: string;
  rebalance_frequency: string;
  benchmark: string;
  compositions: Record<string, number>[]; // [{ticker: weight}]
}

/**
 * Single point in equity curve
 */
export interface EquityCurvePoint {
  date: string;
  portfolio_value: number;
  benchmark_value: number;
  portfolio_return_pct: number;
  benchmark_return_pct: number;
}

/**
 * Drawdown data point
 */
export interface DrawdownPoint {
  date: string;
  drawdown_pct: number;
}

/**
 * Monthly return data
 */
export interface MonthlyReturn {
  period: string; // YYYY-MM
  return_pct: number;
  benchmark_return_pct: number;
}

/**
 * Complete backtest result
 */
export interface BacktestResult {
  // Performance metrics
  total_return_pct: number;
  annualized_return_pct: number;
  benchmark_return_pct: number;
  benchmark_annualized_return_pct: number;
  alpha: number;

  // Risk metrics
  volatility_annual_pct: number;
  benchmark_volatility_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;

  // Win/loss
  winning_periods: number;
  losing_periods: number;
  win_rate_pct: number;
  best_period_pct: number;
  worst_period_pct: number;
  best_month: string;
  worst_month: string;

  // Final values
  final_portfolio_value: number;
  final_benchmark_value: number;

  // Time series
  equity_curve: EquityCurvePoint[];
  drawdown_curve: DrawdownPoint[];
  monthly_returns: MonthlyReturn[];

  // Metadata
  data_points: number;
  start_date: string;
  end_date: string;
  strategy_id: string;
  benchmark: string;
}

/**
 * Backtest preset configuration
 */
export interface BacktestPreset {
  id: string;
  label: string;
  description: string;
  start_offset_years?: number;
  start_date?: string;
}

/**
 * Available benchmark information
 */
export interface BenchmarkInfo {
  id: string;
  name: string;
  description: string;
  asset_class: string;
}

/**
 * Rebalance frequency option
 */
export interface RebalanceFrequency {
  id: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  label: string;
  description: string;
}

/**
 * Backtest statistics metadata
 */
export interface BacktestStats {
  default_initial_capital: number;
  min_initial_capital: number;
  max_initial_capital: number;
  risk_free_rate_annual: number;
  default_rebalance_frequency: string;
  default_benchmark: string;
  supported_frequencies: string[];
  available_benchmarks: string[];
}
