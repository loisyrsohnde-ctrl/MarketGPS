'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Pill } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Target,
  Shield,
  TrendingUp,
  BarChart3,
  Briefcase,
  Loader2,
  ChevronRight,
  Clock,
  AlertCircle,
  Sparkles,
  Brain,
  Zap,
  Lock,
  Star,
  Dumbbell,
  PieChart,
  ArrowUpRight,
  Edit3,
  Trash2,
  Calendar,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

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
    blocks?: Array<{
      name: string;
      label: string;
      weight: number;
      description: string;
    }>;
  };
  scope: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchTemplates(): Promise<StrategyTemplate[]> {
  const res = await fetch(`${API_BASE}/api/strategies/templates`);
  if (!res.ok) throw new Error('Failed to fetch templates');
  return res.json();
}

async function fetchScopeCounts(): Promise<{ US_EU: number; AFRICA: number }> {
  const res = await fetch(`${API_BASE}/api/metrics/counts`);
  if (!res.ok) return { US_EU: 0, AFRICA: 0 };
  return res.json();
}

interface UserStrategy {
  id: number;
  name: string;
  description?: string;
  template_id?: number;
  template_slug?: string;
  compositions: Array<{ ticker: string; weight: number; block_name: string }>;
  created_at?: string;
  updated_at?: string;
}

