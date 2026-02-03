import { useEffect, useState } from 'react';
import { ViralArticle } from '@/types/admin';

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
}

export function useViralNews(params?: UseViralNewsParams): UseViralNewsResult {
  const [articles, setArticles] = useState<ViralArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticles = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      if (params?.region) queryParams.append('region', params.region);
      if (params?.language) queryParams.append('language', params.language);
      if (params?.minViralityScore) {
        queryParams.append('minViralityScore', params.minViralityScore.toString());
      }
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());

      const response = await fetch(
        `/api/admin/news?${queryParams.toString()}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch viral news');
      }

      const data = await response.json();
      setArticles(data.articles || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setArticles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [params?.region, params?.language, params?.minViralityScore, params?.page]);

  return {
    articles,
    total,
    loading,
    error,
    refetch: fetchArticles,
  };
}
