/**
 * MarketGPS Mobile - Price Chart Component
 * SVG-based price chart using react-native-svg
 */

import React, { useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
} from 'react-native';
import Svg, { Path, Line, Defs, LinearGradient, Stop, Rect, Text as SvgText } from 'react-native-svg';
import { ChartDataPoint } from '@/lib/api';
import { GpsLoading } from './GpsLoading';

interface PriceChartProps {
  data: ChartDataPoint[];
  width?: number;
  height?: number;
  isLoading?: boolean;
  error?: boolean;
  period?: string;
}

const CHART_PADDING = { top: 20, right: 20, bottom: 30, left: 60 };

export function PriceChart({
  data,
  width = Dimensions.get('window').width - 40,
  height = 200,
  isLoading = false,
  error = false,
  period = '30d',
}: PriceChartProps) {
  // Calculate chart dimensions
  const chartWidth = width - CHART_PADDING.left - CHART_PADDING.right;
  const chartHeight = height - CHART_PADDING.top - CHART_PADDING.bottom;

  // Process data and calculate scales
  const { path, areaPath, minPrice, maxPrice, priceChange, isPositive, yLabels, xLabels } = useMemo(() => {
    if (!data || data.length === 0) {
      return { path: '', areaPath: '', minPrice: 0, maxPrice: 0, priceChange: 0, isPositive: true, yLabels: [], xLabels: [] };
    }

    // Use close prices for line chart
    const prices = data.map(d => d.close);
    const min = Math.min(...prices) * 0.995; // Add 0.5% padding
    const max = Math.max(...prices) * 1.005;
    const range = max - min || 1;

    // Calculate price change
    const firstPrice = prices[0];
    const lastPrice = prices[prices.length - 1];
    const change = ((lastPrice - firstPrice) / firstPrice) * 100;
    const positive = change >= 0;

    // Generate path
    const points = data.map((d, i) => {
      const x = (i / (data.length - 1)) * chartWidth;
      const y = chartHeight - ((d.close - min) / range) * chartHeight;
      return { x, y };
    });

    // Line path
    const linePath = points.reduce((acc, point, i) => {
      if (i === 0) return `M ${point.x} ${point.y}`;
      return `${acc} L ${point.x} ${point.y}`;
    }, '');

    // Area path (for gradient fill)
    const area = `${linePath} L ${chartWidth} ${chartHeight} L 0 ${chartHeight} Z`;

    // Y-axis labels (4 labels)
    const yLabelCount = 4;
    const yLabelsArr = Array.from({ length: yLabelCount }, (_, i) => {
      const value = min + (range * i) / (yLabelCount - 1);
      const y = chartHeight - (i / (yLabelCount - 1)) * chartHeight;
      return { value, y };
    });

    // X-axis labels (based on period)
    const xLabelsArr = getXLabels(data, period);

    return {
      path: linePath,
      areaPath: area,
      minPrice: min,
      maxPrice: max,
      priceChange: change,
      isPositive: positive,
      yLabels: yLabelsArr,
      xLabels: xLabelsArr,
    };
  }, [data, chartWidth, chartHeight, period]);

  // Format price for y-axis
  const formatPrice = (price: number): string => {
    if (price >= 1000) {
      return `$${(price / 1000).toFixed(1)}k`;
    }
    if (price >= 1) {
      return `$${price.toFixed(2)}`;
    }
    return `$${price.toFixed(4)}`;
  };

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { width, height }]}>
        <View style={styles.loadingContainer}>
          <GpsLoading size="small" minimal />
        </View>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={[styles.container, { width, height }]}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Données indisponibles</Text>
        </View>
      </View>
    );
  }

  // Empty data state
  if (!data || data.length === 0) {
    return (
      <View style={[styles.container, { width, height }]}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>Aucune donnée de prix</Text>
        </View>
      </View>
    );
  }

  const lineColor = isPositive ? '#22C55E' : '#EF4444';
  const gradientColor = isPositive ? ['rgba(34, 197, 94, 0.3)', 'rgba(34, 197, 94, 0)'] : ['rgba(239, 68, 68, 0.3)', 'rgba(239, 68, 68, 0)'];

  return (
    <View style={[styles.container, { width, height }]}>
      {/* Price Change Badge */}
      <View style={styles.changeContainer}>
        <View style={[styles.changeBadge, isPositive ? styles.changeBadgePositive : styles.changeBadgeNegative]}>
          <Text style={[styles.changeText, isPositive ? styles.changeTextPositive : styles.changeTextNegative]}>
            {isPositive ? '+' : ''}{priceChange.toFixed(2)}%
          </Text>
        </View>
      </View>

      <Svg width={width} height={height}>
        <Defs>
          <LinearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <Stop offset="0" stopColor={gradientColor[0]} />
            <Stop offset="1" stopColor={gradientColor[1]} />
          </LinearGradient>
        </Defs>

        {/* Y-axis grid lines and labels */}
        {yLabels.map((label, i) => (
          <React.Fragment key={`y-${i}`}>
            {/* Grid line */}
            <Line
              x1={CHART_PADDING.left}
              y1={CHART_PADDING.top + label.y}
              x2={width - CHART_PADDING.right}
              y2={CHART_PADDING.top + label.y}
              stroke="#1E293B"
              strokeWidth={1}
              strokeDasharray="4,4"
            />
            {/* Label */}
            <SvgText
              x={CHART_PADDING.left - 8}
              y={CHART_PADDING.top + label.y + 4}
              fill="#64748B"
              fontSize={10}
              textAnchor="end"
            >
              {formatPrice(label.value)}
            </SvgText>
          </React.Fragment>
        ))}

        {/* X-axis labels */}
        {xLabels.map((label, i) => (
          <SvgText
            key={`x-${i}`}
            x={CHART_PADDING.left + (label.position * chartWidth)}
            y={height - 8}
            fill="#64748B"
            fontSize={10}
            textAnchor="middle"
          >
            {label.text}
          </SvgText>
        ))}

        {/* Area fill */}
        <Path
          d={areaPath}
          fill="url(#areaGradient)"
          transform={`translate(${CHART_PADDING.left}, ${CHART_PADDING.top})`}
        />

        {/* Line */}
        <Path
          d={path}
          fill="none"
          stroke={lineColor}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          transform={`translate(${CHART_PADDING.left}, ${CHART_PADDING.top})`}
        />

        {/* Current price dot */}
        {data.length > 0 && (
          <Rect
            x={CHART_PADDING.left + chartWidth - 4}
            y={CHART_PADDING.top + (chartHeight - ((data[data.length - 1].close - minPrice) / (maxPrice - minPrice || 1)) * chartHeight) - 4}
            width={8}
            height={8}
            rx={4}
            fill={lineColor}
          />
        )}
      </Svg>
    </View>
  );
}

