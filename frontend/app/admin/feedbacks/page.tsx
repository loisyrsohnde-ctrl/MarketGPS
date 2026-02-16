'use client';

import { useState } from 'react';
import { useAdminFeedbacks } from '@/hooks/useAdminFeedbacks';
import {
  MessageSquare,
  Filter,
  Star,
  Bug,
  Lightbulb,
  HelpCircle,
} from 'lucide-react';

type StatusFilter = 'all' | 'new' | 'reviewed' | 'resolved';
type TypeFilter = 'all' | 'bug' | 'feature' | 'general';

export default function FeedbacksPage() {
  const [status, setStatus] = useState<StatusFilter>('all');
  const [type, setType] = useState<TypeFilter>('all');
  const { feedbacks, loading, error } = useAdminFeedbacks({ status, type });

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      new: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      reviewed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      resolved: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    };

    const labels: Record<string, string> = {
      new: 'Nouveau',
      reviewed: 'Examiné',
      resolved: 'Résolu',
    };

    return (
      <span
        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
          styles[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
        }`}
      >
        {labels[status] || status}
      </span>
    );
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'bug':
        return <Bug className="h-4 w-4 text-red-500" />;
      case 'feature':
        return <Lightbulb className="h-4 w-4 text-yellow-500" />;
      default:
        return <HelpCircle className="h-4 w-4 text-blue-500" />;
    }
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      bug: 'Bug',
      feature: 'Feature',
      general: 'Général',
    };
    return labels[type] || type;
  };

  const renderStars = (rating: number | null) => {
    if (!rating) return <span className="text-xs text-gray-400">—</span>;
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <Star
            key={i}
            className={`h-3.5 w-3.5 ${
              i <= rating
                ? 'fill-yellow-400 text-yellow-400'
                : 'text-gray-300 dark:text-gray-600'
            }`}
          />
        ))}
      </div>
    );
  };

  // Stats
  const newCount = feedbacks.filter((f) => f.status === 'new').length;
  const bugCount = feedbacks.filter((f) => f.type === 'bug').length;

  if (loading && feedbacks.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Feedbacks
        </h1>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-gray-200 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Feedbacks
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Retours et signalements des utilisateurs
        </p>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/20">
              <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {feedbacks.length}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-yellow-100 p-2 dark:bg-yellow-900/20">
              <MessageSquare className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Nouveaux</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {newCount}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/20">
              <Bug className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Bugs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {bugCount}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filtres
          </h3>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Statut
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as StatusFilter)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="all">Tous</option>
              <option value="new">Nouveaux</option>
              <option value="reviewed">Examinés</option>
              <option value="resolved">Résolus</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as TypeFilter)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="all">Tous</option>
              <option value="bug">Bugs</option>
              <option value="feature">Features</option>
              <option value="general">Général</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Feedbacks List */}
      {feedbacks.length > 0 ? (
        <div className="space-y-3">
          {feedbacks.map((fb) => (
            <div
              key={fb.id}
              className="rounded-lg border border-gray-200 p-5 hover:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-3">
                    {getTypeIcon(fb.type)}
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                      {getTypeLabel(fb.type)}
                    </span>
                    {getStatusBadge(fb.status)}
                    {renderStars(fb.rating)}
                  </div>

                  {fb.subject && (
                    <h4 className="mb-1 font-medium text-gray-900 dark:text-white">
                      {fb.subject}
                    </h4>
                  )}

                  <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                    {fb.message}
                  </p>

                  <div className="mt-3 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    {fb.user_email && <span>{fb.user_email}</span>}
                    {fb.platform && <span>{fb.platform}</span>}
                    <span>
                      {new Date(fb.created_at).toLocaleDateString('fr-FR', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
          <p className="text-gray-600 dark:text-gray-400">Aucun feedback trouvé</p>
        </div>
      )}
    </div>
  );
}
