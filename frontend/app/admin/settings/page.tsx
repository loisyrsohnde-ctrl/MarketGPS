'use client';

import { useState, useEffect } from 'react';
import { Settings, Save, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { useAdminSettings } from '@/hooks/useAdminSettings';
import { AdminSettings } from '@/types/admin';

const DEFAULT_SETTINGS: AdminSettings = {
  editorial: {
    virality_threshold_2x: 2,
    virality_threshold_5x: 5,
    virality_threshold_10x: 10,
    min_editorial_score: 60,
    rewrite_model: 'openai',
    rewrite_temperature: 0.7,
    editorial_line: 'Éveil des consciences et développement de l\'Afrique',
  },
  notifications: {
    alert_on_viral_break: true,
    viral_threshold: 5,
    alert_channels: [],
    webhook_url: '',
  },
  maintenance: {
    is_under_maintenance: false,
    maintenance_message: '',
    api_rate_limit: 1000,
  },
  scraping: {
    enable_automatic_ingestion: true,
    max_articles_per_source: 50,
    daily_ingest_times: ['08:00', '14:00', '20:00'],
  },
};

/** Safely merge partial settings with defaults — never returns undefined sub-objects */
function mergeWithDefaults(partial: any): AdminSettings {
  return {
    editorial: { ...DEFAULT_SETTINGS.editorial, ...(partial?.editorial || {}) },
    notifications: { ...DEFAULT_SETTINGS.notifications, ...(partial?.notifications || {}) },
    maintenance: { ...DEFAULT_SETTINGS.maintenance, ...(partial?.maintenance || {}) },
    scraping: { ...DEFAULT_SETTINGS.scraping, ...(partial?.scraping || {}) },
  };
}

export default function SettingsPage() {
  const { settings: loadedSettings, loading: isLoading, error, updateSettings: saveSettings, refetch } = useAdminSettings();
  const [settings, setSettings] = useState<AdminSettings>(DEFAULT_SETTINGS);
  const [originalSettings, setOriginalSettings] = useState<AdminSettings>(DEFAULT_SETTINGS);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Sync loaded settings into local state via useEffect (safe — never runs during render)
  useEffect(() => {
    if (loadedSettings && !initialized) {
      const merged = mergeWithDefaults(loadedSettings);
      setSettings(merged);
      setOriginalSettings(merged);
      setInitialized(true);
    }
  }, [loadedSettings, initialized]);

  // Always compute safe settings for rendering — guaranteed to have all sub-objects
  const s = mergeWithDefaults(settings);

  const handleChange = (path: string, value: any) => {
    const keys = path.split('.');
    setSettings((prev) => {
      const newSettings = JSON.parse(JSON.stringify(prev));
      let current = newSettings;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const success = await saveSettings(settings);

      if (success) {
        setOriginalSettings(JSON.parse(JSON.stringify(settings)));
        setMessage({
          type: 'success',
          text: 'Paramètres sauvegardés avec succès',
        });
        setTimeout(() => setMessage(null), 3000);
        // Refresh settings after save
        refetch();
      } else {
        setMessage({
          type: 'error',
          text: error || 'Une erreur est survenue',
        });
      }
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Une erreur est survenue',
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-8 max-w-4xl">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Paramètres Administrateur
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Configurez le comportement du système MarketGPS
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-4xl">
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
        {/* Scraping & Pipeline */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-6 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Scraping & Pipeline
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Score de Viralité Minimum (2x)
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={s.editorial.virality_threshold_2x}
                onChange={(e) =>
                  handleChange('editorial.virality_threshold_2x', parseFloat(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Nombre Maximum d'Articles par Source
              </label>
              <input
                type="number"
                min="1"
                value={s.scraping.max_articles_per_source}
                onChange={(e) =>
                  handleChange('scraping.max_articles_per_source', parseInt(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>

            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={s.scraping.enable_automatic_ingestion}
                  onChange={(e) =>
                    handleChange('scraping.enable_automatic_ingestion', e.target.checked)
                  }
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Ingestion automatique
                </span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Horaires d'ingestion (séparés par des virgules)
              </label>
              <input
                type="text"
                value={s.scraping.daily_ingest_times?.join(', ') || ''}
                onChange={(e) =>
                  handleChange('scraping.daily_ingest_times', e.target.value.split(',').map(t => t.trim()))
                }
                placeholder="08:00, 14:00, 20:00"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Rédaction & IA */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-6 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Rédaction & IA
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Modèle IA pour Réécriture
              </label>
              <select
                value={s.editorial.rewrite_model}
                onChange={(e) =>
                  handleChange('editorial.rewrite_model', e.target.value as 'openai' | 'gemini')
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              >
                <option value="openai">OpenAI (GPT-4)</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Température ({s.editorial.rewrite_temperature.toFixed(2)})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={s.editorial.rewrite_temperature}
                onChange={(e) =>
                  handleChange('editorial.rewrite_temperature', parseFloat(e.target.value))
                }
                className="mt-2 w-full"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Plus élevé = plus créatif, Plus bas = plus factuel
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Ligne Éditoriale
              </label>
              <textarea
                value={s.editorial.editorial_line}
                onChange={(e) =>
                  handleChange('editorial.editorial_line', e.target.value)
                }
                rows={4}
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-6 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Notifications
            </h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={s.notifications.alert_on_viral_break}
                  onChange={(e) =>
                    handleChange('notifications.alert_on_viral_break', e.target.checked)
                  }
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Activer les alertes
                </span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Seuil de Viralité pour Alerte
              </label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={s.notifications.viral_threshold}
                onChange={(e) =>
                  handleChange('notifications.viral_threshold', parseFloat(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                URL Webhook
              </label>
              <input
                type="url"
                value={s.notifications.webhook_url}
                onChange={(e) =>
                  handleChange('notifications.webhook_url', e.target.value)
                }
                placeholder="https://example.com/webhook"
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Système */}
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <div className="mb-6 flex items-center gap-2">
            <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Système
            </h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-4 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              <div className="flex-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={s.maintenance.is_under_maintenance}
                    onChange={(e) =>
                      handleChange('maintenance.is_under_maintenance', e.target.checked)
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

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Limite de Taux API
              </label>
              <input
                type="number"
                min="1"
                value={s.maintenance.api_rate_limit}
                onChange={(e) =>
                  handleChange('maintenance.api_rate_limit', parseInt(e.target.value))
                }
                className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Requêtes par minute
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
