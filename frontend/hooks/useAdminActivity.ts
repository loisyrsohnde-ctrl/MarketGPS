import { useEffect, useState, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

interface ActivityLogEntry {
  id: number;
  admin_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details?: string;
  changes_json?: string;
  created_at: string;
}

interface ActivityLogResponse {
  entries: ActivityLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

interface UseAdminActivityParams {
  limit?: number;
  offset?: number;
  action?: string;
  resourceType?: string;
  dateFilter?: string;
}

export function useAdminActivity(params?: UseAdminActivityParams) {
  const [entries, setEntries] = useState<ActivityLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const limit = params?.limit || 20;
  const offset = params?.offset || 0;

  const fetchActivityLog = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';

      if (!adminKey) {
        setError('Clé d\'administration non trouvée');
        setLoading(false);
        return;
      }

      const queryParams = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });

      if (params?.action && params.action !== 'all') {
        queryParams.append('action', params.action);
      }

      if (params?.resourceType && params.resourceType !== 'all') {
        queryParams.append('resource_type', params.resourceType);
      }

      const response = await fetch(
        `${API_BASE}/api/admin/activity?${queryParams}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey,
          },
          cache: 'no-store',
        }
      );

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data: ActivityLogResponse = await response.json();

      // Client-side date filtering
      let filteredEntries = data.entries;
      if (params?.dateFilter && params.dateFilter !== 'all') {
        const now = new Date();
        let cutoffDate = new Date();

        if (params.dateFilter === 'today') {
          cutoffDate.setHours(0, 0, 0, 0);
        } else if (params.dateFilter === '7days') {
          cutoffDate.setDate(cutoffDate.getDate() - 7);
        } else if (params.dateFilter === '30days') {
          cutoffDate.setDate(cutoffDate.getDate() - 30);
        }

        filteredEntries = filteredEntries.filter(
          (entry) => new Date(entry.created_at) >= cutoffDate
        );
      }

      setEntries(filteredEntries);
      setTotal(data.total);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Erreur lors du chargement du journal'
      );
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [limit, offset, params?.action, params?.resourceType, params?.dateFilter]);

  useEffect(() => {
    fetchActivityLog();
  }, [fetchActivityLog]);

  return { entries, total, loading, error, refetch: fetchActivityLog };
}
