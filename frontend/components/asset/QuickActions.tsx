'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuickActions } from '@/hooks/useQuickActions';
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
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { shareAssetOnWhatsApp } from '@/lib/share';
import { track } from '@/lib/analytics';
import Toast from '@/components/feedback/Toast';

// ═══════════════════════════════════════════════════════════════════════════
// QUICK ACTIONS COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface QuickActionsProps {
  asset: Asset;
  onOpenAlert?: () => void;
  onOpenComparator?: () => void;
  onOpenAIChat?: () => void;
  userId?: string;
  variant?: 'horizontal' | 'vertical' | 'floating';
}

interface ActionItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  tooltip: string;
  action: () => Promise<void> | void;
  isActive?: boolean;
  loading?: boolean;
  color?: string;
}

interface ToastMessage {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

const Toast_: React.FC<{ message: ToastMessage; onClose: () => void }> = ({ message, onClose }) => (
  <motion.div
    initial={{ opacity: 0, y: -10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    className={cn(
      'px-4 py-3 rounded-lg text-sm font-medium flex items-center gap-2',
      message.type === 'success' && 'bg-score-green/20 text-score-green',
      message.type === 'error' && 'bg-score-red/20 text-score-red',
      message.type === 'info' && 'bg-accent/20 text-accent'
    )}
  >
    <span>{message.message}</span>
  </motion.div>
);

export function QuickActions({
  asset,
  onOpenAlert,
  onOpenComparator,
  onOpenAIChat,
  userId = 'default',
  variant = 'horizontal',
}: QuickActionsProps) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [showMenu, setShowMenu] = useState(false);

  const { isInWatchlist, toggleWatchlist, copyToClipboard, share, isToggling } =
    useQuickActions({
      assetId: asset.asset_id,
      ticker: asset.ticker,
      userId,
      marketScope: asset.market_scope,
      onActionComplete: (action, success) => {
        addToast(
          success
            ? getSuccessMessage(action)
            : 'Erreur lors de l\'action',
          success ? 'success' : 'error'
        );
      },
    });

  const addToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  const getSuccessMessage = (action: string): string => {
    const messages: Record<string, string> = {
      watchlist: isInWatchlist ? 'Retiré de la watchlist' : 'Ajouté à la watchlist',
      alert: 'Alerte créée',
      comparator: 'Comparateur ouvert',
      ai: 'Chat IA ouvert',
      copy: 'Infos copiées',
      share: 'Partagé avec succès',
    };
    return messages[action] || 'Action complétée';
  };

  const actions: ActionItem[] = [
    {
      id: 'watchlist',
      label: isInWatchlist ? 'Suivi' : 'Ajouter',
      icon: isInWatchlist ? (
        <Star className="w-4 h-4 fill-current" />
      ) : (
        <StarOff className="w-4 h-4" />
      ),
      tooltip: isInWatchlist ? 'Retirer de la watchlist' : 'Ajouter à la watchlist',
      action: () => toggleWatchlist(),
      isActive: isInWatchlist,
      loading: isToggling,
    },
    {
      id: 'alert',
      label: 'Alerte',
      icon: <Bell className="w-4 h-4" />,
      tooltip: 'Créer une alerte',
      action: () => {
        onOpenAlert?.();
        addToast('Modal d\'alerte ouverte', 'info');
      },
      color: 'accent',
    },
    {
      id: 'compare',
      label: 'Comparer',
      icon: <TrendingUp className="w-4 h-4" />,
      tooltip: 'Comparer avec d\'autres actifs',
      action: () => {
        onOpenComparator?.();
        addToast('Comparateur ouvert', 'info');
      },
    },
    {
      id: 'ai',
      label: 'IA',
      icon: <MessageCircle className="w-4 h-4" />,
      tooltip: 'Demander à l\'IA',
      action: () => {
        onOpenAIChat?.();
        addToast('Chat IA ouvert', 'info');
      },
      color: 'accent',
    },
    {
      id: 'copy',
      label: 'Copier',
      icon: <Copy className="w-4 h-4" />,
      tooltip: 'Copier les infos',
      action: () => copyToClipboard(asset),
    },
    {
      id: 'share',
      label: 'Partager',
      icon: <Share2 className="w-4 h-4" />,
      tooltip: 'Partager cet actif',
      action: () => share(asset),
    },
    {
      id: 'whatsapp',
      label: 'WhatsApp',
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
        </svg>
      ),
      tooltip: 'Partager sur WhatsApp',
      action: () => {
        shareAssetOnWhatsApp(asset.ticker, asset.score_total ?? null);
        track.shareAction('whatsapp', 'asset');
      },
      color: 'emerald',
    },
  ];

  if (variant === 'floating') {
    return (
      <div className="fixed bottom-6 right-6 z-40">
        {/* Floating menu */}
        <motion.div
          animate={{ scale: showMenu ? 1 : 0 }}
          initial={{ scale: 0 }}
          transition={{ type: 'spring', damping: 15, stiffness: 300 }}
          className="absolute bottom-16 right-0"
        >
          <AnimatePresence>
            {showMenu && (
              <motion.div className="flex flex-col gap-3 p-4 bg-bg-secondary border border-glass-border rounded-2xl shadow-2xl">
                {actions.map((action) => (
                  <motion.button
                    key={action.id}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={async () => {
                      await action.action();
                      setShowMenu(false);
                    }}
                    disabled={action.loading}
                    title={action.tooltip}
                    className={cn(
                      'w-11 h-11 rounded-lg flex items-center justify-center transition-all',
                      action.isActive
                        ? 'bg-accent text-white'
                        : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-hover',
                      action.loading && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {action.loading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
                    ) : (
                      action.icon
                    )}
                  </motion.button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Main button */}
        <motion.button
          onClick={() => setShowMenu(!showMenu)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
          className="w-14 h-14 rounded-full bg-gradient-to-br from-accent to-accent-dark text-white shadow-lg hover:shadow-xl transition-shadow flex items-center justify-center"
        >
          <Zap className="w-6 h-6" />
        </motion.button>
      </div>
    );
  }

  if (variant === 'vertical') {
    return (
      <div className="flex flex-col gap-2">
        {actions.map((action, index) => (
          <motion.button
            key={action.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => action.action()}
            disabled={action.loading}
            title={action.tooltip}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium',
              action.isActive
                ? 'bg-accent text-white'
                : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-hover',
              action.loading && 'opacity-50 cursor-not-allowed'
            )}
          >
            {action.loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
            ) : (
              action.icon
            )}
            <span>{action.label}</span>
          </motion.button>
        ))}
      </div>
    );
  }

  // Horizontal variant (default)
  return (
    <div className="space-y-4">
      {/* Action buttons */}
      <div className="flex flex-wrap gap-2">
        {actions.map((action, index) => (
          <motion.button
            key={action.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => action.action()}
            disabled={action.loading}
            title={action.tooltip}
            className={cn(
              'inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium',
              action.isActive
                ? 'bg-accent text-white'
                : 'bg-surface text-text-secondary hover:text-text-primary hover:bg-surface-hover',
              action.loading && 'opacity-50 cursor-not-allowed'
            )}
          >
            {action.loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" />
            ) : (
              action.icon
            )}
            <span className="hidden sm:inline">{action.label}</span>
          </motion.button>
        ))}
      </div>

      {/* Toast notifications */}
      <AnimatePresence>
        {toasts.length > 0 && (
          <div className="space-y-2">
            {toasts.map((toast) => (
              <Toast_
                key={toast.id}
                message={toast}
                onClose={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
              />
            ))}
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default QuickActions;
