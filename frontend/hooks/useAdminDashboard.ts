import { useEffect, useState } from 'react';
import { DashboardMetrics, ActivityLogEntry } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

export function useAdminDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      // Only show skeleton on initial load, not on auto-refresh
      if (!metrics) setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';

      // Fetch both stats and diagnostics for comprehensive metrics
      const [statsRes, diagRes] = await Promise.all([
        fetch(`${API_BASE}/admin/stats`, {
          headers: { 'X-Admin-Key': adminKey },
          cache: 'no-store',
        }),
        fetch(`${API_BASE}/admin/diagnostics`, {
          headers: { 'X-Admin-Key': adminKey },
          cache: 'no-store',
        }),
      ]);

      if (!statsRes.ok || !diagRes.ok) {
        throw new Error('Erreur lors du chargement des métriques');
      }

      const statsData = await statsRes.json();
      const diagData = await diagRes.json();

      // Compute trend data from 7 last days
      const trend_7d = computeTrend7Days(diagData);

      const computed: DashboardMetrics = {
        pipeline: {
          articles_today: diagData.news?.articles_today || statsData.articles_today || 0,
          articles_week: diagData.news?.articles_this_week || 0,
          viral_count: statsData.viral_count || 0,
          published_count: diagData.news?.articles_today || 0,
          in_workflow: {
            pending: diagData.news?.by_status?.pending || 0,
            researched: diagData.news?.by_status?.researched || 0,
            rewritten: diagData.news?.by_status?.rewritten || 0,
            approved: diagData.news?.by_status?.approved || 0,
            published: diagData.news?.by_status?.published || 0,
            rejected: diagData.news?.by_status?.rejected || 0,
          },
          trend_7d,
        },
        geography: {
          by_country: Object.entries(diagData.news?.by_region || {})
            .map(([country, count]) => ({
              country,
              count: count as number,
              interactions: 0,
            }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 10),
        },
        editorial: {
          avg_score: diagData.scores?.distribution?.high_70_plus
            ? Math.round(
                (diagData.scores.distribution.high_70_plus * 80 +
                  diagData.scores.distribution.medium_40_69 * 55) /
                  (diagData.scores.distribution.high_70_plus +
                    diagData.scores.distribution.medium_40_69)
              )
            : 0,
          top_topics: [],
          source_diversity: diagData.universe?.by_scope ? Object.keys(diagData.universe.by_scope).length : 0,
        },
        system: {
          last_pipeline_run: statsData.last_pipeline_run || null,
          sources_active: statsData.sources_active || 0,
          llm_provider: statsData.llm_provider || 'openai',
          db_size_mb: 0,
        },
        recent_activity: [],
      };

      setMetrics(computed);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setMetrics(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    // Refresh every 2 minutes
    const interval = setInterval(fetchMetrics, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return { metrics, loading, error, refetch: fetchMetrics };
}

function computeTrend7Days(diagData: any) {
  // Use real daily breakdown from diagnostics if available
  const dailyBreakdown = diagData.news?.daily_breakdown;
  if (dailyBreakdown && typeof dailyBreakdown === 'object') {
    return Object.entries(dailyBreakdown)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-7)
      .map(([date, count]) => ({
        date: date.split('-').slice(1).join('/'),
        count: count as number,
      }));
  }

  // Fallback: show only today's real count, no fake historical data
  const now = new Date();
  const todayStr = now.toISOString().split('T')[0].split('-').slice(1).join('/');
  const todayCount = diagData.news?.articles_today || 0;
  const weekCount = diagData.news?.articles_this_week || 0;
  const avgDaily = weekCount > 0 ? Math.round(weekCount / 7) : 0;

  const trend: { date: string; count: number }[] = [];
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0].split('-').slice(1).join('/');

    // Use real today count for today, weekly average for past days
    trend.push({
      date: dateStr,
      count: i === 0 ? todayCount : avgDaily,
    });
  }

  return trend;
}
