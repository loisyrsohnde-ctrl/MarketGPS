'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  BellRing,
  X,
  Check,
  CheckCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Newspaper,
  Sun,
  Clock,
  ChevronRight,
  Settings,
  Trash2,
  Eye,
  Volume2,
  VolumeX,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type NotificationType = 
  | 'score_drop'      // Score dropped below threshold
  | 'score_surge'     // Score increased significantly
  | 'rebalance'       // Portfolio needs rebalancing
  | 'news_impact'     // News affecting portfolio
  | 'morning_brief'   // Daily morning summary
  | 'opportunity'     // New opportunity detected
  | 'alert'           // General alert
  | 'system';         // System notification

type NotificationPriority = 'critical' | 'high' | 'medium' | 'low';

interface Notification {
  id: string;
  type: NotificationType;
  priority: NotificationPriority;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  dismissed: boolean;
  data?: Record<string, any>;
  actions?: {
    label: string;
    action: string;
    primary?: boolean;
  }[];
}

interface NotificationCenterProps {
  onAction?: (notificationId: string, action: string) => void;
  onNavigate?: (path: string) => void;
}

// =============================================================================
// Configuration
// =============================================================================

const TYPE_CONFIG: Record<NotificationType, { 
  icon: React.ElementType; 
  color: string; 
  label: string;
}> = {
  score_drop: { 
    icon: TrendingDown, 
    color: 'text-red-400 bg-red-500/10', 
    label: 'Alerte Score' 
  },
  score_surge: { 
    icon: TrendingUp, 
    color: 'text-emerald-400 bg-emerald-500/10', 
    label: 'Score en hausse' 
  },
  rebalance: { 
    icon: RefreshCw, 
    color: 'text-amber-400 bg-amber-500/10', 
    label: 'Rééquilibrage' 
  },
  news_impact: { 
    icon: Newspaper, 
    color: 'text-blue-400 bg-blue-500/10', 
    label: 'Actualité' 
  },
  morning_brief: { 
    icon: Sun, 
    color: 'text-orange-400 bg-orange-500/10', 
    label: 'Brief Matinal' 
  },
  opportunity: { 
    icon: TrendingUp, 
    color: 'text-purple-400 bg-purple-500/10', 
    label: 'Opportunité' 
  },
  alert: { 
    icon: AlertTriangle, 
    color: 'text-amber-400 bg-amber-500/10', 
    label: 'Alerte' 
  },
  system: { 
    icon: Bell, 
    color: 'text-slate-400 bg-slate-500/10', 
    label: 'Système' 
  },
};

const PRIORITY_STYLES: Record<NotificationPriority, string> = {
  critical: 'border-l-red-500',
  high: 'border-l-orange-500',
  medium: 'border-l-amber-500',
  low: 'border-l-slate-500',
};

// =============================================================================
// Demo Data
// =============================================================================

