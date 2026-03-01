'use client';

import { Flame, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';

interface StreakCounterProps {
  days: number;
  multiplier: number;
  isActive?: boolean;
  hasActivityToday?: boolean;
}

export function StreakCounter({
  days,
  multiplier,
  isActive = true,
  hasActivityToday = true,
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

  const streakAtRisk = days > 0 && !hasActivityToday;

  return (
    <div className="space-y-2">
      {/* Streak at risk warning */}
      {streakAtRisk && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30"
        >
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <p className="text-xs text-amber-300">
            Votre s&eacute;rie de <strong>{days} jours</strong> est en danger !{' '}
            <Link href="/dashboard" className="text-amber-400 underline">
              Consultez un score
            </Link>{' '}
            pour la maintenir.
          </p>
        </motion.div>
      )}

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
              <p className="text-xs text-text-muted">S&eacute;rie en cours</p>
              <p className={`text-2xl font-bold ${getStreakColor(days)}`}>
                {days} {days === 1 ? 'jour' : 'jours'}
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
              &times;{multiplier.toFixed(1)}
            </motion.div>
          )}
        </div>
      </div>

      {/* Streak Info */}
      {days > 0 ? (
        <p className="text-xs text-accent text-center">
          Continuez ! {multiplier > 1 ? `Bonus XP : +${((multiplier - 1) * 100).toFixed(0)}%` : ''}
        </p>
      ) : (
        <p className="text-xs text-text-muted text-center">
          Consultez un score pour d&eacute;marrer votre s&eacute;rie !
        </p>
      )}
    </div>
  );
}
