'use client';

import { useState } from 'react';
import { useAdminDiagnostics } from '@/hooks/useAdminDiagnostics';
import {
  Activity,
  Database,
  BarChart3,
  Newspaper,
  Play,
  RefreshCw,
  Trash2,
  Zap,
  ArrowUpCircle,
  Clock,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';

type PipelineAction = 'run' | 'ingest' | 'publish' | 'cleanup' | 'score-v2' | 'update-interactions';

export default function DiagnosticsPage() {
  const { diagnostics, pipeline, loading, error, refetch, runPipelineAction } =
    useAdminDiagnostics();
  const [runningAction, setRunningAction] = useState<string | null>(null);
  const [actionResult, setActionResult] = useState<string | null>(null);

  const handlePipelineAction = async (action: PipelineAction) => {
    setRunningAction(action);
    setActionResult(null);
    try {
      const result = await runPipelineAction(action);
      setActionResult(`${action} terminé avec succès`);
      console.log('Pipeline result:', result);
    } catch (err) {
      setActionResult(
        `Erreur: ${err instanceof Error ? err.message : 'Erreur inconnue'}`
      );
    } finally {
      setRunningAction(null);
      setTimeout(() => setActionResult(null), 5000);
    }
  };

  const pipelineActions: {
    action: PipelineAction;
    label: string;
    icon: typeof Play;
    color: string;
  }[] = [
    { action: 'run', label: 'Full Pipeline', icon: Play, color: 'green' },
    { action: 'ingest', label: 'Ingest', icon: ArrowUpCircle, color: 'blue' },
    { action: 'publish', label: 'Publish', icon: Zap, color: 'purple' },
    { action: 'score-v2', label: 'Score V2', icon: BarChart3, color: 'orange' },
    { action: 'update-interactions', label: 'Update Interactions', icon: RefreshCw, color: 'teal' },
    { action: 'cleanup', label: 'Cleanup', icon: Trash2, color: 'red' },
  ];

  if (loading) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Diagnostics & Pipeline
        </h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 rounded-lg bg-gray-200 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Diagnostics & Pipeline
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Santé du système et gestion du pipeline
          </p>
        </div>
        <button
          onClick={refetch}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          <RefreshCw className="mr-2 inline h-4 w-4" />
          Rafraîchir
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Pipeline Status */}
      {pipeline && (
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
            <Activity className="h-5 w-5" />
            Statut Pipeline
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Dernier run</p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {pipeline.last_run
                  ? new Date(pipeline.last_run).toLocaleString('fr-FR')
                  : 'Jamais'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Statut</p>
              <div className="mt-1 flex items-center gap-1">
                {pipeline.is_stale ? (
                  <>
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                    <span className="font-medium text-yellow-600 dark:text-yellow-400">
                      Stale ({pipeline.minutes_since_last_run} min)
                    </span>
                  </>
                ) : pipeline.scheduler_configured ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="font-medium text-green-600 dark:text-green-400">
                      Actif
                    </span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4 text-gray-400" />
                    <span className="font-medium text-gray-500">Non configuré</span>
                  </>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Sources</p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {pipeline.sources_configured}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Historique</p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {pipeline.history.length} runs récents
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Actions */}
      <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
        <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
          <Zap className="h-5 w-5" />
          Actions Pipeline
        </h2>

        {actionResult && (
          <div
            className={`mb-4 rounded-lg border p-3 text-sm ${
              actionResult.startsWith('Erreur')
                ? 'border-red-200 bg-red-50 text-red-800 dark:border-red-900/30 dark:bg-red-900/20 dark:text-red-300'
                : 'border-green-200 bg-green-50 text-green-800 dark:border-green-900/30 dark:bg-green-900/20 dark:text-green-300'
            }`}
          >
            {actionResult}
          </div>
        )}

        <div className="grid gap-3 md:grid-cols-3">
          {pipelineActions.map(({ action, label, icon: Icon, color }) => (
            <button
              key={action}
              onClick={() => handlePipelineAction(action)}
              disabled={runningAction !== null}
              className={`flex items-center gap-3 rounded-lg border border-gray-200 p-4 text-left transition-colors hover:border-gray-300 disabled:opacity-50 dark:border-gray-700 dark:hover:border-gray-600 ${
                runningAction === action ? 'animate-pulse' : ''
              }`}
            >
              <div
                className={`rounded-lg p-2 ${
                  color === 'green'
                    ? 'bg-green-100 dark:bg-green-900/20'
                    : color === 'blue'
                    ? 'bg-blue-100 dark:bg-blue-900/20'
                    : color === 'purple'
                    ? 'bg-purple-100 dark:bg-purple-900/20'
                    : color === 'orange'
                    ? 'bg-orange-100 dark:bg-orange-900/20'
                    : color === 'teal'
                    ? 'bg-teal-100 dark:bg-teal-900/20'
                    : 'bg-red-100 dark:bg-red-900/20'
                }`}
              >
                <Icon
                  className={`h-5 w-5 ${
                    color === 'green'
                      ? 'text-green-600 dark:text-green-400'
                      : color === 'blue'
                      ? 'text-blue-600 dark:text-blue-400'
                      : color === 'purple'
                      ? 'text-purple-600 dark:text-purple-400'
                      : color === 'orange'
                      ? 'text-orange-600 dark:text-orange-400'
                      : color === 'teal'
                      ? 'text-teal-600 dark:text-teal-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                />
              </div>
              <div>
                <p className="font-medium text-gray-900 dark:text-white">{label}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {runningAction === action ? 'En cours...' : 'Cliquer pour lancer'}
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Diagnostics Grid */}
      {diagnostics && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Universe */}
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
              <Database className="h-5 w-5 text-blue-500" />
              Universe
            </h3>
            {diagnostics.universe.error ? (
              <p className="text-sm text-red-500">{diagnostics.universe.error}</p>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total actifs</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.universe.total}
                  </span>
                </div>
                {Object.entries(diagnostics.universe.active_by_scope || {}).map(
                  ([scope, count]) => (
                    <div key={scope} className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">{scope}</span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {count}
                      </span>
                    </div>
                  )
                )}
                <hr className="border-gray-200 dark:border-gray-700" />
                {Object.entries(diagnostics.universe.by_type || {}).map(
                  ([type, count]) => (
                    <div key={type} className="flex justify-between text-sm">
                      <span className="text-gray-500 dark:text-gray-400">{type}</span>
                      <span className="text-gray-700 dark:text-gray-300">{count}</span>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          {/* Scores */}
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
              <BarChart3 className="h-5 w-5 text-green-500" />
              Scores
            </h3>
            {diagnostics.scores.error ? (
              <p className="text-sm text-red-500">{diagnostics.scores.error}</p>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total scorés</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.scores.total_scored}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    Dernière MAJ
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.scores.last_update
                      ? new Date(diagnostics.scores.last_update).toLocaleString('fr-FR')
                      : 'N/A'}
                  </span>
                </div>
                <hr className="border-gray-200 dark:border-gray-700" />
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-green-600 dark:text-green-400">High (70+)</span>
                    <span className="font-medium">{diagnostics.scores.distribution.high_70_plus}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-yellow-600 dark:text-yellow-400">Medium (40-69)</span>
                    <span className="font-medium">{diagnostics.scores.distribution.medium_40_69}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-red-600 dark:text-red-400">Low (&lt;40)</span>
                    <span className="font-medium">{diagnostics.scores.distribution.low_below_40}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* News */}
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
              <Newspaper className="h-5 w-5 text-purple-500" />
              News
            </h3>
            {diagnostics.news.error ? (
              <p className="text-sm text-red-500">{diagnostics.news.error}</p>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total articles</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.news.total_articles}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Aujourd&apos;hui</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.news.articles_today}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Cette semaine</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {diagnostics.news.articles_this_week}
                  </span>
                </div>
                <hr className="border-gray-200 dark:border-gray-700" />
                {Object.entries(diagnostics.news.by_region || {}).map(
                  ([region, count]) => (
                    <div key={region} className="flex justify-between text-sm">
                      <span className="text-gray-500 dark:text-gray-400">{region}</span>
                      <span className="text-gray-700 dark:text-gray-300">{count}</span>
                    </div>
                  )
                )}
              </div>
            )}
          </div>

          {/* Strategies & Watchlist */}
          <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-gray-900 dark:text-white">
              <Clock className="h-5 w-5 text-orange-500" />
              Stratégies & Watchlist
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Templates</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {diagnostics.strategies.error
                    ? 'Erreur'
                    : diagnostics.strategies.templates_count}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">
                  Stratégies utilisateurs
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {diagnostics.strategies.error
                    ? 'Erreur'
                    : diagnostics.strategies.user_strategies_count}
                </span>
              </div>
              <hr className="border-gray-200 dark:border-gray-700" />
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">
                  Items watchlist
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {diagnostics.watchlist.error
                    ? 'Erreur'
                    : diagnostics.watchlist.total_items}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">
                  Utilisateurs watchlist
                </span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {diagnostics.watchlist.error
                    ? 'Erreur'
                    : diagnostics.watchlist.unique_users}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
