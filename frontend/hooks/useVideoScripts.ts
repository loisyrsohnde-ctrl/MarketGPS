import { useCallback, useEffect, useState } from 'react';
import { VideoScript } from '@/types/admin';

interface UseVideoScriptsParams {
  status?: VideoScript['status'];
  page?: number;
  limit?: number;
}

interface UseVideoScriptsResult {
  scripts: VideoScript[];
  total: number;
  loading: boolean;
  error: string | null;
  createScript: (articleId: string, data: Partial<VideoScript>) => Promise<VideoScript>;
  updateScript: (id: string, data: Partial<VideoScript>) => Promise<VideoScript>;
  deleteScript: (id: string) => Promise<void>;
  refetch: () => Promise<void>;
}

export function useVideoScripts(params?: UseVideoScriptsParams): UseVideoScriptsResult {
  const [scripts, setScripts] = useState<VideoScript[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchScripts = useCallback(async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      if (params?.status) queryParams.append('status', params.status);
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());

      const url = `/api/admin/scripts?${queryParams.toString()}`;
      console.log('Fetching scripts from:', url);

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to fetch scripts: ${response.status}`);
      }

      const data = await response.json();
      console.log('Scripts response:', data);

      setScripts(data.scripts || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      console.error('Error fetching scripts:', errorMessage);
      setError(errorMessage);
      setScripts([]);
    } finally {
      setLoading(false);
    }
  }, [params?.status, params?.page, params?.limit]);

  useEffect(() => {
    fetchScripts();
  }, [fetchScripts]);

  const createScript = useCallback(
    async (articleId: string, data: Partial<VideoScript>): Promise<VideoScript> => {
      const response = await fetch('/api/admin/scripts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articleId, ...data }),
      });

      if (!response.ok) {
        throw new Error('Failed to create script');
      }

      const script = await response.json();
      setScripts((prev) => [script, ...prev]);
      return script;
    },
    []
  );

  const updateScript = useCallback(
    async (id: string, data: Partial<VideoScript>): Promise<VideoScript> => {
      const response = await fetch(`/api/admin/scripts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update script');
      }

      const script = await response.json();
      setScripts((prev) =>
        prev.map((s) => (s.id === id ? script : s))
      );
      return script;
    },
    []
  );

  const deleteScript = useCallback(
    async (id: string): Promise<void> => {
      const response = await fetch(`/api/admin/scripts/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete script');
      }

      setScripts((prev) => prev.filter((s) => s.id !== id));
    },
    []
  );

  return {
    scripts,
    total,
    loading,
    error,
    createScript,
    updateScript,
    deleteScript,
    refetch: fetchScripts,
  };
}
