import { useEffect, useState, useCallback } from 'react';
import { Feedback } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

interface UseAdminFeedbacksParams {
  status?: string;
  type?: string;
  limit?: number;
}

export function useAdminFeedbacks(params?: UseAdminFeedbacksParams) {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFeedbacks = useCallback(async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (params?.status && params.status !== 'all') {
        queryParams.append('status', params.status);
      }
      if (params?.type && params.type !== 'all') {
        queryParams.append('type', params.type);
      }
      queryParams.append('limit', String(params?.limit || 50));

      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(
        `${API_BASE}/admin/feedbacks?${queryParams.toString()}`,
        {
          headers: { 'X-Admin-Key': adminKey },
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des feedbacks');
      }

      const data = await response.json();
      setFeedbacks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setFeedbacks([]);
    } finally {
      setLoading(false);
    }
  }, [params?.status, params?.type, params?.limit]);

  useEffect(() => {
    fetchFeedbacks();
  }, [fetchFeedbacks]);

  return { feedbacks, loading, error, refetch: fetchFeedbacks };
}
