'use client';

import { Trophy, Flame, Target, Award } from 'lucide-react';
import { MorningBriefCard } from './MorningBriefCard';
import { motion } from 'framer-motion';
import type { GamificationStatus, GamificationLevel } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// GAMIFICATION WIDGET
// Shows progress, level, and weekly objectives
// ═══════════════════════════════════════════════════════════════════════════

interface GamificationWidgetProps {
  status: GamificationStatus;
  onViewDetails?: () => void;
}

const getLevelIcon = (level: GamificationLevel): string => {
  switch (level) {
    case 'novice':
      return '🌱';
    case 'apprentice':
      return '📚';
    case 'analyst':
      return '🔬';
    case 'expert':
      return '⭐';
    case 'legend':
      return '👑';
    default:
      return '🎯';
  }
};

const getLevelColor = (level: GamificationLevel): string => {
  switch (level) {
    case 'novice':
      return 'text-text-muted';
    case 'apprentice':
      return 'text-score-blue';
    case 'analyst':
      return 'text-score-green';
    case 'expert':
      return 'text-score-yellow';
    case 'legend':
      return 'text-score-red';
    default:
      return 'text-text-primary';
  }
};

export function GamificationWidget({
  status,
  onViewDetails,
}: GamificationWidgetProps) {
  const isLevelingUp = status.points % 1000 < 100;
  const weeklyProgress = (status.weeklyPoints / status.weeklyTarget) * 100;

  const gamificationVariants = {
    container: {
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: {
          staggerChildren: 0.1,
          delayChildren: 0.15,
        },
      },
    },
    item: {
      hidden: { opacity: 0, scale: 0.95 },
      show: { opacity: 1, scale: 1 },
    },
  };

  return (
    <MorningBriefCard
      title="Weekly Challenge"
      icon={isLevelingUp ? <Flame className="w-6 h-6 text-score-red animate-pulse" /> : <Trophy className="w-6 h-6" />}
      actionLabel="Details"
      onAction={onViewDetails}
      variant={isLevelingUp ? 'highlight' : 'default'}
    >
      <motion.div
        variants={gamificationVariants.container}
        initial="hidden"
        animate="show"
        className="flex flex-col gap-4"
      >
        {/* Level Card */}
        <motion.div
          variants={gamificationVariants.item}
          className="p-4 rounded-lg bg-gradient-to-br from-surface to-surface/50 border border-surface/50"
        >
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs text-text-secondary mb-1">Current Level</p>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getLevelIcon(status.level)}</span>
                <div>
                  <p className={`text-lg font-bold capitalize ${getLevelColor(status.level)}`}>
                    {status.level}
                  </p>
                  <p className="text-xs text-text-muted">
                    {status.points.toLocaleString()} pts
                  </p>
                </div>
              </div>
            </div>

            {status.streakDays > 0 && (
              <div className="text-right">
                <p className="text-xs text-text-secondary mb-1">Streak</p>
                <div className="flex items-center gap-1 text-lg font-bold text-score-red">
                  <Flame className="w-5 h-5" />
                  <span>{status.streakDays}</span>
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Weekly Progress */}
        <motion.div
          variants={gamificationVariants.item}
          className="flex flex-col gap-2"
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Target className="w-4 h-4" />
              Weekly Progress
            </p>
            <p className="text-sm font-bold text-text-primary">
              {status.weeklyPoints}/{status.weeklyTarget}
            </p>
          </div>

          <div className="flex-1 h-3 bg-surface rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-score-blue via-score-green to-score-yellow"
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(weeklyProgress, 100)}%` }}
              transition={{ duration: 1, ease: 'easeInOut' }}
            />
          </div>

          <p className="text-xs text-text-muted">
            {Math.min(weeklyProgress, 100).toFixed(0)}% complete
            {weeklyProgress < 100 && (
              <span>
                {' '}
                • {Math.max(0, status.weeklyTarget - status.weeklyPoints)} pts remaining
              </span>
            )}
          </p>
        </motion.div>

        {/* Active Objectives */}
        {status.objectives.length > 0 && (
          <motion.div
            variants={gamificationVariants.item}
            className="flex flex-col gap-2"
          >
            <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Award className="w-4 h-4" />
              Active Objectives
            </p>

            <div className="space-y-2">
              {status.objectives.slice(0, 3).map((objective) => (
                <div key={objective.id} className="p-2 rounded-lg bg-surface/50">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-xs font-semibold text-text-primary">
                      {objective.title}
                    </p>
                    {objective.isCompleted && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-score-green/20 text-score-green font-bold">
                        ✓ Complete
                      </span>
                    )}
                  </div>

                  <div className="flex-1 h-2 bg-surface rounded-full overflow-hidden mb-1">
                    <motion.div
                      className={`h-full ${
                        objective.isCompleted
                          ? 'bg-score-green'
                          : 'bg-gradient-to-r from-score-blue to-score-cyan'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min((objective.progress / objective.target) * 100, 100)}%` }}
                      transition={{ duration: 0.6 }}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <p className="text-xs text-text-muted">
                      {objective.progress}/{objective.target}
                    </p>
                    <p className="text-xs text-score-yellow font-semibold">
                      +{objective.reward} pts
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {status.objectives.filter(o => !o.isCompleted).length === 0 && (
              <p className="text-xs text-text-secondary text-center py-2">
                🎉 All objectives completed!
              </p>
            )}
          </motion.div>
        )}
      </motion.div>
    </MorningBriefCard>
  );
}

export default GamificationWidget;
