'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  ChevronDown,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
  Building2,
  Landmark,
  FileText,
  Zap,
  Globe,
} from 'lucide-react';

import {
  getLiveNews,
  getCentralBankRates,
  getImpactColor,
  formatTimeAgo,
  type LiveNewsItem,
} from '@/lib/api-wealth';
import type { CentralBankRate } from '@/types/wealth-agent';

// Use LiveNewsItem as PulseItem for this page
type PulseItem = LiveNewsItem;

// =============================================================================
// Sub-Components
// =============================================================================

function RateCard({ rate }: { rate: CentralBankRate }) {
  const trendIcon = {
    up: <TrendingUp size={16} className="text-red-400" />,
    down: <TrendingDown size={16} className="text-green-400" />,
    stable: <Minus size={16} className="text-slate-400" />,
  }[rate.trend];

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{rate.bank}</span>
        {trendIcon}
      </div>
      <p className="text-2xl font-semibold tabular-nums">{rate.rate.toFixed(2)}%</p>
      <p className="text-xs text-slate-500 mt-1">{rate.bank_full_name}</p>
      {rate.next_decision_date && (
        <p className="text-xs text-slate-400 mt-2">
          Prochaine décision: {new Date(rate.next_decision_date).toLocaleDateString('fr-FR')}
        </p>
      )}
    </div>
  );
}

function CategoryIcon({ category }: { category: string }) {
  const icons: Record<string, React.ReactNode> = {
    regulation: <FileText size={16} className="text-purple-400" />,
    rates: <Landmark size={16} className="text-blue-400" />,
    market: <TrendingUp size={16} className="text-emerald-400" />,
    local: <Globe size={16} className="text-cyan-400" />,
    fiscal: <Building2 size={16} className="text-amber-400" />,
    energy: <Zap size={16} className="text-yellow-400" />,
  };
  return icons[category] || <Bell size={16} className="text-slate-400" />;
}

