'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { 
  Search, ChevronLeft, ChevronRight, Plus, AlertTriangle,
  Loader2, ArrowUpDown, Filter
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import { ScoreGaugeBadge } from '@/components/ui/badge';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface CandidatesTableProps {
  type: 'core' | 'satellite';
  marketScope?: string;
  onAddToBuilder?: (asset: any) => void;
  onSelectAsset?: (assetId: string) => void;
  addedAssetIds?: string[];
}

interface CandidateFilters {
  q: string;
  min_score_total: string;
  min_score_safety: string;
  min_score_momentum: string;
  max_vol_annual: string;
  asset_type: string;
}

async function fetchCandidates(
  type: 'core' | 'satellite',
  params: {
    market_scope: string;
    limit: number;
    offset: number;
    sort_by: string;
    sort_order: string;
    q?: string;
    min_score_total?: number;
    min_score_safety?: number;
    min_score_momentum?: number;
    max_vol_annual?: number;
    asset_type?: string;
  }
) {
  const searchParams = new URLSearchParams();
  searchParams.set('market_scope', params.market_scope);
  searchParams.set('limit', String(params.limit));
  searchParams.set('offset', String(params.offset));
  searchParams.set('sort_by', params.sort_by);
  searchParams.set('sort_order', params.sort_order);
  
  if (params.q) searchParams.set('q', params.q);
  if (params.min_score_total) searchParams.set('min_score_total', String(params.min_score_total));
  if (params.min_score_safety) searchParams.set('min_score_safety', String(params.min_score_safety));
  if (params.min_score_momentum) searchParams.set('min_score_momentum', String(params.min_score_momentum));
  if (params.max_vol_annual) searchParams.set('max_vol_annual', String(params.max_vol_annual));
  if (params.asset_type) searchParams.set('asset_type', params.asset_type);

  const endpoint = type === 'core' ? '/api/barbell/candidates/core' : '/api/barbell/candidates/satellite';
  const res = await fetch(`${API_BASE}${endpoint}?${searchParams}`);
  if (!res.ok) throw new Error('Failed to fetch candidates');
  return res.json();
}

