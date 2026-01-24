'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Bookmark,
  BookmarkCheck,
  Share2,
  ExternalLink,
  Clock,
  Newspaper,
  Copy,
  Check,
  Loader2,
  AlertCircle,
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
  content_md: string | null;
  tldr: string[] | null;
  tags: string[] | null;
  country: string | null;
  language: string;
  image_url: string | null;
  source_name: string;
  source_url: string;
  canonical_url: string | null;
  published_at: string | null;
  view_count: number;
  is_saved: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// API
// ═══════════════════════════════════════════════════════════════════════════

const API_BASE = getApiBaseUrl();

async function fetchArticle(slug: string): Promise<NewsArticle> {
  const res = await fetch(`${API_BASE}/api/news/${slug}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error('Article non trouvé');
    throw new Error('Failed to fetch article');
  }
  return res.json();
}

async function saveArticle(articleId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/news/${articleId}/save`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to save');
}

async function unsaveArticle(articleId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/news/${articleId}/save`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to unsave');
}

// ═══════════════════════════════════════════════════════════════════════════
// Country flags
// ═══════════════════════════════════════════════════════════════════════════

const COUNTRY_FLAGS: Record<string, string> = {
  NG: '🇳🇬', ZA: '🇿🇦', KE: '🇰🇪', EG: '🇪🇬', GH: '🇬🇭',
  CI: '🇨🇮', SN: '🇸🇳', MA: '🇲🇦', TN: '🇹🇳', RW: '🇷🇼',
};

// ═══════════════════════════════════════════════════════════════════════════
// Page
// ═══════════════════════════════════════════════════════════════════════════

export default function ArticlePage() {
  const params = useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const slug = params.slug as string;
  
  const [copied, setCopied] = useState(false);
  
  const { data: article, isLoading, isError, error } = useQuery({
    queryKey: ['news-article', slug],
    queryFn: () => fetchArticle(slug),
    staleTime: 30000,
  });
  
  const saveMutation = useMutation({
    mutationFn: () => article ? saveArticle(article.id) : Promise.reject(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news-article', slug] });
    },
  });
  
  const unsaveMutation = useMutation({
    mutationFn: () => article ? unsaveArticle(article.id) : Promise.reject(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news-article', slug] });
    },
  });
  
  const handleShare = async () => {
    const url = window.location.href;
    
    // Try Web Share API (mobile)
    if (navigator.share) {
      try {
        await navigator.share({
          title: article?.title,
          text: article?.excerpt || undefined,
          url,
        });
        return;
      } catch (e) {
        // User cancelled or not supported
      }
    }
    
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      console.error('Failed to copy:', e);
    }
  };
  
  const handleSaveToggle = () => {
    if (!article) return;
    
    if (article.is_saved) {
      unsaveMutation.mutate();
    } else {
      saveMutation.mutate();
    }
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }
  
  // Error state
  if (isError || !article) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <AlertCircle className="w-16 h-16 text-score-red mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Article non trouvé
        </h1>
        <p className="text-text-secondary mb-6">
          {error instanceof Error ? error.message : "Cet article n'existe pas ou a été supprimé."}
        </p>
        <Link href="/news">
          <Button variant="secondary">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour aux actualités
          </Button>
        </Link>
      </div>
    );
  }
  
  const flag = article.country ? COUNTRY_FLAGS[article.country] : null;
  
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Back button */}
      <Link href="/news" className="inline-flex items-center text-text-secondary hover:text-accent transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Retour aux actualités
      </Link>
      
      {/* Header */}
      <header className="space-y-4">
        {/* Tags & Country */}
        <div className="flex items-center gap-2 flex-wrap">
          {flag && <span className="text-xl">{flag}</span>}
          {article.tags?.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 rounded text-xs font-medium bg-accent/10 text-accent"
            >
              {tag}
            </span>
          ))}
        </div>
        
        {/* Title */}
        <h1 className="text-2xl sm:text-3xl font-bold text-text-primary leading-tight">
          {article.title}
        </h1>
        
        {/* Meta */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-text-muted">
          <span className="flex items-center gap-1.5">
            <Newspaper className="w-4 h-4" />
            {article.source_name}
          </span>
          {article.published_at && (
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              {new Date(article.published_at).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric'
              })}
            </span>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant={article.is_saved ? 'primary' : 'secondary'}
            size="sm"
            onClick={handleSaveToggle}
            disabled={saveMutation.isPending || unsaveMutation.isPending}
          >
            {article.is_saved ? (
              <>
                <BookmarkCheck className="w-4 h-4 mr-1.5" />
                Sauvegardé
              </>
            ) : (
              <>
                <Bookmark className="w-4 h-4 mr-1.5" />
                Sauvegarder
              </>
            )}
          </Button>
          
          <Button variant="secondary" size="sm" onClick={handleShare}>
            {copied ? (
              <>
                <Check className="w-4 h-4 mr-1.5" />
                Copié !
              </>
            ) : (
              <>
                <Share2 className="w-4 h-4 mr-1.5" />
                Partager
              </>
            )}
          </Button>
          
          <a
            href={article.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex"
          >
            <Button variant="ghost" size="sm">
              <ExternalLink className="w-4 h-4 mr-1.5" />
              Source
            </Button>
          </a>
        </div>
      </header>
      
      {/* Featured image */}
      {article.image_url && (
        <div className="aspect-video rounded-xl overflow-hidden bg-bg-elevated">
          <img
            src={article.image_url}
            alt=""
            className="w-full h-full object-cover"
          />
        </div>
      )}
      
      {/* TL;DR */}
      {article.tldr && article.tldr.length > 0 && (
        <GlassCard className="border-accent/30">
          <h2 className="text-sm font-semibold text-accent mb-3 flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center text-xs">
              ⚡
            </span>
            TL;DR
          </h2>
          <ul className="space-y-2">
            {article.tldr.map((point, i) => (
              <li key={i} className="flex gap-2 text-sm text-text-secondary">
                <span className="text-accent font-bold">•</span>
                {point}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}
      
      {/* Content */}
      {article.content_md && (
        <article className="prose prose-invert prose-sm sm:prose-base max-w-none">
          <div 
            className="text-text-secondary leading-relaxed space-y-4"
            style={{ whiteSpace: 'pre-wrap' }}
          >
            {article.content_md}
          </div>
        </article>
      )}
      
      {/* Source attribution */}
      <GlassCard className="text-sm text-text-muted">
        <p>
          Source : <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">{article.source_name}</a>
          {article.published_at && (
            <> — Publié le {new Date(article.published_at).toLocaleDateString('fr-FR')}</>
          )}
        </p>
        <p className="mt-2 text-xs">
          Contenu reformulé par MarketGPS. Pour l&apos;article original, consultez la source.
        </p>
      </GlassCard>
    </div>
  );
}
