'use client';

import { forwardRef, type HTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { getScoreConfig } from '@/types';

// ═══════════════════════════════════════════════════════════════════════════
// BADGE VARIANTS
// ═══════════════════════════════════════════════════════════════════════════

const badgeVariants = cva(
  'inline-flex items-center justify-center font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-surface text-text-secondary border border-glass-border',
        success: 'bg-score-green/15 text-score-green',
        warning: 'bg-score-yellow/15 text-score-yellow',
        danger: 'bg-score-red/15 text-score-red',
        info: 'bg-status-info/15 text-status-info',
        accent: 'bg-accent-dim text-accent',
      },
      size: {
        sm: 'px-2 py-0.5 text-[10px] rounded-md',
        md: 'px-2.5 py-1 text-xs rounded-lg',
        lg: 'px-3 py-1.5 text-sm rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// BADGE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(badgeVariants({ variant, size }), className)}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

// ═══════════════════════════════════════════════════════════════════════════
// SCORE BADGE COMPONENT
// Automatically colored based on score value
// ═══════════════════════════════════════════════════════════════════════════

interface ScoreBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  score: number | null;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const ScoreBadge = forwardRef<HTMLSpanElement, ScoreBadgeProps>(
  ({ className, score, showLabel = false, size = 'md', ...props }, ref) => {
    const config = getScoreConfig(score);
    
    const sizeClasses = {
      sm: 'px-2 py-0.5 text-xs min-w-[40px]',
      md: 'px-3 py-1 text-sm min-w-[50px]',
      lg: 'px-4 py-1.5 text-base min-w-[60px]',
    };
    
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-semibold rounded-lg',
          sizeClasses[size],
          className
        )}
        style={{
          backgroundColor: config.bgColor,
          color: config.color,
        }}
        {...props}
      >
        {score !== null ? score : '—'}
        {showLabel && score !== null && (
          <span className="ml-1.5 opacity-80 text-[0.85em]">{config.label}</span>
        )}
      </span>
    );
  }
);

ScoreBadge.displayName = 'ScoreBadge';

// ═══════════════════════════════════════════════════════════════════════════
// SCORE GAUGE BADGE COMPONENT
// Mini circular gauge with color gradient (red → yellow → green)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Calculates the color based on score (0-100)
 * 0-30: Red (#ef4444)
 * 30-60: Red → Yellow gradient
 * 60-80: Yellow → Green gradient  
 * 80-100: Green (#22c55e)
 */
function getScoreColor(score: number): string {
  if (score <= 30) {
    return '#ef4444'; // Pure red
  } else if (score <= 50) {
    // Red to Orange (30-50)
    const t = (score - 30) / 20;
    const r = 239;
    const g = Math.round(68 + t * (146 - 68));
    const b = Math.round(68 + t * (0 - 68));
    return `rgb(${r}, ${g}, ${b})`;
  } else if (score <= 70) {
    // Orange to Yellow (50-70)
    const t = (score - 50) / 20;
    const r = Math.round(239 + t * (234 - 239));
    const g = Math.round(146 + t * (179 - 146));
    const b = 0;
    return `rgb(${r}, ${g}, ${b})`;
  } else if (score <= 85) {
    // Yellow to Light green (70-85)
    const t = (score - 70) / 15;
    const r = Math.round(234 - t * (234 - 132));
    const g = Math.round(179 + t * (204 - 179));
    const b = Math.round(0 + t * 22);
    return `rgb(${r}, ${g}, ${b})`;
  } else {
    // Light green to Green (85-100)
    const t = (score - 85) / 15;
    const r = Math.round(132 - t * (132 - 34));
    const g = Math.round(204 - t * (204 - 197));
    const b = Math.round(22 + t * (94 - 22));
    return `rgb(${r}, ${g}, ${b})`;
  }
}

interface ScoreGaugeBadgeProps extends HTMLAttributes<HTMLDivElement> {
  score: number | null;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  showText?: boolean;
}

const ScoreGaugeBadge = forwardRef<HTMLDivElement, ScoreGaugeBadgeProps>(
  ({ className, score, size = 'md', showText = true, ...props }, ref) => {
    const normalizedScore = score !== null ? Math.max(0, Math.min(100, score)) : 0;
    const color = score !== null ? getScoreColor(normalizedScore) : '#6b7280';
    const fillPercent = score !== null ? normalizedScore : 0;
    
    const sizeConfig = {
      xs: { width: 90, height: 22, fontSize: '11px', barHeight: 8, radius: 4 },
      sm: { width: 110, height: 26, fontSize: '12px', barHeight: 10, radius: 5 },
      md: { width: 130, height: 30, fontSize: '13px', barHeight: 12, radius: 6 },
      lg: { width: 160, height: 36, fontSize: '15px', barHeight: 14, radius: 7 },
    };
    
    const config = sizeConfig[size];
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex flex-col items-center justify-center gap-0.5',
          className
        )}
        style={{ minWidth: config.width }}
        {...props}
      >
        {/* Score number */}
        {showText && (
          <span 
            className="font-bold leading-none"
            style={{ 
              fontSize: config.fontSize,
              color: score !== null ? color : '#6b7280'
            }}
          >
            {score !== null ? Math.round(score) : '—'}
          </span>
        )}
        
        {/* Gauge bar */}
        <div 
          className="w-full rounded-full overflow-hidden"
          style={{ 
            height: config.barHeight,
            backgroundColor: 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.05)'
          }}
        >
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${fillPercent}%`,
              backgroundColor: color,
              boxShadow: score !== null && score > 50 ? `0 0 8px ${color}40` : 'none'
            }}
          />
        </div>
      </div>
    );
  }
);

ScoreGaugeBadge.displayName = 'ScoreGaugeBadge';

// ═══════════════════════════════════════════════════════════════════════════
// PILL COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface PillProps extends HTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  icon?: React.ReactNode;
}

const Pill = forwardRef<HTMLButtonElement, PillProps>(
  ({ className, active = false, icon, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-full',
          'border transition-all duration-200',
          active
            ? 'bg-accent border-accent text-bg-primary'
            : 'bg-surface border-glass-border text-text-secondary hover:border-accent hover:text-text-primary',
          className
        )}
        {...props}
      >
        {icon}
        {children}
      </button>
    );
  }
);

Pill.displayName = 'Pill';

// ═══════════════════════════════════════════════════════════════════════════
// STATUS DOT COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface StatusDotProps extends HTMLAttributes<HTMLSpanElement> {
  status: 'online' | 'offline' | 'away' | 'busy';
  pulse?: boolean;
}

const StatusDot = forwardRef<HTMLSpanElement, StatusDotProps>(
  ({ className, status, pulse = false, ...props }, ref) => {
    const statusColors = {
      online: 'bg-score-green',
      offline: 'bg-text-muted',
      away: 'bg-score-yellow',
      busy: 'bg-score-red',
    };
    
    return (
      <span
        ref={ref}
        className={cn(
          'inline-block w-2 h-2 rounded-full',
          statusColors[status],
          pulse && 'animate-pulse',
          className
        )}
        {...props}
      />
    );
  }
);

StatusDot.displayName = 'StatusDot';

export { Badge, badgeVariants, ScoreBadge, ScoreGaugeBadge, getScoreColor, Pill, StatusDot };
