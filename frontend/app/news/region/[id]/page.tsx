'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getApiBaseUrl } from '@/lib/config';
import { Newspaper, ArrowLeft, ChevronRight } from 'lucide-react';
import Link from 'next/link';

// Region configuration with countries
const REGIONS: Record<string, { label: string; description: string; countries: { code: string; name: string }[] }> = {
  'cemac': {
    label: 'CEMAC',
    description: 'Communauté Économique et Monétaire de l\'Afrique Centrale',
    countries: [
      { code: 'CM', name: 'Cameroun' },
      { code: 'GA', name: 'Gabon' },
      { code: 'CG', name: 'Congo' },
      { code: 'TD', name: 'Tchad' },
      { code: 'CF', name: 'Centrafrique' },
      { code: 'GQ', name: 'Guinée équatoriale' },
    ]
  },
  'uemoa': {
    label: 'UEMOA',
    description: 'Union Économique et Monétaire Ouest-Africaine',
    countries: [
      { code: 'SN', name: 'Sénégal' },
      { code: 'CI', name: 'Côte d\'Ivoire' },
      { code: 'BF', name: 'Burkina Faso' },
      { code: 'ML', name: 'Mali' },
      { code: 'NE', name: 'Niger' },
      { code: 'TG', name: 'Togo' },
      { code: 'BJ', name: 'Bénin' },
    ]
  },
  'north-africa': {
    label: 'Afrique du Nord',
    description: 'Maghreb & Égypte',
    countries: [
      { code: 'MA', name: 'Maroc' },
      { code: 'DZ', name: 'Algérie' },
      { code: 'TN', name: 'Tunisie' },
      { code: 'EG', name: 'Égypte' },
      { code: 'LY', name: 'Libye' },
    ]
  },
  'east-africa': {
    label: 'Afrique de l\'Est',
    description: 'Communauté d\'Afrique de l\'Est',
    countries: [
      { code: 'KE', name: 'Kenya' },
      { code: 'TZ', name: 'Tanzanie' },
      { code: 'UG', name: 'Ouganda' },
      { code: 'RW', name: 'Rwanda' },
      { code: 'ET', name: 'Éthiopie' },
    ]
  },
  'southern-africa': {
    label: 'Afrique Australe',
    description: 'SADC - Communauté de développement d\'Afrique australe',
    countries: [
      { code: 'ZA', name: 'Afrique du Sud' },
      { code: 'AO', name: 'Angola' },
      { code: 'MZ', name: 'Mozambique' },
      { code: 'ZW', name: 'Zimbabwe' },
      { code: 'NA', name: 'Namibie' },
    ]
  },
  'nigeria': {
    label: 'Nigeria',
    description: 'La première économie d\'Afrique',
    countries: [
      { code: 'NG', name: 'Nigeria' },
    ]
  }
};

// Simple Article Card
function ArticleCard({ article }: { article: any }) {
  return (
    <Link href={`/news/${article.slug}`} className="block group">
      <article className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
        <div className="aspect-[16/10] overflow-hidden bg-slate-100">
          {article.image_url ? (
            <img src={article.image_url} alt="" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Newspaper className="w-12 h-12 text-slate-300" />
            </div>
          )}
        </div>
        <div className="p-4">
          <span className="inline-block px-2 py-0.5 text-[10px] font-semibold uppercase bg-blue-600 text-white rounded mb-2">
            {article.category || 'Actualité'}
          </span>
          <h3 className="font-serif text-lg font-bold text-slate-900 group-hover:text-blue-700 transition-colors line-clamp-2 mb-2">
            {article.title}
          </h3>
          {article.excerpt && (
            <p className="text-sm text-slate-600 line-clamp-2 mb-3">{article.excerpt}</p>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>{article.source_name}</span>
            {article.published_at && (
              <>
                <span>•</span>
                <span>{new Date(article.published_at).toLocaleDateString('fr-FR')}</span>
              </>
            )}
          </div>
        </div>
      </article>
    </Link>
  );
}

export default function RegionPage() {
  const params = useParams();
  const regionId = params.id as string;
  const region = REGIONS[regionId];

  const countryCodes = region?.countries.map(c => c.code).join(',') || '';

  const { data: articles, isLoading } = useQuery({
    queryKey: ['news', 'region', regionId],
    queryFn: async () => {
      const API_BASE = getApiBaseUrl();
      const res = await fetch(`${API_BASE}/api/news?countries=${countryCodes}&limit=30`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      return data.data || data || [];
    },
    enabled: !!region
  });

  if (!region) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">Région non trouvée</h1>
        <Link href="/news" className="text-blue-600 hover:underline">← Retour aux actualités</Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href="/news" className="inline-flex items-center text-sm text-slate-500 hover:text-blue-600 mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour aux actualités
        </Link>
        
        <h1 className="text-4xl font-serif font-bold text-slate-900 mb-2">{region.label}</h1>
        <p className="text-lg text-slate-600">{region.description}</p>
      </div>

      {/* Country Tabs */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4">Filtrer par pays</h2>
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/news/region/${regionId}`}
            className="px-4 py-2 bg-blue-600 text-white rounded-full text-sm font-medium"
          >
            Tous les pays
          </Link>
          {region.countries.map(country => (
            <Link
              key={country.code}
              href={`/news/region/${regionId}/${country.code.toLowerCase()}`}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-full text-sm font-medium transition-colors"
            >
              {country.name}
            </Link>
          ))}
        </div>
      </div>

      {/* Articles Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-80 bg-slate-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : articles && articles.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map((article: any) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <Newspaper className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-slate-600 mb-2">Aucun article pour cette région</h3>
          <p className="text-slate-500">Revenez plus tard pour de nouvelles actualités.</p>
        </div>
      )}
    </div>
  );
}
