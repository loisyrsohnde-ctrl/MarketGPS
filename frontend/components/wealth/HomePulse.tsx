'use client';

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Bell,
  Target,
  Zap,
  Building2,
  Globe,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Clock,
  Wallet,
  BarChart3,
  Eye,
} from 'lucide-react';

import type {
  GeoContext,
  MarketPulse,
  OpportunitySummary,
  PulseSummary,
  Opportunity,
  CentralBankRate,
} from '@/types/wealth-agent';
import {
  formatCurrency,
  formatPercent,
  getSignalIcon,
  getSignalLabel,
  getImpactColor,
  formatTimeAgo,
} from '@/lib/api-wealth';

// =============================================================================
// Types
// =============================================================================

interface HomePulseProps {
  geoContext?: GeoContext;
  opportunitySummary?: OpportunitySummary;
  pulseSummary?: PulseSummary;
  onNavigateOpportunities?: () => void;
  onNavigateAnalyze?: () => void;
  onNavigatePulse?: () => void;
  onSelectOpportunity?: (id: string) => void;
  isLoading?: boolean;
}

// =============================================================================
// Sub-Components
// =============================================================================

function RateBadge({ rate }: { rate: CentralBankRate }) {
  const trendIcon = {
    up: <TrendingUp size={12} className="text-red-400" />,
    down: <TrendingDown size={12} className="text-green-400" />,
    stable: <Minus size={12} className="text-slate-400" />,
  }[rate.trend];

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 flex items-center gap-3">
      <div className="flex-1">
        <p className="text-[10px] text-slate-500 uppercase font-semibold tracking-wider">
          {rate.bank}
        </p>
        <p className="text-lg font-medium tabular-nums">
          {rate.rate.toFixed(2)}%
        </p>
      </div>
      <div className="flex items-center gap-1">
        {trendIcon}
        {rate.change_amount !== 0 && (
          <span className={`text-xs ${rate.change_amount > 0 ? 'text-red-400' : 'text-green-400'}`}>
            {rate.change_amount > 0 ? '+' : ''}{(rate.change_amount * 100).toFixed(0)}bp
          </span>
        )}
      </div>
    </div>
  );
}

function MarketPulseCard({ pulse, currency }: { pulse: MarketPulse; currency: string }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe size={16} className="text-indigo-400" />
          <span className="text-sm font-medium">{pulse.city}, {pulse.country}</span>
        </div>
        <span className="text-[10px] text-slate-500 uppercase">Pulse Local</span>
      </div>
      
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-[10px] text-slate-500 uppercase mb-1">Prix/m²</p>
          <p className="text-sm font-medium tabular-nums">
            {formatCurrency(pulse.avg_price_per_m2, currency)}
          </p>
          <p className={`text-xs ${pulse.price_trend_yoy >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(pulse.price_trend_yoy)} /an
          </p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase mb-1">Loyer/m²</p>
          <p className="text-sm font-medium tabular-nums">
            {formatCurrency(pulse.avg_rent_per_m2, currency)}
          </p>
          <p className={`text-xs ${pulse.rent_trend_yoy >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(pulse.rent_trend_yoy)} /an
          </p>
        </div>
        <div>
          <p className="text-[10px] text-slate-500 uppercase mb-1">Yield Moyen</p>
          <p className="text-sm font-medium tabular-nums">
            {pulse.avg_yield.toFixed(1)}%
          </p>
          <p className="text-xs text-slate-400">
            ~{pulse.days_on_market_avg}j DOM
          </p>
        </div>
      </div>
    </div>
  );
}

function SignalCard({
  opportunity,
  onClick,
}: {
  opportunity: {
    listing: any;
    signal_count: number;
    top_signal: any;
  };
  onClick?: () => void;
}) {
  const { listing, top_signal } = opportunity;
  
  return (
    <div 
      className="bg-slate-800/40 hover:bg-slate-800/60 border border-slate-700 hover:border-slate-600 rounded-xl p-4 cursor-pointer transition-all group"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="text-sm font-medium">{listing.city}</p>
          <p className="text-xs text-slate-400">{listing.title?.slice(0, 40)}...</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold tabular-nums">
            {formatCurrency(listing.price, listing.currency)}
          </p>
          <p className="text-xs text-slate-400">{listing.surface_m2} m²</p>
        </div>
      </div>
      
      {top_signal && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">{getSignalIcon(top_signal.signal_type)}</span>
          <span className="text-xs text-slate-300">{top_signal.summary}</span>
        </div>
      )}
      
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <BarChart3 size={12} className="text-indigo-400" />
            <span className="text-xs font-medium">{listing.prophetia_score || '—'}</span>
          </div>
          {listing.rental_yield_gross && (
            <div className="flex items-center gap-1">
              <Wallet size={12} className="text-emerald-400" />
              <span className="text-xs font-medium">{listing.rental_yield_gross.toFixed(1)}%</span>
            </div>
          )}
        </div>
        <ChevronRight size={16} className="text-slate-500 group-hover:text-slate-300 transition-colors" />
      </div>
    </div>
  );
}

