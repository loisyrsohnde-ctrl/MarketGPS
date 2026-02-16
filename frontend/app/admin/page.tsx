'use client';

import { useAdminStats } from '@/hooks/useAdminStats';
import { useAdminDashboard } from '@/hooks/useAdminDashboard';
import { StatsCard } from '@/components/admin/StatsCard';
import { DashboardChart } from '@/components/admin/DashboardChart';
import {
  Users,
  Newspaper,
  FileText,
  TrendingUp,
  Activity,
  Zap,
  Clock,
  Server,
} from 'lucide-react';

export default function AdminDashboard() {
  const { stats, loading: statsLoading, error: statsError } = useAdminStats();
  const { metrics, loading: metricsLoading, error: metricsError } = useAdminDashboard();

  const loading = statsLoading || metricsLoading;
  const error = statsError || metricsError;

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Tableau de Bord
        </h1>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-32 rounded-lg bg-gray-200 dark:bg-gray-800 animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
        <p className="text-sm text-red-800 dark:text-red-300">
          Erreur lors du chargement du tableau de bord: {error}
        </p>
      </div>
    );
  }

  // Calculate week-over-week changes
  const usersTrend = stats && stats.users.total > 0
    ? Math.round((stats.users.newThisWeek / stats.users.total) * 100)
    : 0;

  const articlesTrend = metrics?.pipeline.articles_week ?
    Math.round(((metrics.pipeline.articles_today / Math.max(metrics.pipeline.articles_week / 7, 1)) - 1) * 100)
    : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Tableau de Bord
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Vue d'ensemble de votre système MarketGPS
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Utilisateurs */}
        <StatsCard
          title="Utilisateurs Total"
          value={stats?.users.total || 0}
          change={usersTrend}
          icon={<Users className="h-6 w-6" />}
          color="blue"
        />

        <StatsCard
          title="Utilisateurs Pro"
          value={stats?.users.pro || 0}
          icon={<TrendingUp className="h-6 w-6" />}
          color="green"
        />

        <StatsCard
          title="Utilisateurs Gratuit"
          value={stats?.users.free || 0}
          icon={<Users className="h-6 w-6" />}
          color="purple"
        />

        {/* News & Content */}
        <StatsCard
          title="Articles Scrapés (Aujourd'hui)"
          value={stats?.news.scrapedToday || 0}
          change={articlesTrend}
          icon={<Newspaper className="h-6 w-6" />}
          color="orange"
        />

        <StatsCard
          title="Actualités Virales"
          value={stats?.news.viralCount || 0}
          icon={<Zap className="h-6 w-6" />}
          color="red"
        />

        <StatsCard
          title="Scripts Générés"
          value={stats?.news.scriptsGenerated || 0}
          icon={<FileText className="h-6 w-6" />}
          color="blue"
        />
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Articles par jour */}
        <DashboardChart
          title="Articles par jour (7 derniers jours)"
          type="bar"
          data={(metrics?.pipeline.trend_7d || []).map(item => ({ name: item.date, value: item.count }))}
          xKey="name"
          yKey="value"
          color="#3b82f6"
          height={300}
        />

        {/* Répartition par pays */}
        <DashboardChart
          title="Répartition par pays (Top 10)"
          type="bar"
          data={(metrics?.geography.by_country || []).map(item => ({ name: item.country, value: item.count }))}
          xKey="name"
          yKey="value"
          color="#10b981"
          height={300}
          horizontal
        />
      </div>

      {/* Workflow Pipeline */}
      <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          Workflow Pipeline
        </h3>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            {
              label: 'En attente',
              value: metrics?.pipeline.in_workflow.pending || 0,
              borderColor: 'border-gray-400',
              bgColor: 'bg-gray-50 dark:bg-gray-900/30',
            },
            {
              label: 'Réécrits',
              value: metrics?.pipeline.in_workflow.rewritten || 0,
              borderColor: 'border-blue-400',
              bgColor: 'bg-blue-50 dark:bg-blue-900/30',
            },
            {
              label: 'Validés',
              value: metrics?.pipeline.in_workflow.approved || 0,
              borderColor: 'border-green-400',
              bgColor: 'bg-green-50 dark:bg-green-900/30',
            },
            {
              label: 'Publiés',
              value: metrics?.pipeline.in_workflow.published || 0,
              borderColor: 'border-emerald-400',
              bgColor: 'bg-emerald-50 dark:bg-emerald-900/30',
            },
          ].map((step, idx) => (
            <div
              key={idx}
              className={`rounded-lg border-2 ${step.borderColor} ${step.bgColor} p-4 text-center`}
            >
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {step.label}
              </p>
              <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                {step.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* System Health */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pipeline Status */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Statut du Système
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-3 w-3 rounded-full bg-green-500"></div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Pipeline
                </span>
              </div>
              <span className="text-xs font-medium text-green-600 dark:text-green-400">
                Actif
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Newspaper className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Sources Actives
                </span>
              </div>
              <span className="text-sm font-bold text-gray-900 dark:text-white">
                {stats?.system.sourcesActive || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Server className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Fournisseur LLM
                </span>
              </div>
              <span className="text-sm font-bold text-gray-900 dark:text-white">
                OpenAI
              </span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Clock className="h-4 w-4 text-orange-600 dark:text-orange-400" />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Dernier Pipeline
                </span>
              </div>
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                {stats?.system.lastPipelineRun
                  ? new Date(stats.system.lastPipelineRun).toLocaleTimeString('fr-FR')
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Distribution Plans */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            Distribution des Plans
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Pro</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {stats?.users.pro || 0} ({Math.round(((stats?.users.pro || 0) / (stats?.users.total || 1)) * 100)}%)
                </span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-gray-200 dark:bg-gray-800">
                <div
                  className="h-full rounded-full bg-green-500"
                  style={{
                    width: `${Math.round(((stats?.users.pro || 0) / (stats?.users.total || 1)) * 100)}%`,
                  }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Gratuit</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {stats?.users.free || 0} ({Math.round(((stats?.users.free || 0) / (stats?.users.total || 1)) * 100)}%)
                </span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-gray-200 dark:bg-gray-800">
                <div
                  className="h-full rounded-full bg-purple-500"
                  style={{
                    width: `${Math.round(((stats?.users.free || 0) / (stats?.users.total || 1)) * 100)}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
