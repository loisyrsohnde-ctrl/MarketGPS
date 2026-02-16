'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface AcademyProgressProps {
  value: number;
  label?: string;
  showPercentage?: boolean;
}

export function AcademyProgress({
  value,
  label,
  showPercentage = true,
}: AcademyProgressProps) {
  const clampedValue = Math.min(Math.max(value, 0), 100);

  return (
    <div className="w-full space-y-2">
      {(label || showPercentage) && (
        <div className="flex items-center justify-between">
          {label && <span className="text-sm font-medium text-text-primary">{label}</span>}
          {showPercentage && (
            <span className="text-sm font-semibold text-accent">{clampedValue}%</span>
          )}
        </div>
      )}

      <div
        className={cn(
          'w-full h-2 rounded-full overflow-hidden',
          'bg-surface border border-glass-border'
        )}
      >
        <motion.div
          className="h-full bg-gradient-to-r from-accent to-accent/80"
          initial={{ width: 0 }}
          animate={{ width: `${clampedValue}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}
