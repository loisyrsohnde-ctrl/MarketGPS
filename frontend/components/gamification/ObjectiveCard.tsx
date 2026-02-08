'use client';

import { Objective } from '@/types/gamification';
import { CheckCircle2, Clock, Target } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ObjectiveCardProps {
  objective: Objective;
}

export function ObjectiveCard({ objective }: ObjectiveCardProps) {
  const progressPercent = Math.min(
    100,
    (objective.progress / objective.target) * 100
  );

  const isCompleted = objective.completed;

  // Calculate time remaining
  const timeRemaining = new Date(objective.expires_at).getTime() - Date.now();
  const daysRemaining = Math.ceil(timeRemaining / (1000 * 60 * 60 * 24));

  const getTimestampLabel = () => {
    if (isCompleted) return 'Completed!';
    if (daysRemaining < 0) return 'Expired';
    if (objective.type === 'daily') return `${daysRemaining}h remaining`;
    return `${daysRemaining}d remaining`;
  };

  const getCategoryColor = (type: string) => {
    switch (type) {
      case 'daily':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
      case 'weekly':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
      default:
        return 'bg-accent/20 text-accent border-accent/30';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative p-4 rounded-xl border backdrop-blur-sm transition-all duration-200',
        isCompleted
          ? 'bg-score-green/5 border-score-green/30'
          : 'bg-surface border-glass-border hover:bg-surface-hover hover:border-glass-border-hover'
      )}
    >
      {/* Completion Animation */}
      {isCompleted && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-3 -right-3 z-10"
        >
          <div className="w-8 h-8 rounded-full bg-score-green flex items-center justify-center shadow-lg">
            <CheckCircle2 className="w-5 h-5 text-white" />
          </div>
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-sm text-text-primary">
              {objective.title}
            </h3>
            <span
              className={`text-xs px-2 py-0.5 rounded-full border font-medium ${getCategoryColor(objective.type)}`}
            >
              {objective.type === 'daily' ? '📅 Daily' : '📆 Weekly'}
            </span>
          </div>
          <p className="text-xs text-text-muted line-clamp-1">
            {objective.description}
          </p>
        </div>

        {/* Points Reward */}
        <div className="ml-3 text-right">
          <p className="text-xs text-text-muted">Reward</p>
          <p className="text-lg font-bold text-accent">+{objective.reward_points}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2 mb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs text-text-secondary">
            <Target className="w-3.5 h-3.5" />
            <span>
              {objective.progress} / {objective.target}
            </span>
          </div>
          <span className="text-xs font-semibold text-accent">
            {Math.round(progressPercent)}%
          </span>
        </div>

        {/* Progress Bar Fill */}
        <div className="h-2 rounded-full overflow-hidden bg-surface border border-glass-border">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progressPercent}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className={cn(
              'h-full rounded-full transition-colors',
              isCompleted
                ? 'bg-gradient-to-r from-score-green to-accent'
                : 'bg-gradient-to-r from-accent to-accent-light'
            )}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-text-muted capitalize">
          {objective.category}
        </span>
        <div className="flex items-center gap-1 text-text-muted">
          <Clock className="w-3.5 h-3.5" />
          <span>{getTimestampLabel()}</span>
        </div>
      </div>
    </motion.div>
  );
}
