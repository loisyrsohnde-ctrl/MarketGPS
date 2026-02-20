'use client';

import { useAuth } from './useAuth';
import { useSubscription } from './useSubscription';

// ═══════════════════════════════════════════════════════════════════════════
// useAccessLevel Hook
// Unified access level system: guest → free → subscriber
// Inspired by TradingView's freemium model
// ═══════════════════════════════════════════════════════════════════════════

export type AccessLevel = 'guest' | 'free' | 'subscriber';

export interface AccessLevelState {
  level: AccessLevel;
  isGuest: boolean;
  isFree: boolean;
  isSubscriber: boolean;
  isAuthenticated: boolean;
  isLoading: boolean;
  user: any;
}

export function useAccessLevel(): AccessLevelState {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { isActive, isLoading: subLoading } = useSubscription();

  const isLoading = authLoading || (isAuthenticated && subLoading);

  let level: AccessLevel = 'guest';
  if (isAuthenticated && isActive) {
    level = 'subscriber';
  } else if (isAuthenticated) {
    level = 'free';
  }

  return {
    level,
    isGuest: level === 'guest',
    isFree: level === 'free',
    isSubscriber: level === 'subscriber',
    isAuthenticated,
    isLoading,
    user,
  };
}

export default useAccessLevel;
