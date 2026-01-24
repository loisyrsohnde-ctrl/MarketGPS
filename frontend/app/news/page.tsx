'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  ArrowRight,
  Bookmark,
  ChevronRight,
  Loader2,
  AlertCircle,
  Newspaper,
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
  tldr: string[] | null;
  tags: string[] | null;
  country: string | null;
  image_url: string | null;
  source_name: string;
  published_at: string | null;
  category?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
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

async function fetchNewsFeed(page: number = 1): Promise<NewsFeedResponse> {
  const res = await fetch(`${API_BASE}/api/news?page=${page}&page_size=20`);
  if (!res.ok) throw new Error('Failed to fetch news');
  return res.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Ticker Data (Mock - could be fetched from API)
// ═══════════════════════════════════════════════════════════════════════════

const TICKER_ITEMS = [
  { symbol: 'BRVM', value: '+1.2%', positive: true },
  { symbol: 'NGX ASI', value: '+0.8%', positive: true },
  { symbol: 'JSE TOP40', value: '-0.3%', positive: false },
  { symbol: 'BRENT', value: '$82.4', positive: true },
  { symbol: 'GOLD', value: '-0.4%', positive: false },
  { symbol: 'EUR/XOF', value: '655.96', positive: true },
  { symbol: 'USD/NGN', value: '1,550', positive: false },
];

// ═══════════════════════════════════════════════════════════════════════════
// Category Colors
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
  if (category) {
    return CATEGORY_STYLES[category.toLowerCase()] || CATEGORY_STYLES.default;
  }
  if (tags && tags.length > 0) {
    const firstTag = tags[0].toLowerCase();
    return CATEGORY_STYLES[firstTag] || CATEGORY_STYLES.default;
  }
  return CATEGORY_STYLES.default;
}

function getCategoryLabel(category?: string | null, tags?: string[] | null): string {
  if (category) return category;
  if (tags && tags.length > 0) return tags[0];
  return 'Actualité';
}

// ═══════════════════════════════════════════════════════════════════════════
// Ticker Component
// ═══════════════════════════════════════════════════════════════════════════

