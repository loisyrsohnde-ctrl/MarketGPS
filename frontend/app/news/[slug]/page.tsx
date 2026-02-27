'use client';

import { useState, useEffect } from 'react';
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
import { track } from '@/lib/analytics';
import { shareNewsOnWhatsApp } from '@/lib/share';
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
// Helper Components
// ═══════════════════════════════════════════════════════════════════════════

function SimpleMarkdown({ text }: { text: string }) {
  if (!text) return null;
  
  // Split by newlines first to handle paragraphs if needed, 
  // but here we are inside a pre-wrap div so we just need to handle bold
  
  // Split by ** markers
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
          return <strong key={i} className="text-text-primary font-bold">{part.slice(2, -2)}</strong>;
        }
        return part;
      })}
    </>
  );
}

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
  
  // Track article read in PostHog
  useEffect(() => {
    if (article) {
      track.newsRead(article.slug, article.country ?? undefined);
    }
  }, [article]);

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
                year: 'numeric',
                timeZone: 'UTC'
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
          
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              shareNewsOnWhatsApp(article.title, article.slug);
              track.shareAction('whatsapp', 'news');
            }}
            className="text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
          >
            <svg className="w-4 h-4 mr-1.5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
            </svg>
            WhatsApp
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
                <SimpleMarkdown text={point} />
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
            <SimpleMarkdown text={article.content_md} />
          </div>
        </article>
      )}
      
      {/* Source attribution */}
      <GlassCard className="text-sm text-text-muted">
        <p>
          Source : <a href={article.source_url} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">{article.source_name}</a>
          {article.published_at && (
            <> — Publié le {new Date(article.published_at).toLocaleDateString('fr-FR', { timeZone: 'UTC' })}</>
          )}
        </p>
        <p className="mt-2 text-xs font-medium text-accent/80">
          ✨ Analyse propulsée par MarketGPS, votre copilote pour l&apos;investissement intelligent en Afrique.
        </p>
      </GlassCard>
    </div>
  );
}
