import { useEffect, useState } from 'react';
import { NewsSource } from '@/types/admin';
import { getApiBaseUrl } from '@/lib/config';

const API_BASE = getApiBaseUrl();

// Static fallback data from sources_registry.json
const DEFAULT_SOURCES: NewsSource[] = [
  {
    name: 'African Business',
    url: 'https://african.business',
    rss_url: 'https://african.business/feed/',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'en',
    tags: ['business', 'vc', 'fintech'],
    trust_score: 0.9,
    enabled: true,
  },
  {
    name: 'The Africa Report',
    url: 'https://www.theafricareport.com',
    rss_url: 'https://www.theafricareport.com/feed/',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'en',
    tags: ['business', 'economy', 'fintech'],
    trust_score: 0.9,
    enabled: true,
  },
  {
    name: 'Jeune Afrique',
    url: 'https://www.jeuneafrique.com',
    rss_url: 'https://www.jeuneafrique.com/feed/',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'fr',
    tags: ['business', 'politics', 'economy'],
    trust_score: 0.95,
    enabled: true,
  },
  {
    name: 'Agence Ecofin',
    url: 'https://www.agenceecofin.com',
    rss_url: 'https://www.agenceecofin.com/a-la-une/rss',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'fr',
    tags: ['fintech', 'banking', 'telecom'],
    trust_score: 0.9,
    enabled: true,
  },
  {
    name: 'Financial Afrik',
    url: 'https://www.financialafrik.com',
    rss_url: 'https://www.financialafrik.com/feed/',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'fr',
    tags: ['fintech', 'banking', 'markets'],
    trust_score: 0.9,
    enabled: true,
  },
  {
    name: 'Disrupt Africa',
    url: 'https://disrupt-africa.com',
    rss_url: 'https://disrupt-africa.com/feed/',
    type: 'rss',
    country: null,
    region: 'PAN',
    language: 'en',
    tags: ['startup', 'vc', 'funding'],
    trust_score: 0.9,
    enabled: true,
  },
  {
    name: 'TechCabal',
    url: 'https://techcabal.com',
    rss_url: 'https://techcabal.com/feed/',
    type: 'rss',
    country: null,
    region: 'WEST',
    language: 'en',
    tags: ['tech', 'startup', 'innovation'],
    trust_score: 0.85,
    enabled: true,
  },
  {
    name: 'Zawya',
    url: 'https://www.zawya.com',
    rss_url: 'https://www.zawya.com/rss/',
    type: 'rss',
    country: null,
    region: 'NORTH',
    language: 'en',
    tags: ['finance', 'markets', 'economy'],
    trust_score: 0.88,
    enabled: true,
  },
  {
    name: 'Business Insider Africa',
    url: 'https://www.businessinsiderafrica.com',
    rss_url: 'https://www.businessinsiderafrica.com/feed/',
    type: 'rss',
    country: null,
    region: 'SOUTH',
    language: 'en',
    tags: ['business', 'markets', 'economy'],
    trust_score: 0.92,
    enabled: true,
  },
];

interface UseNewsSourcesResult {
  sources: NewsSource[];
  loading: boolean;
  error: string | null;
  toggleSource: (name: string) => Promise<void>;
  updateSource: (name: string, updates: Partial<NewsSource>) => Promise<void>;
  refetch: () => Promise<void>;
}

export function useNewsSources(): UseNewsSourcesResult {
  const [sources, setSources] = useState<NewsSource[]>(DEFAULT_SOURCES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const adminKey = localStorage.getItem('adminKey') || '';

      try {
        const response = await fetch(`${API_BASE}/api/admin/sources`, {
          headers: { 'X-Admin-Key': adminKey },
        });

        if (response.ok) {
          const data = await response.json();
          setSources(data.sources || DEFAULT_SOURCES);
          setError(null);
          return;
        }
      } catch (fetchErr) {
        console.warn('Could not fetch sources from API, using defaults', fetchErr);
      }

      // Fallback to defaults
      setSources(DEFAULT_SOURCES);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
      setSources(DEFAULT_SOURCES);
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = async (name: string) => {
    try {
      const source = sources.find((s) => s.name === name);
      if (!source) return;

      const updated = { ...source, enabled: !source.enabled };
      const adminKey = localStorage.getItem('adminKey') || '';

      const response = await fetch(`${API_BASE}/api/admin/sources/${name}`, {
        method: 'PATCH',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updated),
      });

      if (response.ok) {
        setSources((prev) =>
          prev.map((s) => (s.name === name ? updated : s))
        );
      }
    } catch (err) {
      console.error('Failed to toggle source:', err);
    }
  };

  const updateSource = async (name: string, updates: Partial<NewsSource>) => {
    try {
      const source = sources.find((s) => s.name === name);
      if (!source) return;

      const updated = { ...source, ...updates };
      const adminKey = localStorage.getItem('adminKey') || '';

      const response = await fetch(`${API_BASE}/api/admin/sources/${name}`, {
        method: 'PATCH',
        headers: {
          'X-Admin-Key': adminKey,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updated),
      });

      if (response.ok) {
        setSources((prev) =>
          prev.map((s) => (s.name === name ? updated : s))
        );
      }
    } catch (err) {
      console.error('Failed to update source:', err);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  return {
    sources,
    loading,
    error,
    toggleSource,
    updateSource,
    refetch: fetchSources,
  };
}
