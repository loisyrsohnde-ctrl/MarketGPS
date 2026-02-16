'use client';

import { useState, useRef, useEffect } from 'react';
import { Bell, Flame, AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export interface Notification {
  id: string;
  type: 'viral_break' | 'pipeline_error' | 'publish_success' | 'system';
  message: string;
  timestamp: Date;
  read: boolean;
}

interface NotificationCenterProps {
  className?: string;
}

const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'viral_break',
    message: 'Article "Tesla Stock Surge" a atteint 500K vues',
    timestamp: new Date(Date.now() - 5 * 60000),
    read: false,
  },
  {
    id: '2',
    type: 'publish_success',
    message: 'Article "Market Analysis Q4" publié avec succès',
    timestamp: new Date(Date.now() - 15 * 60000),
    read: false,
  },
  {
    id: '3',
    type: 'pipeline_error',
    message: 'Erreur lors du scraping: Connection timeout',
    timestamp: new Date(Date.now() - 30 * 60000),
    read: false,
  },
  {
    id: '4',
    type: 'system',
    message: 'Mise à jour système disponible',
    timestamp: new Date(Date.now() - 2 * 3600000),
    read: true,
  },
  {
    id: '5',
    type: 'viral_break',
    message: 'Nouveau script "Economic Indicators" déployé',
    timestamp: new Date(Date.now() - 4 * 3600000),
    read: true,
  },
];

function getNotificationIcon(type: Notification['type']) {
  switch (type) {
    case 'viral_break':
      return <Flame className="h-5 w-5 text-orange-500" />;
    case 'pipeline_error':
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    case 'publish_success':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'system':
      return <Info className="h-5 w-5 text-blue-500" />;
  }
}

function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'À l\'instant';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}j`;

  return date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' });
}

export function NotificationCenter({ className = '' }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  const handleMarkAllAsRead = () => {
    setNotifications(
      notifications.map(n => ({ ...n, read: true }))
    );
  };

  const handleNotificationClick = (id: string) => {
    setNotifications(
      notifications.map(n =>
        n.id === id ? { ...n, read: true } : n
      )
    );
  };

  const handleDismiss = (id: string) => {
    setNotifications(notifications.filter(n => n.id !== id));
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Close dropdown on Escape key
  useEffect(() => {
    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => {
        document.removeEventListener('keydown', handleEscapeKey);
      };
    }
  }, [isOpen]);

  const visibleNotifications = notifications.slice(0, 10);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Bell button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative inline-flex items-center justify-center p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <Bell className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        )}
      </button>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-sm bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 z-50 overflow-hidden">
          {/* Header */}
          <div className="sticky top-0 flex items-center justify-between gap-3 px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
              >
                Tout marquer comme lu
              </button>
            )}
          </div>

          {/* Notifications list */}
          <div className="max-h-96 overflow-y-auto">
            {visibleNotifications.length > 0 ? (
              visibleNotifications.map(notification => (
                <div
                  key={notification.id}
                  onClick={() => handleNotificationClick(notification.id)}
                  className={`flex gap-3 px-4 py-3 border-b border-gray-100 dark:border-gray-800 cursor-pointer transition-colors last:border-b-0 ${
                    notification.read
                      ? 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                      : 'bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30'
                  }`}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0 mt-0.5">
                    {getNotificationIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${
                      notification.read
                        ? 'text-gray-700 dark:text-gray-300'
                        : 'text-gray-900 dark:text-white font-medium'
                    }`}>
                      {notification.message}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {formatRelativeTime(notification.timestamp)}
                    </p>
                  </div>

                  {/* Dismiss button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDismiss(notification.id);
                    }}
                    className="flex-shrink-0 p-1 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-400 transition-colors"
                    aria-label="Dismiss notification"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center py-8">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Aucune notification
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
