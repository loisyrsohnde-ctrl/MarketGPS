'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { cn } from '@/lib/utils';
import { supabase, signOut, getSession } from '@/lib/supabase';

interface LayoutProps {
  children: React.ReactNode;
}

export default function SettingsLayout({ children }: LayoutProps) {
  const router = useRouter();
  const [sidebarCollapsed] = useState(false);
  const [user, setUser] = useState<{ email: string; display_name?: string } | null>(null);
  const [scopeCounts, setScopeCounts] = useState({ US_EU: 0, AFRICA: 0 });

  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8501';
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

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const session = await getSession();
        if (session?.user) {
          setUser({ email: session.user.email || '', display_name: session.user.user_metadata?.display_name });
        }
      } catch (error) {
        console.error('Auth error:', error);
      }
    };
    checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) {
        setUser({ email: session.user.email || '', display_name: session.user.user_metadata?.display_name });
      }
    });
    return () => subscription.unsubscribe();
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
    if (query) router.push(`/dashboard/explorer?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      <Sidebar scopeCounts={scopeCounts} onLogout={handleLogout} />
      <Topbar user={user} onSearch={handleSearch} sidebarCollapsed={sidebarCollapsed} />
      <main className={cn('pt-16 min-h-screen transition-all duration-300', sidebarCollapsed ? 'ml-[72px]' : 'ml-[240px]')}>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
