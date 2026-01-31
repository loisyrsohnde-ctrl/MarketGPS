'use client';

import React from 'react';
import {
  Eye,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Wrench,
  ThumbsUp,
  ThumbsDown,
  HelpCircle,
  Home,
  Zap,
  Paintbrush,
  ChevronDown,
} from 'lucide-react';

import type { VisualAnalysis, DetectedElement, RenovationEstimate } from '@/types/wealth-agent';
import { formatCurrency, getConditionLabel } from '@/lib/api-wealth';

// =============================================================================
// Types
// =============================================================================

interface VisualInspectorResultProps {
  analysis: VisualAnalysis;
  currency?: string;
}

// =============================================================================
// Sub-Components
// =============================================================================

function ConditionBadge({ condition, score }: { condition: string; score: number }) {
  const config: Record<string, { bg: string; text: string; icon: React.ReactNode }> = {
    excellent: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: <CheckCircle size={16} /> },
    good: { bg: 'bg-green-500/20', text: 'text-green-400', icon: <CheckCircle size={16} /> },
    fair: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: <HelpCircle size={16} /> },
    poor: { bg: 'bg-orange-500/20', text: 'text-orange-400', icon: <AlertTriangle size={16} /> },
    to_renovate: { bg: 'bg-red-500/20', text: 'text-red-400', icon: <XCircle size={16} /> },
  };
  
  const { bg, text, icon } = config[condition] || config.fair;
  
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${bg} ${text}`}>
      {icon}
      <span className="font-medium">{getConditionLabel(condition)}</span>
      <span className="text-sm opacity-80">({score}/100)</span>
    </div>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  const color = percent >= 80 ? 'bg-emerald-500' : percent >= 60 ? 'bg-yellow-500' : 'bg-orange-500';
  
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${color} rounded-full`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs text-slate-400">{percent}%</span>
    </div>
  );
}

function ElementCard({ element }: { element: DetectedElement }) {
  const conditionColors: Record<string, string> = {
    excellent: 'text-emerald-400',
    good: 'text-green-400',
    fair: 'text-yellow-400',
    poor: 'text-red-400',
  };
  
  const typeLabels: Record<string, string> = {
    windows: 'Fenêtres',
    flooring: 'Sol',
    walls: 'Murs',
    ceiling: 'Plafond',
    kitchen: 'Cuisine',
    bathroom: 'Salle de bain',
    electrical: 'Électricité',
    plumbing: 'Plomberie',
    heating: 'Chauffage',
    insulation: 'Isolation',
    facade: 'Façade',
    roof: 'Toiture',
    doors: 'Portes',
    balcony: 'Balcon',
    garden: 'Jardin',
  };
  
  return (
    <div className="p-3 bg-slate-800/50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-sm">
          {typeLabels[element.type] || element.type}
        </span>
        <span className={`text-xs font-medium ${conditionColors[element.condition] || 'text-slate-400'}`}>
          {getConditionLabel(element.condition)}
        </span>
      </div>
      {element.material && (
        <p className="text-xs text-slate-400 mb-1">
          Matériau: {element.material}
        </p>
      )}
      {element.age_estimate && (
        <p className="text-xs text-slate-400 mb-1">
          Âge estimé: {element.age_estimate}
        </p>
      )}
      {element.notes && (
        <p className="text-xs text-slate-500 mt-2 italic">
          {element.notes}
        </p>
      )}
    </div>
  );
}

