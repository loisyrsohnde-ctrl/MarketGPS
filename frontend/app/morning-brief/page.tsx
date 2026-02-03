'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { motion } from 'framer-motion';
import { PortfolioSummary } from '@/components/dashboard/PortfolioSummary';
import { AlertsPreview } from '@/components/dashboard/AlertsPreview';
import { OpportunitiesWidget } from '@/components/dashboard/OpportunitiesWidget';
import { NewsDigest } from '@/components/dashboard/NewsDigest';
import { GamificationWidget } from '@/components/dashboard/GamificationWidget';
import { Loader } from '@/components/ui/loader';
import { RefreshCw } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// MORNING BRIEF PAGE
// Personalized dashboard showing key metrics at a glance
// ═══════════════════════════════════════════════════════════════════════════

export default function MorningBriefPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data, isLoading, error, refetch } = useMorningBrief();

  // Redirect if not authenticated
  if (!authLoading && !isAuthenticated) {
    router.push('/login');
    return null;
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader />
      </div>
    );
  }

  const handleRefresh = async () => {
    await refetch();
  };

  const handleViewPortfolioDetails = () => {
    router.push('/dashboard/wealth');
  };

  const handleViewAllAlerts = () => {
    router.push('/dashboard/alerts');
  };

  const handleViewAllOpportunities = () => {
    router.push('/dashboard/opportunities');
  };

  const handleViewAllNews = () => {
    router.push('/news');
  };

  const handleViewGamification = () => {
    router.push('/dashboard/gamification');
  };

  const handleAddOpportunityToWatchlist = async (opportunity: any) => {
    try {
      const response = await fetch('/api/watchlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: opportunity.asset.ticker,
          notes: `Added from Morning Brief - ${opportunity.type}`,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to add to watchlist');
      }

      // Optionally show success toast
      console.log('Added to watchlist:', opportunity.asset.ticker);
    } catch (err) {
      console.error('Error adding to watchlist:', err);
    }
  };

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader />
      </div>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: 'easeOut',
      },
    },
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="sticky top-0 z-40 backdrop-blur-md bg-bg-primary/80 border-b border-surface/40 px-6 py-4 sm:px-8"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-text-primary">
              {data.greeting.timeOfDay === 'morning' ? 'Good Morning' :
               data.greeting.timeOfDay === 'afternoon' ? 'Good Afternoon' :
               'Good Evening'},
              <span className="text-score-green ml-2">{data.greeting.firstName}</span>
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Here's your personalized market briefing
            </p>
          </div>

          <motion.button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-score-blue/10 hover:bg-score-blue/20 text-score-blue transition-all duration-200 disabled:opacity-50"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">Refresh</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Main Content */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="px-6 py-8 sm:px-8 max-w-7xl mx-auto"
      >
        {/* Error State */}
        {error && (
          <motion.div
            variants={itemVariants}
            className="mb-8 p-4 rounded-lg bg-score-red/10 border border-score-red/30 text-score-red"
          >
            <p className="text-sm font-semibold">Failed to load morning brief</p>
            <p className="text-xs text-score-red/80 mt-1">{error.message}</p>
          </motion.div>
        )}

        {/* Top Row: Portfolio & Alerts */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
        >
          <div className="lg:col-span-2">
            <PortfolioSummary
              metrics={data.portfolio}
              onViewDetails={handleViewPortfolioDetails}
            />
          </div>
          <div className="lg:col-span-1">
            <AlertsPreview
              unreadCount={data.alerts.unreadCount}
              criticalCount={data.alerts.criticalCount}
              recentAlerts={data.alerts.recent}
              onViewAll={handleViewAllAlerts}
            />
          </div>
        </motion.div>

        {/* Middle Row: Opportunities & Gamification */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
        >
          <div className="lg:col-span-2">
            <OpportunitiesWidget
              opportunities={data.opportunities}
              onAddToWatchlist={handleAddOpportunityToWatchlist}
              onViewAll={handleViewAllOpportunities}
            />
          </div>
          <div className="lg:col-span-1">
            <GamificationWidget
              status={data.gamification}
              onViewDetails={handleViewGamification}
            />
          </div>
        </motion.div>

        {/* Bottom Row: News */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1"
        >
          <NewsDigest
            breaking={data.news.breaking}
            important={data.news.important}
            onViewAll={handleViewAllNews}
          />
        </motion.div>
      </motion.div>

      {/* Last Updated */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
        className="fixed bottom-6 right-6 text-xs text-text-muted"
      >
        <p>
          Last updated:{' '}
          {new Date(data.lastUpdated).toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </motion.div>
    </div>
  );
}
