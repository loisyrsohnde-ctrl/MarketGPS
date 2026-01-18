'use client';

/**
 * Institutional Badges Component
 * ADD-ON v2.0 - Displays liquidity, data quality, and horizon warnings
 * 
 * Usage:
 *   <LiquidityBadge tier="D" flag={true} />
 *   <DataQualityBadge flag={true} score={45} />
 *   <HorizonBadge years={3} />
 *   <InstitutionalWarnings asset={asset} />
 */

import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import {
  AlertTriangle,
  Droplets,
  Clock,
  ShieldAlert,
  TrendingDown,
  Info,
  CheckCircle,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// LIQUIDITY TIER BADGE
// ═══════════════════════════════════════════════════════════════════════════

interface LiquidityTierBadgeProps extends HTMLAttributes<HTMLDivElement> {
  tier: 'A' | 'B' | 'C' | 'D' | null;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

const tierConfig = {
  A: {
    label: 'Institutionnel',
    color: 'text-score-green',
    bgColor: 'bg-score-green/10',
    borderColor: 'border-score-green/30',
    icon: CheckCircle,
  },
  B: {
    label: 'Bonne liquidité',
    color: 'text-score-light-green',
    bgColor: 'bg-score-light-green/10',
    borderColor: 'border-score-light-green/30',
    icon: CheckCircle,
  },
  C: {
    label: 'Liquidité limitée',
    color: 'text-score-yellow',
    bgColor: 'bg-score-yellow/10',
    borderColor: 'border-score-yellow/30',
    icon: AlertTriangle,
  },
  D: {
    label: 'Illiquide',
    color: 'text-score-red',
    bgColor: 'bg-score-red/10',
    borderColor: 'border-score-red/30',
    icon: AlertTriangle,
  },
};

export const LiquidityTierBadge = forwardRef<HTMLDivElement, LiquidityTierBadgeProps>(
  ({ tier, showLabel = true, size = 'md', className, ...props }, ref) => {
    if (!tier) return null;
    
    const config = tierConfig[tier];
    const Icon = config.icon;
    
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1',
      md: 'px-2 py-1 text-xs gap-1.5',
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md border font-medium',
          sizeClasses[size],
          config.bgColor,
          config.borderColor,
          config.color,
          className
        )}
        title={`Liquidité: Tier ${tier} - ${config.label}`}
        {...props}
      >
        <Droplets className={cn(size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5')} />
        <span>Tier {tier}</span>
        {showLabel && <span className="opacity-75">({config.label})</span>}
      </div>
    );
  }
);

LiquidityTierBadge.displayName = 'LiquidityTierBadge';

// ═══════════════════════════════════════════════════════════════════════════
// LIQUIDITY WARNING BADGE (for flagged assets)
// ═══════════════════════════════════════════════════════════════════════════

interface LiquidityFlagBadgeProps extends HTMLAttributes<HTMLDivElement> {
  flag?: boolean | null;
  advUsd?: number | null;
  size?: 'sm' | 'md';
}

export const LiquidityFlagBadge = forwardRef<HTMLDivElement, LiquidityFlagBadgeProps>(
  ({ flag, advUsd, size = 'md', className, ...props }, ref) => {
    if (!flag) return null;
    
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1',
      md: 'px-2 py-1 text-xs gap-1.5',
    };
    
    const advText = advUsd 
      ? `ADV: $${advUsd >= 1_000_000 ? (advUsd / 1_000_000).toFixed(1) + 'M' : (advUsd / 1000).toFixed(0) + 'K'}`
      : '';
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md border font-semibold',
          'bg-score-red/10 border-score-red/30 text-score-red',
          sizeClasses[size],
          className
        )}
        title={`Attention: Liquidité insuffisante ${advText}`}
        {...props}
      >
        <TrendingDown className={cn(size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5')} />
        <span>LOW LIQUIDITY</span>
      </div>
    );
  }
);

LiquidityFlagBadge.displayName = 'LiquidityFlagBadge';

// ═══════════════════════════════════════════════════════════════════════════
// DATA QUALITY WARNING BADGE
// ═══════════════════════════════════════════════════════════════════════════

interface DataQualityBadgeProps extends HTMLAttributes<HTMLDivElement> {
  flag?: boolean | null;
  score?: number | null;
  size?: 'sm' | 'md';
}

