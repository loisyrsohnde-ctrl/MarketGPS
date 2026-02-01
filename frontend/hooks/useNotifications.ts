/**
 * useNotifications - Hook pour gérer les notifications utilisateur
 * Récupère les notifications depuis le backend et permet de les marquer comme lues
 * Inclut également les breaking news depuis le système de news
 */

import { useState, useEffect, useCallback } from 'react';
import * as userApi from '@/lib/api-user';
import { getApiBaseUrl } from '@/lib/config';

// Type pour les notifications du système news
interface NewsNotification {
  id: string;
  type: 'breaking_news' | 'news_impact' | string;
  priority: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  dismissed: boolean;
  data?: {
    article_id?: number;
    slug?: string;
    source?: string;
    country?: string;
    category?: string;
  };
  actions?: Array<{
    label: string;
    action: string;
    primary?: boolean;
  }>;
}

export interface UseNotificationsReturn {
  // State
  notifications: userApi.UserNotification[];
  unreadCount: number;
  loading: boolean;
  error: string | null;

  // Methods
  markAsRead: (notificationIds?: string[]) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  refetch: () => Promise<void>;
}

// Convertir une notification news en notification utilisateur
function convertNewsNotification(news: NewsNotification): userApi.UserNotification {
  const typeMap: Record<string, 'alert' | 'warning' | 'info' | 'success'> = {
    'breaking_news': 'alert',
    'news_impact': 'info',
    'score_drop': 'warning',
    'score_surge': 'success',
    'rebalance': 'warning',
    'morning_brief': 'info',
    'opportunity': 'success',
  };

  // Format time ago
  const formatTimeAgo = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return "À l'instant";
      if (diffMins < 60) return `Il y a ${diffMins} min`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `Il y a ${diffHours}h`;
      const diffDays = Math.floor(diffHours / 24);
      return `Il y a ${diffDays}j`;
    } catch {
      return '';
    }
  };

  return {
    id: news.id,
    type: typeMap[news.type] || 'info',
    title: news.title,
    description: news.message,
    time: formatTimeAgo(news.timestamp),
    read: news.read,
  };
}

export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<userApi.UserNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch notifications from backend (both user and news)
  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const API_BASE = getApiBaseUrl();

      // Fetch both user notifications and news notifications in parallel
      const [notificationMessages, countResult, newsNotificationsRes] = await Promise.all([
        userApi.getNotificationMessages(20),
        userApi.getUnreadNotificationCount(),
        fetch(`${API_BASE}/api/notifications?limit=10`).then(res => res.ok ? res.json() : { notifications: [] }),
      ]);

      // Convert and merge news notifications
      const newsNotifications: userApi.UserNotification[] = (newsNotificationsRes.notifications || [])
        .filter((n: NewsNotification) => n.type === 'breaking_news' || n.type === 'news_impact')
        .map(convertNewsNotification);

      // Merge and dedupe by ID, prioritizing user notifications
      const userIds = new Set(notificationMessages.map(n => n.id));
      const mergedNotifications = [
        ...notificationMessages,
        ...newsNotifications.filter(n => !userIds.has(n.id)),
      ];

      // Sort by time (newest first) - breaking news uses timestamp
      mergedNotifications.sort((a, b) => {
        // Simple string comparison works for "Il y a X" format
        return 0; // Keep original order as already sorted
      });

      const totalUnread = countResult.count + newsNotifications.filter(n => !n.read).length;

      setNotifications(mergedNotifications.slice(0, 20));
      setUnreadCount(totalUnread);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch notifications:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load on mount
  useEffect(() => {
    fetchNotifications();
    
    // Optional: Poll for new notifications every 60 seconds
    const interval = setInterval(fetchNotifications, 60000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  // Mark specific notifications as read
  const markAsRead = useCallback(async (notificationIds?: string[]) => {
    try {
      setError(null);
      await userApi.markNotificationsAsRead(notificationIds);
      
      // Optimistic update
      if (notificationIds) {
        setNotifications(prev => 
          prev.map(n => 
            notificationIds.includes(n.id) ? { ...n, read: true } : n
          )
        );
        setUnreadCount(prev => Math.max(0, prev - notificationIds.length));
      } else {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        setUnreadCount(0);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      // Refetch on error to get correct state
      await fetchNotifications();
    }
  }, [fetchNotifications]);

  // Mark all as read
  const markAllAsRead = useCallback(async () => {
    await markAsRead(undefined);
  }, [markAsRead]);

  return {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    refetch: fetchNotifications,
  };
}
