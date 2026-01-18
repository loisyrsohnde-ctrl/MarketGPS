'use client';

import { useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Pill, ScoreGaugeBadge } from '@/components/ui/badge';
import { cn, formatNumberSafe } from '@/lib/utils';
import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Plus,
  Minus,
  Star,
  Play,
  Save,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Clock,
  CheckCircle,
  XCircle,
  Info,
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface BlockDefinition {
  name: string;
  label: string;
  weight: number;
  description: string;
  eligibility?: Record<string, any>;
}

interface StrategyTemplate {
  id: number;
  slug: string;
  name: string;
  description: string | null;
  category: string;
  risk_level: string;
  horizon_years: number;
  rebalance_frequency: string;
  structure: {
    blocks?: BlockDefinition[];
  };
  scope: string;
}

interface EligibleInstrument {
  ticker: string;
  name: string;
  asset_type: string;
  fit_score: number;
  global_score: number | null;
  lt_score: number | null;
  liquidity_badge: string;
  data_quality_badge: string;
  fit_breakdown?: Record<string, number>;
}

interface InstrumentComposition {
  ticker: string;
  block_name: string;
  weight: number;
  fit_score?: number;
  name?: string;
}

interface SimulationResult {
  cagr: number | null;
  volatility: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  final_value: number | null;
  total_return: number | null;
  series: Array<{ date: string; value: number }> | null;
  data_quality_score: number | null;
  warnings: string[];
  composition_hash: string | null;
  executed_at: string | null;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8501';

async function fetchTemplate(slug: string): Promise<StrategyTemplate> {
  const res = await fetch(`${API_BASE}/api/strategies/templates/${slug}`);
  if (!res.ok) throw new Error('Template not found');
  return res.json();
}

async function fetchEligibleInstruments(
  blockType: string,
  strategySlug?: string
): Promise<{ instruments: EligibleInstrument[]; total: number }> {
  const params = new URLSearchParams({ block_type: blockType });
  if (strategySlug) params.set('strategy_slug', strategySlug);
  const res = await fetch(`${API_BASE}/api/strategies/eligible-instruments?${params}`);
  if (!res.ok) throw new Error('Failed to fetch instruments');
  return res.json();
}

async function runSimulation(data: {
  compositions: InstrumentComposition[];
  period_years: number;
  initial_value: number;
  rebalance_frequency: string;
}): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/api/strategies/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Simulation failed');
  }
  return res.json();
}

async function addToWatchlist(ticker: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/watchlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker }),
  });
  if (!res.ok) throw new Error('Failed to add to watchlist');
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

const badgeColors: Record<string, string> = {
  good: 'bg-score-green/10 text-score-green',
  medium: 'bg-score-yellow/10 text-score-yellow',
  low: 'bg-score-red/10 text-score-red',
};