export const DataQualityBadge = forwardRef<HTMLDivElement, DataQualityBadgeProps>(
  ({ flag, score, size = 'md', className, ...props }, ref) => {
    if (!flag) return null;
    
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1',
      md: 'px-2 py-1 text-xs gap-1.5',
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md border font-semibold',
          'bg-score-yellow/10 border-score-yellow/30 text-score-yellow',
          sizeClasses[size],
          className
        )}
        title={`Attention: Qualité des données insuffisante${score ? ` (${score.toFixed(0)}%)` : ''}`}
        {...props}
      >
        <ShieldAlert className={cn(size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5')} />
        <span>DATA RISK</span>
      </div>
    );
  }
);

DataQualityBadge.displayName = 'DataQualityBadge';

// ═══════════════════════════════════════════════════════════════════════════
// STALE PRICE BADGE
// ═══════════════════════════════════════════════════════════════════════════

interface StalePriceBadgeProps extends HTMLAttributes<HTMLDivElement> {
  flag?: boolean | null;
  size?: 'sm' | 'md';
}

export const StalePriceBadge = forwardRef<HTMLDivElement, StalePriceBadgeProps>(
  ({ flag, size = 'md', className, ...props }, ref) => {
    if (!flag) return null;
    
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1',
      md: 'px-2 py-1 text-xs gap-1.5',
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md border font-semibold',
          'bg-score-yellow/10 border-score-yellow/30 text-score-yellow',
          sizeClasses[size],
          className
        )}
        title="Attention: Prix potentiellement obsolète"
        {...props}
      >
        <Clock className={cn(size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5')} />
        <span>STALE</span>
      </div>
    );
  }
);

StalePriceBadge.displayName = 'StalePriceBadge';

// ═══════════════════════════════════════════════════════════════════════════
// RECOMMENDED HORIZON BADGE
// ═══════════════════════════════════════════════════════════════════════════

interface HorizonBadgeProps extends HTMLAttributes<HTMLDivElement> {
  years?: number | null;
  size?: 'sm' | 'md';
}

const horizonConfig: Record<number, { label: string; color: string; bgColor: string }> = {
  1: { label: 'Court terme', color: 'text-score-red', bgColor: 'bg-score-red/10' },
  3: { label: 'Moyen terme', color: 'text-score-yellow', bgColor: 'bg-score-yellow/10' },
  5: { label: 'Long terme', color: 'text-score-light-green', bgColor: 'bg-score-light-green/10' },
  10: { label: 'Très long terme', color: 'text-score-green', bgColor: 'bg-score-green/10' },
};

export const HorizonBadge = forwardRef<HTMLDivElement, HorizonBadgeProps>(
  ({ years, size = 'md', className, ...props }, ref) => {
    if (!years) return null;
    
    // Get config for closest horizon
    const horizonKey = years <= 1 ? 1 : years <= 3 ? 3 : years <= 5 ? 5 : 10;
    const config = horizonConfig[horizonKey];
    
    const sizeClasses = {
      sm: 'px-1.5 py-0.5 text-[10px] gap-1',
      md: 'px-2 py-1 text-xs gap-1.5',
    };
    
    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-md font-medium',
          sizeClasses[size],
          config.bgColor,
          config.color,
          className
        )}
        title={`Horizon d'investissement recommandé: ${years} an${years > 1 ? 's' : ''} minimum`}
        {...props}
      >
        <Clock className={cn(size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5')} />
        <span>Horizon: {years}+ ans</span>
      </div>
    );
  }
);

HorizonBadge.displayName = 'HorizonBadge';

// ═══════════════════════════════════════════════════════════════════════════
// INSTITUTIONAL SCORE BADGE
// ═══════════════════════════════════════════════════════════════════════════

