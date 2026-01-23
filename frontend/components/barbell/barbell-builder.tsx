'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import {
  Dumbbell, Trash2, Save, RefreshCw, Play, AlertCircle,
  TrendingUp, BarChart3, Loader2, ChevronDown, ChevronUp
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart
} from 'recharts';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// Types
interface BuilderAsset {
  asset_id: string;
  ticker: string;
  name: string;
  block: 'core' | 'satellite';
  weight: number;
  score_total?: number;
  score_safety?: number;
  score_momentum?: number;
  vol_annual?: number;
  coverage?: number;
}

interface SimulationResult {
  cagr: number | null;
  volatility: number | null;
  sharpe: number | null;
  max_drawdown: number | null;
  total_return: number | null;
  final_value: number | null;
  equity_curve: Array<{ date: string; value: number }>;
  yearly_table: Array<{ year: number; return: number }>;
  best_year: { year: number; return: number } | null;
  worst_year: { year: number; return: number } | null;
  warnings: string[];
  data_quality_score: number | null;
  assets_included: number;
  assets_excluded: number;
  error: string | null;
}

interface BarbellBuilderProps {
  compositions: BuilderAsset[];
  riskProfile: string;
  coreRatio: number;
  satelliteRatio: number;
  onUpdateComposition: (compositions: BuilderAsset[]) => void;
  onRemoveAsset: (assetId: string) => void;
  onUpdateWeight: (assetId: string, weight: number) => void;
  onResetToSuggested: () => void;
  onSave?: () => void;
}

