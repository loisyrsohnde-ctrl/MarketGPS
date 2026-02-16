'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle,
  XCircle,
  Edit3,
  Settings,
  FileText,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Loader,
} from 'lucide-react';
import { getApiBaseUrl } from '@/lib/config';

// Types
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

// Action labels in French
const ACTION_LABELS: Record<string, { label: string; color: string; icon: string }> = {
  publish: { label: 'Article publié', color: 'green', icon: 'check' },
  batch_publish: { label: 'Lot publié', color: 'green', icon: 'check' },
  reject: { label: 'Article rejeté', color: 'red', icon: 'x' },
  batch_reject: { label: 'Lot rejeté', color: 'red', icon: 'x' },
  validate: { label: 'Article validé', color: 'blue', icon: 'check' },
  batch_validate: { label: 'Lot validé', color: 'blue', icon: 'check' },
  rewrite: { label: 'Contenu réécrit', color: 'purple', icon: 'edit' },
  update_french: { label: 'Contenu mis à jour', color: 'purple', icon: 'edit' },
  settings_update: { label: 'Paramètres modifiés', color: 'gray', icon: 'settings' },
};

// Resource type labels in French
const RESOURCE_TYPE_LABELS: Record<string, string> = {
  article: 'Article',
  script: 'Script',
  source: 'Source',
  settings: 'Paramètres',
};

// Get icon based on action
function getActionIcon(action: string) {
  const config = ACTION_LABELS[action] || { icon: 'alert' };

  switch (config.icon) {
    case 'check':
      return <CheckCircle className="h-5 w-5" />;
    case 'x':
      return <XCircle className="h-5 w-5" />;
    case 'edit':
      return <Edit3 className="h-5 w-5" />;
    case 'settings':
      return <Settings className="h-5 w-5" />;
    default:
      return <AlertCircle className="h-5 w-5" />;
  }
}

// Get color classes based on action
function getColorClasses(action: string): { bg: string; text: string; border: string } {
  const config = ACTION_LABELS[action];

  switch (config?.color) {
    case 'green':
      return {
        bg: 'bg-green-50 dark:bg-green-950/30',
        text: 'text-green-600 dark:text-green-400',
        border: 'border-green-200 dark:border-green-900/50',
      };
    case 'red':
      return {
        bg: 'bg-red-50 dark:bg-red-950/30',
        text: 'text-red-600 dark:text-red-400',
        border: 'border-red-200 dark:border-red-900/50',
      };
    case 'blue':
      return {
        bg: 'bg-blue-50 dark:bg-blue-950/30',
        text: 'text-blue-600 dark:text-blue-400',
        border: 'border-blue-200 dark:border-blue-900/50',
      };
    case 'purple':
      return {
        bg: 'bg-purple-50 dark:bg-purple-950/30',
        text: 'text-purple-600 dark:text-purple-400',
        border: 'border-purple-200 dark:border-purple-900/50',
      };
    default:
      return {
        bg: 'bg-gray-50 dark:bg-gray-900/30',
        text: 'text-gray-600 dark:text-gray-400',
        border: 'border-gray-200 dark:border-gray-800/50',
      };
  }
}

