/**
 * User API Services
 * Services pour gérer le profil utilisateur, sécurité, notifications
 */

import { apiClient } from './api-client';
import { getApiBaseUrl } from './config';

export interface UserProfile {
  id: string;
  email: string;
  displayName: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export interface NotificationSettings {
  emailNotifications: boolean;
  marketAlerts: boolean;
  priceAlerts: boolean;
  portfolioUpdates: boolean;
}

export interface UserEntitlements {
  plan: 'FREE' | 'MONTHLY' | 'YEARLY';
  status: 'active' | 'inactive' | 'canceled';
  dailyRequestsLimit: number;
}

/**
 * Récupérer le profil utilisateur
 */
export async function getUserProfile(): Promise<UserProfile> {
  try {
    return await apiClient.get('/users/profile');
  } catch (error) {
    console.error('Failed to fetch user profile:', error);
    throw error;
  }
}

/**
 * Mettre à jour le profil utilisateur
 */
export async function updateUserProfile(data: {
  displayName?: string;
  avatar?: string;
}): Promise<UserProfile> {
  try {
    return await apiClient.post('/users/profile/update', data);
  } catch (error) {
    console.error('Failed to update user profile:', error);
    throw error;
  }
}

/**
 * Uploader une photo de profil
 */
export async function uploadProfileAvatar(file: File): Promise<{
  url: string;
  path: string;
}> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${getApiBaseUrl()}/users/avatar/upload`,
      {
        method: 'POST',
        body: formData,
        // Note: Ne pas définir Content-Type, le navigateur le fera
      }
    );

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to upload avatar:', error);
    throw error;
  }
}

/**
 * Récupérer les préférences de notifications
 */
export async function getNotificationSettings(): Promise<NotificationSettings> {
  try {
    return await apiClient.get('/users/notifications');
  } catch (error) {
    console.error('Failed to fetch notification settings:', error);
    // Retourner les valeurs par défaut en cas d'erreur
    return {
      emailNotifications: true,
      marketAlerts: true,
      priceAlerts: true,
      portfolioUpdates: true,
    };
  }
}

/**
 * Mettre à jour les préférences de notifications
 */
export async function updateNotificationSettings(
  settings: NotificationSettings
): Promise<NotificationSettings> {
  try {
    return await apiClient.post('/users/notifications/update', settings);
  } catch (error) {
    console.error('Failed to update notification settings:', error);
    throw error;
  }
}

/**
 * Changer le mot de passe
 */
export async function changePassword(data: {
  currentPassword: string;
  newPassword: string;
}): Promise<{ success: boolean }> {
  try {
    return await apiClient.post('/users/security/change-password', data);
  } catch (error) {
    console.error('Failed to change password:', error);
    throw error;
  }
}

/**
 * Se déconnecter
 */
export async function logout(): Promise<{ success: boolean }> {
  try {
    return await apiClient.post('/users/logout', {});
  } catch (error) {
    console.error('Failed to logout:', error);
    throw error;
  }
}

/**
 * Supprimer le compte
 */
export async function deleteAccount(password: string): Promise<{
  success: boolean;
}> {
  try {
    return await apiClient.post('/users/delete-account', { password });
  } catch (error) {
    console.error('Failed to delete account:', error);
    throw error;
  }
}

/**
 * Récupérer les droits utilisateur
 */
export async function getUserEntitlements(): Promise<UserEntitlements> {
  try {
    return await apiClient.get('/users/entitlements');
  } catch (error) {
    console.error('Failed to fetch user entitlements:', error);
    // Retourner le plan gratuit par défaut
    return {
      plan: 'FREE',
      status: 'active',
      dailyRequestsLimit: 10,
    };
  }
}
