'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sun,
  X,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  BarChart3,
  Wallet,
  Target,
  Zap,
  Clock,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface MorningBriefData {
  date: string;
  greeting: string;
  market_summary: string;
  portfolio_status: {
    value: number;
    change_1d: number;
    change_1d_value: number;
    score: number;
    score_trend: 'up' | 'down' | 'stable';
    vs_benchmark: number;
  };
  key_metrics: {
    label: string;
    value: string;
    status: 'good' | 'warning' | 'neutral';
  }[];
  alerts: {
    type: 'warning' | 'info' | 'success';
    message: string;
  }[];
  opportunities: {
    ticker: string;
    score: number;
    signal: string;
  }[];
  action_items: string[];
}

interface MorningBriefProps {
  isOpen: boolean;
  onClose: () => void;
  data?: MorningBriefData;
  userName?: string;
  focusMode?: boolean;
}

// =============================================================================
// Demo Data
// =============================================================================

function generateDemoData(): MorningBriefData {
  const today = new Date();
  const hour = today.getHours();
  
  return {
    date: today.toLocaleDateString('fr-FR', { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric' 
    }),
    greeting: hour < 12 ? 'Bonjour' : hour < 18 ? 'Bon après-midi' : 'Bonsoir',
    market_summary: `Les marchés européens progressent de 0.4% ce matin, portés par les valeurs technologiques. 
Le CAC 40 gagne 0.5% tandis que le DAX avance de 0.3%. 
Les futures américains indiquent une ouverture stable. 
La BCE maintient ses taux inchangés, comme anticipé.`,
    portfolio_status: {
      value: 247850,
      change_1d: 0.82,
      change_1d_value: 2015,
      score: 72,
      score_trend: 'stable',
      vs_benchmark: 2.3,
    },
    key_metrics: [
      { label: 'Score ProphetIA', value: '72', status: 'good' },
      { label: 'Perf. YTD', value: '+12.4%', status: 'good' },
      { label: 'Volatilité', value: '14.2%', status: 'neutral' },
      { label: 'Alpha vs S&P', value: '+2.3%', status: 'good' },
    ],
    alerts: [
      { type: 'warning', message: 'AAPL : résultats Q4 ce soir à 22h00' },
      { type: 'info', message: 'Dividende MSFT : €420 à réinvestir' },
      { type: 'success', message: 'Votre portefeuille surperforme le benchmark' },
    ],
    opportunities: [
      { ticker: 'MSFT', score: 84, signal: 'Accumulation institutionnelle' },
      { ticker: 'GOOGL', score: 79, signal: 'Breakout technique' },
      { ticker: 'NVDA', score: 82, signal: 'Momentum fort' },
    ],
    action_items: [
      'Surveiller les résultats AAPL ce soir',
      'Considérer renforcement position MSFT',
      'Rééquilibrer : -5% actions, +5% obligations',
    ],
  };
}

// =============================================================================
// Sub-Components
// =============================================================================

