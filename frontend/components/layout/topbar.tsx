'use client';

import { useState } from 'react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { SearchInput } from '@/components/ui/input';
import { Bell, Settings, User, CheckCircle, AlertCircle, TrendingUp, Info, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNotifications } from '@/hooks/useNotifications';

// ═══════════════════════════════════════════════════════════════════════════
// NOTIFICATION TYPES (re-exported for compatibility)
// ═══════════════════════════════════════════════════════════════════════════

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'info' | 'alert';
  title: string;
  description: string;
  time: string;
  read: boolean;
}

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

  // Use the notifications hook to fetch real notifications from backend
  const { notifications, unreadCount, loading, markAllAsRead } = useNotifications();

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch?.(value);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    onSearch?.('');
  };

  const handleMarkAllAsRead = async () => {
    await markAllAsRead();
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
              {/* Notification badge - only show if there are unread notifications */}
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center bg-score-red text-[10px] font-bold text-white rounded-full">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
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
                  <div className="p-4 border-b border-glass-border flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
                    {unreadCount > 0 && (
                      <button 
                        onClick={handleMarkAllAsRead}
                        className="text-xs text-accent hover:text-accent-light transition-colors"
                      >
                        Tout marquer comme lu
                      </button>
                    )}
                  </div>
                  <div className="p-2 max-h-80 overflow-y-auto">
                    {loading ? (
                      <div className="py-8 text-center">
                        <Loader2 className="w-6 h-6 text-accent mx-auto mb-2 animate-spin" />
                        <p className="text-sm text-text-muted">Chargement...</p>
                      </div>
                    ) : notifications.length === 0 ? (
                      <div className="py-8 text-center">
                        <Bell className="w-8 h-8 text-text-muted mx-auto mb-2 opacity-50" />
                        <p className="text-sm text-text-muted">Aucune notification</p>
                        <p className="text-xs text-text-dim mt-1">
                          Les alertes et mises à jour apparaîtront ici
                        </p>
                      </div>
                    ) : (
                      notifications.map((notification) => (
                        <NotificationItem
                          key={notification.id}
                          type={notification.type}
                          title={notification.title}
                          description={notification.description}
                          time={notification.time}
                          read={notification.read}
                        />
                      ))
                    )}
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
  type: 'success' | 'warning' | 'info' | 'alert';
  title: string;
  description: string;
  time: string;
  read?: boolean;
}

function NotificationItem({ type, title, description, time, read = false }: NotificationItemProps) {
  const iconMap = {
    success: CheckCircle,
    warning: AlertCircle,
    info: Info,
    alert: TrendingUp,
  };
  
  const colorMap = {
    success: 'text-score-green',
    warning: 'text-score-yellow',
    info: 'text-accent',
    alert: 'text-score-red',
  };
  
  const Icon = iconMap[type];
  
  return (
    <div className={cn(
      "p-3 rounded-lg hover:bg-surface transition-colors cursor-pointer flex gap-3",
      !read && "bg-accent/5"
    )}>
      <Icon className={cn("w-5 h-5 flex-shrink-0 mt-0.5", colorMap[type])} />
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium", read ? "text-text-secondary" : "text-text-primary")}>{title}</p>
        <p className="text-xs text-text-muted mt-0.5 truncate">{description}</p>
        <p className="text-[10px] text-text-dim mt-1">{time}</p>
      </div>
      {!read && (
        <div className="w-2 h-2 rounded-full bg-accent flex-shrink-0 mt-2" />
      )}
    </div>
  );
}

export default Topbar;
