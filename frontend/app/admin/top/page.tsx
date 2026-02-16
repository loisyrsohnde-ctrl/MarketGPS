'use client';

import { useState, useEffect, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/config';
import {
  Star,
  RefreshCw,
  TrendingUp,
  Flame,
  ExternalLink,
  AlertTriangle,
  Medal,
  Globe,
  BarChart3,
  Loader2,
} from 'lucide-react';

const API_BASE = getApiBaseUrl();

interface TopArticle {
  id: string;
  title: string;
  source_name: string;
  country: string;
  language: string;
  total_interactions: number;
  published_at: string;
  scraped_at: string;
  source_url: string;
  is_breaking_news: boolean;
  importance_level: string;
  viral_score_v2?: number;
  viral_reasons_v2?: string;
  trend_velocity_ratio?: number;
  attention_proxy_score?: number;
  cluster_label?: string;
  engagement_score?: number;
}

type ViewMode = 'top10' | 'top20' | 'top50' | 'trending' | 'breaking';

export default function TopArticlesPage() {
  const [articles, setArticles] = useState<TopArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('top20');
  const [countryFilter, setCountryFilter] = useState('');
  const [rescoring, setRescoring] = useState(false);

  const limitForMode: Record<ViewMode, number> = {
    top10: 10,
    top20: 20,
    top50: 50,
    trending: 40,
    breaking: 30,
  };

  const fetchArticles = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';

      let url: string;
      const params = new URLSearchParams();

      if (viewMode === 'trending') {
        // High-interaction articles (trending)
        params.append('limit', '40');
        params.append('min_interactions', '100');
        if (countryFilter) params.append('country', countryFilter);
        url = `${API_BASE}/news-admin/articles?${params.toString()}`;
      } else if (viewMode === 'breaking') {
        // Breaking news — articles with highest interactions (most visible)
        params.append('limit', '30');
        params.append('min_interactions', '50');
        params.append('trending', 'true');
        if (countryFilter) params.append('country', countryFilter);
        url = `${API_BASE}/news-admin/articles?${params.toString()}`;
      } else {
        // Top 10/20/50 — use regular articles sorted by interactions
        // Try V2 scored endpoint first, fallback to regular articles
        params.append('limit', limitForMode[viewMode].toString());
        if (countryFilter) params.append('country', countryFilter);
        url = `${API_BASE}/news-admin/articles?${params.toString()}`;
      }

      const response = await fetch(url, {
        headers: { 'X-Admin-Key': adminKey },
      });

      if (!response.ok) {
        throw new Error(`Erreur: ${response.status}`);
      }

      const data = await response.json();
      const rawArticles = data.articles || [];
      setArticles(rawArticles);
      setTotal(data.total || rawArticles.length);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [viewMode, countryFilter]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  const handleRescore = async () => {
    try {
      setRescoring(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(
        `${API_BASE}/news-admin/score-v2?top_k=60&days_back=3&min_score=10`,
        {
          method: 'POST',
          headers: { 'X-Admin-Key': adminKey, 'Content-Type': 'application/json' },
        }
      );
      if (response.ok) {
        await fetchArticles();
      }
    } catch (err) {
      console.error('Rescore error:', err);
    } finally {
      setRescoring(false);
    }
  };

  const formatInteractions = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    const now = new Date();
    const diffH = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60));
    if (diffH < 1) return 'Maintenant';
    if (diffH < 24) return `${diffH}h`;
    if (diffH < 48) return 'Hier';
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  const getRankBadge = (idx: number) => {
    if (idx === 0) return <Medal className="h-5 w-5 text-yellow-500" />;
    if (idx === 1) return <Medal className="h-5 w-5 text-gray-400" />;
    if (idx === 2) return <Medal className="h-5 w-5 text-amber-700" />;
    return <span className="text-sm font-bold text-gray-500">#{idx + 1}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="rounded-xl bg-gradient-to-br from-yellow-400 to-orange-500 p-3">
          <Star className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Top Articles
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Classement des articles par viralité, tendance et importance
          </p>
        </div>

        <div className="ml-auto flex gap-2">
          <button
            onClick={handleRescore}
            disabled={rescoring}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {rescoring ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
            {rescoring ? 'Scoring...' : 'Rescorer'}
          </button>
          <button
            onClick={fetchArticles}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            <RefreshCw className="h-4 w-4" />
            Actualiser
          </button>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="flex flex-wrap gap-2">
        {([
          { value: 'top10', label: 'Top 10', icon: Star },
          { value: 'top20', label: 'Top 20', icon: Star },
          { value: 'top50', label: 'Top 50', icon: Star },
          { value: 'trending', label: 'Trending', icon: TrendingUp },
          { value: 'breaking', label: 'Breaking News', icon: AlertTriangle },
        ] as const).map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setViewMode(value)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
              viewMode === value
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}

        {/* Country Filter */}
        <div className="ml-auto flex items-center gap-2">
          <Globe className="h-4 w-4 text-gray-500" />
          <select
            value={countryFilter}
            onChange={(e) => setCountryFilter(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          >
            <option value="">Tous les pays</option>
            <option value="FR">France</option>
            <option value="DE">Allemagne</option>
            <option value="US">États-Unis</option>
            <option value="UK">Royaume-Uni</option>
            <option value="MA">Maroc</option>
            <option value="SN">Sénégal</option>
            <option value="CI">Côte d'Ivoire</option>
          </select>
        </div>
      </div>

      {/* Stats Bar */}
      {!loading && articles.length > 0 && (
        <div className="flex items-center gap-6 rounded-lg border border-gray-200 bg-gray-50 px-6 py-3 dark:border-gray-800 dark:bg-gray-900/50">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            <strong className="text-gray-900 dark:text-white">{articles.length}</strong> articles
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Total interactions: <strong className="text-gray-900 dark:text-white">
              {formatInteractions(articles.reduce((s, a) => s + (a.total_interactions || 0), 0))}
            </strong>
          </span>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Breaking: <strong className="text-red-600 dark:text-red-400">
              {articles.filter(a => a.is_breaking_news).length}
            </strong>
          </span>
          {articles[0]?.viral_score_v2 != null && (
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Score max: <strong className="text-emerald-600 dark:text-emerald-400">
                {articles[0].viral_score_v2.toFixed(1)}
              </strong>
            </span>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Articles */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(10)].map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800" />
          ))}
        </div>
      ) : articles.length > 0 ? (
        <div className="space-y-2">
          {articles.map((article, idx) => (
            <div
              key={article.id}
              className={`flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-gray-50 dark:hover:bg-gray-900/50 ${
                article.is_breaking_news
                  ? 'border-red-200 bg-red-50/30 dark:border-red-900/30 dark:bg-red-900/10'
                  : idx < 3
                    ? 'border-yellow-200 bg-yellow-50/20 dark:border-yellow-900/30 dark:bg-yellow-900/5'
                    : 'border-gray-200 dark:border-gray-800'
              }`}
            >
              {/* Rank */}
              <div className="flex w-10 flex-shrink-0 items-center justify-center">
                {getRankBadge(idx)}
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <div className="flex items-start gap-2">
                  {article.is_breaking_news && (
                    <span className="mt-0.5 flex items-center gap-1 whitespace-nowrap rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      <AlertTriangle className="h-3 w-3" />
                      URGENT
                    </span>
                  )}
                  <h3 className="text-sm font-medium text-gray-900 dark:text-white line-clamp-1">
                    {article.title}
                  </h3>
                </div>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  <span>{article.source_name}</span>
                  <span>{article.country || '—'}</span>
                  <span>{formatDate(article.published_at || article.scraped_at)}</span>
                  {article.cluster_label && (
                    <span className="rounded bg-purple-100 px-1.5 py-0.5 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                      {article.cluster_label}
                    </span>
                  )}
                </div>
              </div>

              {/* Scores */}
              <div className="flex items-center gap-4 flex-shrink-0">
                {article.viral_score_v2 != null && (
                  <div className="text-center">
                    <p className={`text-lg font-bold ${
                      article.viral_score_v2 >= 70 ? 'text-red-600' :
                      article.viral_score_v2 >= 40 ? 'text-orange-600' :
                      'text-blue-600'
                    }`}>
                      {article.viral_score_v2.toFixed(0)}
                    </p>
                    <p className="text-[10px] text-gray-500">Score V2</p>
                  </div>
                )}

                <div className="text-center">
                  <p className={`text-lg font-bold ${
                    article.total_interactions >= 1000 ? 'text-red-600' :
                    article.total_interactions >= 100 ? 'text-orange-600' :
                    'text-gray-600'
                  }`}>
                    {formatInteractions(article.total_interactions || 0)}
                  </p>
                  <p className="text-[10px] text-gray-500">Interactions</p>
                </div>

                {article.source_url && (
                  <a
                    href={article.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg p-2 text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/20"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-16 text-center dark:border-gray-800">
          <Star className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Aucun article dans le classement
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Lancez le scoring V2 pour classer les articles
          </p>
          <button
            onClick={handleRescore}
            disabled={rescoring}
            className="mt-4 rounded-lg bg-emerald-600 px-6 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {rescoring ? 'Scoring...' : 'Lancer le scoring'}
          </button>
        </div>
      )}
    </div>
  );
}