function MetricCard({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status: 'good' | 'warning' | 'neutral';
}) {
  const statusColors = {
    good: 'text-emerald-400 bg-emerald-500/10',
    warning: 'text-amber-400 bg-amber-500/10',
    neutral: 'text-slate-400 bg-slate-500/10',
  };
  
  return (
    <div className={`p-3 rounded-xl ${statusColors[status]}`}>
      <p className="text-[10px] uppercase tracking-wide opacity-70 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function AlertItem({ alert }: { alert: { type: string; message: string } }) {
  const config = {
    warning: { icon: AlertTriangle, color: 'text-amber-400' },
    info: { icon: Clock, color: 'text-blue-400' },
    success: { icon: CheckCircle, color: 'text-emerald-400' },
  }[alert.type as 'warning' | 'info' | 'success'] || { icon: AlertTriangle, color: 'text-slate-400' };
  
  const Icon = config.icon;
  
  return (
    <div className="flex items-start gap-2 py-2">
      <Icon size={14} className={`mt-0.5 ${config.color}`} />
      <p className="text-sm text-slate-300">{alert.message}</p>
    </div>
  );
}

function OpportunityRow({ opp }: { opp: { ticker: string; score: number; signal: string } }) {
  return (
    <div className="flex items-center gap-3 py-2 px-2 hover:bg-slate-800/30 rounded-lg transition-colors cursor-pointer">
      <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-sm font-bold">
        {opp.ticker.slice(0, 2)}
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium">{opp.ticker}</p>
        <p className="text-xs text-slate-500">{opp.signal}</p>
      </div>
      <div 
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold
          ${opp.score >= 80 ? 'bg-emerald-500/20 text-emerald-400' : 
            opp.score >= 70 ? 'bg-blue-500/20 text-blue-400' : 
            'bg-amber-500/20 text-amber-400'}`}
      >
        {opp.score}
      </div>
      <ChevronRight size={14} className="text-slate-600" />
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function MorningBrief({
  isOpen,
  onClose,
  data,
  userName = 'Investisseur',
  focusMode = false,
}: MorningBriefProps) {
  const [briefData, setBriefData] = useState<MorningBriefData | null>(null);

  useEffect(() => {
    if (isOpen) {
      setBriefData(data || generateDemoData());
    }
  }, [isOpen, data]);

  if (!isOpen || !briefData) return null;

  const formatCurrency = (value: number) => {
    if (focusMode) return '•••••';
    return new Intl.NumberFormat('fr-FR', { 
      style: 'currency', 
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 50, scale: 0.95 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="w-full max-w-2xl bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="relative p-6 pb-4 bg-gradient-to-r from-orange-600/20 via-amber-600/10 to-yellow-600/20 border-b border-slate-800">
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 hover:bg-slate-800/50 rounded-lg transition-colors"
            >
              <X size={18} className="text-slate-400" />
            </button>
            
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center">
                <Sun size={24} className="text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-200">
                  {briefData.greeting}, {userName}
                </h2>
                <p className="text-sm text-slate-400 capitalize">{briefData.date}</p>
              </div>
            </div>
            
            {/* Portfolio Summary */}
            <div className="flex items-center gap-6">
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wide">Valeur portefeuille</p>
                <p className="text-2xl font-bold text-slate-200">
                  {formatCurrency(briefData.portfolio_status.value)}
                </p>
              </div>
              <div className={`flex items-center gap-1 ${
                briefData.portfolio_status.change_1d >= 0 ? 'text-emerald-400' : 'text-red-400'
              }`}>
                {briefData.portfolio_status.change_1d >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span className="font-semibold">
                  {briefData.portfolio_status.change_1d >= 0 ? '+' : ''}
                  {briefData.portfolio_status.change_1d.toFixed(2)}%
                </span>
                <span className="text-xs opacity-70">
                  ({focusMode ? '•••' : formatCurrency(briefData.portfolio_status.change_1d_value)})
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Key Metrics */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <BarChart3 size={14} />
                Métriques clés
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {briefData.key_metrics.map((metric, i) => (
                  <MetricCard key={i} {...metric} />
                ))}
              </div>
            </div>

            {/* Market Summary */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                <Sparkles size={14} />
                Résumé marchés
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed bg-slate-800/30 rounded-xl p-4">
                {briefData.market_summary}
              </p>
            </div>

            {/* Alerts */}
            {briefData.alerts.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <AlertTriangle size={14} />
                  Alertes du jour
                </h3>
                <div className="bg-slate-800/30 rounded-xl p-4 divide-y divide-slate-800">
                  {briefData.alerts.map((alert, i) => (
                    <AlertItem key={i} alert={alert} />
                  ))}
                </div>
              </div>
            )}

            {/* Opportunities */}
            {briefData.opportunities.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <Target size={14} />
                  Opportunités détectées
                </h3>
                <div className="bg-slate-800/30 rounded-xl p-2">
                  {briefData.opportunities.map((opp, i) => (
                    <OpportunityRow key={i} opp={opp} />
                  ))}
                </div>
              </div>
            )}

            {/* Action Items */}
            {briefData.action_items.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-2">
                  <Zap size={14} />
                  Actions recommandées
                </h3>
                <div className="space-y-2">
                  {briefData.action_items.map((item, i) => (
                    <div 
                      key={i}
                      className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl hover:bg-slate-800/50 transition-colors cursor-pointer group"
                    >
                      <div className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-semibold">
                        {i + 1}
                      </div>
                      <p className="flex-1 text-sm text-slate-300">{item}</p>
                      <ArrowRight size={14} className="text-slate-600 group-hover:text-indigo-400 transition-colors" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-between">
            <p className="text-[10px] text-slate-500">
              Généré à {new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
            >
              Commencer la journée
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
