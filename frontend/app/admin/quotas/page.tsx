'use client';

import { useState } from 'react';
import { useAdminQuotas } from '@/hooks/useAdminQuotas';
import {
  Cpu,
  AlertTriangle,
  RotateCcw,
  Unlock,
  Lock,
} from 'lucide-react';

export default function QuotasPage() {
  const { quotas, exhausted, loading, error, updateQuota } = useAdminQuotas();
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const handleAction = async (
    userId: string,
    provider: string,
    action: 'disable_limit' | 'enable_limit' | 'reset'
  ) => {
    const key = `${userId}-${provider}-${action}`;
    setActionLoading(key);
    setActionMessage(null);

    const success = await updateQuota(userId, provider, action);
    if (success) {
      const labels: Record<string, string> = {
        disable_limit: 'Limite désactivée',
        enable_limit: 'Limite activée',
        reset: 'Quota réinitialisé',
      };
      setActionMessage(labels[action]);
    }
    setActionLoading(null);

    // Clear message after 3s
    setTimeout(() => setActionMessage(null), 3000);
  };

  // Group quotas by user
  const userQuotasMap = new Map<
    string,
    { user_id: string; openai?: typeof quotas[0]; gemini?: typeof quotas[0] }
  >();

  for (const q of quotas) {
    const existing = userQuotasMap.get(q.user_id) || { user_id: q.user_id };
    if (q.provider === 'openai') existing.openai = q;
    if (q.provider === 'gemini') existing.gemini = q;
    userQuotasMap.set(q.user_id, existing);
  }

  const userQuotas = Array.from(userQuotasMap.values());
  const exhaustedIds = new Set(exhausted.map((e) => e.user_id));

  if (loading && quotas.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Quotas AI
        </h1>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-gray-200 dark:bg-gray-800" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Quotas AI
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gestion des quotas OpenAI et Gemini par utilisateur
        </p>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/20">
              <Cpu className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Utilisateurs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {userQuotas.length}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900/20">
              <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Quotas épuisés</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {exhausted.length}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-green-100 p-2 dark:bg-green-900/20">
              <Unlock className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Illimités</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {quotas.filter((q) => q.limit_disabled).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Action message */}
      {actionMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-3 dark:border-green-900/30 dark:bg-green-900/20">
          <p className="text-sm text-green-800 dark:text-green-300">{actionMessage}</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Quotas Table */}
      {userQuotas.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-800">
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Utilisateur
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  OpenAI
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Gemini
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {userQuotas.map((uq) => {
                const isExhausted = exhaustedIds.has(uq.user_id);
                return (
                  <tr
                    key={uq.user_id}
                    className={`border-b border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50 ${
                      isExhausted ? 'bg-red-50/50 dark:bg-red-900/10' : ''
                    }`}
                  >
                    <td className="px-6 py-4">
                      <p className="font-mono text-sm text-gray-900 dark:text-white">
                        {uq.user_id.slice(0, 12)}...
                      </p>
                      {isExhausted && (
                        <span className="mt-1 inline-flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                          <AlertTriangle className="h-3 w-3" /> Épuisé
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {uq.openai ? (
                        <div>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {uq.openai.usage_count}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400">
                            {uq.openai.limit_disabled ? ' / ∞' : ` / ${uq.openai.limit}`}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {uq.gemini ? (
                        <div>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {uq.gemini.usage_count}
                          </span>
                          <span className="text-gray-500 dark:text-gray-400">
                            {uq.gemini.limit_disabled ? ' / ∞' : ` / ${uq.gemini.limit}`}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAction(uq.user_id, 'all', 'reset')}
                          disabled={actionLoading !== null}
                          title="Réinitialiser"
                          className="rounded-lg border border-gray-300 p-2 text-gray-600 hover:bg-gray-100 disabled:opacity-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-800"
                        >
                          <RotateCcw className="h-4 w-4" />
                        </button>
                        {(uq.openai?.limit_disabled || uq.gemini?.limit_disabled) ? (
                          <button
                            onClick={() => handleAction(uq.user_id, 'all', 'enable_limit')}
                            disabled={actionLoading !== null}
                            title="Activer les limites"
                            className="rounded-lg border border-yellow-300 p-2 text-yellow-600 hover:bg-yellow-50 disabled:opacity-50 dark:border-yellow-700 dark:text-yellow-400 dark:hover:bg-yellow-900/20"
                          >
                            <Lock className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleAction(uq.user_id, 'all', 'disable_limit')}
                            disabled={actionLoading !== null}
                            title="Désactiver les limites (illimité)"
                            className="rounded-lg border border-green-300 p-2 text-green-600 hover:bg-green-50 disabled:opacity-50 dark:border-green-700 dark:text-green-400 dark:hover:bg-green-900/20"
                          >
                            <Unlock className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
          <p className="text-gray-600 dark:text-gray-400">
            Aucun quota AI trouvé
          </p>
        </div>
      )}
    </div>
  );
}
