'use client';

import { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/glass-card';
import { motion } from 'framer-motion';
import { ChevronRight } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// MORNING BRIEF CARD
// Reusable card component for Morning Brief sections
// ═══════════════════════════════════════════════════════════════════════════

interface MorningBriefCardProps {
  title: string;
  icon: ReactNode;
  children: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  variant?: 'default' | 'highlight' | 'alert';
  size?: 'sm' | 'md' | 'lg';
}

export function MorningBriefCard({
  title,
  icon,
  children,
  actionLabel,
  onAction,
  className,
  variant = 'default',
  size = 'md',
}: MorningBriefCardProps) {
  const variantStyles = {
    default: 'border-surface/40',
    highlight: 'border-score-green/30 bg-gradient-to-br from-score-green/5 to-transparent',
    alert: 'border-score-red/30 bg-gradient-to-br from-score-red/5 to-transparent',
  };

  const sizeStyles = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <GlassCard
        className={cn(
          'flex flex-col gap-4',
          variantStyles[variant],
          sizeStyles[size],
          'border',
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 flex items-center justify-center text-lg">
              {icon}
            </div>
            <h3 className="text-lg font-semibold text-text-primary">
              {title}
            </h3>
          </div>

          {actionLabel && onAction && (
            <motion.button
              onClick={onAction}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 rounded-lg',
                'text-sm font-medium text-score-blue',
                'hover:bg-score-blue/10 transition-all duration-200',
                'cursor-pointer'
              )}
              whileHover={{ x: 4 }}
            >
              {actionLabel}
              <ChevronRight className="w-4 h-4" />
            </motion.button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1">
          {children}
        </div>
      </GlassCard>
    </motion.div>
  );
}

export default MorningBriefCard;
