/**
 * MarketGPS Mobile - Watchlist Screen
 */

import React from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api, WatchlistItem } from '@/lib/api';
import { AssetCard, LoadingSpinner, EmptyState, Button } from '@/components/ui';
import { useIsAuthenticated } from '@/store/auth';

export default function WatchlistScreen() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const isAuthenticated = useIsAuthenticated();
  
  // Fetch watchlist
  const { data: watchlist, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['watchlist'],
    queryFn: () => api.getWatchlist(),
    enabled: isAuthenticated,
  });
  
  // Remove from watchlist mutation
  const removeMutation = useMutation({
    mutationFn: (ticker: string) => api.removeFromWatchlist(ticker),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
    onError: (error) => {
      Alert.alert('Erreur', 'Impossible de retirer cet actif de la watchlist');
    },
  });
  
  const handleRemove = (ticker: string) => {
    Alert.alert(
      'Retirer de la watchlist',
      `Voulez-vous retirer ${ticker} de votre watchlist ?`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Retirer',
          style: 'destructive',
          onPress: () => removeMutation.mutate(ticker),
        },
      ]
    );
  };
  
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Text style={styles.title}>Watchlist</Text>
        </View>
        <EmptyState
          icon="log-in-outline"
          title="Connexion requise"
          description="Connectez-vous pour accéder à votre watchlist personnalisée"
          actionLabel="Se connecter"
          onAction={() => router.push('/(auth)/login')}
        />
      </SafeAreaView>
    );
  }
  
  const renderItem = ({ item }: { item: WatchlistItem }) => (
    <AssetCard
      asset={item.asset || { symbol: item.ticker, name: item.ticker, asset_type: 'EQUITY', market_scope: 'US_EU', score_total: null, asset_id: item.ticker }}
      showWatchlistButton
      isInWatchlist
      onWatchlistToggle={() => handleRemove(item.ticker)}
    />
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Watchlist</Text>
        {watchlist && watchlist.length > 0 && (
          <Text style={styles.count}>{watchlist.length} actifs</Text>
        )}
      </View>
      
      {isLoading ? (
        <LoadingSpinner fullScreen message="Chargement..." />
      ) : (
        <FlatList
          data={watchlist || []}
          renderItem={renderItem}
          keyExtractor={(item) => item.ticker}
          ListEmptyComponent={
            <EmptyState
              icon="bookmark-outline"
              title="Watchlist vide"
              description="Ajoutez des actifs à votre watchlist pour les suivre facilement"
              actionLabel="Explorer les actifs"
              onAction={() => router.push('/explorer')}
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
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
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  count: {
    fontSize: 14,
    color: '#64748B',
  },
  listContent: {
    padding: 20,
    paddingTop: 0,
    flexGrow: 1,
  },
});
