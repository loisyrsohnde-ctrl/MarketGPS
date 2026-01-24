'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getApiBaseUrl } from '@/lib/config';
import { motion } from 'framer-motion';
import { Newspaper, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { NewsGrid } from '@/components/news/NewsGrid';

// Region configuration with countries
const REGIONS: Record<string, { label: string, countries: string[] }> = {
  'cemac': { 
    label: 'CEMAC (Afrique Centrale)', 
    countries: ['CM', 'GA', 'CG', 'TD', 'CF', 'GQ'] 
  },
  'uemoa': { 
    label: 'UEMOA (Afrique de l\'Ouest)', 
    countries: ['SN', 'CI', 'BF', 'ML', 'NE', 'TG', 'BJ', 'GW'] 
  },
  'north-africa': { 
    label: 'Afrique du Nord', 
    countries: ['MA', 'DZ', 'TN', 'EG', 'LY'] 
  },
  'east-africa': { 
    label: 'Afrique de l\'Est', 
    countries: ['KE', 'TZ', 'UG', 'RW', 'ET'] 
  },
  'southern-africa': { 
    label: 'Afrique Australe', 
    countries: ['ZA', 'AO', 'MZ', 'ZW', 'NA'] 
  },
  'nigeria': { 
    label: 'Nigeria', 
    countries: ['NG'] 
  }
};

// Country names mapping
const COUNTRY_NAMES: Record<string, string> = {
  'CM': 'Cameroun', 'GA': 'Gabon', 'CG': 'Congo', 'SN': 'Sénégal',
  'CI': 'Côte d\'Ivoire', 'MA': 'Maroc', 'DZ': 'Algérie', 'TN': 'Tunisie',
  'EG': 'Égypte', 'KE': 'Kenya', 'ZA': 'Afrique du Sud', 'NG': 'Nigeria',
  'RW': 'Rwanda'
};

export default function RegionNewsPage() {
  const params = useParams();
  const regionKey = params.region as string; // 'cemac', 'uemoa', etc.
  const regionConfig = REGIONS[regionKey];

  const { data: articles, isLoading } = useQuery({
    queryKey: ['news', regionKey],
    queryFn: async () => {
      const API_BASE = getApiBaseUrl();
      const countryList = regionConfig?.countries.join(',');
      // Fetch news filtered by these countries
      const res = await fetch(`${API_BASE}/api/news?countries=${countryList}&limit=30`);
      if (!res.ok) throw new Error('Failed to fetch news');
      return res.json();
    },
    enabled: !!regionConfig
  });

  if (!regionConfig) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh]">
        <h1 className="text-2xl font-bold text-text-primary">Région non trouvée</h1>
        <Link href="/news" className="mt-4 text-accent hover:underline">Retour aux actualités</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href="/news" className="inline-flex items-center text-sm text-text-secondary hover:text-accent mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour au fil d'actualité
        </Link>
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-accent/10 text-accent">
            <Newspaper className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text-primary">{regionConfig.label}</h1>
            <p className="text-text-secondary mt-1">
              Actualités économiques et business : {regionConfig.countries.map(c => COUNTRY_NAMES[c] || c).join(', ')}
            </p>
          </div>
        </div>
      </div>

      {/* Country Filter Tabs */}
      <div className="flex flex-wrap gap-2 mb-8 border-b border-glass-border pb-4">
        <Link 
          href={`/news/${regionKey}`}
          className="px-4 py-2 rounded-full bg-accent text-white text-sm font-medium"
        >
          Tout voir
        </Link>
        {regionConfig.countries.map(countryCode => (
           COUNTRY_NAMES[countryCode] && (
            <Link
              key={countryCode}
              href={`/news/${regionKey}/${countryCode.toLowerCase()}`}
              className="px-4 py-2 rounded-full bg-surface hover:bg-surface-hover text-text-secondary hover:text-text-primary text-sm transition-all border border-glass-border"
            >
              {COUNTRY_NAMES[countryCode]}
            </Link>
          )
        ))}
      </div>

      {/* News Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
           {[1, 2, 3, 4, 5, 6].map((i) => (
             <div key={i} className="h-80 bg-surface/50 rounded-2xl animate-pulse" />
           ))}
        </div>
      ) : (
        <NewsGrid articles={articles || []} />
      )}
    </div>
  );
}
