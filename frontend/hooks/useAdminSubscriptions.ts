import { useEffect, useState, useCallback } from 'react';
import { Subscription } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

interface UseAdminSubscriptionsParams {
  status?: string;
  limit?: number;
}

export function useAdminSubscriptions(params?: UseAdminSubscriptionsParams) {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSubscriptions = useCallback(async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (params?.status && params.status !== 'all') {
        queryParams.append('status', params.status);
      }
      queryParams.append('limit', String(params?.limit || 100));

      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(
        `${API_BASE}/admin/subscriptions?${queryParams.toString()}`,
        {
          headers: { 'X-Admin-Key': adminKey },
        }
      );

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des abonnements');
      }

      const data = await response.json();
      setSubscriptions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setSubscriptions([]);
    } finally {
      setLoading(false);
    }
  }, [params?.status, params?.limit]);

  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  return { subscriptions, loading, error, refetch: fetchSubscriptions };
}
