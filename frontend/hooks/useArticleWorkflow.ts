'use client';

import { useState, useCallback } from 'react';
import { getApiBaseUrl } from '@/lib/config';

export interface WorkflowArticle {
  id: string;
  title: string;
  source_title: string;
  source_url: string;
  country: string;
  language: string;
  published_date: string;
  original_content_md: string;
  french_content_md?: string;
  editorial_status: 'pending' | 'researched' | 'rewritten' | 'validated' | 'published';
  editorial_notes?: string;
  approval_notes?: string;
  category?: string;
  editorial_scores?: {
    relevance: number;
    impact: number;
    originality: number;
    timeliness: number;
    engagement: number;
  };
  interactions_count?: number;
}

export interface UseArticleWorkflowResult {
  article: WorkflowArticle | null;
  loading: boolean;
  error: string | null;
  currentStep: number;
  rewriting: boolean;
  validating: boolean;
  publishing: boolean;
  fetchArticle: (id: string) => Promise<void>;
  triggerRewrite: (sourceLang?: string) => Promise<boolean>;
  saveFrenchContent: (content: string, notes?: string) => Promise<boolean>;
  validateArticle: (notes?: string) => Promise<boolean>;
  publishArticle: (notes?: string) => Promise<boolean>;
}

function mapStatusToStep(status: string): number {
  switch (status) {
    case 'pending':
    case 'researched':
      return 1;
    case 'rewritten':
      return 2;
    case 'validated':
      return 3;
    case 'published':
      return 4;
    default:
      return 1;
  }
}

export function useArticleWorkflow(): UseArticleWorkflowResult {
  const [article, setArticle] = useState<WorkflowArticle | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rewriting, setRewriting] = useState(false);
  const [validating, setValidating] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const getHeaders = () => {
    const adminKey = typeof window !== 'undefined' ? localStorage.getItem('adminKey') : null;
    return {
      'Content-Type': 'application/json',
      ...(adminKey && { 'X-Admin-Key': adminKey }),
    };
  };

  const fetchArticle = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/admin/articles/${id}/workflow`, {
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch article: ${response.statusText}`);
      }

      const data = await response.json();
      setArticle(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerRewrite = useCallback(
    async (sourceLang?: string) => {
      if (!article) return false;

      setRewriting(true);
      setError(null);
      try {
        const apiBaseUrl = getApiBaseUrl();
        const response = await fetch(`${apiBaseUrl}/api/admin/articles/${article.id}/rewrite`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ source_lang: sourceLang || article.language }),
        });

        if (!response.ok) {
          throw new Error(`Rewrite failed: ${response.statusText}`);
        }

        const data = await response.json();
        setArticle((prev) =>
          prev ? { ...prev, french_content_md: data.french_content_md } : null
        );
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Rewrite failed';
        setError(message);
        return false;
      } finally {
        setRewriting(false);
      }
    },
    [article]
  );

  const saveFrenchContent = useCallback(
    async (content: string, notes?: string) => {
      if (!article) return false;

      setLoading(true);
      setError(null);
      try {
        const apiBaseUrl = getApiBaseUrl();
        const response = await fetch(`${apiBaseUrl}/api/admin/articles/${article.id}/french-content`, {
          method: 'PUT',
          headers: getHeaders(),
          body: JSON.stringify({
            french_content_md: content,
            editorial_notes: notes,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to save French content: ${response.statusText}`);
        }

        const data = await response.json();
        setArticle((prev) =>
          prev
            ? {
                ...prev,
                french_content_md: data.french_content_md,
                editorial_notes: notes,
                editorial_status: 'rewritten',
              }
            : null
        );
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to save content';
        setError(message);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [article]
  );

  const validateArticle = useCallback(
    async (notes?: string) => {
      if (!article) return false;

      setValidating(true);
      setError(null);
      try {
        const apiBaseUrl = getApiBaseUrl();
        const response = await fetch(`${apiBaseUrl}/api/admin/articles/${article.id}/validate`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ approval_notes: notes }),
        });

        if (!response.ok) {
          throw new Error(`Validation failed: ${response.statusText}`);
        }

        const data = await response.json();
        setArticle((prev) =>
          prev
            ? {
                ...prev,
                editorial_status: 'validated',
                approval_notes: notes,
              }
            : null
        );
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Validation failed';
        setError(message);
        return false;
      } finally {
        setValidating(false);
      }
    },
    [article]
  );

  const publishArticle = useCallback(
    async (notes?: string) => {
      if (!article) return false;

      setPublishing(true);
      setError(null);
      try {
        const apiBaseUrl = getApiBaseUrl();
        const response = await fetch(`${apiBaseUrl}/api/admin/articles/${article.id}/publish-final`, {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ final_notes: notes }),
        });

        if (!response.ok) {
          throw new Error(`Publication failed: ${response.statusText}`);
        }

        const data = await response.json();
        setArticle((prev) =>
          prev
            ? {
                ...prev,
                editorial_status: 'published',
              }
            : null
        );
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Publication failed';
        setError(message);
        return false;
      } finally {
        setPublishing(false);
      }
    },
    [article]
  );

  const currentStep = article ? mapStatusToStep(article.editorial_status) : 1;

  return {
    article,
    loading,
    error,
    currentStep,
    rewriting,
    validating,
    publishing,
    fetchArticle,
    triggerRewrite,
    saveFrenchContent,
    validateArticle,
    publishArticle,
  };
}