function MarketTicker() {
  return (
    <div className="bg-slate-900 text-white py-2 overflow-hidden">
      <div className="flex animate-ticker">
        {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, idx) => (
          <div
            key={idx}
            className="flex items-center gap-2 px-6 whitespace-nowrap text-sm"
          >
            <span className="font-medium text-slate-300">{item.symbol}</span>
            <span className={cn(
              'font-semibold flex items-center gap-1',
              item.positive ? 'text-emerald-400' : 'text-red-400'
            )}>
              {item.positive ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Hero Article Component
// ═══════════════════════════════════════════════════════════════════════════

function HeroArticle({ article }: { article: NewsArticle }) {
  const category = getCategoryLabel(article.category, article.tags);
  
  return (
    <Link href={`/news/${article.slug}`} className="block group">
      <article className="relative h-[500px] md:h-[600px] overflow-hidden rounded-sm">
        {/* Background Image */}
        <div className="absolute inset-0">
          {article.image_url ? (
            <img
              src={article.image_url}
              alt=""
              className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-slate-800 to-slate-900" />
          )}
          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />
        </div>
        
        {/* Content */}
        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-12">
          {/* Category Badge */}
          <div className="mb-4">
            <span className={cn(
              'inline-block px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-sm',
              getCategoryStyle(article.category, article.tags)
            )}>
              {category}
            </span>
          </div>
          
          {/* Title - Serif Font */}
          <h1 className="font-serif text-3xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-4 max-w-4xl">
            {article.title}
          </h1>
          
          {/* Excerpt */}
          {article.excerpt && (
            <p className="text-lg md:text-xl text-slate-200 max-w-2xl mb-6 line-clamp-2">
              {article.excerpt}
            </p>
          )}
          
          {/* Meta */}
          <div className="flex items-center gap-4 text-sm text-slate-300">
            <span className="font-medium">{article.source_name}</span>
            <span className="w-1 h-1 rounded-full bg-slate-400" />
            {article.published_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {new Date(article.published_at).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric'
                })}
              </span>
            )}
          </div>
        </div>
      </article>
    </Link>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Secondary Article Card
// ═══════════════════════════════════════════════════════════════════════════

function SecondaryArticle({ article }: { article: NewsArticle }) {
  const category = getCategoryLabel(article.category, article.tags);
  
  return (
    <Link href={`/news/${article.slug}`} className="block group">
      <article className="h-full">
        {/* Image */}
        <div className="aspect-[16/10] overflow-hidden rounded-sm mb-4 bg-slate-200">
          {article.image_url ? (
            <img
              src={article.image_url}
              alt=""
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-slate-300 to-slate-400 flex items-center justify-center">
              <Newspaper className="w-12 h-12 text-slate-500" />
            </div>
          )}
        </div>
        
        {/* Category */}
        <span className={cn(
          'inline-block px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-sm mb-3',
          getCategoryStyle(article.category, article.tags)
        )}>
          {category}
        </span>
        
        {/* Title - Serif */}
        <h2 className="font-serif text-xl md:text-2xl font-bold text-slate-900 leading-tight mb-2 group-hover:text-blue-700 transition-colors">
          {article.title}
        </h2>
        
        {/* Excerpt */}
        {article.excerpt && (
          <p className="text-slate-600 text-sm line-clamp-2 mb-3">
            {article.excerpt}
          </p>
        )}
        
        {/* Meta */}
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>{article.source_name}</span>
          {article.published_at && (
            <>
              <span>•</span>
              <span>
                {new Date(article.published_at).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'short'
                })}
              </span>
            </>
          )}
        </div>
      </article>
    </Link>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Latest News Item (for sidebar/list)
// ═══════════════════════════════════════════════════════════════════════════

function LatestNewsItem({ article, index }: { article: NewsArticle; index: number }) {
  const category = getCategoryLabel(article.category, article.tags);
  
  return (
    <Link href={`/news/${article.slug}`} className="block group">
      <article className="flex gap-4 py-4 border-b border-slate-200 last:border-0">
        {/* Time */}
        <div className="w-16 flex-shrink-0 text-xs text-slate-400 font-mono">
          {article.published_at ? (
            new Date(article.published_at).toLocaleTimeString('fr-FR', {
              hour: '2-digit',
              minute: '2-digit'
            })
          ) : (
            `0${index + 1}:00`
          )}
        </div>
        
        {/* Category Badge */}
        <span className={cn(
          'flex-shrink-0 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-sm h-fit',
          getCategoryStyle(article.category, article.tags)
        )}>
          {category}
        </span>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-slate-800 group-hover:text-blue-700 transition-colors line-clamp-2">
            {article.title}
          </h3>
          <p className="text-xs text-slate-500 mt-1">{article.source_name}</p>
        </div>
      </article>
    </Link>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Section Header
// ═══════════════════════════════════════════════════════════════════════════

function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border-b-2 border-slate-900 pb-2 mb-8">
      <h2 className="font-serif text-2xl md:text-3xl font-bold text-slate-900">
        {title}
      </h2>
      {subtitle && (
        <p className="text-slate-500 text-sm mt-1">{subtitle}</p>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Empty State
// ═══════════════════════════════════════════════════════════════════════════

function EmptyState() {
  return (
    <div className="min-h-[400px] flex flex-col items-center justify-center text-center py-16">
      <Newspaper className="w-20 h-20 text-slate-300 mb-6" />
      <h2 className="font-serif text-3xl font-bold text-slate-800 mb-3">
        Aucune actualité disponible
      </h2>
      <p className="text-slate-500 max-w-md">
        Les actualités Fintech & Finance Afrique seront disponibles très prochainement.
      </p>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Loading State
// ═══════════════════════════════════════════════════════════════════════════

function LoadingState() {
  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="w-10 h-10 animate-spin text-slate-400 mx-auto mb-4" />
        <p className="text-slate-500">Chargement des actualités...</p>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════════════════

export default function NewsPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['news-premium'],
    queryFn: () => fetchNewsFeed(1),
    staleTime: 60000,
  });
  
  if (isLoading) return <LoadingState />;
  
  const articles = data?.data || [];
  
  if (articles.length === 0) {
    return (
      <div className="min-h-screen bg-zinc-50">
        <MarketTicker />
        <div className="max-w-7xl mx-auto px-4 py-12">
          <EmptyState />
        </div>
      </div>
    );
  }
  
  // Split articles: 1 hero, 3 secondary, rest for latest
  const heroArticle = articles[0];
  const secondaryArticles = articles.slice(1, 4);
  const latestArticles = articles.slice(4, 12);
  
  return (
    <div className="min-h-screen bg-zinc-50">
      {/* Market Ticker */}
      <MarketTicker />
      
      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Hero Section */}
        <section className="mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <HeroArticle article={heroArticle} />
          </motion.div>
        </section>
        
        {/* Secondary Articles Grid */}
        {secondaryArticles.length > 0 && (
          <section className="mb-16">
            <SectionHeader 
              title="À la Une" 
              subtitle="Les articles incontournables du moment"
            />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {secondaryArticles.map((article, idx) => (
                <motion.div
                  key={article.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: idx * 0.1 }}
                >
                  <SecondaryArticle article={article} />
                </motion.div>
              ))}
            </div>
          </section>
        )}
        
        {/* Latest News Section */}
        {latestArticles.length > 0 && (
          <section className="mb-16">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
              {/* Latest News List */}
              <div className="lg:col-span-2">
                <SectionHeader 
                  title="Dernières Dépêches" 
                  subtitle="Fil d'actualité en temps réel"
                />
                <div className="bg-white rounded-sm shadow-sm border border-slate-200 p-6">
                  {latestArticles.map((article, idx) => (
                    <LatestNewsItem 
                      key={article.id} 
                      article={article} 
                      index={idx}
                    />
                  ))}
                </div>
              </div>
              
              {/* Sidebar */}
              <div className="lg:col-span-1">
                <SectionHeader title="Régions" />
                <div className="bg-white rounded-sm shadow-sm border border-slate-200 p-6">
                  <nav className="space-y-3">
                    {[
                      { name: 'CEMAC', desc: 'Afrique Centrale', href: '/news/region/cemac' },
                      { name: 'UEMOA', desc: 'Afrique de l\'Ouest', href: '/news/region/uemoa' },
                      { name: 'Afrique du Nord', desc: 'Maghreb & Égypte', href: '/news/region/north-africa' },
                      { name: 'Afrique de l\'Est', desc: 'Kenya, Rwanda...', href: '/news/region/east-africa' },
                      { name: 'Afrique Australe', desc: 'Afrique du Sud...', href: '/news/region/southern-africa' },
                      { name: 'Nigeria', desc: 'La puissance économique', href: '/news/region/nigeria' },
                    ].map((region) => (
                      <Link
                        key={region.name}
                        href={region.href}
                        className="w-full flex items-center justify-between p-3 rounded hover:bg-slate-50 transition-colors text-left group"
                      >
                        <div>
                          <span className="font-medium text-slate-800 group-hover:text-blue-700">
                            {region.name}
                          </span>
                          <p className="text-xs text-slate-500">{region.desc}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-700" />
                      </Link>
                    ))}
                  </nav>
                </div>
                
                {/* Newsletter CTA */}
                <div className="mt-8 bg-slate-900 rounded-sm p-6 text-white">
                  <h3 className="font-serif text-xl font-bold mb-2">
                    Newsletter Premium
                  </h3>
                  <p className="text-slate-300 text-sm mb-4">
                    Recevez chaque matin le résumé des marchés africains.
                  </p>
                  <button className="w-full bg-white text-slate-900 font-semibold py-2 px-4 rounded-sm hover:bg-slate-100 transition-colors">
                    S&apos;inscrire gratuitement
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}
        
        {/* View All Link */}
        <div className="text-center pb-12">
          <Link
            href="/news/saved"
            className="inline-flex items-center gap-2 text-blue-700 font-semibold hover:text-blue-800 transition-colors"
          >
            <Bookmark className="w-4 h-4" />
            Voir mes articles sauvegardés
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </main>
    </div>
  );
}
