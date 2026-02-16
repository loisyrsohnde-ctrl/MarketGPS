'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Search,
  PenTool,
  CheckCircle,
  Send,
  Loader2,
  AlertCircle,
  CheckSquare,
  Square,
  Zap,
} from 'lucide-react';
import { useArticleWorkflow } from '@/hooks/useArticleWorkflow';
import StepIndicator from '@/components/admin/StepIndicator';
import Step1Research from '@/components/admin/workflow/Step1Research';
import Step2Writing from '@/components/admin/workflow/Step2Writing';
import Step3Validation from '@/components/admin/workflow/Step3Validation';
import Step4Publication from '@/components/admin/workflow/Step4Publication';

export default function ArticleWorkflowPage() {
  const params = useParams();
  const router = useRouter();
  const articleId = params.id as string;

  const {
    article,
    loading,
    error,
    currentStep,
    rewriting,
    validating,
    publishing,
    fetchArticle,
    triggerRewrite,
    saveFrenchContent,
    validateArticle,
    publishArticle,
  } = useArticleWorkflow();

  const [showConfirmPublish, setShowConfirmPublish] = useState(false);

  useEffect(() => {
    if (articleId) {
      fetchArticle(articleId);
    }
  }, [articleId, fetchArticle]);

  const handleGoBack = () => {
    router.back();
  };

  if (loading && !article) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400">
                Chargement de l&apos;article...
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={handleGoBack}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 mb-6 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Retour
          </button>
          <div className="bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 p-8">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                  Article non trouvé
                </h2>
                <p className="text-slate-600 dark:text-slate-400">
                  {error || 'Impossible de charger l\'article demandé.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadge = () => {
    const statusMap = {
      pending: { label: 'En attente', color: 'bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-slate-200' },
      researched: { label: 'Recherche', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' },
      rewritten: { label: 'Rédaction', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
      validated: { label: 'Validé', color: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200' },
      published: { label: 'Publié', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' },
    };

    const status = statusMap[article.editorial_status as keyof typeof statusMap] || statusMap.pending;
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${status.color}`}>
        {status.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={handleGoBack}
              className="p-2 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition-colors"
              title="Retour"
            >
              <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-2">
                {article.title}
              </h1>
              {getStatusBadge()}
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-red-800 dark:text-red-300">{error}</p>
          </div>
        )}

        {/* Step Indicator */}
        <StepIndicator currentStep={currentStep} />

        {/* Step Content */}
        <div className="mt-8">
          {currentStep === 1 && <Step1Research article={article} />}
          {currentStep === 2 && (
            <Step2Writing
              article={article}
              rewriting={rewriting}
              onTriggerRewrite={triggerRewrite}
              onSaveContent={saveFrenchContent}
            />
          )}
          {currentStep === 3 && (
            <Step3Validation
              article={article}
              validating={validating}
              onValidate={validateArticle}
            />
          )}
          {currentStep === 4 && (
            <Step4Publication
              article={article}
              publishing={publishing}
              onPublish={publishArticle}
              showConfirmPublish={showConfirmPublish}
              setShowConfirmPublish={setShowConfirmPublish}
            />
          )}
        </div>
      </div>
    </div>
  );
}
