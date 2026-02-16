'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ChevronDown,
  CheckCircle2,
  Clock,
  Target,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { AcademyProgress } from '@/components/academy/AcademyProgress';
import { fetchUserProgress, fetchProgressStats, fetchParts } from '@/lib/academy-api';
import { AcademyUserProgress, AcademyPart } from '@/lib/academy-types';

interface ProgressStats {
  total_lessons: number;
  completed_lessons: number;
  average_score: number;
  estimated_time_remaining: number;
  overall_percentage: number;
}

export default function ProgressionPage() {
  const [userProgress, setUserProgress] = useState<AcademyUserProgress[]>([]);
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [expandedParts, setExpandedParts] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        // TODO: Get actual user ID from auth context
        const userId = 'user_id';

        const progressData = await fetchUserProgress(userId);
        setUserProgress(progressData);

        const statsData = await fetchProgressStats(userId);
        setStats(statsData);

        const partsData = await fetchParts();
        setParts(partsData);

        // Expand first part by default
        if (partsData.length > 0) {
          setExpandedParts(new Set([partsData[0].id]));
        }
      } catch (error) {
        console.error('Failed to load progress data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const togglePart = (partId: string) => {
    const newExpanded = new Set(expandedParts);
    if (newExpanded.has(partId)) {
      newExpanded.delete(partId);
    } else {
      newExpanded.add(partId);
    }
    setExpandedParts(newExpanded);
  };

  const getPartProgress = (part: AcademyPart) => {
    const partLessons = userProgress.filter((p) => {
      // Filter lessons belonging to this part
      return p.lesson_id.toString().startsWith(part.id);
    });

    if (partLessons.length === 0) return 0;
    const completed = partLessons.filter((p) => p.status === 'completed').length;
    return Math.round((completed / partLessons.length) * 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Chargement de la progression...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-12">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-8">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl font-bold text-text-primary mb-8"
        >
          Votre Progression
        </motion.h1>

        {/* Overall Progress */}
        {stats && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className={cn('p-8 rounded-lg mb-8', 'bg-surface border border-glass-border')}
          >
            <AcademyProgress
              value={stats.overall_percentage}
              label="Progression globale"
              showPercentage={true}
            />
          </motion.div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {[
              {
                icon: CheckCircle2,
                label: 'Leçons complétées',
                value: `${stats.completed_lessons}/${stats.total_lessons}`,
                color: 'accent',
              },
              {
                icon: Target,
                label: 'Score moyen',
                value: `${Math.round(stats.average_score)}%`,
                color: 'accent',
              },
              {
                icon: Clock,
                label: 'Temps restant (estimé)',
                value: `${Math.round(stats.estimated_time_remaining / 60)}h`,
                color: 'accent',
              },
              {
                icon: TrendingUp,
                label: 'Taux de progression',
                value: `${Math.round(stats.overall_percentage)}%`,
                color: 'accent',
              },
            ].map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 * (idx + 1) }}
                  className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}
                >
                  <Icon className={cn('w-8 h-8 mb-3', 'text-accent')} />
                  <p className="text-text-primary/70 text-sm">{stat.label}</p>
                  <p className="text-2xl font-bold text-text-primary mt-2">{stat.value}</p>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Progress by Part */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-4"
        >
          <h2 className="text-2xl font-bold text-text-primary mb-6">Progression par Module</h2>

          {parts.map((part, partIdx) => {
            const isExpanded = expandedParts.has(part.id);
            const progress = getPartProgress(part);

            return (
              <div key={part.id} className={cn('rounded-lg', 'bg-surface border border-glass-border')}>
                {/* Part Header */}
                <button
                  onClick={() => togglePart(part.id)}
                  className="w-full flex items-center gap-4 p-6 hover:bg-glass-border/50 transition-colors"
                >
                  <ChevronDown
                    className={cn(
                      'w-5 h-5 text-accent flex-shrink-0 transition-transform',
                      isExpanded ? 'rotate-0' : '-rotate-90'
                    )}
                  />
                  <div className="flex-1 text-left">
                    <h3 className="font-semibold text-text-primary">{part.title_fr}</h3>
                  </div>
                  <div className="flex items-center gap-4 flex-shrink-0">
                    <div className="w-32">
                      <AcademyProgress value={progress} showPercentage={true} />
                    </div>
                  </div>
                </button>

                {/* Modules Details */}
                {isExpanded && (
                  <div className="px-6 pb-6 pt-2 border-t border-glass-border space-y-3">
                    {part.modules?.map((module) => {
                      const moduleLessons = userProgress.filter(
                        (p) => p.lesson_id.toString().startsWith(part.id)
                        // In a real app, you'd match lessons more precisely
                      );
                      const completedCount = moduleLessons.filter(
                        (p) => p.status === 'completed'
                      ).length;
                      const moduleProgress =
                        moduleLessons.length > 0
                          ? Math.round((completedCount / moduleLessons.length) * 100)
                          : 0;

                      return (
                        <div key={module.id} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <p className="text-text-primary/70 text-sm">{module.title_fr}</p>
                            <span className="text-accent font-semibold text-sm">
                              {moduleProgress}%
                            </span>
                          </div>
                          <AcademyProgress value={moduleProgress} showPercentage={false} />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}
