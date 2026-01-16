/**
 * API Client pour MarketGPS Frontend
 * 
 * Utilise la configuration centralisée depuis frontend/lib/config.ts
 * Toutes les requêtes au backend passent par ce module
 */

import { API_CONFIG } from './config';

class APIClient {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
    this.defaultHeaders = API_CONFIG.DEFAULT_HEADERS;
  }

  /**
   * Effectue une requête GET
   */
  async get<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  /**
   * Effectue une requête POST
   */
  async post<T = any>(
    endpoint: string,
    body?: any,
    options?: RequestInit
  ): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  /**
   * Effectue une requête DELETE
   */
  async delete<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }

  /**
   * Requête générique avec gestion des erreurs
   */
  private async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.defaultHeaders,
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Request Failed: ${endpoint}`, error);
      throw error;
    }
  }
}

export const apiClient = new APIClient();

/**
 * Utilisation depuis les composants React :
 * 
 * import { apiClient } from '@/lib/api';
 * 
 * // Récupérer des assets
 * const assets = await apiClient.get('/api/assets/top-scored?limit=20');
 * 
 * // Ajouter à la watchlist (exemple du bouton "Suivre")
 * await apiClient.post('/api/watchlist/add', {
 *   asset_id: '123',
 *   user_id: 'abc123'
 * });
 * 
 * // Retirer de la watchlist
 * await apiClient.delete(`/api/watchlist/remove?asset_id=${id}`);
 */