// Helper to get X-axis labels based on period
function getXLabels(data: ChartDataPoint[], period: string): Array<{ text: string; position: number }> {
  if (!data || data.length === 0) return [];

  const labels: Array<{ text: string; position: number }> = [];
  const len = data.length;

  // Determine number of labels based on data length
  const labelCount = Math.min(5, len);
  const step = Math.floor(len / (labelCount - 1));

  for (let i = 0; i < labelCount; i++) {
    const idx = Math.min(i * step, len - 1);
    const dataPoint = data[idx];
    if (!dataPoint) continue;

    const date = new Date(dataPoint.date);
    let text = '';

    // Format based on period
    if (period === '1d' || period === '1w') {
      text = date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    } else if (period === '30d' || period === '3m') {
      text = date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    } else {
      text = date.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' });
    }

    labels.push({
      text,
      position: idx / (len - 1),
    });
  }

  return labels;
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0A0F1C',
    borderRadius: 12,
    overflow: 'hidden',
  },
  changeContainer: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 1,
  },
  changeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  changeBadgePositive: {
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
  },
  changeBadgeNegative: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
  },
  changeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  changeTextPositive: {
    color: '#22C55E',
  },
  changeTextNegative: {
    color: '#EF4444',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 8,
    fontSize: 12,
    color: '#64748B',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    fontSize: 12,
    color: '#EF4444',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    fontSize: 12,
    color: '#64748B',
  },
});

export default PriceChart;
