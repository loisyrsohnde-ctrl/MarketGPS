'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from './useAuth';
import { useUserProfile } from './useUserProfile';
import type { MorningBriefData, UseMorningBriefResponse } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// useMorningBrief Hook
// Fetches and aggregates all morning brief data
// ═══════════════════════════════════════════════════════════════════════════

const DEFAULT_MORNING_BRIEF: MorningBriefData = {
  greeting: {
    firstName: 'User',
    timeOfDay: 'morning',
  },
  portfolio: {
    totalValue: 0,
    dayChange: 0,
    dayChangePercent: 0,
    weekChange: 0,
    weekChangePercent: 0,
    monthChange: 0,
    monthChangePercent: 0,
    averageScore: 0,
    topGainers: [],
    topLosers: [],
    diversificationScore: 0,
    riskScore: 0,
  },
  alerts: {
    unreadCount: 0,
    recent: [],
    criticalCount: 0,
  },
  opportunities: [],
  news: {
    breaking: [],
    important: [],
  },
  gamification: {
    level: 'novice',
    points: 0,
    weeklyPoints: 0,
    weeklyTarget: 500,
    objectives: [],
    streakDays: 0,
  },
  lastUpdated: new Date().toISOString(),
};

export function useMorningBrief(): UseMorningBriefResponse {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { profile: userProfile, loading: profileLoading } = useUserProfile();
  const [data, setData] = useState<MorningBriefData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Determine time of day for greeting
  const getTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 18) return 'afternoon';
    return 'evening';
  };

  // Fetch portfolio metrics
  const fetchPortfolioMetrics = async () => {
    try {
      const response = await fetch('/api/portfolio/metrics');
      if (!response.ok) throw new Error('Failed to fetch portfolio metrics');
      return await response.json();
    } catch (err) {
      console.error('Error fetching portfolio metrics:', err);
      return DEFAULT_MORNING_BRIEF.portfolio;
    }
  };

  // Fetch alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/alerts?limit=3');
      if (!response.ok) throw new Error('Failed to fetch alerts');
      return await response.json();
    } catch (err) {
      console.error('Error fetching alerts:', err);
      return DEFAULT_MORNING_BRIEF.alerts;
    }
  };

  // Fetch opportunities
  const fetchOpportunities = async () => {
    try {
      const response = await fetch('/api/opportunities?limit=5');
      if (!response.ok) throw new Error('Failed to fetch opportunities');
      return await response.json();
    } catch (err) {
      console.error('Error fetching opportunities:', err);
      return [];
    }
  };

  // Fetch news digest
  const fetchNewsDigest = async () => {
    try {
      const response = await fetch('/api/news/digest?limit=5');
      if (!response.ok) throw new Error('Failed to fetch news');
      return await response.json();
    } catch (err) {
      console.error('Error fetching news digest:', err);
      return DEFAULT_MORNING_BRIEF.news;
    }
  };

  // Fetch gamification data
  const fetchGamification = async () => {
    try {
      const response = await fetch('/api/gamification/status');
      if (!response.ok) throw new Error('Failed to fetch gamification data');
      return await response.json();
    } catch (err) {
      console.error('Error fetching gamification:', err);
      return DEFAULT_MORNING_BRIEF.gamification;
    }
  };

  // Main data fetching function
  const fetchMorningBriefData = useCallback(async () => {
    if (!isAuthenticated || authLoading || profileLoading) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Fetch all data in parallel
      const [portfolio, alerts, opportunities, news, gamification] = await Promise.all([
        fetchPortfolioMetrics(),
        fetchAlerts(),
        fetchOpportunities(),
        fetchNewsDigest(),
        fetchGamification(),
      ]);

      // Construct complete morning brief data
      const briefData: MorningBriefData = {
        greeting: {
          firstName: userProfile?.displayName?.split(' ')[0] || 'User',
          timeOfDay: getTimeOfDay(),
        },
        portfolio,
        alerts,
        opportunities,
        news,
        gamification,
        lastUpdated: new Date().toISOString(),
      };

      setData(briefData);
    } catch (err) {
      const errorObj = err instanceof Error ? err : new Error('Unknown error');
      setError(errorObj);
      console.error('Error fetching morning brief:', err);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, authLoading, profileLoading, userProfile]);

  // Fetch data on mount and when auth changes
  useEffect(() => {
    if (!authLoading && !profileLoading) {
      fetchMorningBriefData();
    }
  }, [isAuthenticated, authLoading, profileLoading, fetchMorningBriefData]);

  // Refetch function for manual refresh
  const refetch = useCallback(async () => {
    await fetchMorningBriefData();
  }, [fetchMorningBriefData]);

  return {
    data,
    isLoading: isLoading || authLoading || profileLoading,
    error,
    refetch,
  };
}

export default useMorningBrief;
