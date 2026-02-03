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
