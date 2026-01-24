'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getApiBaseUrl } from '@/lib/config';
import { Newspaper, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { NewsGrid } from '@/components/news/NewsGrid';

const COUNTRY_NAMES: Record<string, string> = {
  'cm': 'Cameroun', 'ga': 'Gabon', 'cg': 'Congo', 'sn': 'Sénégal',
  'ci': 'Côte d\'Ivoire', 'ma': 'Maroc', 'dz': 'Algérie', 'tn': 'Tunisie',
  'eg': 'Égypte', 'ke': 'Kenya', 'za': 'Afrique du Sud', 'ng': 'Nigeria',
  'rw': 'Rwanda'
};

export default function CountryNewsPage() {
  const params = useParams();
  const regionKey = params.region as string;
  const countryKey = params.country as string;
  const countryName = COUNTRY_NAMES[countryKey] || countryKey.toUpperCase();
  const countryCode = countryKey.toUpperCase();

  const { data: articles, isLoading } = useQuery({
    queryKey: ['news', regionKey, countryKey],
    queryFn: async () => {
      const API_BASE = getApiBaseUrl();
      const res = await fetch(`${API_BASE}/api/news?countries=${countryCode}&limit=30`);
      if (!res.ok) throw new Error('Failed to fetch news');
      return res.json();
    }
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href={`/news/${regionKey}`} className="inline-flex items-center text-sm text-text-secondary hover:text-accent mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour à {regionKey.toUpperCase()}
        </Link>
        
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-accent/10 text-accent">
            <span className="text-2xl">
              {countryCode === 'NG' ? '🇳🇬' : 
               countryCode === 'CM' ? '🇨🇲' : 
               countryCode === 'SN' ? '🇸🇳' : 
               countryCode === 'CI' ? '🇨🇮' : 
               countryCode === 'ZA' ? '🇿🇦' : '🌍'}
            </span>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text-primary">Actualités : {countryName}</h1>
            <p className="text-text-secondary mt-1">
              Dernières nouvelles économiques et tech
            </p>
          </div>
        </div>
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
