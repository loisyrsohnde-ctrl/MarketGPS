'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  MapPin,
  Home,
  Ruler,
  Calendar,
  Zap,
  AlertTriangle,
  ExternalLink,
  Phone,
  Mail,
  CheckCircle,
  Clock,
  TrendingUp,
  Wallet,
  BarChart3,
  Eye,
  Building2,
} from 'lucide-react';

import { VisualInspectorResult } from '@/components/wealth';
import {
  getOpportunityDetail,
  analyzeImages,
  formatCurrency,
  getSignalIcon,
  getSignalLabel,
  getPriorityColor,
  getEnergyRatingColor,
  getScoreColor,
  formatTimeAgo,
} from '@/lib/api-wealth';
import type { Opportunity, VisualAnalysis } from '@/types/wealth-agent';

// =============================================================================
// Score Bar Component
// =============================================================================

function ScoreBar({ score, label, color }: { score: number; label: string; color?: string }) {
  const width = Math.min(100, Math.max(0, score));
  const barColor = color || (score >= 70 ? 'bg-emerald-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500');
  
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-500 uppercase w-16">{label}</span>
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColor} rounded-full transition-all`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="text-sm font-medium tabular-nums w-8">{score}</span>
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [loading, setLoading] = useState(true);
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [visualAnalysis, setVisualAnalysis] = useState<VisualAnalysis | null>(null);
  const [analyzingImages, setAnalyzingImages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getOpportunityDetail(id);
        setOpportunity(data);
      } catch (err) {
        console.error('Failed to fetch opportunity:', err);
        setError('Opportunité non trouvée');
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      fetchData();
    }
  }, [id]);

  const handleAnalyzeImages = async () => {
    if (!opportunity?.listing.images?.length) return;
    
    setAnalyzingImages(true);
    try {
      const analysis = await analyzeImages({
        image_urls: opportunity.listing.images.slice(0, 5),
        country: opportunity.listing.country,
        surface_m2: opportunity.listing.surface_m2,
        listed_price: opportunity.listing.price,
      });
      setVisualAnalysis(analysis);
    } catch (err) {
      console.error('Failed to analyze images:', err);
    } finally {
      setAnalyzingImages(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Chargement...</p>
        </div>
      </div>
    );
  }

  if (error || !opportunity) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <Home size={48} className="mx-auto text-slate-600 mb-4" />
          <h2 className="text-xl font-medium mb-2">{error || 'Opportunité non trouvée'}</h2>
          <button
            onClick={() => router.push('/dashboard/wealth/opportunities')}
            className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
          >
            Retour aux opportunités
          </button>
        </div>
      </div>
    );
  }

  const { listing, signals, market_stats } = opportunity;
  const currency = listing.currency || 'EUR';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 lg:p-8">
      {/* Back Button */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
      >
        <ArrowLeft size={18} />
        Retour
      </button>

      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold mb-2">{listing.title}</h1>
            <div className="flex items-center gap-2 text-slate-400">
              <MapPin size={16} />
              <span>{listing.city}, {listing.country}</span>
              {listing.neighborhood && (
                <>
                  <span>•</span>
                  <span>{listing.neighborhood}</span>
                </>
              )}
            </div>
          </div>
          
          <div className="text-right">
            <p className="text-3xl font-semibold">{formatCurrency(listing.price, currency)}</p>
            <p className="text-slate-400">{listing.price_per_m2?.toLocaleString()} €/m²</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Image Gallery Placeholder */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="h-64 bg-slate-800 flex items-center justify-center">
              {listing.images?.[0] ? (
                <img 
                  src={listing.images[0]} 
                  alt={listing.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center">
                  <Building2 size={48} className="mx-auto text-slate-600 mb-2" />
                  <p className="text-slate-500">Aucune image disponible</p>
                </div>
              )}
            </div>
            
            {/* Visual Inspector Button */}
            <div className="p-4 border-t border-slate-800">
              <button
                onClick={handleAnalyzeImages}
                disabled={analyzingImages || !listing.images?.length}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {analyzingImages ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white/30 border-t-white rounded-full" />
                    Analyse en cours...
                  </>
                ) : (
                  <>
                    <Eye size={18} />
                    Lancer l'Inspecteur Visuel IA
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Visual Analysis Results */}
          {visualAnalysis && (
            <VisualInspectorResult analysis={visualAnalysis} currency={currency} />
          )}

          {/* Signals */}
          {signals.length > 0 && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Zap size={20} className="text-amber-400" />
                Signaux détectés
              </h2>
              <div className="space-y-4">
                {signals.map((signal) => (
                  <div key={signal.id} className="p-4 bg-slate-800/50 rounded-xl">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getSignalIcon(signal.signal_type)}</span>
                        <span className="font-medium">{getSignalLabel(signal.signal_type)}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getPriorityColor(signal.priority)} text-white`}>
                          {signal.priority}
                        </span>
                      </div>
                      {signal.score_delta && (
                        <span className={`text-sm font-medium ${signal.score_delta > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {signal.score_delta > 0 ? '+' : ''}{signal.score_delta} pts
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm text-slate-300 mb-3">{signal.summary_long}</p>
                    
                    {/* Evidence */}
                    {signal.evidence?.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-slate-500 uppercase mb-2">Preuves</p>
                        <ul className="space-y-1">
                          {signal.evidence.map((e, i) => (
                            <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                              <CheckCircle size={12} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                              {e}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* Risks */}
                    {signal.risks?.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs text-slate-500 uppercase mb-2">Risques</p>
                        <ul className="space-y-1">
                          {signal.risks.map((r, i) => (
                            <li key={i} className="text-xs text-orange-400 flex items-start gap-2">
                              <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" />
                              {r}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* Next Steps */}
                    {signal.next_steps?.length > 0 && (
                      <div>
                        <p className="text-xs text-slate-500 uppercase mb-2">Prochaines étapes</p>
                        <ul className="space-y-1">
                          {signal.next_steps.map((s, i) => (
                            <li key={i} className="text-xs text-indigo-400 flex items-start gap-2">
                              <span className="font-medium">{i + 1}.</span>
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {listing.description && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-medium mb-4">Description</h2>
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                {listing.description}
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-lg font-medium mb-4">Caractéristiques</h2>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <Ruler size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="text-lg font-semibold">{listing.surface_m2} m²</p>
                <p className="text-xs text-slate-500">Surface</p>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <Home size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="text-lg font-semibold">{listing.rooms || '—'}</p>
                <p className="text-xs text-slate-500">Pièces</p>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <Calendar size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="text-lg font-semibold">{listing.construction_year || '—'}</p>
                <p className="text-xs text-slate-500">Construction</p>
              </div>
              <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                <Clock size={20} className="mx-auto text-slate-400 mb-1" />
                <p className="text-lg font-semibold">{listing.days_on_market}j</p>
                <p className="text-xs text-slate-500">Sur marché</p>
              </div>
            </div>

            {/* Energy Rating */}
            {listing.energy_rating && (
              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg mb-4">
                <span className="text-sm text-slate-400">DPE</span>
                <div className={`w-10 h-10 ${getEnergyRatingColor(listing.energy_rating)} rounded-lg flex items-center justify-center font-bold text-white`}>
                  {listing.energy_rating}
                </div>
              </div>
            )}

            {/* Rental Info */}
            {listing.current_rent_monthly && (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400">Loyer mensuel</span>
                  <span className="font-semibold">{formatCurrency(listing.current_rent_monthly, currency)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-400">Rendement brut</span>
                  <span className="font-semibold text-emerald-400">{listing.rental_yield_gross?.toFixed(1)}%</span>
                </div>
              </div>
            )}
          </div>

          {/* ProphetIA Score */}
          {listing.prophetia_score && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
                <BarChart3 size={20} className="text-indigo-400" />
                Score ProphetIA
              </h2>
              
              <div className="text-center mb-6">
                <div className={`text-5xl font-bold ${getScoreColor(listing.prophetia_score)}`}>
                  {listing.prophetia_score}
                </div>
                <p className="text-sm text-slate-400 mt-1">/100</p>
              </div>
              
              <div className="space-y-3">
                <ScoreBar score={listing.prophetia_yield || 0} label="Yield" color="bg-emerald-500" />
                <ScoreBar score={listing.prophetia_safety || 0} label="Sécurité" color="bg-blue-500" />
                <ScoreBar score={listing.prophetia_growth || 0} label="Croissance" color="bg-purple-500" />
                <ScoreBar score={listing.prophetia_legal || 0} label="Légal" color="bg-amber-500" />
              </div>
            </div>
          )}

          {/* Market Stats */}
          {market_stats && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-lg font-medium mb-4">Marché Local</h2>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Prix médian/m²</span>
                  <span className="font-medium">{formatCurrency(market_stats.median_price_per_m2, currency)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Yield moyen</span>
                  <span className="font-medium">{market_stats.avg_yield_gross?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Durée moyenne vente</span>
                  <span className="font-medium">{market_stats.avg_days_on_market}j</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-slate-400">Écart vs médiane</span>
                  <span className={`font-medium ${
                    listing.price_per_m2 < market_stats.median_price_per_m2 ? 'text-emerald-400' : 'text-orange-400'
                  }`}>
                    {((listing.price_per_m2 - market_stats.median_price_per_m2) / market_stats.median_price_per_m2 * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-3">
            {listing.url && (
              <a
                href={listing.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
              >
                <ExternalLink size={18} />
                Voir l'annonce originale
              </a>
            )}
            
            <button
              onClick={() => router.push('/dashboard/wealth/analyze')}
              className="w-full py-3 bg-slate-800 hover:bg-slate-700 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
            >
              <TrendingUp size={18} />
              Simulation fiscale
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
