'use client';

import { Badge as BadgeType } from '@/types/gamification';
import { Lock, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import * as Tooltip from '@radix-ui/react-tooltip';

interface BadgeCardProps {
  badge: BadgeType;
}

const TIER_COLORS = {
  bronze: {
    bg: 'bg-amber-900/20',
    border: 'border-amber-700/40',
    text: 'text-amber-400',
    glow: 'shadow-[0_0_15px_rgba(180,83,9,0.3)]',
  },
  silver: {
    bg: 'bg-slate-500/20',
    border: 'border-slate-400/40',
    text: 'text-slate-300',
    glow: 'shadow-[0_0_15px_rgba(148,163,184,0.3)]',
  },
  gold: {
    bg: 'bg-yellow-500/20',
    border: 'border-yellow-400/40',
    text: 'text-yellow-300',
    glow: 'shadow-[0_0_15px_rgba(250,204,21,0.3)]',
  },
  platinum: {
    bg: 'bg-cyan-400/20',
    border: 'border-cyan-300/40',
    text: 'text-cyan-200',
    glow: 'shadow-[0_0_15px_rgba(34,211,238,0.3)]',
  },
};

export function BadgeCard({ badge }: BadgeCardProps) {
  const tierColors = TIER_COLORS[badge.tier];

  if (!badge.earned) {
    // Locked Badge
    return (
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <motion.div
            whileHover={{ y: 0 }}
            className={`
              relative p-4 rounded-xl border backdrop-blur-sm
              bg-surface/50 border-glass-border opacity-50
              transition-all duration-200 cursor-help
            `}
          >
            {/* Lock Overlay */}
            <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-black/30">
              <Lock className="w-6 h-6 text-text-muted" />
            </div>

            {/* Content (blurred) */}
            <div className="blur-sm pointer-events-none">
              <div
                className={`
                  w-12 h-12 rounded-lg flex items-center justify-center mb-3
                  ${tierColors.bg} ${tierColors.border}
                `}
              >
                <span className="text-xl">{badge.icon}</span>
              </div>
              <h3 className="font-semibold text-sm text-text-primary truncate">
                {badge.name}
              </h3>
              <p className="text-xs text-text-muted mt-1 line-clamp-2">
                {badge.description}
              </p>
            </div>
          </motion.div>
        </Tooltip.Trigger>
        <Tooltip.Content
          className="rounded-lg px-3 py-2 text-sm bg-surface border border-glass-border text-text-primary"
          sideOffset={5}
        >
          <p className="font-semibold mb-1">{badge.name}</p>
          <p className="text-xs text-text-secondary mb-2">{badge.description}</p>
          {badge.requirements && (
            <p className="text-xs text-accent">Requirements: {badge.requirements}</p>
          )}
        </Tooltip.Content>
      </Tooltip.Root>
    );
  }

  // Earned Badge
  return (
    <Tooltip.Root>
      <Tooltip.Trigger asChild>
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          whileHover={{ scale: 1.05, y: -4 }}
          className={`
            relative p-4 rounded-xl border backdrop-blur-sm
            ${tierColors.bg} ${tierColors.border} ${tierColors.glow}
            transition-all duration-200 cursor-pointer
            hover:border-opacity-100 group
          `}
        >
          {/* Earned Check */}
          <div className="absolute -top-2 -right-2">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: 'spring' }}
              className="relative"
            >
              <div className="w-6 h-6 rounded-full bg-accent flex items-center justify-center shadow-lg">
                <CheckCircle2 className="w-4 h-4 text-bg-primary" />
              </div>
            </motion.div>
          </div>

          {/* Icon */}
          <div
            className={`
              w-12 h-12 rounded-lg flex items-center justify-center mb-3
              ${tierColors.bg} ${tierColors.border}
              group-hover:scale-110 transition-transform
            `}
          >
            <span className="text-2xl">{badge.icon}</span>
          </div>

          {/* Content */}
          <h3 className={`font-semibold text-sm ${tierColors.text} truncate`}>
            {badge.name}
          </h3>
          <p className="text-xs text-text-muted mt-1 line-clamp-2">
            {badge.description}
          </p>

          {/* Tier Badge */}
          <div className="mt-3 pt-3 border-t border-glass-border">
            <span className={`text-xs font-medium ${tierColors.text} capitalize`}>
              {badge.tier} Badge
            </span>
          </div>
        </motion.div>
      </Tooltip.Trigger>
      <Tooltip.Content
        className="rounded-lg px-3 py-2 text-sm bg-surface border border-glass-border text-text-primary max-w-xs"
        sideOffset={5}
      >
        <p className="font-semibold mb-1">{badge.name}</p>
        <p className="text-xs text-text-secondary mb-2">{badge.description}</p>
        {badge.earned_at && (
          <p className="text-xs text-accent">
            Earned: {new Date(badge.earned_at).toLocaleDateString()}
          </p>
        )}
        <p className={`text-xs font-medium ${tierColors.text} mt-1 capitalize`}>
          {badge.tier} Badge
        </p>
      </Tooltip.Content>
    </Tooltip.Root>
  );
}
