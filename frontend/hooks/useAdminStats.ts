import { useEffect, useState } from 'react';
import { AdminStats } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

export function useAdminStats() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStats = async () => {
    try {
      // Only show skeleton on initial load, not on auto-refresh
      if (!stats) setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/admin/stats`, {
        headers: { 'X-Admin-Key': adminKey },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des statistiques');
      }

      const data = await response.json();

      // Map backend response to frontend AdminStats type
      setStats({
        users: {
          total: data.total_users || 0,
          pro: data.pro_users || 0,
          free: data.free_users || 0,
          newToday: data.new_users_today || 0,
          newThisWeek: data.new_users_week || 0,
        },
        news: {
          scrapedToday: data.articles_today || 0,
          viralCount: data.viral_count || 0,
          scriptsGenerated: data.scripts_generated || 0,
        },
        system: {
          lastPipelineRun: data.last_pipeline_run || '',
          sourcesActive: data.sources_active || 0,
          llm_provider: data.llm_provider || 'OpenAI',
        },
      });
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    // Refresh stats every 2 minutes (was 5 min)
    const interval = setInterval(fetchStats, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return { stats, loading, error, refetch: fetchStats, lastUpdated };
}