// Format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'À l\'instant';
  if (diffMins < 60) return `il y a ${diffMins}m`;
  if (diffHours < 24) return `il y a ${diffHours}h`;
  if (diffDays === 1) return 'Hier';
  if (diffDays < 7) return `il y a ${diffDays}j`;

  // Format as date
  return date.toLocaleDateString('fr-FR', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

// Parse date string to Date object
function parseDate(dateString: string): Date {
  return new Date(dateString);
}

// Activity Entry Component
function ActivityEntry({ entry }: { entry: ActivityLogEntry }) {
  const actionConfig = ACTION_LABELS[entry.action] || ACTION_LABELS['settings_update'];
  const colors = getColorClasses(entry.action);
  const resourceLabel = RESOURCE_TYPE_LABELS[entry.resource_type] || entry.resource_type;

  return (
    <div className={`border-l-4 px-4 py-4 ${colors.border} ${colors.bg}`}>
      <div className="flex items-start gap-4">
        {/* Timeline dot */}
        <div className={`mt-1 flex-shrink-0 ${colors.text}`}>
          {getActionIcon(entry.action)}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Action and resource */}
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-medium text-gray-900 dark:text-white">
              {actionConfig.label}
            </p>
            {entry.resource_id && (
              <span className="text-sm text-gray-600 dark:text-gray-400">
                ({resourceLabel} #{entry.resource_id})
              </span>
            )}
          </div>

          {/* Details */}
          {entry.details && (
            <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
              {entry.details}
            </p>
          )}

          {/* Admin and timestamp */}
          <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-gray-600 dark:text-gray-500">
            <span>Par {entry.admin_id}</span>
            <span>{formatRelativeTime(entry.created_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminActivityLog() {
  const [entries, setEntries] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [actionFilter, setActionFilter] = useState<string>('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<string>('all');

  // Pagination
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 20;

  // Fetch activity log
  const fetchActivityLog = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const adminKey = localStorage.getItem('adminKey');
      if (!adminKey) {
        setError('Clé d\'administration non trouvée');
        setLoading(false);
        return;
      }

      const baseUrl = getApiBaseUrl();
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: (page * limit).toString(),
      });

      if (actionFilter && actionFilter !== 'all') {
        params.append('action', actionFilter);
      }

      if (resourceTypeFilter && resourceTypeFilter !== 'all') {
        params.append('resource_type', resourceTypeFilter);
      }

      // Handle date filter
      if (dateFilter !== 'all') {
        const now = new Date();
        let cutoffDate = new Date();

        if (dateFilter === 'today') {
          cutoffDate.setHours(0, 0, 0, 0);
        } else if (dateFilter === '7days') {
          cutoffDate.setDate(cutoffDate.getDate() - 7);
        } else if (dateFilter === '30days') {
          cutoffDate.setDate(cutoffDate.getDate() - 30);
        }

        // Note: This filtering happens client-side since the API doesn't support date filters
        // In a production system, you'd add this to the backend
      }

      const response = await fetch(
        `${baseUrl}/api/admin/activity?${params}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Key': adminKey,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data: ActivityLogResponse = await response.json();

      // Client-side date filtering
      let filteredEntries = data.entries;
      if (dateFilter !== 'all') {
        const now = new Date();
        let cutoffDate = new Date();

        if (dateFilter === 'today') {
          cutoffDate.setHours(0, 0, 0, 0);
        } else if (dateFilter === '7days') {
          cutoffDate.setDate(cutoffDate.getDate() - 7);
        } else if (dateFilter === '30days') {
          cutoffDate.setDate(cutoffDate.getDate() - 30);
        }

        filteredEntries = filteredEntries.filter(
          (entry) => parseDate(entry.created_at) >= cutoffDate
        );
      }

      setEntries(filteredEntries);
      setTotal(data.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Erreur lors du chargement du journal'
      );
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [page, limit, actionFilter, resourceTypeFilter, dateFilter]);

  // Fetch on mount and when filters change
  useEffect(() => {
    setPage(0);
  }, [actionFilter, resourceTypeFilter, dateFilter]);

  useEffect(() => {
    fetchActivityLog();
  }, [fetchActivityLog]);

  const maxPages = Math.ceil(total / limit);
  const hasPrevious = page > 0;
  const hasNext = page < maxPages - 1;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Journal d'Activité
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Suivi de toutes les actions administrateur et modifications système
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-950">
        <div className="grid gap-4 md:grid-cols-3">
          {/* Action Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Action
            </label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            >
              <option value="">Tous</option>
              <option value="publish">Publier</option>
              <option value="batch_publish">Lot publié</option>
              <option value="reject">Rejeter</option>
              <option value="batch_reject">Lot rejeté</option>
              <option value="validate">Valider</option>
              <option value="batch_validate">Lot validé</option>
              <option value="rewrite">Réécrire</option>
              <option value="update_french">Mise à jour contenu</option>
              <option value="settings_update">Paramètres</option>
            </select>
          </div>

          {/* Resource Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Type de Ressource
            </label>
            <select
              value={resourceTypeFilter}
              onChange={(e) => setResourceTypeFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            >
              <option value="">Tous</option>
              <option value="article">Article</option>
              <option value="script">Script</option>
              <option value="source">Source</option>
              <option value="settings">Paramètres</option>
            </select>
          </div>

          {/* Date Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Période
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
            >
              <option value="all">Tout</option>
              <option value="today">Aujourd'hui</option>
              <option value="7days">7 jours</option>
              <option value="30days">30 jours</option>
            </select>
          </div>
        </div>
      </div>

      {/* Activity Timeline */}
      <div className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-6 w-6 animate-spin text-gray-400 dark:text-gray-600" />
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
            <p className="text-sm text-red-800 dark:text-red-300">
              Erreur: {error}
            </p>
          </div>
        ) : entries.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-12 text-center dark:border-gray-800 dark:bg-gray-950">
            <p className="text-gray-600 dark:text-gray-400">
              Aucune activité enregistrée
            </p>
          </div>
        ) : (
          <>
            {entries.map((entry) => (
              <ActivityEntry key={entry.id} entry={entry} />
            ))}
          </>
        )}
      </div>

      {/* Pagination */}
      {!loading && entries.length > 0 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-800">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Page {page + 1} de {maxPages} ({total} entrées)
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={!hasPrevious}
              className="flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Précédent
            </button>

            <button
              onClick={() => setPage((p) => Math.min(maxPages - 1, p + 1))}
              disabled={!hasNext}
              className="flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 disabled:opacity-50 dark:border-gray-700 dark:text-gray-300 dark:disabled:opacity-50"
            >
              Suivant
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
