'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import type { Asset } from '@/types';
import { X, Plus, TrendingUp } from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// ASSET COMPARATOR MODAL
// ═══════════════════════════════════════════════════════════════════════════

interface AssetComparatorProps {
  isOpen: boolean;
  onClose: () => void;
  initialAsset?: Asset;
  assets?: Asset[];
  onCompare?: (selectedAssets: Asset[]) => void;
}

interface ComparableMetric {
  key: keyof Asset;
  label: string;
  format: (value: any) => string;
  highlight?: 'highest' | 'lowest';
}

const comparableMetrics: ComparableMetric[] = [
  {
    key: 'score_total',
    label: 'Score Total',
    format: (v) => (v !== null ? v.toFixed(1) : 'N/A'),
    highlight: 'highest',
  },
  {
    key: 'score_value',
    label: 'Score Valeur',
    format: (v) => (v !== null ? v.toFixed(1) : 'N/A'),
    highlight: 'highest',
  },
  {
    key: 'score_momentum',
    label: 'Score Momentum',
    format: (v) => (v !== null ? v.toFixed(1) : 'N/A'),
    highlight: 'highest',
  },
  {
    key: 'score_safety',
    label: 'Score Sécurité',
    format: (v) => (v !== null ? v.toFixed(1) : 'N/A'),
    highlight: 'highest',
  },
  {
    key: 'last_price',
    label: 'Prix Actuel',
    format: (v) => (v !== null ? `${v.toFixed(2)}` : 'N/A'),
  },
  {
    key: 'liquidity',
    label: 'Liquidité',
    format: (v) => {
      if (v === null) return 'N/A';
      if (v <= 1) return `${(v * 100).toFixed(0)}%`;
      if (v > 1e9) return `${(v / 1e9).toFixed(1)}B`;
      if (v > 1e6) return `${(v / 1e6).toFixed(1)}M`;
      if (v > 1e3) return `${(v / 1e3).toFixed(1)}K`;
      return v.toFixed(0);
    },
    highlight: 'highest',
  },
  {
    key: 'coverage',
    label: 'Couverture',
    format: (v) => (v !== null ? `${(v > 1 ? v : v * 100).toFixed(0)}%` : 'N/A'),
    highlight: 'highest',
  },
  {
    key: 'volatility',
    label: 'Volatilité',
    format: (v) => (v !== null ? `${v.toFixed(1)}%` : 'N/A'),
    highlight: 'lowest',
  },
  {
    key: 'vol_annual',
    label: 'Vol. Annuelle',
    format: (v) => (v !== null ? `${v.toFixed(1)}%` : 'N/A'),
    highlight: 'lowest',
  },
  {
    key: 'max_drawdown',
    label: 'Max Drawdown',
    format: (v) => (v !== null ? `${v.toFixed(1)}%` : 'N/A'),
    highlight: 'lowest',
  },
  {
    key: 'rsi',
    label: 'RSI (14)',
    format: (v) => (v !== null ? `${v.toFixed(1)}` : 'N/A'),
  },
  {
    key: 'sma200',
    label: 'SMA 200',
    format: (v) => (v !== null ? `${v.toFixed(2)}` : 'N/A'),
  },
  {
    key: 'confidence',
    label: 'Confiance',
    format: (v) => (v !== null ? `${v.toFixed(0)}%` : 'N/A'),
    highlight: 'highest',
  },
];

