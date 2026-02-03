'use client';

import { useAdminStats } from '@/hooks/useAdminStats';
import { StatsCard } from '@/components/admin/StatsCard';
import {
  Users,
  Newspaper,
  FileText,
  TrendingUp,
  Activity,
  Zap,
} from 'lucide-react';

export default function AdminDashboard() {
  const { stats, loading, error } = useAdminStats();

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
              className="h-32 rounded-lg bg-gray-200 dark:bg-gray-800"
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
          Erreur lors du chargement des statistiques: {error}
        </p>
      </div>
    );
  }

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
          change={stats?.users.newThisWeek || 0}
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

      {/* System Info */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Pipeline Status */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Dernier Pipeline
              </p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.system.lastPipelineRun
                  ? new Date(stats.system.lastPipelineRun).toLocaleTimeString(
                      'fr-FR'
                    )
                  : 'N/A'}
              </p>
              <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                ✓ Actif
              </p>
            </div>
            <div className="rounded-lg bg-green-100 p-3 dark:bg-green-900/20">
              <Activity className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        {/* Sources */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Sources Actives
              </p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {stats?.system.sourcesActive || 0}
              </p>
              <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
                Connectées et en cours de scraping
              </p>
            </div>
            <div className="rounded-lg bg-blue-100 p-3 dark:bg-blue-900/20">
              <Newspaper className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section - Placeholder */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Activity Chart */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Activité cette semaine
          </h3>
          <div className="mt-4 flex h-32 items-end justify-around gap-2">
            {[65, 78, 90, 81, 56, 55, 40].map((value, i) => (
              <div
                key={i}
                className="flex-1 rounded-t-lg bg-blue-500/50"
                style={{ height: `${value}%` }}
              />
            ))}
          </div>
          <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
            Lun - Dim
          </p>
        </div>

        {/* Distribution */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Distribution des Plans
          </h3>
          <div className="mt-4 space-y-3">
            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Pro</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {stats?.users.pro || 0} ({Math.round(((stats?.users.pro || 0) / (stats?.users.total || 1)) * 100)}%)
                </span>
              </div>
              <div className="mt-1 h-2 rounded-full bg-gray-200 dark:bg-gray-800">
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
              <div className="mt-1 h-2 rounded-full bg-gray-200 dark:bg-gray-800">
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
