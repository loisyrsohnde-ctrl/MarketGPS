'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
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
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

async function fetchTemplates(): Promise<StrategyTemplate[]> {
  const res = await fetch(`${API_BASE}/api/strategies/templates`);
  if (!res.ok) throw new Error('Failed to fetch templates');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════

const categoryConfig: Record<string, { icon: any; color: string; label: string }> = {
  defensive: { icon: Shield, color: 'text-score-green', label: 'Défensif' },
  balanced: { icon: BarChart3, color: 'text-accent', label: 'Équilibré' },
  growth: { icon: TrendingUp, color: 'text-score-yellow', label: 'Croissance' },
  tactical: { icon: Target, color: 'text-score-red', label: 'Tactique' },
};

const riskConfig: Record<string, { color: string; bgColor: string; label: string }> = {
  low: { color: 'text-score-green', bgColor: 'bg-score-green/10', label: 'Risque faible' },
  moderate: { color: 'text-score-yellow', bgColor: 'bg-score-yellow/10', label: 'Risque modéré' },
  high: { color: 'text-score-red', bgColor: 'bg-score-red/10', label: 'Risque élevé' },
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function StrategyCard({ template }: { template: StrategyTemplate }) {
  const category = categoryConfig[template.category] || categoryConfig.balanced;
  const risk = riskConfig[template.risk_level] || riskConfig.moderate;
  const Icon = category.icon;
  const blocks = template.structure?.blocks || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full"
    >
      <Link href={`/strategies/${template.slug}`} className="block h-full">
        <GlassCard className="h-full hover:border-accent/50 transition-all duration-300 group cursor-pointer">
          <div className="flex flex-col h-full p-6">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className={cn('p-3 rounded-xl', risk.bgColor)}>
                <Icon className={cn('w-6 h-6', category.color)} />
              </div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  'text-xs font-medium px-2 py-1 rounded-full',
                  risk.bgColor, risk.color
                )}>
                  {risk.label}
                </span>
              </div>
            </div>

            {/* Content */}
            <h3 className="text-lg font-bold text-text-primary mb-2 group-hover:text-accent transition-colors">
              {template.name}
            </h3>
            <p className="text-sm text-text-secondary mb-4 line-clamp-2 flex-grow">
              {template.description}
            </p>

            {/* Blocks Preview */}
            {blocks.length > 0 && (
              <div className="mb-4">
                <div className="flex flex-wrap gap-2">
                  {blocks.slice(0, 3).map((block) => (
                    <span
                      key={block.name}
                      className="text-xs bg-surface px-2 py-1 rounded-md text-text-muted"
                    >
                      {block.label} ({Math.round(block.weight * 100)}%)
                    </span>
                  ))}
                  {blocks.length > 3 && (
                    <span className="text-xs text-text-dim">
                      +{blocks.length - 3} blocs
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-glass-border">
              <div className="flex items-center gap-4 text-xs text-text-muted">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {template.horizon_years} ans
                </span>
                <span className="capitalize">{template.rebalance_frequency}</span>
              </div>
              <ChevronRight className="w-5 h-5 text-text-dim group-hover:text-accent group-hover:translate-x-1 transition-all" />
            </div>
          </div>
        </GlassCard>
      </Link>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function StrategiesPage() {
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [riskFilter, setRiskFilter] = useState<string | null>(null);

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

  // Filter templates
  const filteredTemplates = templates?.filter((t) => {
    if (categoryFilter && t.category !== categoryFilter) return false;
    if (riskFilter && t.risk_level !== riskFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-accent/10">
            <Briefcase className="w-8 h-8 text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Stratégies Institutionnelles</h1>
            <p className="text-sm text-text-secondary">
              Templates de portefeuille éprouvés + Builder personnalisable + Simulation historique
            </p>
          </div>
        </div>
      </div>

      {/* Intro Card */}
      <GlassCardAccent>
        <div className="p-6 flex items-start gap-4">
          <Sparkles className="w-6 h-6 text-accent flex-shrink-0 mt-1" />
          <div>
            <h3 className="font-semibold text-text-primary mb-1">
              Construisez votre portefeuille comme les institutionnels
            </h3>
            <p className="text-sm text-text-secondary">
              Choisissez un template, personnalisez les instruments et poids, puis lancez une simulation 
              sur 5, 10 ou 20 ans pour évaluer les performances historiques (CAGR, volatilité, Sharpe, drawdown).
            </p>
          </div>
        </div>
      </GlassCardAccent>

      {/* Filters */}
      <GlassCard>
        <div className="flex flex-wrap items-center gap-4">
          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-text-secondary">Catégorie:</span>
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
                  <cfg.icon className="w-3 h-3 mr-1" />
                  {cfg.label}
                </Pill>
              ))}
            </div>
          </div>

          <div className="h-6 w-px bg-glass-border" />

          {/* Risk Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-text-secondary">Risque:</span>
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
                  <span className={cn('w-2 h-2 rounded-full mr-1', cfg.bgColor.replace('/10', ''))}></span>
                  {cfg.label.replace('Risque ', '')}
                </Pill>
              ))}
            </div>
          </div>
        </div>
      </GlassCard>

      {/* Error State */}
      {isError && (
        <GlassCard className="border-score-red/30 bg-score-red/5">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-score-red" />
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
            <GlassCard key={i} className="h-64 animate-pulse">
              <div className="p-6 space-y-4">
                <div className="flex justify-between">
                  <div className="w-12 h-12 bg-surface rounded-xl" />
                  <div className="w-20 h-6 bg-surface rounded-full" />
                </div>
                <div className="w-3/4 h-6 bg-surface rounded" />
                <div className="w-full h-12 bg-surface rounded" />
                <div className="flex gap-2">
                  <div className="w-16 h-5 bg-surface rounded" />
                  <div className="w-16 h-5 bg-surface rounded" />
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Templates Grid */}
      {!isLoading && filteredTemplates && (
        <>
          {filteredTemplates.length === 0 ? (
            <GlassCard className="text-center py-12">
              <Briefcase className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-text-primary">Aucune stratégie trouvée</h3>
              <p className="text-sm text-text-secondary mt-1">
                Essayez de modifier vos filtres
              </p>
            </GlassCard>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredTemplates.map((template, idx) => (
                <motion.div
                  key={template.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <StrategyCard template={template} />
                </motion.div>
              ))}
            </div>
          )}
        </>
      )}

      {/* My Strategies Section */}
      <div className="pt-8 border-t border-glass-border">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-text-primary">Mes Stratégies</h2>
          <Button variant="ghost" size="sm" disabled>
            Voir tout →
          </Button>
        </div>
        <GlassCard className="text-center py-8">
          <p className="text-text-muted">
            Sélectionnez un template ci-dessus pour créer votre première stratégie personnalisée.
          </p>
        </GlassCard>
      </div>
    </div>
  );
}
