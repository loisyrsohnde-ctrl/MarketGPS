'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { supabase, signOut, getSession } from '@/lib/supabase';
import { getApiBaseUrl } from '@/lib/config';

// Layout components
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';
import { TopbarMobile } from './TopbarMobile';
import { MobileTabBar } from './MobileTabBar';
import { AssetInspector } from '@/components/AssetInspector';
import { Paywall } from '@/components/Paywall';

// Phase 4 - AI Concierge FAB
import ConciergeFAB from '@/components/wealth/ConciergeFAB';

// Phase 5 - Guest Conversion Banner
import { GuestConversionBanner } from '@/components/GuestConversionBanner';

// ═══════════════════════════════════════════════════════════════════════════
// APP SHELL
// Responsive layout shell that handles:
// - Desktop: Sidebar + Topbar
// - Mobile: Compact Topbar + Bottom Tab Bar
// - Guest access: Shows layout without auth redirect on allowed routes
// ═══════════════════════════════════════════════════════════════════════════

// Routes accessible without authentication (guest mode)
const GUEST_ALLOWED_ROUTES = [
  '/dashboard',
  '/dashboard/explorer',
  '/strategies',
  '/news',
  '/academy',
  '/asset',
  '/pricing',
  '/barbell',
];

// Routes that require a paid subscription (not just free account)
const SUBSCRIBER_ONLY_ROUTES = [
  '/academy/cours',
];

interface AppShellProps {
  children: React.ReactNode;
  /** If true, bypass the paywall (for settings, profile, etc.) */
  bypassPaywall?: boolean;
  /** If true, allow guest access (no auth redirect) */
  allowGuest?: boolean;
}

function isGuestAllowedRoute(pathname: string | null): boolean {
  if (!pathname) return false;
  return GUEST_ALLOWED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );
}

export function AppShell({ children, bypassPaywall = false, allowGuest }: AppShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [user, setUser] = useState<{
    email: string;
    display_name?: string;
    avatar_url?: string;
  } | null>(null);
  const [scopeCounts, setScopeCounts] = useState({ US_EU: 0, AFRICA: 0 });
  const [isLoading, setIsLoading] = useState(true);

  // Check if current route allows guest access
  const isPublicRoute = pathname?.startsWith('/news');
  const guestAllowed = allowGuest !== undefined ? allowGuest : isGuestAllowedRoute(pathname);

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
        } else if (!isPublicRoute && !guestAllowed) {
          // Only redirect to login if route doesn't allow guests
          router.push('/login');
        }
      } catch (error) {
        console.error('Auth error:', error);
        if (!isPublicRoute && !guestAllowed) {
          router.push('/login');
        }
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
        setUser(null);
        if (!isPublicRoute && !guestAllowed) {
          router.push('/login');
        }
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
  }, [router, isPublicRoute, guestAllowed]);

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
        <Sidebar 
          scopeCounts={scopeCounts} 
          onLogout={handleLogout} 
          isAuthenticated={!!user}
        />
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
        <div className="p-4 md:p-6">
          {bypassPaywall || guestAllowed ? children : <Paywall>{children}</Paywall>}
        </div>
      </main>

      {/* Global Asset Inspector Slide-Over */}
      <AssetInspector />

      {/* Phase 4 - AI Concierge Floating Action Button */}
      <ConciergeFAB />

      {/* Guest conversion banner */}
      <GuestConversionBanner />
    </div>
  );
}

export default AppShell;