interface InstitutionalScoreBadgeProps extends HTMLAttributes<HTMLDivElement> {
  scoreTotal?: number | null;
  scoreInstitutional?: number | null;
  showDiff?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const InstitutionalScoreBadge = forwardRef<HTMLDivElement, InstitutionalScoreBadgeProps>(
  ({ scoreTotal, scoreInstitutional, showDiff = true, size = 'md', className, ...props }, ref) => {
    if (scoreInstitutional === null || scoreInstitutional === undefined) return null;
    
    const diff = scoreTotal && scoreInstitutional ? scoreTotal - scoreInstitutional : 0;
    const hasPenalty = diff > 0;
    
    const sizeClasses = {
      sm: 'text-xs',
      md: 'text-sm',
      lg: 'text-base',
    };
    
    return (
      <div
        ref={ref}
        className={cn('inline-flex items-center gap-2', sizeClasses[size], className)}
        {...props}
      >
        <span className="font-bold text-accent">{scoreInstitutional.toFixed(0)}</span>
        {showDiff && hasPenalty && (
          <span className="text-score-red text-[0.85em]">
            (-{diff.toFixed(0)})
          </span>
        )}
      </div>
    );
  }
);

InstitutionalScoreBadge.displayName = 'InstitutionalScoreBadge';

// ═══════════════════════════════════════════════════════════════════════════
// COMBINED INSTITUTIONAL WARNINGS
// ═══════════════════════════════════════════════════════════════════════════

interface InstitutionalWarningsProps extends HTMLAttributes<HTMLDivElement> {
  asset: {
    liquidity_flag?: boolean | null;
    data_quality_flag?: boolean | null;
    stale_price_flag?: boolean | null;
    liquidity_tier?: 'A' | 'B' | 'C' | 'D' | null;
    min_recommended_horizon_years?: number | null;
    adv_usd?: number | null;
    data_quality_score?: number | null;
  };
  showTier?: boolean;
  showHorizon?: boolean;
  size?: 'sm' | 'md';
  layout?: 'inline' | 'stack';
}

export const InstitutionalWarnings = forwardRef<HTMLDivElement, InstitutionalWarningsProps>(
  ({ asset, showTier = true, showHorizon = true, size = 'sm', layout = 'inline', className, ...props }, ref) => {
    const hasWarnings = asset.liquidity_flag || asset.data_quality_flag || asset.stale_price_flag;
    
    // Don't render if no warnings and not showing tier/horizon
    if (!hasWarnings && !showTier && !showHorizon) return null;
    
    const layoutClasses = {
      inline: 'flex flex-wrap items-center gap-1.5',
      stack: 'flex flex-col gap-1',
    };
    
    return (
      <div
        ref={ref}
        className={cn(layoutClasses[layout], className)}
        {...props}
      >
        {/* Flags (always show if present) */}
        <LiquidityFlagBadge flag={asset.liquidity_flag} advUsd={asset.adv_usd} size={size} />
        <DataQualityBadge flag={asset.data_quality_flag} score={asset.data_quality_score} size={size} />
        <StalePriceBadge flag={asset.stale_price_flag} size={size} />
        
        {/* Tier (optional) */}
        {showTier && asset.liquidity_tier && (
          <LiquidityTierBadge tier={asset.liquidity_tier} showLabel={false} size={size} />
        )}
        
        {/* Horizon (optional) */}
        {showHorizon && asset.min_recommended_horizon_years && (
          <HorizonBadge years={asset.min_recommended_horizon_years} size={size} />
        )}
      </div>
    );
  }
);

InstitutionalWarnings.displayName = 'InstitutionalWarnings';

// ═══════════════════════════════════════════════════════════════════════════
// RANKING MODE TOGGLE
// ═══════════════════════════════════════════════════════════════════════════

interface RankingModeToggleProps {
  mode: 'total' | 'institutional';
  onChange: (mode: 'total' | 'institutional') => void;
  className?: string;
}

export function RankingModeToggle({ mode, onChange, className }: RankingModeToggleProps) {
  return (
    <div className={cn('inline-flex rounded-lg border border-glass-border p-1 bg-surface', className)}>
      <button
        onClick={() => onChange('total')}
        className={cn(
          'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
          mode === 'total'
            ? 'bg-accent text-white'
            : 'text-text-secondary hover:text-text-primary'
        )}
      >
        Score Global
      </button>
      <button
        onClick={() => onChange('institutional')}
        className={cn(
          'px-3 py-1.5 text-sm font-medium rounded-md transition-all flex items-center gap-1.5',
          mode === 'institutional'
            ? 'bg-accent text-white'
            : 'text-text-secondary hover:text-text-primary'
        )}
      >
        <ShieldAlert className="w-3.5 h-3.5" />
        Institutionnel
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════════════════

export {
  tierConfig,
  horizonConfig,
};
