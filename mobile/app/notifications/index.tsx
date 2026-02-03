/**
 * MarketGPS Mobile - Notifications List Screen
 * Liste des notifications avec actions
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, AppNotification } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState, Button } from '@/components/ui';

// Simple relative time formatter (replaces date-fns)
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'à l\'instant';
  if (diffMins < 60) return `il y a ${diffMins} min`;
  if (diffHours < 24) return `il y a ${diffHours}h`;
  if (diffDays < 7) return `il y a ${diffDays}j`;
  return date.toLocaleDateString('fr-FR');
}

const NOTIFICATION_ICONS: Record<string, string> = {
  score_drop: 'trending-down',
  score_surge: 'trending-up',
  rebalance: 'refresh',
  news_impact: 'newspaper',
  morning_brief: 'sunny',
  opportunity: 'flash',
  alert: 'warning',
  system: 'information-circle',
  breaking_news: 'megaphone',
};

const NOTIFICATION_COLORS: Record<string, string> = {
  score_drop: '#EF4444',
  score_surge: '#22C55E',
  rebalance: '#8B5CF6',
  news_impact: '#3B82F6',
  morning_brief: '#F59E0B',
  opportunity: '#19D38C',
  alert: '#F97316',
  system: '#64748B',
  breaking_news: '#EC4899',
};

const PRIORITY_STYLES: Record<string, { bg: string; text: string }> = {
  critical: { bg: '#EF444420', text: '#EF4444' },
  high: { bg: '#F9731620', text: '#F97316' },
  medium: { bg: '#3B82F620', text: '#3B82F6' },
  low: { bg: '#64748B20', text: '#64748B' },
};

export default function NotificationsListScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  // Fetch notifications
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['notifications', 'list', filter],
    queryFn: () => api.getAppNotifications({
      limit: 50,
      unread_only: filter === 'unread',
    }),
  });

  // Mark as read mutation
  const markReadMutation = useMutation({
    mutationFn: (notificationIds: string[]) => api.markNotificationRead(notificationIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Dismiss mutation
  const dismissMutation = useMutation({
    mutationFn: (notificationIds: string[]) => api.dismissNotification(notificationIds),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const handleNotificationPress = useCallback((notification: AppNotification) => {
    // Mark as read
    if (!notification.read) {
      markReadMutation.mutate([notification.id]);
    }

    // Navigate based on notification type and data
    if (notification.data?.ticker) {
      router.push(`/asset/${notification.data.ticker}`);
    } else if (notification.data?.slug) {
      router.push(`/news/${notification.data.slug}`);
    } else if (notification.type === 'morning_brief') {
      router.push('/notifications/brief' as any);
    }
  }, [router, markReadMutation]);

  const handleDismiss = (notification: AppNotification) => {
    dismissMutation.mutate([notification.id]);
  };

  const handleMarkAllRead = () => {
    const unreadIds = data?.notifications
      .filter(n => !n.read)
      .map(n => n.id) || [];

    if (unreadIds.length > 0) {
      markReadMutation.mutate(unreadIds);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const formatTime = (timestamp: string) => {
    try {
      return formatRelativeTime(timestamp);
    } catch {
      return '';
    }
  };

  const renderNotification = ({ item }: { item: AppNotification }) => {
    const iconName = NOTIFICATION_ICONS[item.type] || 'notifications';
    const iconColor = NOTIFICATION_COLORS[item.type] || '#64748B';
    const priorityStyle = PRIORITY_STYLES[item.priority] || PRIORITY_STYLES.low;

    return (
      <TouchableOpacity
        style={[
          styles.notificationCard,
          !item.read && styles.notificationUnread,
        ]}
        onPress={() => handleNotificationPress(item)}
        activeOpacity={0.7}
      >
        <View style={styles.notificationContent}>
          <View style={[styles.iconContainer, { backgroundColor: `${iconColor}20` }]}>
            <Ionicons name={iconName as any} size={20} color={iconColor} />
          </View>

          <View style={styles.textContent}>
            <View style={styles.headerRow}>
              <Text style={styles.notificationTitle} numberOfLines={1}>
                {item.title}
              </Text>
              {item.priority === 'critical' || item.priority === 'high' ? (
                <View style={[styles.priorityBadge, { backgroundColor: priorityStyle.bg }]}>
                  <Text style={[styles.priorityText, { color: priorityStyle.text }]}>
                    {item.priority === 'critical' ? 'URGENT' : 'IMPORTANT'}
                  </Text>
                </View>
              ) : null}
            </View>

            <Text style={styles.notificationMessage} numberOfLines={2}>
              {item.message}
            </Text>

            <View style={styles.metaRow}>
              <Text style={styles.timestamp}>{formatTime(item.timestamp)}</Text>
              {!item.read && <View style={styles.unreadDot} />}
            </View>

            {/* Actions */}
            {item.actions && item.actions.length > 0 && (
              <View style={styles.actionsRow}>
                {item.actions.map((action, index) => (
                  <TouchableOpacity
                    key={index}
                    style={[
                      styles.actionButton,
                      action.primary && styles.actionButtonPrimary,
                    ]}
                    onPress={() => {
                      // Handle action
                      handleNotificationPress(item);
                    }}
                  >
                    <Text
                      style={[
                        styles.actionButtonText,
                        action.primary && styles.actionButtonTextPrimary,
                      ]}
                    >
                      {action.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          <TouchableOpacity
            style={styles.dismissButton}
            onPress={() => handleDismiss(item)}
          >
            <Ionicons name="close" size={18} color="#64748B" />
          </TouchableOpacity>
        </View>
      </TouchableOpacity>
    );
  };

  const renderHeader = () => (
    <View style={styles.filterContainer}>
      <View style={styles.filterTabs}>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'all' && styles.filterTabActive]}
          onPress={() => setFilter('all')}
        >
          <Text style={[styles.filterTabText, filter === 'all' && styles.filterTabTextActive]}>
            Toutes ({data?.total || 0})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'unread' && styles.filterTabActive]}
          onPress={() => setFilter('unread')}
        >
          <Text style={[styles.filterTabText, filter === 'unread' && styles.filterTabTextActive]}>
            Non lues ({data?.unread_count || 0})
          </Text>
        </TouchableOpacity>
      </View>

      {(data?.unread_count || 0) > 0 && (
        <TouchableOpacity onPress={handleMarkAllRead}>
          <Text style={styles.markAllText}>Tout marquer comme lu</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Notifications',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
          headerRight: () => (
            <TouchableOpacity
              onPress={() => router.push('/settings/notifications')}
              style={styles.headerButton}
            >
              <Ionicons name="settings-outline" size={24} color="#94A3B8" />
            </TouchableOpacity>
          ),
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        {isLoading ? (
          <LoadingSpinner fullScreen message="Chargement des notifications..." />
        ) : (
          <FlatList
            data={data?.notifications || []}
            renderItem={renderNotification}
            keyExtractor={(item) => item.id}
            ListHeaderComponent={renderHeader}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <EmptyState
                icon="notifications-outline"
                title="Aucune notification"
                description={
                  filter === 'unread'
                    ? "Vous avez lu toutes vos notifications"
                    : "Vous n'avez pas encore reçu de notifications"
                }
              />
            }
            refreshControl={
              <RefreshControl
                refreshing={isRefetching}
                onRefresh={refetch}
                tintColor="#19D38C"
              />
            }
          />
        )}
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  listContent: {
    padding: 20,
    paddingBottom: 40,
  },
  headerButton: {
    marginRight: 8,
    padding: 4,
  },
  filterContainer: {
    marginBottom: 20,
  },
  filterTabs: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 4,
    marginBottom: 12,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  filterTabActive: {
    backgroundColor: '#0A0F1C',
  },
  filterTabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#64748B',
  },
  filterTabTextActive: {
    color: '#F1F5F9',
  },
  markAllText: {
    fontSize: 13,
    color: '#19D38C',
    fontWeight: '500',
    textAlign: 'center',
  },
  notificationCard: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
  },
  notificationUnread: {
    borderLeftWidth: 3,
    borderLeftColor: '#19D38C',
  },
  notificationContent: {
    flexDirection: 'row',
    padding: 16,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textContent: {
    flex: 1,
    marginLeft: 12,
    marginRight: 8,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 4,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
    flex: 1,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
  },
  notificationMessage: {
    fontSize: 13,
    color: '#94A3B8',
    lineHeight: 18,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timestamp: {
    fontSize: 11,
    color: '#64748B',
  },
  unreadDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#19D38C',
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
  },
  actionButton: {
    backgroundColor: '#334155',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  actionButtonPrimary: {
    backgroundColor: '#19D38C',
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  actionButtonTextPrimary: {
    color: '#0A0F1C',
  },
  dismissButton: {
    padding: 4,
    alignSelf: 'flex-start',
  },
});
