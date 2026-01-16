'use client';

import { forwardRef, useState } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/glass-card';
import { ScoreBadge } from '@/components/ui/badge';
import { ScoreGauge, PillarBar } from '@/components/charts/score-gauge';
import { Star, StarOff, ExternalLink } from 'lucide-react';
import type { Asset } from '@/types';
import { motion } from 'framer-motion';

// ═══════════════════════════════════════════════════════════════════════════
// ASSET CARD COMPONENT
// Premium glassmorphism card for displaying asset details
// ═══════════════════════════════════════════════════════════════════════════

interface AssetCardProps {
  asset: Asset;
  isWatchlisted?: boolean;
  onWatchlistToggle?: (asset: Asset) => void;
  onClick?: (asset: Asset) => void;
  variant?: 'default' | 'compact' | 'detailed';
  className?: string;
}

export function AssetCard({
  asset,
  isWatchlisted = false,
  onWatchlistToggle,
  onClick,
  variant = 'default',
  className,
}: AssetCardProps) {
  const handleWatchlistClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onWatchlistToggle?.(asset);
  };

  if (variant === 'compact') {
    return (
      <CompactAssetCard
        asset={asset}
        isWatchlisted={isWatchlisted}
        onWatchlistToggle={onWatchlistToggle}
        onClick={onClick}
        className={className}
      />
    );
  }

  if (variant === 'detailed') {
    return (
      <DetailedAssetCard
        asset={asset}
        isWatchlisted={isWatchlisted}
        onWatchlistToggle={onWatchlistToggle}
        className={className}
      />
    );
  }

  return (
    <GlassCard
      className={cn('cursor-pointer group', className)}
      onClick={() => onClick?.(asset)}
    >
      <div className="flex items-start justify-between">
        {/* Left: Logo + Info */}
        <div className="flex items-center gap-4">
          <AssetLogo ticker={asset.ticker} size="lg" />
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-text-primary">{asset.ticker}</h3>
              <span className="text-xs px-2 py-0.5 rounded bg-surface text-text-muted">
                {asset.asset_type}
              </span>
            </div>
            <p className="text-sm text-text-secondary line-clamp-1">{asset.name}</p>
          </div>
        </div>

        {/* Right: Score + Actions */}
        <div className="flex items-center gap-3">
          <ScoreBadge score={asset.score_total} size="lg" />
          {onWatchlistToggle && (
            <button
              onClick={handleWatchlistClick}
              className={cn(
                'p-2 rounded-lg transition-all duration-200',
                isWatchlisted
                  ? 'bg-score-yellow/15 text-score-yellow'
                  : 'bg-surface text-text-muted hover:text-score-yellow'
              )}
            >
              {isWatchlisted ? (
                <Star className="w-5 h-5 fill-current" />
              ) : (
                <StarOff className="w-5 h-5" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Pillars */}
      <div className="mt-4 pt-4 border-t border-glass-border space-y-2">
        <PillarBar label="Valeur" value={asset.score_value} icon="📈" />
        <PillarBar label="Momentum" value={asset.score_momentum} icon="🚀" />
        <PillarBar label="Sécurité" value={asset.score_safety} icon="🛡️" />
      </div>
    </GlassCard>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPACT ASSET CARD
// For lists and tables
// ═══════════════════════════════════════════════════════════════════════════

interface CompactAssetCardProps extends Omit<AssetCardProps, 'variant'> {}

function CompactAssetCard({
  asset,
  isWatchlisted,
  onWatchlistToggle,
  onClick,
  className,
}: CompactAssetCardProps) {
  return (
    <motion.div
      className={cn(
        'flex items-center gap-4 p-4 rounded-xl',
        'bg-surface border border-glass-border',
        'cursor-pointer transition-all duration-200',
        'hover:bg-surface-hover hover:border-glass-border-hover',
        className
      )}
      onClick={() => onClick?.(asset)}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <AssetLogo ticker={asset.ticker} size="md" />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-text-primary">{asset.ticker}</span>
          <span className="text-xs text-text-muted">{asset.market_code}</span>
        </div>
        <p className="text-sm text-text-secondary truncate">{asset.name}</p>
      </div>

      <ScoreBadge score={asset.score_total} />

      {onWatchlistToggle && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onWatchlistToggle(asset);
          }}
          className={cn(
            'p-1.5 rounded-lg transition-colors',
            isWatchlisted
              ? 'text-score-yellow'
              : 'text-text-muted hover:text-score-yellow'
          )}
        >
          <Star className={cn('w-4 h-4', isWatchlisted && 'fill-current')} />
        </button>
      )}
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// DETAILED ASSET CARD
// For asset detail pages
// ═══════════════════════════════════════════════════════════════════════════

interface DetailedAssetCardProps extends Omit<AssetCardProps, 'variant' | 'onClick'> {}

function DetailedAssetCard({
  asset,
  isWatchlisted,
  onWatchlistToggle,
  className,
}: DetailedAssetCardProps) {
  return (
    <GlassCard className={cn('space-y-6', className)} padding="lg">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <AssetLogo ticker={asset.ticker} size="xl" />
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-text-primary">{asset.ticker}</h1>
              <span className="px-2.5 py-1 rounded-lg bg-surface text-sm text-text-secondary">
                {asset.asset_type}
              </span>
            </div>
            <p className="text-text-secondary mt-1">{asset.name}</p>
            <p className="text-sm text-text-muted mt-0.5">
              {asset.market_scope} • {asset.market_code}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {onWatchlistToggle && (
            <button
              onClick={() => onWatchlistToggle(asset)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-200',
                isWatchlisted
                  ? 'bg-score-yellow/15 text-score-yellow border border-score-yellow/30'
                  : 'bg-surface text-text-secondary border border-glass-border hover:border-score-yellow hover:text-score-yellow'
              )}
            >
              <Star className={cn('w-4 h-4', isWatchlisted && 'fill-current')} />
              {isWatchlisted ? 'Suivi' : 'Suivre'}
            </button>
          )}
          <Link
            href={`https://finance.yahoo.com/quote/${asset.ticker}`}
            target="_blank"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface text-text-secondary border border-glass-border hover:border-accent hover:text-accent transition-all duration-200"
          >
            <ExternalLink className="w-4 h-4" />
            Yahoo
          </Link>
        </div>
      </div>

      {/* Score Section */}
      <div className="grid grid-cols-2 gap-8">
        <div className="flex flex-col items-center">
          <ScoreGauge score={asset.score_total} size="lg" />
        </div>
        <div className="space-y-4 py-4">
          <PillarBar label="Valeur" value={asset.score_value} icon="📈" />
          <PillarBar label="Momentum" value={asset.score_momentum} icon="🚀" />
          <PillarBar label="Sécurité" value={asset.score_safety} icon="🛡️" />
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-glass-border">
        <KpiCard
          label="Couverture"
          value={asset.coverage}
          unit="%"
          icon="📊"
        />
        <KpiCard
          label="Liquidité"
          value={asset.liquidity !== null ? Math.round(asset.liquidity * 100) : null}
          unit="%"
          icon="💧"
        />
        <KpiCard
          label="Risque FX"
          value={asset.fx_risk !== null ? Math.round(asset.fx_risk * 100) : null}
          unit="%"
          icon="💱"
          variant={asset.fx_risk && asset.fx_risk > 0.5 ? 'warning' : 'default'}
        />
      </div>
    </GlassCard>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// ASSET LOGO COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

import { 
  Building2, Layers, DollarSign, Landmark, BarChart3, 
  Coins, Bitcoin, Leaf, LineChart, Briefcase, TrendingUp 
} from 'lucide-react';

// Currency flags for Forex pairs
const CURRENCY_FLAGS: Record<string, string> = {
  EUR: '🇪🇺', USD: '🇺🇸', GBP: '🇬🇧', JPY: '🇯🇵', CHF: '🇨🇭',
  AUD: '🇦🇺', CAD: '🇨🇦', NZD: '🇳🇿', CNH: '🇨🇳', HKD: '🇭🇰',
  SGD: '🇸🇬', INR: '🇮🇳', MXN: '🇲🇽', ZAR: '🇿🇦', TRY: '🇹🇷',
  SEK: '🇸🇪', NOK: '🇳🇴', BRL: '🇧🇷',
};

// Asset type icons and colors
const ASSET_TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
  EQUITY: { icon: <Building2 className="w-1/2 h-1/2" />, color: 'from-blue-500/30 to-blue-600/10' },
  ETF: { icon: <Layers className="w-1/2 h-1/2" />, color: 'from-purple-500/30 to-purple-600/10' },
  FX: { icon: <DollarSign className="w-1/2 h-1/2" />, color: 'from-green-500/30 to-green-600/10' },
  BOND: { icon: <Landmark className="w-1/2 h-1/2" />, color: 'from-amber-500/30 to-amber-600/10' },
  OPTION: { icon: <BarChart3 className="w-1/2 h-1/2" />, color: 'from-rose-500/30 to-rose-600/10' },
  FUTURE: { icon: <Coins className="w-1/2 h-1/2" />, color: 'from-orange-500/30 to-orange-600/10' },
  CRYPTO: { icon: <Bitcoin className="w-1/2 h-1/2" />, color: 'from-yellow-500/30 to-yellow-600/10' },
  COMMODITY: { icon: <Leaf className="w-1/2 h-1/2" />, color: 'from-emerald-500/30 to-emerald-600/10' },
  INDEX: { icon: <LineChart className="w-1/2 h-1/2" />, color: 'from-cyan-500/30 to-cyan-600/10' },
  FUND: { icon: <Briefcase className="w-1/2 h-1/2" />, color: 'from-indigo-500/30 to-indigo-600/10' },
  DEFAULT: { icon: <TrendingUp className="w-1/2 h-1/2" />, color: 'from-accent-dim to-surface' },
};

// Known crypto tickers (for fallback icon)
const CRYPTO_TICKERS = new Set([
  'BTC', 'ETH', 'XRP', 'BNB', 'SOL', 'DOGE', 'ADA', 'TRX', 'AVAX', 'LINK',
  'TON', 'SHIB', 'DOT', 'BCH', 'LTC', 'XLM', 'UNI', 'ATOM', 'XMR', 'ETC',
  'NEAR', 'APT', 'ARB', 'OP', 'MATIC', 'FTM', 'ALGO', 'VET', 'FIL', 'HBAR',
  'AAVE', 'MKR', 'GRT', 'SAND', 'MANA', 'AXS', 'ENJ', 'CRV', 'SNX', 'COMP',
]);

// Check if ticker is a Forex pair (like EURUSD, GBPJPY)
function isForexPair(ticker: string): boolean {
  if (ticker.length !== 6) return false;
  const base = ticker.substring(0, 3);
  const quote = ticker.substring(3, 6);
  return base in CURRENCY_FLAGS && quote in CURRENCY_FLAGS;
}

// Get Forex pair flags
function getForexFlags(ticker: string): { base: string; quote: string } | null {
  if (!isForexPair(ticker)) return null;
  const base = ticker.substring(0, 3);
  const quote = ticker.substring(3, 6);
  return {
    base: CURRENCY_FLAGS[base] || base,
    quote: CURRENCY_FLAGS[quote] || quote,
  };
}

// Detect asset type from ticker
function detectAssetType(ticker: string): string {
  const upper = ticker.toUpperCase();
  
  // Check crypto
  if (CRYPTO_TICKERS.has(upper)) return 'CRYPTO';
  
  // Check forex
  if (isForexPair(upper)) return 'FX';
  
  // Check common ETF patterns
  if (upper.endsWith('ETF') || ['SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'EEM', 'EFA', 'VEA', 'VWO', 'GLD', 'SLV', 'TLT', 'HYG', 'LQD', 'IEF', 'XLK', 'XLF', 'XLV', 'XLE', 'XLI'].includes(upper)) {
    return 'ETF';
  }
  
  return 'EQUITY';
}

interface AssetLogoProps {
  ticker: string;
  assetType?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export function AssetLogo({ ticker, assetType, size = 'md', className }: AssetLogoProps) {
  const [hasError, setHasError] = useState(false);
  
  const sizeClasses = {
    xs: 'w-6 h-6 text-[10px]',
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg',
  };

  const emojiSizes = {
    xs: 'text-[10px]',
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
    xl: 'text-xl',
  };

  const logoPath = `/logos/${ticker.toUpperCase()}.png`;
  const forexFlags = getForexFlags(ticker);
  
  // Determine asset type for fallback icon
  const effectiveAssetType = assetType || detectAssetType(ticker);
  const typeConfig = ASSET_TYPE_CONFIG[effectiveAssetType] || ASSET_TYPE_CONFIG.DEFAULT;

  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-xl overflow-hidden flex-shrink-0',
        hasError ? `bg-gradient-to-br ${typeConfig.color}` : 'bg-gradient-to-br from-accent-dim to-surface',
        'border border-glass-border',
        sizeClasses[size],
        className
      )}
    >
      {forexFlags ? (
        // Forex pair: show two flags
        <div className={cn('flex items-center gap-px', emojiSizes[size])}>
          <span>{forexFlags.base}</span>
          <span className="opacity-50">/</span>
          <span>{forexFlags.quote}</span>
        </div>
      ) : !hasError ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={logoPath}
          alt={`${ticker} logo`}
          className="w-full h-full object-contain p-1"
          onError={() => setHasError(true)}
        />
      ) : (
        // Fallback: show type-specific icon with colored background
        <div className="text-text-muted">
          {typeConfig.icon}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// KPI CARD COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface KpiCardProps {
  label: string;
  value: number | null;
  unit?: string;
  icon?: string;
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

function KpiCard({ label, value, unit = '', icon, variant = 'default' }: KpiCardProps) {
  const variantColors = {
    default: 'text-accent',
    success: 'text-score-green',
    warning: 'text-score-yellow',
    danger: 'text-score-red',
  };

  return (
    <div className="p-4 rounded-xl bg-surface/50 border border-glass-border">
      <div className="flex items-center gap-2 mb-2">
        {icon && <span className="text-lg">{icon}</span>}
        <span className="text-xs text-text-muted uppercase tracking-wide">{label}</span>
      </div>
      <p className={cn('text-2xl font-bold', variantColors[variant])}>
        {value !== null ? `${value}${unit}` : '—'}
      </p>
    </div>
  );
}

export default AssetCard;
