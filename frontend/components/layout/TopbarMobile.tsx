'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Bell, Search, X, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNotifications } from '@/hooks/useNotifications';

// ═══════════════════════════════════════════════════════════════════════════
// MOBILE TOPBAR
// Compact header for mobile devices
// ═══════════════════════════════════════════════════════════════════════════

interface TopbarMobileProps {
  user?: {
    email: string;
    display_name?: string;
    avatar_url?: string;
  } | null;
}

export function TopbarMobile({ user }: TopbarMobileProps) {
  const router = useRouter();
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);

  const { notifications, unreadCount, loading, markAllAsRead } = useNotifications();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/dashboard/explorer?q=${encodeURIComponent(searchQuery.trim())}`);
      setShowSearch(false);
      setSearchQuery('');
    }
  };

  const userInitial = user?.display_name?.[0] || user?.email?.[0] || 'U';

  return (
    <>
      <header
        className={cn(
          'fixed top-0 left-0 right-0 z-40',
          'bg-bg-secondary/95 backdrop-blur-glass',
          'border-b border-glass-border',
          'h-14 md:hidden' // Only show on mobile
        )}
      >
        <div className="flex items-center justify-between h-full px-4">
          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
              <span className="text-sm text-white font-bold">◉</span>
            </div>
            <span className="text-base font-bold text-text-primary">MarketGPS</span>
          </Link>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            {/* Search toggle */}
            <button
              onClick={() => setShowSearch(true)}
              className={cn(
                'flex items-center justify-center w-10 h-10 rounded-xl',
                'bg-surface border border-glass-border',
                'text-text-secondary active:bg-surface-hover',
                'transition-colors'
              )}
              aria-label="Rechercher"
            >
              <Search className="w-5 h-5" />
            </button>

            {/* Notifications */}
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className={cn(
                'relative flex items-center justify-center w-10 h-10 rounded-xl',
                'bg-surface border border-glass-border',
                'text-text-secondary active:bg-surface-hover',
                'transition-colors'
              )}
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center bg-score-red text-[10px] font-bold text-white rounded-full">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* User avatar */}
            <Link
              href="/settings"
              className={cn(
                'flex items-center justify-center w-10 h-10 rounded-full',
                'bg-gradient-to-br from-accent to-accent-dark',
                'text-white font-semibold text-sm',
                'border-2 border-accent'
              )}
            >
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || user.email}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                userInitial.toUpperCase()
              )}
            </Link>
          </div>
        </div>
      </header>

      {/* Search overlay */}
      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-bg-primary/95 backdrop-blur-lg md:hidden"
          >
            <div className="flex flex-col h-full">
              {/* Search header */}
              <div className="flex items-center gap-3 p-4 border-b border-glass-border">
                <form onSubmit={handleSearch} className="flex-1">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Rechercher un actif..."
                    autoFocus
                    className={cn(
                      'w-full h-12 px-4 rounded-xl',
                      'bg-surface border border-glass-border',
                      'text-text-primary placeholder:text-text-muted',
                      'focus:outline-none focus:border-accent',
                      'text-base' // Prevent iOS zoom
                    )}
                  />
                </form>
                <button
                  onClick={() => {
                    setShowSearch(false);
                    setSearchQuery('');
                  }}
                  className={cn(
                    'flex items-center justify-center w-12 h-12 rounded-xl',
                    'bg-surface border border-glass-border',
                    'text-text-secondary'
                  )}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Quick suggestions */}
              <div className="flex-1 p-4">
                <p className="text-xs text-text-muted uppercase tracking-wider mb-3">
                  Suggestions
                </p>
                <div className="flex flex-wrap gap-2">
                  {['AAPL', 'MSFT', 'BTC', 'ETH', 'GOOGL', 'AMZN'].map((symbol) => (
                    <button
                      key={symbol}
                      onClick={() => {
                        router.push(`/dashboard/explorer?q=${symbol}`);
                        setShowSearch(false);
                      }}
                      className={cn(
                        'px-4 py-2 rounded-lg',
                        'bg-surface border border-glass-border',
                        'text-sm text-text-secondary',
                        'active:bg-surface-hover'
                      )}
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Notifications dropdown (mobile-optimized) */}
      <AnimatePresence>
        {showNotifications && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/50 md:hidden"
              onClick={() => setShowNotifications(false)}
            />
            {/* Notifications panel */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={cn(
                'fixed top-14 left-4 right-4 z-50',
                'bg-bg-elevated border border-glass-border rounded-xl',
                'shadow-glass-lg overflow-hidden',
                'max-h-[60vh]',
                'md:hidden'
              )}
            >
              <div className="p-4 border-b border-glass-border flex items-center justify-between">
                <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
                {unreadCount > 0 && (
                  <button
                    onClick={() => markAllAsRead()}
                    className="text-xs text-accent"
                  >
                    Tout marquer comme lu
                  </button>
                )}
              </div>
              <div className="p-2 max-h-[50vh] overflow-y-auto">
                {loading ? (
                  <div className="py-8 text-center">
                    <Loader2 className="w-6 h-6 text-accent mx-auto mb-2 animate-spin" />
                    <p className="text-sm text-text-muted">Chargement...</p>
                  </div>
                ) : notifications.length === 0 ? (
                  <div className="py-8 text-center">
                    <Bell className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                    <p className="text-sm text-text-muted">Aucune notification</p>
                  </div>
                ) : (
                  notifications.slice(0, 5).map((notification) => (
                    <div
                      key={notification.id}
                      className={cn(
                        'p-3 rounded-lg',
                        !notification.read && 'bg-accent/5'
                      )}
                    >
                      <p className="text-sm font-medium text-text-primary">
                        {notification.title}
                      </p>
                      <p className="text-xs text-text-muted mt-0.5 line-clamp-2">
                        {notification.description}
                      </p>
                      <p className="text-[10px] text-text-dim mt-1">
                        {notification.time}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

export default TopbarMobile;
