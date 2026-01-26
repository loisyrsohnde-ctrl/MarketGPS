'use client';

import { useEffect, useState, useCallback } from 'react';
import { useAuth } from './useAuth';

// ═══════════════════════════════════════════════════════════════════════════
// useSubscription Hook
// Provides subscription status for paywall and feature gating
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

export interface SubscriptionState {
  plan: 'free' | 'monthly' | 'annual';
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'inactive';
  isActive: boolean;  // True if user should have access (includes grace period)
  isLoading: boolean;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
  gracePeriodRemainingHours: number | null;
}

export function useSubscription() {
  const { session, isLoading: authLoading, isAuthenticated } = useAuth();

  const [state, setState] = useState<SubscriptionState>({
    plan: 'free',
    status: 'inactive',
    isActive: false,
    isLoading: true,
    currentPeriodEnd: null,
    cancelAtPeriodEnd: false,
    gracePeriodRemainingHours: null,
  });

  const fetchSubscription = useCallback(async () => {
    if (!session?.access_token) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        isActive: false,
        plan: 'free',
        status: 'inactive',
      }));
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/billing/me`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch subscription');
      }

      const data = await response.json();

      setState({
        plan: data.plan || 'free',
        status: data.status || 'inactive',
        isActive: data.is_active || false,
        isLoading: false,
        currentPeriodEnd: data.current_period_end || null,
        cancelAtPeriodEnd: data.cancel_at_period_end || false,
        gracePeriodRemainingHours: data.grace_period_remaining_hours || null,
      });
    } catch (error) {
      console.error('Error fetching subscription:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
      }));
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        isActive: false,
        plan: 'free',
        status: 'inactive',
      }));
      return;
    }

    fetchSubscription();
  }, [authLoading, isAuthenticated, fetchSubscription]);

  return {
    ...state,
    refetch: fetchSubscription,
  };
}

export default useSubscription;