async function runSimulation(data: {
  compositions: Array<{ asset_id: string; weight: number; block: string }>;
  period_years: number;
  rebalance_frequency: string;
  initial_capital: number;
  market_scope: string;
}): Promise<SimulationResult> {
  const res = await fetch(`${API_BASE}/api/barbell/simulate`, {
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

export function BarbellBuilder({
  compositions,
  riskProfile,
  coreRatio,
  satelliteRatio,
  onUpdateComposition,
  onRemoveAsset,
  onUpdateWeight,
  onResetToSuggested,
  onSave,
}: BarbellBuilderProps) {
  // Simulation state
  const [periodYears, setPeriodYears] = useState(10);
  const [rebalanceFreq, setRebalanceFreq] = useState('yearly');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
  const [showEquityCurve, setShowEquityCurve] = useState(true);

  // Calculate weights
  const totalWeight = useMemo(() => 
    compositions.reduce((sum, c) => sum + c.weight, 0), 
    [compositions]
  );

  const coreWeight = useMemo(() => 
    compositions.filter(c => c.block === 'core').reduce((sum, c) => sum + c.weight, 0),
    [compositions]
  );

  const satelliteWeight = useMemo(() =>
    compositions.filter(c => c.block === 'satellite').reduce((sum, c) => sum + c.weight, 0),
    [compositions]
  );

  const isWeightValid = Math.abs(totalWeight - 1) < 0.01;

  // Simulation mutation
  const simulationMutation = useMutation({
    mutationFn: runSimulation,
    onSuccess: (result) => {
      setSimulationResult(result);
    },
  });

  const handleRunSimulation = () => {
    if (!isWeightValid || compositions.length === 0) return;

    simulationMutation.mutate({
      compositions: compositions.map(c => ({
        asset_id: c.asset_id,
        weight: c.weight,
        block: c.block,
      })),
      period_years: periodYears,
      rebalance_frequency: rebalanceFreq,
      initial_capital: initialCapital,
      market_scope: 'US_EU',
    });
  };

  const handleNormalizeWeights = () => {
    if (totalWeight === 0) return;
    
    const normalized = compositions.map(c => ({
      ...c,
      weight: c.weight / totalWeight,
    }));
    onUpdateComposition(normalized);
  };

  // Distribute weights evenly within each block based on target ratios
  const handleDistributeEvenly = () => {
    if (compositions.length === 0) return;
    
    const coreAssets = compositions.filter(c => c.block === 'core');
    const satelliteAssets = compositions.filter(c => c.block === 'satellite');
    
    const coreWeightEach = coreAssets.length > 0 ? coreRatio / coreAssets.length : 0;
    const satelliteWeightEach = satelliteAssets.length > 0 ? satelliteRatio / satelliteAssets.length : 0;
    
    const distributed = compositions.map(c => ({
      ...c,
      weight: c.block === 'core' ? coreWeightEach : satelliteWeightEach,
    }));
    onUpdateComposition(distributed);
  };

  // Auto-adjust to match target ratios (keep relative weights within blocks)
  const handleAutoAdjust = () => {
    if (compositions.length === 0) return;
    
    const coreAssets = compositions.filter(c => c.block === 'core');
    const satelliteAssets = compositions.filter(c => c.block === 'satellite');
    
    const currentCoreTotal = coreAssets.reduce((sum, c) => sum + c.weight, 0);
    const currentSatelliteTotal = satelliteAssets.reduce((sum, c) => sum + c.weight, 0);
    
    const adjusted = compositions.map(c => {
      if (c.block === 'core' && currentCoreTotal > 0) {
        return { ...c, weight: (c.weight / currentCoreTotal) * coreRatio };
      } else if (c.block === 'satellite' && currentSatelliteTotal > 0) {
        return { ...c, weight: (c.weight / currentSatelliteTotal) * satelliteRatio };
      }
      return c;
    });
    onUpdateComposition(adjusted);
  };

  return (
    <div className="space-y-6">
      {/* Builder Header */}
      <GlassCardAccent>
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-text-primary flex items-center gap-2">
              <Dumbbell className="w-5 h-5 text-accent" />
              Barbell Builder
            </h3>
            <div className="flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={onResetToSuggested}
              >
                <RefreshCw className="w-4 h-4 mr-1" />
                Reset
              </Button>
              {onSave && (
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!isWeightValid}
                  onClick={onSave}
                >
                  <Save className="w-4 h-4 mr-1" />
                  Sauvegarder
                </Button>
              )}
            </div>
          </div>

          {/* Ratio Visualization */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-score-green">Core: {(coreWeight * 100).toFixed(1)}%</span>
              <span className="text-text-muted">Cible: {(coreRatio * 100)}% / {(satelliteRatio * 100)}%</span>
              <span className="text-score-red">Satellite: {(satelliteWeight * 100).toFixed(1)}%</span>
            </div>
            <div className="h-3 rounded-full overflow-hidden flex bg-surface">
              <motion.div
                animate={{ width: `${coreWeight * 100}%` }}
                className="bg-score-green h-full"
              />
              <motion.div
                animate={{ width: `${satelliteWeight * 100}%` }}
                className="bg-score-red h-full"
              />
            </div>
          </div>

          {/* Quick Action Buttons */}
          {compositions.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Button size="sm" variant="ghost" onClick={handleDistributeEvenly} title="Répartir équitablement dans chaque bloc">
                ⚖️ Répartir
              </Button>
              <Button size="sm" variant="ghost" onClick={handleAutoAdjust} title="Ajuster automatiquement aux ratios cibles">
                🎯 Auto-ajuster
              </Button>
              <Button size="sm" variant="ghost" onClick={handleNormalizeWeights} title="Normaliser à 100%">
                📊 Normaliser
              </Button>
            </div>
          )}

          {/* Weight Warning */}
          {!isWeightValid && compositions.length > 0 && (
            <div className="flex items-center justify-between p-3 rounded-lg bg-score-yellow/10 border border-score-yellow/30">
              <span className="text-sm text-score-yellow flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Total: {(totalWeight * 100).toFixed(1)}% (doit être 100%)
              </span>
              <Button size="sm" variant="ghost" onClick={handleNormalizeWeights}>
                Normaliser
              </Button>
            </div>
          )}
        </div>
      </GlassCardAccent>

      {/* Composition Table */}
      <GlassCard padding="none">
        <div className="p-4 border-b border-glass-border">
          <h4 className="font-medium text-text-primary">Composition ({compositions.length} actifs)</h4>
        </div>

        {compositions.length === 0 ? (
          <div className="p-8 text-center text-text-muted">
            <Dumbbell className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Ajoutez des actifs depuis les tables Core ou Satellite</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-text-muted border-b border-glass-border bg-surface/50">
                  <th className="px-4 py-2 font-medium">Ticker</th>
                  <th className="px-4 py-2 font-medium hidden md:table-cell">Nom</th>
                  <th className="px-4 py-2 font-medium">Bloc</th>
                  <th className="px-4 py-2 font-medium">Poids</th>
                  <th className="px-4 py-2 font-medium hidden lg:table-cell">Score</th>
                  <th className="px-4 py-2 font-medium hidden lg:table-cell">Vol</th>
                  <th className="px-4 py-2 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {compositions.map((asset, idx) => (
                  <motion.tr
                    key={asset.asset_id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="border-b border-glass-border/50 hover:bg-surface/30"
                  >
                    <td className="px-4 py-2 font-mono font-bold text-accent">
                      {asset.ticker}
                    </td>
                    <td className="px-4 py-2 text-text-secondary max-w-[150px] truncate hidden md:table-cell">
                      {asset.name}
                    </td>
                    <td className="px-4 py-2">
                      <span className={cn(
                        'px-2 py-1 rounded text-xs font-medium',
                        asset.block === 'core'
                          ? 'bg-score-green/20 text-score-green'
                          : 'bg-score-red/20 text-score-red'
                      )}>
                        {asset.block === 'core' ? 'Core' : 'Satellite'}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <div className="flex items-center gap-1">
                        {/* Quick decrease button */}
                        <button
                          onClick={() => onUpdateWeight(asset.asset_id, Math.max(0, asset.weight - 0.01))}
                          className="p-1 hover:bg-surface rounded text-text-muted hover:text-text-primary transition-colors"
                          title="-1%"
                        >
                          −
                        </button>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="1"
                          value={Math.round(asset.weight * 100)}
                          onChange={(e) => onUpdateWeight(asset.asset_id, parseInt(e.target.value) / 100)}
                          className="w-14 px-1 py-1 text-sm text-center bg-bg-primary border border-glass-border rounded focus:outline-none focus:border-accent"
                        />
                        {/* Quick increase button */}
                        <button
                          onClick={() => onUpdateWeight(asset.asset_id, Math.min(1, asset.weight + 0.01))}
                          className="p-1 hover:bg-surface rounded text-text-muted hover:text-text-primary transition-colors"
                          title="+1%"
                        >
                          +
                        </button>
                        <span className="text-text-muted text-xs">%</span>
                      </div>
                    </td>
                    <td className="px-4 py-2 hidden lg:table-cell">
                      {asset.score_total?.toFixed(0) || '-'}
                    </td>
                    <td className="px-4 py-2 hidden lg:table-cell">
                      <span className={cn(
                        (asset.vol_annual || 0) < 25 ? 'text-score-green' :
                        (asset.vol_annual || 0) < 40 ? 'text-score-yellow' : 'text-score-red'
                      )}>
                        {asset.vol_annual?.toFixed(1) || '-'}%
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {/* Switch block button */}
                        <button
                          onClick={() => {
                            const newBlock: 'core' | 'satellite' = asset.block === 'core' ? 'satellite' : 'core';
                            const updated = compositions.map(c => 
                              c.asset_id === asset.asset_id ? { ...c, block: newBlock } : c
                            );
                            onUpdateComposition(updated);
                          }}
                          className={cn(
                            "p-1.5 rounded-lg transition-colors text-xs",
                            asset.block === 'core' 
                              ? "hover:bg-score-red/10 text-text-muted hover:text-score-red" 
                              : "hover:bg-score-green/10 text-text-muted hover:text-score-green"
                          )}
                          title={asset.block === 'core' ? 'Déplacer vers Satellite' : 'Déplacer vers Core'}
                        >
                          ↔
                        </button>
                        {/* Remove button */}
                        <button
                          onClick={() => onRemoveAsset(asset.asset_id)}
                          className="p-1.5 rounded-lg hover:bg-score-red/10 text-text-muted hover:text-score-red transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Simulation Panel */}
      <GlassCard>
        <h4 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-accent" />
          Simulation Backtest
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          {/* Period */}
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Période</label>
            <div className="flex gap-2">
              {[5, 10, 20].map((years) => (
                <button
                  key={years}
                  onClick={() => setPeriodYears(years)}
                  className={cn(
                    'flex-1 py-2 rounded-lg text-sm font-medium transition-all',
                    periodYears === years
                      ? 'bg-accent text-white'
                      : 'bg-surface text-text-secondary hover:bg-surface-hover'
                  )}
                >
                  {years} ans
                </button>
              ))}
            </div>
          </div>

          {/* Rebalancing */}
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Rebalancement</label>
            <select
              value={rebalanceFreq}
              onChange={(e) => setRebalanceFreq(e.target.value)}
              className="w-full px-3 py-2 bg-surface border border-glass-border rounded-lg text-text-primary"
            >
              <option value="yearly">Annuel</option>
              <option value="quarterly">Trimestriel</option>
              <option value="monthly">Mensuel</option>
            </select>
          </div>

          {/* Initial Capital */}
          <div>
            <label className="text-sm text-text-secondary mb-2 block">Capital initial</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1000"
                step="1000"
                value={initialCapital}
                onChange={(e) => setInitialCapital(parseInt(e.target.value) || 10000)}
                className="flex-1 px-3 py-2 bg-surface border border-glass-border rounded-lg text-text-primary"
              />
              <span className="text-text-muted">€</span>
            </div>
          </div>
        </div>

        {/* Run Button */}
        <Button
          onClick={handleRunSimulation}
          disabled={!isWeightValid || compositions.length === 0 || simulationMutation.isPending}
          className="w-full"
        >
          {simulationMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Simulation en cours...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              Lancer la simulation
            </>
          )}
        </Button>

        {/* Simulation Error */}
        {simulationMutation.isError && (
          <div className="mt-4 p-3 rounded-lg bg-score-red/10 border border-score-red/30 text-score-red text-sm">
            <AlertCircle className="w-4 h-4 inline mr-2" />
            {simulationMutation.error instanceof Error ? simulationMutation.error.message : 'Erreur de simulation'}
          </div>
        )}
      </GlassCard>

      {/* Simulation Results */}
      <AnimatePresence>
        {simulationResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <GlassCardAccent>
              <div className="p-4">
                <h4 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  Résultats ({periodYears} ans)
                </h4>

                {simulationResult.error ? (
                  <div className="p-4 rounded-lg bg-score-red/10 text-score-red">
                    {simulationResult.error}
                  </div>
                ) : (
                  <>
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted uppercase">CAGR</div>
                        <div className={cn(
                          'text-xl font-bold',
                          (simulationResult.cagr || 0) >= 0 ? 'text-score-green' : 'text-score-red'
                        )}>
                          {simulationResult.cagr !== null ? `${simulationResult.cagr > 0 ? '+' : ''}${simulationResult.cagr.toFixed(2)}%` : '—'}
                        </div>
                      </div>
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted uppercase">Volatilité</div>
                        <div className="text-xl font-bold text-text-primary">
                          {simulationResult.volatility?.toFixed(2) || '—'}%
                        </div>
                      </div>
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted uppercase">Sharpe</div>
                        <div className={cn(
                          'text-xl font-bold',
                          (simulationResult.sharpe || 0) >= 0.5 ? 'text-score-green' : 'text-text-primary'
                        )}>
                          {simulationResult.sharpe?.toFixed(2) || '—'}
                        </div>
                      </div>
                      <div className="p-3 bg-surface rounded-lg">
                        <div className="text-xs text-text-muted uppercase">Max Drawdown</div>
                        <div className="text-xl font-bold text-score-red">
                          {simulationResult.max_drawdown?.toFixed(2) || '—'}%
                        </div>
                      </div>
                    </div>

                    {/* Final Value */}
                    <div className="p-4 bg-surface rounded-lg mb-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="text-sm text-text-muted">Valeur finale</div>
                          <div className="text-2xl font-bold text-accent">
                            {simulationResult.final_value?.toLocaleString() || '—'} €
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-text-muted">Rendement total</div>
                          <div className={cn(
                            'text-lg font-bold',
                            (simulationResult.total_return || 0) >= 0 ? 'text-score-green' : 'text-score-red'
                          )}>
                            {simulationResult.total_return !== null
                              ? `${simulationResult.total_return > 0 ? '+' : ''}${simulationResult.total_return.toFixed(1)}%`
                              : '—'}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Equity Curve */}
                    {simulationResult.equity_curve && simulationResult.equity_curve.length > 0 && (
                      <div className="mb-4">
                        <button
                          onClick={() => setShowEquityCurve(!showEquityCurve)}
                          className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary mb-2"
                        >
                          {showEquityCurve ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          Equity Curve
                        </button>
                        
                        {showEquityCurve && (
                          <div className="h-64 w-full">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={simulationResult.equity_curve}>
                                <defs>
                                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#19D38C" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#19D38C" stopOpacity={0} />
                                  </linearGradient>
                                </defs>
                                <XAxis
                                  dataKey="date"
                                  tick={{ fontSize: 10, fill: '#6B7280' }}
                                  tickFormatter={(v) => v?.slice(0, 7)}
                                />
                                <YAxis
                                  tick={{ fontSize: 10, fill: '#6B7280' }}
                                  tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                                />
                                <Tooltip
                                  contentStyle={{
                                    backgroundColor: '#1a1a2e',
                                    border: '1px solid #2d2d44',
                                    borderRadius: '8px',
                                  }}
                                  formatter={(value: number) => [`${value.toLocaleString()} €`, 'Valeur']}
                                />
                                <Area
                                  type="monotone"
                                  dataKey="value"
                                  stroke="#19D38C"
                                  fill="url(#equityGradient)"
                                  strokeWidth={2}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Yearly Table */}
                    {simulationResult.yearly_table && simulationResult.yearly_table.length > 0 && (
                      <div className="mb-4">
                        <div className="text-sm text-text-secondary mb-2">Performance annuelle</div>
                        <div className="flex flex-wrap gap-2">
                          {simulationResult.yearly_table.map((year) => (
                            <div
                              key={year.year}
                              className={cn(
                                'px-2 py-1 rounded text-xs font-medium',
                                year.return >= 0
                                  ? 'bg-score-green/20 text-score-green'
                                  : 'bg-score-red/20 text-score-red'
                              )}
                            >
                              {year.year}: {year.return > 0 ? '+' : ''}{year.return.toFixed(1)}%
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warnings */}
                    {simulationResult.warnings && simulationResult.warnings.length > 0 && (
                      <div className="p-3 rounded-lg bg-score-yellow/10 border border-score-yellow/30">
                        <div className="text-sm text-score-yellow font-medium mb-1">Avertissements</div>
                        <ul className="text-xs text-text-secondary space-y-1">
                          {simulationResult.warnings.map((w, i) => (
                            <li key={i}>• {w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Data Quality */}
                    <div className="mt-4 flex items-center justify-between text-xs text-text-muted">
                      <span>Qualité des données: {simulationResult.data_quality_score?.toFixed(0)}%</span>
                      <span>{simulationResult.assets_included} actifs inclus, {simulationResult.assets_excluded} exclus</span>
                    </div>
                  </>
                )}
              </div>
            </GlassCardAccent>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default BarbellBuilder;
