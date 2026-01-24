'use client';

import { useState, useCallback, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Pill, ScoreGaugeBadge } from '@/components/ui/badge';
import { AssetLogo } from '@/components/cards/asset-card';
import { AssetListItem, AssetListSkeleton } from '@/components/cards/AssetListItem';
import { useAssetInspector } from '@/store/useAssetInspector';
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
  country?: string;  // Country code for filtering (e.g., 'ZA', 'NG')
  region?: string;   // Region for filtering (e.g., 'SOUTHERN', 'WEST')
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
  if (params.country) {
    searchParams.append('country', params.country);
  }
  if (params.region) {
    searchParams.append('region', params.region);
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
  
  // Global inspector
  const { openInspector } = useAssetInspector();
  
  const [marketScope, setMarketScope] = useState<'US_EU' | 'AFRICA'>(initialScope);
  const [typeFilter, setTypeFilter] = useState<AssetType | null>(null);
  const [africaRegion, setAfricaRegion] = useState<string | null>(null); // Africa subdivision
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState<'score_total' | 'symbol' | 'name'>('symbol');
  const [sortDesc, setSortDesc] = useState(false);
  const [onlyScored, setOnlyScored] = useState(false); // Show ALL assets by default

  // Africa regions/countries configuration
  const africaRegions = [
    { value: null, label: 'Toute l\'Afrique', icon: '🌍', countries: [] },
    // Southern Africa
    { value: 'SOUTHERN', label: 'Afrique Australe', icon: '🇿🇦', countries: ['ZA', 'BW', 'ZW', 'ZM', 'MW', 'MZ', 'NA', 'LS', 'SZ'] },
    // West Africa  
    { value: 'WEST', label: 'Afrique de l\'Ouest', icon: '🇳🇬', countries: ['NG', 'GH', 'CI', 'SN', 'ML', 'BF', 'NE', 'BJ', 'TG'] },
    // North Africa
    { value: 'NORTH', label: 'Afrique du Nord', icon: '🇲🇦', countries: ['MA', 'DZ', 'TN', 'EG', 'LY'] },
    // East Africa
    { value: 'EAST', label: 'Afrique de l\'Est', icon: '🇰🇪', countries: ['KE', 'TZ', 'UG', 'RW', 'ET', 'MU'] },
    // Central Africa
    { value: 'CENTRAL', label: 'Afrique Centrale', icon: '🇨🇲', countries: ['CM', 'CD', 'CG', 'GA', 'CF', 'TD'] },
  ];

  // Individual countries for detailed filtering
  const africaCountries = [
    { value: 'ZA', label: 'Afrique du Sud', icon: '🇿🇦', exchange: 'JSE' },
    { value: 'NG', label: 'Nigeria', icon: '🇳🇬', exchange: 'NGX' },
    { value: 'EG', label: 'Égypte', icon: '🇪🇬', exchange: 'EGX' },
    { value: 'MA', label: 'Maroc', icon: '🇲🇦', exchange: 'CSE' },
    { value: 'KE', label: 'Kenya', icon: '🇰🇪', exchange: 'NSE' },
    { value: 'CI', label: 'Côte d\'Ivoire (BRVM)', icon: '🇨🇮', exchange: 'BRVM' },
    { value: 'GH', label: 'Ghana', icon: '🇬🇭', exchange: 'GSE' },
    { value: 'TN', label: 'Tunisie', icon: '🇹🇳', exchange: 'BVMT' },
    { value: 'MU', label: 'Maurice', icon: '🇲🇺', exchange: 'SEM' },
    { value: 'BW', label: 'Botswana', icon: '🇧🇼', exchange: 'BSE' },
  ];
  
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

  // Determine if africaRegion is a country code or a region
  const isAfricaCountryCode = africaRegion && africaRegion.length === 2;
  const africaCountryFilter = isAfricaCountryCode ? africaRegion : undefined;
  const africaRegionFilter = africaRegion && !isAfricaCountryCode ? africaRegion : undefined;

  // Fetch data
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['explorer', marketScope, typeFilter, africaRegion, debouncedQuery, currentPage, sortBy, sortDesc, onlyScored],
    queryFn: () => fetchExplorerData({
      market_scope: marketScope,
      asset_type: typeFilter || undefined,
      country: africaCountryFilter,
      region: africaRegionFilter,
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
         HEADER (responsive)
         ───────────────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3 sm:gap-4">
          <Link href="/dashboard" className="hidden sm:block">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Retour
            </Button>
          </Link>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-text-primary">Explorer</h1>
            <p className="text-xs sm:text-sm text-text-muted">
              {formatNumberSafe(totalAssets)} actifs
            </p>
          </div>
        </div>
        
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={() => refetch()}
          leftIcon={<RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />}
          className="self-end sm:self-auto"
        >
          <span className="hidden sm:inline">Actualiser</span>
          <span className="sm:hidden">Sync</span>
        </Button>
      </div>

      {/* ─────────────────────────────────────────────────────────────────
         FILTERS (responsive)
         ───────────────────────────────────────────────────────────────── */}
      <GlassCard className="overflow-hidden">
        <div className="space-y-3">
          {/* Row 1: Search + Market scope */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Search */}
            <div className="flex-1 min-w-0">
              <Input
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>

            {/* Market scope pills */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <Filter className="w-4 h-4 text-text-muted hidden sm:block" />
              <div className="flex gap-1 sm:gap-2">
                {marketFilters.map((f) => (
                  <Pill
                    key={f.value}
                    active={marketScope === f.value}
                    onClick={() => {
                      setMarketScope(f.value);
                      setAfricaRegion(null);
                      setCurrentPage(1);
                    }}
                    icon={<span className="text-sm">{f.icon}</span>}
                  >
                    <span className="hidden sm:inline">{f.label}</span>
                  </Pill>
                ))}
              </div>
            </div>
          </div>

          {/* Row 2: Type filters (horizontal scroll on mobile) */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap">
            {typeFilters.map((f) => (
              <Pill
                key={f.value || 'all'}
                active={typeFilter === f.value}
                onClick={() => {
                  setTypeFilter(f.value);
                  setCurrentPage(1);
                }}
                className="flex-shrink-0"
              >
                {f.label}
              </Pill>
            ))}
            <div className="w-px h-6 bg-glass-border hidden sm:block flex-shrink-0" />
            <Pill
              active={onlyScored}
              onClick={() => {
                setOnlyScored(!onlyScored);
                setCurrentPage(1);
              }}
              icon={<TrendingUp className="w-3 h-3" />}
              className="flex-shrink-0"
            >
              <span className="hidden sm:inline">Scorés uniquement</span>
              <span className="sm:hidden">Scorés</span>
            </Pill>
          </div>

          {/* Africa region filter - only shown when Africa is selected */}
          {marketScope === 'AFRICA' && (
            <div className="pt-2 border-t border-glass-border space-y-2">
              {/* Regions */}
              <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap">
                {africaRegions.map((region) => (
                  <Pill
                    key={region.value || 'all'}
                    active={africaRegion === region.value}
                    onClick={() => {
                      setAfricaRegion(region.value);
                      setCurrentPage(1);
                    }}
                    icon={<span className="text-xs">{region.icon}</span>}
                    className="flex-shrink-0"
                  >
                    <span className="text-xs">{region.label}</span>
                  </Pill>
                ))}
              </div>
              {/* Countries */}
              <div className="flex gap-1 overflow-x-auto pb-1 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 sm:flex-wrap">
                {africaCountries.map((country) => (
                  <button
                    key={country.value}
                    onClick={() => {
                      setAfricaRegion(country.value);
                      setCurrentPage(1);
                    }}
                    className={cn(
                      "px-2 py-1 rounded text-xs transition-all flex-shrink-0 min-h-[32px]",
                      africaRegion === country.value
                        ? "bg-accent text-white"
                        : "bg-glass-subtle text-text-secondary active:bg-glass-border"
                    )}
                  >
                    <span className="mr-1">{country.icon}</span>
                    {country.exchange}
                  </button>
                ))}
              </div>
            </div>
          )}
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
         ASSET LIST (responsive: cards on mobile, table on desktop)
         ───────────────────────────────────────────────────────────────── */}
      <GlassCardAccent padding="none">
        {/* Desktop Table Header - hidden on mobile */}
        <div className="hidden md:grid grid-cols-12 gap-4 p-4 border-b border-glass-border bg-bg-elevated/50">
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

        {/* Mobile Sort Bar - visible only on mobile */}
        <div className="md:hidden flex items-center justify-between p-3 border-b border-glass-border bg-bg-elevated/50">
          <span className="text-xs text-text-muted">
            {formatNumberSafe(totalAssets)} résultats
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleSort('score_total')}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-colors",
                sortBy === 'score_total' ? "bg-accent/20 text-accent" : "bg-surface text-text-muted"
              )}
            >
              <ArrowUpDown className="w-3 h-3" />
              Score
            </button>
            <button
              onClick={() => toggleSort('symbol')}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-colors",
                sortBy === 'symbol' ? "bg-accent/20 text-accent" : "bg-surface text-text-muted"
              )}
            >
              <ArrowUpDown className="w-3 h-3" />
              A-Z
            </button>
          </div>
        </div>

        {/* List Body - responsive */}
        <div className="divide-y divide-glass-border md:divide-y-0">
          {/* Mobile: card grid with gaps */}
          <div className="md:hidden p-3 space-y-2">
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <AssetListSkeleton key={i} />
              ))
            ) : assets.length === 0 ? (
              <div className="py-12 text-center">
                <Search className="w-10 h-10 text-text-muted mx-auto mb-3" />
                <p className="text-text-secondary">Aucun actif trouvé</p>
                <p className="text-xs text-text-muted mt-1">Modifiez vos filtres</p>
              </div>
            ) : (
              assets.map((asset, index) => (
                <motion.div
                  key={asset.asset_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(index * 0.02, 0.2) }}
                >
                  <AssetListItem
                    asset={asset}
                    index={(currentPage - 1) * pageSize + index + 1}
                    onInspect={openInspector}
                  />
                </motion.div>
              ))
            )}
          </div>

          {/* Desktop: table rows */}
          <div className="hidden md:block divide-y divide-glass-border">
            {isLoading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <AssetListSkeleton key={i} />
              ))
            ) : assets.length === 0 ? (
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
                >
                  <AssetListItem
                    asset={asset}
                    index={(currentPage - 1) * pageSize + index + 1}
                    onInspect={openInspector}
                  />
                </motion.div>
              ))
            )}
          </div>
        </div>

        {/* Pagination (responsive) */}
        {totalPages > 1 && (
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 sm:p-4 border-t border-glass-border bg-bg-elevated/30">
            <p className="text-xs sm:text-sm text-text-muted text-center sm:text-left">
              Page {currentPage}/{totalPages}
              <span className="hidden sm:inline"> ({formatNumberSafe(totalAssets)} actifs)</span>
            </p>
            <div className="flex items-center justify-center gap-1 sm:gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-2 sm:px-3"
              >
                <ChevronLeft className="w-4 h-4" />
                <span className="hidden sm:inline ml-1">Préc</span>
              </Button>
              
              {/* Page numbers - fewer on mobile */}
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(typeof window !== 'undefined' && window.innerWidth < 640 ? 3 : 5, totalPages) }, (_, i) => {
                  const maxPages = 5;
                  let pageNum: number;
                  if (totalPages <= maxPages) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - maxPages + 1 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={cn(
                        'w-8 h-8 sm:w-9 sm:h-9 rounded-lg text-sm font-medium transition-colors',
                        pageNum === currentPage
                          ? 'bg-accent text-bg-primary'
                          : 'text-text-secondary active:bg-surface'
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
                className="px-2 sm:px-3"
              >
                <span className="hidden sm:inline mr-1">Suiv</span>
                <ChevronRight className="w-4 h-4" />
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