function MetricCard({
  label,
  value,
  suffix = '',
  positive = true,
  icon: Icon,
}: {
  label: string;
  value: number | null;
  suffix?: string;
  positive?: boolean;
  icon?: any;
}) {
  const isPositive = value !== null && value >= 0;
  const color = positive ? (isPositive ? 'text-score-green' : 'text-score-red') : 'text-text-primary';

  return (
    <div className="bg-surface rounded-xl p-4 border border-glass-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-text-muted uppercase tracking-wider">{label}</span>
        {Icon && <Icon className="w-4 h-4 text-text-dim" />}
      </div>
      <p className={cn('text-2xl font-bold', color)}>
        {value !== null ? `${value > 0 ? '+' : ''}${formatNumberSafe(value)}${suffix}` : '—'}
      </p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function StrategyBuilderPage() {
  const params = useParams();
  const slug = params.slug as string;

  // State
  const [activeBlock, setActiveBlock] = useState<string | null>(null);
  const [compositions, setCompositions] = useState<InstrumentComposition[]>([]);
  const [simulationPeriod, setSimulationPeriod] = useState(10);
  const [initialValue, setInitialValue] = useState(10000);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);

  // Queries
  const {
    data: template,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['strategyTemplate', slug],
    queryFn: () => fetchTemplate(slug),
    staleTime: 5 * 60 * 1000,
  });

  const blocks = template?.structure?.blocks || [];
  const currentBlock = blocks.find((b) => b.name === activeBlock) || blocks[0];

  const {
    data: eligibleData,
    isLoading: isLoadingEligible,
  } = useQuery({
    queryKey: ['eligibleInstruments', currentBlock?.name, slug],
    queryFn: () => fetchEligibleInstruments(currentBlock?.name || 'core', slug),
    enabled: !!currentBlock,
    staleTime: 2 * 60 * 1000,
  });

  // Mutations
  const simulationMutation = useMutation({
    mutationFn: runSimulation,
    onSuccess: (result) => {
      setSimulationResult(result);
    },
  });

  const watchlistMutation = useMutation({
    mutationFn: addToWatchlist,
  });

  // Calculate total weights
  const totalWeight = useMemo(() => {
    return compositions.reduce((sum, c) => sum + c.weight, 0);
  }, [compositions]);

  const weightsByBlock = useMemo(() => {
    const result: Record<string, number> = {};
    for (const comp of compositions) {
      result[comp.block_name] = (result[comp.block_name] || 0) + comp.weight;
    }
    return result;
  }, [compositions]);

  // Handlers
  const handleAddInstrument = (instrument: EligibleInstrument, blockName: string, blockWeight: number) => {
    // Calculate default weight (evenly distributed within block remaining)
    const currentBlockWeight = weightsByBlock[blockName] || 0;
    const remainingBlockWeight = blockWeight - currentBlockWeight;
    const defaultWeight = Math.max(0.01, Math.min(remainingBlockWeight, 0.1));

    setCompositions((prev) => {
      const exists = prev.find((c) => c.ticker === instrument.ticker);
      if (exists) return prev;
      return [
        ...prev,
        {
          ticker: instrument.ticker,
          block_name: blockName,
          weight: Math.round(defaultWeight * 100) / 100,
          fit_score: instrument.fit_score,
          name: instrument.name,
        },
      ];
    });
  };

  const handleRemoveInstrument = (ticker: string) => {
    setCompositions((prev) => prev.filter((c) => c.ticker !== ticker));
  };

  const handleWeightChange = (ticker: string, newWeight: number) => {
    setCompositions((prev) =>
      prev.map((c) =>
        c.ticker === ticker ? { ...c, weight: Math.max(0, Math.min(1, newWeight)) } : c
      )
    );
  };

  const handleRunSimulation = () => {
    if (compositions.length === 0) return;
    simulationMutation.mutate({
      compositions,
      period_years: simulationPeriod,
      initial_value: initialValue,
      rebalance_frequency: 'annual',
    });
  };

  // Set default active block
  if (blocks.length > 0 && !activeBlock) {
    setActiveBlock(blocks[0].name);
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  // Error state
  if (isError || !template) {
    return (
      <GlassCard className="border-score-red/30 bg-score-red/5">
        <div className="flex items-center gap-4">
          <AlertCircle className="w-8 h-8 text-score-red" />
          <div className="flex-1">
            <h3 className="font-semibold text-text-primary">Stratégie non trouvée</h3>
            <p className="text-sm text-text-secondary">
              {error instanceof Error ? error.message : 'Template introuvable'}
            </p>
          </div>
          <Link href="/strategies">
            <Button variant="secondary">Retour</Button>
          </Link>
        </div>
      </GlassCard>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/strategies">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-text-primary">{template.name}</h1>
          <p className="text-sm text-text-secondary">{template.description}</p>
        </div>
        <div className="flex items-center gap-2">
          <Pill active={false}>{template.horizon_years} ans</Pill>
          <Pill active={false} className="capitalize">{template.risk_level}</Pill>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Left: Blocks & Eligible Instruments */}
        <div className="lg:col-span-2 space-y-6">
          {/* Block Tabs */}
          <GlassCard>
            <div className="flex flex-wrap gap-2">
              {blocks.map((block) => (
                <button
                  key={block.name}
                  onClick={() => setActiveBlock(block.name)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium transition-all',
                    activeBlock === block.name
                      ? 'bg-accent text-white'
                      : 'bg-surface text-text-secondary hover:bg-surface-hover'
                  )}
                >
                  {block.label}
                  <span className="ml-2 text-xs opacity-70">
                    ({Math.round(block.weight * 100)}%)
                  </span>
                </button>
              ))}
            </div>
          </GlassCard>

          {/* Current Block Info */}
          {currentBlock && (
            <GlassCardAccent>
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-text-primary">{currentBlock.label}</h3>
                  <span className="text-sm text-accent font-medium">
                    Cible: {Math.round(currentBlock.weight * 100)}%
                    {weightsByBlock[currentBlock.name] !== undefined && (
                      <span className="ml-2 text-text-muted">
                        (Actuel: {Math.round((weightsByBlock[currentBlock.name] || 0) * 100)}%)
                      </span>
                    )}
                  </span>
                </div>
                <p className="text-sm text-text-secondary">{currentBlock.description}</p>
              </div>
            </GlassCardAccent>
          )}

          {/* Eligible Instruments Table */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-text-primary">Instruments Éligibles</h3>
              {isLoadingEligible && (
                <Loader2 className="w-4 h-4 animate-spin text-accent" />
              )}
            </div>

            {eligibleData && eligibleData.instruments.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-text-muted border-b border-glass-border">
                      <th className="pb-3 font-medium">Ticker</th>
                      <th className="pb-3 font-medium">Nom</th>
                      <th className="pb-3 font-medium text-center">Fit Score</th>
                      <th className="pb-3 font-medium text-center">Score Global</th>
                      <th className="pb-3 font-medium text-center">Liquidité</th>
                      <th className="pb-3 font-medium text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {eligibleData.instruments.map((inst) => {
                      const isAdded = compositions.some((c) => c.ticker === inst.ticker);
                      return (
                        <tr
                          key={inst.ticker}
                          className="border-b border-glass-border/50 hover:bg-surface/50"
                        >
                          <td className="py-3">
                            <Link
                              href={`/asset/${inst.ticker}`}
                              className="font-medium text-accent hover:underline"
                            >
                              {inst.ticker}
                            </Link>
                          </td>
                          <td className="py-3 text-text-secondary max-w-[200px] truncate">
                            {inst.name}
                          </td>
                          <td className="py-3 text-center">
                            <ScoreGaugeBadge score={inst.fit_score} size="sm" />
                          </td>
                          <td className="py-3 text-center">
                            {inst.global_score ? (
                              <ScoreGaugeBadge score={inst.global_score} size="sm" />
                            ) : (
                              <span className="text-text-dim">—</span>
                            )}
                          </td>
                          <td className="py-3 text-center">
                            <span className={cn('text-xs px-2 py-1 rounded-full', badgeColors[inst.liquidity_badge])}>
                              {inst.liquidity_badge}
                            </span>
                          </td>
                          <td className="py-3 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button
                                onClick={() => watchlistMutation.mutate(inst.ticker)}
                                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-score-yellow transition-colors"
                                title="Ajouter à la watchlist"
                              >
                                <Star className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() =>
                                  isAdded
                                    ? handleRemoveInstrument(inst.ticker)
                                    : handleAddInstrument(inst, currentBlock?.name || '', currentBlock?.weight || 0.25)
                                }
                                className={cn(
                                  'p-1.5 rounded-lg transition-colors',
                                  isAdded
                                    ? 'bg-score-red/10 text-score-red hover:bg-score-red/20'
                                    : 'bg-accent/10 text-accent hover:bg-accent/20'
                                )}
                              >
                                {isAdded ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-text-muted">
                {isLoadingEligible ? 'Chargement...' : 'Aucun instrument éligible'}
              </div>
            )}
          </GlassCard>
        </div>

        {/* Right: Composition & Simulation */}
        <div className="space-y-6">
          {/* Composition */}
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-text-primary">Composition</h3>
              <span
                className={cn(
                  'text-sm font-medium',
                  Math.abs(totalWeight - 1) < 0.01 ? 'text-score-green' : 'text-score-yellow'
                )}
              >
                Total: {Math.round(totalWeight * 100)}%
              </span>
            </div>

            {compositions.length === 0 ? (
              <div className="text-center py-8 text-text-muted">
                <PieChart className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Ajoutez des instruments depuis la liste</p>
              </div>
            ) : (
              <div className="space-y-3">
                {compositions.map((comp) => (
                  <div
                    key={comp.ticker}
                    className="flex items-center gap-3 p-3 bg-surface rounded-xl"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-text-primary truncate">{comp.ticker}</p>
                      <p className="text-xs text-text-muted truncate">{comp.name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="1"
                        value={Math.round(comp.weight * 100)}
                        onChange={(e) =>
                          handleWeightChange(comp.ticker, parseInt(e.target.value) / 100)
                        }
                        className="w-16 px-2 py-1 text-sm text-center bg-bg-primary border border-glass-border rounded-lg focus:outline-none focus:border-accent"
                      />
                      <span className="text-sm text-text-muted">%</span>
                      <button
                        onClick={() => handleRemoveInstrument(comp.ticker)}
                        className="p-1 rounded-lg hover:bg-score-red/10 text-text-muted hover:text-score-red transition-colors"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Weight Warning */}
            {compositions.length > 0 && Math.abs(totalWeight - 1) > 0.01 && (
              <div className="mt-4 p-3 rounded-xl bg-score-yellow/10 border border-score-yellow/30">
                <div className="flex items-center gap-2 text-score-yellow text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>Le total des poids doit être de 100%</span>
                </div>
              </div>
            )}
          </GlassCard>

          {/* Simulation Panel */}
          <GlassCard>
            <h3 className="font-semibold text-text-primary mb-4">Simulation</h3>

            <div className="space-y-4">
              {/* Period */}
              <div>
                <label className="text-sm text-text-secondary mb-2 block">Période</label>
                <div className="flex gap-2">
                  {[5, 10, 20].map((years) => (
                    <button
                      key={years}
                      onClick={() => setSimulationPeriod(years)}
                      className={cn(
                        'flex-1 py-2 rounded-xl text-sm font-medium transition-all',
                        simulationPeriod === years
                          ? 'bg-accent text-white'
                          : 'bg-surface text-text-secondary hover:bg-surface-hover'
                      )}
                    >
                      {years} ans
                    </button>
                  ))}
                </div>
              </div>

              {/* Initial Value */}
              <div>
                <label className="text-sm text-text-secondary mb-2 block">Capital initial</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="100"
                    step="1000"
                    value={initialValue}
                    onChange={(e) => setInitialValue(parseInt(e.target.value) || 10000)}
                    className="flex-1 px-3 py-2 bg-surface border border-glass-border rounded-xl text-text-primary focus:outline-none focus:border-accent"
                  />
                  <span className="text-text-muted">€</span>
                </div>
              </div>

              {/* Run Button */}
              <Button
                onClick={handleRunSimulation}
                disabled={compositions.length === 0 || Math.abs(totalWeight - 1) > 0.01 || simulationMutation.isPending}
                className="w-full"
              >
                {simulationMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Simulation...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Lancer la simulation
                  </>
                )}
              </Button>
            </div>

            {/* Simulation Error */}
            {simulationMutation.isError && (
              <div className="mt-4 p-3 rounded-xl bg-score-red/10 border border-score-red/30">
                <div className="flex items-center gap-2 text-score-red text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>
                    {simulationMutation.error instanceof Error
                      ? simulationMutation.error.message
                      : 'Erreur de simulation'}
                  </span>
                </div>
              </div>
            )}
          </GlassCard>

          {/* Simulation Results */}
          <AnimatePresence>
            {simulationResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <GlassCardAccent>
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-semibold text-text-primary">Résultats</h3>
                      <span className="text-xs text-text-muted">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {simulationResult.executed_at?.split('T')[0]}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <MetricCard
                        label="CAGR"
                        value={simulationResult.cagr}
                        suffix="%"
                        icon={TrendingUp}
                      />
                      <MetricCard
                        label="Volatilité"
                        value={simulationResult.volatility}
                        suffix="%"
                        positive={false}
                        icon={BarChart3}
                      />
                      <MetricCard
                        label="Sharpe"
                        value={simulationResult.sharpe}
                        suffix=""
                        icon={TrendingUp}
                      />
                      <MetricCard
                        label="Max Drawdown"
                        value={simulationResult.max_drawdown}
                        suffix="%"
                        icon={TrendingDown}
                      />
                    </div>

                    {/* Final Value */}
                    <div className="mt-4 p-4 bg-surface rounded-xl">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-text-muted">Valeur finale</span>
                        <span className="text-xl font-bold text-accent">
                          {formatNumberSafe(simulationResult.final_value)} €
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-text-dim">Rendement total</span>
                        <span
                          className={cn(
                            'text-sm font-medium',
                            (simulationResult.total_return || 0) >= 0 ? 'text-score-green' : 'text-score-red'
                          )}
                        >
                          {(simulationResult.total_return || 0) > 0 ? '+' : ''}
                          {formatNumberSafe(simulationResult.total_return)}%
                        </span>
                      </div>
                    </div>

                    {/* Warnings */}
                    {simulationResult.warnings.length > 0 && (
                      <div className="mt-4 space-y-2">
                        {simulationResult.warnings.map((warning, i) => (
                          <div
                            key={i}
                            className="flex items-start gap-2 text-xs text-score-yellow p-2 bg-score-yellow/5 rounded-lg"
                          >
                            <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                            <span>{warning}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Data Quality */}
                    <div className="mt-4 flex items-center justify-between text-xs text-text-muted">
                      <span>Qualité des données</span>
                      <span
                        className={cn(
                          'font-medium',
                          (simulationResult.data_quality_score || 0) > 80
                            ? 'text-score-green'
                            : (simulationResult.data_quality_score || 0) > 50
                            ? 'text-score-yellow'
                            : 'text-score-red'
                        )}
                      >
                        {formatNumberSafe(simulationResult.data_quality_score)}%
                      </span>
                    </div>
                  </div>
                </GlassCardAccent>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Save Button */}
          <Button variant="secondary" className="w-full" disabled>
            <Save className="w-4 h-4 mr-2" />
            Sauvegarder la stratégie
          </Button>
        </div>
      </div>
    </div>
  );
}
