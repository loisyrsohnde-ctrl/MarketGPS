'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export interface DashboardChartProps {
  title: string;
  type: 'bar' | 'line' | 'area';
  data: { name: string; value: number; [key: string]: any }[];
  xKey?: string;
  yKey?: string;
  color?: string;
  height?: number;
  horizontal?: boolean;
  showLegend?: boolean;
}

export function DashboardChart({
  title,
  type,
  data,
  xKey = 'name',
  yKey = 'value',
  color = '#3b82f6',
  height = 300,
  horizontal = false,
  showLegend = false,
}: DashboardChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        <div className="mt-4 flex items-center justify-center" style={{ height }}>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Aucune donnée disponible
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
        {title}
      </h3>
      <div className="mt-4" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <>
            {type === 'bar' && (
              <BarChart
                data={data}
                layout={horizontal ? 'vertical' : 'horizontal'}
                margin={
                  horizontal
                    ? { top: 5, right: 30, left: 200, bottom: 5 }
                    : { top: 5, right: 30, left: 0, bottom: 5 }
                }
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e7eb"
                  className="dark:stroke-gray-700"
                />
                {horizontal ? (
                  <>
                    <XAxis type="number" />
                    <YAxis dataKey={xKey} type="category" width={150} />
                  </>
                ) : (
                  <>
                    <XAxis dataKey={xKey} />
                    <YAxis />
                  </>
                )}
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f3f4f6',
                  }}
                />
                {showLegend && <Legend />}
                <Bar dataKey={yKey} fill={color} radius={[8, 8, 0, 0]} />
              </BarChart>
            )}

            {type === 'line' && (
              <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e7eb"
                  className="dark:stroke-gray-700"
                />
                <XAxis dataKey={xKey} />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f3f4f6',
                  }}
                />
                {showLegend && <Legend />}
                <Line
                  type="monotone"
                  dataKey={yKey}
                  stroke={color}
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            )}

            {type === 'area' && (
              <AreaChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e5e7eb"
                  className="dark:stroke-gray-700"
                />
                <XAxis dataKey={xKey} />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: 'none',
                    borderRadius: '8px',
                    color: '#f3f4f6',
                  }}
                />
                {showLegend && <Legend />}
                <Area
                  type="monotone"
                  dataKey={yKey}
                  fill={color}
                  stroke={color}
                  fillOpacity={0.3}
                />
              </AreaChart>
            )}
          </>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