export function CandidatesTable({
  type,
  marketScope = 'US_EU',
  onAddToBuilder,
  onSelectAsset,
  addedAssetIds = [],
}: CandidatesTableProps) {
  const [page, setPage] = useState(0);
  const [pageSize] = useState(15);
  const [sortBy, setSortBy] = useState(type === 'core' ? 'core_score' : 'satellite_score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<CandidateFilters>({
    q: '',
    min_score_total: '',
    min_score_safety: '',
    min_score_momentum: '',
    max_vol_annual: '',
    asset_type: '',
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['candidates', type, marketScope, page, sortBy, sortOrder, filters],
    queryFn: () => fetchCandidates(type, {
      market_scope: marketScope,
      limit: pageSize,
      offset: page * pageSize,
      sort_by: sortBy,
      sort_order: sortOrder,
      q: filters.q || undefined,
      min_score_total: filters.min_score_total ? parseFloat(filters.min_score_total) : undefined,
      min_score_safety: filters.min_score_safety ? parseFloat(filters.min_score_safety) : undefined,
      min_score_momentum: filters.min_score_momentum ? parseFloat(filters.min_score_momentum) : undefined,
      max_vol_annual: filters.max_vol_annual ? parseFloat(filters.max_vol_annual) : undefined,
      asset_type: filters.asset_type || undefined,
    }),
    staleTime: 30000,
  });

  const candidates = data?.candidates || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setPage(0);
  };

  const isCore = type === 'core';

  return (
    <GlassCard padding="none">
      {/* Header */}
      <div className="p-4 border-b border-glass-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-text-primary flex items-center gap-2">
            {isCore ? (
              <>🛡️ Candidats Core</>
            ) : (
              <>🚀 Candidats Satellite</>
            )}
            <span className="text-sm text-text-muted">({total})</span>
          </h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            leftIcon={<Filter className="w-4 h-4" />}
          >
            Filtres
          </Button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher ticker ou nom..."
            value={filters.q}
            onChange={(e) => {
              setFilters({ ...filters, q: e.target.value });
              setPage(0);
            }}
            className="w-full pl-10 pr-4 py-2 bg-surface border border-glass-border rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-3 pt-3 border-t border-glass-border"
          >
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <label className="text-xs text-text-muted">Score min</label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  placeholder="0"
                  value={filters.min_score_total}
                  onChange={(e) => setFilters({ ...filters, min_score_total: e.target.value })}
                  className="w-full px-2 py-1.5 text-sm bg-bg-primary border border-glass-border rounded-lg"
                />
              </div>
              {isCore && (
                <>
                  <div>
                    <label className="text-xs text-text-muted">Safety min</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      placeholder="0"
                      value={filters.min_score_safety}
                      onChange={(e) => setFilters({ ...filters, min_score_safety: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm bg-bg-primary border border-glass-border rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-text-muted">Vol max</label>
                    <input
                      type="number"
                      min="0"
                      placeholder="30"
                      value={filters.max_vol_annual}
                      onChange={(e) => setFilters({ ...filters, max_vol_annual: e.target.value })}
                      className="w-full px-2 py-1.5 text-sm bg-bg-primary border border-glass-border rounded-lg"
                    />
                  </div>
                </>
              )}
              {!isCore && (
                <div>
                  <label className="text-xs text-text-muted">Momentum min</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    placeholder="50"
                    value={filters.min_score_momentum}
                    onChange={(e) => setFilters({ ...filters, min_score_momentum: e.target.value })}
                    className="w-full px-2 py-1.5 text-sm bg-bg-primary border border-glass-border rounded-lg"
                  />
                </div>
              )}
              <div>
                <label className="text-xs text-text-muted">Type</label>
                <select
                  value={filters.asset_type}
                  onChange={(e) => setFilters({ ...filters, asset_type: e.target.value })}
                  className="w-full px-2 py-1.5 text-sm bg-bg-primary border border-glass-border rounded-lg"
                >
                  <option value="">Tous</option>
                  <option value="EQUITY">Actions</option>
                  <option value="ETF">ETF</option>
                  <option value="BOND">Obligations</option>
                </select>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-text-muted border-b border-glass-border bg-surface/50">
              <th className="px-4 py-3 font-medium">Ticker</th>
              <th className="px-4 py-3 font-medium hidden md:table-cell">Nom</th>
              <th 
                className="px-4 py-3 font-medium cursor-pointer hover:text-accent"
                onClick={() => handleSort('score_total')}
              >
                <span className="flex items-center gap-1">
                  Score
                  <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th 
                className="px-4 py-3 font-medium cursor-pointer hover:text-accent"
                onClick={() => handleSort(isCore ? 'score_safety' : 'score_momentum')}
              >
                <span className="flex items-center gap-1">
                  {isCore ? 'Safety' : 'Momentum'}
                  <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th 
                className="px-4 py-3 font-medium cursor-pointer hover:text-accent hidden lg:table-cell"
                onClick={() => handleSort('vol_annual')}
              >
                <span className="flex items-center gap-1">
                  Vol
                  <ArrowUpDown className="w-3 h-3" />
                </span>
              </th>
              <th className="px-4 py-3 font-medium hidden lg:table-cell">Status</th>
              <th className="px-4 py-3 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center">
                  <Loader2 className="w-6 h-6 mx-auto text-accent animate-spin" />
                </td>
              </tr>
            )}

            {error && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-score-red">
                  Erreur de chargement
                </td>
              </tr>
            )}

            {!isLoading && candidates.map((candidate: any, idx: number) => {
              const isAdded = addedAssetIds.includes(candidate.asset_id);
              const hasWarnings = candidate.warnings && candidate.warnings.length > 0;

              return (
                <motion.tr
                  key={candidate.asset_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  className={cn(
                    'border-b border-glass-border/50 hover:bg-surface/50 transition-colors',
                    isAdded && 'bg-accent/5'
                  )}
                >
                  <td className="px-4 py-3">
                    <button
                      onClick={() => onSelectAsset?.(candidate.asset_id)}
                      className="font-mono font-bold text-accent hover:underline"
                    >
                      {candidate.ticker}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-text-secondary max-w-[200px] truncate hidden md:table-cell">
                    {candidate.name}
                  </td>
                  <td className="px-4 py-3">
                    <ScoreGaugeBadge score={candidate.score_total} size="sm" />
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      'font-medium',
                      (isCore ? candidate.score_safety : candidate.score_momentum) > 60 
                        ? 'text-score-green' 
                        : 'text-text-secondary'
                    )}>
                      {(isCore ? candidate.score_safety : candidate.score_momentum)?.toFixed(0)}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <span className={cn(
                      'font-medium',
                      candidate.vol_annual < 25 ? 'text-score-green' :
                      candidate.vol_annual < 40 ? 'text-score-yellow' : 'text-score-red'
                    )}>
                      {candidate.vol_annual?.toFixed(1)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    {hasWarnings ? (
                      <span className="inline-flex items-center gap-1 text-xs text-score-yellow">
                        <AlertTriangle className="w-3 h-3" />
                        {candidate.warnings.length} alert{candidate.warnings.length > 1 ? 's' : ''}
                      </span>
                    ) : (
                      <span className="text-xs text-score-green">✓ Eligible</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant={isAdded ? 'ghost' : 'secondary'}
                      disabled={isAdded}
                      onClick={() => onAddToBuilder?.(candidate)}
                      className={cn(
                        isCore ? 'hover:bg-score-green/10 hover:text-score-green' : 'hover:bg-score-red/10 hover:text-score-red'
                      )}
                    >
                      {isAdded ? 'Ajouté' : <Plus className="w-4 h-4" />}
                    </Button>
                  </td>
                </motion.tr>
              );
            })}

            {!isLoading && candidates.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-text-muted">
                  Aucun candidat trouvé
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-glass-border flex items-center justify-between">
          <span className="text-sm text-text-muted">
            Page {page + 1} sur {totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              disabled={page === 0}
              onClick={() => setPage(p => p - 1)}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(p => p + 1)}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </GlassCard>
  );
}

export default CandidatesTable;
