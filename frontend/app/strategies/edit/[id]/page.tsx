'use client';

import { useState, useMemo, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Plus,
  Save,
  Trash2,
  Search,
  X,
  CheckCircle,
  Briefcase,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { ScoreGaugeBadge } from '@/components/ui/badge';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface UserStrategy {
  id: number;
  name: string;
  description?: string;
  template_id?: number;
  template_slug?: string;
  compositions: Array<{
    ticker: string;
    weight: number;
    block_name: string;
    fit_score?: number;
  }>;
  created_at?: string;
  updated_at?: string;
}

interface Asset {
  ticker: string;
  name: string;
  asset_type: string;
  score_total: number | null;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchStrategy(strategyId: number): Promise<UserStrategy> {
  const res = await fetch(`${API_BASE}/api/strategies/user/${strategyId}?user_id=default`);
  if (!res.ok) throw new Error('Strategy not found');
  return res.json();
}

async function updateStrategy(strategyId: number, data: {
  name: string;
  description?: string;
  compositions: Array<{ ticker: string; weight: number; block_name: string }>;
}): Promise<UserStrategy> {
  const res = await fetch(`${API_BASE}/api/strategies/user/${strategyId}?user_id=default`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update strategy');
  return res.json();
}

async function searchAssets(query: string): Promise<Asset[]> {
  if (!query || query.length < 2) return [];
  const res = await fetch(`${API_BASE}/api/assets/search?q=${encodeURIComponent(query)}&limit=20`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.results || [];
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function EditStrategyPage() {
  const router = useRouter();
  const params = useParams();
  const strategyId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [compositions, setCompositions] = useState<Array<{
    ticker: string;
    weight: number;
    block_name: string;
    name?: string;
  }>>([]);
  const [hasChanges, setHasChanges] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<Asset[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);

  // Query
  const { data: strategy, isLoading, isError } = useQuery({
    queryKey: ['user-strategy', strategyId],
    queryFn: () => fetchStrategy(strategyId),
    enabled: !isNaN(strategyId),
  });

  // Initialize form with strategy data
  useEffect(() => {
    if (strategy) {
      setName(strategy.name);
      setDescription(strategy.description || '');
      setCompositions(strategy.compositions.map(c => ({
        ticker: c.ticker,
        weight: c.weight,
        block_name: c.block_name,
      })));
    }
  }, [strategy]);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: () => updateStrategy(strategyId, {
      name,
      description,
      compositions,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-strategies'] });
      queryClient.invalidateQueries({ queryKey: ['user-strategy', strategyId] });
      setHasChanges(false);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    },
  });

  // Calculate total weight
  const totalWeight = useMemo(() => {
    return compositions.reduce((sum, c) => sum + c.weight, 0);
  }, [compositions]);

  // Handlers
  const handleSearch = async () => {
    if (!searchQuery || searchQuery.length < 2) return;
    setIsSearching(true);
    try {
      const results = await searchAssets(searchQuery);
      setSearchResults(results);
    } finally {
      setIsSearching(false);
    }
  };

  const handleAddAsset = (asset: Asset) => {
    if (compositions.find((c) => c.ticker === asset.ticker)) return;
    const remainingWeight = Math.max(0, 1 - totalWeight);
    const defaultWeight = Math.min(remainingWeight, 0.1);
    setCompositions([
      ...compositions,
      { ticker: asset.ticker, weight: defaultWeight, block_name: 'custom', name: asset.name },
    ]);
    setSearchResults([]);
    setSearchQuery('');
    setHasChanges(true);
  };

  const handleRemoveAsset = (ticker: string) => {
    setCompositions(compositions.filter((c) => c.ticker !== ticker));
    setHasChanges(true);
  };

  const handleWeightChange = (ticker: string, newWeight: number) => {
    setCompositions(
      compositions.map((c) =>
        c.ticker === ticker ? { ...c, weight: Math.max(0, Math.min(1, newWeight)) } : c
      )
    );
    setHasChanges(true);
  };

  const handleNormalizeWeights = () => {
    if (compositions.length === 0) return;
    const equalWeight = 1 / compositions.length;
    setCompositions(compositions.map((c) => ({ ...c, weight: Math.round(equalWeight * 100) / 100 })));
    setHasChanges(true);
  };

  const handleSave = () => {
    if (!name || compositions.length === 0 || Math.abs(totalWeight - 1) > 0.02) return;
    updateMutation.mutate();
  };

  // Loading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    );
  }

  // Error
  if (isError || !strategy) {
    return (
      <GlassCard className="border-score-red/30 bg-score-red/5">
        <div className="flex items-center gap-4">
          <AlertCircle className="w-8 h-8 text-score-red" />
          <div className="flex-1">
            <h3 className="font-semibold text-text-primary">Stratégie non trouvée</h3>
            <p className="text-sm text-text-secondary">Cette stratégie n&apos;existe pas ou a été supprimée</p>
          </div>
          <Link href="/strategies">
            <Button variant="secondary">Retour</Button>
          </Link>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/strategies">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
              <Briefcase className="w-6 h-6 text-accent" />
              Modifier la stratégie
            </h1>
            <p className="text-sm text-text-secondary">
              Ajustez votre composition et vos allocations
            </p>
          </div>
        </div>

        <Button
          onClick={handleSave}
          disabled={!hasChanges || updateMutation.isPending || Math.abs(totalWeight - 1) > 0.02}
          className="bg-accent hover:bg-accent/90"
        >
          {updateMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Sauvegarde...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Sauvegarder
            </>
          )}
        </Button>
      </div>

      {/* Success Message */}
      {showSuccess && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="p-4 rounded-xl bg-score-green/10 border border-score-green/30 text-score-green flex items-center gap-3"
        >
          <CheckCircle className="w-5 h-5" />
          <span>Stratégie mise à jour avec succès !</span>
        </motion.div>
      )}

      {/* Name & Description */}
      <GlassCard>
        <h3 className="font-semibold text-text-primary mb-4">Informations</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Nom de la stratégie</label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setHasChanges(true);
              }}
              className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Description</label>
            <textarea
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                setHasChanges(true);
              }}
              rows={2}
              className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary focus:outline-none focus:border-accent resize-none"
            />
          </div>
        </div>
      </GlassCard>

      {/* Add Assets */}
      <GlassCard>
        <h3 className="font-semibold text-text-primary mb-4">Ajouter des actifs</h3>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Rechercher un actif..."
              className="w-full pl-10 pr-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary focus:outline-none focus:border-accent"
            />
          </div>
          <Button onClick={handleSearch} disabled={isSearching}>
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Rechercher'}
          </Button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-2 max-h-48 overflow-y-auto">
            {searchResults.map((asset) => (
              <div
                key={asset.ticker}
                className="flex items-center justify-between p-3 bg-surface rounded-xl"
              >
                <div>
                  <span className="font-medium text-accent">{asset.ticker}</span>
                  <span className="text-text-secondary ml-2">{asset.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  {asset.score_total && <ScoreGaugeBadge score={asset.score_total} size="sm" />}
                  <button
                    onClick={() => handleAddAsset(asset)}
                    className="p-2 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      {/* Current Allocation */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-text-primary">Allocation</h3>
          <div className="flex items-center gap-3">
            <span
              className={cn(
                'text-sm font-medium',
                Math.abs(totalWeight - 1) < 0.02 ? 'text-score-green' : 'text-score-yellow'
              )}
            >
              Total: {(totalWeight * 100).toFixed(0)}%
            </span>
            <Button onClick={handleNormalizeWeights} variant="ghost" size="sm">
              Égaliser
            </Button>
          </div>
        </div>

        {compositions.length === 0 ? (
          <div className="text-center py-8 text-text-muted">
            Aucun actif dans cette stratégie
          </div>
        ) : (
          <div className="space-y-3">
            {compositions.map((comp) => (
              <div
                key={comp.ticker}
                className="flex items-center gap-4 p-3 bg-surface rounded-xl"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-accent">{comp.ticker}</p>
                  {comp.name && <p className="text-xs text-text-muted truncate">{comp.name}</p>}
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={Math.round(comp.weight * 100)}
                    onChange={(e) => handleWeightChange(comp.ticker, parseInt(e.target.value) / 100)}
                    className="w-20 accent-accent"
                  />
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="1"
                    value={Math.round(comp.weight * 100)}
                    onChange={(e) => handleWeightChange(comp.ticker, parseInt(e.target.value) / 100)}
                    className="w-14 px-2 py-1 text-sm text-center bg-bg-primary border border-glass-border rounded-lg focus:outline-none focus:border-accent"
                  />
                  <span className="text-sm text-text-muted">%</span>
                  <button
                    onClick={() => handleRemoveAsset(comp.ticker)}
                    className="p-2 rounded-lg hover:bg-score-red/10 text-text-muted hover:text-score-red transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Weight Warning */}
        {compositions.length > 0 && Math.abs(totalWeight - 1) > 0.02 && (
          <div className="mt-4 p-3 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
            <div className="flex items-center gap-2 text-score-yellow text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>Le total doit être de 100% pour sauvegarder</span>
            </div>
          </div>
        )}
      </GlassCard>
    </div>
  );
}
