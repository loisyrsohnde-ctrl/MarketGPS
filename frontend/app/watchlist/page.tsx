'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { ScoreGaugeBadge } from '@/components/ui/badge';
import { AssetLogo } from '@/components/cards/asset-card';
import { ScoreGauge, PillarBar } from '@/components/charts/score-gauge';
import { api } from '@/lib/api';
import { cn, formatDate } from '@/lib/utils';
import type { WatchlistItem } from '@/types';
import {
  Star,
  Trash2,
  Search,
  Plus,
  TrendingUp,
  ExternalLink,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════
// WATCHLIST PAGE
// Displays only assets explicitly added by the user
// ═══════════════════════════════════════════════════════════════════════════

export default function WatchlistPage() {
  const queryClient = useQueryClient();
  const [selectedAsset, setSelectedAsset] = useState<WatchlistItem | null>(null);
  const [userId] = useState('default'); // In production, get from auth

  // Fetch watchlist from backend
  const {
    data: watchlist,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['watchlist', userId],
    queryFn: () => api.getWatchlist(userId),
    staleTime: 30000, // 30 seconds
  });

  // Set initial selected asset when data loads
  useEffect(() => {
    if (watchlist && watchlist.length > 0 && !selectedAsset) {
      setSelectedAsset(watchlist[0]);
    }
  }, [watchlist, selectedAsset]);

  // Mutation to remove from watchlist
  const removeMutation = useMutation({
    mutationFn: (ticker: string) => api.removeFromWatchlist(ticker, userId),
    onSuccess: (_, ticker) => {
      // Invalidate and refetch watchlist
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
      
      // Update selected asset if it was removed
      if (selectedAsset?.ticker === ticker) {
        const remaining = watchlist?.filter((a) => a.ticker !== ticker);
        setSelectedAsset(remaining?.[0] || null);
      }
    },
    onError: (err) => {
      console.error('Failed to remove from watchlist:', err);
    },
  });

  const handleRemove = (ticker: string) => {
    removeMutation.mutate(ticker);
  };

  const items = watchlist || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
            <Star className="w-7 h-7 text-score-yellow fill-score-yellow" />
            Ma liste de suivi
          </h1>
          <p className="text-text-secondary mt-1">
            {isLoading ? (
              'Chargement...'
            ) : (
              <>
                {items.length} actif{items.length !== 1 ? 's' : ''} suivi{items.length !== 1 ? 's' : ''}
              </>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
            leftIcon={<RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />}
          >
            Actualiser
          </Button>
          <Link href="/dashboard/explorer">
            <Button leftIcon={<Plus className="w-4 h-4" />}>
              Ajouter un actif
            </Button>
          </Link>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <GlassCard className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="w-12 h-12 text-score-red mb-4" />
          <h2 className="text-lg font-semibold text-text-primary mb-2">
            Erreur de chargement
          </h2>
          <p className="text-text-secondary text-center max-w-md mb-4">
            {error instanceof Error ? error.message : 'Impossible de charger votre liste de suivi'}
          </p>
          <Button variant="secondary" onClick={() => refetch()}>
            Réessayer
          </Button>
        </GlassCard>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <GlassCard padding="none">
              <div className="p-4 border-b border-glass-border">
                <div className="h-6 w-32 skeleton rounded" />
              </div>
              <div className="p-4 space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-14 skeleton rounded-xl" />
                ))}
              </div>
            </GlassCard>
          </div>
          <div className="lg:col-span-2">
            <GlassCard className="h-96 skeleton" />
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && items.length === 0 && (
        <GlassCard className="flex flex-col items-center justify-center py-20">
          <div className="w-20 h-20 rounded-full bg-score-yellow/10 flex items-center justify-center mb-6">
            <Star className="w-10 h-10 text-score-yellow" />
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">
            Votre liste est vide
          </h2>
          <p className="text-text-secondary text-center max-w-md mb-6">
            Ajoutez des actifs à votre liste de suivi pour suivre leur évolution et comparer leurs scores.
          </p>
          <Link href="/dashboard/explorer">
            <Button size="lg" leftIcon={<Search className="w-4 h-4" />}>
              Explorer les actifs
            </Button>
          </Link>
        </GlassCard>
      )}

      {/* Watchlist content */}
      {!isLoading && !isError && items.length > 0 && (
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Left: Watchlist */}
          <div className="lg:col-span-1">
            <GlassCardAccent padding="none">
              <div className="p-4 border-b border-glass-border">
                <h2 className="font-semibold text-text-primary">Actifs suivis</h2>
              </div>

              <div className="p-2 max-h-[600px] overflow-y-auto scrollbar-hide">
                <AnimatePresence mode="popLayout">
                  {items.map((asset, index) => (
                    <motion.div
                      key={asset.ticker}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ delay: index * 0.05 }}
                      layout
                      className={cn(
                        'group flex items-center gap-3 p-3 rounded-xl cursor-pointer',
                        'transition-all duration-200',
                        selectedAsset?.ticker === asset.ticker
                          ? 'bg-accent-dim border-l-2 border-accent'
                          : 'hover:bg-surface'
                      )}
                      onClick={() => setSelectedAsset(asset)}
                    >
                      <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="sm" />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-text-primary">{asset.ticker}</p>
                        <p className="text-xs text-text-muted truncate">{asset.name}</p>
                      </div>
                      <ScoreGaugeBadge score={asset.score_total ?? null} size="sm" />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemove(asset.ticker);
                        }}
                        disabled={removeMutation.isPending}
                        className={cn(
                          'p-1.5 rounded-lg opacity-0 group-hover:opacity-100',
                          'text-text-muted hover:text-score-red hover:bg-score-red/10',
                          'transition-all',
                          removeMutation.isPending && 'opacity-50 cursor-not-allowed'
                        )}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </GlassCardAccent>
          </div>

          {/* Right: Selected asset details */}
          <div className="lg:col-span-2">
            {selectedAsset ? (
              <GlassCard className="space-y-6">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    <AssetLogo ticker={selectedAsset.ticker} assetType={selectedAsset.asset_type} size="xl" />
                    <div>
                      <div className="flex items-center gap-3">
                        <h2 className="text-2xl font-bold text-text-primary">
                          {selectedAsset.ticker}
                        </h2>
                        <span className="px-2.5 py-1 rounded-lg bg-surface text-sm text-text-secondary">
                          {selectedAsset.asset_type}
                        </span>
                        {selectedAsset.market_scope && (
                          <span className="px-2.5 py-1 rounded-lg bg-accent-dim text-sm text-accent">
                            {selectedAsset.market_scope === 'US_EU' ? '🇺🇸🇪🇺' : '🌍'} {selectedAsset.market_scope}
                          </span>
                        )}
                      </div>
                      <p className="text-text-secondary">{selectedAsset.name}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleRemove(selectedAsset.ticker)}
                      disabled={removeMutation.isPending}
                      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-score-red/10 text-score-red border border-score-red/30 hover:bg-score-red/20 transition-all disabled:opacity-50"
                    >
                      <Trash2 className="w-4 h-4" />
                      Retirer
                    </button>
                    <Link href={`/asset/${selectedAsset.ticker}`}>
                      <Button variant="secondary" size="md" rightIcon={<ExternalLink className="w-4 h-4" />}>
                        Détails
                      </Button>
                    </Link>
                  </div>
                </div>

                {/* Score + Pillars */}
                <div className="grid md:grid-cols-2 gap-8 pt-4 border-t border-glass-border">
                  <div className="flex justify-center">
                    <ScoreGauge score={selectedAsset.score_total ?? null} size="lg" />
                  </div>
                  <div className="space-y-4 py-4">
                    <PillarBar label="Valeur" value={selectedAsset.score_value ?? null} icon="📈" />
                    <PillarBar label="Momentum" value={selectedAsset.score_momentum ?? null} icon="🚀" />
                    <PillarBar label="Sécurité" value={selectedAsset.score_safety ?? null} icon="🛡️" />
                  </div>
                </div>

                {/* KPIs */}
                {(selectedAsset.coverage || selectedAsset.liquidity) && (
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-glass-border">
                    {selectedAsset.coverage != null && (
                      <div className="p-3 rounded-xl bg-surface">
                        <span className="text-xs text-text-muted uppercase tracking-wide">Couverture</span>
                        <p className="text-lg font-semibold text-text-primary mt-1">
                          {Math.round(selectedAsset.coverage)}%
                        </p>
                      </div>
                    )}
                    {selectedAsset.liquidity != null && (
                      <div className="p-3 rounded-xl bg-surface">
                        <span className="text-xs text-text-muted uppercase tracking-wide">Liquidité</span>
                        <p className="text-lg font-semibold text-accent mt-1">
                          {selectedAsset.liquidity >= 0.9 ? 'Élevée' : selectedAsset.liquidity >= 0.5 ? 'Moyenne' : 'Faible'}
                        </p>
                      </div>
                    )}
                    {selectedAsset.fx_risk != null && (
                      <div className="p-3 rounded-xl bg-surface">
                        <span className="text-xs text-text-muted uppercase tracking-wide">Risque FX</span>
                        <p className={cn(
                          'text-lg font-semibold mt-1',
                          selectedAsset.fx_risk > 0.5 ? 'text-score-yellow' : 'text-score-green'
                        )}>
                          {selectedAsset.fx_risk > 0.5 ? 'Modéré' : 'Faible'}
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {/* Notes */}
                {selectedAsset.notes && (
                  <div className="pt-4 border-t border-glass-border">
                    <span className="text-xs text-text-muted uppercase tracking-wide">Notes</span>
                    <p className="text-text-secondary mt-2">{selectedAsset.notes}</p>
                  </div>
                )}

                {/* Meta info */}
                <div className="pt-4 border-t border-glass-border flex items-center justify-between text-sm text-text-muted">
                  <span>
                    {selectedAsset.added_at && (
                      <>Ajouté le {formatDate(selectedAsset.added_at, 'long')}</>
                    )}
                  </span>
                  <span>
                    {selectedAsset.updated_at && (
                      <>Mis à jour: {formatDate(selectedAsset.updated_at, 'short')}</>
                    )}
                  </span>
                </div>
              </GlassCard>
            ) : (
              <GlassCard className="flex flex-col items-center justify-center py-20">
                <TrendingUp className="w-12 h-12 text-text-muted mb-4" />
                <p className="text-text-secondary">Sélectionnez un actif</p>
              </GlassCard>
            )}
          </div>
        </div>
      )}

      {/* Help text */}
      <div className="text-center text-sm text-text-muted">
        <p>
          💡 Pour ajouter des actifs à votre liste, utilisez le bouton ⭐ sur les pages de détails ou dans l&apos;
          <Link href="/dashboard/explorer" className="text-accent hover:underline">explorateur</Link>.
        </p>
      </div>
    </div>
  );
}