function generateDemoNotifications(): Notification[] {
  const now = Date.now();
  
  return [
    {
      id: '1',
      type: 'morning_brief',
      priority: 'medium',
      title: 'Brief Matinal — 30 Janvier',
      message: 'Marchés en hausse de 0.8%. Votre portefeuille surperforme le S&P 500. 2 opportunités détectées.',
      timestamp: new Date(now - 3600000).toISOString(),
      read: false,
      dismissed: false,
      actions: [
        { label: 'Voir le brief', action: 'view_brief', primary: true },
      ],
    },
    {
      id: '2',
      type: 'score_drop',
      priority: 'high',
      title: 'AAPL : Score en baisse (-8 pts)',
      message: 'Le score ProphetIA d\'Apple est passé de 82 à 74 suite aux résultats trimestriels.',
      timestamp: new Date(now - 7200000).toISOString(),
      read: false,
      dismissed: false,
      data: { ticker: 'AAPL', oldScore: 82, newScore: 74 },
      actions: [
        { label: 'Analyser', action: 'analyze_asset', primary: true },
        { label: 'Ignorer', action: 'dismiss' },
      ],
    },
    {
      id: '3',
      type: 'rebalance',
      priority: 'medium',
      title: 'Rééquilibrage suggéré',
      message: 'Votre allocation actions dépasse la cible de 5%. Considérez un arbitrage vers les obligations.',
      timestamp: new Date(now - 86400000).toISOString(),
      read: true,
      dismissed: false,
      actions: [
        { label: 'Voir détails', action: 'view_rebalance', primary: true },
      ],
    },
    {
      id: '4',
      type: 'news_impact',
      priority: 'medium',
      title: 'BCE : Impact sur votre portefeuille',
      message: 'La décision de la BCE sur les taux pourrait impacter vos positions obligataires (+0.3% estimé).',
      timestamp: new Date(now - 172800000).toISOString(),
      read: true,
      dismissed: false,
      data: { impact: 0.3, sector: 'bonds' },
    },
    {
      id: '5',
      type: 'opportunity',
      priority: 'low',
      title: 'Nouvelle opportunité : MSFT',
      message: 'Microsoft atteint un score de 84 avec un signal d\'accumulation institutionnelle.',
      timestamp: new Date(now - 259200000).toISOString(),
      read: true,
      dismissed: false,
      data: { ticker: 'MSFT', score: 84 },
      actions: [
        { label: 'Voir', action: 'view_opportunity' },
        { label: 'Ajouter watchlist', action: 'add_watchlist', primary: true },
      ],
    },
  ];
}

// =============================================================================
// Utility Functions
// =============================================================================

