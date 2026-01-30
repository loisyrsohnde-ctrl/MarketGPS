'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  Target,
  Filter,
  Search,
  ChevronDown,
  Grid,
  List,
  Zap,
  MapPin,
  X,
} from 'lucide-react';

import { OpportunityCard } from '@/components/wealth';
import {
  getOpportunities,
  getOpportunitiesSummary,
  formatCurrency,
  getSignalIcon,
  getSignalLabel,
} from '@/lib/api-wealth';
import type { Opportunity, OpportunitySummary } from '@/types/wealth-agent';

// =============================================================================
// Filter Options
// =============================================================================

const COUNTRY_OPTIONS = [
  { code: 'FR', name: 'France', flag: '🇫🇷' },
  { code: 'BE', name: 'Belgique', flag: '🇧🇪' },
  { code: 'DE', name: 'Allemagne', flag: '🇩🇪' },
  { code: 'UK', name: 'Royaume-Uni', flag: '🇬🇧' },
  { code: 'US', name: 'États-Unis', flag: '🇺🇸' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
];

const PRICE_RANGES = [
  { label: 'Tout', min: undefined, max: undefined },
  { label: '< 150k€', min: undefined, max: 150000 },
  { label: '150k - 300k€', min: 150000, max: 300000 },
  { label: '300k - 500k€', min: 300000, max: 500000 },
  { label: '> 500k€', min: 500000, max: undefined },
];

// =============================================================================
// Components
// =============================================================================

function FilterButton({
  label,
  active,
  onClick,
  icon,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  icon?: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
        active
          ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50'
          : 'bg-slate-800 text-slate-400 border border-slate-700 hover:border-slate-600'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function SignalFilterChip({
  type,
  count,
  active,
  onClick,
}: {
  type: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-2 rounded-lg text-sm transition-all flex items-center gap-2 ${
        active
          ? 'bg-amber-500/20 border border-amber-500/50'
          : 'bg-slate-800/50 border border-slate-700 hover:border-slate-600'
      }`}
    >
      <span>{getSignalIcon(type)}</span>
      <span>{getSignalLabel(type)}</span>
      <span className="text-xs text-slate-500">({count})</span>
    </button>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function OpportunitiesPage() {
  const router = useRouter();
  
  // State
  const [loading, setLoading] = useState(true);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [summary, setSummary] = useState<OpportunitySummary | null>(null);
  
  // Filters
  const [selectedCountries, setSelectedCountries] = useState<string[]>(['FR', 'BE']);
  const [priceRange, setPriceRange] = useState<{ min?: number; max?: number }>({});
  const [yieldMin, setYieldMin] = useState<number | undefined>();
  const [scoreMin, setScoreMin] = useState<number | undefined>();
  const [signalsOnly, setSignalsOnly] = useState(false);
  const [selectedSignalType, setSelectedSignalType] = useState<string | null>(null);
  
  // View
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [showFilters, setShowFilters] = useState(false);

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const [oppData, summaryData] = await Promise.all([
          getOpportunities({
            countries: selectedCountries,
            price_min: priceRange.min,
            price_max: priceRange.max,
            yield_min: yieldMin,
            score_min: scoreMin,
            signals_only: signalsOnly,
            limit: 50,
          }),
          getOpportunitiesSummary(selectedCountries),
        ]);

        setOpportunities(oppData.opportunities);
        setSummary(summaryData);
      } catch (error) {
        console.error('Failed to fetch opportunities:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [selectedCountries, priceRange, yieldMin, scoreMin, signalsOnly]);

  // Filter by signal type
  const filteredOpportunities = useMemo(() => {
    if (!selectedSignalType) return opportunities;
    
    return opportunities.filter((opp) =>
      opp.signals.some((s) => s.signal_type === selectedSignalType)
    );
  }, [opportunities, selectedSignalType]);

  // Handlers
  const handleToggleCountry = (code: string) => {
    setSelectedCountries((prev) =>
      prev.includes(code)
        ? prev.filter((c) => c !== code)
        : [...prev, code]
    );
  };

  const handleSelectOpportunity = (id: string) => {
    router.push(`/dashboard/wealth/opportunities/${id}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 lg:p-8">
      {/* Header */}
      <header className="mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold flex items-center gap-3">
              <Target className="text-indigo-400" size={28} />
              Opportunités
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              {summary?.total_opportunities || 0} biens correspondant à vos critères
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                showFilters
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50'
                  : 'bg-slate-800 text-slate-400 border border-slate-700'
              }`}
            >
              <Filter size={16} />
              Filtres
              <ChevronDown size={14} className={showFilters ? 'rotate-180' : ''} />
            </button>
            
            <div className="flex items-center border border-slate-700 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-slate-700' : 'bg-slate-800 hover:bg-slate-750'}`}
              >
                <List size={18} />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-slate-700' : 'bg-slate-800 hover:bg-slate-750'}`}
              >
                <Grid size={18} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Countries */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Pays
              </label>
              <div className="flex flex-wrap gap-2">
                {COUNTRY_OPTIONS.map((c) => (
                  <FilterButton
                    key={c.code}
                    label={`${c.flag} ${c.code}`}
                    active={selectedCountries.includes(c.code)}
                    onClick={() => handleToggleCountry(c.code)}
                  />
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Budget
              </label>
              <div className="flex flex-wrap gap-2">
                {PRICE_RANGES.map((range) => (
                  <FilterButton
                    key={range.label}
                    label={range.label}
                    active={priceRange.min === range.min && priceRange.max === range.max}
                    onClick={() => setPriceRange({ min: range.min, max: range.max })}
                  />
                ))}
              </div>
            </div>

            {/* Yield Min */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Rendement min.
              </label>
              <div className="flex gap-2">
                {[undefined, 4, 5, 6].map((val) => (
                  <FilterButton
                    key={val ?? 'all'}
                    label={val ? `${val}%+` : 'Tout'}
                    active={yieldMin === val}
                    onClick={() => setYieldMin(val)}
                  />
                ))}
              </div>
            </div>

            {/* Score Min */}
            <div>
              <label className="text-xs text-slate-500 uppercase font-semibold mb-2 block">
                Score ProphetIA min.
              </label>
              <div className="flex gap-2">
                {[undefined, 60, 70, 80].map((val) => (
                  <FilterButton
                    key={val ?? 'all'}
                    label={val ? `${val}+` : 'Tout'}
                    active={scoreMin === val}
                    onClick={() => setScoreMin(val)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Signals Only Toggle */}
          <div className="mt-4 pt-4 border-t border-slate-800 flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={signalsOnly}
                onChange={(e) => setSignalsOnly(e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-indigo-500 focus:ring-indigo-500/50"
              />
              <span className="text-sm">Signaux uniquement</span>
            </label>
          </div>
        </div>
      )}

      {/* Signal Type Filter Chips */}
      {summary && Object.keys(summary.signals_by_type).length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={16} className="text-amber-400" />
            <span className="text-sm font-medium text-slate-400">Filtrer par signal</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <FilterButton
              label="Tous"
              active={!selectedSignalType}
              onClick={() => setSelectedSignalType(null)}
            />
            {Object.entries(summary.signals_by_type).map(([type, count]) => (
              <SignalFilterChip
                key={type}
                type={type}
                count={count}
                active={selectedSignalType === type}
                onClick={() => setSelectedSignalType(selectedSignalType === type ? null : type)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-slate-400">Recherche en cours...</p>
          </div>
        </div>
      ) : filteredOpportunities.length === 0 ? (
        <div className="text-center py-20">
          <Target size={48} className="mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium mb-2">Aucune opportunité trouvée</h3>
          <p className="text-slate-400 text-sm">
            Essayez d'élargir vos critères de recherche
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredOpportunities.map((opp) => (
            <OpportunityCard
              key={opp.listing.id}
              opportunity={opp}
              variant="full"
              onClick={() => handleSelectOpportunity(opp.listing.id)}
            />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredOpportunities.map((opp) => (
            <OpportunityCard
              key={opp.listing.id}
              opportunity={opp}
              variant="compact"
              onClick={() => handleSelectOpportunity(opp.listing.id)}
            />
          ))}
        </div>
      )}

      {/* Results Count */}
      {!loading && filteredOpportunities.length > 0 && (
        <div className="text-center text-sm text-slate-500 mt-6">
          {filteredOpportunities.length} résultat(s) affiché(s)
        </div>
      )}
    </div>
  );
}
