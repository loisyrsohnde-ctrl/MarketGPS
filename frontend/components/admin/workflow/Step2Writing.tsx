'use client';

import { useState } from 'react';
import { Loader2, Zap } from 'lucide-react';
import { WorkflowArticle } from '@/hooks/useArticleWorkflow';
import MarkdownRenderer from '@/components/admin/MarkdownRenderer';

interface Step2WritingProps {
  article: WorkflowArticle;
  rewriting: boolean;
  onTriggerRewrite: (sourceLang?: string) => Promise<boolean>;
  onSaveContent: (content: string, notes?: string) => Promise<boolean>;
}

const WORD_TARGET_MIN = 400;
const WORD_TARGET_MAX = 600;

export default function Step2Writing({
  article,
  rewriting,
  onTriggerRewrite,
  onSaveContent,
}: Step2WritingProps) {
  const [frenchContent, setFrenchContent] = useState(article.french_content_md || '');
  const [editorialNotes, setEditorialNotes] = useState(article.editorial_notes || '');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const wordCount = frenchContent.trim().split(/\s+/).filter((word) => word.length > 0).length;

  const getWordCountColor = () => {
    if (wordCount < WORD_TARGET_MIN) return 'text-red-600 dark:text-red-400';
    if (wordCount > WORD_TARGET_MAX) return 'text-orange-600 dark:text-orange-400';
    return 'text-green-600 dark:text-green-400';
  };

  const handleRewrite = async () => {
    const success = await onTriggerRewrite(article.language);
    if (success && article.french_content_md) {
      setFrenchContent(article.french_content_md);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      const success = await onSaveContent(frenchContent, editorialNotes);
      if (success) {
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
          Ligne éditoriale
        </h3>
        <p className="text-blue-800 dark:text-blue-300">
          Éveil des consciences et développement de l&apos;Afrique. Style blog, pas robotique.
        </p>
      </div>

      {/* Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel: Original Content */}
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
          <div className="bg-slate-100 dark:bg-slate-700 px-6 py-4 border-b border-gray-200 dark:border-slate-600">
            <h2 className="font-bold text-slate-900 dark:text-slate-100">
              Contenu original
            </h2>
          </div>
          <div className="p-6">
            <div className="prose prose-sm dark:prose-invert max-w-none overflow-auto max-h-96">
              <MarkdownRenderer content={article.original_content_md} />
            </div>
          </div>
        </div>

        {/* Right Panel: French Content Editor */}
        <div className="flex flex-col bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
          <div className="bg-slate-100 dark:bg-slate-700 px-6 py-4 border-b border-gray-200 dark:border-slate-600">
            <h2 className="font-bold text-slate-900 dark:text-slate-100">
              Contenu en français
            </h2>
          </div>
          <div className="p-6 flex flex-col flex-1">
            {frenchContent ? (
              <textarea
                value={frenchContent}
                onChange={(e) => setFrenchContent(e.target.value)}
                className="flex-1 font-mono text-sm p-4 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="Votre contenu en français..."
                rows={15}
              />
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center py-12">
                <p className="text-slate-500 dark:text-slate-400 mb-4">
                  Aucun contenu français n&apos;existe encore
                </p>
                <button
                  onClick={handleRewrite}
                  disabled={rewriting}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors dark:bg-blue-700 dark:hover:bg-blue-600"
                >
                  {rewriting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Génération en cours...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Réécrire avec l&apos;IA
                    </>
                  )}
                </button>
              </div>
            )}

            {/* Word Count */}
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className={`font-medium ${getWordCountColor()}`}>
                {wordCount} mots
                {wordCount < WORD_TARGET_MIN && ` (min: ${WORD_TARGET_MIN})`}
                {wordCount > WORD_TARGET_MAX && ` (max: ${WORD_TARGET_MAX})`}
              </span>
              <span className="text-slate-500 dark:text-slate-400">
                Cible: {WORD_TARGET_MIN}-{WORD_TARGET_MAX} mots
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Editorial Notes */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-6">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
          Notes éditoriales
        </h2>
        <textarea
          value={editorialNotes}
          onChange={(e) => setEditorialNotes(e.target.value)}
          placeholder="Ajoutez des notes sur votre processus de rédaction..."
          className="w-full font-mono text-sm p-4 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical min-h-24"
        />
      </div>

      {/* Buttons */}
      <div className="flex items-center justify-between">
        {saveSuccess && (
          <div className="text-green-600 dark:text-green-400 font-medium">
            ✓ Contenu enregistré avec succès
          </div>
        )}
        <div className="flex gap-3 ml-auto">
          {frenchContent && (
            <button
              onClick={handleSave}
              disabled={saving || !frenchContent.trim()}
              className="px-6 py-3 bg-slate-200 hover:bg-slate-300 disabled:bg-gray-300 text-slate-900 font-semibold rounded-lg transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100"
            >
              {saving ? (
                <Loader2 className="w-5 h-5 animate-spin inline mr-2" />
              ) : null}
              Enregistrer le brouillon
            </button>
          )}
          <button
            disabled={saving || !frenchContent.trim()}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors dark:bg-blue-700 dark:hover:bg-blue-600"
          >
            Valider la rédaction
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 10l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
