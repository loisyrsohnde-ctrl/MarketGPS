import { useEffect, useState, useCallback } from 'react';
import { EditorialArticle } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

interface UseEditorialScoresParams {
  topK?: number;
  daysBack?: number;
  minScore?: number;
}

interface UseEditorialScoresResult {
  articles: EditorialArticle[];
  total: number;
  updatedAt: string | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  rescore: (daysBack?: number, topK?: number) => Promise<{ success: boolean; message: string }>;
  rescoring: boolean;
}

export function useEditorialScores(params?: UseEditorialScoresParams): UseEditorialScoresResult {
  const [articles, setArticles] = useState<EditorialArticle[]>([]);
  const [total, setTotal] = useState(0);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rescoring, setRescoring] = useState(false);

  const fetchScores = useCallback(async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      if (params?.topK) queryParams.append('top_k', params.topK.toString());
      if (params?.daysBack) queryParams.append('days_back', params.daysBack.toString());
      if (params?.minScore !== undefined) queryParams.append('min_score', params.minScore.toString());

      const adminKey = localStorage.getItem('adminKey') || '';
      const url = `${API_BASE}/api/admin/editorial-scores?${queryParams.toString()}`;
      const response = await fetch(url, {
        headers: { 'X-Admin-Key': adminKey },
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to fetch editorial scores: ${response.status}`);
      }

      const data = await response.json();

      setArticles(data.articles || []);
      setTotal(data.total || 0);
      setUpdatedAt(data.updated_at || null);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      console.error('Error fetching editorial scores:', errorMessage);
      setError(errorMessage);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, [params?.topK, params?.daysBack, params?.minScore]);

  const rescore = useCallback(async (daysBack = 7, topK = 100) => {
    try {
      setRescoring(true);

      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/rescore-articles`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ days_back: daysBack, top_k: topK }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Rescore failed: ${response.status}`);
      }

      const data = await response.json();

      // Refetch scores after rescoring
      await fetchScores();

      return { success: true, message: data.message };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Rescore failed';
      console.error('Error rescoring articles:', errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setRescoring(false);
    }
  }, [fetchScores]);

  useEffect(() => {
    fetchScores();
  }, [fetchScores]);

  return {
    articles,
    total,
    updatedAt,
    loading,
    error,
    refetch: fetchScores,
    rescore,
    rescoring,
  };
}
