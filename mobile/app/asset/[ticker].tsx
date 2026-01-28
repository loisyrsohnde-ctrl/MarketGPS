/**
 * MarketGPS Mobile - Asset Detail Screen
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useNavigation } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { api } from '@/lib/api';
import { Card, ScoreBadge, LoadingSpinner, Button, PriceChart } from '@/components/ui';
import { getScoreColor } from '@/lib/config';
import { useIsAuthenticated } from '@/store/auth';

const CHART_PERIODS = [
  { key: '1d', label: '1J' },
  { key: '1w', label: '1S' },
  { key: '30d', label: '1M' },
  { key: '3m', label: '3M' },
  { key: '1y', label: '1A' },
  { key: '5y', label: '5A' },
];

export default function AssetDetailScreen() {
  const { ticker } = useLocalSearchParams<{ ticker: string }>();
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  const isAuthenticated = useIsAuthenticated();
  const [chartPeriod, setChartPeriod] = useState('30d');
  
  // Fetch asset details
  const { data: asset, isLoading, error } = useQuery({
    queryKey: ['asset', ticker],
    queryFn: () => api.getAssetDetails(ticker!),
    enabled: !!ticker,
  });
  
  // Check watchlist status
  const { data: watchlistStatus } = useQuery({
    queryKey: ['watchlist', 'check', ticker],
    queryFn: () => api.checkInWatchlist(ticker!),
    enabled: !!ticker && isAuthenticated,
  });

  // Fetch chart data
  const { data: chartData, isLoading: chartLoading, error: chartError } = useQuery({
    queryKey: ['asset', 'chart', ticker, chartPeriod],
    queryFn: () => api.getAssetChart(ticker!, chartPeriod),
    enabled: !!ticker,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
  
  // Watchlist mutations
  const addToWatchlist = useMutation({
    mutationFn: () => api.addToWatchlist(ticker!, asset?.market_scope || 'US_EU'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      queryClient.invalidateQueries({ queryKey: ['watchlist', 'check', ticker] });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    },
    onError: (error) => {
      console.error('Watchlist add error:', error);
      Alert.alert('Erreur', 'Impossible d\'ajouter cet actif à votre watchlist');
    },
  });
  
  const removeFromWatchlist = useMutation({
    mutationFn: () => api.removeFromWatchlist(ticker!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      queryClient.invalidateQueries({ queryKey: ['watchlist', 'check', ticker] });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    },
    onError: (error) => {
      console.error('Watchlist remove error:', error);
      Alert.alert('Erreur', 'Impossible de retirer cet actif de votre watchlist');
    },
  });
  
  const isInWatchlist = watchlistStatus?.in_watchlist ?? false;
  
  const handleWatchlistToggle = () => {
    if (!isAuthenticated) {
      Alert.alert('Connexion requise', 'Connectez-vous pour ajouter des actifs à votre watchlist');
      return;
    }
    
    if (isInWatchlist) {
      removeFromWatchlist.mutate();
    } else {
      addToWatchlist.mutate();
    }
  };
  
  // Set navigation title
  React.useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: asset?.symbol || ticker,
    });
  }, [asset, ticker, navigation]);
  
  if (isLoading) {
    return <LoadingSpinner fullScreen message="Chargement..." />;
  }
  
  if (error || !asset) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={48} color="#EF4444" />
          <Text style={styles.errorText}>Impossible de charger cet actif</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  const priceChange = asset.pct_change_1d ?? 0;
  const isPositive = priceChange >= 0;
  
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.symbol}>{asset.symbol}</Text>
          <View style={styles.typeBadge}>
            <Text style={styles.typeText}>{asset.asset_type}</Text>
          </View>
        </View>
        <TouchableOpacity
          style={[styles.watchlistButton, isInWatchlist && styles.watchlistButtonActive]}
          onPress={handleWatchlistToggle}
        >
          <Ionicons
            name={isInWatchlist ? 'bookmark' : 'bookmark-outline'}
            size={24}
            color={isInWatchlist ? '#19D38C' : '#64748B'}
          />
        </TouchableOpacity>
      </View>
      
      <Text style={styles.name}>{asset.name}</Text>
      
      {/* Price Section */}
      <View style={styles.priceSection}>
        <Text style={styles.price}>
          ${asset.last_price?.toLocaleString(undefined, { minimumFractionDigits: 2 }) ?? '—'}
        </Text>
        <View style={[styles.changeBadge, isPositive ? styles.changePositive : styles.changeNegative]}>
          <Ionicons
            name={isPositive ? 'arrow-up' : 'arrow-down'}
            size={14}
            color={isPositive ? '#22C55E' : '#EF4444'}
          />
          <Text style={[styles.changeText, isPositive ? styles.textPositive : styles.textNegative]}>
            {Math.abs(priceChange).toFixed(2)}%
          </Text>
        </View>
      </View>
      
      {/* Chart Period Selector */}
      <View style={styles.periodSelector}>
        {CHART_PERIODS.map(({ key, label }) => (
          <TouchableOpacity
            key={key}
            style={[styles.periodButton, chartPeriod === key && styles.periodButtonActive]}
            onPress={() => setChartPeriod(key)}
          >
            <Text
              style={[styles.periodText, chartPeriod === key && styles.periodTextActive]}
            >
              {label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Price Chart */}
      <View style={styles.chartContainer}>
        <PriceChart
          data={chartData || []}
          isLoading={chartLoading}
          error={!!chartError}
          period={chartPeriod}
          height={220}
        />
      </View>

      {/* Score Card */}
      <Card style={styles.scoreCard}>
        <View style={styles.scoreHeader}>
          <Text style={styles.scoreTitle}>Score Global</Text>
          <ScoreBadge score={asset.score_total} size="lg" showLabel />
        </View>

        <View style={styles.scoreBreakdown}>
          <ScoreItem label="Valeur" score={asset.score_value} />
          <ScoreItem label="Momentum" score={asset.score_momentum} />
          <ScoreItem label="Sécurité" score={asset.score_safety} />
        </View>

        {/* Score Calculation Explanation */}
        <View style={styles.scoreExplanation}>
          <View style={styles.scoreFormula}>
            <Text style={styles.formulaLabel}>Formule</Text>
            <Text style={styles.formulaText}>
              Score = (Valeur × 0.4) + (Momentum × 0.3) + (Sécurité × 0.3)
            </Text>
          </View>
          <View style={styles.scoreCalculation}>
            <Text style={styles.calculationText}>
              = ({asset.score_value?.toFixed(0) ?? 0} × 0.4) + ({asset.score_momentum?.toFixed(0) ?? 0} × 0.3) + ({asset.score_safety?.toFixed(0) ?? 0} × 0.3)
            </Text>
            <Text style={styles.calculationResult}>
              = {asset.score_total?.toFixed(0) ?? '—'}
            </Text>
          </View>
        </View>
      </Card>
      
      {/* Metrics Grid */}
      <View style={styles.metricsGrid}>
        <MetricCard label="RSI (14)" value={asset.rsi?.toFixed(1)} />
        <MetricCard label="Volatilité" value={asset.vol_annual ? `${(asset.vol_annual * 100).toFixed(1)}%` : null} />
        <MetricCard label="Max DD" value={asset.max_drawdown ? `${(asset.max_drawdown * 100).toFixed(1)}%` : null} />
        <MetricCard label="Z-Score" value={asset.zscore?.toFixed(2)} />
      </View>
      
      {/* Additional Info */}
      <Card>
        <Text style={styles.sectionTitle}>Informations</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Marché</Text>
          <Text style={styles.infoValue}>{asset.market_scope === 'US_EU' ? 'US/Europe' : 'Afrique'}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Exchange</Text>
          <Text style={styles.infoValue}>{asset.exchange || '—'}</Text>
        </View>
        {asset.pe_ratio && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>P/E Ratio</Text>
            <Text style={styles.infoValue}>{asset.pe_ratio.toFixed(2)}</Text>
          </View>
        )}
        {asset.dividend_yield && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Dividende</Text>
            <Text style={styles.infoValue}>{(asset.dividend_yield * 100).toFixed(2)}%</Text>
          </View>
        )}
        {asset.market_cap && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Cap. Marché</Text>
            <Text style={styles.infoValue}>
              ${(asset.market_cap / 1e9).toFixed(2)}B
            </Text>
          </View>
        )}
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>État</Text>
          <Text style={styles.infoValue}>{asset.state_label || 'Normal'}</Text>
        </View>
      </Card>
      
      {/* Institutional Guard (if available) */}
      {asset.score_institutional && (
        <Card style={styles.institutionalCard}>
          <View style={styles.institutionalHeader}>
            <Ionicons name="shield-checkmark-outline" size={24} color="#19D38C" />
            <Text style={styles.institutionalTitle}>Garde Institutionnel</Text>
          </View>
          <View style={styles.scoreBreakdown}>
            <ScoreItem label="Score Inst." score={asset.score_institutional} />
            <View style={styles.scoreItem}>
              <Text style={styles.scoreItemLabel}>Liquidité</Text>
              <Text style={styles.scoreItemValue}>{asset.liquidity_tier || '—'}</Text>
            </View>
            <View style={styles.scoreItem}>
              <Text style={styles.scoreItemLabel}>Horizon</Text>
              <Text style={styles.scoreItemValue}>
                {asset.horizon_years ? `${asset.horizon_years}A` : '—'}
              </Text>
            </View>
          </View>
        </Card>
      )}
    </ScrollView>
  );
}

