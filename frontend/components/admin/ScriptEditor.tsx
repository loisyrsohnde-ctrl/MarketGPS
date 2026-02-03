'use client';

import { useState, useEffect } from 'react';
import { VideoScript } from '@/types/admin';
import { Save, Check, Share2 } from 'lucide-react';

interface ScriptEditorProps {
  script: VideoScript | null;
  isLoading?: boolean;
  onSave: (data: Partial<VideoScript>) => Promise<void>;
  onApprove?: () => Promise<void>;
  onPublish?: () => Promise<void>;
}

export function ScriptEditor({
  script,
  isLoading = false,
  onSave,
  onApprove,
  onPublish,
}: ScriptEditorProps) {
  const [title, setTitle] = useState('');
  const [hook, setHook] = useState('');
  const [scriptText, setScriptText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    if (script) {
      setTitle(script.title);
      setHook(script.hook);
      setScriptText(script.scriptText);
    }
  }, [script]);

  const wordCount = scriptText.split(/\s+/).filter(Boolean).length;
  const estimatedDuration = Math.round(wordCount / 150); // ~150 mots par minute

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave({ title, hook, scriptText });
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await onApprove?.();
    } finally {
      setIsApproving(false);
    }
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    try {
      await onPublish?.();
    } finally {
      setIsPublishing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-10 rounded-lg bg-gray-200 dark:bg-gray-800" />
        <div className="h-40 rounded-lg bg-gray-200 dark:bg-gray-800" />
      </div>
    );
  }

  if (!script) {
    return (
      <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
        <p className="text-gray-600 dark:text-gray-400">
          Sélectionnez un script pour l'éditer
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Article Source */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/50">
        <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
          Article Source
        </p>
        <p className="mt-1 text-sm text-gray-700 dark:text-gray-300">
          {script.articleTitle || 'Article sans titre'}
        </p>
      </div>

      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Titre du Script
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          placeholder="Ex: Stratégie de Trading pour Débutants"
        />
      </div>

      {/* Hook */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Accroche (Hook)
        </label>
        <textarea
          value={hook}
          onChange={(e) => setHook(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          placeholder="L'accroche pour attirer l'attention..."
        />
      </div>

      {/* Script */}
      <div>
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Script Complet
          </label>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {wordCount} mots • ~{estimatedDuration}min
          </div>
        </div>
        <textarea
          value={scriptText}
          onChange={(e) => setScriptText(e.target.value)}
          rows={12}
          className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 font-mono text-sm text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
          placeholder="Écrivez votre script vidéo ici..."
        />
      </div>

      {/* Preview */}
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900/50">
        <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
          Aperçu Formaté
        </p>
        <div className="mt-2 space-y-2 text-sm text-gray-700 dark:text-gray-300">
          {hook && (
            <p className="font-semibold italic">
              "{hook}"
            </p>
          )}
          {scriptText && (
            <p className="whitespace-pre-wrap">
              {scriptText.substring(0, 300)}
              {scriptText.length > 300 && '...'}
            </p>
          )}
        </div>
      </div>

      {/* Status Badge */}
      <div className="rounded-lg border border-gray-200 p-3 dark:border-gray-800">
        <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">
          Statut
        </p>
        <div className="mt-2 flex items-center gap-2">
          <span
            className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
              script.status === 'published'
                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                : script.status === 'approved'
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                : script.status === 'reviewed'
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
            }`}
          >
            {script.status === 'draft' && 'Brouillon'}
            {script.status === 'reviewed' && 'En Révision'}
            {script.status === 'approved' && 'Approuvé'}
            {script.status === 'published' && 'Publié'}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          <Save className="h-4 w-4" />
          {isSaving ? 'Sauvegarde...' : 'Sauvegarder'}
        </button>

        {script.status !== 'approved' && script.status !== 'published' && (
          <button
            onClick={handleApprove}
            disabled={isApproving}
            className="flex items-center gap-2 rounded-lg bg-yellow-600 px-4 py-2 font-medium text-white hover:bg-yellow-700 disabled:opacity-50 dark:bg-yellow-500 dark:hover:bg-yellow-600"
          >
            <Check className="h-4 w-4" />
            {isApproving ? 'Approbation...' : 'Approuver'}
          </button>
        )}

        {script.status === 'approved' && (
          <button
            onClick={handlePublish}
            disabled={isPublishing}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 font-medium text-white hover:bg-green-700 disabled:opacity-50 dark:bg-green-500 dark:hover:bg-green-600"
          >
            <Share2 className="h-4 w-4" />
            {isPublishing ? 'Publication...' : 'Publier vers Actualités'}
          </button>
        )}
      </div>
    </div>
  );
}
