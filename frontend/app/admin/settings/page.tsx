'use client';

import { useState } from 'react';
import { Settings, Save, AlertCircle, CheckCircle } from 'lucide-react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    minViralityScore: 2,
    maxArticlesPerDay: 1000,
    scriptGenerationModel: 'gpt-4',
    notificationsEnabled: true,
    maintenanceMode: false,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleChange = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const response = await fetch('/api/admin/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la sauvegarde des paramètres');
      }

      setMessage({
        type: 'success',
        text: 'Paramètres sauvegardés avec succès',
      });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Une erreur est survenue',
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Paramètres Administrateur
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Configurez le comportement du système MarketGPS
        </p>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={`rounded-lg border p-4 ${
            message.type === 'success'
              ? 'border-green-200 bg-green-50 dark:border-green-900/30 dark:bg-green-900/20'
              : 'border-red-200 bg-red-50 dark:border-red-900/30 dark:bg-red-900/20'
          }`}
        >
          <div className="flex items-center gap-3">
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            )}
            <p
              className={`text-sm ${
                message.type === 'success'
                  ? 'text-green-800 dark:text-green-300'
                  : 'text-red-800 dark:text-red-300'
              }`}
            >
              {message.text}
            </p>
          </div>
        </div>
      )}

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* Scraping Settings */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Paramètres de Scraping
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Score de Viralité Minimum
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={settings.minViralityScore}
                onChange={(e) =>
                  handleChange('minViralityScore', parseFloat(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Les articles avec un score inférieur seront ignorés
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Nombre Maximum d'Articles par Jour
              </label>
              <input
                type="number"
                min="1"
                value={settings.maxArticlesPerDay}
                onChange={(e) =>
                  handleChange('maxArticlesPerDay', parseInt(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Limite le nombre d'articles traités chaque jour
              </p>
            </div>
          </div>
        </div>

        {/* Script Generation Settings */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Génération de Scripts
            </h3>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Modèle IA
            </label>
            <select
              value={settings.scriptGenerationModel}
              onChange={(e) =>
                handleChange('scriptGenerationModel', e.target.value)
              }
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="gpt-4">GPT-4 (Meilleure qualité)</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Rapide)</option>
              <option value="claude">Claude (Créatif)</option>
            </select>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Sélectionnez le modèle IA pour générer les scripts
            </p>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Notifications
            </h3>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.notificationsEnabled}
                onChange={(e) =>
                  handleChange('notificationsEnabled', e.target.checked)
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Activer les notifications
              </span>
            </label>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Recevez des alertes pour les événements importants
            </p>
          </div>
        </div>

        {/* System Settings */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-4 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Système
            </h3>
          </div>

          <div className="flex items-center gap-4 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
            <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <div className="flex-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.maintenanceMode}
                  onChange={(e) =>
                    handleChange('maintenanceMode', e.target.checked)
                  }
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                  Mode Maintenance
                </span>
              </label>
              <p className="mt-1 text-xs text-yellow-700 dark:text-yellow-400">
                Désactiver l'accès des utilisateurs pendant la maintenance
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600"
        >
          <Save className="h-4 w-4" />
          {isSaving ? 'Sauvegarde...' : 'Sauvegarder les paramètres'}
        </button>
      </div>

      {/* Info Box */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900/30 dark:bg-blue-900/20">
        <p className="text-sm text-blue-800 dark:text-blue-300">
          Les modifications seront appliquées immédiatement après la sauvegarde.
          Certains paramètres peuvent nécessiter un redémarrage du service.
        </p>
      </div>
    </div>
  );
}
