'use client';

import { Flame } from 'lucide-react';
import { motion } from 'framer-motion';

interface StreakCounterProps {
  days: number;
  multiplier: number;
  isActive?: boolean;
}

export function StreakCounter({
  days,
  multiplier,
  isActive = true,
}: StreakCounterProps) {
  // Color intensity based on streak length
  const getStreakColor = (days: number) => {
    if (days === 0) return 'text-text-muted';
    if (days < 7) return 'text-orange-400';
    if (days < 14) return 'text-orange-500';
    if (days < 30) return 'text-red-500';
    return 'text-red-600';
  };

  const getBgColor = (days: number) => {
    if (days === 0) return 'bg-surface border-glass-border';
    if (days < 7) return 'bg-orange-500/10 border-orange-500/30';
    if (days < 14) return 'bg-orange-600/10 border-orange-500/40';
    if (days < 30) return 'bg-red-500/10 border-red-500/40';
    return 'bg-red-600/10 border-red-600/40';
  };

  return (
    <div className="space-y-2">
      {/* Streak Card */}
      <div
        className={`
          relative rounded-xl border p-4 transition-all duration-200
          ${getBgColor(days)}
        `}
      >
        {/* Pulsing animation for active streaks */}
        {days > 0 && isActive && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className={`absolute inset-0 rounded-xl pointer-events-none ${getBgColor(days)}`}
          />
        )}

        {/* Content */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Flame Icon */}
            <motion.div
              animate={
                days > 0 && isActive
                  ? { scale: [1, 1.1, 1], rotate: [0, 5, 0] }
                  : { scale: 1 }
              }
              transition={
                days > 0 && isActive
                  ? { duration: 1.5, repeat: Infinity }
                  : { duration: 0 }
              }
              className="flex-shrink-0"
            >
              <Flame
                className={`w-6 h-6 ${getStreakColor(days)}`}
                fill="currentColor"
              />
            </motion.div>

            {/* Streak Info */}
            <div>
              <p className="text-xs text-text-muted">Current Streak</p>
              <p className={`text-2xl font-bold ${getStreakColor(days)}`}>
                {days} {days === 1 ? 'day' : 'days'}
              </p>
            </div>
          </div>

          {/* Multiplier Badge */}
          {days > 0 && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="px-3 py-1 rounded-full bg-accent/20 text-accent text-sm font-bold"
            >
              ×{multiplier.toFixed(1)}
            </motion.div>
          )}
        </div>
      </div>

      {/* Streak Info */}
      {days > 0 ? (
        <p className="text-xs text-accent text-center">
          Keep it up! {multiplier > 1 ? `Earning ${((multiplier - 1) * 100).toFixed(0)}% bonus XP!` : ''}
        </p>
      ) : (
        <p className="text-xs text-text-muted text-center">
          Complete an action today to start your streak!
        </p>
      )}
    </div>
  );
}
