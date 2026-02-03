'use client';

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// TOAST COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
  onClose?: () => void;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const typeConfig = {
  success: {
    bg: 'bg-score-green/10',
    border: 'border-score-green/30',
    text: 'text-score-green',
    dot: 'bg-score-green',
  },
  error: {
    bg: 'bg-score-red/10',
    border: 'border-score-red/30',
    text: 'text-score-red',
    dot: 'bg-score-red',
  },
  warning: {
    bg: 'bg-score-yellow/10',
    border: 'border-score-yellow/30',
    text: 'text-score-yellow',
    dot: 'bg-score-yellow',
  },
  info: {
    bg: 'bg-accent/10',
    border: 'border-accent/30',
    text: 'text-accent',
    dot: 'bg-accent',
  },
};

export function Toast({
  message,
  type = 'info',
  duration = 3000,
  onClose,
  icon,
  action,
}: ToastProps) {
  useEffect(() => {
    if (duration && duration > 0) {
      const timer = setTimeout(() => {
        onClose?.();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const config = typeConfig[type];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ type: 'spring', damping: 15, stiffness: 300 }}
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm',
        config.bg,
        config.border,
        config.text
      )}
    >
      {/* Indicator dot */}
      <div className={cn('w-2 h-2 rounded-full flex-shrink-0', config.dot)} />

      {/* Content */}
      <div className="flex-1 flex items-center gap-3">
        {icon && <div className="flex-shrink-0">{icon}</div>}
        <p className="text-sm font-medium">{message}</p>
      </div>

      {/* Action button */}
      {action && (
        <button
          onClick={action.onClick}
          className="text-sm font-medium underline hover:opacity-80 transition-opacity flex-shrink-0"
        >
          {action.label}
        </button>
      )}

      {/* Close button */}
      {onClose && (
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={onClose}
          className={cn(
            'p-1 rounded-md hover:bg-white/20 transition-colors flex-shrink-0',
            config.text
          )}
        >
          <X className="w-4 h-4" />
        </motion.button>
      )}
    </motion.div>
  );
}

export default Toast;
