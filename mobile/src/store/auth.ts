/**
 * MarketGPS Mobile - Auth Store (Zustand)
 */

import { create } from 'zustand';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import { api, SubscriptionStatus } from '@/lib/api';
import { Platform } from 'react-native';

interface AuthState {
  session: Session | null;
  user: User | null;
  subscription: SubscriptionStatus | null;
  hasLocalApplePurchase: boolean;
  isLoading: boolean;
  isInitialized: boolean;

  // Actions
  initialize: () => Promise<void>;
  setSession: (session: Session | null) => void;
  refreshSubscription: () => Promise<void>;
  checkLocalApplePurchase: () => Promise<void>;
  setLocalApplePurchase: (value: boolean) => void;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  user: null,
  subscription: null,
  hasLocalApplePurchase: false,
  isLoading: true,
  isInitialized: false,

  initialize: async () => {
    try {
      set({ isLoading: true });

      // Get current session
      const { data: { session } } = await supabase.auth.getSession();

      set({
        session,
        user: session?.user ?? null,
        isInitialized: true,
      });

      // Fetch subscription if logged in
      if (session) {
        get().refreshSubscription();
      }

      // Check local Apple purchases (works without auth - uses Apple ID)
      get().checkLocalApplePurchase();

      // Listen for auth changes
      supabase.auth.onAuthStateChange(async (event, session) => {
        set({
          session,
          user: session?.user ?? null,
        });

        if (session) {
          get().refreshSubscription();
        } else {
          set({ subscription: null });
        }
      });
    } catch (error) {
      if (__DEV__) console.error('Auth initialization error:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  setSession: (session) => {
    set({
      session,
      user: session?.user ?? null,
    });
  },

  refreshSubscription: async () => {
    try {
      const subscription = await api.getSubscriptionStatus();
      set({ subscription });
    } catch (error) {
      if (__DEV__) console.error('Failed to fetch subscription:', error);
      // Default to free plan on error
      set({
        subscription: {
          user_id: get().user?.id ?? '',
          plan: 'free',
          status: 'inactive',
          current_period_end: null,
          cancel_at_period_end: false,
          is_active: false,
          grace_period_remaining_hours: null,
        },
      });
    }
  },

  checkLocalApplePurchase: async () => {
    if (Platform.OS !== 'ios') return;
    try {
      const { initIAP, restorePurchases, hasProSubscription, closeIAP } = await import('@/lib/iap');
      const connected = await initIAP();
      if (!connected) return;
      const purchases = await restorePurchases();
      set({ hasLocalApplePurchase: hasProSubscription(purchases) });
      await closeIAP();
    } catch (error) {
      if (__DEV__) console.warn('Local Apple purchase check failed:', error);
    }
  },

  setLocalApplePurchase: (value: boolean) => {
    set({ hasLocalApplePurchase: value });
  },

  signOut: async () => {
    try {
      await supabase.auth.signOut();
      set({
        session: null,
        user: null,
        subscription: null,
      });
    } catch (error) {
      if (__DEV__) console.error('Sign out error:', error);
      throw error;
    }
  },
}));

// Selectors
export const useSession = () => useAuthStore((state) => state.session);
export const useUser = () => useAuthStore((state) => state.user);
export const useSubscription = () => useAuthStore((state) => state.subscription);
export const useIsAuthenticated = () => useAuthStore((state) => !!state.session);
export const useIsPro = () => useAuthStore((state) =>
  (state.subscription?.is_active ?? false) || state.hasLocalApplePurchase
);
