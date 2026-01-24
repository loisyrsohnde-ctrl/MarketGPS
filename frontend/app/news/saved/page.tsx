'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Bookmark,
  ArrowLeft,
  Clock,
  Newspaper,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/config';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';

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
  saved_at?: string;
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

async function fetchSavedNews(page: number): Promise<NewsFeedResponse> {
  const res = await fetch(`${API_BASE}/api/news/saved?page=${page}&page_size=12`);
  if (!res.ok) throw new Error('Failed to fetch saved news');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Country flags
// ═══════════════════════════════════════════════════════════════════════════

const COUNTRY_FLAGS: Record<string, string> = {
  NG: '🇳🇬', ZA: '🇿🇦', KE: '🇰🇪', EG: '🇪🇬', GH: '🇬🇭',
  CI: '🇨🇮', SN: '🇸🇳', MA: '🇲🇦', TN: '🇹🇳', RW: '🇷🇼',
};

// ═══════════════════════════════════════════════════════════════════════════
// Components
// ═══════════════════════════════════════════════════════════════════════════

function SavedNewsCard({ article }: { article: NewsArticle }) {
  const flag = article.country ? COUNTRY_FLAGS[article.country] : null;
  
  return (
    <Link href={`/news/${article.slug}`}>
      <motion.div
        whileHover={{ y: -2 }}
        className={cn(
          'group flex gap-4 p-4',
          'bg-surface/50 hover:bg-surface/80',
          'border border-glass-border hover:border-accent/30',
          'rounded-xl',
          'transition-all duration-200',
          'cursor-pointer'
        )}
      >
        {/* Image */}
        {article.image_url && (
          <div className="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-bg-elevated">
            <img
              src={article.image_url}
              alt=""
              className="w-full h-full object-cover"
            />
          </div>
        )}
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Tags */}
          <div className="flex items-center gap-2 mb-1.5">
            {flag && <span className="text-sm">{flag}</span>}
            {article.tags?.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-accent/10 text-accent"
              >
                {tag}
              </span>
            ))}
          </div>
          
          {/* Title */}
          <h3 className="font-semibold text-text-primary group-hover:text-accent transition-colors line-clamp-2 mb-1">
            {article.title}
          </h3>
          
          {/* Meta */}
          <div className="flex items-center gap-3 text-xs text-text-muted">
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

function EmptyState() {
  return (
    <div className="py-16 text-center">
      <Bookmark className="w-16 h-16 text-text-muted mx-auto mb-4" />
      <h3 className="text-lg font-semibold text-text-primary mb-2">
        Aucun article sauvegardé
      </h3>
      <p className="text-text-secondary max-w-md mx-auto mb-6">
        Sauvegardez des articles pour les retrouver facilement ici.
      </p>
      <Link href="/news">
        <Button variant="secondary">
          Parcourir les actualités
        </Button>
      </Link>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Page
// ═══════════════════════════════════════════════════════════════════════════

export default function SavedNewsPage() {
  const [page, setPage] = useState(1);
  
  const { data, isLoading, isError } = useQuery({
    queryKey: ['news-saved', page],
    queryFn: () => fetchSavedNews(page),
    staleTime: 30000,
  });
  
  const articles = data?.data || [];
  const totalPages = data?.total_pages || 1;
  const total = data?.total || 0;
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/news" className="text-text-secondary hover:text-accent transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <Bookmark className="w-6 h-6 text-accent" />
            Articles sauvegardés
          </h1>
          <p className="text-sm text-text-secondary">
            {total} article{total !== 1 ? 's' : ''}
          </p>
        </div>
      </div>
      
      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      ) : articles.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-3">
          {articles.map((article, index) => (
            <motion.div
              key={article.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <SavedNewsCard article={article} />
            </motion.div>
          ))}
        </div>
      )}
      
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
