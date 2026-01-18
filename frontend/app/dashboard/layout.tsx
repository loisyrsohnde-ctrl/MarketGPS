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

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
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
          {children}
        </div>
      </main>
    </div>
  );
}
