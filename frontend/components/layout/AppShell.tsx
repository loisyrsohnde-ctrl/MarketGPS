'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { supabase, signOut, getSession } from '@/lib/supabase';
import { getApiBaseUrl } from '@/lib/config';

// Layout components
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';
import { TopbarMobile } from './TopbarMobile';
import { MobileTabBar } from './MobileTabBar';
import { AssetInspector } from '@/components/AssetInspector';

// ═══════════════════════════════════════════════════════════════════════════
// APP SHELL
// Responsive layout shell that handles:
// - Desktop: Sidebar + Topbar
// - Mobile: Compact Topbar + Bottom Tab Bar
// ═══════════════════════════════════════════════════════════════════════════

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<{
    email: string;
    display_name?: string;
    avatar_url?: string;
  } | null>(null);
  const [scopeCounts, setScopeCounts] = useState({ US_EU: 0, AFRICA: 0 });
  const [isLoading, setIsLoading] = useState(true);

  // Fetch scope counts on mount
  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const API_BASE = getApiBaseUrl();
        const res = await fetch(`${API_BASE}/api/metrics/counts`);
        if (res.ok) {
          const data = await res.json();
          setScopeCounts({ US_EU: data.US_EU || 0, AFRICA: data.AFRICA || 0 });
        }
      } catch (error) {
        console.error('Failed to fetch scope counts:', error);
      }
    };
    fetchCounts();
  }, []);

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const session = await getSession();
        if (session?.user) {
          setUser({
            email: session.user.email || '',
            display_name: session.user.user_metadata?.display_name,
            avatar_url: session.user.user_metadata?.avatar_url,
          });
        } else {
          router.push('/login');
        }
      } catch (error) {
        console.error('Auth error:', error);
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT') {
        router.push('/login');
      } else if (session?.user) {
        setUser({
          email: session.user.email || '',
          display_name: session.user.user_metadata?.display_name,
          avatar_url: session.user.user_metadata?.avatar_url,
        });
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router]);

  const handleLogout = useCallback(async () => {
    try {
      await signOut();
      router.push('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  }, [router]);

  const handleSearch = useCallback(
    (query: string) => {
      if (query) {
        router.push(`/dashboard/explorer?q=${encodeURIComponent(query)}`);
      }
    },
    [router]
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary overflow-x-hidden">
      {/* ═══════════════════════════════════════════════════════════════════
         DESKTOP LAYOUT (md and up)
         ═══════════════════════════════════════════════════════════════════ */}

      {/* Desktop Sidebar - hidden on mobile */}
      <div className="hidden md:block">
        <Sidebar scopeCounts={scopeCounts} onLogout={handleLogout} />
      </div>

      {/* Desktop Topbar - hidden on mobile */}
      <div className="hidden md:block">
        <Topbar
          user={user}
          onSearch={handleSearch}
          sidebarCollapsed={sidebarCollapsed}
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════════════
         MOBILE LAYOUT (below md)
         ═══════════════════════════════════════════════════════════════════ */}

      {/* Mobile Topbar - hidden on desktop */}
      <TopbarMobile user={user} />

      {/* Mobile Bottom Tab Bar - hidden on desktop */}
      <MobileTabBar />

      {/* ═══════════════════════════════════════════════════════════════════
         MAIN CONTENT
         ═══════════════════════════════════════════════════════════════════ */}
      <main
        className={cn(
          'min-h-screen transition-all duration-300',
          // Desktop: offset for sidebar
          'md:ml-[240px]',
          // Mobile: no sidebar offset, but add padding for topbar and bottom tabs
          'pt-14 pb-20', // Mobile: topbar (56px) + bottom tabs (80px with safe area)
          'md:pt-16 md:pb-0' // Desktop: only topbar offset
        )}
      >
        <div className="p-4 md:p-6">{children}</div>
      </main>

      {/* Global Asset Inspector Slide-Over */}
      <AssetInspector />
    </div>
  );
}

export default AppShell;
