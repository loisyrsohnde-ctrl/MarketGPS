'use client';

import { useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { track } from '@/lib/analytics';
import { shareBriefOnWhatsApp } from '@/lib/share';
import { useMorningBrief } from '@/hooks/useMorningBrief';
import { motion } from 'framer-motion';
import { PortfolioSummary } from '@/components/dashboard/PortfolioSummary';
import { AlertsPreview } from '@/components/dashboard/AlertsPreview';
import { OpportunitiesWidget } from '@/components/dashboard/OpportunitiesWidget';
import { NewsDigest } from '@/components/dashboard/NewsDigest';
import { GamificationWidget } from '@/components/dashboard/GamificationWidget';
import { AccessGate } from '@/components/AccessGate';
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

  // Track morning brief view
  useEffect(() => {
    if (isAuthenticated && data) {
      track.morningBriefView();
    }
  }, [isAuthenticated, data]);

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

          <div className="flex items-center gap-2">
            <motion.button
              onClick={() => {
                shareBriefOnWhatsApp();
                track.shareAction('whatsapp', 'brief');
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 transition-all duration-200"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              <span className="text-sm font-medium hidden sm:inline">WhatsApp</span>
            </motion.button>
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

        {/* Top Row: Portfolio & Alerts — Pro only */}
        <AccessGate requiredLevel="subscriber" feature="Briefing personnalisé" blurContent>
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
        </AccessGate>

        {/* Middle Row: Opportunities (Pro) & Gamification (free) */}
        <motion.div
          variants={itemVariants}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6"
        >
          <div className="lg:col-span-2">
            <AccessGate requiredLevel="subscriber" feature="Opportunités du jour" blurContent>
              <OpportunitiesWidget
                opportunities={data.opportunities}
                onAddToWatchlist={handleAddOpportunityToWatchlist}
                onViewAll={handleViewAllOpportunities}
              />
            </AccessGate>
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
            timeZone: 'UTC',
          })}
        </p>
      </motion.div>
    </div>
  );
}
