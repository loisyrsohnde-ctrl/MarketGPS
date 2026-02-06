'use client';

import { useEffect, useState, useCallback } from 'react';
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [adminKey, setAdminKey] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  const checkAuth = useCallback(async (key: string) => {
    try {
      const response = await fetch(`${API_BASE}/admin/auth/check`, {
        headers: { 'X-Admin-Key': key },
      });
      if (response.ok) {
        setIsAuthorized(true);
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    const savedKey = localStorage.getItem('adminKey');
    if (savedKey) {
      setAdminKey(savedKey);
      checkAuth(savedKey).then((ok) => {
        if (!ok) {
          localStorage.removeItem('adminKey');
        }
        setIsLoading(false);
      });
    } else {
      setIsLoading(false);
    }
  }, [checkAuth]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);

    try {
      const ok = await checkAuth(adminKey);
      if (ok) {
        localStorage.setItem('adminKey', adminKey);
      } else {
        setLoginError('Clé admin invalide');
      }
    } catch {
      setLoginError('Erreur de connexion au serveur');
    } finally {
      setLoginLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-white dark:bg-gray-950">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Vérification des permissions...</p>
        </div>
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="flex h-screen items-center justify-center bg-white dark:bg-gray-950">
        <div className="w-full max-w-md p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center">
                <span className="text-white font-bold">◉</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">MarketGPS Admin</span>
            </div>
            <p className="text-gray-500 dark:text-gray-400">
              Entrez la clé d&apos;administration pour accéder au dashboard.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Clé Admin
              </label>
              <input
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                placeholder="Entrez la clé admin"
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
              />
            </div>

            {loginError && (
              <p className="text-red-500 text-sm">{loginError}</p>
            )}

            <button
              type="submit"
              disabled={loginLoading}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-colors disabled:opacity-50"
            >
              {loginLoading ? 'Vérification...' : 'Accéder au Dashboard'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <AdminSidebar />
      <main className="ml-64 flex-1 overflow-auto">
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
