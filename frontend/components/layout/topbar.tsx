'use client';

import { useState } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { SearchInput } from '@/components/ui/input';
import { Bell, Settings, User } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// ═══════════════════════════════════════════════════════════════════════════
// TOPBAR COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface TopbarProps {
  user?: {
    email: string;
    display_name?: string;
    avatar_url?: string;
  } | null;
  onSearch?: (query: string) => void;
  sidebarCollapsed?: boolean;
}

export function Topbar({ user, onSearch, sidebarCollapsed = false }: TopbarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch?.(value);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    onSearch?.('');
  };

  const userInitial = user?.display_name?.[0] || user?.email?.[0] || 'U';

  return (
    <header
      className={cn(
        'fixed top-0 right-0 z-30 h-16',
        'bg-bg-primary/80 backdrop-blur-glass',
        'border-b border-glass-border',
        'transition-all duration-300',
        sidebarCollapsed ? 'left-[72px]' : 'left-[240px]'
      )}
    >
      <div className="flex items-center justify-between h-full px-6">
        {/* ─────────────────────────────────────────────────────────────────
           SEARCH
           ───────────────────────────────────────────────────────────────── */}
        <div className="flex-1 max-w-xl">
          <SearchInput
            value={searchQuery}
            onChange={handleSearch}
            onClear={handleClearSearch}
            placeholder="Rechercher un actif..."
            className="w-full"
          />
        </div>

        {/* ─────────────────────────────────────────────────────────────────
           RIGHT SECTION
           ───────────────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-3">
          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className={cn(
                'relative flex items-center justify-center w-10 h-10 rounded-xl',
                'bg-surface border border-glass-border',
                'text-text-secondary hover:text-text-primary',
                'hover:bg-surface-hover hover:border-glass-border-hover',
                'transition-all duration-200'
              )}
            >
              <Bell className="w-5 h-5" />
              {/* Notification badge */}
              <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center bg-score-red text-[10px] font-bold text-white rounded-full">
                3
              </span>
            </button>

            {/* Notifications dropdown */}
            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 top-full mt-2 w-80 bg-bg-elevated border border-glass-border rounded-xl shadow-glass-lg overflow-hidden"
                >
                  <div className="p-4 border-b border-glass-border">
                    <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
                  </div>
                  <div className="p-2 max-h-80 overflow-y-auto">
                    <NotificationItem
                      title="Score mis à jour"
                      description="Le score de AAPL a été recalculé"
                      time="Il y a 5 min"
                    />
                    <NotificationItem
                      title="Nouvel actif disponible"
                      description="NVDA a été ajouté à l'univers"
                      time="Il y a 1h"
                    />
                    <NotificationItem
                      title="Alerte watchlist"
                      description="MSFT a dépassé votre seuil"
                      time="Il y a 2h"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Settings */}
          <Link
            href="/settings"
            className={cn(
              'flex items-center justify-center w-10 h-10 rounded-xl',
              'bg-surface border border-glass-border',
              'text-text-secondary hover:text-text-primary',
              'hover:bg-surface-hover hover:border-glass-border-hover',
              'transition-all duration-200'
            )}
          >
            <Settings className="w-5 h-5" />
          </Link>

          {/* User avatar */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className={cn(
                'flex items-center justify-center w-10 h-10 rounded-full',
                'bg-gradient-to-br from-accent to-accent-dark',
                'text-white font-semibold text-sm',
                'border-2 border-accent',
                'hover:shadow-glow transition-all duration-200'
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
            </button>

            {/* User menu dropdown */}
            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 top-full mt-2 w-56 bg-bg-elevated border border-glass-border rounded-xl shadow-glass-lg overflow-hidden"
                >
                  <div className="p-4 border-b border-glass-border">
                    <p className="text-sm font-medium text-text-primary truncate">
                      {user?.display_name || 'Utilisateur'}
                    </p>
                    <p className="text-xs text-text-muted truncate">{user?.email}</p>
                  </div>
                  <div className="p-2">
                    <Link
                      href="/settings"
                      className="flex items-center gap-3 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface rounded-lg transition-colors"
                    >
                      <User className="w-4 h-4" />
                      Mon compte
                    </Link>
                    <Link
                      href="/settings/billing"
                      className="flex items-center gap-3 px-3 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-surface rounded-lg transition-colors"
                    >
                      <Settings className="w-4 h-4" />
                      Abonnement
                    </Link>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Click outside handler */}
      {(showNotifications || showUserMenu) && (
        <div
          className="fixed inset-0 z-[-1]"
          onClick={() => {
            setShowNotifications(false);
            setShowUserMenu(false);
          }}
        />
      )}
    </header>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// NOTIFICATION ITEM
// ═══════════════════════════════════════════════════════════════════════════

interface NotificationItemProps {
  title: string;
  description: string;
  time: string;
}

function NotificationItem({ title, description, time }: NotificationItemProps) {
  return (
    <div className="p-3 rounded-lg hover:bg-surface transition-colors cursor-pointer">
      <p className="text-sm font-medium text-text-primary">{title}</p>
      <p className="text-xs text-text-muted mt-0.5">{description}</p>
      <p className="text-[10px] text-text-dim mt-1">{time}</p>
    </div>
  );
}

export default Topbar;
