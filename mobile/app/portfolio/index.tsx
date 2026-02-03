/**
 * MarketGPS Mobile - Portfolio Overview Screen
 * Vue d'ensemble du portefeuille avec performance et allocation
 */

import React from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api, PortfolioSummary } from '@/lib/api';
import { Card, LoadingSpinner, EmptyState, Button } from '@/components/ui';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const ALLOCATION_COLORS = [
  '#19D38C',
  '#8B5CF6',
  '#F59E0B',
  '#3B82F6',
  '#EF4444',
  '#EC4899',
  '#22C55E',
  '#06B6D4',
];

function formatCurrency(value: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export default function PortfolioOverviewScreen() {
  const router = useRouter();

  const { data: summary, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: () => api.getPortfolioSummary(),
  });

  const handleNavigateToAccounts = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push('/portfolio/accounts' as any);
  };

  const handleNavigateToPositions = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.push('/portfolio/positions' as any);
  };

  if (isLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Mon Portefeuille',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <LoadingSpinner fullScreen message="Chargement du portefeuille..." />
      </>
    );
  }

  // Show empty state if no portfolio data
  if (!summary || summary.accounts_count === 0) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            headerTitle: 'Mon Portefeuille',
            headerStyle: { backgroundColor: '#0A0F1C' },
            headerTintColor: '#F1F5F9',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.emptyContainer}>
            <EmptyState
              icon="wallet-outline"
              title="Aucun compte"
              description="Créez un compte pour commencer à suivre vos investissements"
              actionLabel="Créer un compte"
              onAction={handleNavigateToAccounts}
            />
          </View>
        </SafeAreaView>
      </>
    );
  }

  const isProfitable = summary.total_pnl >= 0;

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          headerTitle: 'Mon Portefeuille',
          headerStyle: { backgroundColor: '#0A0F1C' },
          headerTintColor: '#F1F5F9',
        }}
      />

      <SafeAreaView style={styles.container} edges={['bottom']}>
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
          {/* Total Value Card */}
          <Card style={styles.valueCard}>
            <Text style={styles.valueLabel}>Valeur Totale</Text>
            <Text style={styles.valueAmount}>
              {formatCurrency(summary.total_value, summary.currency)}
            </Text>

            <View style={styles.pnlContainer}>
              <View style={[styles.pnlBadge, isProfitable ? styles.pnlPositive : styles.pnlNegative]}>
                <Ionicons
                  name={isProfitable ? 'trending-up' : 'trending-down'}
                  size={16}
                  color={isProfitable ? '#22C55E' : '#EF4444'}
                />
                <Text style={[styles.pnlText, isProfitable ? styles.pnlTextPositive : styles.pnlTextNegative]}>
                  {formatCurrency(Math.abs(summary.total_pnl), summary.currency)} ({formatPercent(summary.total_pnl_pct)})
                </Text>
              </View>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{summary.accounts_count}</Text>
                <Text style={styles.statLabel}>Comptes</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{summary.positions_count}</Text>
                <Text style={styles.statLabel}>Positions</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{formatCurrency(summary.total_cost, summary.currency)}</Text>
                <Text style={styles.statLabel}>Investi</Text>
              </View>
            </View>
          </Card>

          {/* Quick Actions */}
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={styles.quickAction}
              onPress={handleNavigateToAccounts}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#3B82F620' }]}>
                <Ionicons name="wallet-outline" size={24} color="#3B82F6" />
              </View>
              <Text style={styles.quickActionText}>Comptes</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickAction}
              onPress={handleNavigateToPositions}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#8B5CF620' }]}>
                <Ionicons name="briefcase-outline" size={24} color="#8B5CF6" />
              </View>
              <Text style={styles.quickActionText}>Positions</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.quickAction}
              onPress={() => router.push('/portfolio/import' as any)}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: '#F59E0B20' }]}>
                <Ionicons name="download-outline" size={24} color="#F59E0B" />
              </View>
              <Text style={styles.quickActionText}>Importer</Text>
            </TouchableOpacity>
          </View>

          {/* Top Holdings */}
          {summary.top_holdings && summary.top_holdings.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Top Holdings</Text>
              <Card padding="none">
                {summary.top_holdings.map((holding, index) => (
                  <TouchableOpacity
                    key={holding.ticker}
                    style={styles.holdingItem}
                    onPress={() => router.push(`/asset/${holding.ticker}`)}
                  >
                    <View style={styles.holdingRank}>
                      <Text style={styles.holdingRankText}>{index + 1}</Text>
                    </View>
                    <View style={styles.holdingInfo}>
                      <Text style={styles.holdingTicker}>{holding.ticker}</Text>
                      <Text style={styles.holdingName} numberOfLines={1}>
                        {holding.name}
                      </Text>
                    </View>
                    <View style={styles.holdingStats}>
                      <Text style={styles.holdingWeight}>{(holding.weight * 100).toFixed(1)}%</Text>
                      <Text style={[
                        styles.holdingPnl,
                        holding.pnl_pct >= 0 ? styles.textPositive : styles.textNegative
                      ]}>
                        {formatPercent(holding.pnl_pct)}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </Card>
            </View>
          )}

          {/* Allocation by Type */}
          {summary.allocation_by_type && Object.keys(summary.allocation_by_type).length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Allocation par Type</Text>
              <Card>
                {/* Simple bar chart */}
                <View style={styles.allocationChart}>
                  {Object.entries(summary.allocation_by_type).map(([type, weight], index) => (
                    <View key={type} style={styles.allocationRow}>
                      <View style={styles.allocationLabel}>
                        <View
                          style={[
                            styles.allocationDot,
                            { backgroundColor: ALLOCATION_COLORS[index % ALLOCATION_COLORS.length] }
                          ]}
                        />
                        <Text style={styles.allocationText}>{type}</Text>
                      </View>
                      <View style={styles.allocationBarContainer}>
                        <View
                          style={[
                            styles.allocationBar,
                            {
                              width: `${(weight as number) * 100}%`,
                              backgroundColor: ALLOCATION_COLORS[index % ALLOCATION_COLORS.length],
                            }
                          ]}
                        />
                      </View>
                      <Text style={styles.allocationPercent}>
                        {((weight as number) * 100).toFixed(1)}%
                      </Text>
                    </View>
                  ))}
                </View>
              </Card>
            </View>
          )}

          {/* Last Updated */}
          <Text style={styles.lastUpdated}>
            Dernière mise à jour: {new Date(summary.last_updated).toLocaleString('fr-FR')}
          </Text>
        </ScrollView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0F1C',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  valueCard: {
    marginBottom: 20,
    alignItems: 'center',
  },
  valueLabel: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 8,
  },
  valueAmount: {
    fontSize: 36,
    fontWeight: '800',
    color: '#F1F5F9',
    letterSpacing: -1,
  },
  pnlContainer: {
    marginTop: 12,
  },
  pnlBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    gap: 6,
  },
  pnlPositive: {
    backgroundColor: '#22C55E20',
  },
  pnlNegative: {
    backgroundColor: '#EF444420',
  },
  pnlText: {
    fontSize: 14,
    fontWeight: '600',
  },
  pnlTextPositive: {
    color: '#22C55E',
  },
  pnlTextNegative: {
    color: '#EF4444',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#1E293B',
    width: '100%',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  statLabel: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: '#1E293B',
  },
  quickActions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  quickAction: {
    flex: 1,
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    gap: 8,
  },
  quickActionIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
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
  holdingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  holdingRank: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#334155',
    alignItems: 'center',
    justifyContent: 'center',
  },
  holdingRankText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },
  holdingInfo: {
    flex: 1,
    marginLeft: 12,
  },
  holdingTicker: {
    fontSize: 15,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  holdingName: {
    fontSize: 12,
    color: '#64748B',
    marginTop: 2,
  },
  holdingStats: {
    alignItems: 'flex-end',
  },
  holdingWeight: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  holdingPnl: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
  },
  textPositive: {
    color: '#22C55E',
  },
  textNegative: {
    color: '#EF4444',
  },
  allocationChart: {
    gap: 12,
  },
  allocationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  allocationLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 80,
    gap: 8,
  },
  allocationDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  allocationText: {
    fontSize: 12,
    color: '#94A3B8',
  },
  allocationBarContainer: {
    flex: 1,
    height: 8,
    backgroundColor: '#1E293B',
    borderRadius: 4,
    overflow: 'hidden',
  },
  allocationBar: {
    height: '100%',
    borderRadius: 4,
  },
  allocationPercent: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F1F5F9',
    width: 48,
    textAlign: 'right',
  },
  lastUpdated: {
    fontSize: 11,
    color: '#475569',
    textAlign: 'center',
    marginTop: 8,
  },
});