function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins} min`;
  if (diffHours < 24) return `Il y a ${diffHours}h`;
  if (diffDays < 7) return `Il y a ${diffDays}j`;
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

// =============================================================================
// Sub-Components
// =============================================================================

function NotificationItem({
  notification,
  onRead,
  onDismiss,
  onAction,
}: {
  notification: Notification;
  onRead: () => void;
  onDismiss: () => void;
  onAction: (action: string) => void;
}) {
  const config = TYPE_CONFIG[notification.type];
  const Icon = config.icon;
  const priorityStyle = PRIORITY_STYLES[notification.priority];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className={`
        relative bg-slate-900/80 border border-slate-800 rounded-xl
        border-l-4 ${priorityStyle}
        ${!notification.read ? 'bg-slate-900' : 'bg-slate-950/50'}
        transition-all duration-200
      `}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${config.color}`}>
            <Icon size={16} />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className={`text-sm font-medium ${!notification.read ? 'text-slate-200' : 'text-slate-400'}`}>
                {notification.title}
              </h4>
              {!notification.read && (
                <span className="w-2 h-2 rounded-full bg-indigo-500" />
              )}
            </div>
            
            <p className="text-xs text-slate-500 line-clamp-2 mb-2">
              {notification.message}
            </p>
            
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-600">
                {formatTimeAgo(notification.timestamp)}
              </span>
              
              {/* Actions */}
              {notification.actions && notification.actions.length > 0 && (
                <div className="flex gap-2">
                  {notification.actions.map((action, i) => (
                    <button
                      key={i}
                      onClick={() => onAction(action.action)}
                      className={`
                        px-2 py-1 text-[10px] font-medium rounded transition-colors
                        ${action.primary 
                          ? 'bg-indigo-600 hover:bg-indigo-500 text-white' 
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}
                      `}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Close button */}
          <button
            onClick={onDismiss}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
          >
            <X size={14} className="text-slate-500" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

function NotificationBell({
  unreadCount,
  onClick,
  hasNewCritical,
}: {
  unreadCount: number;
  onClick: () => void;
  hasNewCritical: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className="relative p-2 hover:bg-slate-800 rounded-lg transition-colors"
    >
      {hasNewCritical ? (
        <BellRing size={20} className="text-slate-300 animate-bounce" />
      ) : (
        <Bell size={20} className="text-slate-400" />
      )}
      
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center bg-red-500 text-white text-[10px] font-bold rounded-full px-1">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </button>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function NotificationCenter({
  onAction,
  onNavigate,
}: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [soundEnabled, setSoundEnabled] = useState(true);

  // Load notifications
  useEffect(() => {
    setNotifications(generateDemoNotifications());
  }, []);

  // Count unread
  const unreadCount = notifications.filter(n => !n.read && !n.dismissed).length;
  const hasNewCritical = notifications.some(n => !n.read && n.priority === 'critical');

  // Filtered notifications
  const filteredNotifications = notifications
    .filter(n => !n.dismissed)
    .filter(n => filter === 'all' || !n.read)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const handleRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  const handleDismiss = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, dismissed: true } : n)
    );
  }, []);

  const handleAction = useCallback((notificationId: string, action: string) => {
    handleRead(notificationId);
    
    if (action === 'dismiss') {
      handleDismiss(notificationId);
      return;
    }
    
    onAction?.(notificationId, action);
    
    // Navigation based on action
    const navMap: Record<string, string> = {
      'view_brief': '/dashboard/wealth/horizon',
      'analyze_asset': '/asset/',
      'view_rebalance': '/strategies',
      'view_opportunity': '/opportunities',
      'add_watchlist': '/watchlist',
    };
    
    if (navMap[action]) {
      onNavigate?.(navMap[action]);
      setIsOpen(false);
    }
  }, [handleRead, handleDismiss, onAction, onNavigate]);

  const handleMarkAllRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const handleClearAll = () => {
    setNotifications(prev => prev.map(n => ({ ...n, dismissed: true })));
  };

  return (
    <>
      {/* Bell Button */}
      <NotificationBell
        unreadCount={unreadCount}
        onClick={() => setIsOpen(true)}
        hasNewCritical={hasNewCritical}
      />

      {/* Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/40"
              onClick={() => setIsOpen(false)}
            />
            
            {/* Panel */}
            <motion.div
              initial={{ opacity: 0, x: 300 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 300 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl flex flex-col"
            >
              {/* Header */}
              <div className="p-4 border-b border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                    <Bell size={20} className="text-indigo-400" />
                    Notifications
                    {unreadCount > 0 && (
                      <span className="text-xs bg-indigo-600 text-white px-2 py-0.5 rounded-full">
                        {unreadCount} nouvelle{unreadCount > 1 ? 's' : ''}
                      </span>
                    )}
                  </h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <X size={18} className="text-slate-400" />
                  </button>
                </div>
                
                {/* Filters & Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    <button
                      onClick={() => setFilter('all')}
                      className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                        filter === 'all' ? 'bg-slate-700 text-slate-200' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      Toutes
                    </button>
                    <button
                      onClick={() => setFilter('unread')}
                      className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                        filter === 'unread' ? 'bg-slate-700 text-slate-200' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      Non lues
                    </button>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSoundEnabled(!soundEnabled)}
                      className="p-1.5 hover:bg-slate-800 rounded transition-colors"
                      title={soundEnabled ? 'Désactiver le son' : 'Activer le son'}
                    >
                      {soundEnabled ? (
                        <Volume2 size={14} className="text-slate-400" />
                      ) : (
                        <VolumeX size={14} className="text-slate-500" />
                      )}
                    </button>
                    <button
                      onClick={handleMarkAllRead}
                      className="p-1.5 hover:bg-slate-800 rounded transition-colors"
                      title="Tout marquer comme lu"
                    >
                      <CheckCheck size={14} className="text-slate-400" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Notifications List */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                <AnimatePresence mode="popLayout">
                  {filteredNotifications.map(notification => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onRead={() => handleRead(notification.id)}
                      onDismiss={() => handleDismiss(notification.id)}
                      onAction={(action) => handleAction(notification.id, action)}
                    />
                  ))}
                </AnimatePresence>
                
                {filteredNotifications.length === 0 && (
                  <div className="text-center py-12">
                    <Bell size={32} className="mx-auto text-slate-600 mb-3" />
                    <p className="text-sm text-slate-500">
                      {filter === 'unread' ? 'Aucune notification non lue' : 'Aucune notification'}
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t border-slate-800 flex items-center justify-between">
                <button
                  onClick={handleClearAll}
                  className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1"
                >
                  <Trash2 size={12} />
                  Tout effacer
                </button>
                <button
                  onClick={() => onNavigate?.('/settings/notifications')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                >
                  <Settings size={12} />
                  Paramètres
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

// Export types
export type { Notification, NotificationType, NotificationPriority };
