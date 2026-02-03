'use client';

import { useState } from 'react';
import { useViralNews } from '@/hooks/useViralNews';
import { NewsTable } from '@/components/admin/NewsTable';
import { Filter, RefreshCw } from 'lucide-react';

export default function NewsPage() {
  const [region, setRegion] = useState<string>();
  const [language, setLanguage] = useState<string>();
  const [minViralityScore, setMinViralityScore] = useState<number>();
  const [page, setPage] = useState(1);

  const { articles, total, loading, error, refetch } = useViralNews({
    region,
    language,
    minViralityScore,
    page,
    limit: 20,
  });

  const handleGenerateScript = async (articleId: string) => {
    try {
      const response = await fetch('/api/admin/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ articleId }),
      });

      if (response.ok) {
        refetch();
      }
    } catch (error) {
      console.error('Erreur lors de la génération du script:', error);
    }
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Actualités Virales
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gérez les actualités virales et générez des scripts vidéo
        </p>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filtres
          </h3>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {/* Region Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Région
            </label>
            <select
              value={region || ''}
              onChange={(e) => {
                setRegion(e.target.value || undefined);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Toutes les régions</option>
              <option value="FR">France</option>
              <option value="US">États-Unis</option>
              <option value="EU">Europe</option>
              <option value="ASIA">Asie</option>
            </select>
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Langue
            </label>
            <select
              value={language || ''}
              onChange={(e) => {
                setLanguage(e.target.value || undefined);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Toutes les langues</option>
              <option value="fr">Français</option>
              <option value="en">Anglais</option>
              <option value="de">Allemand</option>
              <option value="es">Espagnol</option>
            </select>
          </div>

          {/* Min Virality Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Viralité Min
            </label>
            <select
              value={minViralityScore || ''}
              onChange={(e) => {
                setMinViralityScore(e.target.value ? Number(e.target.value) : undefined);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Tous les niveaux</option>
              <option value="2">2x</option>
              <option value="5">5x</option>
              <option value="10">10x</option>
            </select>
          </div>

          {/* Refresh Button */}
          <div className="flex items-end">
            <button
              onClick={() => refetch()}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 flex items-center justify-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Actualiser
            </button>
          </div>
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
              Affichage de <strong>1-{Math.min(20, total)}</strong> sur{' '}
              <strong>{total}</strong> actualités
            </>
          ) : (
            'Aucune actualité trouvée'
          )}
        </div>
      )}

      {/* News Table */}
      <NewsTable
        articles={articles}
        isLoading={loading}
        onGenerateScript={handleGenerateScript}
      />

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
    </div>
  );
}
