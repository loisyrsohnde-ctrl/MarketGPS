'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ViralArticle } from '@/types/admin';
import { ViralityBadge } from './ViralityBadge';
import { ChevronRight, Zap, ExternalLink, Eye, Copy, Check, CheckCircle, XCircle, Workflow } from 'lucide-react';

interface NewsTableProps {
  articles: ViralArticle[];
  isLoading?: boolean;
  onGenerateScript?: (articleId: string) => void;
  onPublish?: (articleId: string) => Promise<boolean>;
  onReject?: (articleId: string) => Promise<boolean>;
  viewMode?: 'table' | 'cards';
  selectedIds?: Set<string>;
  onSelectionChange?: (ids: Set<string>) => void;
}

export function NewsTable({
  articles,
  isLoading = false,
  onGenerateScript,
  onPublish,
  onReject,
  viewMode = 'table',
  selectedIds = new Set<string>(),
  onSelectionChange,
}: NewsTableProps) {
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<ViralArticle | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleToggleSelection = (articleId: string) => {
    if (!onSelectionChange) return;
    const newSelection = new Set(selectedIds);
    if (newSelection.has(articleId)) {
      newSelection.delete(articleId);
    } else {
      newSelection.add(articleId);
    }
    onSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    if (!onSelectionChange) return;
    const allIds = new Set(articles.map((a) => a.id));
    onSelectionChange(allIds);
  };

  const handleDeselectAll = () => {
    if (!onSelectionChange) return;
    onSelectionChange(new Set());
  };

  const isAllSelected = articles.length > 0 && articles.every((a) => selectedIds.has(a.id));
  const isSomeSelected = articles.some((a) => selectedIds.has(a.id));

  const handlePublish = async (articleId: string) => {
    if (!onPublish) return;
    setPublishingId(articleId);
    await onPublish(articleId);
    setPublishingId(null);
  };

  const handleReject = async (articleId: string) => {
    if (!onReject) return;
    setPublishingId(articleId);
    await onReject(articleId);
    setPublishingId(null);
  };

  const handleGenerateScript = async (articleId: string) => {
    setGeneratingId(articleId);
    try {
      onGenerateScript?.(articleId);
    } finally {
      setGeneratingId(null);
    }
  };

  const handleCopyTitle = (title: string, id: string) => {
    navigator.clipboard.writeText(title);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const openArticle = (url?: string) => {
    if (url) {
      window.open(url, '_blank');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-gray-200 dark:bg-gray-800" />
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

  // Card view
  if (viewMode === 'cards') {
    return (
      <>
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
          {articles.map((article) => (
            <div
              key={article.id}
              className={`rounded-lg border transition-all ${
                selectedIds.has(article.id)
                  ? 'border-blue-500 bg-blue-50 dark:border-blue-500 dark:bg-blue-950/30'
                  : 'border-gray-200 bg-white hover:shadow-lg dark:border-gray-800 dark:bg-gray-900/50'
              } p-5`}
            >
              {/* Checkbox */}
              <div className="mb-3 flex items-start justify-between gap-2">
                <input
                  type="checkbox"
                  checked={selectedIds.has(article.id)}
                  onChange={() => handleToggleSelection(article.id)}
                  className="mt-1 w-4 h-4 rounded border-gray-300 cursor-pointer dark:bg-gray-700 dark:border-gray-600"
                  title="Sélectionner cet article"
                />
              </div>
              {/* Thumbnail */}
              {article.thumbnail && (
                <div className="mb-4 h-40 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                  <img
                    src={article.thumbnail}
                    alt={article.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Header */}
              <div className="mb-3 flex items-start justify-between gap-2">
                <div className="flex-1">
                  <button
                    onClick={() => setSelectedArticle(article)}
                    className="text-left hover:opacity-75 transition-opacity w-full"
                  >
                    <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2">
                      {article.title}
                    </h3>
                  </button>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(article.publishedAt).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <ViralityBadge score={article.viralityScore} size="sm" showLabel={false} />
              </div>

              {/* Metadata */}
              <div className="mb-4 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Source:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {article.source}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Interactions:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {article.interactions.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Région:</span>
                  <span className="inline-flex rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                    {article.region}
                  </span>
                </div>
              </div>

              {/* Script Status */}
              <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-800">
                {article.hasScript ? (
                  <span className="inline-flex rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-300">
                    ✓ Script généré
                  </span>
                ) : (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Pas de script
                  </span>
                )}
              </div>

              {/* Actions */}
              <div className="grid grid-cols-4 gap-2">
                <button
                  onClick={() => handleCopyTitle(article.title, article.id)}
                  className="flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                  title="Copier le titre"
                >
                  {copiedId === article.id ? (
                    <Check className="h-3 w-3 text-green-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  <span className="hidden sm:inline">Copier</span>
                </button>

                <button
                  onClick={() => setSelectedArticle(article)}
                  className="flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                  title="Aperçu"
                >
                  <Eye className="h-3 w-3" />
                  <span className="hidden sm:inline">Aperçu</span>
                </button>

                <Link
                  href={`/admin/news/${article.id}`}
                  className="flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                  title="Workflow"
                >
                  <Workflow className="h-3 w-3" />
                  <span className="hidden sm:inline">Workflow</span>
                </Link>

                {article.url && (
                  <button
                    onClick={() => openArticle(article.url)}
                    className="flex items-center justify-center gap-1.5 rounded-lg border border-gray-300 px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                    title="Voir l'article original"
                  >
                    <ExternalLink className="h-3 w-3" />
                    <span className="hidden sm:inline">Voir</span>
                  </button>
                )}

                <div className="col-span-4">
                  {!article.hasScript ? (
                    <button
                      onClick={() => handleGenerateScript(article.id)}
                      disabled={generatingId === article.id}
                      className="w-full rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600 flex items-center justify-center gap-1.5"
                    >
                      <Zap className="h-3 w-3" />
                      {generatingId === article.id ? 'Génération...' : 'Générer script'}
                    </button>
                  ) : (
                    <Link
                      href={`/admin/scripts?articleId=${article.id}`}
                      className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-emerald-100 px-3 py-2 text-xs font-medium text-emerald-700 hover:bg-emerald-200 transition-colors dark:bg-emerald-900/30 dark:text-emerald-300 dark:hover:bg-emerald-900/50"
                    >
                      Voir script <ChevronRight className="h-3 w-3" />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Preview Modal */}
        {selectedArticle && (
          <ArticlePreviewModal
            article={selectedArticle}
            onClose={() => setSelectedArticle(null)}
          />
        )}
      </>
    );
  }

  // Table view
  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900/50">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/80">
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                <input
                  type="checkbox"
                  checked={isAllSelected}
                  onChange={() => (isAllSelected ? handleDeselectAll() : handleSelectAll())}
                  className="w-4 h-4 rounded border-gray-300 cursor-pointer dark:bg-gray-700 dark:border-gray-600"
                  title={isAllSelected ? 'Désélectionner tous' : 'Sélectionner tous'}
                  ref={(el) => {
                    if (el) {
                      (el as any).indeterminate = isSomeSelected && !isAllSelected;
                    }
                  }}
                />
              </th>
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
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {articles.map((article) => (
              <tr
                key={article.id}
                className={`border-b transition-colors ${
                  selectedIds.has(article.id)
                    ? 'bg-blue-50 dark:bg-blue-950/30'
                    : 'border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50'
                }`}
              >
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(article.id)}
                    onChange={() => handleToggleSelection(article.id)}
                    className="w-4 h-4 rounded border-gray-300 cursor-pointer dark:bg-gray-700 dark:border-gray-600"
                    title="Sélectionner cet article"
                  />
                </td>
                <td className="px-6 py-4">
                  <button
                    onClick={() => setSelectedArticle(article)}
                    className="max-w-xs text-left hover:opacity-75 transition-opacity"
                  >
                    <p className="font-medium text-gray-900 hover:text-blue-600 dark:text-white dark:hover:text-blue-400 line-clamp-2">
                      {article.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {new Date(article.publishedAt).toLocaleDateString('fr-FR')}
                    </p>
                  </button>
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
                <td className="px-6 py-4 text-sm font-medium text-gray-600 dark:text-gray-400">
                  {article.interactions.toLocaleString()}
                </td>
                <td className="px-6 py-4">
                  {article.hasScript ? (
                    <span className="inline-flex rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/30 dark:text-green-300">
                      ✓ Généré
                    </span>
                  ) : (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      —
                    </span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <div className="flex gap-2 flex-wrap">
                    {onPublish && (
                      <button
                        onClick={() => handlePublish(article.id)}
                        disabled={publishingId === article.id}
                        className="inline-flex items-center gap-1 rounded-lg bg-green-100 px-2 py-1 text-xs font-medium text-green-800 hover:bg-green-200 disabled:opacity-50 transition-colors dark:bg-green-900/30 dark:text-green-300 dark:hover:bg-green-900/50"
                        title="Publier"
                      >
                        <CheckCircle className="h-3 w-3" />
                        Publier
                      </button>
                    )}
                    {onReject && (
                      <button
                        onClick={() => handleReject(article.id)}
                        disabled={publishingId === article.id}
                        className="inline-flex items-center gap-1 rounded-lg bg-red-100 px-2 py-1 text-xs font-medium text-red-800 hover:bg-red-200 disabled:opacity-50 transition-colors dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50"
                        title="Rejeter"
                      >
                        <XCircle className="h-3 w-3" />
                        Rejeter
                      </button>
                    )}
                    <Link
                      href={`/admin/news/${article.id}`}
                      className="inline-flex items-center gap-1 rounded-lg bg-purple-100 px-2 py-1 text-xs font-medium text-purple-800 hover:bg-purple-200 transition-colors dark:bg-purple-900/30 dark:text-purple-300 dark:hover:bg-purple-900/50"
                      title="Workflow"
                    >
                      <Workflow className="h-3 w-3" />
                      Workflow
                    </Link>
                    {article.url && (
                      <button
                        onClick={() => openArticle(article.url)}
                        className="inline-flex items-center gap-1 rounded-lg bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 hover:bg-amber-200 transition-colors dark:bg-amber-900/30 dark:text-amber-300 dark:hover:bg-amber-900/50"
                        title="Voir l'article original"
                      >
                        <ExternalLink className="h-3 w-3" />
                        Article
                      </button>
                    )}
                    {!article.hasScript ? (
                      <button
                        onClick={() => handleGenerateScript(article.id)}
                        disabled={generatingId === article.id}
                        className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600"
                      >
                        <Zap className="h-3 w-3" />
                        {generatingId === article.id ? 'Génération...' : 'Générer'}
                      </button>
                    ) : (
                      <Link
                        href={`/admin/scripts?articleId=${article.id}`}
                        className="inline-flex items-center gap-1 rounded-lg bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200 transition-colors dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
                      >
                        Voir <ChevronRight className="h-3 w-3" />
                      </Link>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Preview Modal */}
      {selectedArticle && (
        <ArticlePreviewModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}
    </>
  );
}

/**
 * Article Preview Modal Component
 */
function ArticlePreviewModal({
  article,
  onClose,
}: {
  article: ViralArticle;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white dark:bg-gray-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-800 dark:bg-gray-800">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Aperçu de l'article
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-4">
          {article.thumbnail && (
            <div className="h-64 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
              <img
                src={article.thumbnail}
                alt={article.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
          )}

          <div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
              {article.title}
            </h3>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              {new Date(article.publishedAt).toLocaleDateString('fr-FR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Source
              </p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {article.source}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Région
              </p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {article.region}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Interactions
              </p>
              <p className="mt-1 font-medium text-gray-900 dark:text-white">
                {article.interactions.toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                Viralité
              </p>
              <div className="mt-1">
                <ViralityBadge score={article.viralityScore} size="sm" />
              </div>
            </div>
          </div>

          {article.url && (
            <button
              onClick={() => window.open(article.url, '_blank')}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600 flex items-center justify-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Voir l'article original
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
