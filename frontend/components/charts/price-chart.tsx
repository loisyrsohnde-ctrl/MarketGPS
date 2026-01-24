'use client';

import { useMemo, useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';
import type { ChartDataPoint, ChartPeriod } from '@/types';

// ═══════════════════════════════════════════════════════════════════════════
// PRICE CHART COMPONENT
// Mobile-optimized with simplified axes and touch-friendly tooltip
// ═══════════════════════════════════════════════════════════════════════════

type ChartStyle = 'line' | 'area' | 'candlestick';

interface PriceChartProps {
  data: ChartDataPoint[];
  period: ChartPeriod;
  onPeriodChange?: (period: ChartPeriod) => void;
  height?: number;
  showPeriodSelector?: boolean;
  className?: string;
  chartStyle?: ChartStyle;
}

// Hook to detect mobile
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  return isMobile;
}

const periods: { value: ChartPeriod; label: string }[] = [
  { value: '30d', label: '30j' },
  { value: '1y', label: '1 an' },
  { value: '5y', label: '5 ans' },
  { value: '10y', label: '10 ans' },
];

export function PriceChart({
  data,
  period,
  onPeriodChange,
  height = 250,
  showPeriodSelector = true,
  className,
  chartStyle = 'line',
}: PriceChartProps) {
  const isMobile = useIsMobile();
  
  // Responsive height
  const chartHeight = isMobile ? Math.min(height, 180) : height;
  
  // Calculate if price is up or down
  const priceChange = useMemo(() => {
    if (!data || data.length < 2) return 0;
    const first = data[0].close;
    const last = data[data.length - 1].close;
    return ((last - first) / first) * 100;
  }, [data]);

  const isPositive = priceChange >= 0;
  const chartColor = isPositive ? '#22C55E' : '#EF4444';
  // Use unique ID to avoid SVG gradient conflicts
  const gradientId = useMemo(() => `priceGradient-${Date.now()}-${Math.random().toString(36).slice(2)}`, []);
  
  // Mobile: use smaller Y-axis width and fewer ticks
  const yAxisWidth = isMobile ? 40 : 55;
  const xAxisTickFontSize = isMobile ? 9 : 10;
  const yAxisTickFontSize = isMobile ? 9 : 10;

  // Format data for chart - ensure numbers are valid
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      dateFormatted: formatDate(point.date, 'short'),
      // Ensure close is a valid number
      close: typeof point.close === 'number' ? point.close : parseFloat(String(point.close)) || 0,
      open: typeof point.open === 'number' ? point.open : parseFloat(String(point.open)) || 0,
      high: typeof point.high === 'number' ? point.high : parseFloat(String(point.high)) || 0,
      low: typeof point.low === 'number' ? point.low : parseFloat(String(point.low)) || 0,
    }));
  }, [data]);
  
  // Debug log
  if (typeof window !== 'undefined' && chartData.length > 0) {
    console.log('Chart data sample:', JSON.stringify(chartData[0]), 'Total:', chartData.length);
  }
  
  // Calculate min/max for domain
  const minMax = useMemo(() => {
    if (!chartData.length) return { min: 0, max: 100 };
    const closes = chartData.map(d => d.close).filter(v => v != null && !isNaN(v));
    if (!closes.length) return { min: 0, max: 100 };
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const padding = (max - min) * 0.05;
    return { min: Math.floor(min - padding), max: Math.ceil(max + padding) };
  }, [chartData]);

  if (!data || data.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center justify-center bg-surface rounded-xl border border-glass-border',
          className
        )}
        style={{ height }}
      >
        <p className="text-text-muted text-sm">Données non disponibles</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3 sm:space-y-4', className)}>
      {/* Period selector - horizontal scroll on mobile */}
      {showPeriodSelector && onPeriodChange && (
        <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto scrollbar-hide -mx-2 px-2 sm:mx-0 sm:px-0">
          {periods.map((p) => (
            <button
              key={p.value}
              onClick={() => onPeriodChange(p.value)}
              className={cn(
                'px-2.5 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm font-medium rounded-lg transition-all duration-200 flex-shrink-0',
                'min-h-[32px] sm:min-h-0', // Touch target
                period === p.value
                  ? 'bg-accent text-bg-primary'
                  : 'bg-surface text-text-secondary active:bg-surface-hover'
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      )}

      {/* Chart */}
      <div
        className="bg-surface/50 rounded-xl border border-glass-border p-2 sm:p-4"
        style={{ height: chartHeight, minHeight: chartHeight }}
      >
        <ResponsiveContainer width="100%" height="100%">
          {chartStyle === 'area' ? (
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: isMobile ? 5 : 15, left: isMobile ? -10 : 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={chartColor} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={chartColor} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255, 255, 255, 0.08)"
                vertical={false}
              />
              <XAxis
                dataKey="dateFormatted"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: xAxisTickFontSize }}
                dy={10}
                interval="preserveStartEnd"
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: yAxisTickFontSize }}
                domain={[minMax.min, minMax.max]}
                dx={-5}
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(0) : '0'}
                width={yAxisWidth}
                hide={isMobile}
              />
              <Tooltip content={<CustomTooltip isMobile={isMobile} />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke={chartColor}
                strokeWidth={isMobile ? 1.5 : 2}
                fill={`url(#${gradientId})`}
                dot={false}
                activeDot={{ r: isMobile ? 4 : 6, fill: chartColor, stroke: '#fff', strokeWidth: 2 }}
                animationDuration={500}
              />
            </AreaChart>
          ) : chartStyle === 'candlestick' ? (
            <ComposedChart
              data={chartData}
              margin={{ top: 10, right: isMobile ? 5 : 15, left: isMobile ? -10 : 0, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255, 255, 255, 0.08)"
                vertical={false}
              />
              <XAxis
                dataKey="dateFormatted"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: xAxisTickFontSize }}
                dy={10}
                interval="preserveStartEnd"
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: yAxisTickFontSize }}
                domain={[minMax.min, minMax.max]}
                dx={-5}
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(0) : '0'}
                width={yAxisWidth}
                hide={isMobile}
              />
              <Tooltip content={<CustomTooltip isMobile={isMobile} />} />
              <Line
                type="linear"
                dataKey="close"
                stroke={chartColor}
                strokeWidth={isMobile ? 1.5 : 2}
                dot={false}
                activeDot={{ r: isMobile ? 4 : 6, fill: chartColor, stroke: '#fff', strokeWidth: 2 }}
              />
            </ComposedChart>
          ) : (
            <LineChart
              data={chartData}
              margin={{ top: 10, right: isMobile ? 5 : 15, left: isMobile ? -10 : 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={chartColor} stopOpacity={0.4} />
                  <stop offset="100%" stopColor={chartColor} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(255, 255, 255, 0.08)"
                vertical={false}
              />
              <XAxis
                dataKey="dateFormatted"
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: xAxisTickFontSize }}
                dy={10}
                interval="preserveStartEnd"
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#94a3b8', fontSize: yAxisTickFontSize }}
                domain={[minMax.min, minMax.max]}
                dx={-5}
                tickFormatter={(value) => typeof value === 'number' ? value.toFixed(0) : '0'}
                width={yAxisWidth}
                hide={isMobile}
              />
              <Tooltip content={<CustomTooltip isMobile={isMobile} />} />
              <Line
                type="linear"
                dataKey="close"
                stroke={chartColor}
                strokeWidth={isMobile ? 2 : 2.5}
                dot={false}
                activeDot={{ r: isMobile ? 4 : 6, fill: chartColor, stroke: '#fff', strokeWidth: 2 }}
                animationDuration={500}
                connectNulls={true}
                isAnimationActive={false}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// CUSTOM TOOLTIP
// ═══════════════════════════════════════════════════════════════════════════

interface TooltipPayload {
  value: number;
  dataKey: string;
  payload: ChartDataPoint & { dateFormatted: string };
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
  isMobile?: boolean;
}

function CustomTooltip({ active, payload, isMobile }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const data = payload[0].payload;

  // Mobile: simplified tooltip with just date and close price
  if (isMobile) {
    return (
      <div className="bg-bg-elevated border border-glass-border rounded-lg px-2.5 py-1.5 shadow-glass-lg">
        <p className="text-[10px] text-text-muted">{data.dateFormatted}</p>
        <p className="text-sm font-semibold text-text-primary">
          {data.close?.toFixed(2)}
        </p>
      </div>
    );
  }

  // Desktop: full tooltip with OHLC
  return (
    <div className="bg-bg-elevated border border-glass-border rounded-lg p-3 shadow-glass-lg">
      <p className="text-xs text-text-muted mb-2">{data.dateFormatted}</p>
      <div className="space-y-1">
        <div className="flex justify-between gap-4">
          <span className="text-xs text-text-muted">Open</span>
          <span className="text-xs font-medium text-text-primary">
            {data.open?.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-xs text-text-muted">High</span>
          <span className="text-xs font-medium text-score-green">
            {data.high?.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-xs text-text-muted">Low</span>
          <span className="text-xs font-medium text-score-red">
            {data.low?.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-xs text-text-muted">Close</span>
          <span className="text-xs font-semibold text-text-primary">
            {data.close?.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MINI SPARKLINE
// ═══════════════════════════════════════════════════════════════════════════

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function Sparkline({
  data,
  width = 80,
  height = 24,
  color,
  className,
}: SparklineProps) {
  const chartData = data.map((value, index) => ({ value, index }));
  const isPositive = data[data.length - 1] >= data[0];
  const strokeColor = color || (isPositive ? '#22C55E' : '#EF4444');

  return (
    <div className={className} style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <defs>
            <linearGradient id={`spark-${isPositive}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={strokeColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke={strokeColor}
            strokeWidth={1.5}
            fill={`url(#spark-${isPositive})`}
            dot={false}
            animationDuration={500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PriceChart;
