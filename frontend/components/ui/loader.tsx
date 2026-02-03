'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// LOADER COMPONENT
// Animated loading spinner with variants
// ═══════════════════════════════════════════════════════════════════════════

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'pulse' | 'dots';
  className?: string;
}

export function Loader({ size = 'md', variant = 'spinner', className }: LoaderProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-10 h-10',
    lg: 'w-16 h-16',
  };

  if (variant === 'pulse') {
    return (
      <motion.div
        className={cn('rounded-full bg-score-blue', sizeClasses[size], className)}
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />
    );
  }

  if (variant === 'dots') {
    return (
      <div className={cn('flex gap-2 items-center justify-center', className)}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full bg-score-blue"
            animate={{ y: [0, -8, 0] }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay: i * 0.1,
            }}
          />
        ))}
      </div>
    );
  }

  // Default spinner variant
  return (
    <motion.div
      className={cn(
        'border-2 border-surface border-t-score-blue rounded-full',
        sizeClasses[size],
        className
      )}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    />
  );
}

export default Loader;
