'use client';

import { useState } from 'react';
import { EditorialArticle } from '@/types/admin';
import {
  EditorialScoreBadge,
  ScoreComponentBar,
} from './EditorialScoreBadge';
import {
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Newspaper,
  Users,
} from 'lucide-react';

interface EditorialTableProps {
  articles: EditorialArticle[];
  isLoading?: boolean;
  viewMode?: 'table' | 'cards';
}

const COMPONENT_LABELS: Record<string, string> = {
  source_diversity: 'Diversit\u00e9 sources',
  verified_engagement: 'Engagement v\u00e9rifi\u00e9',
  topic_importance: 'Importance sujet',
  freshness: 'Fra\u00eecheur',
  geo_relevance: 'Pertinence g\u00e9o',
};

export function EditorialTable({
  articles,
  isLoading = false,
  viewMode = 'cards',
}: EditorialTableProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-800"
          />
        ))}
      </div>
    );
  }

  if (articles.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
        <Newspaper className="mx-auto h-10 w-10 text-gray-400 mb-3" />
        <p className="text-gray-600 dark:text-gray-400">
          Aucun article avec score \u00e9ditorial trouv\u00e9
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
          Essayez de relancer le scoring ou d&apos;ajuster les filtres
        </p>
      </div>
    );
  }

  // ── Card View ─────────────────────────────────────────────────────────────
  if (viewMode === 'cards') {
    return (
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {articles.map((article, index) => (
          <div
            key={article.article_id}
            className="rounded-lg border border-gray-200 bg-white p-5 hover:shadow-lg transition-shadow dark:border-gray-800 dark:bg-gray-900/50"
          >
            {/* Rank + Score Header */}
            <div className="mb-3 flex items-start justify-between gap-2">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                  #{index + 1}
                </span>
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2 text-sm">
                    {article.title || `Article #${article.article_id}`}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {article.source_name}
                    {article.published_at &&
                      ` \u2022 ${new Date(article.published_at).toLocaleDateString('fr-FR')}`}
                  </p>
                </div>
              </div>
              <EditorialScoreBadge
                score={article.editorial_score}
                size="sm"
                showLabel={false}
              />
            </div>

            {/* Main Reason */}
            {article.reasons.length > 0 && (
              <p className="mb-3 text-xs text-gray-600 dark:text-gray-400 italic">
                {article.reasons[0]}
              </p>
            )}

            {/* Cluster Info */}
            {article.cluster_size > 1 && (
              <div className="mb-3 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/10">
                <div className="flex items-center gap-1.5 text-xs font-medium text-blue-700 dark:text-blue-300 mb-1">
                  <Users className="h-3 w-3" />
                  {article.cluster_size} sources couvrent ce sujet
                </div>
                <p className="text-xs text-blue-600 dark:text-blue-400">
                  {article.cluster_sources.join(', ')}
                </p>
              </div>
            )}

            {/* Component Scores (expandable) */}
            <button
              onClick={() =>
                setExpandedId(
                  expandedId === article.article_id
                    ? null
                    : article.article_id
                )
              }
              className="flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 transition-colors dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-800"
            >
              <span>D\u00e9tail des composants</span>
              {expandedId === article.article_id ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </button>

            {expandedId === article.article_id && (
              <div className="mt-3 space-y-2">
                {Object.entries(article.component_scores).map(([key, val]) => (
                  <ScoreComponentBar
                    key={key}
                    label={COMPONENT_LABELS[key] || key}
                    value={val}
                  />
                ))}
                {article.reasons.length > 1 && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                      Raisons :
                    </p>
                    <ul className="space-y-1">
                      {article.reasons.map((reason, i) => (
                        <li
                          key={i}
                          className="text-xs text-gray-500 dark:text-gray-500"
                        >
                          \u2022 {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Footer: metadata + link */}
            <div className="mt-3 flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex gap-2">
                {article.country && (
                  <span className="inline-flex rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                    {article.country}
                  </span>
                )}
                {article.language && (
                  <span className="inline-flex rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">
                    {article.language}
                  </span>
                )}
              </div>
              {article.url && (
                <button
                  onClick={() => window.open(article.url!, '_blank')}
                  className="inline-flex items-center gap-1 rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200 transition-colors dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  <ExternalLink className="h-3 w-3" />
                  Article
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // ── Table View ────────────────────────────────────────────────────────────
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900/50">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/80">
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white w-8">
              #
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Titre
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Source
            </th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900 dark:text-white">
              Score
            </th>
            <th className="px-4 py-3 text-center text-sm font-semibold text-gray-900 dark:text-white">
              Cluster
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Raison
            </th>
            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {articles.map((article, index) => (
            <tr
              key={article.article_id}
              className="border-b border-gray-200 hover:bg-gray-50 transition-colors dark:border-gray-800 dark:hover:bg-gray-900/50"
            >
              <td className="px-4 py-3">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                  {index + 1}
                </span>
              </td>
              <td className="px-4 py-3 max-w-xs">
                <p className="font-medium text-gray-900 dark:text-white line-clamp-2 text-sm">
                  {article.title || `Article #${article.article_id}`}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                  {article.published_at &&
                    new Date(article.published_at).toLocaleDateString('fr-FR')}
                </p>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {article.source_name}
              </td>
              <td className="px-4 py-3 text-center">
                <EditorialScoreBadge
                  score={article.editorial_score}
                  size="sm"
                />
              </td>
              <td className="px-4 py-3 text-center">
                {article.cluster_size > 1 ? (
                  <span
                    className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                    title={article.cluster_sources.join(', ')}
                  >
                    <Users className="h-3 w-3" />
                    {article.cluster_size}
                  </span>
                ) : (
                  <span className="text-xs text-gray-400">1</span>
                )}
              </td>
              <td className="px-4 py-3 max-w-[200px]">
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {article.reasons[0] || '\u2014'}
                </p>
              </td>
              <td className="px-4 py-3">
                {article.url && (
                  <button
                    onClick={() => window.open(article.url!, '_blank')}
                    className="inline-flex items-center gap-1 rounded-lg bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 hover:bg-amber-200 transition-colors dark:bg-amber-900/30 dark:text-amber-300 dark:hover:bg-amber-900/50"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Voir
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
