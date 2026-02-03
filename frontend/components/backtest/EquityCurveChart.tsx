/**
 * EquityCurveChart Component
 * Visualizes portfolio performance vs benchmark over time
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { BacktestResult, EquityCurvePoint, DrawdownPoint } from '@/types/backtest';

export interface EquityCurveChartProps {
  result: BacktestResult;
  showDrawdown?: boolean;
}

interface ChartData extends EquityCurvePoint {
  drawdown_pct?: number;
}

/**
 * Custom tooltip for equity curve chart
 */
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload) return null;

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
        {payload[0]?.payload?.date}
      </p>
      {payload.map((entry: any, idx: number) => (
        <p key={idx} style={{ color: entry.color }} className="text-sm font-semibold">
          {entry.name}: ${entry.value.toFixed(2)}
        </p>
      ))}
    </div>
  );
}

/**
 * Custom tooltip for drawdown chart
 */
function DrawdownTooltip({ active, payload }: any) {
  if (!active || !payload) return null;

  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
        {payload[0]?.payload?.date}
      </p>
      <p style={{ color: payload[0]?.color }} className="text-sm font-semibold">
        {payload[0]?.name}: {payload[0]?.value.toFixed(2)}%
      </p>
    </div>
  );
}

/**
 * EquityCurveChart Component
 */
export function EquityCurveChart({
  result,
  showDrawdown = true,
}: EquityCurveChartProps) {
  // Merge equity curve and drawdown data
  const chartData = useMemo(() => {
    const equityMap = new Map<string, EquityCurvePoint>();
    const drawdownMap = new Map<string, number>();

    result.equity_curve.forEach((point) => {
      equityMap.set(point.date, point);
    });

    if (showDrawdown) {
      result.drawdown_curve.forEach((point) => {
        drawdownMap.set(point.date, point.drawdown_pct);
      });
    }

    return Array.from(equityMap.entries())
      .map(([date, point]) => ({
        ...point,
        drawdown_pct: drawdownMap.get(date),
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [result.equity_curve, result.drawdown_curve, showDrawdown]);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-gray-500 dark:text-gray-400">No data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Equity Curve Chart */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">
          Portfolio vs Benchmark
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
              tickFormatter={(date) => {
                // Show every Nth label to avoid crowding
                const idx = chartData.findIndex((d) => d.date === date);
                return idx % Math.ceil(chartData.length / 8) === 0
                  ? new Date(date).toLocaleDateString('en-US', {
                      month: 'short',
                      year: '2-digit',
                    })
                  : '';
              }}
            />
            <YAxis
              stroke="#9ca3af"
              tick={{ fontSize: 12 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="portfolio_value"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={2}
              name="Portfolio"
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="benchmark_value"
              stroke="#ef4444"
              dot={false}
              strokeWidth={2}
              strokeDasharray="5 5"
              name={`${result.benchmark} Benchmark`}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
          Blue solid line shows portfolio value. Red dashed line shows benchmark ({result.benchmark})
          performance using the same initial capital.
        </p>
      </div>

      {/* Drawdown Chart */}
      {showDrawdown && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">
            Drawdown from Peak
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(date) => {
                  const idx = chartData.findIndex((d) => d.date === date);
                  return idx % Math.ceil(chartData.length / 8) === 0
                    ? new Date(date).toLocaleDateString('en-US', {
                        month: 'short',
                        year: '2-digit',
                      })
                    : '';
                }}
              />
              <YAxis
                stroke="#9ca3af"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `${value.toFixed(0)}%`}
              />
              <Tooltip content={<DrawdownTooltip />} />
              <Area
                type="monotone"
                dataKey="drawdown_pct"
                fill="#fee2e2"
                stroke="#dc2626"
                strokeWidth={1}
                name="Drawdown"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
            Shows the maximum decline from the portfolio's peak value at any given time.
            More negative values indicate larger drawdowns (peak-to-trough losses).
          </p>
        </div>
      )}
    </div>
  );
}

export default EquityCurveChart;
