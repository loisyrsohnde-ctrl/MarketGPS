'use client';

import { Star, TrendingUp, Zap } from 'lucide-react';
import { MorningBriefCard } from './MorningBriefCard';
import { ScoreBadge } from '@/components/ui/badge';
import { motion } from 'framer-motion';
import Link from 'next/link';
import type { Opportunity } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// OPPORTUNITIES WIDGET
// Shows high-potential assets and trending opportunities
// ═══════════════════════════════════════════════════════════════════════════

interface OpportunitiesWidgetProps {
  opportunities: Opportunity[];
  onAddToWatchlist?: (opportunity: Opportunity) => void;
  onViewAll?: () => void;
}

const getOpportunityIcon = (type: string) => {
  switch (type) {
    case 'high_score':
      return <Star className="w-4 h-4" />;
    case 'trending':
      return <TrendingUp className="w-4 h-4" />;
    case 'undervalued':
      return <Zap className="w-4 h-4" />;
    case 'breakout':
      return <TrendingUp className="w-4 h-4" />;
    default:
      return <Star className="w-4 h-4" />;
  }
};

const getOpportunityLabel = (type: string) => {
  switch (type) {
    case 'high_score':
      return 'High Score';
    case 'trending':
      return 'Trending';
    case 'undervalued':
      return 'Undervalued';
    case 'breakout':
      return 'Breakout';
    default:
      return type;
  }
};

export function OpportunitiesWidget({
  opportunities,
  onAddToWatchlist,
  onViewAll,
}: OpportunitiesWidgetProps) {
  const opportunitiesVariants = {
    container: {
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: {
          staggerChildren: 0.08,
          delayChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, y: 10 },
      show: { opacity: 1, y: 0 },
    },
  };

  return (
    <MorningBriefCard
      title="Opportunities"
      icon="⚡"
      actionLabel="Explore"
      onAction={onViewAll}
      variant="highlight"
    >
      {opportunities.length > 0 ? (
        <motion.div
          variants={opportunitiesVariants.container}
          initial="hidden"
          animate="show"
          className="space-y-2"
        >
          {opportunities.slice(0, 5).map((opp) => (
            <motion.div
              key={`${opp.asset.asset_id}-${opp.type}`}
              variants={opportunitiesItem}
              className="p-3 rounded-lg bg-surface/50 hover:bg-surface/80 transition-all duration-200 group"
            >
              <div className="flex items-start justify-between gap-3">
                {/* Left: Asset Info */}
                <div className="flex-1 min-w-0">
                  <Link
                    href={`/asset/${opp.asset.ticker}`}
                    className="flex items-center gap-2 mb-2 hover:opacity-80 transition-opacity"
                  >
                    <div className="text-sm font-bold text-text-primary">
                      {opp.asset.ticker}
                    </div>
                    <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-score-green/20 text-score-green text-xs font-semibold">
                      {getOpportunityIcon(opp.type)}
                      <span>{getOpportunityLabel(opp.type)}</span>
                    </div>
                  </Link>
                  <p className="text-xs text-text-secondary line-clamp-1 mb-2">
                    {opp.asset.name}
                  </p>
                  <p className="text-xs text-text-muted">
                    {opp.reason}
                  </p>
                </div>

                {/* Right: Score & Actions */}
                <div className="flex flex-col items-end gap-2">
                  <ScoreBadge score={opp.asset.score_total} size="sm" />
                  {opp.scoreImprovement && (
                    <div className="text-xs text-score-green font-semibold">
                      +{opp.scoreImprovement.toFixed(1)}
                    </div>
                  )}
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-score-green to-score-blue"
                    initial={{ width: 0 }}
                    animate={{ width: `${opp.confidence}%` }}
                    transition={{ duration: 0.6 }}
                  />
                </div>
                <span className="text-xs font-semibold text-text-primary whitespace-nowrap">
                  {opp.confidence.toFixed(0)}%
                </span>
              </div>

              {/* Add to Watchlist Button */}
              {onAddToWatchlist && (
                <motion.button
                  onClick={() => onAddToWatchlist(opp)}
                  className="mt-2 w-full px-2 py-1.5 rounded text-xs font-semibold text-text-primary bg-score-blue/20 hover:bg-score-blue/30 transition-all duration-200"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  + Add to Watchlist
                </motion.button>
              )}
            </motion.div>
          ))}
        </motion.div>
      ) : (
        <div className="py-8 text-center">
          <p className="text-sm text-text-secondary">No opportunities found</p>
          <p className="text-xs text-text-muted mt-1">Check back later</p>
        </div>
      )}
    </MorningBriefCard>
  );
}

// Animation variant
const opportunitiesVariants = {
  container: {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.1,
      },
    },
  },
  item: {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 },
  },
};

const opportunitiesItem = opportunitiesVariants.item;

export default OpportunitiesWidget;
