'use client';

import { Flame } from 'lucide-react';

interface ViralityBadgeProps {
  score: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function getViralityLevel(score: number) {
  if (score > 10) return { level: 'Extrême', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' };
  if (score > 5) return { level: 'Très Élevée', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' };
  if (score > 2) return { level: 'Élevée', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' };
  return { level: 'Basse', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300' };
}

const sizeStyles = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
};

export function ViralityBadge({ score, showLabel = true, size = 'md' }: ViralityBadgeProps) {
  const { level, color } = getViralityLevel(score);

  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-medium ${color} ${sizeStyles[size]}`}>
      {score > 2 && <Flame className={size === 'sm' ? 'h-3 w-3' : size === 'md' ? 'h-4 w-4' : 'h-5 w-5'} />}
      {showLabel ? level : `${score.toFixed(1)}x`}
    </span>
  );
}