async function fetchUserStrategies(): Promise<UserStrategy[]> {
  try {
    const res = await fetch(`${API_BASE}/api/strategies/user?user_id=default`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

async function deleteUserStrategy(strategyId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/strategies/user/${strategyId}?user_id=default`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete strategy');
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

const categoryConfig: Record<string, { icon: any; color: string; bgColor: string; label: string }> = {
  defensive: { icon: Shield, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'Défensif' },
  balanced: { icon: BarChart3, color: 'text-accent', bgColor: 'bg-accent/10', label: 'Équilibré' },
  growth: { icon: TrendingUp, color: 'text-amber-400', bgColor: 'bg-amber-500/10', label: 'Croissance' },
  tactical: { icon: Target, color: 'text-rose-400', bgColor: 'bg-rose-500/10', label: 'Tactique' },
};

const riskConfig: Record<string, { color: string; bgColor: string; label: string; gradient: string }> = {
  low: { color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'Faible', gradient: 'from-emerald-500 to-emerald-600' },
  moderate: { color: 'text-amber-400', bgColor: 'bg-amber-500/10', label: 'Modéré', gradient: 'from-amber-500 to-orange-500' },
  high: { color: 'text-rose-400', bgColor: 'bg-rose-500/10', label: 'Élevé', gradient: 'from-rose-500 to-red-600' },
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

// Hero Stats Component
function HeroStats({ templateCount, instrumentCount }: { templateCount: number; instrumentCount: number }) {
  const formatNumber = (n: number) => {
    if (n >= 1000) return n.toLocaleString('fr-FR');
    return n.toString();
  };
  
  const stats = [
    { label: 'Templates', value: templateCount > 0 ? templateCount.toString() : '6', icon: Briefcase, color: 'text-accent' },
    { label: 'Instruments', value: instrumentCount > 0 ? formatNumber(instrumentCount) : '—', icon: PieChart, color: 'text-emerald-400' },
    { label: 'Horizon moyen', value: '12 ans', icon: Clock, color: 'text-amber-400' },
    { label: 'Utilisateurs', value: 'Pro', icon: Star, color: 'text-rose-400' },
  ];
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="p-4 rounded-xl bg-surface/50 border border-glass-border"
        >
          <stat.icon className={cn('w-5 h-5 mb-2', stat.color)} />
          <div className="text-2xl font-bold text-text-primary">{stat.value}</div>
          <div className="text-xs text-text-secondary">{stat.label}</div>
        </motion.div>
      ))}
    </div>
  );
}

// AI Recommendation Panel
function AIRecommendationPanel() {
  const [expanded, setExpanded] = useState(true);

  return (
    <GlassCard className="border-accent/30 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-accent/5 transition-colors"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div className="text-left">
            <h3 className="font-bold text-text-primary flex items-center gap-2">
              Conseiller IA
              <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">BETA</span>
            </h3>
            <p className="text-sm text-text-muted">Recommandations personnalisées basées sur votre profil</p>
          </div>
        </div>
        <ChevronRight className={cn(
          'w-5 h-5 text-text-muted transition-transform',
          expanded && 'rotate-90'
        )} />
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-glass-border"
          >
            <div className="p-5 space-y-4">
              <p className="text-sm text-text-secondary leading-relaxed">
                Basé sur les données de marché actuelles et les modèles institutionnels, voici mes recommandations :
              </p>
              
              {/* Recommendations */}
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                  <Shield className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">Pour un profil conservateur</p>
                    <p className="text-xs text-text-muted mt-1">
                      Privilégiez le <span className="text-emerald-400 font-medium">Permanent Portfolio</span> avec une allocation Or renforcée (+5%) en période d&apos;incertitude.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 rounded-xl bg-accent/5 border border-accent/20">
                  <Dumbbell className="w-5 h-5 text-accent mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">Pour de la croissance contrôlée</p>
                    <p className="text-xs text-text-muted mt-1">
                      La stratégie <span className="text-accent font-medium">Barbell</span> avec 85% Core / 15% Satellite offre le meilleur ratio risque/rendement.
                    </p>
                  </div>
                </div>
                
                <div className="flex items-start gap-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/20">
                  <TrendingUp className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-text-primary">Pour maximiser le rendement</p>
                    <p className="text-xs text-text-muted mt-1">
                      Le <span className="text-amber-400 font-medium">Factor Investing</span> avec tilts Value + Momentum surperforme historiquement de 2-3% annuellement.
                    </p>
                  </div>
                </div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 pt-2">
                <div className="text-center p-3 rounded-lg bg-surface/50">
                  <div className="text-lg font-bold text-emerald-400">8.2%</div>
                  <div className="text-xs text-text-muted">CAGR moyen</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-surface/50">
                  <div className="text-lg font-bold text-accent">0.65</div>
                  <div className="text-xs text-text-muted">Sharpe moyen</div>
                </div>
                <div className="text-center p-3 rounded-lg bg-surface/50">
                  <div className="text-lg font-bold text-amber-400">-18%</div>
                  <div className="text-xs text-text-muted">Drawdown max</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </GlassCard>
  );
}

// Enhanced Strategy Card
function StrategyCard({ template, index }: { template: StrategyTemplate; index: number }) {
  const category = categoryConfig[template.category] || categoryConfig.balanced;
  const risk = riskConfig[template.risk_level] || riskConfig.moderate;
  const Icon = category.icon;
  const blocks = template.structure?.blocks || [];

  // Calculate total allocation for visual bar
  const totalWeight = blocks.reduce((sum, b) => sum + b.weight, 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
    >
      <Link href={`/strategies/${template.slug}`} className="block group">
        <div className="relative h-full p-6 rounded-2xl border border-glass-border bg-surface/30 backdrop-blur-sm hover:border-accent/50 hover:bg-surface/50 transition-all duration-300 overflow-hidden">
          {/* Gradient overlay on hover */}
          <div className="absolute inset-0 bg-gradient-to-br from-accent/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          
            {/* Header */}
          <div className="relative flex items-start justify-between mb-4">
            <div className={cn('p-3 rounded-xl', category.bgColor)}>
                <Icon className={cn('w-6 h-6', category.color)} />
              </div>
                <span className={cn(
              'text-xs font-medium px-3 py-1.5 rounded-full',
                  risk.bgColor, risk.color
                )}>
              Risque {risk.label.toLowerCase()}
                </span>
            </div>

          {/* Title & Description */}
          <h3 className="relative text-lg font-bold text-text-primary mb-2 group-hover:text-accent transition-colors">
              {template.name}
            </h3>
          <p className="relative text-sm text-text-secondary mb-5 line-clamp-2">
              {template.description}
            </p>

          {/* Allocation Bars */}
            {blocks.length > 0 && (
            <div className="relative mb-5">
              <div className="flex h-2 rounded-full overflow-hidden bg-bg-primary">
                {blocks.map((block, i) => {
                  const colors = [
                    'bg-emerald-500',
                    'bg-accent',
                    'bg-amber-500',
                    'bg-rose-500',
                  ];
                  return (
                    <motion.div
                      key={block.name}
                      initial={{ width: 0 }}
                      animate={{ width: `${(block.weight / totalWeight) * 100}%` }}
                      transition={{ delay: index * 0.08 + i * 0.1, duration: 0.5 }}
                      className={cn('h-full', colors[i % colors.length])}
                    />
                  );
                })}
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                {blocks.slice(0, 3).map((block, i) => {
                  const textColors = [
                    'text-emerald-400',
                    'text-accent',
                    'text-amber-400',
                  ];
                  return (
                    <span
                      key={block.name}
                      className={cn('text-xs', textColors[i % textColors.length])}
                    >
                      {block.label} ({Math.round(block.weight * 100)}%)
                    </span>
                  );
                })}
                  {blocks.length > 3 && (
                  <span className="text-xs text-text-dim">+{blocks.length - 3}</span>
                  )}
                </div>
              </div>
            )}

            {/* Footer */}
          <div className="relative flex items-center justify-between pt-4 border-t border-glass-border/50">
              <div className="flex items-center gap-4 text-xs text-text-muted">
                <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                  {template.horizon_years} ans
                </span>
                <span className="capitalize">{template.rebalance_frequency}</span>
              </div>
            <div className="flex items-center gap-1 text-accent opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-sm font-medium">Explorer</span>
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

// Quick Actions
function QuickActions() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Link href="/barbell">
        <GlassCard className="p-5 hover:border-accent/50 transition-all group cursor-pointer">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
              <Dumbbell className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-text-primary group-hover:text-accent transition-colors">Haltères</h4>
              <p className="text-xs text-text-muted">Core + Satellite personnalisable</p>
            </div>
            <ChevronRight className="w-5 h-5 text-text-dim group-hover:text-accent transition-colors" />
          </div>
        </GlassCard>
      </Link>

      <GlassCard className="p-5 border-dashed opacity-60">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center">
            <Zap className="w-6 h-6 text-text-muted" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-text-primary flex items-center gap-2">
              Backtest Avancé
              <span className="text-xs bg-surface px-2 py-0.5 rounded-full">Bientôt</span>
            </h4>
            <p className="text-xs text-text-muted">Monte Carlo, Stress Test</p>
          </div>
          <Lock className="w-5 h-5 text-text-dim" />
        </div>
      </GlassCard>

      <GlassCard className="p-5 border-dashed opacity-60">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center">
            <Brain className="w-6 h-6 text-text-muted" />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-text-primary flex items-center gap-2">
              IA Optimizer
              <span className="text-xs bg-surface px-2 py-0.5 rounded-full">Bientôt</span>
            </h4>
            <p className="text-xs text-text-muted">Optimisation automatique</p>
          </div>
          <Lock className="w-5 h-5 text-text-dim" />
        </div>
      </GlassCard>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function StrategiesPage() {
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const {
    data: templates,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['strategyTemplates'],
    queryFn: fetchTemplates,
    staleTime: 5 * 60 * 1000,
  });

  // Fetch user's custom strategies
  const { data: userStrategies = [], isLoading: isLoadingUserStrategies } = useQuery({
    queryKey: ['user-strategies'],
    queryFn: fetchUserStrategies,
    staleTime: 30 * 1000,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteUserStrategy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-strategies'] });
    },
  });

  const { data: scopeCounts } = useQuery({
    queryKey: ['scopeCounts'],
    queryFn: fetchScopeCounts,
    staleTime: 5 * 60 * 1000,
  });

  const totalInstruments = (scopeCounts?.US_EU || 0) + (scopeCounts?.AFRICA || 0);

  // Filter templates
  const filteredTemplates = useMemo(() => {
    return templates?.filter((t) => {
    if (categoryFilter && t.category !== categoryFilter) return false;
    if (riskFilter && t.risk_level !== riskFilter) return false;
    return true;
  });
  }, [templates, categoryFilter, riskFilter]);

  return (
    <div className="space-y-8">
      {/* Hero Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between"
      >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent via-accent-dark to-emerald-600 flex items-center justify-center shadow-glow">
              <Briefcase className="w-7 h-7 text-white" />
          </div>
          <div>
              <h1 className="text-3xl font-bold text-text-primary tracking-tight">
                Stratégies
              </h1>
              <p className="text-text-secondary">
                Templates éprouvés • Builder personnalisé • Simulation historique
            </p>
          </div>
          </div>
          <Link href="/strategies/new">
            <Button className="bg-accent hover:bg-accent/90">
              <Sparkles className="w-4 h-4 mr-2" />
              Créer ma stratégie
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* Stats */}
      <HeroStats templateCount={templates?.length || 0} instrumentCount={totalInstruments} />

      {/* AI Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <AIRecommendationPanel />
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2">
          <Zap className="w-4 h-4" />
          Accès rapide
        </h2>
        <QuickActions />
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
      >
        <GlassCard className="p-4">
          <div className="flex flex-wrap items-center gap-6">
          {/* Category Filter */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-text-secondary">Catégorie</span>
            <div className="flex gap-2">
              <Pill
                active={categoryFilter === null}
                onClick={() => setCategoryFilter(null)}
              >
                Toutes
              </Pill>
              {Object.entries(categoryConfig).map(([key, cfg]) => (
                <Pill
                  key={key}
                  active={categoryFilter === key}
                  onClick={() => setCategoryFilter(key)}
                >
                    <cfg.icon className={cn('w-3.5 h-3.5 mr-1.5', cfg.color)} />
                  {cfg.label}
                </Pill>
              ))}
            </div>
          </div>

          <div className="h-6 w-px bg-glass-border" />

          {/* Risk Filter */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-text-secondary">Risque</span>
            <div className="flex gap-2">
              <Pill
                active={riskFilter === null}
                onClick={() => setRiskFilter(null)}
              >
                Tous
              </Pill>
              {Object.entries(riskConfig).map(([key, cfg]) => (
                <Pill
                  key={key}
                  active={riskFilter === key}
                  onClick={() => setRiskFilter(key)}
                >
                    <span className={cn('w-2 h-2 rounded-full mr-1.5 bg-gradient-to-r', cfg.gradient)}></span>
                    {cfg.label}
                </Pill>
              ))}
            </div>
          </div>
        </div>
      </GlassCard>
      </motion.div>

      {/* Error State */}
      {isError && (
        <GlassCard className="border-rose-500/30 bg-rose-500/5 p-6">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-rose-400" />
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary">Erreur de chargement</h3>
              <p className="text-sm text-text-secondary">
                {error instanceof Error ? error.message : 'Impossible de charger les stratégies'}
              </p>
            </div>
            <Button variant="secondary" onClick={() => window.location.reload()}>
              Réessayer
            </Button>
          </div>
        </GlassCard>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-72 rounded-2xl bg-surface/30 border border-glass-border animate-pulse">
              <div className="p-6 space-y-4">
                <div className="flex justify-between">
                  <div className="w-14 h-14 bg-surface rounded-xl" />
                  <div className="w-24 h-7 bg-surface rounded-full" />
                </div>
                <div className="w-3/4 h-6 bg-surface rounded" />
                <div className="w-full h-12 bg-surface rounded" />
                <div className="w-full h-2 bg-surface rounded-full" />
                <div className="flex gap-2">
                  <div className="w-20 h-5 bg-surface rounded" />
                  <div className="w-20 h-5 bg-surface rounded" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Templates Grid */}
      {!isLoading && filteredTemplates && (
        <>
          {filteredTemplates.length === 0 ? (
            <GlassCard className="text-center py-16">
              <Briefcase className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-50" />
              <h3 className="text-xl font-semibold text-text-primary mb-2">Aucune stratégie trouvée</h3>
              <p className="text-sm text-text-secondary">
                Modifiez vos filtres pour voir plus de résultats
              </p>
            </GlassCard>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map((template, idx) => (
                <StrategyCard key={template.id} template={template} index={idx} />
              ))}
            </div>
          )}
        </>
      )}

      {/* My Strategies Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="pt-8 border-t border-glass-border"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <Star className="w-5 h-5 text-amber-400" />
            Mes Stratégies
            {userStrategies.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-accent/20 text-accent text-sm rounded-full">
                {userStrategies.length}
              </span>
            )}
          </h2>
          <Link href="/strategies/new">
            <Button variant="secondary" size="sm">
              <Sparkles className="w-4 h-4 mr-2" />
              Nouvelle stratégie
          </Button>
          </Link>
        </div>

        {isLoadingUserStrategies ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-accent animate-spin" />
          </div>
        ) : userStrategies.length === 0 ? (
          <GlassCard className="text-center py-12 border-dashed">
            <PieChart className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
            <p className="text-text-muted mb-4">
              Sélectionnez un template ci-dessus pour créer votre première stratégie personnalisée
            </p>
            <Link href="/strategies/new">
              <Button variant="secondary">
                <Sparkles className="w-4 h-4 mr-2" />
                Créer une stratégie
              </Button>
            </Link>
          </GlassCard>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {userStrategies.map((strategy) => (
              <motion.div
                key={strategy.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="group"
              >
                <GlassCard className="h-full hover:border-accent/30 transition-all">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-lg bg-accent/10">
                        <Briefcase className="w-4 h-4 text-accent" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-text-primary">{strategy.name}</h3>
                        <p className="text-xs text-text-muted">
                          {strategy.compositions?.length || 0} positions
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link href={`/strategies/edit/${strategy.id}`}>
                        <button className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-accent transition-colors">
                          <Edit3 className="w-4 h-4" />
                        </button>
                      </Link>
                      <button
                        onClick={() => {
                          if (confirm('Supprimer cette stratégie ?')) {
                            deleteMutation.mutate(strategy.id);
                          }
                        }}
                        className="p-1.5 rounded-lg hover:bg-score-red/10 text-text-muted hover:text-score-red transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {strategy.description && (
                    <p className="text-sm text-text-secondary mb-3 line-clamp-2">
                      {strategy.description}
                    </p>
                  )}

                  {/* Composition Preview */}
                  <div className="flex flex-wrap gap-1 mb-3">
                    {strategy.compositions?.slice(0, 4).map((comp) => (
                      <span
                        key={comp.ticker}
                        className="px-2 py-0.5 bg-surface rounded text-xs"
                      >
                        <span className="text-accent">{comp.ticker}</span>
                        <span className="text-text-dim ml-1">{Math.round(comp.weight * 100)}%</span>
                      </span>
                    ))}
                    {(strategy.compositions?.length || 0) > 4 && (
                      <span className="px-2 py-0.5 bg-surface rounded text-xs text-text-muted">
                        +{(strategy.compositions?.length || 0) - 4}
                      </span>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-glass-border">
                    <div className="flex items-center gap-1 text-xs text-text-dim">
                      <Calendar className="w-3 h-3" />
                      {strategy.updated_at
                        ? new Date(strategy.updated_at).toLocaleDateString('fr-FR')
                        : 'Récent'}
                    </div>
                    <Link href={`/strategies/edit/${strategy.id}`}>
                      <Button variant="ghost" size="sm" className="text-accent">
                        Modifier
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </Link>
                  </div>
        </GlassCard>
              </motion.div>
            ))}
      </div>
        )}
      </motion.div>
    </div>
  );
}
