import { useEffect, useState, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

interface QuotaRecord {
  user_id: string;
  provider: string;
  usage_count: number;
  limit: number;
  limit_disabled: boolean;
  last_used: string | null;
}

interface QuotasResponse {
  quotas: QuotaRecord[];
  count: number;
}

interface ExhaustedResponse {
  exhausted_users: QuotaRecord[];
  count: number;
}

function getAdminKey(): string {
  return localStorage.getItem('adminKey') || '';
}

export function useAdminQuotas(limit = 100, offset = 0) {
  const [quotas, setQuotas] = useState<QuotaRecord[]>([]);
  const [exhausted, setExhausted] = useState<QuotaRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQuotas = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = getAdminKey();
      const headers = { 'X-Admin-Key': adminKey };

      const [quotasRes, exhaustedRes] = await Promise.all([
        fetch(`${API_BASE}/admin/ai-quotas?limit=${limit}&offset=${offset}`, { headers }),
        fetch(`${API_BASE}/admin/ai-quotas/exhausted`, { headers }),
      ]);

      if (!quotasRes.ok || !exhaustedRes.ok) {
        throw new Error('Erreur lors du chargement des quotas AI');
      }

      const quotasData: QuotasResponse = await quotasRes.json();
      const exhaustedData: ExhaustedResponse = await exhaustedRes.json();

      setQuotas(quotasData.quotas || []);
      setExhausted(exhaustedData.exhausted_users || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => {
    fetchQuotas();
  }, [fetchQuotas]);

  const updateQuota = async (
    userId: string,
    provider: string,
    action: 'disable_limit' | 'enable_limit' | 'reset' | 'set_limit',
    newLimit?: number
  ) => {
    try {
      const adminKey = getAdminKey();
      const response = await fetch(`${API_BASE}/admin/ai-quotas/update`, {
        method: 'POST',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          provider,
          action,
          new_limit: newLimit,
        }),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la mise à jour du quota');
      }

      // Refresh data
      await fetchQuotas();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de mise à jour');
      return false;
    }
  };

  return { quotas, exhausted, loading, error, refetch: fetchQuotas, updateQuota };
}
