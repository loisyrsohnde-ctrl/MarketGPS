import { useEffect, useState, useCallback } from 'react';
import { DiagnosticsData, PipelineStatus } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

function getAdminKey(): string {
  return localStorage.getItem('adminKey') || '';
}

export function useAdminDiagnostics() {
  const [diagnostics, setDiagnostics] = useState<DiagnosticsData | null>(null);
  const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = getAdminKey();
      const headers = { 'X-Admin-Key': adminKey };

      const [diagRes, pipeRes] = await Promise.all([
        fetch(`${API_BASE}/admin/diagnostics`, { headers }),
        fetch(`${API_BASE}/admin/news-pipeline-status`, { headers }),
      ]);

      if (!diagRes.ok) {
        throw new Error('Erreur lors du chargement des diagnostics');
      }

      const diagData = await diagRes.json();
      setDiagnostics(diagData);

      if (pipeRes.ok) {
        const pipeData = await pipeRes.json();
        setPipeline(pipeData);
      }

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const runPipelineAction = async (
    action: 'run' | 'ingest' | 'publish' | 'cleanup' | 'score-v2' | 'update-interactions'
  ) => {
    try {
      const adminKey = getAdminKey();
      const headers: Record<string, string> = {
        'X-Admin-Key': adminKey,
        'Content-Type': 'application/json',
      };

      let url = '';
      switch (action) {
        case 'run':
          url = `${API_BASE}/news-admin/pipeline/run?sync=true`;
          break;
        case 'ingest':
          url = `${API_BASE}/news-admin/pipeline/ingest`;
          break;
        case 'publish':
          url = `${API_BASE}/news-admin/pipeline/publish`;
          break;
        case 'cleanup':
          url = `${API_BASE}/news-admin/cleanup?keep_days=5&keep_top=50&dry_run=false`;
          break;
        case 'score-v2':
          url = `${API_BASE}/news-admin/score-v2?top_k=60&days_back=3&min_score=10`;
          break;
        case 'update-interactions':
          url = `${API_BASE}/news-admin/update-interactions?sync=true&limit=200`;
          break;
      }

      const response = await fetch(url, { method: 'POST', headers });

      if (!response.ok) {
        throw new Error(`Erreur pipeline: ${action}`);
      }

      const result = await response.json();
      // Refresh diagnostics after action
      await fetchAll();
      return result;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Erreur pipeline');
    }
  };

  return { diagnostics, pipeline, loading, error, refetch: fetchAll, runPipelineAction };
}
