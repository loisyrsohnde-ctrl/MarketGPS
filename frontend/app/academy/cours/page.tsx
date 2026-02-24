'use client';

import React, { Suspense, useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ChevronDown,
  Circle,
  Clock,
  Lock,
  GraduationCap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchParts } from '@/lib/academy-api';
import type { AcademyPart } from '@/lib/academy-types';
import { useSubscription } from '@/hooks/useSubscription';

/**
 * Check if a lesson is free based on its position in the course structure.
 * Only Part 1, Module 1, Lessons 1-2 are free.
 */
function isLessonFree(partIndex: number, moduleIndex: number, lessonIndex: number): boolean {
  return partIndex === 0 && moduleIndex === 0 && lessonIndex < 2;
}

export default function CoursPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-text-primary/60">Chargement des cours...</p></div>}>
      <CoursPageContent />
    </Suspense>
  );
}

function CoursPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const partParam = searchParams.get('part');
  const { hasAcademy } = useSubscription();

  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const dataLoaded = useRef(false);

  useEffect(() => {
    if (dataLoaded.current) return;

    const loadData = async () => {
      try {
        const partsData = await fetchParts();
        setParts(partsData);

        // Expand first module by default
        if (partsData.length > 0 && partsData[0].modules?.length) {
          setExpandedModules(new Set([partsData[0].modules[0].id]));
        }
        dataLoaded.current = true;
      } catch (error) {
        console.error('Failed to load courses:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const toggleModule = useCallback((moduleId: string) => {
    setExpandedModules((prev) => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(moduleId)) {
        newExpanded.delete(moduleId);
      } else {
        newExpanded.add(moduleId);
      }
      return newExpanded;
    });
  }, []);

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
        <h1 className="text-3xl font-bold text-text-primary mb-8">
          Parcourir les Cours
        </h1>

        <div className="space-y-8">
          {displayParts.map((part, partIndex) => {
            // Adjust partIndex when filtering by part param
            const actualPartIndex = partParam ? parseInt(partParam) - 1 : partIndex;

            return (
              <div
                key={part.id}
                className={cn('p-6 rounded-lg', 'bg-surface border border-glass-border')}
              >
                <h2 className="text-2xl font-bold text-accent mb-6">{part.title_fr}</h2>

                <div className="space-y-3">
                  {part.modules?.map((mod, moduleIndex) => {
                    const isExpanded = expandedModules.has(mod.id);

                    return (
                      <div key={mod.id} className="space-y-2">
                        {/* Module Header */}
                        <button
                          onClick={() => toggleModule(mod.id)}
                          className={cn(
                            'w-full flex items-center gap-3 p-4 rounded-lg transition-all',
                            'bg-glass-border/50 hover:bg-glass-border'
                          )}
                        >
                          <ChevronDown
                            className={cn(
                              'w-5 h-5 flex-shrink-0 text-accent transition-transform duration-200',
                              isExpanded ? 'rotate-0' : '-rotate-90'
                            )}
                          />
                          <span className="flex-1 text-left font-semibold text-text-primary">
                            {mod.title_fr}
                          </span>
                          <span className="text-sm text-text-primary/40">
                            {mod.lessons?.length || 0} lecons
                          </span>
                        </button>

                        {/* Lessons */}
                        {isExpanded && (
                          <div className="pl-4 space-y-2">
                            {mod.lessons?.map((lesson, lessonIndex) => {
                              const isFree = isLessonFree(actualPartIndex, moduleIndex, lessonIndex);
                              const canAccess = hasAcademy || isFree;

                              return (
                                <button
                                  key={lesson.id}
                                  onClick={() => {
                                    if (canAccess) {
                                      router.push(`/academy/cours/${lesson.id}`);
                                    } else {
                                      router.push('/academy');
                                    }
                                  }}
                                  className={cn(
                                    'w-full flex items-center gap-3 p-3 rounded-lg transition-all text-left',
                                    canAccess
                                      ? 'hover:bg-glass-border/50'
                                      : 'opacity-50 cursor-not-allowed'
                                  )}
                                >
                                  {canAccess ? (
                                    <Circle className="w-5 h-5 text-text-primary/40 flex-shrink-0" />
                                  ) : (
                                    <Lock className="w-5 h-5 text-text-primary/30 flex-shrink-0" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <p className={cn(
                                      'font-medium truncate',
                                      canAccess ? 'text-text-primary' : 'text-text-primary/50'
                                    )}>
                                      {lesson.title_fr}
                                    </p>
                                  </div>
                                  {isFree && !hasAcademy && (
                                    <span className="text-xs text-purple-400 font-medium flex-shrink-0">
                                      Gratuit
                                    </span>
                                  )}
                                  {!canAccess && (
                                    <span className="text-xs text-text-muted flex-shrink-0">
                                      Premium
                                    </span>
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
