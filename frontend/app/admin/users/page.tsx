'use client';

import { useEffect, useState } from 'react';
import { User } from '@/types/admin';
import { Mail, Calendar, Activity, Filter } from 'lucide-react';

type PlanFilter = 'all' | 'pro' | 'free' | 'enterprise';

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<PlanFilter>('all');
  const [page, setPage] = useState(1);
  const [searchEmail, setSearchEmail] = useState('');

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (plan !== 'all') params.append('plan', plan);
      if (searchEmail) params.append('search', searchEmail);
      params.append('page', page.toString());
      params.append('limit', '20');

      const response = await fetch(`/api/admin/users?${params.toString()}`);

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des utilisateurs');
      }

      const data = await response.json();
      setUsers(data.users || []);
      setTotal(data.total || 0);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [plan, page, searchEmail]);

  const totalPages = Math.ceil(total / 20);

  const getPlanBadge = (plan: User['plan']) => {
    const styles = {
      free: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
      pro: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      enterprise: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    };

    const labels = {
      free: 'Gratuit',
      pro: 'Pro',
      enterprise: 'Entreprise',
    };

    return (
      <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${styles[plan]}`}>
        {labels[plan]}
      </span>
    );
  };

  const getActivityStatus = (lastLogin: string) => {
    const days = Math.floor(
      (Date.now() - new Date(lastLogin).getTime()) / (1000 * 60 * 60 * 24)
    );

    if (days === 0) return { text: 'Aujourd\'hui', color: 'text-green-600 dark:text-green-400' };
    if (days === 1) return { text: 'Hier', color: 'text-green-600 dark:text-green-400' };
    if (days <= 7) return { text: `Il y a ${days}j`, color: 'text-blue-600 dark:text-blue-400' };
    if (days <= 30) return { text: `Il y a ${Math.floor(days / 7)}sem`, color: 'text-yellow-600 dark:text-yellow-400' };
    return { text: `Il y a ${Math.floor(days / 30)}m`, color: 'text-gray-600 dark:text-gray-400' };
  };

  if (loading && users.length === 0) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Utilisateurs
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
          Utilisateurs
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Gérez les utilisateurs du système
        </p>
      </div>

      {/* Filters & Search */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Filtres
          </h3>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Rechercher par email
            </label>
            <input
              type="email"
              value={searchEmail}
              onChange={(e) => {
                setSearchEmail(e.target.value);
                setPage(1);
              }}
              placeholder="user@example.com"
              className="mt-1 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:placeholder-gray-500"
            />
          </div>

          {/* Plan Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Plan
            </label>
            <select
              value={plan}
              onChange={(e) => {
                setPlan(e.target.value as PlanFilter);
                setPage(1);
              }}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
            >
              <option value="all">Tous les plans</option>
              <option value="free">Gratuit</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Entreprise</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/30 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-300">
            Erreur: {error}
          </p>
        </div>
      )}

      {/* Stats */}
      {!loading && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {total > 0 ? (
            <>
              Affichage de <strong>1-{Math.min(20, total)}</strong> sur{' '}
              <strong>{total}</strong> utilisateur{total > 1 ? 's' : ''}
            </>
          ) : (
            'Aucun utilisateur trouvé'
          )}
        </div>
      )}

      {/* Users List */}
      {users.length > 0 ? (
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
                  Inscription
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Dernier Accès
                </th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900 dark:text-white">
                  Statut
                </th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const activity = getActivityStatus(user.lastLogin);
                return (
                  <tr
                    key={user.id}
                    className="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900/50"
                  >
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {user.name || 'N/A'}
                        </p>
                        <p className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                          <Mail className="h-3 w-3" />
                          {user.email}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getPlanBadge(user.plan)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                        <Calendar className="h-4 w-4" />
                        {new Date(user.createdAt).toLocaleDateString('fr-FR')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className={`flex items-center gap-1 text-sm ${activity.color}`}>
                        <Activity className="h-4 w-4" />
                        {activity.text}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                          user.isActive
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
                        }`}
                      >
                        {user.isActive ? 'Actif' : 'Inactif'}
                      </span>
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
            Aucun utilisateur trouvé
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Précédent
          </button>

          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter(
              (p) => Math.abs(p - page) <= 2 || p === 1 || p === totalPages
            )
            .map((p, i, arr) => (
              <div key={p}>
                {i > 0 && arr[i - 1] !== p - 1 && (
                  <span className="px-2 text-gray-600 dark:text-gray-400">...</span>
                )}
                <button
                  onClick={() => setPage(p)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium ${
                    page === p
                      ? 'bg-blue-600 text-white dark:bg-blue-500'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800'
                  }`}
                >
                  {p}
                </button>
              </div>
            ))}

          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
}
