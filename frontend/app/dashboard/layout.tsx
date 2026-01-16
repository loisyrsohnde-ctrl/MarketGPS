'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { cn } from '@/lib/utils';
import { supabase, signOut, getSession } from '@/lib/supabase';

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD LAYOUT
// Authenticated layout with sidebar and topbar
// ═══════════════════════════════════════════════════════════════════════════

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<{ email: string; display_name?: string } | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      // Check for demo mode
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('demo') === 'true') {
        setIsDemo(true);
        setUser({ email: 'demo@marketgps.io', display_name: 'Demo User' });
        return;
      }

      // Check Supabase session
      try {
        const session = await getSession();
        if (session?.user) {
          setUser({
            email: session.user.email || '',
            display_name: session.user.user_metadata?.display_name,
          });
        } else {
          // No session, redirect to login
          router.push('/login');
        }
      } catch (error) {
        console.error('Auth error:', error);
        router.push('/login');
      }
    };

    checkAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT') {
        router.push('/login');
      } else if (session?.user) {
        setUser({
          email: session.user.email || '',
          display_name: session.user.user_metadata?.display_name,
        });
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const handleLogout = async () => {
    if (isDemo) {
      router.push('/');
      return;
    }
    
    try {
      await signOut();
      router.push('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleSearch = (query: string) => {
    if (query) {
      router.push(`/dashboard/explorer?q=${encodeURIComponent(query)}`);
    }
  };

  // Mock scope counts (replace with real data)
  const scopeCounts = {
    US_EU: 3552,
    AFRICA: 50,
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Sidebar */}
      <Sidebar
        scopeCounts={scopeCounts}
        onLogout={handleLogout}
      />

      {/* Topbar */}
      <Topbar
        user={user}
        onSearch={handleSearch}
        sidebarCollapsed={sidebarCollapsed}
      />

      {/* Main content */}
      <main
        className={cn(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarCollapsed ? 'ml-[72px]' : 'ml-[240px]'
        )}
      >
        <div className="p-6">
          {/* Demo banner */}
          {isDemo && (
            <div className="mb-6 p-4 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
              <p className="text-sm text-score-yellow">
                🎭 Mode démo actif.{' '}
                <a href="/signup" className="underline hover:no-underline">
                  Créez un compte
                </a>{' '}
                pour accéder à toutes les fonctionnalités.
              </p>
            </div>
          )}

          {children}
        </div>
      </main>
    </div>
  );
}
