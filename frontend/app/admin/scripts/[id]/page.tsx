'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { VideoScript } from '@/types/admin';
import { ScriptEditor } from '@/components/admin/ScriptEditor';
import { ArrowLeft } from 'lucide-react';

export default function EditScriptPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [script, setScript] = useState<VideoScript | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchScript = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/admin/scripts/${params.id}`);

        if (!response.ok) {
          throw new Error('Script non trouvé');
        }

        const data = await response.json();
        setScript(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      } finally {
        setLoading(false);
      }
    };

    fetchScript();
  }, [params.id]);

  const handleSave = async (data: Partial<VideoScript>) => {
    try {
      const response = await fetch(`/api/admin/scripts/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la sauvegarde');
      }

      const updated = await response.json();
      setScript(updated);
      setSaveMessage('Script sauvegardé avec succès');
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      setSaveMessage(null);
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    }
  };

  const handleApprove = async () => {
    try {
      const response = await fetch(`/api/admin/scripts/${params.id}/approve`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'approbation');
      }

      const updated = await response.json();
      setScript(updated);
      setSaveMessage('Script approuvé');
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      setSaveMessage(null);
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'approbation');
    }
  };

  const handlePublish = async () => {
    try {
      const response = await fetch(`/api/admin/scripts/${params.id}/publish`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la publication');
      }

      const updated = await response.json();
      setScript(updated);
      setSaveMessage('Script publié vers les actualités');
      setTimeout(() => {
        router.push('/admin/scripts');
      }, 2000);
    } catch (err) {
      setSaveMessage(null);
      setError(err instanceof Error ? err.message : 'Erreur lors de la publication');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="inline-flex items-center gap-2 rounded-lg hover:bg-gray-100 px-2 py-2 dark:hover:bg-gray-800"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Éditer Script
          </h1>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Modifiez et gérez le script vidéo
          </p>
        </div>
      </div>

      {/* Messages */}
      {saveMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900/30 dark:bg-green-900/20">
          <p className="text-sm text-green-800 dark:text-green-300">
            {saveMessage}
          </p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">
            Erreur: {error}
          </p>
        </div>
      )}

      {/* Editor */}
      <ScriptEditor
        script={script}
        isLoading={loading}
        onSave={handleSave}
        onApprove={handleApprove}
        onPublish={handlePublish}
      />
    </div>
  );
}
