'use client';

import React from 'react';
import {
  MapPin,
  Home,
  Ruler,
  Calendar,
  TrendingUp,
  AlertTriangle,
  ChevronRight,
  Zap,
  BarChart3,
  Wallet,
  Clock,
  ExternalLink,
} from 'lucide-react';

import type { Opportunity, DealSignal, NormalizedListing } from '@/types/wealth-agent';
import {
  formatCurrency,
  getSignalIcon,
  getSignalLabel,
  getPriorityColor,
  getEnergyRatingColor,
  getScoreColor,
} from '@/lib/api-wealth';

// =============================================================================
// Types
// =============================================================================

interface OpportunityCardProps {
  opportunity: Opportunity;
  onClick?: () => void;
  variant?: 'compact' | 'full';
  currency?: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

function SignalBadge({ signal }: { signal: DealSignal }) {
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
      signal.priority === 'critical' ? 'bg-red-500/20 text-red-300' :
      signal.priority === 'high' ? 'bg-orange-500/20 text-orange-300' :
      signal.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-300' :
      'bg-blue-500/20 text-blue-300'
    }`}>
      <span>{getSignalIcon(signal.signal_type)}</span>
      <span>{getSignalLabel(signal.signal_type)}</span>
    </div>
  );
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const width = Math.min(100, Math.max(0, score));
  const color = score >= 70 ? 'bg-emerald-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500';
  
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-500 uppercase w-12">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} rounded-full transition-all`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="text-xs font-medium tabular-nums w-6">{score}</span>
    </div>
  );
}

// =============================================================================
// Compact Card
// =============================================================================

