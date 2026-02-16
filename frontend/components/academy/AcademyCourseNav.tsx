'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  CheckCircle2,
  CircleDot,
  Lock,
  Circle,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { AcademyPart, AcademyModule, AcademyLesson, AcademyUserProgress } from '@/lib/academy-types';

interface AcademyCourseNavProps {
  parts: AcademyPart[];
  currentLessonId?: string;
  userProgress?: AcademyUserProgress[];
  onLessonSelect: (lessonId: string) => void;
}

export function AcademyCourseNav({
  parts,
  currentLessonId,
  userProgress = [],
  onLessonSelect,
}: AcademyCourseNavProps) {
  const [expandedParts, setExpandedParts] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());

  const togglePart = (partId: string) => {
    const newExpanded = new Set(expandedParts);
    if (newExpanded.has(partId)) {
      newExpanded.delete(partId);
    } else {
      newExpanded.add(partId);
    }
    setExpandedParts(newExpanded);
  };

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

  const getStatusIcon = (status: string, isLocked: boolean) => {
    if (isLocked) {
      return <Lock className="w-4 h-4 text-text-primary/40" />;
    }
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-accent" />;
      case 'in_progress':
        return <CircleDot className="w-4 h-4 text-accent" />;
      case 'available':
        return <Circle className="w-4 h-4 text-text-primary/40" />;
      default:
        return <Circle className="w-4 h-4 text-text-primary/40" />;
    }
  };

  return (
    <nav className={cn('w-full p-4 space-y-2', 'text-sm')}>
      {parts.map((part) => {
        const isPartExpanded = expandedParts.has(part.id);

        return (
          <div key={part.id} className="space-y-1">
            {/* Part Header */}
            <button
              onClick={() => togglePart(part.id)}
              className={cn(
                'w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-all',
                'hover:bg-surface text-text-primary/80 hover:text-text-primary'
              )}
            >
              <ChevronDown
                className={cn(
                  'w-4 h-4 flex-shrink-0 transition-transform',
                  isPartExpanded ? 'rotate-0' : '-rotate-90'
                )}
              />
              <span className="flex-1 text-left font-semibold">{part.title_fr}</span>
            </button>

            {/* Part Content */}
            <AnimatePresence>
              {isPartExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden pl-4 space-y-1"
                >
                  {part.modules?.map((module) => {
                    const isModuleExpanded = expandedModules.has(module.id);

                    return (
                      <div key={module.id} className="space-y-1">
                        {/* Module Header */}
                        <button
                          onClick={() => toggleModule(module.id)}
                          className={cn(
                            'w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-all',
                            'hover:bg-glass-border text-text-primary/70 hover:text-text-primary/90'
                          )}
                        >
                          <ChevronDown
                            className={cn(
                              'w-4 h-4 flex-shrink-0 transition-transform',
                              isModuleExpanded ? 'rotate-0' : '-rotate-90'
                            )}
                          />
                          <span className="flex-1 text-left text-sm">{module.title_fr}</span>
                        </button>

                        {/* Module Lessons */}
                        <AnimatePresence>
                          {isModuleExpanded && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden pl-4 space-y-1"
                            >
                              {module.lessons?.map((lesson) => {
                                const status = getProgressStatus(lesson.id);
                                const isLocked = false; // TODO: implement unlock logic
                                const isActive = currentLessonId === lesson.id;

                                return (
                                  <button
                                    key={lesson.id}
                                    onClick={() => onLessonSelect(lesson.id)}
                                    className={cn(
                                      'w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-all',
                                      'text-xs text-left',
                                      isActive
                                        ? 'bg-accent/20 border border-accent text-accent'
                                        : 'hover:bg-glass-border/50 text-text-primary/60 hover:text-text-primary/80'
                                    )}
                                  >
                                    {getStatusIcon(status, isLocked)}
                                    <span className="flex-1 truncate">{lesson.title_fr}</span>
                                    {lesson.duration_minutes && (
                                      <span className="text-xs text-text-primary/40 flex-shrink-0">
                                        {lesson.duration_minutes}m
                                      </span>
                                    )}
                                  </button>
                                );
                              })}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </nav>
  );
}
