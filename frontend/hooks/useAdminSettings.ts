import { useEffect, useState } from 'react';
import { AdminSettings } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

export function useAdminSettings() {
  const [settings, setSettings] = useState<AdminSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/settings`, {
        headers: { 'X-Admin-Key': adminKey },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des paramètres');
      }

      const data = await response.json();
      setSettings(data.settings || null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setSettings(null);
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (newSettings: AdminSettings) => {
    try {
      const adminKey = localStorage.getItem('adminKey') || '';
      const response = await fetch(`${API_BASE}/api/admin/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Key': adminKey,
        },
        body: JSON.stringify({ settings: newSettings }),
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la sauvegarde des paramètres');
      }

      setSettings(newSettings);
      setError(null);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      return false;
    }
  };

  useEffect(() => {
    fetchSettings();
    const interval = setInterval(fetchSettings, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return { settings, loading, error, updateSettings, refetch: fetchSettings };
}