function ImpactBadge({ level, type }: { level: string; type: string }) {
  const levelConfig: Record<string, { bg: string; text: string }> = {
    critical: { bg: 'bg-red-500/20', text: 'text-red-400' },
    high: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
    medium: { bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
    low: { bg: 'bg-green-500/20', text: 'text-green-400' },
    info: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  };
  
  const typeIcons: Record<string, React.ReactNode> = {
    positive: <TrendingUp size={12} />,
    negative: <TrendingDown size={12} />,
    neutral: <Minus size={12} />,
    mixed: <AlertTriangle size={12} />,
  };
  
  const { bg, text } = levelConfig[level] || levelConfig.info;
  
  return (
    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full ${bg} ${text} text-xs font-medium`}>
      {typeIcons[type]}
      <span className="capitalize">{level}</span>
    </div>
  );
}

function PulseItemCard({
  item,
  onSelect,
}: {
  item: PulseItem;
  onSelect: () => void;
}) {
  const categoryLabels: Record<string, string> = {
    regulation: 'Réglementation',
    rates: 'Taux',
    market: 'Marché',
    local: 'Local',
    fiscal: 'Fiscalité',
    energy: 'Énergie',
  };

  const isHighPriority = item.impact_level === 'critical' || item.impact_level === 'high';

  return (
    <div 
      className="bg-slate-900/50 border border-slate-800 hover:border-slate-700 rounded-xl p-5 cursor-pointer transition-all"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2">
          <CategoryIcon category={item.category} />
          <span className="text-xs text-slate-500 uppercase font-medium">
            {categoryLabels[item.category] || item.category}
          </span>
        </div>
        <span className="text-xs text-slate-500">{formatTimeAgo(item.published_at)}</span>
      </div>
      
      <h3 className="font-medium mb-2 line-clamp-2">{item.title}</h3>
      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{item.summary}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ImpactBadge level={item.impact_level} type={item.impact_type} />
          {item.countries_affected && item.countries_affected.length > 0 && (
            <span className="text-xs text-slate-500">
              {item.countries_affected.slice(0, 3).join(', ')}
              {item.countries_affected.length > 3 && '...'}
            </span>
          )}
        </div>
        
        {isHighPriority && (
          <span className="text-xs text-orange-400 flex items-center gap-1">
            <AlertTriangle size={12} />
            Priorité
          </span>
        )}
      </div>
      
      {/* Source indicator */}
      <div className="mt-3 pt-3 border-t border-slate-800/50">
        <span className="text-xs text-slate-600">{item.source}</span>
      </div>
    </div>
  );
}

function PulseDetailModal({
  item,
  onClose,
}: {
  item: PulseItem;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div 
        className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-2">
              <CategoryIcon category={item.category} />
              <ImpactBadge level={item.impact_level} type={item.impact_type} />
            </div>
            <button onClick={onClose} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
          
          <h2 className="text-xl font-semibold mb-2">{item.title}</h2>
          <p className="text-sm text-slate-500 mb-4">
            {new Date(item.published_at).toLocaleDateString('fr-FR', {
              day: 'numeric',
              month: 'long',
              year: 'numeric',
            })} • {item.source}
          </p>
          
          {/* Content */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase mb-2">Résumé</h3>
              <p className="text-slate-300">{item.summary}</p>
            </div>
            
            {item.content && (
              <div className="p-4 bg-slate-800/50 rounded-lg">
                <h3 className="text-sm font-semibold text-slate-400 uppercase mb-2">Contenu</h3>
                <p className="text-slate-300 text-sm">{item.content}</p>
              </div>
            )}
            
            {/* Keywords */}
            {item.keywords && item.keywords.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase mb-2">Mots-clés</h3>
                <div className="flex flex-wrap gap-2">
                  {item.keywords.map((keyword, i) => (
                    <span 
                      key={i} 
                      className="px-2 py-1 bg-slate-800 text-slate-300 text-xs rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {/* Countries affected */}
            {item.countries_affected && item.countries_affected.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase mb-2">Pays concernés</h3>
                <div className="flex gap-2">
                  {item.countries_affected.map((country) => (
                    <span 
                      key={country} 
                      className="px-3 py-1.5 bg-indigo-500/20 text-indigo-400 text-sm rounded-lg font-medium"
                    >
                      {country}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* Footer */}
          {item.source_url && (
            <div className="mt-6 pt-4 border-t border-slate-800">
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300"
              >
                <ExternalLink size={14} />
                Voir la source originale
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Filter Options
// =============================================================================

const CATEGORY_OPTIONS = [
  { value: 'regulation', label: 'Réglementation' },
  { value: 'rates', label: 'Taux' },
  { value: 'market', label: 'Marché' },
  { value: 'local', label: 'Local' },
  { value: 'fiscal', label: 'Fiscalité' },
  { value: 'energy', label: 'Énergie' },
];

const IMPACT_OPTIONS = [
  { value: 'critical', label: 'Critique' },
  { value: 'high', label: 'Élevé' },
  { value: 'medium', label: 'Moyen' },
  { value: 'low', label: 'Faible' },
];

// =============================================================================
// Main Page
// =============================================================================

interface NewsSummary {
  total_items: number;
  action_required_count: number;
  by_category?: Record<string, number>;
  by_impact_level?: Record<string, number>;
  sources: string[];
  live: boolean;
}

export default function NewsPage() {
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<PulseItem[]>([]);
  const [summary, setSummary] = useState<NewsSummary | null>(null);
  const [rates, setRates] = useState<CentralBankRate[]>([]);
  const [selectedItem, setSelectedItem] = useState<PulseItem | null>(null);
  
  // Filters
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedImpacts, setSelectedImpacts] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch live news and central bank rates in parallel
        const [newsData, ratesData] = await Promise.all([
          getLiveNews({
            countries: ['FR', 'EU', 'US', 'UK'],
            categories: selectedCategories.length > 0 ? selectedCategories : undefined,
            limit: 30,
          }),
          getCentralBankRates(),
        ]);

        // Filter by impact level client-side (since live API doesn't support it)
        let filteredItems = newsData.items;
        if (selectedImpacts.length > 0) {
          filteredItems = filteredItems.filter(item => 
            selectedImpacts.includes(item.impact_level)
          );
        }

        setItems(filteredItems);
        
        // Build summary from items
        const categoryCounts: Record<string, number> = {};
        const impactCounts: Record<string, number> = {};
        let actionRequired = 0;
        
        for (const item of newsData.items) {
          categoryCounts[item.category] = (categoryCounts[item.category] || 0) + 1;
          impactCounts[item.impact_level] = (impactCounts[item.impact_level] || 0) + 1;
          if (item.impact_level === 'critical' || item.impact_level === 'high') {
            actionRequired++;
          }
        }
        
        setSummary({
          total_items: newsData.total,
          action_required_count: actionRequired,
          by_category: categoryCounts,
          by_impact_level: impactCounts,
          sources: newsData.sources,
          live: newsData.live,
        });
        
        setRates(ratesData);
      } catch (error) {
        console.error('Failed to fetch news:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [selectedCategories, selectedImpacts]);

  const toggleCategory = (cat: string) => {
    setSelectedCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const toggleImpact = (impact: string) => {
    setSelectedImpacts((prev) =>
      prev.includes(impact) ? prev.filter((i) => i !== impact) : [...prev, impact]
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Chargement des actualités...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 lg:p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-semibold flex items-center gap-3">
                <Bell className="text-indigo-400" size={28} />
                Actualités & Alertes
              </h1>
              {summary?.live && (
                <span className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/20 text-emerald-400 text-xs font-medium rounded-full">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  Live
                </span>
              )}
            </div>
            <p className="text-slate-400 text-sm">
              Veille réglementaire, macro-économique et marché
              {summary?.sources && summary.sources.length > 0 && (
                <span className="text-slate-500"> • Sources: {summary.sources.slice(0, 3).join(', ')}</span>
              )}
            </p>
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              showFilters || selectedCategories.length > 0 || selectedImpacts.length > 0
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <Filter size={16} />
            Filtres
            {(selectedCategories.length > 0 || selectedImpacts.length > 0) && (
              <span className="bg-indigo-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                {selectedCategories.length + selectedImpacts.length}
              </span>
            )}
            <ChevronDown size={14} className={showFilters ? 'rotate-180' : ''} />
          </button>
        </div>
      </header>

      {/* Central Bank Rates */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Taux Directeurs
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {rates.map((rate) => (
            <RateCard key={rate.bank} rate={rate} />
          ))}
        </div>
      </section>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Categories */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Catégories
              </label>
              <div className="flex flex-wrap gap-2">
                {CATEGORY_OPTIONS.map((cat) => (
                  <button
                    key={cat.value}
                    onClick={() => toggleCategory(cat.value)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      selectedCategories.includes(cat.value)
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50'
                        : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Impact Levels */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Niveau d'impact
              </label>
              <div className="flex flex-wrap gap-2">
                {IMPACT_OPTIONS.map((impact) => (
                  <button
                    key={impact.value}
                    onClick={() => toggleImpact(impact.value)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      selectedImpacts.includes(impact.value)
                        ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50'
                        : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    {impact.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Clear Filters */}
          {(selectedCategories.length > 0 || selectedImpacts.length > 0) && (
            <button
              onClick={() => {
                setSelectedCategories([]);
                setSelectedImpacts([]);
              }}
              className="mt-4 text-sm text-slate-400 hover:text-slate-300"
            >
              Effacer les filtres
            </button>
          )}
        </div>
      )}

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-semibold">{summary.total_items}</p>
            <p className="text-xs text-slate-500 uppercase">Actualités</p>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-center">
            <p className="text-2xl font-semibold text-red-400">{summary.action_required_count}</p>
            <p className="text-xs text-slate-500 uppercase">Actions requises</p>
          </div>
          <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 text-center">
            <p className="text-2xl font-semibold text-orange-400">
              {(summary.by_impact_level?.critical || 0) + (summary.by_impact_level?.high || 0)}
            </p>
            <p className="text-xs text-slate-500 uppercase">Priorité haute</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
            <p className="text-2xl font-semibold">
              {Object.keys(summary.by_category || {}).length}
            </p>
            <p className="text-xs text-slate-500 uppercase">Catégories</p>
          </div>
        </div>
      )}

      {/* News Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item) => (
          <PulseItemCard
            key={item.id}
            item={item}
            onSelect={() => setSelectedItem(item)}
          />
        ))}
      </div>

      {items.length === 0 && (
        <div className="text-center py-20">
          <Bell size={48} className="mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium mb-2">Aucune actualité</h3>
          <p className="text-slate-400 text-sm">
            Modifiez vos filtres pour voir plus de résultats
          </p>
        </div>
      )}

      {/* Detail Modal */}
      {selectedItem && (
        <PulseDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}
