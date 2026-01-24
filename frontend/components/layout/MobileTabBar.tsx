'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Search,
  Star,
  Newspaper,
  Settings,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// MOBILE TAB BAR
// Bottom navigation for mobile devices
// ═══════════════════════════════════════════════════════════════════════════

interface TabItem {
  href: string;
  icon: React.ElementType;
  label: string;
  matchPaths?: string[];
}

const tabs: TabItem[] = [
  {
    href: '/dashboard',
    icon: LayoutDashboard,
    label: 'Dashboard',
    matchPaths: ['/dashboard'],
  },
  {
    href: '/dashboard/explorer',
    icon: Search,
    label: 'Marchés',
    matchPaths: ['/dashboard/explorer', '/dashboard/markets', '/asset'],
  },
  {
    href: '/watchlist',
    icon: Star,
    label: 'Watchlist',
    matchPaths: ['/watchlist'],
  },
  {
    href: '/news',
    icon: Newspaper,
    label: 'News',
    matchPaths: ['/news'],
  },
  {
    href: '/settings',
    icon: Settings,
    label: 'Réglages',
    matchPaths: ['/settings'],
  },
];

export function MobileTabBar() {
  const pathname = usePathname();

  const isActive = (tab: TabItem): boolean => {
    // Exact match for dashboard home
    if (tab.href === '/dashboard' && pathname === '/dashboard') {
      return true;
    }
    // Check if pathname starts with any of the matchPaths
    return tab.matchPaths?.some(path => {
      if (path === '/dashboard') {
        return pathname === '/dashboard';
      }
      return pathname.startsWith(path);
    }) ?? false;
  };

  return (
    <nav
      className={cn(
        'fixed bottom-0 left-0 right-0 z-50',
        'bg-bg-secondary/95 backdrop-blur-glass',
        'border-t border-glass-border',
        'md:hidden', // Hide on desktop
        // iOS safe area support
        'pb-[env(safe-area-inset-bottom)]'
      )}
    >
      <div className="flex items-center justify-around h-16">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const active = isActive(tab);

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                'flex flex-col items-center justify-center',
                'min-w-[64px] h-full px-2',
                'transition-colors duration-200',
                // Ensure 44px touch target
                'touch-manipulation',
                active
                  ? 'text-accent'
                  : 'text-text-muted active:text-text-secondary'
              )}
            >
              <Icon
                className={cn(
                  'w-6 h-6 mb-1',
                  active && 'drop-shadow-[0_0_8px_rgba(25,211,140,0.5)]'
                )}
              />
              <span
                className={cn(
                  'text-[10px] font-medium',
                  active ? 'text-accent' : 'text-text-muted'
                )}
              >
                {tab.label}
              </span>
              {/* Active indicator dot */}
              {active && (
                <div className="absolute bottom-1 w-1 h-1 rounded-full bg-accent" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export default MobileTabBar;
