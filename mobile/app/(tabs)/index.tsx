/**
 * MarketGPS Mobile - Dashboard Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/lib/api';
import { Card, AssetCard, LoadingSpinner, GpsLoading, ScoreBadge } from '@/components/ui';
import { useUser, useSubscription } from '@/store/auth';
import { MARKET_SCOPES, type MarketScope } from '@/lib/config';

export default function DashboardScreen() {
  const router = useRouter();
  const user = useUser();
  const subscription = useSubscription();
  const [selectedScope, setSelectedScope] = useState<MarketScope>('US_EU');
  
  // Fetch top scored assets with error handling
  const { 
    data: topScored, 
    isLoading, 
    refetch, 
    isRefetching,
    error: topScoredError,
    isError: hasTopScoredError,
  } = useQuery({
    queryKey: ['topScored', selectedScope],
    queryFn: async () => {
      console.log('[Dashboard] Fetching top scored for scope:', selectedScope);
      try {
        const result = await api.getTopScored({ limit: 10, market_scope: selectedScope });
        console.log('[Dashboard] Got', result?.data?.length || 0, 'assets');
        return result;
      } catch (err) {
        console.error('[Dashboard] Error fetching top scored:', err);
        throw err;
      }
    },
    retry: 2,
    staleTime: 60000,
  });
  
  // Fetch scope counts with error handling
  const { data: counts, error: countsError } = useQuery({
    queryKey: ['scopeCounts'],
    queryFn: async () => {
      console.log('[Dashboard] Fetching scope counts...');
      try {
        const result = await api.getScopeCounts();
        console.log('[Dashboard] Scope counts:', result);
        return result;
      } catch (err) {
        console.error('[Dashboard] Error fetching counts:', err);
        throw err;
      }
    },
    retry: 2,
    staleTime: 300000,
  });
  
  const isPro = subscription?.is_active ?? false;
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>
            {user ? `Bonjour${user.email ? ', ' + user.email.split('@')[0] : ''}` : 'Bienvenue'}
          </Text>
          <Text style={styles.title}>MarketGPS</Text>
        </View>
        <TouchableOpacity
          style={styles.notificationButton}
          onPress={() => router.push('/settings')}
        >
          <Ionicons name="notifications-outline" size={24} color="#F1F5F9" />
          {!isPro && (
            <View style={styles.proBadge}>
              <Text style={styles.proBadgeText}>PRO</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={refetch}
            tintColor="#19D38C"
          />
        }
      >
        {/* Scope Selector */}
        <View style={styles.scopeSelector}>
          {Object.keys(MARKET_SCOPES).map((scope) => (
            <TouchableOpacity
              key={scope}
              style={[
                styles.scopeButton,
                selectedScope === scope && styles.scopeButtonActive,
              ]}
              onPress={() => setSelectedScope(scope as MarketScope)}
            >
              <Text
                style={[
                  styles.scopeButtonText,
                  selectedScope === scope && styles.scopeButtonTextActive,
                ]}
              >
                {scope === 'US_EU' ? 'US/EU' : 'Afrique'}
              </Text>
              {counts && (
                <Text style={styles.scopeCount}>
                  {counts[scope as keyof typeof counts]?.toLocaleString() ?? 0}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
        
        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() => router.push('/strategy/barbell')}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: '#19D38C20' }]}>
              <Ionicons name="barbell-outline" size={24} color="#19D38C" />
            </View>
            <Text style={styles.quickActionText}>Barbell</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() => router.push('/settings/strategies')}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: '#8B5CF620' }]}>
              <Ionicons name="layers-outline" size={24} color="#8B5CF6" />
            </View>
            <Text style={styles.quickActionText}>Stratégies</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickAction}
            onPress={() => router.push('/settings/markets')}
          >
            <View style={[styles.quickActionIcon, { backgroundColor: '#F5973520' }]}>
              <Ionicons name="trending-up-outline" size={24} color="#F59735" />
            </View>
            <Text style={styles.quickActionText}>Marchés</Text>
          </TouchableOpacity>
        </View>
        
        {/* Top Scored Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Top Scores</Text>
            <TouchableOpacity onPress={() => router.push('/explorer')}>
              <Text style={styles.seeAllLink}>Voir tout</Text>
            </TouchableOpacity>
          </View>
          
          {isLoading ? (
            <GpsLoading message="Recherche des meilleures opportunités..." size="medium" />
          ) : hasTopScoredError ? (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
              <Text style={styles.errorTitle}>Erreur de chargement</Text>
              <Text style={styles.errorText}>
                {(topScoredError as Error)?.message || 'Impossible de charger les données'}
              </Text>
              <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
                <Text style={styles.retryButtonText}>Réessayer</Text>
              </TouchableOpacity>
            </View>
          ) : !topScored?.data || topScored.data.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Ionicons name="search-outline" size={48} color="#64748B" />
              <Text style={styles.emptyTitle}>Aucun actif disponible</Text>
              <Text style={styles.emptyText}>
                Aucun actif trouvé pour {selectedScope === 'US_EU' ? 'US/EU' : 'Afrique'}
              </Text>
              <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
                <Text style={styles.retryButtonText}>Actualiser</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View>
              {topScored.data.slice(0, 5).map((asset) => (
                <AssetCard
                  key={asset.asset_id || asset.symbol}
                  asset={asset}
                  showWatchlistButton
                />
              ))}
            </View>
          )}
        </View>
        
        {/* Pro CTA for free users */}
        {!isPro && (
          <Card variant="elevated" style={styles.proCta}>
            <View style={styles.proCtaContent}>
              <Ionicons name="diamond-outline" size={32} color="#19D38C" />
              <View style={styles.proCtaText}>
                <Text style={styles.proCtaTitle}>Passez à Pro</Text>
                <Text style={styles.proCtaDescription}>
                  Accédez à tous les actifs, stratégies et analyses
                </Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.proCtaButton}
              onPress={() => router.push('/checkout')}
            >
              <Text style={styles.proCtaButtonText}>À partir de 9,99€/mois</Text>
              <Ionicons name="arrow-forward" size={16} color="#0A0F1C" />
            </TouchableOpacity>
          </Card>
        )}
      </ScrollView>
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
  greeting: {
    fontSize: 14,
    color: '#94A3B8',
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  notificationButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  proBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: '#19D38C',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  proBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#0A0F1C',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  scopeSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  scopeButton: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  scopeButtonActive: {
    borderColor: '#19D38C',
    backgroundColor: '#19D38C10',
  },
  scopeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#94A3B8',
  },
  scopeButtonTextActive: {
    color: '#19D38C',
  },
  scopeCount: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 4,
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  quickAction: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#94A3B8',
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  seeAllLink: {
    fontSize: 14,
    color: '#19D38C',
    fontWeight: '500',
  },
  proCta: {
    marginTop: 8,
  },
  proCtaContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    marginBottom: 16,
  },
  proCtaText: {
    flex: 1,
  },
  proCtaTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  proCtaDescription: {
    fontSize: 13,
    color: '#94A3B8',
    marginTop: 4,
  },
  proCtaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#19D38C',
    borderRadius: 12,
    paddingVertical: 14,
    gap: 8,
  },
  proCtaButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#0A0F1C',
  },
  // Error state
  errorContainer: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: '#1E293B',
    borderRadius: 16,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 8,
  },
  retryButton: {
    backgroundColor: '#19D38C',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginTop: 16,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#0A0F1C',
  },
  // Empty state
  emptyContainer: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: '#1E293B',
    borderRadius: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    marginTop: 8,
  },
});
