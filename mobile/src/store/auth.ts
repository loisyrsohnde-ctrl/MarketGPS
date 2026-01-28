/**
 * MarketGPS Mobile - Auth Store (Zustand)
 */

import { create } from 'zustand';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import { api, SubscriptionStatus } from '@/lib/api';

interface AuthState {
  session: Session | null;
  user: User | null;
  subscription: SubscriptionStatus | null;
  isLoading: boolean;
  isInitialized: boolean;
  
  // Actions
  initialize: () => Promise<void>;
  setSession: (session: Session | null) => void;
  refreshSubscription: () => Promise<void>;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  session: null,
  user: null,
  subscription: null,
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
      console.error('Auth initialization error:', error);
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
      console.error('Failed to fetch subscription:', error);
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
  
  signOut: async () => {
    try {
      await supabase.auth.signOut();
      set({
        session: null,
        user: null,
        subscription: null,
      });
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    }
  },
}));

// Selectors
export const useSession = () => useAuthStore((state) => state.session);
export const useUser = () => useAuthStore((state) => state.user);
export const useSubscription = () => useAuthStore((state) => state.subscription);
export const useIsAuthenticated = () => useAuthStore((state) => !!state.session);
export const useIsPro = () => useAuthStore((state) => state.subscription?.is_active ?? false);
