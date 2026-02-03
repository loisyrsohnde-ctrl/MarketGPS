'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuickActions } from '@/hooks/useQuickActions';
import { KeyboardShortcutsHelp } from './KeyboardShortcutsHelp';
import type { Asset } from '@/types';
import {
  Star,
  StarOff,
  Bell,
  Copy,
  Share2,
  Zap,
  TrendingUp,
  MessageCircle,
  Check,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// QUICK ACTIONS BAR - STICKY HEADER COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface QuickActionsBarProps {
  asset: Asset;
  onOpenAlert?: () => void;
  onOpenComparator?: () => void;
  onOpenAIChat?: () => void;
  userId?: string;
  sticky?: boolean;
  showTooltips?: boolean;
}

interface ActionState {
  id: string;
  loading: boolean;
  success: boolean;
  message?: string;
}

export function QuickActionsBar({
  asset,
  onOpenAlert,
  onOpenComparator,
  onOpenAIChat,
  userId = 'default',
  sticky = true,
  showTooltips = true,
}: QuickActionsBarProps) {
  const [actionStates, setActionStates] = useState<Record<string, ActionState>>({});

  const { isInWatchlist, toggleWatchlist, copyToClipboard, share, isToggling } =
    useQuickActions({
      assetId: asset.asset_id,
      ticker: asset.ticker,
      userId,
      marketScope: asset.market_scope,
      onActionComplete: (action, success) => {
        setActionStates((prev) => ({
          ...prev,
          [action]: {
            id: action,
            loading: false,
            success,
            message: success ? 'Succès' : 'Erreur',
          },
        }));

        setTimeout(() => {
          setActionStates((prev) => ({
            ...prev,
            [action]: { ...prev[action], success: false },
          }));
        }, 2000);
      },
    });

  const getActionState = (actionId: string): ActionState => {
    return (
      actionStates[actionId] || {
        id: actionId,
        loading: false,
        success: false,
      }
    );
  };

  const actions = [
    {
      id: 'watchlist',
      icon: isInWatchlist ? (
        <Star className="w-4 h-4 fill-current" />
      ) : (
        <StarOff className="w-4 h-4" />
      ),
      label: isInWatchlist ? 'Suivi' : 'Ajouter',
      tooltip: isInWatchlist ? 'Retirer de la watchlist (W)' : 'Ajouter à la watchlist (W)',
      action: () => toggleWatchlist(),
      loading: isToggling,
      isActive: isInWatchlist,
    },
    {
      id: 'alert',
      icon: <Bell className="w-4 h-4" />,
      label: 'Alerte',
      tooltip: 'Créer une alerte (A)',
      action: () => onOpenAlert?.(),
    },
    {
      id: 'compare',
      icon: <TrendingUp className="w-4 h-4" />,
      label: 'Comparer',
      tooltip: 'Comparer avec d\'autres actifs (C)',
      action: () => onOpenComparator?.(),
    },
    {
      id: 'ai',
      icon: <MessageCircle className="w-4 h-4" />,
      label: 'IA',
      tooltip: 'Demander à l\'IA (I)',
      action: () => onOpenAIChat?.(),
    },
    {
      id: 'copy',
      icon: <Copy className="w-4 h-4" />,
      label: 'Copier',
      tooltip: 'Copier les infos',
      action: () => copyToClipboard(asset),
    },
    {
      id: 'share',
      icon: <Share2 className="w-4 h-4" />,
      label: 'Partager',
      tooltip: 'Partager cet actif',
      action: () => share(asset),
    },
  ];

  return (
    <motion.div
      className={cn(
        'bg-gradient-to-r from-bg-secondary/95 to-bg-secondary/90 border-b border-glass-border backdrop-blur-md',
        sticky && 'sticky top-0 z-30'
      )}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-3 flex items-center justify-between gap-4">
          {/* Asset info */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-surface flex items-center justify-center text-lg font-semibold">
              {asset.ticker[0]}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-text-primary">{asset.ticker}</p>
              <p className="text-xs text-text-muted truncate">{asset.name}</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 flex-wrap justify-end">
            {actions.map((action) => {
              const state = getActionState(action.id);
              const isLoading = state.loading || action.loading;

              return (
                <div key={action.id} className="relative">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => action.action()}
                    disabled={isLoading}
                    title={showTooltips ? action.tooltip : undefined}
                    className={cn(
                      'inline-flex items-center gap-1.5 px-3 py-2 rounded-lg transition-all text-sm font-medium',
                      action.isActive
                        ? 'bg-accent/20 text-accent border border-accent/30'
                        : 'bg-surface/50 text-text-secondary hover:text-text-primary hover:bg-surface border border-glass-border',
                      isLoading && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {isLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                    ) : state.success ? (
                      <Check className="w-4 h-4 text-score-green" />
                    ) : (
                      action.icon
                    )}
                    <span className="hidden sm:inline">{action.label}</span>
                  </motion.button>

                  {/* Success indicator */}
                  <AnimatePresence>
                    {state.success && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="absolute -top-2 -right-2"
                      >
                        <div className="w-6 h-6 rounded-full bg-score-green flex items-center justify-center">
                          <Check className="w-3.5 h-3.5 text-white" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}

            {/* Help button */}
            <div className="relative">
              <KeyboardShortcutsHelp />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default QuickActionsBar;
