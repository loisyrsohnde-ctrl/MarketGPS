import { useEffect, useState } from 'react';
import { ViralArticle } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

function calculateViralityScore(interactions: number): number {
  if (interactions >= 1000) return 5;
  if (interactions >= 500) return 4;
  if (interactions >= 250) return 3;
  if (interactions >= 100) return 2;
  if (interactions > 0) return 1;
  return 0;
}

interface UseViralNewsParams {
  region?: string;
  language?: string;
  minViralityScore?: number;
  page?: number;
  limit?: number;
}

interface UseViralNewsResult {
  articles: ViralArticle[];
  total: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  publishArticle: (articleId: string) => Promise<boolean>;
  rejectArticle: (articleId: string, reason?: string) => Promise<boolean>;
}

export function useViralNews(params?: UseViralNewsParams): UseViralNewsResult {
  const [articles, setArticles] = useState<ViralArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const queryParams = new URLSearchParams();

      // Map frontend parameters to backend parameters
      if (params?.region) queryParams.append('source', params.region);
      if (params?.language) queryParams.append('language', params.language);
      if (params?.minViralityScore) {
        queryParams.append('min_interactions', params.minViralityScore.toString());
      }
      if (params?.page) {
        const page = params.page;
        const limit = params?.limit || 20;
        const offset = (page - 1) * limit;
        queryParams.append('offset', offset.toString());
        queryParams.append('limit', limit.toString());
      } else if (params?.limit) {
        queryParams.append('limit', params.limit.toString());
      }

      // Call backend directly
      const url = `${API_BASE}/news-admin/articles?${queryParams.toString()}`;

      const response = await fetch(url, {
        headers: { 'X-Admin-Key': adminKey },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch viral news: ${response.status}`);
      }

      const data = await response.json();

      // Transform backend response to frontend format
      const transformedArticles = (data.articles || []).map((article: any) => ({
        id: article.id,
        title: article.title,
        source: article.source_name || article.source,
        region: article.country || 'Unknown',
        language: article.language || 'unknown',
        interactions: article.total_interactions || 0,
        viralityScore: calculateViralityScore(article.total_interactions || 0),
        publishedAt: article.published_at || article.scraped_at || new Date().toISOString(),
        hasScript: !!article.has_script,
        url: article.source_url || article.url,
        thumbnail: article.image_url || article.thumbnail_url,
        status: article.status,
      }));

      setArticles(transformedArticles);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      console.error('Error fetching viral news:', errorMessage);
      setError(errorMessage);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [params?.region, params?.language, params?.minViralityScore, params?.page, params?.limit]);

  const publishArticle = async (articleId: string): Promise<boolean> => {
    try {
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/news-admin/publish`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_id: articleId }),
      });
      if (!response.ok) throw new Error('Erreur publication');
      await fetchArticles();
      return true;
    } catch {
      return false;
    }
  };

  const rejectArticle = async (articleId: string, reason?: string): Promise<boolean> => {
    try {
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/news-admin/reject`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ article_id: articleId, reason: reason || '' }),
      });
      if (!response.ok) throw new Error('Erreur rejet');
      await fetchArticles();
      return true;
    } catch {
      return false;
    }
  };

  return {
    articles,
    total,
    loading,
    error,
    refetch: fetchArticles,
    publishArticle,
    rejectArticle,
  };
}
