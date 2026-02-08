'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// LEVEL THRESHOLDS
// ═══════════════════════════════════════════════════════════════════════════

const LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2500, 4000, 6000, 10000];

const LEVEL_COLORS = [
  '#6B7280', // Level 1: Gray
  '#3B82F6', // Level 2: Blue
  '#06B6D4', // Level 3: Cyan
  '#19D38C', // Level 4: Green
  '#FBBF24', // Level 5: Amber
  '#F97316', // Level 6: Orange
  '#EF4444', // Level 7: Red
  '#EC4899', // Level 8: Pink
  '#A855F7', // Level 9: Purple
  '#8B5CF6', // Level 10: Violet
];

interface LevelProgressBarProps {
  level: number;
  currentXp: number;
  totalXp: number;
}

export function LevelProgressBar({
  level,
  currentXp,
  totalXp,
}: LevelProgressBarProps) {
  // Calculate progress to next level
  const currentLevelThreshold = LEVEL_THRESHOLDS[Math.max(0, level - 1)] || 0;
  const nextLevelThreshold = LEVEL_THRESHOLDS[Math.min(level, 9)] || LEVEL_THRESHOLDS[9];

  const xpInCurrentLevel = totalXp - currentLevelThreshold;
  const xpNeededForLevel = nextLevelThreshold - currentLevelThreshold;
  const progressPercent = Math.min(
    100,
    (xpInCurrentLevel / xpNeededForLevel) * 100
  );

  const currentColor = LEVEL_COLORS[Math.max(0, Math.min(level - 1, 9))];
  const nextColor = LEVEL_COLORS[Math.max(0, Math.min(level, 9))];

  const isMaxLevel = level >= 10;

  return (
    <div className="space-y-3">
      {/* Level Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
            style={{ backgroundColor: currentColor }}
          >
            {level}
          </div>
          <div>
            <p className="text-xs text-text-muted">Level {level}</p>
            <p className="text-sm font-semibold text-text-primary">
              {isMaxLevel ? 'Max Level' : `${xpInCurrentLevel} / ${xpNeededForLevel} XP`}
            </p>
          </div>
        </div>
        {!isMaxLevel && (
          <span className="text-xs px-2 py-1 rounded-lg bg-accent/10 text-accent">
            {Math.round(progressPercent)}%
          </span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="relative h-4 rounded-full overflow-hidden bg-surface border border-glass-border">
        {/* Animated fill */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progressPercent}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="h-full rounded-full"
          style={{
            background: `linear-gradient(90deg, ${currentColor}, ${nextColor})`,
            boxShadow: `0 0 20px ${currentColor}40`,
          }}
        />

        {/* Shine effect */}
        <motion.div
          animate={{ x: ['0%', '200%'] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white to-transparent opacity-20"
        />
      </div>

      {/* Next Level Info */}
      {!isMaxLevel && (
        <div className="text-xs text-text-muted text-center">
          Next level in {xpNeededForLevel - xpInCurrentLevel} XP
        </div>
      )}
    </div>
  );
}
