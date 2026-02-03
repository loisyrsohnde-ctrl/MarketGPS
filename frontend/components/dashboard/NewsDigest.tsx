'use client';

import { Flame, TrendingUp, TrendingDown } from 'lucide-react';
import { MorningBriefCard } from './MorningBriefCard';
import { motion } from 'framer-motion';
import { formatRelativeTime } from '@/lib/utils';
import Link from 'next/link';
import type { NewsItem } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// NEWS DIGEST
// Shows important and breaking news
// ═══════════════════════════════════════════════════════════════════════════

interface NewsDigestProps {
  breaking: NewsItem[];
  important: NewsItem[];
  onViewAll?: () => void;
}

const getSentimentIcon = (sentiment: NewsItem['sentiment']) => {
  switch (sentiment) {
    case 'positive':
      return <TrendingUp className="w-4 h-4 text-score-green" />;
    case 'negative':
      return <TrendingDown className="w-4 h-4 text-score-red" />;
    default:
      return <span className="w-4 h-4">—</span>;
  }
};

const getSentimentLabel = (sentiment: NewsItem['sentiment']) => {
  switch (sentiment) {
    case 'positive':
      return 'Bullish';
    case 'negative':
      return 'Bearish';
    default:
      return 'Neutral';
  }
};

interface NewsItemProps {
  news: NewsItem;
  showBreaking?: boolean;
}

const NewsItemComponent = ({ news, showBreaking = false }: NewsItemProps) => {
  return (
    <motion.a
      href={news.url}
      target="_blank"
      rel="noopener noreferrer"
      className="p-3 rounded-lg bg-surface/50 hover:bg-surface/80 transition-all duration-200 group block"
      whileHover={{ y: -2 }}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="mt-0.5">
          {getSentimentIcon(news.sentiment)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className="text-sm font-semibold text-text-primary line-clamp-2 group-hover:text-score-blue transition-colors">
              {news.title}
            </h4>
            {showBreaking && news.isBreaking && (
              <div className="flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold bg-score-red text-white whitespace-nowrap">
                <Flame className="w-3 h-3" />
                <span>Breaking</span>
              </div>
            )}
          </div>

          <p className="text-xs text-text-secondary line-clamp-2 mb-2">
            {news.summary}
          </p>

          <div className="flex items-center justify-between gap-2">
            {/* Source & Sentiment */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-muted">
                {news.source}
              </span>
              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                news.sentiment === 'positive'
                  ? 'bg-score-green/20 text-score-green'
                  : news.sentiment === 'negative'
                  ? 'bg-score-red/20 text-score-red'
                  : 'bg-surface text-text-muted'
              }`}>
                {getSentimentLabel(news.sentiment)}
              </span>
            </div>

            {/* Time */}
            <span className="text-xs text-text-muted">
              {formatRelativeTime(news.publishedAt)}
            </span>
          </div>

          {/* Tickers */}
          {news.tickers.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {news.tickers.slice(0, 3).map((ticker) => (
                <span
                  key={ticker}
                  className="text-xs px-2 py-0.5 rounded-full bg-score-blue/10 text-score-blue font-medium"
                >
                  {ticker}
                </span>
              ))}
              {news.tickers.length > 3 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-surface text-text-muted font-medium">
                  +{news.tickers.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.a>
  );
};

export function NewsDigest({
  breaking,
  important,
  onViewAll,
}: NewsDigestProps) {
  const newsVariants = {
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

  const allNews = [...breaking, ...important];
  const hasNews = allNews.length > 0;

  return (
    <MorningBriefCard
      title="News & Market Updates"
      icon={breaking.length > 0 ? '🔥' : '📰'}
      actionLabel="Read All"
      onAction={onViewAll}
      variant={breaking.length > 0 ? 'highlight' : 'default'}
    >
      {hasNews ? (
        <motion.div
          variants={newsVariants.container}
          initial="hidden"
          animate="show"
          className="space-y-2"
        >
          {/* Breaking News Section */}
          {breaking.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-score-red mb-2 flex items-center gap-1">
                <Flame className="w-3 h-3" />
                Breaking News
              </h4>
              <div className="space-y-2">
                {breaking.slice(0, 2).map((news) => (
                  <motion.div
                    key={news.id}
                    variants={newsVariants.item}
                  >
                    <NewsItemComponent news={news} showBreaking={true} />
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Important News Section */}
          {important.length > 0 && breaking.length > 0 && (
            <div className="pt-2 border-t border-surface" />
          )}

          {important.length > 0 && (
            <div>
              {breaking.length > 0 && (
                <h4 className="text-xs font-bold text-text-primary mb-2">
                  Important News
                </h4>
              )}
              <div className="space-y-2">
                {important.slice(0, breaking.length > 0 ? 2 : 4).map((news) => (
                  <motion.div
                    key={news.id}
                    variants={newsVariants.item}
                  >
                    <NewsItemComponent news={news} showBreaking={false} />
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      ) : (
        <div className="py-8 text-center">
          <p className="text-sm text-text-secondary">No news at the moment</p>
          <p className="text-xs text-text-muted mt-1">Check back later</p>
        </div>
      )}
    </MorningBriefCard>
  );
}

export default NewsDigest;