export function AssetComparator({
  isOpen,
  onClose,
  initialAsset,
  assets = [],
  onCompare,
}: AssetComparatorProps) {
  const [selectedAssets, setSelectedAssets] = useState<Asset[]>(
    initialAsset ? [initialAsset] : []
  );
  const [searchQuery, setSearchQuery] = useState('');

  const addAsset = (asset: Asset) => {
    if (!selectedAssets.some((a) => a.ticker === asset.ticker)) {
      setSelectedAssets((prev) => [...prev, asset]);
    }
  };

  const removeAsset = (ticker: string) => {
    setSelectedAssets((prev) => prev.filter((a) => a.ticker !== ticker));
  };

  const getScoreColor = (value: number | null, highlight?: string): string => {
    if (value === null) return 'text-text-muted';
    if (highlight === 'lowest') {
      if (value <= 20) return 'text-score-green';
      if (value <= 40) return 'text-score-yellow';
      return 'text-score-red';
    }
    if (value >= 70) return 'text-score-green';
    if (value >= 40) return 'text-score-yellow';
    return 'text-score-red';
  };

  const getHighestValue = (metric: ComparableMetric): any => {
    return selectedAssets.reduce((max, asset) => {
      const value = asset[metric.key];
      if (value === null) return max;
      if (max === null) return value;
      if (metric.highlight === 'lowest') return Math.min(max, value);
      return Math.max(max, value);
    }, null);
  };

  const isHighlighted = (metric: ComparableMetric, asset: Asset): boolean => {
    const value = asset[metric.key];
    const highestValue = getHighestValue(metric);
    return value === highestValue && value !== null;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Comparateur d'actifs"
      size="xl"
    >
      <div className="space-y-6">
        {/* Selected assets */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-text-primary">Actifs sélectionnés</label>
          {selectedAssets.length === 0 ? (
            <div className="p-4 rounded-lg bg-surface/50 border border-glass-border text-center text-text-muted text-sm">
              Sélectionnez 1 à 4 actifs à comparer
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <AnimatePresence>
                {selectedAssets.map((asset, index) => (
                  <motion.div
                    key={asset.ticker}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="p-3 rounded-lg bg-surface border border-glass-border"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-semibold text-text-primary">
                        {asset.ticker}
                      </span>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => removeAsset(asset.ticker)}
                        className="p-1 rounded text-text-muted hover:text-score-red transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </motion.button>
                    </div>
                    <p className="text-xs text-text-secondary line-clamp-1">{asset.name}</p>
                    <div className="mt-2 pt-2 border-t border-glass-border">
                      <p className={cn(
                        'text-sm font-bold',
                        asset.score_total ? 'text-text-primary' : 'text-text-muted'
                      )}>
                        {asset.score_total ? asset.score_total.toFixed(1) : 'N/A'}
                      </p>
                      <p className="text-xs text-text-muted">Score</p>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Search and add */}
        {selectedAssets.length < 4 && (
          <div className="space-y-3">
            <label className="text-sm font-medium text-text-primary flex items-center gap-2">
              <Plus className="w-4 h-4 text-accent" />
              Ajouter un actif
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Rechercher par ticker..."
              className="w-full px-3 py-2 rounded-lg bg-surface border border-glass-border text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-accent placeholder:text-text-muted"
            />

            {/* Asset suggestions */}
            {assets.length > 0 && (
              <div className="max-h-40 overflow-y-auto space-y-1">
                {assets
                  .filter((a) =>
                    !selectedAssets.some((s) => s.ticker === a.ticker) &&
                    (searchQuery === '' ||
                      a.ticker.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      a.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  )
                  .slice(0, 5)
                  .map((asset) => (
                    <motion.button
                      key={asset.ticker}
                      whileHover={{ x: 4 }}
                      onClick={() => {
                        addAsset(asset);
                        setSearchQuery('');
                      }}
                      className="w-full p-2 rounded-lg text-left bg-surface/50 hover:bg-surface border border-glass-border transition-colors text-sm"
                    >
                      <span className="font-medium text-text-primary">{asset.ticker}</span>
                      <span className="ml-2 text-text-secondary">{asset.name}</span>
                    </motion.button>
                  ))}
              </div>
            )}
          </div>
        )}

        {/* Comparison table */}
        {selectedAssets.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-text-primary flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-accent" />
              Comparaison détaillée
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-glass-border">
                    <th className="text-left py-2 px-3 font-medium text-text-primary sticky left-0 bg-bg-secondary z-10">
                      Métrique
                    </th>
                    {selectedAssets.map((asset) => (
                      <th
                        key={asset.ticker}
                        className="text-center py-2 px-3 font-medium text-text-primary min-w-[100px]"
                      >
                        {asset.ticker}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {comparableMetrics.map((metric, idx) => (
                    <tr
                      key={metric.key}
                      className={cn(
                        'border-b border-glass-border/50',
                        idx % 2 === 0 && 'bg-surface/30'
                      )}
                    >
                      <td className="py-2 px-3 font-medium text-text-secondary sticky left-0 bg-inherit z-10">
                        {metric.label}
                      </td>
                      {selectedAssets.map((asset) => (
                        <td
                          key={`${asset.ticker}-${metric.key}`}
                          className={cn(
                            'text-center py-2 px-3 font-semibold',
                            isHighlighted(metric, asset) && 'bg-accent/10 text-accent rounded',
                            getScoreColor(asset[metric.key] as any, metric.highlight)
                          )}
                        >
                          {metric.format(asset[metric.key] as any)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            variant="secondary"
            onClick={onClose}
            className="flex-1"
          >
            Fermer
          </Button>
          {selectedAssets.length > 1 && (
            <Button
              variant="primary"
              onClick={() => {
                onCompare?.(selectedAssets);
                onClose();
              }}
              className="flex-1"
            >
              Analyser la comparaison
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}

export default AssetComparator;
