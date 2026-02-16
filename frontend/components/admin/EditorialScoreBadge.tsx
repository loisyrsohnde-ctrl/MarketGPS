'use client';

import { Award } from 'lucide-react';

interface EditorialScoreBadgeProps {
  score: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function getScoreLevel(score: number) {
  if (score >= 80)
    return {
      level: 'Excellent',
      color:
        'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
    };
  if (score >= 60)
    return {
      level: 'Bon',
      color:
        'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
    };
  if (score >= 40)
    return {
      level: 'Moyen',
      color:
        'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    };
  return {
    level: 'Faible',
    color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  };
}

const sizeStyles = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
};

const iconSizes = {
  sm: 'h-3 w-3',
  md: 'h-4 w-4',
  lg: 'h-5 w-5',
};

export function EditorialScoreBadge({
  score,
  showLabel = true,
  size = 'md',
}: EditorialScoreBadgeProps) {
  const { level, color } = getScoreLevel(score);

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${color} ${sizeStyles[size]}`}
    >
      {score >= 60 && <Award className={iconSizes[size]} />}
      {showLabel ? level : `${score.toFixed(0)}`}
    </span>
  );
}

/**
 * Small progress bar for a single score component (0-100).
 */
export function ScoreComponentBar({
  label,
  value,
  maxValue = 100,
}: {
  label: string;
  value: number;
  maxValue?: number;
}) {
  const pct = Math.min(100, Math.max(0, (value / maxValue) * 100));

  let barColor = 'bg-gray-400 dark:bg-gray-600';
  if (pct >= 80) barColor = 'bg-emerald-500 dark:bg-emerald-400';
  else if (pct >= 60) barColor = 'bg-amber-500 dark:bg-amber-400';
  else if (pct >= 40) barColor = 'bg-yellow-500 dark:bg-yellow-400';

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-28 shrink-0 text-gray-600 dark:text-gray-400 truncate">
        {label}
      </span>
      <div className="flex-1 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right font-medium text-gray-700 dark:text-gray-300">
        {value.toFixed(0)}
      </span>
    </div>
  );
}