function CompactCard({
  listing,
  signals,
  onClick,
  currency,
}: {
  listing: NormalizedListing;
  signals: DealSignal[];
  onClick?: () => void;
  currency: string;
}) {
  const topSignal = signals[0];
  
  return (
    <div 
      className="bg-slate-800/40 hover:bg-slate-800/60 border border-slate-700 hover:border-slate-600 rounded-xl p-4 cursor-pointer transition-all group"
      onClick={onClick}
    >
      <div className="flex gap-4">
        {/* Image Placeholder */}
        <div className="w-20 h-20 bg-slate-700 rounded-lg flex-shrink-0 overflow-hidden">
          {listing.images?.[0] ? (
            <img 
              src={listing.images[0]} 
              alt={listing.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Home size={24} className="text-slate-500" />
            </div>
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <div>
              <p className="text-sm font-medium truncate">{listing.city}</p>
              <p className="text-xs text-slate-400 truncate">{listing.neighborhood || listing.postal_code}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-sm font-semibold tabular-nums">
                {formatCurrency(listing.price, currency)}
              </p>
              <p className="text-xs text-slate-400">
                {listing.price_per_m2?.toLocaleString()} €/m²
              </p>
            </div>
          </div>
          
          {/* Signals */}
          {topSignal && (
            <div className="mt-2">
              <SignalBadge signal={topSignal} />
            </div>
          )}
          
          {/* Quick Stats */}
          <div className="flex items-center gap-4 mt-2">
            <div className="flex items-center gap-1 text-xs text-slate-400">
              <Ruler size={12} />
              {listing.surface_m2} m²
            </div>
            {listing.prophetia_score && (
              <div className={`flex items-center gap-1 text-xs ${getScoreColor(listing.prophetia_score)}`}>
                <BarChart3 size={12} />
                {listing.prophetia_score}
              </div>
            )}
            {listing.rental_yield_gross && (
              <div className="flex items-center gap-1 text-xs text-emerald-400">
                <Wallet size={12} />
                {listing.rental_yield_gross.toFixed(1)}%
              </div>
            )}
          </div>
        </div>
        
        {/* Arrow */}
        <ChevronRight size={18} className="text-slate-500 group-hover:text-slate-300 flex-shrink-0 self-center" />
      </div>
    </div>
  );
}

// =============================================================================
// Full Card
// =============================================================================

function FullCard({
  listing,
  signals,
  onClick,
  currency,
}: {
  listing: NormalizedListing;
  signals: DealSignal[];
  onClick?: () => void;
  currency: string;
}) {
  return (
    <div 
      className="bg-slate-900/50 border border-slate-800 hover:border-slate-700 rounded-2xl overflow-hidden cursor-pointer transition-all group"
      onClick={onClick}
    >
      {/* Header with Image */}
      <div className="relative h-48 bg-slate-800">
        {listing.images?.[0] ? (
          <img 
            src={listing.images[0]} 
            alt={listing.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Home size={48} className="text-slate-600" />
          </div>
        )}
        
        {/* Overlay badges */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2">
          {signals.slice(0, 2).map((signal) => (
            <SignalBadge key={signal.id} signal={signal} />
          ))}
        </div>
        
        {/* Energy Rating */}
        {listing.energy_rating && (
          <div className={`absolute top-3 right-3 w-8 h-8 ${getEnergyRatingColor(listing.energy_rating)} rounded-lg flex items-center justify-center text-sm font-bold text-white`}>
            {listing.energy_rating}
          </div>
        )}
        
        {/* Price Tag */}
        <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-sm rounded-lg px-3 py-2">
          <p className="text-lg font-semibold">
            {formatCurrency(listing.price, currency)}
          </p>
          <p className="text-xs text-slate-400">
            {listing.price_per_m2?.toLocaleString()} €/m²
          </p>
        </div>
      </div>
      
      {/* Content */}
      <div className="p-5">
        {/* Title & Location */}
        <div className="mb-4">
          <h3 className="font-medium text-lg line-clamp-1 group-hover:text-indigo-400 transition-colors">
            {listing.title}
          </h3>
          <div className="flex items-center gap-1 text-slate-400 text-sm mt-1">
            <MapPin size={14} />
            {listing.city}, {listing.country}
          </div>
        </div>
        
        {/* Key Features */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="text-center p-2 bg-slate-800/50 rounded-lg">
            <p className="text-lg font-semibold">{listing.surface_m2}</p>
            <p className="text-[10px] text-slate-500 uppercase">m²</p>
          </div>
          <div className="text-center p-2 bg-slate-800/50 rounded-lg">
            <p className="text-lg font-semibold">{listing.rooms || '—'}</p>
            <p className="text-[10px] text-slate-500 uppercase">Pièces</p>
          </div>
          <div className="text-center p-2 bg-slate-800/50 rounded-lg">
            <p className="text-lg font-semibold">{listing.prophetia_score || '—'}</p>
            <p className="text-[10px] text-slate-500 uppercase">Score</p>
          </div>
          <div className="text-center p-2 bg-slate-800/50 rounded-lg">
            <p className="text-lg font-semibold">
              {listing.rental_yield_gross?.toFixed(1) || '—'}%
            </p>
            <p className="text-[10px] text-slate-500 uppercase">Yield</p>
          </div>
        </div>
        
        {/* ProphetIA Scores */}
        {listing.prophetia_score && (
          <div className="space-y-1.5 mb-4">
            <ScoreBar score={listing.prophetia_yield || 0} label="Yield" />
            <ScoreBar score={listing.prophetia_safety || 0} label="Safety" />
            <ScoreBar score={listing.prophetia_growth || 0} label="Growth" />
          </div>
        )}
        
        {/* Signal Summary */}
        {signals[0] && (
          <div className="p-3 bg-slate-800/50 rounded-lg mb-4">
            <div className="flex items-start gap-2">
              <Zap size={16} className="text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium">{signals[0].summary}</p>
                {signals[0].risks?.[0] && (
                  <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                    <AlertTriangle size={10} />
                    {signals[0].risks[0]}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Clock size={12} />
              {listing.days_on_market}j
            </span>
            {listing.construction_year && (
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {listing.construction_year}
              </span>
            )}
          </div>
          
          <button className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors">
            Voir détails
            <ExternalLink size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function OpportunityCard({
  opportunity,
  onClick,
  variant = 'compact',
  currency = 'EUR',
}: OpportunityCardProps) {
  const { listing, signals } = opportunity;
  
  if (variant === 'full') {
    return (
      <FullCard
        listing={listing}
        signals={signals}
        onClick={onClick}
        currency={currency}
      />
    );
  }
  
  return (
    <CompactCard
      listing={listing}
      signals={signals}
      onClick={onClick}
      currency={currency}
    />
  );
}
