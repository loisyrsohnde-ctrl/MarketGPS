'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  X, Star, Plus, TrendingUp, Shield, Rocket, 
  AlertTriangle, CheckCircle, Loader2, ExternalLink 
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import { ScoreGauge, PillarBar } from '@/components/charts/score-gauge';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface AssetDrawerProps {
  assetId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onAddToBuilder?: (asset: any, block: 'core' | 'satellite') => void;
}

async function fetchAssetDetail(assetId: string) {
  const res = await fetch(`${API_BASE}/api/assets/${assetId}`);
  if (!res.ok) throw new Error('Failed to fetch asset');
  return res.json();
}

async function addToWatchlist(ticker: string, userId: string = 'default_user', scope: string = 'US_EU') {
  const res = await fetch(`${API_BASE}/api/watchlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, user_id: userId, market_scope: scope }),
  });
  if (!res.ok) throw new Error('Failed to add to watchlist');
  return res.json();
}

export function AssetDrawer({ assetId, isOpen, onClose, onAddToBuilder }: AssetDrawerProps) {
  const queryClient = useQueryClient();

  const { data: asset, isLoading, error } = useQuery({
    queryKey: ['asset-detail', assetId],
    queryFn: () => fetchAssetDetail(assetId!),
    enabled: !!assetId && isOpen,
    staleTime: 60000,
  });

  const watchlistMutation = useMutation({
    mutationFn: () => addToWatchlist(asset?.ticker || asset?.symbol, 'default_user', asset?.market_scope || 'US_EU'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['watchlist'] });
    },
  });

  const handleAddToBuilder = (block: 'core' | 'satellite') => {
    if (asset && onAddToBuilder) {
      onAddToBuilder({
        asset_id: asset.asset_id,
        ticker: asset.ticker || asset.symbol,
        name: asset.name,
        score_total: asset.score_total,
        score_safety: asset.score_safety,
        score_momentum: asset.score_momentum,
        vol_annual: asset.vol_annual,
        coverage: asset.confidence || asset.coverage,
      }, block);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-bg-secondary border-l border-glass-border z-50 overflow-y-auto"
          >
            {/* Header */}
            <div className="sticky top-0 bg-bg-secondary/95 backdrop-blur-sm border-b border-glass-border p-4 flex items-center justify-between z-10">
              <h2 className="text-lg font-bold text-text-primary">Détail de l'actif</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 space-y-6">
              {isLoading && (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="w-8 h-8 text-accent animate-spin" />
                </div>
              )}

              {error && (
                <div className="p-4 rounded-xl bg-score-red/10 border border-score-red/30 text-score-red">
                  <AlertTriangle className="w-5 h-5 inline mr-2" />
                  Erreur de chargement
                </div>
              )}

              {asset && (
                <>
                  {/* Asset Header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-2xl font-bold text-text-primary">
                        {asset.ticker || asset.symbol}
                      </h3>
                      <p className="text-text-secondary">{asset.name}</p>
                      <div className="flex gap-2 mt-2">
                        <span className="px-2 py-1 rounded-md bg-surface text-xs text-text-muted">
                          {asset.asset_type}
                        </span>
                        <span className="px-2 py-1 rounded-md bg-surface text-xs text-text-muted">
                          {asset.market_scope || 'US_EU'}
                        </span>
                      </div>
                    </div>
                    <Link
                      href={`/asset/${asset.ticker || asset.symbol}`}
                      className="p-2 rounded-lg hover:bg-surface text-text-muted hover:text-accent transition-colors"
                    >
                      <ExternalLink className="w-5 h-5" />
                    </Link>
                  </div>

                  {/* Score Gauge */}
                  <div className="flex justify-center py-4">
                    <ScoreGauge score={asset.score_total || 0} size="lg" />
                  </div>

                  {/* Pillars */}
                  <GlassCard>
                    <h4 className="font-semibold text-text-primary mb-4">Breakdown des scores</h4>
                    <div className="space-y-4">
                      <PillarBar label="Valeur" value={asset.score_value || 0} icon="📈" />
                      <PillarBar label="Momentum" value={asset.score_momentum || 0} icon="🚀" />
                      <PillarBar label="Sécurité" value={asset.score_safety || 0} icon="🛡️" />
                    </div>
                  </GlassCard>

                  {/* Key Metrics */}
                  <GlassCard>
                    <h4 className="font-semibold text-text-primary mb-4">Métriques clés</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted">Volatilité annuelle</div>
                        <div className={cn(
                          'text-lg font-bold',
                          (asset.vol_annual || 0) < 25 ? 'text-score-green' : 
                          (asset.vol_annual || 0) < 40 ? 'text-score-yellow' : 'text-score-red'
                        )}>
                          {(asset.vol_annual || 0).toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted">Couverture données</div>
                        <div className={cn(
                          'text-lg font-bold',
                          (asset.confidence || 0) > 80 ? 'text-score-green' : 
                          (asset.confidence || 0) > 60 ? 'text-score-yellow' : 'text-score-red'
                        )}>
                          {(asset.confidence || 0).toFixed(0)}%
                        </div>
                      </div>
                      {asset.lt_score && (
                        <div className="p-3 bg-surface rounded-lg">
                          <div className="text-xs text-text-muted">Score Long-Terme</div>
                          <div className="text-lg font-bold text-accent">
                            {asset.lt_score.toFixed(1)}
                          </div>
                        </div>
                      )}
                      {asset.lt_confidence && (
                        <div className="p-3 bg-surface rounded-lg">
                          <div className="text-xs text-text-muted">Confiance LT</div>
                          <div className="text-lg font-bold text-text-primary">
                            {asset.lt_confidence.toFixed(0)}%
                          </div>
                        </div>
                      )}
                    </div>
                  </GlassCard>

                  {/* Warnings */}
                  {asset.warnings && asset.warnings.length > 0 && (
                    <div className="p-3 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
                      <div className="flex items-center gap-2 text-score-yellow mb-2">
                        <AlertTriangle className="w-4 h-4" />
                        <span className="font-medium">Avertissements</span>
                      </div>
                      <ul className="text-sm text-text-secondary space-y-1">
                        {asset.warnings.map((w: string, i: number) => (
                          <li key={i}>• {w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="space-y-3">
                    <Button
                      onClick={() => watchlistMutation.mutate()}
                      disabled={watchlistMutation.isPending}
                      variant="secondary"
                      className="w-full"
                      leftIcon={<Star className="w-4 h-4" />}
                    >
                      {watchlistMutation.isPending ? 'Ajout...' : 'Ajouter à la watchlist'}
                    </Button>

                    {onAddToBuilder && (
                      <div className="grid grid-cols-2 gap-3">
                        <Button
                          onClick={() => handleAddToBuilder('core')}
                          variant="secondary"
                          className="border-score-green/30 hover:bg-score-green/10"
                          leftIcon={<Shield className="w-4 h-4 text-score-green" />}
                        >
                          Core
                        </Button>
                        <Button
                          onClick={() => handleAddToBuilder('satellite')}
                          variant="secondary"
                          className="border-score-red/30 hover:bg-score-red/10"
                          leftIcon={<Rocket className="w-4 h-4 text-score-red" />}
                        >
                          Satellite
                        </Button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default AssetDrawer;
