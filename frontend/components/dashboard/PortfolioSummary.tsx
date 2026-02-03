'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';
import { MorningBriefCard } from './MorningBriefCard';
import { ScoreBadge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import type { PortfolioMetrics } from '@/types/morning-brief';
import { formatCurrency, formatPercent } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// PORTFOLIO SUMMARY
// Shows portfolio performance and key metrics
// ═══════════════════════════════════════════════════════════════════════════

interface PortfolioSummaryProps {
  metrics: PortfolioMetrics;
  onViewDetails?: () => void;
}

export function PortfolioSummary({ metrics, onViewDetails }: PortfolioSummaryProps) {
  const performanceVariants = {
    container: {
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
          delayChildren: 0.2,
        },
      },
    },
    item: {
      hidden: { opacity: 0, x: -20 },
      show: { opacity: 1, x: 0 },
    },
  };

  const PerformanceMetric = ({
    label,
    value,
    change,
    changePercent,
    timeframe,
  }: {
    label: string;
    value: number;
    change: number;
    changePercent: number;
    timeframe: string;
  }) => {
    const isPositive = change >= 0;
    return (
      <motion.div
        variants={performanceVariants.item}
        className="flex flex-col gap-2 p-3 rounded-lg bg-surface/50"
      >
        <span className="text-xs text-text-secondary">{label}</span>
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold text-text-primary">
            {formatCurrency(value)}
          </span>
          <div
            className={`flex items-center gap-1 text-xs font-medium ${
              isPositive ? 'text-score-green' : 'text-score-red'
            }`}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span>
              {Math.abs(change)} ({isPositive ? '+' : ''}{formatPercent(changePercent)})
            </span>
          </div>
        </div>
        <span className="text-xs text-text-muted">{timeframe}</span>
      </motion.div>
    );
  };

  return (
    <MorningBriefCard
      title="Portfolio Performance"
      icon="📊"
      actionLabel="View Details"
      onAction={onViewDetails}
      variant="highlight"
    >
      <motion.div
        variants={performanceVariants.container}
        initial="hidden"
        animate="show"
        className="flex flex-col gap-4"
      >
        {/* Total Value */}
        <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-score-green/10 to-transparent border border-score-green/20">
          <div>
            <p className="text-xs text-text-secondary mb-1">Total Value</p>
            <p className="text-2xl font-bold text-text-primary">
              {formatCurrency(metrics.totalValue)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-text-secondary mb-1">Avg Score</p>
            <div className="flex justify-end">
              <ScoreBadge score={metrics.averageScore} size="lg" />
            </div>
          </div>
        </div>

        {/* Performance Grid */}
        <div className="grid grid-cols-3 gap-2">
          <PerformanceMetric
            label="Day"
            value={Math.abs(metrics.dayChange)}
            change={metrics.dayChange}
            changePercent={metrics.dayChangePercent}
            timeframe="Today"
          />
          <PerformanceMetric
            label="Week"
            value={Math.abs(metrics.weekChange)}
            change={metrics.weekChange}
            changePercent={metrics.weekChangePercent}
            timeframe="7 Days"
          />
          <PerformanceMetric
            label="Month"
            value={Math.abs(metrics.monthChange)}
            change={metrics.monthChange}
            changePercent={metrics.monthChangePercent}
            timeframe="30 Days"
          />
        </div>

        {/* Top Performers */}
        {(metrics.topGainers.length > 0 || metrics.topLosers.length > 0) && (
          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-surface">
            {/* Top Gainers */}
            {metrics.topGainers.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-xs font-semibold text-score-green">Top Gainers</p>
                <div className="space-y-1">
                  {metrics.topGainers.slice(0, 2).map((asset) => (
                    <div key={asset.asset_id} className="flex items-center justify-between text-xs">
                      <span className="font-medium text-text-primary">{asset.ticker}</span>
                      <span className="text-score-green">
                        +{asset.score_total?.toFixed(1) || 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Losers */}
            {metrics.topLosers.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-xs font-semibold text-score-red">Top Losers</p>
                <div className="space-y-1">
                  {metrics.topLosers.slice(0, 2).map((asset) => (
                    <div key={asset.asset_id} className="flex items-center justify-between text-xs">
                      <span className="font-medium text-text-primary">{asset.ticker}</span>
                      <span className="text-score-red">
                        {asset.score_total?.toFixed(1) || 'N/A'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Risk & Diversification */}
        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-surface">
          <div className="flex flex-col gap-2">
            <p className="text-xs text-text-secondary">Diversification</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-score-green to-score-blue"
                  initial={{ width: 0 }}
                  animate={{ width: `${metrics.diversificationScore}%` }}
                  transition={{ duration: 0.8 }}
                />
              </div>
              <span className="text-xs font-semibold text-text-primary">
                {metrics.diversificationScore.toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <p className="text-xs text-text-secondary">Risk Score</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-score-yellow to-score-red"
                  initial={{ width: 0 }}
                  animate={{ width: `${metrics.riskScore}%` }}
                  transition={{ duration: 0.8 }}
                />
              </div>
              <span className="text-xs font-semibold text-text-primary">
                {metrics.riskScore.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </motion.div>
    </MorningBriefCard>
  );
}

export default PortfolioSummary;
