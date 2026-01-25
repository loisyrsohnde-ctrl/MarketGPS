'use client';

import { useEffect, useState, useCallback } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

// ═══════════════════════════════════════════════════════════════════════════
// useAuth Hook
// Provides authentication state and methods
// ═══════════════════════════════════════════════════════════════════════════

interface AuthState {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    session: null,
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  useEffect(() => {
    // Get initial session
    const getSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        setState({
          session,
          user: session?.user ?? null,
          isLoading: false,
          isAuthenticated: !!session,
        });
      } catch (error) {
        console.error('Error getting session:', error);
        setState(prev => ({ ...prev, isLoading: false }));
      }
    };

    getSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setState({
          session,
          user: session?.user ?? null,
          isLoading: false,
          isAuthenticated: !!session,
        });
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signOut = useCallback(async () => {
    try {
      await supabase.auth.signOut();
    } catch (error) {
      console.error('Error signing out:', error);
    }
  }, []);

  const refreshSession = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.refreshSession();
      setState(prev => ({
        ...prev,
        session,
        user: session?.user ?? null,
        isAuthenticated: !!session,
      }));
      return session;
    } catch (error) {
      console.error('Error refreshing session:', error);
      return null;
    }
  }, []);

  return {
    ...state,
    signOut,
    refreshSession,
  };
}

export default useAuth;