function PulseItemCard({
  item,
  onClick,
}: {
  item: any;
  onClick?: () => void;
}) {
  const iconMap: Record<string, React.ReactNode> = {
    critical: <AlertTriangle size={14} className="text-red-400" />,
    high: <AlertTriangle size={14} className="text-orange-400" />,
    medium: <Clock size={14} className="text-yellow-400" />,
    low: <CheckCircle size={14} className="text-green-400" />,
    info: <Bell size={14} className="text-blue-400" />,
  };

  return (
    <div 
      className="flex items-start gap-3 py-3 px-2 hover:bg-slate-800/30 rounded-lg cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="mt-0.5">{iconMap[item.impact_level] || iconMap.info}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{item.title}</p>
        <p className="text-xs text-slate-400 line-clamp-2">{item.summary}</p>
      </div>
      <span className="text-[10px] text-slate-500 whitespace-nowrap">
        {formatTimeAgo(item.published_at)}
      </span>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function HomePulse({
  geoContext,
  opportunitySummary,
  pulseSummary,
  onNavigateOpportunities,
  onNavigateAnalyze,
  onNavigatePulse,
  onSelectOpportunity,
  isLoading = false,
}: HomePulseProps) {
  const currency = geoContext?.currency?.code || 'EUR';
  const marketPulse = geoContext?.market_pulse;
  const rates = pulseSummary?.central_bank_rates || [];
  const topOpportunities = opportunitySummary?.top_opportunities || [];
  const criticalPulse = pulseSummary?.critical_items || [];
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Chargement du Market Pulse...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 lg:p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-semibold tracking-tight flex items-center gap-3">
              <Zap className="text-indigo-400" size={28} />
              Market Pulse
            </h1>
            <p className="text-slate-400 mt-1 text-sm">
              {geoContext?.city}, {geoContext?.country} • Mis à jour en temps réel
            </p>
          </div>
          
          {/* Quick Actions */}
          <div className="flex gap-3">
            <button
              onClick={onNavigateAnalyze}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Eye size={16} />
              Analyser un bien
            </button>
            <button
              onClick={onNavigateOpportunities}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              <Target size={16} />
              Opportunités
            </button>
          </div>
        </div>
      </header>

      {/* Central Bank Rates */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Taux Directeurs
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {rates.map((rate) => (
            <RateBadge key={rate.bank} rate={rate} />
          ))}
        </div>
      </section>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Local Market Pulse */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Marché Local
          </h2>
          {marketPulse && (
            <MarketPulseCard pulse={marketPulse} currency={currency} />
          )}
          
          {/* Signal Summary */}
          <div className="mt-4 bg-slate-900/50 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
              <Zap size={14} className="text-amber-400" />
              Signaux Actifs
            </h3>
            <div className="space-y-3">
              {Object.entries(opportunitySummary?.signals_by_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>{getSignalIcon(type)}</span>
                    <span className="text-sm text-slate-300">{getSignalLabel(type)}</span>
                  </div>
                  <span className="text-sm font-semibold tabular-nums">{count}</span>
                </div>
              ))}
            </div>
            <button
              onClick={onNavigateOpportunities}
              className="w-full mt-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              Voir {opportunitySummary?.total_opportunities || 0} opportunités
              <ChevronRight size={14} />
            </button>
          </div>
        </div>

        {/* Top Opportunities */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Target size={14} />
            Signaux du Jour
          </h2>
          <div className="space-y-3">
            {topOpportunities.slice(0, 4).map((opp) => (
              <SignalCard
                key={opp.listing.id}
                opportunity={opp}
                onClick={() => onSelectOpportunity?.(opp.listing.id)}
              />
            ))}
            {topOpportunities.length === 0 && (
              <div className="bg-slate-800/30 border border-slate-700 rounded-xl p-6 text-center">
                <Target size={24} className="mx-auto text-slate-500 mb-2" />
                <p className="text-sm text-slate-400">
                  Aucun signal fort aujourd'hui
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Configurez vos critères pour recevoir des alertes
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Pulse Feed */}
        <div className="lg:col-span-1">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Bell size={14} />
            Actualités & Alertes
          </h2>
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
            {/* Action Required Badge */}
            {(pulseSummary?.action_required_count || 0) > 0 && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-3">
                <AlertTriangle size={18} className="text-red-400" />
                <div>
                  <p className="text-sm font-medium text-red-300">
                    {pulseSummary?.action_required_count} action(s) requise(s)
                  </p>
                  <p className="text-xs text-red-400/80">
                    Des éléments nécessitent votre attention
                  </p>
                </div>
              </div>
            )}
            
            {/* Pulse Items */}
            <div className="space-y-1 divide-y divide-slate-800">
              {criticalPulse.slice(0, 5).map((item) => (
                <PulseItemCard
                  key={item.id}
                  item={item}
                  onClick={onNavigatePulse}
                />
              ))}
            </div>
            
            <button
              onClick={onNavigatePulse}
              className="w-full mt-4 py-2 text-sm text-slate-400 hover:text-slate-300 transition-colors flex items-center justify-center gap-1"
            >
              Voir toutes les actualités
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Footer */}
      <footer className="mt-8 pt-6 border-t border-slate-800">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-semibold tabular-nums">
              {opportunitySummary?.total_opportunities || 0}
            </p>
            <p className="text-xs text-slate-500 uppercase">Opportunités</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold tabular-nums text-amber-400">
              {opportunitySummary?.high_priority_count || 0}
            </p>
            <p className="text-xs text-slate-500 uppercase">Priorité Haute</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold tabular-nums">
              {pulseSummary?.total_items || 0}
            </p>
            <p className="text-xs text-slate-500 uppercase">Actualités</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-semibold tabular-nums text-red-400">
              {pulseSummary?.action_required_count || 0}
            </p>
            <p className="text-xs text-slate-500 uppercase">Actions Requises</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
