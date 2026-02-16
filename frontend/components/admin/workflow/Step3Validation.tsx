'use client';

import { useState } from 'react';
import { Loader2, CheckSquare, Square } from 'lucide-react';
import { WorkflowArticle } from '@/hooks/useArticleWorkflow';
import MarkdownRenderer from '@/components/admin/MarkdownRenderer';

interface Step3ValidationProps {
  article: WorkflowArticle;
  validating: boolean;
  onValidate: (notes?: string) => Promise<boolean>;
}

export default function Step3Validation({
  article,
  validating,
  onValidate,
}: Step3ValidationProps) {
  const [approvalNotes, setApprovalNotes] = useState(article.approval_notes || '');
  const [checklist, setChecklist] = useState({
    localImpact: false,
    positiveAngle: false,
    futureProspective: false,
    noHtmlTags: false,
    blogStyle: false,
  });

  const handleToggleCheck = (key: keyof typeof checklist) => {
    setChecklist((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleValidate = async () => {
    const success = await onValidate(approvalNotes);
    if (success) {
      // Reset form if needed
    }
  };

  const allChecked = Object.values(checklist).every((value) => value);

  return (
    <div className="space-y-6">
      {/* Article Preview */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 overflow-hidden">
        <div className="bg-slate-100 dark:bg-slate-700 px-8 py-6 border-b border-gray-200 dark:border-slate-600">
          <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
            {article.title}
          </h2>
        </div>

        <div className="p-8">
          {/* Metadata Bar */}
          <div className="flex flex-wrap gap-4 mb-8 pb-8 border-b border-gray-200 dark:border-slate-600">
            {article.category && (
              <div>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Catégorie
                </span>
                <p className="text-slate-900 dark:text-slate-100 font-medium">
                  {article.category}
                </p>
              </div>
            )}
            <div>
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Pays
              </span>
              <p className="text-slate-900 dark:text-slate-100 font-medium">
                {article.country}
              </p>
            </div>
            <div>
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                Date
              </span>
              <p className="text-slate-900 dark:text-slate-100 font-medium">
                {new Date(article.published_date).toLocaleDateString('fr-FR')}
              </p>
            </div>
          </div>

          {/* Image Placeholder */}
          <div className="bg-gradient-to-br from-gray-200 to-gray-300 dark:from-slate-700 dark:to-slate-600 w-full h-48 rounded-lg mb-8 flex items-center justify-center">
            <span className="text-gray-500 dark:text-slate-400 font-medium">
              Image de l&apos;article
            </span>
          </div>

          {/* Content */}
          <div className="prose prose-sm dark:prose-invert max-w-none mb-8">
            <MarkdownRenderer content={article.french_content_md || ''} />
          </div>
        </div>
      </div>

      {/* Validation Checklist */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-6">
          Checklist de validation
        </h2>

        <div className="space-y-3">
          <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            <input
              type="checkbox"
              checked={checklist.localImpact}
              onChange={() => handleToggleCheck('localImpact')}
              className="mt-1"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Impact local mentionné
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            <input
              type="checkbox"
              checked={checklist.positiveAngle}
              onChange={() => handleToggleCheck('positiveAngle')}
              className="mt-1"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Angle positif / empowerment
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            <input
              type="checkbox"
              checked={checklist.futureProspective}
              onChange={() => handleToggleCheck('futureProspective')}
              className="mt-1"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Perspective future
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            <input
              type="checkbox"
              checked={checklist.noHtmlTags}
              onChange={() => handleToggleCheck('noHtmlTags')}
              className="mt-1"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Pas de balises HTML
            </span>
          </label>

          <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors">
            <input
              type="checkbox"
              checked={checklist.blogStyle}
              onChange={() => handleToggleCheck('blogStyle')}
              className="mt-1"
            />
            <span className="text-slate-700 dark:text-slate-300">
              Style blog / article internet
            </span>
          </label>
        </div>
      </div>

      {/* Approval Notes */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
        <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
          Remarques d&apos;approbation
        </h2>
        <textarea
          value={approvalNotes}
          onChange={(e) => setApprovalNotes(e.target.value)}
          placeholder="Ajoutez vos remarques avant approbation..."
          className="w-full font-mono text-sm p-4 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical min-h-24"
        />
      </div>

      {/* Buttons */}
      <div className="flex items-center justify-between">
        <button className="px-6 py-3 bg-slate-200 hover:bg-slate-300 text-slate-900 font-semibold rounded-lg transition-colors dark:bg-slate-700 dark:hover:bg-slate-600 dark:text-slate-100">
          Retour
        </button>
        <button
          onClick={handleValidate}
          disabled={validating}
          className="inline-flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors dark:bg-green-700 dark:hover:bg-green-600"
        >
          {validating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Approbation en cours...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
              Approuver
            </>
          )}
        </button>
      </div>
    </div>
  );
}
