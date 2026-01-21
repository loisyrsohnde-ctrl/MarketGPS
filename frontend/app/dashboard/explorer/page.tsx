'use client';

import { useState, useCallback, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Pill, ScoreGaugeBadge } from '@/components/ui/badge';
import { AssetLogo } from '@/components/cards/asset-card';
import { cn, formatNumberSafe } from '@/lib/utils';
import type { Asset, MarketFilter, AssetType } from '@/types';
import {
  ArrowLeft,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Loader2,
  RefreshCw,
  ArrowUpDown,
  TrendingUp,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// API Configuration
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

interface ExplorerParams {
  market_scope: string;
  asset_type?: string;
  query?: string;
  only_scored: boolean;
  sort_by: string;
  sort_desc: boolean;
  page: number;
  page_size: number;
}

interface ExplorerResponse {
  data: Asset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

async function fetchExplorerData(params: ExplorerParams): Promise<ExplorerResponse> {
  const searchParams = new URLSearchParams();
  searchParams.append('market_scope', params.market_scope);
  searchParams.append('page', params.page.toString());
  searchParams.append('page_size', params.page_size.toString());
  searchParams.append('sort_by', params.sort_by);
  searchParams.append('sort_desc', params.sort_desc.toString());
  searchParams.append('only_scored', params.only_scored.toString());
  
  if (params.asset_type) {
    searchParams.append('asset_type', params.asset_type);
  }
  if (params.query) {
    searchParams.append('query', params.query);
  }

  const response = await fetch(`${API_BASE_URL}/api/assets/explorer?${searchParams.toString()}`);
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPLORER PAGE CONTENT
// ═══════════════════════════════════════════════════════════════════════════

function ExplorerPageContent() {
  const searchParams = useSearchParams();
  const initialScope = (searchParams.get('scope') as 'US_EU' | 'AFRICA') || 'US_EU';
  
  const [marketScope, setMarketScope] = useState<'US_EU' | 'AFRICA'>(initialScope);
  const [typeFilter, setTypeFilter] = useState<AssetType | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState<'score_total' | 'symbol' | 'name'>('symbol');
  const [sortDesc, setSortDesc] = useState(false);
  const [onlyScored, setOnlyScored] = useState(false); // Show ALL assets by default
  
  const pageSize = 50;
  
  // Update scope when URL changes
  useEffect(() => {
    const urlScope = searchParams.get('scope') as 'US_EU' | 'AFRICA';
    if (urlScope && urlScope !== marketScope) {
      setMarketScope(urlScope);
      setCurrentPage(1);
    }
  }, [searchParams, marketScope]);

  // Debounce search
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    const timer = setTimeout(() => {
      setDebouncedQuery(value);
      setCurrentPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  // Fetch data
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['explorer', marketScope, typeFilter, debouncedQuery, currentPage, sortBy, sortDesc, onlyScored],
    queryFn: () => fetchExplorerData({
      market_scope: marketScope,
      asset_type: typeFilter || undefined,
      query: debouncedQuery || undefined,
      only_scored: onlyScored,
      sort_by: sortBy,
      sort_desc: sortDesc,
      page: currentPage,
      page_size: pageSize,
    }),
    staleTime: 60000,
    retry: 2,
  });

  const assets = data?.data || [];
  const totalPages = data?.total_pages || 1;
  const totalAssets = data?.total || 0;

  const marketFilters: { value: 'US_EU' | 'AFRICA'; label: string; icon: string }[] = [
    { value: 'US_EU', label: 'US / Europe', icon: '🇺🇸🇪🇺' },
    { value: 'AFRICA', label: 'Afrique', icon: '🌍' },
  ];

  // Tous les types d'instruments financiers disponibles
  const typeFilters: { value: AssetType | null; label: string }[] = [
    { value: null, label: 'Tous types' },
    { value: 'EQUITY', label: 'Actions' },
    { value: 'ETF', label: 'ETF' },
    { value: 'FX', label: 'Forex' },
    { value: 'BOND', label: 'Obligations' },
    { value: 'OPTION', label: 'Options' },
    { value: 'FUTURE', label: 'Futures' },
    { value: 'CRYPTO', label: 'Crypto' },
    { value: 'COMMODITY', label: 'Matières 1ères' },
  ];

  const toggleSort = (column: 'score_total' | 'symbol' | 'name') => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(column === 'score_total');
    }
  };

  return (
    <div className="space-y-6">
      {/* ─────────────────────────────────────────────────────────────────
         HEADER
         ───────────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Retour
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Explorer les actifs</h1>
            <p className="text-sm text-text-muted">
              {formatNumberSafe(totalAssets)} actifs disponibles
            </p>
          </div>
        </div>
        
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={() => refetch()}
          leftIcon={<RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />}
        >
          Actualiser
        </Button>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
         FILTERS
         ───────────────────────────────────────────────────────────────── */}
      <GlassCard>
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px] max-w-md">
            <Input
              placeholder="Rechercher un actif..."
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>

          <div className="h-6 w-px bg-glass-border" />

          {/* Market scope */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-text-muted" />
            <div className="flex gap-2">
              {marketFilters.map((f) => (
                <Pill
                  key={f.value}
                  active={marketScope === f.value}
                  onClick={() => {
                    setMarketScope(f.value);
                    setCurrentPage(1);
                  }}
                  icon={<span>{f.icon}</span>}
                >
                  {f.label}
                </Pill>
              ))}
            </div>
          </div>

          <div className="h-6 w-px bg-glass-border" />

          {/* Type filter */}
          <div className="flex flex-wrap gap-2">
            {typeFilters.map((f) => (
              <Pill
                key={f.value || 'all'}
                active={typeFilter === f.value}
                onClick={() => {
                  setTypeFilter(f.value);
                  setCurrentPage(1);
                }}
              >
                {f.label}
              </Pill>
            ))}
          </div>

          <div className="h-6 w-px bg-glass-border" />

          {/* Only scored toggle */}
          <Pill
            active={onlyScored}
            onClick={() => {
              setOnlyScored(!onlyScored);
              setCurrentPage(1);
            }}
            icon={<TrendingUp className="w-3 h-3" />}
          >
            Scorés uniquement
          </Pill>
        </div>
      </GlassCard>

      {/* ─────────────────────────────────────────────────────────────────
         ERROR STATE
         ───────────────────────────────────────────────────────────────── */}
      {isError && (
        <GlassCard className="border-score-red/30 bg-score-red/5">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-score-red" />
            <div className="flex-1">
              <h3 className="font-semibold text-text-primary">Erreur de chargement</h3>
              <p className="text-sm text-text-secondary">
                {error instanceof Error ? error.message : 'Impossible de charger les données'}
              </p>
            </div>
            <Button variant="secondary" onClick={() => refetch()}>
              Réessayer
            </Button>
          </div>
        </GlassCard>
      )}

      {/* ─────────────────────────────────────────────────────────────────
         TABLE
         ───────────────────────────────────────────────────────────────── */}
      <GlassCardAccent padding="none">
        {/* Table Header */}
        <div className="grid grid-cols-12 gap-4 p-4 border-b border-glass-border bg-bg-elevated/50">
          <div className="col-span-1 text-xs font-semibold text-text-muted uppercase">#</div>
          <button 
            onClick={() => toggleSort('symbol')}
            className="col-span-2 flex items-center gap-1 text-xs font-semibold text-text-muted uppercase hover:text-text-primary transition-colors"
          >
            Ticker
            <ArrowUpDown className="w-3 h-3" />
          </button>
          <button
            onClick={() => toggleSort('name')}
            className="col-span-4 flex items-center gap-1 text-xs font-semibold text-text-muted uppercase hover:text-text-primary transition-colors"
          >
            Nom
            <ArrowUpDown className="w-3 h-3" />
          </button>
          <div className="col-span-1 text-xs font-semibold text-text-muted uppercase">Type</div>
          <button
            onClick={() => toggleSort('score_total')}
            className="col-span-2 flex items-center gap-1 text-xs font-semibold text-text-muted uppercase hover:text-text-primary transition-colors"
          >
            Score
            <ArrowUpDown className="w-3 h-3" />
          </button>
          <div className="col-span-2 text-xs font-semibold text-text-muted uppercase text-right">Action</div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-glass-border">
          {isLoading ? (
            // Skeleton
            Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="grid grid-cols-12 gap-4 p-4">
                <div className="col-span-1"><div className="h-4 w-8 skeleton rounded" /></div>
                <div className="col-span-2"><div className="h-4 w-16 skeleton rounded" /></div>
                <div className="col-span-4"><div className="h-4 w-48 skeleton rounded" /></div>
                <div className="col-span-1"><div className="h-4 w-12 skeleton rounded" /></div>
                <div className="col-span-2"><div className="h-6 w-12 skeleton rounded" /></div>
                <div className="col-span-2"><div className="h-8 w-20 skeleton rounded ml-auto" /></div>
              </div>
            ))
          ) : assets.length === 0 ? (
            // Empty state
            <div className="p-12 text-center">
              <Search className="w-12 h-12 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary text-lg">Aucun actif trouvé</p>
              <p className="text-sm text-text-muted mt-1">
                Essayez de modifier vos filtres
              </p>
            </div>
          ) : (
            assets.map((asset, index) => (
              <motion.div
                key={asset.asset_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.02 }}
                className="grid grid-cols-12 gap-4 p-4 hover:bg-surface/50 transition-colors"
              >
                <div className="col-span-1 text-sm text-text-muted">
                  {(currentPage - 1) * pageSize + index + 1}
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <AssetLogo ticker={asset.ticker} assetType={asset.asset_type} size="xs" />
                  <span className="font-semibold text-text-primary">{asset.ticker}</span>
                </div>
                <div className="col-span-4 text-sm text-text-secondary truncate">
                  {asset.name}
                </div>
                <div className="col-span-1">
                  <span className="px-2 py-0.5 rounded text-xs bg-surface text-text-muted">
                    {asset.asset_type}
                  </span>
                </div>
                <div className="col-span-2">
                  {asset.score_total ? (
                    <ScoreGaugeBadge score={asset.score_total} size="sm" />
                  ) : (
                    <span className="text-xs text-text-dim">—</span>
                  )}
                </div>
                <div className="col-span-2 text-right">
                  <Link href={`/asset/${asset.ticker}`}>
                    <Button variant="ghost" size="sm">
                      Détails
                    </Button>
                  </Link>
                </div>
              </motion.div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-glass-border bg-bg-elevated/30">
            <p className="text-sm text-text-muted">
              Page {currentPage} sur {totalPages} ({formatNumberSafe(totalAssets)} actifs)
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                leftIcon={<ChevronLeft className="w-4 h-4" />}
              >
                Précédent
              </Button>
              
              {/* Page numbers */}
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={cn(
                        'w-8 h-8 rounded-lg text-sm font-medium transition-colors',
                        pageNum === currentPage
                          ? 'bg-accent text-bg-primary'
                          : 'text-text-secondary hover:bg-surface'
                      )}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                rightIcon={<ChevronRight className="w-4 h-4" />}
              >
                Suivant
              </Button>
            </div>
          </div>
        )}
      </GlassCardAccent>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTED PAGE (with Suspense wrapper)
// ═══════════════════════════════════════════════════════════════════════════

export default function ExplorerPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    }>
      <ExplorerPageContent />
    </Suspense>
  );
}
