'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { getApiBaseUrl } from '@/lib/config';

export interface SearchResult {
  id: string;
  title: string;
  type: 'article' | 'category' | 'country' | 'user';
  url?: string;
  description?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  query: string;
}

export interface UseGlobalSearchResult {
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  search: (query: string) => Promise<void>;
  clear: () => void;
}

const DEBOUNCE_DELAY = 300;

export function useGlobalSearch(): UseGlobalSearchResult {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  const getHeaders = () => {
    const adminKey = typeof window !== 'undefined' ? localStorage.getItem('adminKey') : null;
    return {
      'Content-Type': 'application/json',
      ...(adminKey && { 'X-Admin-Key': adminKey }),
    };
  };

  const search = useCallback(async (query: string) => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (!query.trim()) {
      setResults([]);
      setError(null);
      return;
    }

    // Set new debounce timer
    debounceTimerRef.current = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const apiBaseUrl = getApiBaseUrl();
        const encodedQuery = encodeURIComponent(query);
        const response = await fetch(
          `${apiBaseUrl}/api/admin/search?q=${encodedQuery}`,
          {
            headers: getHeaders(),
          }
        );

        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const data: SearchResponse = await response.json();
        setResults(data.results || []);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Search failed';
        setError(message);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_DELAY);
  }, []);

  const clear = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    setResults([]);
    setError(null);
    setLoading(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    results,
    loading,
    error,
    search,
    clear,
  };
}
