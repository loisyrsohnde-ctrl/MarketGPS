'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Newspaper,
  Search,
  Filter,
  Clock,
  ExternalLink,
  Bookmark,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/config';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Pill } from '@/components/ui/badge';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface NewsArticle {
  id: number;
  slug: string;
  title: string;
  excerpt: string | null;
  tldr: string[] | null;
  tags: string[] | null;
  country: string | null;
  image_url: string | null;
  source_name: string;
  published_at: string | null;
}

interface NewsFeedResponse {
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

async function fetchNewsFeed(params: {
  page: number;
  q?: string;
  country?: string;
  tag?: string;
}): Promise<NewsFeedResponse> {
  const searchParams = new URLSearchParams();
  searchParams.append('page', params.page.toString());
  searchParams.append('page_size', '12');
  
  if (params.q) searchParams.append('q', params.q);
  if (params.country) searchParams.append('country', params.country);
  if (params.tag) searchParams.append('tag', params.tag);
  
  const res = await fetch(`${API_BASE}/api/news?${searchParams}`);
  if (!res.ok) throw new Error('Failed to fetch news');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Country flags
// ═══════════════════════════════════════════════════════════════════════════

const COUNTRY_FLAGS: Record<string, string> = {
  NG: '🇳🇬',
  ZA: '🇿🇦',
  KE: '🇰🇪',
  EG: '🇪🇬',
  GH: '🇬🇭',
  CI: '🇨🇮',
  SN: '🇸🇳',
  MA: '🇲🇦',
  TN: '🇹🇳',
  RW: '🇷🇼',
  CM: '🇨🇲',
  UG: '🇺🇬',
  TG: '🇹🇬',
  GA: '🇬🇦',
};

const TAGS = [
  { id: 'fintech', label: 'Fintech' },
  { id: 'startup', label: 'Startup' },
  { id: 'vc', label: 'VC / Levée' },
  { id: 'regulation', label: 'Régulation' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'banking', label: 'Banque' },
];

const COUNTRIES = [
  { code: 'NG', name: 'Nigeria' },
  { code: 'ZA', name: 'Afrique du Sud' },
  { code: 'KE', name: 'Kenya' },
  { code: 'EG', name: 'Égypte' },
  { code: 'GH', name: 'Ghana' },
  { code: 'CI', name: "Côte d'Ivoire" },
];

// ═══════════════════════════════════════════════════════════════════════════
// Components
// ═══════════════════════════════════════════════════════════════════════════

function NewsCard({ article }: { article: NewsArticle }) {
  const flag = article.country ? COUNTRY_FLAGS[article.country] : null;
  
  return (
    <Link href={`/news/${article.slug}`}>
      <motion.div
        whileHover={{ y: -2 }}
        className={cn(
          'group h-full',
          'bg-surface/50 hover:bg-surface/80',
          'border border-glass-border hover:border-accent/30',
          'rounded-xl overflow-hidden',
          'transition-all duration-200',
          'cursor-pointer'
        )}
      >
        {/* Image */}
        {article.image_url && (
          <div className="aspect-video bg-bg-elevated overflow-hidden">
            <img
              src={article.image_url}
              alt=""
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          </div>
        )}
        
        {/* Content */}
        <div className="p-4">
          {/* Tags & Country */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            {flag && (
              <span className="text-sm">{flag}</span>
            )}
            {article.tags?.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 rounded text-[10px] font-medium bg-accent/10 text-accent"
              >
                {tag}
              </span>
            ))}
          </div>
          
          {/* Title */}
          <h3 className="font-semibold text-text-primary group-hover:text-accent transition-colors line-clamp-2 mb-2">
            {article.title}
          </h3>
          
          {/* Excerpt */}
          {article.excerpt && (
            <p className="text-sm text-text-secondary line-clamp-2 mb-3">
              {article.excerpt}
            </p>
          )}
          
          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span className="flex items-center gap-1">
              <Newspaper className="w-3 h-3" />
              {article.source_name}
            </span>
            {article.published_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(article.published_at).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'short'
                })}
              </span>
            )}
          </div>
        </div>
      </motion.div>
    </Link>
  );
}

