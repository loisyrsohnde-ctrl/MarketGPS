'use client';

import { useState } from 'react';
import { useAdminSubscriptions } from '@/hooks/useAdminSubscriptions';
import {
  CreditCard,
  Filter,
  Calendar,
  DollarSign,
  AlertCircle,
} from 'lucide-react';

type StatusFilter = 'all' | 'active' | 'canceled' | 'past_due';

export default function SubscriptionsPage() {
  const [status, setStatus] = useState<StatusFilter>('all');
  const { subscriptions, loading, error } = useAdminSubscriptions({ status });

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      canceled: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      past_due: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
      trialing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    };

    const labels: Record<string, string> = {
      active: 'Actif',
      canceled: 'Annulé',
      past_due: 'En retard',
      trialing: 'Essai',
    };

    return (
      <span
        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
          styles[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
        }`}
      >
        {labels[status] || status}
      </span>
    );
  };

  const formatAmount = (amount: number | null, currency: string | null) => {
    if (!amount) return 'N/A';
    const cur = (currency || 'EUR').toUpperCase();
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: cur,
    }).format(amount / 100);
  };

  // Stats summary
  const activeCount = subscriptions.filter((s) => s.status === 'active').length;
  const totalMRR = subscriptions
    .filter((s) => s.status === 'active')
    .reduce((sum, s) => sum + (s.amount || 0), 0);

  if (loading && subscriptions.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Abonnements
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
          Abonnements
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Suivi des abonnements et revenus
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-green-100 p-2 dark:bg-green-900/20">
              <CreditCard className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Actifs</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {activeCount}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/20">
              <DollarSign className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">MRR estimé</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatAmount(totalMRR, 'eur')}
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 p-5 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900/20">
              <AlertCircle className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {subscriptions.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filtres
          </h3>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Statut
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as StatusFilter)}
            className="mt-1 w-full max-w-xs rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          >
            <option value="all">Tous</option>
            <option value="active">Actifs</option>
            <option value="canceled">Annulés</option>
            <option value="past_due">En retard</option>
          </select>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">Erreur: {error}</p>
        </div>
      )}

      {/* Table */}
      {subscriptions.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-800">
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Utilisateur
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Plan
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Statut
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Montant
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Période
                </th>
              </tr>
            </thead>
            <tbody>
              {subscriptions.map((sub, idx) => (
                <tr
                  key={`${sub.user_id}-${idx}`}
                  className="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
                >
                  <td className="px-6 py-4">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {sub.full_name || 'N/A'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {sub.email || sub.user_id.slice(0, 8)}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                      {sub.plan}
                    </span>
                  </td>
                  <td className="px-6 py-4">{getStatusBadge(sub.status)}</td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {formatAmount(sub.amount, sub.currency)}
                    </div>
                    {sub.interval && (
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        / {sub.interval === 'month' ? 'mois' : 'an'}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                      <Calendar className="h-4 w-4" />
                      {sub.current_period_end
                        ? new Date(sub.current_period_end).toLocaleDateString('fr-FR')
                        : 'N/A'}
                    </div>
                    {sub.cancel_at_period_end && (
                      <div className="mt-1 text-xs text-yellow-600 dark:text-yellow-400">
                        Annulation prévue
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-lg border border-gray-200 py-12 text-center dark:border-gray-800">
          <p className="text-gray-600 dark:text-gray-400">
            Aucun abonnement trouvé
          </p>
        </div>
      )}
    </div>
  );
}
