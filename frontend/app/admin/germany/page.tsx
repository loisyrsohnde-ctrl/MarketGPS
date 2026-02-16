'use client';

import { useState, useEffect, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/config';
import {
  Globe2,
  RefreshCw,
  AlertTriangle,
  TrendingUp,
  Newspaper,
  ExternalLink,
  Flame,
  Clock,
  BarChart3,
  Filter,
} from 'lucide-react';

const API_BASE = getApiBaseUrl();

interface GermanArticle {
  id: string;
  title: string;
  source_name: string;
  country: string;
  language: string;
  total_interactions: number;
  published_at: string;
  scraped_at: string;
  source_url: string;
  image_url?: string;
  is_breaking_news: boolean;
  importance_level: string;
  status: string;
  category?: string;
  excerpt?: string;
  sentiment?: string;
}

type SortMode = 'interactions' | 'freshness' | 'breaking';

export default function GermanyPage() {
  const [articles, setArticles] = useState<GermanArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortMode>('interactions');
  const [minInteractions, setMinInteractions] = useState(0);
  const [breakingOnly, setBreakingOnly] = useState(false);
  const [page, setPage] = useState(1);
  const limit = 30;

  const fetchArticles = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const params = new URLSearchParams();
      params.append('country', 'DE');
      params.append('limit', limit.toString());
      params.append('offset', ((page - 1) * limit).toString());
      params.append('sort_by', sortBy);

      if (minInteractions > 0) {
        params.append('min_interactions', minInteractions.toString());
      }
      if (breakingOnly) {
        params.append('is_breaking', 'true');
      }

      const response = await fetch(`${API_BASE}/news-admin/articles?${params.toString()}`, {
        headers: { 'X-Admin-Key': adminKey },
      });

      if (!response.ok) {
        throw new Error(`Erreur: ${response.status}`);
      }

      const data = await response.json();
      setArticles(data.articles || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de chargement');
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [sortBy, minInteractions, breakingOnly, page]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  const totalPages = Math.ceil(total / limit);

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffH = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffH < 1) return 'Il y a quelques minutes';
    if (diffH < 24) return `Il y a ${diffH}h`;
    if (diffH < 48) return 'Hier';
    return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  const formatInteractions = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return n.toString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="rounded-xl bg-gradient-to-br from-yellow-400 to-red-500 p-3">
          <Globe2 className="h-8 w-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Allemagne
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Actualités allemandes — Sources: Handelsblatt, Spiegel, Tagesschau, DW
          </p>
        </div>

        <button
          onClick={fetchArticles}
          className="ml-auto flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
        >
          <RefreshCw className="h-4 w-4" />
          Actualiser
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/20">
              <Newspaper className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Articles</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{total}</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Breaking News</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {articles.filter(a => a.is_breaking_news).length}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-orange-100 p-2 dark:bg-orange-900/20">
              <TrendingUp className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Trending (100+)</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {articles.filter(a => a.total_interactions >= 100).length}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-green-100 p-2 dark:bg-green-900/20">
              <BarChart3 className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Moy. Interactions</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {articles.length > 0
                  ? formatInteractions(
                      Math.round(articles.reduce((s, a) => s + a.total_interactions, 0) / articles.length)
                    )
                  : '0'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Tri :</span>
          </div>

          {([
            { value: 'interactions', label: 'Plus virales', icon: Flame },
            { value: 'freshness', label: 'Plus récentes', icon: Clock },
            { value: 'breaking', label: 'Breaking News', icon: AlertTriangle },
          ] as const).map(({ value, label, icon: Icon }) => (
            <button
              key={value}
              onClick={() => { setSortBy(value); setPage(1); }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                sortBy === value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {label}
            </button>
          ))}

          <div className="ml-auto flex items-center gap-3">
            <select
              value={minInteractions}
              onChange={(e) => { setMinInteractions(Number(e.target.value)); setPage(1); }}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value={0}>Toutes interactions</option>
              <option value={50}>50+ interactions</option>
              <option value={100}>100+ interactions</option>
              <option value={500}>500+ interactions</option>
              <option value={1000}>1000+ interactions</option>
            </select>

            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={breakingOnly}
                onChange={(e) => { setBreakingOnly(e.target.checked); setPage(1); }}
                className="rounded border-gray-300"
              />
              Breaking uniquement
            </label>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Articles Table */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800" />
          ))}
        </div>
      ) : articles.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-800">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">#</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Article</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Source</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Interactions</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Date</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Statut</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Lien</th>
              </tr>
            </thead>
            <tbody>
              {articles.map((article, idx) => (
                <tr
                  key={article.id}
                  className={`border-t border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50 ${
                    article.is_breaking_news ? 'bg-red-50/50 dark:bg-red-900/10' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-sm font-mono text-gray-500">
                    {(page - 1) * limit + idx + 1}
                  </td>
                  <td className="max-w-md px-4 py-3">
                    <div className="flex items-start gap-2">
                      {article.is_breaking_news && (
                        <span className="mt-0.5 flex items-center gap-1 whitespace-nowrap rounded bg-red-100 px-1.5 py-0.5 text-[10px] font-bold uppercase text-red-700 dark:bg-red-900/30 dark:text-red-400">
                          <AlertTriangle className="h-3 w-3" />
                          URGENT
                        </span>
                      )}
                      <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">
                        {article.title}
                      </p>
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {article.source_name}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right">
                    <span className={`text-sm font-bold ${
                      article.total_interactions >= 1000
                        ? 'text-red-600 dark:text-red-400'
                        : article.total_interactions >= 100
                          ? 'text-orange-600 dark:text-orange-400'
                          : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {formatInteractions(article.total_interactions)}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(article.published_at || article.scraped_at)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${
                      article.status === 'published'
                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                        : article.status === 'rejected'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                    }`}>
                      {article.status || 'pending'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {article.source_url && (
                      <a
                        href={article.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
          <Globe2 className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Aucun article allemand trouvé
          </p>
          <p className="mt-1 text-sm text-gray-500">
            Vérifiez que les sources DE sont activées dans le pipeline
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300"
          >
            Précédent
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Page {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
}
