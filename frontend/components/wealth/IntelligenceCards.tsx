'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  ChevronRight,
  X,
  Zap,
  Target,
  Bell,
  BarChart3,
  ArrowRight,
  Shield,
  DollarSign,
  Home,
  FileText,
  Lightbulb,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

type CardType = 'alert' | 'opportunity' | 'insight' | 'action' | 'news';
type Priority = 'critical' | 'high' | 'medium' | 'low' | 'info';

interface IntelligenceCard {
  id: string;
  type: CardType;
  priority: Priority;
  title: string;
  summary: string;
  detail?: string;
  timestamp: string;
  asset_id?: string;
  asset_name?: string;
  metrics?: {
    label: string;
    value: string;
    change?: number;
  }[];
  actions?: {
    label: string;
    type: 'primary' | 'secondary';
    action: string;
  }[];
  dismissed?: boolean;
}

interface IntelligenceCardsProps {
  cards: IntelligenceCard[];
  onCardClick?: (card: IntelligenceCard) => void;
  onDismiss?: (cardId: string) => void;
  onAction?: (cardId: string, action: string) => void;
  focusMode?: boolean;
  maxVisible?: number;
  className?: string;
}

// =============================================================================
// Utils
// =============================================================================

function formatTimeAgo(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins}min`;
  if (diffHours < 24) return `Il y a ${diffHours}h`;
  if (diffDays < 7) return `Il y a ${diffDays}j`;
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
}

const typeConfig: Record<CardType, { icon: React.ElementType; label: string; color: string }> = {
  alert: { icon: AlertTriangle, label: 'Alerte', color: 'text-red-400 bg-red-500/10 border-red-500/30' },
  opportunity: { icon: Target, label: 'Opportunité', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  insight: { icon: Lightbulb, label: 'Insight', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  action: { icon: Zap, label: 'Action', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
  news: { icon: Bell, label: 'Actualité', color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' },
};

const priorityConfig: Record<Priority, { color: string; glow: string }> = {
  critical: { color: 'border-l-red-500', glow: 'shadow-red-500/20' },
  high: { color: 'border-l-orange-500', glow: 'shadow-orange-500/20' },
  medium: { color: 'border-l-amber-500', glow: 'shadow-amber-500/10' },
  low: { color: 'border-l-slate-500', glow: '' },
  info: { color: 'border-l-blue-500', glow: '' },
};

// =============================================================================
// Single Card Component
// =============================================================================

function Card({
  card,
  onClick,
  onDismiss,
  onAction,
  focusMode,
  expanded,
  onToggleExpand,
}: {
  card: IntelligenceCard;
  onClick?: () => void;
  onDismiss?: () => void;
  onAction?: (action: string) => void;
  focusMode?: boolean;
  expanded?: boolean;
  onToggleExpand?: () => void;
}) {
  const config = typeConfig[card.type];
  const priority = priorityConfig[card.priority];
  const Icon = config.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, x: -100, scale: 0.95 }}
      transition={{ duration: 0.3 }}
      className={`
        relative bg-slate-900/60 backdrop-blur-sm border border-slate-800 rounded-xl
        border-l-4 ${priority.color} ${priority.glow}
        hover:bg-slate-900/80 hover:border-slate-700
        transition-all duration-200 overflow-hidden
        ${expanded ? 'ring-1 ring-slate-700' : ''}
      `}
    >
      {/* Main Content */}
      <div 
        className="p-4 cursor-pointer"
        onClick={onToggleExpand || onClick}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${config.color}`}>
              <Icon size={14} />
            </div>
            <span className={`text-[10px] font-semibold uppercase tracking-wider ${config.color.split(' ')[0]}`}>
              {config.label}
            </span>
            {card.asset_name && (
              <span className="text-[10px] text-slate-500">• {card.asset_name}</span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-slate-500">
              {formatTimeAgo(card.timestamp)}
            </span>
            {onDismiss && (
              <button
                onClick={(e) => { e.stopPropagation(); onDismiss(); }}
                className="p-1 hover:bg-slate-800 rounded transition-colors"
              >
                <X size={12} className="text-slate-500" />
              </button>
            )}
          </div>
        </div>

        {/* Title & Summary */}
        <h4 className="text-sm font-medium text-slate-200 mb-1">
          {card.title}
        </h4>
        <p className="text-xs text-slate-400 line-clamp-2">
          {card.summary}
        </p>

        {/* Metrics Preview */}
        {card.metrics && card.metrics.length > 0 && !focusMode && (
          <div className="flex gap-4 mt-3">
            {card.metrics.slice(0, 3).map((metric, i) => (
              <div key={i} className="flex items-center gap-1">
                <span className="text-[10px] text-slate-500">{metric.label}:</span>
                <span className="text-xs font-semibold tabular-nums">{metric.value}</span>
                {metric.change !== undefined && (
                  <span className={`text-[10px] ${metric.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {metric.change >= 0 ? '+' : ''}{metric.change}%
                  </span>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Expand indicator */}
        {(card.detail || card.actions) && (
          <div className="flex justify-end mt-2">
            <ChevronRight 
              size={14} 
              className={`text-slate-500 transition-transform ${expanded ? 'rotate-90' : ''}`}
            />
          </div>
        )}
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-slate-800"
          >
            <div className="p-4 bg-slate-950/50">
              {/* Detail */}
              {card.detail && (
                <p className="text-xs text-slate-300 mb-4 leading-relaxed">
                  {card.detail}
                </p>
              )}

              {/* Full Metrics */}
              {card.metrics && card.metrics.length > 0 && !focusMode && (
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {card.metrics.map((metric, i) => (
                    <div key={i} className="bg-slate-800/50 rounded-lg p-2">
                      <p className="text-[10px] text-slate-500 uppercase">{metric.label}</p>
                      <p className="text-sm font-semibold tabular-nums">{metric.value}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              {card.actions && card.actions.length > 0 && (
                <div className="flex gap-2">
                  {card.actions.map((action, i) => (
                    <button
                      key={i}
                      onClick={(e) => { e.stopPropagation(); onAction?.(action.action); }}
                      className={`
                        flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-colors
                        flex items-center justify-center gap-1
                        ${action.type === 'primary' 
                          ? 'bg-indigo-600 hover:bg-indigo-500 text-white' 
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}
                      `}
                    >
                      {action.label}
                      <ArrowRight size={12} />
                    </button>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function IntelligenceCards({
  cards,
  onCardClick,
  onDismiss,
  onAction,
  focusMode = false,
  maxVisible = 10,
  className = '',
}: IntelligenceCardsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<CardType | 'all'>('all');

  // Filter and sort cards
  const filteredCards = cards
    .filter(c => !c.dismissed)
    .filter(c => filter === 'all' || c.type === filter)
    .sort((a, b) => {
      // Sort by priority first
      const priorityOrder: Record<Priority, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
      const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority];
      if (priorityDiff !== 0) return priorityDiff;
      // Then by timestamp
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
    })
    .slice(0, maxVisible);

  // Stats
  const criticalCount = cards.filter(c => c.priority === 'critical' && !c.dismissed).length;
  const actionableCount = cards.filter(c => c.actions && c.actions.length > 0 && !c.dismissed).length;

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Zap size={16} className="text-amber-400" />
            Intelligence Feed
          </h3>
          
          {criticalCount > 0 && (
            <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-[10px] font-semibold rounded-full">
              {criticalCount} critique{criticalCount > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex gap-1">
          {(['all', 'alert', 'opportunity', 'insight'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`
                px-2 py-1 text-[10px] font-medium rounded transition-colors
                ${filter === f 
                  ? 'bg-slate-700 text-slate-200' 
                  : 'text-slate-500 hover:text-slate-300'}
              `}
            >
              {f === 'all' ? 'Tout' : typeConfig[f].label}
            </button>
          ))}
        </div>
      </div>

      {/* Cards List */}
      <div className="space-y-3">
        <AnimatePresence mode="popLayout">
          {filteredCards.map((card) => (
            <Card
              key={card.id}
              card={card}
              onClick={() => onCardClick?.(card)}
              onDismiss={onDismiss ? () => onDismiss(card.id) : undefined}
              onAction={onAction ? (action) => onAction(card.id, action) : undefined}
              focusMode={focusMode}
              expanded={expandedId === card.id}
              onToggleExpand={() => setExpandedId(expandedId === card.id ? null : card.id)}
            />
          ))}
        </AnimatePresence>

        {filteredCards.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            <CheckCircle size={24} className="mx-auto mb-2 text-emerald-400" />
            <p className="text-sm">Aucune alerte active</p>
            <p className="text-xs mt-1">Votre portefeuille est en bonne santé</p>
          </div>
        )}
      </div>

      {/* Footer Stats */}
      {cards.length > maxVisible && (
        <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {filteredCards.length} sur {cards.filter(c => !c.dismissed).length} éléments
          </span>
          <button className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1">
            Voir tout <ChevronRight size={12} />
          </button>
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Export Types
// =============================================================================

export type { IntelligenceCard, CardType, Priority, IntelligenceCardsProps };
