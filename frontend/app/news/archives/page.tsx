'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Clock,
  ArrowLeft,
  Search,
  Filter,
  ChevronDown,
  Loader2,
  Newspaper,
  TrendingUp,
  Calendar,
  SortAsc,
  SortDesc,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/config';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface NewsArticle {
  id: number;
  slug: string;
  title: string;
  excerpt: string | null;
  tags: string[] | null;
  country: string | null;
  image_url: string | null;
  source_name: string;
  published_at: string | null;
  category?: string;
  engagement_score?: number;
  is_breaking_news?: boolean;
  importance_level?: string;
}

interface ArchivesResponse {
  data: NewsArticle[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = getApiBaseUrl();

async function fetchArchives(
  page: number,
  pageSize: number,
  search: string,
  region: string,
  sortBy: string
): Promise<ArchivesResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (search) params.set('q', search);
  if (region && region !== 'all') params.set('region', region);
  if (sortBy === 'relevance') params.set('sort_by', 'relevance');

  const res = await fetch(`${API_BASE}/api/news?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch archives');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Category Styles
// ═══════════════════════════════════════════════════════════════════════════

const CATEGORY_STYLES: Record<string, string> = {
  fintech: 'bg-emerald-600 text-white',
  finance: 'bg-blue-600 text-white',
  startup: 'bg-violet-600 text-white',
  tech: 'bg-cyan-600 text-white',
  regulation: 'bg-amber-600 text-white',
  banking: 'bg-slate-700 text-white',
  default: 'bg-slate-600 text-white',
};

function getCategoryStyle(category?: string | null, tags?: string[] | null): string {
  if (category) return CATEGORY_STYLES[category.toLowerCase()] || CATEGORY_STYLES.default;
  if (tags && tags.length > 0) return CATEGORY_STYLES[tags[0].toLowerCase()] || CATEGORY_STYLES.default;
  return CATEGORY_STYLES.default;
}

function getCategoryLabel(category?: string | null, tags?: string[] | null): string {
  if (category) return category;
  if (tags && tags.length > 0) return tags[0];
  return 'Actualité';
}

// ═══════════════════════════════════════════════════════════════════════════
// Regions
// ═══════════════════════════════════════════════════════════════════════════

const REGIONS = [
  { id: 'all', name: 'Toutes les régions' },
  { id: 'PAN', name: 'Panafricain' },
  { id: 'WEST', name: 'Afrique de l\'Ouest' },
  { id: 'CENTRAL', name: 'Afrique Centrale' },
  { id: 'EAST', name: 'Afrique de l\'Est' },
  { id: 'NORTH', name: 'Afrique du Nord' },
  { id: 'SOUTH', name: 'Afrique Australe' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Archive Card Component
// ═══════════════════════════════════════════════════════════════════════════

function ArchiveCard({ article }: { article: NewsArticle }) {
  const category = getCategoryLabel(article.category, article.tags);
  const isBreaking = article.is_breaking_news;
  const isHighImportance = article.importance_level === 'high';

  return (
    <Link href={`/news/${article.slug}`} className="block group">
      <article className={cn(
        "bg-white rounded-sm border transition-all duration-200 hover:shadow-md",
        isBreaking ? "border-red-300 ring-1 ring-red-200" :
        isHighImportance ? "border-amber-300" : "border-slate-200"
      )}>
        <div className="flex gap-4 p-4">
          {/* Image Thumbnail */}
          <div className="w-24 h-24 md:w-32 md:h-32 flex-shrink-0 overflow-hidden rounded bg-slate-100">
            {article.image_url ? (
              <img
                src={article.image_url}
                alt=""
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Newspaper className="w-8 h-8 text-slate-300" />
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Badges */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {isBreaking && (
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-sm bg-red-600 text-white animate-pulse">
                  🔴 Alerte Info
                </span>
              )}
              {isHighImportance && !isBreaking && (
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-sm bg-amber-500 text-white">
                  ⚡ Important
                </span>
              )}
              <span className={cn(
                'px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-sm',
                getCategoryStyle(article.category, article.tags)
              )}>
                {category}
              </span>
              {article.country && (
                <span className="text-xs text-slate-500">
                  {article.country}
                </span>
              )}
            </div>

            {/* Title */}
            <h3 className="font-serif text-lg md:text-xl font-bold text-slate-900 leading-tight mb-2 group-hover:text-blue-700 transition-colors line-clamp-2">
              {article.title}
            </h3>

            {/* Excerpt */}
            {article.excerpt && (
              <p className="text-slate-600 text-sm line-clamp-2 mb-2 hidden md:block">
                {article.excerpt}
              </p>
            )}

            {/* Meta */}
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span className="font-medium">{article.source_name}</span>
              {article.published_at && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(article.published_at).toLocaleDateString('fr-FR', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric'
                    })}
                  </span>
                </>
              )}
              {article.engagement_score !== undefined && article.engagement_score > 0.7 && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1 text-emerald-600">
                    <TrendingUp className="w-3 h-3" />
                    Populaire
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Pagination Component
// ═══════════════════════════════════════════════════════════════════════════

function Pagination({
  page,
  totalPages,
  onPageChange
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  if (totalPages <= 1) return null;

  const pages = [];
  const showEllipsisStart = page > 3;
  const showEllipsisEnd = page < totalPages - 2;

  // Always show first page
  pages.push(1);

  if (showEllipsisStart) pages.push(-1); // Ellipsis

  // Show pages around current
  for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
    if (!pages.includes(i)) pages.push(i);
  }

  if (showEllipsisEnd) pages.push(-2); // Ellipsis

  // Always show last page
  if (totalPages > 1 && !pages.includes(totalPages)) pages.push(totalPages);

  return (
    <div className="flex items-center justify-center gap-2 mt-8">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Précédent
      </button>

      <div className="flex items-center gap-1">
        {pages.map((p, idx) =>
          p < 0 ? (
            <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">...</span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(p)}
              className={cn(
                'w-10 h-10 text-sm font-medium rounded transition-colors',
                p === page
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-700 hover:bg-slate-100'
              )}
            >
              {p}
            </button>
          )
        )}
      </div>

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Suivant
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════════

export default function ArchivesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [region, setRegion] = useState('all');
  const [sortBy, setSortBy] = useState<'date' | 'relevance'>('date');
  const pageSize = 30;

  const { data, isLoading, isError } = useQuery({
    queryKey: ['news-archives', page, search, region, sortBy],
    queryFn: () => fetchArchives(page, pageSize, search, region, sortBy),
    staleTime: 60000,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  const handleRegionChange = (newRegion: string) => {
    setRegion(newRegion);
    setPage(1);
  };

  const handleSortChange = () => {
    setSortBy(sortBy === 'date' ? 'relevance' : 'date');
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/news"
                className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span className="hidden sm:inline">Retour</span>
              </Link>
              <div className="h-6 w-px bg-slate-300" />
              <div>
                <h1 className="font-serif text-2xl font-bold text-slate-900">
                  Archives
                </h1>
                <p className="text-sm text-slate-500">
                  {data?.total || 0} articles disponibles
                </p>
              </div>
            </div>

            {/* Sort Toggle */}
            <button
              onClick={handleSortChange}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 bg-slate-100 rounded hover:bg-slate-200 transition-colors"
            >
              {sortBy === 'date' ? (
                <>
                  <Calendar className="w-4 h-4" />
                  <span className="hidden sm:inline">Par date</span>
                </>
              ) : (
                <>
                  <TrendingUp className="w-4 h-4" />
                  <span className="hidden sm:inline">Par pertinence</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Filters Bar */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Rechercher un article..."
                  className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </form>

            {/* Region Filter */}
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <select
                value={region}
                onChange={(e) => handleRegionChange(e.target.value)}
                className="pl-10 pr-8 py-2 border border-slate-300 rounded bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none cursor-pointer"
              >
                {REGIONS.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            </div>
          </div>

          {/* Active Filters */}
          {(search || region !== 'all') && (
            <div className="flex items-center gap-2 mt-3">
              <span className="text-xs text-slate-500">Filtres actifs:</span>
              {search && (
                <button
                  onClick={() => { setSearch(''); setSearchInput(''); }}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  &quot;{search}&quot;
                  <span className="font-bold">×</span>
                </button>
              )}
              {region !== 'all' && (
                <button
                  onClick={() => setRegion('all')}
                  className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  {REGIONS.find(r => r.id === region)?.name}
                  <span className="font-bold">×</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        ) : isError ? (
          <div className="text-center py-20">
            <p className="text-red-600">Erreur lors du chargement des archives</p>
          </div>
        ) : data?.data.length === 0 ? (
          <div className="text-center py-20">
            <Newspaper className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h2 className="font-serif text-2xl font-bold text-slate-800 mb-2">
              Aucun article trouvé
            </h2>
            <p className="text-slate-500">
              Essayez de modifier vos filtres ou votre recherche
            </p>
          </div>
        ) : (
          <>
            {/* Articles Grid */}
            <div className="space-y-4">
              {data?.data.map((article, idx) => (
                <motion.div
                  key={article.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: idx * 0.03 }}
                >
                  <ArchiveCard article={article} />
                </motion.div>
              ))}
            </div>

            {/* Pagination */}
            <Pagination
              page={page}
              totalPages={data?.total_pages || 1}
              onPageChange={setPage}
            />
          </>
        )}
      </main>
    </div>
  );
}
