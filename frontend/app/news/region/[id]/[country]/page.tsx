'use client';

import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { getApiBaseUrl } from '@/lib/config';
import { Newspaper, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const COUNTRY_NAMES: Record<string, string> = {
  'cm': 'Cameroun', 'ga': 'Gabon', 'cg': 'Congo', 'td': 'Tchad',
  'cf': 'Centrafrique', 'gq': 'Guinée équatoriale',
  'sn': 'Sénégal', 'ci': 'Côte d\'Ivoire', 'bf': 'Burkina Faso',
  'ml': 'Mali', 'ne': 'Niger', 'tg': 'Togo', 'bj': 'Bénin',
  'ma': 'Maroc', 'dz': 'Algérie', 'tn': 'Tunisie', 'eg': 'Égypte', 'ly': 'Libye',
  'ke': 'Kenya', 'tz': 'Tanzanie', 'ug': 'Ouganda', 'rw': 'Rwanda', 'et': 'Éthiopie',
  'za': 'Afrique du Sud', 'ao': 'Angola', 'mz': 'Mozambique', 'zw': 'Zimbabwe', 'na': 'Namibie',
  'ng': 'Nigeria',
};

const COUNTRY_FLAGS: Record<string, string> = {
  'ng': '🇳🇬', 'cm': '🇨🇲', 'sn': '🇸🇳', 'ci': '🇨🇮', 'za': '🇿🇦',
  'ke': '🇰🇪', 'ma': '🇲🇦', 'eg': '🇪🇬', 'ga': '🇬🇦', 'rw': '🇷🇼',
  'gh': '🇬🇭', 'tz': '🇹🇿', 'et': '🇪🇹', 'dz': '🇩🇿', 'tn': '🇹🇳',
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
                <span>{new Date(article.published_at).toLocaleDateString('fr-FR', { timeZone: 'UTC' })}</span>
              </>
            )}
          </div>
        </div>
      </article>
    </Link>
  );
}

export default function CountryPage() {
  const params = useParams();
  const regionId = params.id as string;
  const countryCode = (params.country as string).toLowerCase();
  const countryName = COUNTRY_NAMES[countryCode] || countryCode.toUpperCase();
  const countryFlag = COUNTRY_FLAGS[countryCode] || '🌍';

  const { data: articles, isLoading } = useQuery({
    queryKey: ['news', 'country', countryCode],
    queryFn: async () => {
      const API_BASE = getApiBaseUrl();
      const res = await fetch(`${API_BASE}/api/news?country=${countryCode.toUpperCase()}&page_size=30`);
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      return data.data || data || [];
    }
  });

  return (
    <div className="min-h-screen bg-zinc-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link href={`/news/region/${regionId}`} className="inline-flex items-center text-sm text-slate-500 hover:text-blue-600 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour à la région
          </Link>
          
          <div className="flex items-center gap-4">
            <span className="text-5xl">{countryFlag}</span>
            <div>
              <h1 className="text-4xl font-serif font-bold text-slate-900">{countryName}</h1>
              <p className="text-lg text-slate-600">Actualités économiques et business</p>
            </div>
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
            <h3 className="text-xl font-medium text-slate-600 mb-2">Aucun article pour {countryName}</h3>
            <p className="text-slate-500">Revenez plus tard pour de nouvelles actualités.</p>
          </div>
        )}
      </div>
    </div>
  );
}
