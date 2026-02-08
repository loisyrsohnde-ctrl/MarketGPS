/**
 * useGamification - Hook for managing gamification state and API interactions
 * Fetches user progress, badges, objectives, leaderboard, and records actions
 */

import { useState, useCallback, useEffect } from 'react';
import {
  GamificationProfile,
  Badge,
  Objective,
  LeaderboardEntry,
  GamificationAction,
} from '@/types/gamification';

interface UseGamificationReturn {
  // State
  profile: GamificationProfile | null;
  badges: Badge[] | null;
  objectives: Objective[] | null;
  leaderboard: LeaderboardEntry[] | null;
  loading: boolean;
  error: string | null;

  // Methods
  fetchProfile: () => Promise<void>;
  fetchBadges: () => Promise<void>;
  fetchObjectives: () => Promise<void>;
  fetchLeaderboard: (limit?: number) => Promise<void>;
  recordAction: (action: GamificationAction) => Promise<void>;
  refetch: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export function useGamification(): UseGamificationReturn {
  const [profile, setProfile] = useState<GamificationProfile | null>(null);
  const [badges, setBadges] = useState<Badge[] | null>(null);
  const [objectives, setObjectives] = useState<Objective[] | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch user gamification profile
   */
  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE}/api/gamification/progress`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch gamification profile');
      }

      const data = await response.json();
      setProfile(data.data || data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch gamification profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetch all badges with earned status
   */
  const fetchBadges = useCallback(async () => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE}/api/gamification/badges`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch badges');
      }

      const data = await response.json();
      setBadges(data.data || data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch badges:', err);
    }
  }, []);

  /**
   * Fetch current objectives
   */
  const fetchObjectives = useCallback(async () => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE}/api/gamification/objectives`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch objectives');
      }

      const data = await response.json();
      setObjectives(data.data || data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch objectives:', err);
    }
  }, []);

  /**
   * Fetch leaderboard
   */
  const fetchLeaderboard = useCallback(async (limit: number = 20) => {
    try {
      setError(null);

      const response = await fetch(
        `${API_BASE}/api/gamification/leaderboard?limit=${limit}`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }

      const data = await response.json();
      setLeaderboard(data.data || data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch leaderboard:', err);
    }
  }, []);

  /**
   * Record a user action and earn points
   */
  const recordAction = useCallback(async (action: GamificationAction) => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE}/api/gamification/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(action),
      });

      if (!response.ok) {
        throw new Error('Failed to record action');
      }

      const data = await response.json();

      // Update profile with new data after action
      if (data.data?.profile) {
        setProfile(data.data.profile);
      }

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to record action:', err);
      throw err;
    }
  }, []);

  /**
   * Refetch all gamification data
   */
  const refetch = useCallback(async () => {
    await Promise.all([
      fetchProfile(),
      fetchBadges(),
      fetchObjectives(),
      fetchLeaderboard(),
    ]);
  }, [fetchProfile, fetchBadges, fetchObjectives, fetchLeaderboard]);

  // Load initial data on mount
  useEffect(() => {
    refetch();
  }, [refetch]);

  return {
    profile,
    badges,
    objectives,
    leaderboard,
    loading,
    error,
    fetchProfile,
    fetchBadges,
    fetchObjectives,
    fetchLeaderboard,
    recordAction,
    refetch,
  };
}
