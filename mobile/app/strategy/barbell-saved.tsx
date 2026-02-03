/**
 * MarketGPS Mobile - Saved Barbell Portfolios Screen
 */

import React from 'react';
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
import { api, BarbellPortfolio } from '@/lib/api';
import { LoadingSpinner, EmptyState, Card } from '@/components/ui';

const RISK_LABELS: Record<string, string> = {
  conservative: 'Conservateur',
  moderate: 'Modéré',
  aggressive: 'Agressif',
};

const RISK_COLORS: Record<string, string> = {
  conservative: '#3B82F6',
  moderate: '#F59E0B',
  aggressive: '#EF4444',
};

export default function SavedBarbellPortfoliosScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();

  // Fetch saved portfolios
  const { data: portfolios, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['barbell', 'portfolios'],
    queryFn: () => api.getSavedBarbellPortfolios(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (portfolioId: string) => api.deleteBarbellPortfolio(portfolioId),
    onSuccess: () => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      queryClient.invalidateQueries({ queryKey: ['barbell', 'portfolios'] });
    },
    onError: () => {
      Alert.alert('Erreur', 'Impossible de supprimer le portfolio');
    },
  });

  const handleDelete = (portfolio: BarbellPortfolio) => {
    Alert.alert(
      'Supprimer le portfolio',
      `Êtes-vous sûr de vouloir supprimer "${portfolio.name}" ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Supprimer',
          style: 'destructive',
          onPress: () => deleteMutation.mutate(portfolio.id),
        },
      ]
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const renderItem = ({ item }: { item: BarbellPortfolio }) => {
    const coreCount = item.core_assets?.length || 0;
    const satelliteCount = item.satellite_assets?.length || 0;

    return (
      <Card style={styles.portfolioCard}>
        <View style={styles.portfolioHeader}>
          <View style={styles.portfolioInfo}>
            <Text style={styles.portfolioName}>{item.name}</Text>
            <View style={styles.badges}>
              <View
                style={[
                  styles.riskBadge,
                  { backgroundColor: `${RISK_COLORS[item.risk_profile] || '#64748B'}20` },
                ]}
              >
                <Text
                  style={[
                    styles.riskBadgeText,
                    { color: RISK_COLORS[item.risk_profile] || '#64748B' },
                  ]}
                >
                  {RISK_LABELS[item.risk_profile] || item.risk_profile}
                </Text>
              </View>
              <View style={styles.marketBadge}>
                <Text style={styles.marketBadgeText}>
                  {item.market_scope === 'US_EU' ? 'US/EU' : 'Afrique'}
                </Text>
              </View>
            </View>
          </View>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDelete(item)}
          >
            <Ionicons name="trash-outline" size={20} color="#EF4444" />
          </TouchableOpacity>
        </View>

        <View style={styles.assetsSection}>
          <View style={styles.assetGroup}>
            <View style={styles.assetGroupHeader}>
              <View style={styles.coreDot} />
              <Text style={styles.assetGroupLabel}>Core ({coreCount})</Text>
            </View>
            <Text style={styles.assetTickers} numberOfLines={1}>
              {item.core_assets?.map((a) => a.ticker).join(', ') || '-'}
            </Text>
          </View>

          <View style={styles.assetGroup}>
            <View style={styles.assetGroupHeader}>
              <View style={styles.satelliteDot} />
              <Text style={styles.assetGroupLabel}>Satellite ({satelliteCount})</Text>
            </View>
            <Text style={styles.assetTickers} numberOfLines={1}>
              {item.satellite_assets?.map((a) => a.ticker).join(', ') || '-'}
            </Text>
          </View>
        </View>

        <View style={styles.portfolioFooter}>
          <Text style={styles.dateText}>Créé le {formatDate(item.created_at)}</Text>
        </View>
      </Card>
    );
  };

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Mes Portfolios Barbell',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
        {isLoading ? (
          <LoadingSpinner fullScreen message="Chargement des portfolios..." />
        ) : (
          <FlatList
            data={portfolios || []}
            renderItem={renderItem}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.listContent}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <EmptyState
                icon="folder-outline"
                title="Aucun portfolio sauvegardé"
                description="Créez un portfolio Barbell et sauvegardez-le pour le retrouver ici"
                actionLabel="Créer un Portfolio"
                onAction={() => router.back()}
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
  portfolioCard: {
    marginBottom: 16,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  portfolioInfo: {
    flex: 1,
  },
  portfolioName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 8,
  },
  badges: {
    flexDirection: 'row',
    gap: 8,
  },
  riskBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  riskBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  marketBadge: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  marketBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  deleteButton: {
    padding: 8,
    marginLeft: 12,
  },
  assetsSection: {
    gap: 12,
  },
  assetGroup: {
    backgroundColor: '#0A0F1C',
    borderRadius: 8,
    padding: 12,
  },
  assetGroupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  coreDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#19D38C',
  },
  satelliteDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#8B5CF6',
  },
  assetGroupLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  assetTickers: {
    fontSize: 14,
    color: '#F1F5F9',
  },
  portfolioFooter: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
  },
  dateText: {
    fontSize: 12,
    color: '#64748B',
  },
});
