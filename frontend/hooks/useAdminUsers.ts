import { useEffect, useState, useCallback } from 'react';
import { User } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

type PlanFilter = 'all' | 'pro' | 'free' | 'enterprise';

interface UseAdminUsersParams {
  plan?: PlanFilter;
  searchEmail?: string;
  page?: number;
  limit?: number;
}

export function useAdminUsers(params?: UseAdminUsersParams) {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const plan = params?.plan || 'all';
  const searchEmail = params?.searchEmail || '';
  const page = params?.page || 1;
  const limit = params?.limit || 20;

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';
      const queryParams = new URLSearchParams();
      if (plan !== 'all') queryParams.append('filter', plan);
      if (searchEmail) queryParams.append('search', searchEmail);
      const offset = (page - 1) * limit;
      queryParams.append('limit', limit.toString());
      queryParams.append('offset', offset.toString());

      const response = await fetch(`${API_BASE}/admin/users?${queryParams.toString()}`, {
        headers: { 'X-Admin-Key': adminKey },
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Erreur lors du chargement des utilisateurs');
      }

      const data = await response.json();

      // Backend returns UserSummary[] directly (not wrapped in {users, total})
      const rawUsers = Array.isArray(data) ? data : (data.users || []);

      // Map backend fields to frontend User type
      const mappedUsers: User[] = rawUsers.map((u: any) => ({
        id: u.id,
        email: u.email || '',
        name: u.full_name || u.email?.split('@')[0] || 'N/A',
        plan: u.is_pro ? 'pro' : (u.plan === 'enterprise' ? 'enterprise' : 'free'),
        createdAt: u.created_at || new Date().toISOString(),
        lastLogin: u.last_sign_in || u.created_at || new Date().toISOString(),
        isActive: u.last_sign_in
          ? (Date.now() - new Date(u.last_sign_in).getTime()) < 30 * 24 * 60 * 60 * 1000
          : false,
      }));

      setUsers(mappedUsers);
      setTotal(Array.isArray(data) ? data.length : (data.total || mappedUsers.length));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, [plan, searchEmail, page, limit]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return { users, total, loading, error, refetch: fetchUsers };
}
