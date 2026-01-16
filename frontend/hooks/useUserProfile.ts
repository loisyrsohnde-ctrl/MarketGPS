/**
 * useUserProfile - Hook pour gérer le profil utilisateur
 * Charge les données depuis le backend et permet les mises à jour avec persistance
 */

import { useEffect, useState, useCallback } from 'react';
import * as userApi from '@/lib/api-user';

export interface UseUserProfileReturn {
  // State
  profile: userApi.UserProfile | null;
  notifications: userApi.NotificationSettings | null;
  entitlements: userApi.UserEntitlements | null;
  loading: boolean;
  error: string | null;

  // Methods
  updateProfile: (data: {
    displayName?: string;
    avatar?: string;
  }) => Promise<void>;
  uploadAvatar: (file: File) => Promise<string>;
  updateNotifications: (
    settings: userApi.NotificationSettings
  ) => Promise<void>;
  changePassword: (
    currentPassword: string,
    newPassword: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  deleteAccount: (password: string) => Promise<void>;
  refetch: () => Promise<void>;
}

export function useUserProfile(): UseUserProfileReturn {
  const [profile, setProfile] = useState<userApi.UserProfile | null>(null);
  const [notifications, setNotifications] =
    useState<userApi.NotificationSettings | null>(null);
  const [entitlements, setEntitlements] =
    useState<userApi.UserEntitlements | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Charger les données du profil
  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [profile, notifications, entitlements] = await Promise.all([
        userApi.getUserProfile(),
        userApi.getNotificationSettings(),
        userApi.getUserEntitlements(),
      ]);

      setProfile(profile);
      setNotifications(notifications);
      setEntitlements(entitlements);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      console.error('Failed to fetch profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Charger les données au montage
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Mettre à jour le profil
  const updateProfile = useCallback(
    async (data: { displayName?: string; avatar?: string }) => {
      try {
        setError(null);
        const updated = await userApi.updateUserProfile(data);
        setProfile(updated);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'An error occurred';
        setError(message);
        throw err;
      }
    },
    []
  );

  // Uploader une photo
  const uploadAvatar = useCallback(async (file: File): Promise<string> => {
    try {
      setError(null);
      const result = await userApi.uploadProfileAvatar(file);
      // Mettre à jour le profil avec la nouvelle URL
      if (profile) {
        const updated = await userApi.updateUserProfile({
          avatar: result.url,
        });
        setProfile(updated);
      }
      return result.url;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      throw err;
    }
  }, [profile]);

  // Mettre à jour les notifications
  const updateNotifications = useCallback(
    async (settings: userApi.NotificationSettings) => {
      try {
        setError(null);
        const updated = await userApi.updateNotificationSettings(settings);
        setNotifications(updated);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'An error occurred';
        setError(message);
        throw err;
      }
    },
    []
  );

  // Changer le mot de passe
  const changePassword = useCallback(
    async (currentPassword: string, newPassword: string) => {
      try {
        setError(null);
        await userApi.changePassword({
          currentPassword,
          newPassword,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : 'An error occurred';
        setError(message);
        throw err;
      }
    },
    []
  );

  // Se déconnecter
  const logout = useCallback(async () => {
    try {
      setError(null);
      await userApi.logout();
      // Rediriger vers la page de login
      window.location.href = '/login';
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      throw err;
    }
  }, []);

  // Supprimer le compte
  const deleteAccount = useCallback(async (password: string) => {
    try {
      setError(null);
      await userApi.deleteAccount(password);
      // Rediriger vers la page d'accueil
      window.location.href = '/';
    } catch (err) {
      const message = err instanceof Error ? err.message : 'An error occurred';
      setError(message);
      throw err;
    }
  }, []);

  return {
    profile,
    notifications,
    entitlements,
    loading,
    error,
    updateProfile,
    uploadAvatar,
    updateNotifications,
    changePassword,
    logout,
    deleteAccount,
    refetch: fetchProfile,
  };
}
