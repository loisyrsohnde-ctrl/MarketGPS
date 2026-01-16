'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn, formatNumberSafe } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Search,
  Star,
  TrendingUp,
  Settings,
  CreditCard,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Globe,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// SIDEBAR COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface SidebarProps {
  scopeCounts?: {
    US_EU: number;
    AFRICA: number;
  };
  onLogout?: () => void;
}

export function Sidebar({ scopeCounts, onLogout }: SidebarProps) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    {
      section: 'Navigation',
      items: [
        { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { href: '/dashboard/explorer', icon: Search, label: 'Explorer' },
        { href: '/watchlist', icon: Star, label: 'Liste de suivi' },
        { href: '/dashboard/markets', icon: TrendingUp, label: 'Marchés' },
      ],
    },
    {
      section: 'Marchés',
      items: [
        {
          href: '/dashboard?scope=US_EU',
          icon: 'flag-us-eu',
          label: `US / Europe`,
          badge: formatNumberSafe(scopeCounts?.US_EU),
        },
        {
          href: '/dashboard?scope=AFRICA',
          icon: Globe,
          label: 'Afrique',
          badge: formatNumberSafe(scopeCounts?.AFRICA),
        },
      ],
    },
    {
      section: 'Paramètres',
      items: [
        { href: '/settings', icon: Settings, label: 'Paramètres' },
        { href: '/settings/billing', icon: CreditCard, label: 'Abonnement' },
      ],
    },
  ];

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen',
        'bg-gradient-to-b from-bg-secondary to-bg-primary',
        'border-r border-glass-border',
        'transition-all duration-300 ease-in-out',
        collapsed ? 'w-[72px]' : 'w-[240px]'
      )}
    >
      <div className="flex flex-col h-full">
        {/* ─────────────────────────────────────────────────────────────────
           LOGO
           ───────────────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-glass-border">
          <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
            <span className="text-lg text-white font-bold">◉</span>
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="text-lg font-bold text-text-primary whitespace-nowrap overflow-hidden"
              >
                MarketGPS
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* ─────────────────────────────────────────────────────────────────
           NAVIGATION
           ───────────────────────────────────────────────────────────────── */}
        <nav className="flex-1 overflow-y-auto py-4 scrollbar-hide">
          {navItems.map((section) => (
            <div key={section.section} className="mb-6">
              {/* Section label */}
              <AnimatePresence>
                {!collapsed && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="px-4 mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-dim"
                  >
                    {section.section}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Nav items */}
              <div className="space-y-1 px-2">
                {section.items.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-xl',
                        'transition-all duration-200',
                        'group',
                        isActive
                          ? 'bg-accent-dim text-accent'
                          : 'text-text-secondary hover:bg-surface hover:text-text-primary'
                      )}
                    >
                      <span className={cn('flex-shrink-0', collapsed && 'mx-auto')}>
                        {Icon === 'flag-us-eu' ? (
                          <span className="text-sm">🇺🇸🇪🇺</span>
                        ) : (
                          <Icon className="w-5 h-5" />
                        )}
                      </span>
                      <AnimatePresence>
                        {!collapsed && (
                          <motion.span
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex-1 text-sm font-medium whitespace-nowrap"
                          >
                            {item.label}
                          </motion.span>
                        )}
                      </AnimatePresence>
                      {!collapsed && item.badge && (
                        <span className="text-xs text-text-muted bg-surface px-2 py-0.5 rounded-md" suppressHydrationWarning>
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* ─────────────────────────────────────────────────────────────────
           FOOTER
           ───────────────────────────────────────────────────────────────── */}
        <div className="border-t border-glass-border p-4">
          {/* Logout button */}
          {onLogout && (
            <button
              onClick={onLogout}
              className={cn(
                'flex items-center gap-3 w-full px-3 py-2.5 rounded-xl',
                'text-text-secondary hover:bg-surface hover:text-score-red',
                'transition-all duration-200'
              )}
            >
              <LogOut className={cn('w-5 h-5', collapsed && 'mx-auto')} />
              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="text-sm font-medium"
                  >
                    Déconnexion
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          )}

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={cn(
              'flex items-center justify-center w-full mt-2 py-2 rounded-xl',
              'text-text-muted hover:bg-surface hover:text-text-primary',
              'transition-all duration-200'
            )}
          >
            {collapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>

          {/* Version */}
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="mt-3 text-center text-[10px] text-text-dim"
              >
                MarketGPS v2.0
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
