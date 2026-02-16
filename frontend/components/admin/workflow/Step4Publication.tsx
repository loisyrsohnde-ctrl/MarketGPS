'use client';

import { useState } from 'react';
import { Loader2, CheckCircle, ExternalLink } from 'lucide-react';
import { WorkflowArticle } from '@/hooks/useArticleWorkflow';

interface Step4PublicationProps {
  article: WorkflowArticle;
  publishing: boolean;
  onPublish: (notes?: string) => Promise<boolean>;
  showConfirmPublish: boolean;
  setShowConfirmPublish: (show: boolean) => void;
}

const wordCount = (text: string) => {
  return text.trim().split(/\s+/).filter((word) => word.length > 0).length;
};

export default function Step4Publication({
  article,
  publishing,
  onPublish,
  showConfirmPublish,
  setShowConfirmPublish,
}: Step4PublicationProps) {
  const [finalNotes, setFinalNotes] = useState('');
  const isPublished = article.editorial_status === 'published';
  const contentWordCount = wordCount(article.french_content_md || '');

  const handlePublish = async () => {
    const success = await onPublish(finalNotes);
    if (success) {
      setShowConfirmPublish(false);
      setFinalNotes('');
    }
  };

  if (isPublished) {
    return (
      <div className="space-y-6">
        {/* Success Banner */}
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-8">
          <div className="flex items-start gap-4">
            <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400 flex-shrink-0 mt-1" />
            <div>
              <h2 className="text-2xl font-bold text-green-900 dark:text-green-200 mb-2">
                Article publié avec succès!
              </h2>
              <p className="text-green-800 dark:text-green-300">
                L&apos;article est maintenant visible sur le site MarketGPS et en cours de distribution
                aux lecteurs.
              </p>
            </div>
          </div>
        </div>

        {/* Publication Summary */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-6">
            Résumé de publication
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Titre
              </h3>
              <p className="text-slate-900 dark:text-slate-100 font-medium">{article.title}</p>
            </div>

            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Nombre de mots
              </h3>
              <p className="text-slate-900 dark:text-slate-100 font-medium">
                {contentWordCount} mots
              </p>
            </div>

            {article.category && (
              <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-6">
                <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Catégorie
                </h3>
                <p className="text-slate-900 dark:text-slate-100 font-medium">
                  {article.category}
                </p>
              </div>
            )}

            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-6">
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Date de publication
              </h3>
              <p className="text-slate-900 dark:text-slate-100 font-medium">
                {new Date(article.published_date).toLocaleDateString('fr-FR')}
              </p>
            </div>
          </div>
        </div>

        {/* View on Site Button */}
        <div className="flex gap-4">
          <button className="flex-1 px-6 py-3 bg-slate-200 hover:bg-slate-300 text-slate-900 font-semibold rounded-lg transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100">
            Retour à la liste
          </button>
          <button className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors dark:bg-blue-700 dark:hover:bg-blue-600">
            Voir sur le site
            <ExternalLink className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Publication Card */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-6">
          Prêt pour la publication?
        </h2>

        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 pb-8 border-b border-gray-200 dark:border-slate-600">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Titre
            </h3>
            <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
              {article.title}
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Nombre de mots
            </h3>
            <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
              {contentWordCount} mots
            </p>
          </div>

          {article.category && (
            <div>
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                Catégorie
              </h3>
              <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
                {article.category}
              </p>
            </div>
          )}

          <div>
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
              Date
            </h3>
            <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
              {new Date(article.published_date).toLocaleDateString('fr-FR')}
            </p>
          </div>
        </div>

        {/* Final Notes */}
        <div className="mb-8">
          <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-3">
            Notes finales (optionnel)
          </h3>
          <textarea
            value={finalNotes}
            onChange={(e) => setFinalNotes(e.target.value)}
            placeholder="Ajoutez des notes finales avant publication..."
            className="w-full font-mono text-sm p-4 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical min-h-20"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button className="flex-1 px-6 py-3 bg-slate-200 hover:bg-slate-300 text-slate-900 font-semibold rounded-lg transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100">
            Retour
          </button>
          <button
            onClick={() => setShowConfirmPublish(true)}
            disabled={publishing}
            className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors dark:bg-green-700 dark:hover:bg-green-600"
          >
            {publishing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Publication en cours...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 1a1 1 0 011-1h12a1 1 0 011 1H3zm0 4a1 1 0 011-1h12a1 1 0 011 1H3zm0 4a1 1 0 011-1h12a1 1 0 011 1H3zm0 4a1 1 0 011-1h12a1 1 0 011 1H3zm0 4a1 1 0 011-1h12a1 1 0 011 1H3z" />
                </svg>
                Publier sur le site
              </>
            )}
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmPublish && (
        <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-8">
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Confirmer la publication
              </h2>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                Êtes-vous sûr de vouloir publier cet article? Cette action ne peut pas être
                annulée.
              </p>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                <p className="text-sm text-blue-900 dark:text-blue-200">
                  <strong>{article.title}</strong>
                </p>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => setShowConfirmPublish(false)}
                  disabled={publishing}
                  className="flex-1 px-4 py-2 bg-slate-200 hover:bg-slate-300 disabled:bg-gray-300 text-slate-900 font-semibold rounded-lg transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100"
                >
                  Annuler
                </button>
                <button
                  onClick={handlePublish}
                  disabled={publishing}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors dark:bg-green-700 dark:hover:bg-green-600"
                >
                  {publishing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                  Publier
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
