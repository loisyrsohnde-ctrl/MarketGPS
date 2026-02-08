'use client';

import { useState } from 'react';
import { useGamification } from '@/hooks/useGamification';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy,
  Medal,
  Target,
  Flame,
  Loader2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Pill } from '@/components/ui/badge';
import { LevelProgressBar } from './LevelProgressBar';
import { StreakCounter } from './StreakCounter';
import { BadgeCard } from './BadgeCard';
import { ObjectiveCard } from './ObjectiveCard';

// ═══════════════════════════════════════════════════════════════════════════
// GAMIFICATION HUB COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

type TabType = 'overview' | 'badges' | 'leaderboard' | 'objectives';

export function GamificationHub() {
  const { profile, badges, objectives, leaderboard, loading, error, refetch } =
    useGamification();
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  // Separate objectives by type
  const dailyObjectives = objectives?.filter((o) => o.type === 'daily') || [];
  const weeklyObjectives = objectives?.filter((o) => o.type === 'weekly') || [];

  // Separate badges by earned status
  const earnedBadges = badges?.filter((b) => b.earned) || [];
  const lockedBadges = badges?.filter((b) => !b.earned) || [];

  if (error && !profile) {
    return (
      <div className="space-y-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
              <Trophy className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text-primary">
                Gamification Hub
              </h1>
              <p className="text-text-secondary">
                Track your progress and unlock rewards
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            disabled={loading}
          >
            <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
          </Button>
        </div>

        <GlassCard className="border-score-red/30 bg-score-red/5">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-8 h-8 text-score-red flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-text-primary">Error Loading</h3>
              <p className="text-sm text-text-secondary">{error}</p>
            </div>
          </div>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
            <Trophy className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">
              Gamification Hub
            </h1>
            <p className="text-text-secondary">
              Track your progress and unlock rewards
            </p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => refetch()}
          disabled={loading}
        >
          <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-glass-border pb-2 overflow-x-auto">
        <Pill
          active={activeTab === 'overview'}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </Pill>
        <Pill
          active={activeTab === 'badges'}
          onClick={() => setActiveTab('badges')}
        >
          🏆 Badges {earnedBadges.length > 0 && `(${earnedBadges.length})`}
        </Pill>
        <Pill
          active={activeTab === 'leaderboard'}
          onClick={() => setActiveTab('leaderboard')}
        >
          🎯 Leaderboard
        </Pill>
        <Pill
          active={activeTab === 'objectives'}
          onClick={() => setActiveTab('objectives')}
        >
          ⭐ Objectives
        </Pill>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {loading && !profile ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="ml-3 text-text-secondary">Loading your profile...</span>
              </div>
            ) : profile ? (
              <>
                {/* Level & Streak Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Level Progress */}
                  <GlassCardAccent glow>
                    <div className="p-6">
                      <LevelProgressBar
                        level={profile.level}
                        currentXp={profile.current_xp}
                        totalXp={profile.total_xp}
                      />
                    </div>
                  </GlassCardAccent>

                  {/* Streak Counter */}
                  <GlassCardAccent glow>
                    <div className="p-6">
                      <StreakCounter
                        days={profile.streak_days}
                        multiplier={profile.streak_multiplier}
                        isActive={profile.streak_days > 0}
                      />
                    </div>
                  </GlassCardAccent>
                </div>

                {/* Points & Stats */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {/* Total Points */}
                  <GlassCard className="p-4 text-center">
                    <p className="text-text-muted text-sm mb-2">Total Points</p>
                    <p className="text-3xl font-bold text-accent">
                      {profile.points.toLocaleString()}
                    </p>
                  </GlassCard>

                  {/* Badges Earned */}
                  <GlassCard className="p-4 text-center">
                    <p className="text-text-muted text-sm mb-2">Badges</p>
                    <p className="text-3xl font-bold text-accent">
                      {profile.badges_earned}
                    </p>
                  </GlassCard>

                  {/* Multiplier Bonus */}
                  <GlassCard className="p-4 text-center md:col-span-1 col-span-2">
                    <p className="text-text-muted text-sm mb-2">XP Multiplier</p>
                    <p className="text-3xl font-bold text-score-green">
                      ×{profile.streak_multiplier.toFixed(1)}
                    </p>
                  </GlassCard>
                </div>

                {/* Quick Objectives Preview */}
                {(dailyObjectives.length > 0 || weeklyObjectives.length > 0) && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Target className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">
                        Active Objectives
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {dailyObjectives.slice(0, 2).map((obj) => (
                        <ObjectiveCard key={obj.objective_id} objective={obj} />
                      ))}
                      {weeklyObjectives.slice(0, 2).map((obj) => (
                        <ObjectiveCard key={obj.objective_id} objective={obj} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </motion.div>
        )}

        {/* BADGES TAB */}
        {activeTab === 'badges' && (
          <motion.div
            key="badges"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {loading && !badges ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="ml-3 text-text-secondary">Loading badges...</span>
              </div>
            ) : badges && badges.length > 0 ? (
              <>
                {/* Earned Badges */}
                {earnedBadges.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <Medal className="w-5 h-5 text-accent" />
                      <h3 className="font-semibold text-text-primary">
                        Earned Badges ({earnedBadges.length})
                      </h3>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {earnedBadges.map((badge) => (
                        <BadgeCard key={badge.badge_id} badge={badge} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Locked Badges */}
                {lockedBadges.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="font-semibold text-text-primary">
                      Locked Badges ({lockedBadges.length})
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      {lockedBadges.map((badge) => (
                        <BadgeCard key={badge.badge_id} badge={badge} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <GlassCard className="p-8 text-center">
                <p className="text-text-muted">No badges yet. Start earning points!</p>
              </GlassCard>
            )}
          </motion.div>
        )}

        {/* LEADERBOARD TAB */}
        {activeTab === 'leaderboard' && (
          <motion.div
            key="leaderboard"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {loading && !leaderboard ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="ml-3 text-text-secondary">Loading leaderboard...</span>
              </div>
            ) : leaderboard && leaderboard.length > 0 ? (
              <div className="space-y-2">
                {leaderboard.map((entry, index) => (
                  <motion.div
                    key={entry.user_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={cn(
                      'p-4 rounded-xl border backdrop-blur-sm transition-all',
                      index === 0
                        ? 'bg-accent/10 border-accent/30 shadow-glow'
                        : 'bg-surface border-glass-border hover:bg-surface-hover'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      {/* Rank & User */}
                      <div className="flex items-center gap-4 flex-1">
                        <div className="relative">
                          <div
                            className={cn(
                              'w-10 h-10 rounded-full flex items-center justify-center font-bold',
                              index === 0 && 'bg-yellow-500/20 text-yellow-300',
                              index === 1 && 'bg-slate-400/20 text-slate-300',
                              index === 2 && 'bg-amber-700/20 text-amber-400',
                              index >= 3 && 'bg-surface-hover text-text-secondary'
                            )}
                          >
                            {index === 0 && '🥇'}
                            {index === 1 && '🥈'}
                            {index === 2 && '🥉'}
                            {index >= 3 && `#${entry.rank}`}
                          </div>
                        </div>
                        <div>
                          <p className="font-semibold text-text-primary">
                            {entry.display_name}
                          </p>
                          <p className="text-xs text-text-muted">
                            Level {entry.level} • {entry.badges_count} badges
                          </p>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center gap-6">
                        <div className="text-right">
                          <p className="text-xs text-text-muted">Points</p>
                          <p className="font-bold text-accent">
                            {entry.total_points.toLocaleString()}
                          </p>
                        </div>
                        {entry.streak_days > 0 && (
                          <div className="flex items-center gap-1 text-orange-400">
                            <Flame className="w-4 h-4" fill="currentColor" />
                            <span className="text-sm font-bold">
                              {entry.streak_days}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <GlassCard className="p-8 text-center">
                <p className="text-text-muted">No leaderboard data available.</p>
              </GlassCard>
            )}
          </motion.div>
        )}

        {/* OBJECTIVES TAB */}
        {activeTab === 'objectives' && (
          <motion.div
            key="objectives"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {loading && !objectives ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 text-accent animate-spin" />
                <span className="ml-3 text-text-secondary">Loading objectives...</span>
              </div>
            ) : objectives && objectives.length > 0 ? (
              <>
                {/* Daily Objectives */}
                {dailyObjectives.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-300">
                        📅
                      </div>
                      <h3 className="font-semibold text-text-primary">
                        Daily Objectives ({dailyObjectives.length})
                      </h3>
                    </div>
                    <div className="space-y-3">
                      {dailyObjectives.map((obj) => (
                        <ObjectiveCard key={obj.objective_id} objective={obj} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Weekly Objectives */}
                {weeklyObjectives.length > 0 && (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-300">
                        📆
                      </div>
                      <h3 className="font-semibold text-text-primary">
                        Weekly Objectives ({weeklyObjectives.length})
                      </h3>
                    </div>
                    <div className="space-y-3">
                      {weeklyObjectives.map((obj) => (
                        <ObjectiveCard key={obj.objective_id} objective={obj} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <GlassCard className="p-8 text-center">
                <p className="text-text-muted">
                  No objectives available right now.
                </p>
              </GlassCard>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