function ScoreItem({ label, score }: { label: string; score?: number | null }) {
  const color = getScoreColor(score ?? null);
  return (
    <View style={styles.scoreItem}>
      <Text style={styles.scoreItemLabel}>{label}</Text>
      <Text style={[styles.scoreItemValue, { color }]}>
        {score != null ? Math.round(score) : '—'}
      </Text>
    </View>
  );
}

function MetricCard({ label, value }: { label: string; value?: string | null }) {
  return (
    <Card style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value ?? '—'}</Text>
    </Card>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  symbol: {
    fontSize: 28,
    fontWeight: '800',
    color: '#F1F5F9',
  },
  typeBadge: {
    backgroundColor: '#1E293B',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  typeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#64748B',
  },
  watchlistButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#1E293B',
    alignItems: 'center',
    justifyContent: 'center',
  },
  watchlistButtonActive: {
    backgroundColor: '#19D38C20',
  },
  name: {
    fontSize: 16,
    color: '#94A3B8',
    marginBottom: 20,
  },
  priceSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
  },
  price: {
    fontSize: 36,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  changeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  changePositive: {
    backgroundColor: 'rgba(34, 197, 94, 0.15)',
  },
  changeNegative: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
  },
  changeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  textPositive: {
    color: '#22C55E',
  },
  textNegative: {
    color: '#EF4444',
  },
  periodSelector: {
    flexDirection: 'row',
    backgroundColor: '#1E293B',
    borderRadius: 12,
    padding: 4,
    marginBottom: 24,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  periodButtonActive: {
    backgroundColor: '#334155',
  },
  periodText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#64748B',
  },
  periodTextActive: {
    color: '#F1F5F9',
  },
  chartContainer: {
    marginBottom: 24,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#111827',
  },
  scoreCard: {
    marginBottom: 16,
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  scoreTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  scoreBreakdown: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  scoreExplanation: {
    marginTop: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#334155',
  },
  scoreFormula: {
    marginBottom: 12,
  },
  formulaLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  formulaText: {
    fontSize: 13,
    color: '#94A3B8',
    fontFamily: 'monospace',
  },
  scoreCalculation: {
    backgroundColor: '#0F172A',
    borderRadius: 8,
    padding: 12,
  },
  calculationText: {
    fontSize: 12,
    color: '#64748B',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  calculationResult: {
    fontSize: 14,
    fontWeight: '700',
    color: '#19D38C',
    fontFamily: 'monospace',
  },
  scoreItem: {
    alignItems: 'center',
  },
  scoreItemLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  scoreItemValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    minWidth: (Dimensions.get('window').width - 52) / 2,
  },
  metricLabel: {
    fontSize: 12,
    color: '#64748B',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#334155',
  },
  infoLabel: {
    fontSize: 14,
    color: '#94A3B8',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#F1F5F9',
  },
  institutionalCard: {
    marginTop: 16,
  },
  institutionalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  institutionalTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#F1F5F9',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  errorText: {
    fontSize: 16,
    color: '#94A3B8',
    marginTop: 12,
  },
});
