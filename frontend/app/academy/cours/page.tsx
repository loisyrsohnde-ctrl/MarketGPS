'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ChevronDown,
  CheckCircle2,
  CircleDot,
  Lock,
  Circle,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchParts, fetchUserProgress } from '@/lib/academy-api';
import { AcademyPart, AcademyUserProgress } from '@/lib/academy-types';

export default function CoursPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const partParam = searchParams.get('part');

  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [userProgress, setUserProgress] = useState<AcademyUserProgress[]>([]);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const partsData = await fetchParts();
        setParts(partsData);

        // TODO: Get actual user ID from auth context
        const progressData = await fetchUserProgress('user_id');
        setUserProgress(progressData);

        // Expand first module by default
        if (partsData.length > 0 && partsData[0].modules?.length) {
          setExpandedModules(new Set([partsData[0].modules[0].id]));
        }
      } catch (error) {
        console.error('Failed to load courses:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const toggleModule = (moduleId: string) => {
    const newExpanded = new Set(expandedModules);
    if (newExpanded.has(moduleId)) {
      newExpanded.delete(moduleId);
    } else {
      newExpanded.add(moduleId);
    }
    setExpandedModules(newExpanded);
  };

  const getProgressStatus = (lessonId: string) => {
    const progress = userProgress.find((p) => p.lesson_id === lessonId);
    if (!progress) return 'available';
    return progress.status as 'completed' | 'in_progress' | 'available';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-accent" />;
      case 'in_progress':
        return <CircleDot className="w-5 h-5 text-accent" />;
      default:
        return <Circle className="w-5 h-5 text-text-primary/40" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Chargement des cours...</p>
      </div>
    );
  }

  const displayParts = partParam ? parts.slice(parseInt(partParam) - 1, parseInt(partParam)) : parts;

  return (
    <div className="min-h-screen pb-12">
      <div className="max-w-6xl mx-auto px-4 md:px-6 py-8">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold text-text-primary mb-8"
        >
          Parcourir les Cours
        </motion.h1>

        <div className="space-y-8">
          {displayParts.map((part, partIndex) => (
            <motion.div
              key={part.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * partIndex }}
              className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}
            >
              <h2 className="text-2xl font-bold text-accent mb-6">{part.title_fr}</h2>

              <div className="space-y-3">
                {part.modules?.map((module) => {
                  const isExpanded = expandedModules.has(module.id);

                  return (
                    <div key={module.id} className="space-y-2">
                      {/* Module Header */}
                      <button
                        onClick={() => toggleModule(module.id)}
                        className={cn(
                          'w-full flex items-center gap-3 p-4 rounded-lg transition-all',
                          'bg-glass-border/50 hover:bg-glass-border'
                        )}
                      >
                        <ChevronDown
                          className={cn(
                            'w-5 h-5 flex-shrink-0 text-accent transition-transform',
                            isExpanded ? 'rotate-0' : '-rotate-90'
                          )}
                        />
                        <span className="flex-1 text-left font-semibold text-text-primary">
                          {module.title_fr}
                        </span>
                      </button>

                      {/* Lessons */}
                      {isExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="overflow-hidden pl-4 space-y-2"
                        >
                          {module.lessons?.map((lesson) => {
                            const status = getProgressStatus(lesson.id);

                            return (
                              <button
                                key={lesson.id}
                                onClick={() => router.push(`/academy/cours/${lesson.id}`)}
                                className={cn(
                                  'w-full flex items-center gap-3 p-3 rounded-lg transition-all',
                                  'hover:bg-surface text-left'
                                )}
                              >
                                {getStatusIcon(status)}
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-text-primary truncate">
                                    {lesson.title_fr}
                                  </p>
                                </div>
                                {lesson.duration_minutes && (
                                  <div className="flex items-center gap-1 text-text-primary/60 text-sm flex-shrink-0">
                                    <Clock className="w-4 h-4" />
                                    {lesson.duration_minutes}m
                                  </div>
                                )}
                              </button>
                            );
                          })}
                        </motion.div>
                      )}
                    </div>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