function NewsCardSkeleton() {
  return (
    <div className="bg-surface/50 border border-glass-border rounded-xl overflow-hidden">
      <div className="aspect-video bg-bg-elevated skeleton" />
      <div className="p-4 space-y-3">
        <div className="flex gap-2">
          <div className="h-4 w-12 skeleton rounded" />
          <div className="h-4 w-16 skeleton rounded" />
        </div>
        <div className="h-5 w-full skeleton rounded" />
        <div className="h-4 w-3/4 skeleton rounded" />
        <div className="flex justify-between">
          <div className="h-3 w-20 skeleton rounded" />
          <div className="h-3 w-16 skeleton rounded" />
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="col-span-full py-16 text-center">
      <Newspaper className="w-16 h-16 text-text-muted mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        Aucune actualité trouvée
      </h3>
      <p className="text-text-secondary max-w-md mx-auto">
        Les actualités Fintech Afrique seront bientôt disponibles.
        Revenez prochainement !
      </p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Page
// ═══════════════════════════════════════════════════════════════════════════

export default function NewsPage() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);
  
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['news', page, searchQuery, selectedTag, selectedCountry],
    queryFn: () => fetchNewsFeed({
      page,
      q: searchQuery || undefined,
      tag: selectedTag || undefined,
      country: selectedCountry || undefined,
    }),
    staleTime: 60000,
  });
  
  const articles = data?.data || [];
  const totalPages = data?.total_pages || 1;
  
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPage(1);
  };
  
  const handleTagClick = (tag: string) => {
    setSelectedTag(selectedTag === tag ? null : tag);
    setPage(1);
  };
  
  const handleCountryClick = (country: string) => {
    setSelectedCountry(selectedCountry === country ? null : country);
    setPage(1);
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary flex items-center gap-3">
            <Newspaper className="w-8 h-8 text-accent" />
            Actualités
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Fintech & Startups Afrique
          </p>
        </div>
        
        <Link href="/news/saved">
          <Button variant="secondary" size="sm" leftIcon={<Bookmark className="w-4 h-4" />}>
            Sauvegardés
          </Button>
        </Link>
      </div>
      
      {/* Filters */}
      <GlassCard className="space-y-4">
        {/* Search */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
        </div>
        
        {/* Tags */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-text-muted self-center mr-2">Tags:</span>
          {TAGS.map((tag) => (
            <Pill
              key={tag.id}
              active={selectedTag === tag.id}
              onClick={() => handleTagClick(tag.id)}
            >
              {tag.label}
            </Pill>
          ))}
        </div>
        
        {/* Countries */}
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-text-muted self-center mr-2">Pays:</span>
          {COUNTRIES.map((country) => (
            <button
              key={country.code}
              onClick={() => handleCountryClick(country.code)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm transition-colors',
                'flex items-center gap-1.5',
                selectedCountry === country.code
                  ? 'bg-accent text-bg-primary'
                  : 'bg-surface text-text-secondary hover:bg-surface-hover'
              )}
            >
              <span>{COUNTRY_FLAGS[country.code]}</span>
              <span className="hidden sm:inline">{country.name}</span>
            </button>
          ))}
        </div>
      </GlassCard>
      
      {/* Error State */}
      {isError && (
        <GlassCard className="border-score-red/30 bg-score-red/5">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-score-red flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-text-primary">Erreur de chargement</h3>
              <p className="text-sm text-text-secondary">
                {error instanceof Error ? error.message : 'Impossible de charger les actualités'}
              </p>
            </div>
          </div>
        </GlassCard>
      )}
      
      {/* Articles Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <NewsCardSkeleton key={i} />
          ))
        ) : articles.length === 0 ? (
          <EmptyState />
        ) : (
          articles.map((article, index) => (
            <motion.div
              key={article.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <NewsCard article={article} />
            </motion.div>
          ))
        )}
      </div>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Précédent
          </Button>
          
          <span className="text-sm text-text-muted">
            Page {page} sur {totalPages}
          </span>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
          >
            Suivant
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </div>
      )}
    </div>
  );
}
