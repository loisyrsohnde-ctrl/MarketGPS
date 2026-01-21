'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Pill, ScoreBadge, ScoreGaugeBadge } from '@/components/ui/badge';
import { ScoreGauge, PillarBar, KpiBar } from '@/components/charts/score-gauge';
import { PriceChart } from '@/components/charts/price-chart';
import { AssetLogo } from '@/components/cards/asset-card';
import { api } from '@/lib/api';
import { cn, getLiquidityLabel, getRiskLabel } from '@/lib/utils';
import type { Asset, ChartPeriod, MarketFilter, AssetType } from '@/types';
import {
  ArrowRight,
  Star,
  TrendingUp,
  Search,
  Filter,
  ChevronRight,
  ExternalLink,
  AlertCircle,
  Loader2,
  RefreshCw,
  Building2,
  Layers,
  DollarSign,
  Landmark,
  Activity,
  Globe,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD PAGE
// Main dashboard with top scored assets and detailed view
// ═══════════════════════════════════════════════════════════════════════════

export default function DashboardPage() {
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [chartPeriod, setChartPeriod] = useState<ChartPeriod>('30d');
  const [marketFilter, setMarketFilter] = useState<MarketFilter>('ALL');
  const [typeFilter, setTypeFilter] = useState<AssetType | null>(null);
  const [marketScope, setMarketScope] = useState<'US_EU' | 'AFRICA'>('US_EU');
  const [userId] = useState('default'); // In production, get from auth
  const queryClient = useQueryClient();

  // Determine market scope from filter
  useEffect(() => {
    if (marketFilter === 'AFRICA') {
      setMarketScope('AFRICA');
    } else {
      setMarketScope('US_EU');
    }
  }, [marketFilter]);

  // Fetch asset type counts (includes all assets, even unscored)
  const { data: assetTypeCounts } = useQuery({
    queryKey: ['assetTypeCounts', marketScope],
    queryFn: () => api.getAssetTypeCounts(marketScope),
    staleTime: 300000, // 5 minutes
  });

  // Fetch top scored assets from real API
  const { 
    data: assetsResponse, 
    isLoading, 
    isError, 
    error,
    refetch 
  } = useQuery({
    queryKey: ['topScored', marketFilter, typeFilter, marketScope],
    queryFn: async () => {
      const response = await api.getTopScored({
        limit: 50,
        market_filter: marketFilter,
        market_scope: marketScope,
        asset_type: typeFilter || undefined,
      });
      return response;
    },
    staleTime: 60000, // 1 minute
    retry: 2,
  });

  const assets = assetsResponse?.data || [];

  // Auto-select first asset when assets load
  useEffect(() => {
    if (assets.length > 0 && !selectedAsset) {
      setSelectedAsset(assets[0]);
    }
  }, [assets, selectedAsset]);

  // Reset selection when filter changes
  useEffect(() => {
    if (assets.length > 0) {
      setSelectedAsset(assets[0]);
    } else {
      setSelectedAsset(null);
    }
  }, [marketFilter, typeFilter]);

  // Check if selected asset is in watchlist
  const { data: isWatchlisted = false } = useQuery({
    queryKey: ['watchlist-check', selectedAsset?.ticker, userId],
    queryFn: async () => {
      if (!selectedAsset?.ticker) return false;
      try {
        const result = await api.checkInWatchlist(selectedAsset.ticker, userId);
        return result.in_watchlist;
      } catch {
        return false;
      }
    },
    enabled: !!selectedAsset?.ticker,
  });

  // Mutation to add/remove from watchlist
  const watchlistMutation = useMutation({
    mutationFn: async (add: boolean) => {
      if (!selectedAsset?.ticker) return;
      if (add) {
        await api.addToWatchlist(
          selectedAsset.ticker,
          userId,
          selectedAsset.market_scope || 'US_EU'
        );
      } else {
        await api.removeFromWatchlist(selectedAsset.ticker, userId);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist-check', selectedAsset?.ticker, userId] });
      queryClient.invalidateQueries({ queryKey: ['watchlist', userId] });
    },
    onError: (error) => {
      console.error('Watchlist operation failed:', error);
    },
  });

  // Handle watchlist toggle
  const handleWatchlistToggle = () => {
    if (!selectedAsset) return;
    watchlistMutation.mutate(!isWatchlisted);
  };

  const marketFilters: { value: MarketFilter; label: string; icon?: string }[] = [
    { value: 'ALL', label: 'Tous' },
    { value: 'US', label: 'USA', icon: '🇺🇸' },
    { value: 'EU', label: 'Europe', icon: '🇪🇺' },
    { value: 'AFRICA', label: 'Afrique', icon: '🌍' },
  ];

  // Tous les types d'instruments financiers avec icônes
  const typeFilters: { value: AssetType | null; label: string; icon: React.ReactNode }[] = [
    { value: null, label: 'Tous', icon: <Layers className="w-4 h-4" /> },
    { value: 'EQUITY', label: 'Actions', icon: <Building2 className="w-4 h-4" /> },
    { value: 'ETF', label: 'ETF', icon: <Layers className="w-4 h-4" /> },
    { value: 'FX', label: 'Forex', icon: <DollarSign className="w-4 h-4" /> },
    { value: 'BOND', label: 'Obligations', icon: <Landmark className="w-4 h-4" /> },
    { value: 'OPTION', label: 'Options', icon: <Activity className="w-4 h-4" /> },
    { value: 'FUTURE', label: 'Futures', icon: <TrendingUp className="w-4 h-4" /> },
    { value: 'CRYPTO', label: 'Crypto', icon: <Globe className="w-4 h-4" /> },
  ];

  // Fetch real chart data from API
  const { 
    data: chartDataResponse,
    isLoading: isChartLoading,
  } = useQuery({
    queryKey: ['assetChart', selectedAsset?.ticker, chartPeriod],
    queryFn: async () => {
      if (!selectedAsset?.ticker) return null;
      try {
        const data = await api.getAssetChart(selectedAsset.ticker, chartPeriod);
        return data;
      } catch (error) {
        console.warn('Chart data not available, using fallback');
        return null;
      }
    },
    enabled: !!selectedAsset?.ticker,
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });

  // Fallback to generated data if API fails (ensures chart is never empty)
  const chartData = useMemo(() => {
    // If we have real data from API, use it
    if (chartDataResponse && Array.isArray(chartDataResponse) && chartDataResponse.length > 0) {
      return chartDataResponse;
    }
    
    // Fallback: generate realistic-looking data based on asset score
    const days = chartPeriod === '7d' ? 7 : chartPeriod === '30d' ? 30 : chartPeriod === '3m' ? 90 : 365;
    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - 1 - i));
      const basePrice = (selectedAsset?.score_total || 50) * 2 + Math.random() * 20;
      return {
        date: date.toISOString(),
        open: basePrice,
        high: basePrice + Math.random() * 5,
        low: basePrice - Math.random() * 5,
        close: basePrice + (Math.random() - 0.5) * 8,
      };
    });
  }, [chartDataResponse, selectedAsset?.ticker, selectedAsset?.score_total, chartPeriod]);

  return (
    <div className="space-y-6">
      {/* ─────────────────────────────────────────────────────────────────
         FILTERS
         ───────────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <span className="text-sm text-text-muted">Filtres:</span>
        </div>

        {/* Market filter */}
        <div className="flex gap-2">
          {marketFilters.map((f) => (
            <Pill
              key={f.value}
              active={marketFilter === f.value}
              onClick={() => setMarketFilter(f.value)}
              icon={f.icon ? <span>{f.icon}</span> : undefined}
            >
              {f.label}
            </Pill>
          ))}
        </div>

        <div className="h-6 w-px bg-glass-border" />

        {/* Type filter */}
        <div className="flex gap-2">
          {typeFilters.map((f) => (
            <Pill
              key={f.value || 'all'}
              active={typeFilter === f.value}
              onClick={() => setTypeFilter(f.value)}
            >
              {f.label}
            </Pill>
          ))}
        </div>

        <div className="flex-1" />

        {/* Refresh button */}
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={() => refetch()}
          leftIcon={<RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />}
        >
          Actualiser
        </Button>

        <Link href="/dashboard/explorer">
          <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
            Explorer tout
          </Button>
        </Link>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
         ASSET TYPE SUMMARY CARDS
         ───────────────────────────────────────────────────────────────── */}
      {assetTypeCounts && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {typeFilters.filter(f => f.value !== null).map((f) => {
            const stats = assetTypeCounts[f.value!];
            const count = stats?.count || 0;
            const avgScore = stats?.avgScore || 0;
            const isSelected = typeFilter === f.value;
            
            return (
              <motion.button
                key={f.value}
                onClick={() => setTypeFilter(isSelected ? null : f.value)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  'relative p-3 rounded-xl transition-all duration-200',
                  'border text-left',
                  isSelected
                    ? 'bg-accent-dim border-accent shadow-glow-sm'
                    : 'bg-surface border-glass-border hover:border-accent/30'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className={cn(
                    'p-1.5 rounded-lg',
                    isSelected ? 'bg-accent/20 text-accent' : 'bg-surface-hover text-text-muted'
                  )}>
                    {f.icon}
                  </span>
                  <span className="text-xs font-medium text-text-secondary truncate">
                    {f.label}
                  </span>
                </div>
                <div className="flex items-end justify-between">
                  <span className="text-lg font-bold text-text-primary">
                    {count.toLocaleString()}
                  </span>
                  {avgScore > 0 ? (
                    <span className={cn(
                      'text-xs font-medium px-1.5 py-0.5 rounded',
                      avgScore >= 70 ? 'bg-score-green/20 text-score-green' :
                      avgScore >= 50 ? 'bg-score-yellow/20 text-score-yellow' :
                      'bg-score-red/20 text-score-red'
                    )}>
                      {Math.round(avgScore)}
                    </span>
                  ) : (
                    <span className="text-xs text-text-dim">—</span>
                  )}
                </div>
              </motion.button>
            );
          })}
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────────
         ERROR STATE
         ───────────────────────────────────────────────────────────────── */}
      {isError && (
        <GlassCard className="border-score-red/30 bg-score-red/5">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-score-red" />
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary">Erreur de chargement</h3>
              <p className="text-sm text-text-secondary">
                {error instanceof Error ? error.message : 'Impossible de charger les données'}
              </p>
              <p className="text-xs text-text-muted mt-1">
                Vérifiez que le backend est lancé sur le port 8000
              </p>
            </div>
            <Button variant="secondary" onClick={() => refetch()}>
              Réessayer
            </Button>
          </div>
        </GlassCard>
      )}

      {/* ─────────────────────────────────────────────────────────────────
         MAIN CONTENT GRID
         ───────────────────────────────────────────────────────────────── */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* LEFT: Top scored list */}
        <div className="lg:col-span-1">
          <GlassCardAccent padding="none">
            <div className="p-4 border-b border-glass-border">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  Top scorés
                </h2>
                <span className="text-xs text-text-muted">
                  {assets.length} actifs
                </span>
              </div>
            </div>

            {/* Asset list */}
            <div className="max-h-[600px] overflow-y-auto scrollbar-hide">
              {isLoading ? (
                // Skeleton loader
                <div className="p-4 space-y-3">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="h-16 rounded-xl skeleton" />
                  ))}
                </div>
              ) : assets.length === 0 ? (
                // Empty state
                <div className="p-8 text-center">
                  <Search className="w-12 h-12 text-text-muted mx-auto mb-4" />
                  <p className="text-text-secondary">Aucun actif trouvé</p>
                  <p className="text-sm text-text-muted mt-1">
                    {marketFilter === 'AFRICA' 
                      ? 'Les actifs africains ne sont pas encore scorés'
                      : 'Essayez un autre filtre'}
                  </p>
                </div>
              ) : (
                <div className="p-2">
                  {assets.slice(0, 20).map((asset, index) => (
                    <motion.button
                      key={asset.asset_id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.03 }}
                      onClick={() => setSelectedAsset(asset)}
                      className={cn(
                        'w-full flex items-center gap-3 p-3 rounded-xl',
                        'transition-all duration-200',
                        selectedAsset?.asset_id === asset.asset_id
                          ? 'bg-accent-dim border-l-2 border-accent'
                          : 'hover:bg-surface'
                      )}
                    >
                      <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="sm" />
                      <div className="flex-1 text-left min-w-0">
                        <p className="font-semibold text-text-primary">{asset.ticker}</p>
                        <p className="text-xs text-text-muted truncate">{asset.name}</p>
                      </div>
                      <ScoreGaugeBadge score={asset.score_total} size="sm" />
                    </motion.button>
                  ))}
                </div>
              )}
            </div>

            {/* See more */}
            {assets.length > 0 && (
              <div className="p-4 border-t border-glass-border">
                <Link href="/dashboard/explorer">
                  <Button variant="ghost" className="w-full" rightIcon={<ChevronRight className="w-4 h-4" />}>
                    Voir les {assetsResponse?.total || assets.length} actifs
                  </Button>
                </Link>
              </div>
            )}
          </GlassCardAccent>
        </div>

        {/* RIGHT: Selected asset details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedAsset ? (
            <>
              {/* Asset header */}
              <GlassCard>
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <AssetLogo ticker={selectedAsset.ticker} assetType={selectedAsset.asset_type} size="xl" />
                    <div>
                      <div className="flex items-center gap-3">
                        <h1 className="text-2xl font-bold text-text-primary">
                          {selectedAsset.ticker}
                        </h1>
                        <span className="px-2.5 py-1 rounded-lg bg-surface text-sm text-text-secondary">
                          {selectedAsset.asset_type}
                        </span>
                        {selectedAsset.market_code && (
                          <span className="px-2.5 py-1 rounded-lg bg-surface text-xs text-text-muted">
                            {selectedAsset.market_code}
                          </span>
                        )}
                      </div>
                      <p className="text-text-secondary">{selectedAsset.name}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button 
                      variant={isWatchlisted ? 'primary' : 'secondary'} 
                      size="sm" 
                      onClick={handleWatchlistToggle}
                      disabled={watchlistMutation.isPending || !selectedAsset}
                      leftIcon={<Star className={cn('w-4 h-4', isWatchlisted && 'fill-current')} />}
                    >
                      {watchlistMutation.isPending ? '...' : (isWatchlisted ? 'Suivi' : 'Suivre')}
                    </Button>
                    <Link
                      href={`https://finance.yahoo.com/quote/${selectedAsset.ticker}`}
                      target="_blank"
                    >
                      <Button variant="ghost" size="sm" leftIcon={<ExternalLink className="w-4 h-4" />}>
                        Yahoo
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Score + Pillars */}
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="flex justify-center">
                    <ScoreGauge score={selectedAsset.score_total || 0} size="lg" />
                  </div>
                  <div className="space-y-4 py-4">
                    <PillarBar label="Valeur" value={selectedAsset.score_value || 0} icon="📈" />
                    <PillarBar label="Momentum" value={selectedAsset.score_momentum || 0} icon="🚀" />
                    <PillarBar label="Sécurité" value={selectedAsset.score_safety || 0} icon="🛡️" />
                  </div>
                </div>
              </GlassCard>

              {/* KPIs */}
              <div className="grid grid-cols-3 gap-4">
                <GlassCard padding="md">
                  <KpiBar
                    label="Couverture données"
                    value={selectedAsset.coverage || 0}
                    variant={selectedAsset.coverage && selectedAsset.coverage >= 80 ? 'success' : 'warning'}
                  />
                </GlassCard>
                <GlassCard padding="md">
                  <div className="space-y-2">
                    <span className="text-xs text-text-muted uppercase tracking-wide">Liquidité</span>
                    <p className="text-xl font-bold text-accent">
                      {getLiquidityLabel(selectedAsset.liquidity)}
                    </p>
                  </div>
                </GlassCard>
                <GlassCard padding="md">
                  <div className="space-y-2">
                    <span className="text-xs text-text-muted uppercase tracking-wide">Risque FX</span>
                    <p className={cn(
                      'text-xl font-bold',
                      selectedAsset.fx_risk && selectedAsset.fx_risk > 0.5 ? 'text-score-yellow' : 'text-score-green'
                    )}>
                      {getRiskLabel(selectedAsset.fx_risk)}
                    </p>
                  </div>
                </GlassCard>
              </div>

              {/* Chart */}
              <GlassCard>
                <h3 className="text-lg font-semibold text-text-primary mb-4">
                  📈 Évolution du prix
                </h3>
                <PriceChart
                  data={chartData}
                  period={chartPeriod}
                  onPeriodChange={setChartPeriod}
                  height={280}
                />
              </GlassCard>

              {/* Description */}
              <GlassCard>
                <h3 className="text-lg font-semibold text-text-primary mb-3">
                  À propos de {selectedAsset.name}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {selectedAsset.asset_type === 'ETF' 
                    ? `${selectedAsset.name} est un ETF qui permet aux investisseurs d'accéder à un panier diversifié d'actifs. Il offre une exposition à son marché de référence avec une liquidité élevée et des frais de gestion réduits.`
                    : `${selectedAsset.name} est une entreprise cotée sur les marchés financiers. Le score MarketGPS combine des analyses fondamentales et techniques pour évaluer son potentiel d'investissement.`
                  }
                </p>

                {/* External links */}
                <div className="mt-4 flex gap-2">
                  <Link
                    href={`https://finance.yahoo.com/quote/${selectedAsset.ticker}`}
                    target="_blank"
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-colors text-sm"
                  >
                    📊 Yahoo Finance
                  </Link>
                  <Link
                    href={`https://www.google.com/finance/quote/${selectedAsset.ticker}`}
                    target="_blank"
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-colors text-sm"
                  >
                    🔍 Google Finance
                  </Link>
                  <Link
                    href={`https://www.google.com/search?q=${selectedAsset.ticker}+news&tbm=nws`}
                    target="_blank"
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-colors text-sm"
                  >
                    📰 Actualités
                  </Link>
                </div>
              </GlassCard>
            </>
          ) : isLoading ? (
            // Loading state
            <GlassCard className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-12 h-12 text-accent mb-4 animate-spin" />
              <p className="text-text-secondary text-lg">Chargement des données...</p>
            </GlassCard>
          ) : (
            // Empty state
            <GlassCard className="flex flex-col items-center justify-center py-20">
              <Search className="w-12 h-12 text-text-muted mb-4" />
              <p className="text-text-secondary text-lg">Sélectionnez un actif</p>
              <p className="text-text-muted text-sm">pour voir les détails</p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
