'use client';

import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { getScoreColor, getScoreConfig } from '@/types';

// ═══════════════════════════════════════════════════════════════════════════
// SCORE GAUGE COMPONENT
// Circular gauge displaying score with animated fill
// ═══════════════════════════════════════════════════════════════════════════

interface ScoreGaugeProps {
  score: number | null;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showLabel?: boolean;
  className?: string;
}

export function ScoreGauge({ score, size = 'md', showLabel = true, className }: ScoreGaugeProps) {
  const dimensions = {
    sm: { width: 100, strokeWidth: 8, fontSize: '20px', labelSize: '10px' },
    md: { width: 140, strokeWidth: 10, fontSize: '28px', labelSize: '12px' },
    lg: { width: 180, strokeWidth: 12, fontSize: '36px', labelSize: '14px' },
    xl: { width: 220, strokeWidth: 14, fontSize: '44px', labelSize: '16px' },
  };

  const { width, strokeWidth, fontSize, labelSize } = dimensions[size];
  const radius = (width - strokeWidth) / 2;
  const circumference = radius * Math.PI; // Semi-circle
  const center = width / 2;

  const config = getScoreConfig(score);
  const color = getScoreColor(score);
  const percentage = score !== null ? score / 100 : 0;
  const offset = circumference * (1 - percentage);

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <svg
        width={width}
        height={width / 2 + 20}
        viewBox={`0 0 ${width} ${width / 2 + 20}`}
        className="overflow-visible"
      >
        {/* Background arc */}
        <path
          d={`M ${strokeWidth / 2} ${center} A ${radius} ${radius} 0 0 1 ${width - strokeWidth / 2} ${center}`}
          fill="none"
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />

        {/* Score arc */}
        <path
          d={`M ${strokeWidth / 2} ${center} A ${radius} ${radius} 0 0 1 ${width - strokeWidth / 2} ${center}`}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1s ease-out, stroke 0.3s ease',
            filter: `drop-shadow(0 0 8px ${color}40)`,
          }}
        />

        {/* Score text */}
        <text
          x={center}
          y={center - 10}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="var(--text-primary)"
          style={{ fontSize, fontWeight: 700 }}
        >
          {score !== null ? score : '—'}
        </text>

        {/* /100 label */}
        <text
          x={center}
          y={center + 15}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="var(--text-muted)"
          style={{ fontSize: labelSize }}
        >
          /100
        </text>
      </svg>

      {/* Semantic label */}
      {showLabel && (
        <div
          className="mt-2 px-3 py-1 rounded-full text-sm font-medium"
          style={{
            backgroundColor: config.bgColor,
            color: config.color,
          }}
        >
          {config.label}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MINI SCORE GAUGE
// Compact version for lists/tables
// ═══════════════════════════════════════════════════════════════════════════

interface MiniScoreGaugeProps {
  score: number | null;
  className?: string;
}

export function MiniScoreGauge({ score, className }: MiniScoreGaugeProps) {
  const color = getScoreColor(score);
  const percentage = score !== null ? score : 0;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="relative w-8 h-8">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          {/* Background */}
          <circle
            cx="18"
            cy="18"
            r="16"
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="3"
          />
          {/* Progress */}
          <circle
            cx="18"
            cy="18"
            r="16"
            fill="none"
            stroke={color}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${percentage} 100`}
            style={{
              transition: 'stroke-dasharray 0.5s ease',
            }}
          />
        </svg>
      </div>
      <span
        className="text-sm font-semibold"
        style={{ color }}
      >
        {score !== null ? score : '—'}
      </span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// PILLAR BAR COMPONENT
// Horizontal bar for Value/Momentum/Safety pillars
// ═══════════════════════════════════════════════════════════════════════════

interface PillarBarProps {
  label: string;
  value: number | null;
  icon?: string;
  className?: string;
}

export function PillarBar({ label, value, icon, className }: PillarBarProps) {
  const color = getScoreColor(value);
  const percentage = value !== null ? value : 0;

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {icon && <span className="text-lg">{icon}</span>}
      <span className="w-24 text-sm text-text-secondary font-medium">{label}</span>
      <div className="flex-1 h-2.5 bg-glass-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
      <span
        className="w-10 text-right text-sm font-semibold"
        style={{ color }}
      >
        {value !== null ? value : '—'}
      </span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// KPI BAR COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface KpiBarProps {
  label: string;
  value: number | null;
  maxValue?: number;
  unit?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  className?: string;
}

export function KpiBar({
  label,
  value,
  maxValue = 100,
  unit = '%',
  variant = 'default',
  className,
}: KpiBarProps) {
  const percentage = value !== null ? (value / maxValue) * 100 : 0;
  
  const variantColors = {
    default: 'var(--accent)',
    success: 'var(--score-green)',
    warning: 'var(--score-yellow)',
    danger: 'var(--score-red)',
  };

  const color = variantColors[variant];

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted uppercase tracking-wide">{label}</span>
        <span className="text-sm font-semibold text-text-primary">
          {value !== null ? `${value}${unit}` : '—'}
        </span>
      </div>
      <div className="h-1.5 bg-glass-border rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500 ease-out"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}

export default ScoreGauge;
