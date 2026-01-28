/**
 * MarketGPS Mobile - Notifications Settings Screen
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Switch,
  Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/lib/api';
import { Card, LoadingSpinner } from '@/components/ui';
import { useIsAuthenticated } from '@/store/auth';

export default function NotificationsScreen() {
  const queryClient = useQueryClient();
  const isAuthenticated = useIsAuthenticated();
  
  // Fetch notification settings
  const { data: settings, isLoading } = useQuery({
    queryKey: ['notifications', 'settings'],
    queryFn: () => api.getNotificationSettings(),
    enabled: isAuthenticated,
  });
  
  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (newSettings: Record<string, boolean>) =>
      api.updateNotificationSettings(newSettings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'settings'] });
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de sauvegarder les préférences');
    },
  });
  
  const handleToggle = (key: string, value: boolean) => {
    updateMutation.mutate({ [key]: value });
  };
  
  if (!isAuthenticated) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="notifications-off-outline" size={48} color="#64748B" />
        <Text style={styles.centerTitle}>Connexion requise</Text>
        <Text style={styles.centerText}>
          Connectez-vous pour gérer vos notifications
        </Text>
      </View>
    );
  }
  
  if (isLoading) {
    return <LoadingSpinner fullScreen />;
  }
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Email Notifications */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Email</Text>
        <Card padding="none">
          <NotificationRow
            icon="mail-outline"
            title="Notifications par email"
            description="Recevez les mises à jour importantes"
            value={settings?.emailNotifications ?? true}
            onToggle={(v) => handleToggle('emailNotifications', v)}
          />
        </Card>
      </View>
      
      {/* Alert Types */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Types d'alertes</Text>
        <Card padding="none">
          <NotificationRow
            icon="trending-up-outline"
            title="Alertes marché"
            description="Mouvements significatifs du marché"
            value={settings?.marketAlerts ?? true}
            onToggle={(v) => handleToggle('marketAlerts', v)}
          />
          <NotificationRow
            icon="pricetag-outline"
            title="Alertes prix"
            description="Quand un actif atteint votre cible"
            value={settings?.priceAlerts ?? true}
            onToggle={(v) => handleToggle('priceAlerts', v)}
          />
          <NotificationRow
            icon="briefcase-outline"
            title="Mises à jour portefeuille"
            description="Changements dans votre watchlist"
            value={settings?.portfolioUpdates ?? true}
            onToggle={(v) => handleToggle('portfolioUpdates', v)}
            last
          />
        </Card>
      </View>
      
      {/* Info */}
      <Card style={styles.infoCard}>
        <Ionicons name="information-circle-outline" size={20} color="#64748B" />
        <Text style={styles.infoText}>
          Vous pouvez ajuster les notifications push dans les paramètres de votre appareil.
        </Text>
      </Card>
    </ScrollView>
  );
}

function NotificationRow({
  icon,
  title,
  description,
  value,
  onToggle,
  last = false,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  description: string;
  value: boolean;
  onToggle: (value: boolean) => void;
  last?: boolean;
}) {
  return (
    <View style={[styles.row, !last && styles.rowBorder]}>
      <View style={styles.rowIcon}>
        <Ionicons name={icon} size={20} color="#19D38C" />
      </View>
      <View style={styles.rowContent}>
        <Text style={styles.rowTitle}>{title}</Text>
        <Text style={styles.rowDescription}>{description}</Text>
      </View>
      <Switch
        value={value}
        onValueChange={onToggle}
        trackColor={{ false: '#334155', true: '#19D38C40' }}
        thumbColor={value ? '#19D38C' : '#64748B'}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: '#0A0F1C',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  centerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F1F5F9',
    marginTop: 16,
  },
  centerText: {
    fontSize: 14,
    color: '#94A3B8',
    marginTop: 8,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  rowBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  rowIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    backgroundColor: '#19D38C10',
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowContent: {
    flex: 1,
    marginLeft: 12,
    marginRight: 12,
  },
  rowTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  rowDescription: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#94A3B8',
    lineHeight: 18,
  },
});