function RenovationCard({ renovation, currency }: { renovation: RenovationEstimate; currency: string }) {
  const priorityConfig: Record<string, { bg: string; text: string; label: string }> = {
    required: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Obligatoire' },
    recommended: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Recommandé' },
    optional: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Optionnel' },
  };
  
  const { bg, text, label } = priorityConfig[renovation.priority] || priorityConfig.optional;
  
  const workLabels: Record<string, string> = {
    painting: 'Peinture',
    flooring: 'Revêtement sol',
    kitchen: 'Cuisine',
    bathroom: 'Salle de bain',
    electrical: 'Électricité',
    plumbing: 'Plomberie',
    heating: 'Chauffage',
    insulation: 'Isolation',
    peinture: 'Peinture',
    cuisine: 'Cuisine',
    sol: 'Sol',
  };
  
  return (
    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Wrench size={16} className="text-slate-400" />
          <span className="font-medium">
            {workLabels[renovation.work_type.toLowerCase()] || renovation.work_type}
          </span>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full ${bg} ${text}`}>
          {label}
        </span>
      </div>
      
      <p className="text-sm text-slate-400 mb-3">
        {renovation.description}
      </p>
      
      <div className="flex items-center justify-between">
        <div className="text-sm">
          <span className="text-slate-500">Estimation:</span>
          <span className="font-medium ml-2">
            {formatCurrency(renovation.cost_low, currency)} - {formatCurrency(renovation.cost_high, currency)}
          </span>
        </div>
        {renovation.timeline_days && (
          <span className="text-xs text-slate-500">
            ~{renovation.timeline_days}j
          </span>
        )}
      </div>
    </div>
  );
}

function MismatchAlert({
  listed,
  actual,
  percent,
  evidence,
}: {
  listed: string;
  actual: string;
  percent?: number;
  evidence: string[];
}) {
  const positionLabels: Record<string, string> = {
    luxury: 'Luxe',
    premium: 'Premium',
    standard: 'Standard',
    budget: 'Entrée de gamme',
  };
  
  return (
    <div className="p-4 bg-orange-500/10 border border-orange-500/30 rounded-xl">
      <div className="flex items-start gap-3">
        <AlertTriangle size={20} className="text-orange-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-semibold text-orange-300 mb-2">
            Surcote détectée
          </h4>
          <p className="text-sm text-slate-300 mb-3">
            Annoncé comme <span className="font-medium">{positionLabels[listed] || listed}</span>,
            {' '}qualité réelle <span className="font-medium">{positionLabels[actual] || actual}</span>.
            {percent && (
              <span className="text-orange-400 font-semibold ml-1">
                Surcote estimée: {percent}%
              </span>
            )}
          </p>
          
          {evidence.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 uppercase mb-2">Preuves visuelles:</p>
              <ul className="space-y-1">
                {evidence.map((e, i) => (
                  <li key={i} className="text-xs text-slate-400 flex items-start gap-2">
                    <span className="text-orange-400">•</span>
                    {e}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function VisualInspectorResult({
  analysis,
  currency = 'EUR',
}: VisualInspectorResultProps) {
  const [showAllElements, setShowAllElements] = React.useState(false);
  const displayedElements = showAllElements ? analysis.elements : analysis.elements.slice(0, 4);
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-indigo-500/20 rounded-xl">
            <Eye size={24} className="text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Analyse Visuelle</h2>
            <p className="text-sm text-slate-400">
              {analysis.images_analyzed} image(s) analysée(s)
            </p>
          </div>
        </div>
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <ConditionBadge 
            condition={analysis.overall_condition} 
            score={analysis.condition_score}
          />
          
          <div className="flex items-center gap-4">
            <div>
              <p className="text-[10px] text-slate-500 uppercase mb-1">Confiance</p>
              <ConfidenceBar confidence={analysis.condition_confidence} />
            </div>
          </div>
        </div>
        
        <p className="mt-4 text-sm text-slate-300 leading-relaxed">
          {analysis.condition_summary}
        </p>
      </div>
      
      {/* Mismatch Alert */}
      {analysis.mismatch_detected && (
        <MismatchAlert
          listed={analysis.listed_positioning}
          actual={analysis.actual_quality}
          percent={analysis.estimated_overpricing_percent}
          evidence={analysis.mismatch_evidence}
        />
      )}
      
      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strengths */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-5">
          <h3 className="font-medium mb-4 flex items-center gap-2 text-emerald-400">
            <ThumbsUp size={18} />
            Points forts
          </h3>
          <ul className="space-y-2">
            {analysis.strengths.map((s, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                <CheckCircle size={14} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                {s}
              </li>
            ))}
          </ul>
        </div>
        
        {/* Weaknesses */}
        <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-5">
          <h3 className="font-medium mb-4 flex items-center gap-2 text-orange-400">
            <ThumbsDown size={18} />
            Points d&apos;attention
          </h3>
          <ul className="space-y-2">
            {analysis.weaknesses.map((w, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                <AlertTriangle size={14} className="text-orange-400 flex-shrink-0 mt-0.5" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      </div>
      
      {/* Detected Elements */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <Home size={18} className="text-slate-400" />
          Éléments détectés
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {displayedElements.map((element, i) => (
            <ElementCard key={i} element={element} />
          ))}
        </div>
        
        {analysis.elements.length > 4 && (
          <button
            onClick={() => setShowAllElements(!showAllElements)}
            className="mt-4 w-full py-2 text-sm text-slate-400 hover:text-slate-300 flex items-center justify-center gap-1"
          >
            {showAllElements ? 'Voir moins' : `Voir ${analysis.elements.length - 4} de plus`}
            <ChevronDown size={14} className={showAllElements ? 'rotate-180' : ''} />
          </button>
        )}
      </div>
      
      {/* Renovation Estimates */}
      {analysis.renovations.length > 0 && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium flex items-center gap-2">
              <Paintbrush size={18} className="text-slate-400" />
              Estimation des travaux
            </h3>
            <div className="text-right">
              <p className="text-sm text-slate-400">Budget total estimé</p>
              <p className="font-semibold">
                {formatCurrency(analysis.total_cost_low, currency)} - {formatCurrency(analysis.total_cost_high, currency)}
              </p>
            </div>
          </div>
          
          <div className="space-y-3">
            {analysis.renovations.map((reno, i) => (
              <RenovationCard key={i} renovation={reno} currency={currency} />
            ))}
          </div>
        </div>
      )}
      
      {/* Footer */}
      <div className="text-center text-xs text-slate-500">
        <p>
          Analyse générée par {analysis.model_version} • 
          Confiance: {Math.round(analysis.condition_confidence * 100)}%
        </p>
        <p className="mt-1">
          Les estimations sont indicatives et peuvent varier selon les conditions réelles.
        </p>
      </div>
    </div>
  );
}
