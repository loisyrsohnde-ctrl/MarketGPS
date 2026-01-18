/**
 * useNotifications - Hook pour gérer les notifications utilisateur
 * Récupère les notifications depuis le backend et permet de les marquer comme lues
 */

import { useState, useEffect, useCallback } from 'react';
import * as userApi from '@/lib/api-user';

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

export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<userApi.UserNotification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch notifications from backend
  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [notificationMessages, countResult] = await Promise.all([
        userApi.getNotificationMessages(20),
        userApi.getUnreadNotificationCount(),
      ]);

      setNotifications(notificationMessages);
      setUnreadCount(countResult.count);
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
