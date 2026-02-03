'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useVideoScripts } from '@/hooks/useVideoScripts';
import { VideoScript } from '@/types/admin';
import { Eye, Edit2, Trash2, Filter } from 'lucide-react';

export default function ScriptsPage() {
  const [status, setStatus] = useState<VideoScript['status'] | undefined>();
  const [page, setPage] = useState(1);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { scripts, total, loading, error, deleteScript, refetch } =
    useVideoScripts({
      status,
      page,
      limit: 20,
    });

  const handleDelete = async (id: string) => {
    try {
      await deleteScript(id);
      setDeleteId(null);
    } catch (err) {
      console.error('Erreur lors de la suppression:', err);
    }
  };

  const totalPages = Math.ceil(total / 20);

  const getStatusBadge = (status: VideoScript['status']) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      reviewed: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      approved: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      published: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    };

    const labels = {
      draft: 'Brouillon',
      reviewed: 'En Révision',
      approved: 'Approuvé',
      published: 'Publié',
    };

    return (
      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${styles[status]}`}>
        {labels[status]}
      </span>
    );
  };

  if (loading && scripts.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Scripts Vidéo
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
          Scripts Vidéo
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gérez et éditez les scripts vidéo
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Filtrer par statut:
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => {
              setStatus(undefined);
              setPage(1);
            }}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              status === undefined
                ? 'bg-blue-600 text-white dark:bg-blue-500'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
            }`}
          >
            Tous
          </button>
          {(['draft', 'reviewed', 'approved', 'published'] as const).map(
            (s) => (
              <button
                key={s}
                onClick={() => {
                  setStatus(s);
                  setPage(1);
                }}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                  status === s
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
                }`}
              >
                {s === 'draft' && 'Brouillons'}
                {s === 'reviewed' && 'En Révision'}
                {s === 'approved' && 'Approuvés'}
                {s === 'published' && 'Publiés'}
              </button>
            )
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">
            Erreur: {error}
          </p>
        </div>
      )}

      {/* Stats */}
      {!loading && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {total > 0 ? (
            <>
              {total} script{total > 1 ? 's' : ''} trouvé{total > 1 ? 's' : ''}
            </>
          ) : (
            'Aucun script trouvé'
          )}
        </div>
      )}

      {/* Scripts List */}
      {scripts.length > 0 ? (
        <div className="space-y-3">
          {scripts.map((script) => (
            <div
              key={script.id}
              className="rounded-lg border border-gray-200 p-4 hover:border-gray-300 dark:border-gray-800 dark:hover:border-gray-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {script.title}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {script.articleTitle || 'Article sans titre'}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
                    <span>
                      {script.wordCount} mots • ~{script.estimatedDuration}min
                    </span>
                    <span>
                      {new Date(script.createdAt).toLocaleDateString('fr-FR')}
                    </span>
                  </div>
                </div>

                <div className="ml-4 flex flex-col items-end gap-2">
                  {getStatusBadge(script.status)}
                  <div className="flex gap-2">
                    <Link
                      href={`/admin/scripts/${script.id}`}
                      className="inline-flex items-center gap-2 rounded-lg bg-blue-100 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
                    >
                      <Edit2 className="h-3 w-3" />
                      Éditer
                    </Link>
                    <button
                      onClick={() => setDeleteId(script.id)}
                      className="inline-flex items-center gap-2 rounded-lg bg-red-100 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50"
                    >
                      <Trash2 className="h-3 w-3" />
                      Supprimer
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
          <p className="text-gray-600 dark:text-gray-400">
            Aucun script vidéo trouvé
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Précédent
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter(
              (p) => Math.abs(p - page) <= 2 || p === 1 || p === totalPages
            )
            .map((p, i, arr) => (
              <div key={p}>
                {i > 0 && arr[i - 1] !== p - 1 && (
                  <span className="px-2 text-gray-600 dark:text-gray-400">...</span>
                )}
                <button
                  onClick={() => setPage(p)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    page === p
                      ? 'bg-blue-600 text-white dark:bg-blue-500'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
                  }`}
                >
                  {p}
                </button>
              </div>
            ))}

          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Suivant
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 dark:bg-gray-900">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Confirmer la suppression
            </h3>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Êtes-vous sûr de vouloir supprimer ce script? Cette action ne peut
              pas être annulée.
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => setDeleteId(null)}
                className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                Annuler
              </button>
              <button
                onClick={() => handleDelete(deleteId)}
                className="rounded-lg bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
