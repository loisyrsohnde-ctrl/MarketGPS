'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ViralArticle } from '@/types/admin';
import { ViralityBadge } from './ViralityBadge';
import { ChevronRight, Zap } from 'lucide-react';

interface NewsTableProps {
  articles: ViralArticle[];
  isLoading?: boolean;
  onGenerateScript?: (articleId: string) => void;
}

export function NewsTable({ articles, isLoading = false, onGenerateScript }: NewsTableProps) {
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const handleGenerateScript = async (articleId: string) => {
    setGeneratingId(articleId);
    try {
      onGenerateScript?.(articleId);
    } finally {
      setGeneratingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-gray-200 dark:bg-gray-800" />
        ))}
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
        <p className="text-gray-600 dark:text-gray-400">
          Aucune actualité virale trouvée
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-800">
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Titre
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Source
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Région
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Viralité
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Interactions
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Script
            </th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Action
            </th>
          </tr>
        </thead>
        <tbody>
          {articles.map((article) => (
            <tr
              key={article.id}
              className="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
            >
              <td className="px-6 py-4">
                <div className="max-w-xs">
                  <p className="font-medium text-gray-900 dark:text-white">
                    {article.title}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(article.publishedAt).toLocaleDateString('fr-FR')}
                  </p>
                </div>
              </td>
              <td className="px-6 py-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {article.source}
                </p>
              </td>
              <td className="px-6 py-4">
                <span className="inline-flex rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                  {article.region}
                </span>
              </td>
              <td className="px-6 py-4">
                <ViralityBadge score={article.viralityScore} showLabel={false} size="sm" />
              </td>
              <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                {article.interactions.toLocaleString()}
              </td>
              <td className="px-6 py-4">
                {article.hasScript ? (
                  <span className="inline-flex rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-300">
                    ✓ Généré
                  </span>
                ) : (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    -
                  </span>
                )}
              </td>
              <td className="px-6 py-4">
                {!article.hasScript ? (
                  <button
                    onClick={() => handleGenerateScript(article.id)}
                    disabled={generatingId === article.id}
                    className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
                  >
                    <Zap className="h-3 w-3" />
                    {generatingId === article.id ? 'En cours...' : 'Générer'}
                  </button>
                ) : (
                  <Link
                    href={`/admin/scripts?articleId=${article.id}`}
                    className="inline-flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                  >
                    Voir <ChevronRight className="h-3 w-3" />
                  </Link>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
