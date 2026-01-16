'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Pill, ScoreBadge } from '@/components/ui/badge';
import { AssetLogo } from '@/components/cards/asset-card';
import { api } from '@/lib/api';
import { cn, formatNumberSafe } from '@/lib/utils';
import type { Asset, MarketFilter, AssetType } from '@/types';
import {
  TrendingUp,
  TrendingDown,
  Globe,
  BarChart3,
  Building2,
  DollarSign,
  Landmark,
  RefreshCw,
  ChevronRight,
  AlertCircle,
  Layers,
  Activity,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// MARKETS PAGE
// Overview of all market scopes with statistics and top assets
// ═══════════════════════════════════════════════════════════════════════════

interface MarketOverview {
  scope: MarketFilter;
  name: string;
  description: string;
  icon: React.ReactNode;
  flag: string;
  color: string;
}

const MARKETS: MarketOverview[] = [
  {
    scope: 'US_EU',
    name: 'US / Europe',
    description: 'Actions et ETFs des marchés américains et européens',
    icon: <Globe className="w-6 h-6" />,
    flag: '🇺🇸🇪🇺',
    color: 'from-blue-500/20 to-purple-500/20',
  },
  {
    scope: 'AFRICA',
    name: 'Afrique',
    description: 'Actions des marchés africains émergents',
    icon: <Globe className="w-6 h-6" />,
    flag: '🌍',
    color: 'from-amber-500/20 to-orange-500/20',
  },
];

const ASSET_TYPES: { type: AssetType | null; label: string; icon: React.ReactNode }[] = [
  { type: 'EQUITY', label: 'Actions', icon: <Building2 className="w-4 h-4" /> },
  { type: 'ETF', label: 'ETF', icon: <Layers className="w-4 h-4" /> },
  { type: 'FX', label: 'Forex', icon: <DollarSign className="w-4 h-4" /> },
  { type: 'BOND', label: 'Obligations', icon: <Landmark className="w-4 h-4" /> },
  { type: 'OPTION', label: 'Options', icon: <Activity className="w-4 h-4" /> },
  { type: 'FUTURE', label: 'Futures', icon: <TrendingUp className="w-4 h-4" /> },
  { type: 'CRYPTO', label: 'Crypto', icon: <Globe className="w-4 h-4" /> },
];

export default function MarketsPage() {
  const [selectedMarket, setSelectedMarket] = useState<MarketFilter>('US_EU');

  // Fetch scope counts
  const { data: scopeCounts, isLoading: isLoadingCounts } = useQuery({
    queryKey: ['scopeCounts'],
    queryFn: api.getScopeCounts,
    staleTime: 300000, // 5 minutes
  });

  // Fetch top assets for selected market
  const {
    data: topAssetsData,
    isLoading: isLoadingAssets,
    isError: isErrorAssets,
    refetch: refetchAssets,
  } = useQuery({
    queryKey: ['marketsTopAssets', selectedMarket],
    queryFn: async () => {
      const response = await api.getTopScored({
        market_scope: selectedMarket,
        limit: 10,
      });
      return response.data;
    },
    staleTime: 60000,
  });

  const topAssets = topAssetsData || [];

  // Calculate stats per asset type for selected market
  const { data: assetTypeStats } = useQuery({
    queryKey: ['assetTypeStats', selectedMarket],
    queryFn: async () => {
      const stats: Record<string, { count: number; avgScore: number }> = {};
      for (const { type } of ASSET_TYPES) {
        if (type) {
          const response = await api.getTopScored({
            market_scope: selectedMarket,
            asset_type: type,
            limit: 100,
          });
          const assets = response.data || [];
          const validScores = assets.filter(a => a.score_total != null).map(a => a.score_total!);
          stats[type] = {
            count: response.total || assets.length,
            avgScore: validScores.length > 0
              ? Math.round(validScores.reduce((a, b) => a + b, 0) / validScores.length)
              : 0,
          };
        }
      }
      return stats;
    },
    staleTime: 300000,
  });

  const currentMarket = MARKETS.find(m => m.scope === selectedMarket);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <BarChart3 className="w-8 h-8 text-accent" />
            Marchés
          </h1>
          <p className="text-text-secondary mt-1">
            Aperçu des marchés financiers couverts par MarketGPS
          </p>
        </div>
      </div>

      {/* Market Selector */}
      <div className="flex gap-4">
        {MARKETS.map((market) => (
          <motion.button
            key={market.scope}
            onClick={() => setSelectedMarket(market.scope)}
            className={cn(
              'flex-1 p-6 rounded-2xl border transition-all duration-200',
              'bg-gradient-to-br',
              market.color,
              selectedMarket === market.scope
                ? 'border-accent shadow-glow'
                : 'border-glass-border hover:border-glass-border-hover'
            )}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center gap-4">
              <div className="text-4xl">{market.flag}</div>
              <div className="text-left">
                <h3 className="text-lg font-semibold text-text-primary">{market.name}</h3>
                <p className="text-sm text-text-muted">{market.description}</p>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-glass-border">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary text-sm">Actifs disponibles</span>
                <span className="text-2xl font-bold text-accent">
                  {isLoadingCounts ? (
                    <span className="skeleton w-16 h-6 inline-block" />
                  ) : (
                    formatNumberSafe(
                      market.scope === 'US_EU'
                        ? scopeCounts?.US_EU
                        : scopeCounts?.AFRICA
                    )
                  )}
                </span>
              </div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* Market Details Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Asset Types Breakdown */}
        <GlassCardAccent className="lg:col-span-1" padding="none">
          <div className="p-4 border-b border-glass-border">
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <Layers className="w-5 h-5 text-accent" />
              Types d'actifs
            </h2>
          </div>
          <div className="p-4 space-y-4">
            {ASSET_TYPES.map(({ type, label, icon }) => {
              const stats = assetTypeStats?.[type || ''];
              return (
                <Link
                  key={type || 'all'}
                  href={`/dashboard/explorer?market_scope=${selectedMarket}${type ? `&asset_type=${type}` : ''}`}
                >
                  <div
                    className={cn(
                      'flex items-center justify-between p-3 rounded-xl',
                      'bg-surface hover:bg-surface-hover transition-colors',
                      'border border-glass-border hover:border-accent/30'
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-accent-dim text-accent">
                        {icon}
                      </div>
                      <div>
                        <p className="font-medium text-text-primary">{label}</p>
                        <p className="text-xs text-text-muted">
                          {formatNumberSafe(stats?.count)} actifs
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      {stats?.avgScore ? (
                        <ScoreBadge score={stats.avgScore} size="sm" />
                      ) : (
                        <span className="text-xs text-text-muted">—</span>
                      )}
                      <p className="text-xs text-text-muted mt-1">score moyen</p>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </GlassCardAccent>

        {/* Top Performers */}
        <GlassCardAccent className="lg:col-span-2" padding="none">
          <div className="p-4 border-b border-glass-border flex items-center justify-between">
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-accent" />
              Top 10 - {currentMarket?.name}
            </h2>
            <Link href={`/dashboard/explorer?market_scope=${selectedMarket}`}>
              <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="w-4 h-4" />}>
                Voir tout
              </Button>
            </Link>
          </div>

          {isErrorAssets ? (
            <div className="p-8 text-center text-score-red">
              <AlertCircle className="w-10 h-10 mx-auto mb-3" />
              <p className="text-sm">Impossible de charger les actifs.</p>
              <Button onClick={() => refetchAssets()} variant="secondary" size="sm" className="mt-4">
                <RefreshCw className="w-4 h-4 mr-2" /> Réessayer
              </Button>
            </div>
          ) : isLoadingAssets ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-14 rounded-xl skeleton" />
              ))}
            </div>
          ) : topAssets.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              Aucun actif disponible pour ce marché.
            </div>
          ) : (
            <div className="divide-y divide-glass-border">
              {topAssets.map((asset, index) => (
                <Link key={asset.asset_id} href={`/asset/${asset.ticker}`}>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center gap-4 p-4 hover:bg-surface transition-colors"
                  >
                    <span className="w-6 text-center text-sm font-medium text-text-muted">
                      #{index + 1}
                    </span>
                    <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-text-primary">{asset.ticker}</p>
                      <p className="text-xs text-text-muted truncate">{asset.name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-text-muted px-2 py-1 rounded bg-surface">
                        {asset.asset_type}
                      </span>
                      <ScoreBadge score={asset.score_total} size="md" />
                    </div>
                  </motion.div>
                </Link>
              ))}
            </div>
          )}
        </GlassCardAccent>
      </div>

      {/* Market Statistics */}
      <div className="grid md:grid-cols-4 gap-4">
        <GlassCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-accent-dim">
              <Activity className="w-5 h-5 text-accent" />
            </div>
            <span className="text-sm text-text-muted">Score moyen</span>
          </div>
          <p className="text-3xl font-bold text-text-primary">
            {topAssets.length > 0
              ? Math.round(
                  topAssets
                    .filter(a => a.score_total != null)
                    .reduce((sum, a) => sum + (a.score_total || 0), 0) /
                    topAssets.filter(a => a.score_total != null).length
                )
              : '—'}
          </p>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-score-green/10">
              <TrendingUp className="w-5 h-5 text-score-green" />
            </div>
            <span className="text-sm text-text-muted">Score ≥ 70</span>
          </div>
          <p className="text-3xl font-bold text-score-green">
            {topAssets.filter(a => (a.score_total || 0) >= 70).length}
          </p>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-score-yellow/10">
              <TrendingUp className="w-5 h-5 text-score-yellow" />
            </div>
            <span className="text-sm text-text-muted">Score 40-69</span>
          </div>
          <p className="text-3xl font-bold text-score-yellow">
            {topAssets.filter(a => (a.score_total || 0) >= 40 && (a.score_total || 0) < 70).length}
          </p>
        </GlassCard>

        <GlassCard>
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-score-red/10">
              <TrendingDown className="w-5 h-5 text-score-red" />
            </div>
            <span className="text-sm text-text-muted">Score &lt; 40</span>
          </div>
          <p className="text-3xl font-bold text-score-red">
            {topAssets.filter(a => (a.score_total || 0) < 40).length}
          </p>
        </GlassCard>
      </div>

      {/* Quick Links */}
      <GlassCard>
        <h3 className="text-lg font-semibold text-text-primary mb-4">Accès rapide</h3>
        <div className="flex flex-wrap gap-3">
          <Link href={`/dashboard/explorer?market_scope=US_EU&asset_type=ETF`}>
            <Pill icon={<span>🇺🇸</span>}>ETF US/Europe</Pill>
          </Link>
          <Link href={`/dashboard/explorer?market_scope=US_EU&asset_type=EQUITY`}>
            <Pill icon={<span>📈</span>}>Actions US/Europe</Pill>
          </Link>
          <Link href={`/dashboard/explorer?market_scope=AFRICA`}>
            <Pill icon={<span>🌍</span>}>Marchés Africains</Pill>
          </Link>
          <Link href={`/dashboard?scope=US_EU`}>
            <Pill icon={<TrendingUp className="w-4 h-4" />}>Dashboard US/EU</Pill>
          </Link>
          <Link href={`/dashboard?scope=AFRICA`}>
            <Pill icon={<Globe className="w-4 h-4" />}>Dashboard Afrique</Pill>
          </Link>
        </div>
      </GlassCard>
    </div>
  );
}
