'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AcademyVideoPlayer } from '@/components/academy/AcademyVideoPlayer';
import { AcademyExercise } from '@/components/academy/AcademyExercise';
import { AcademyCourseNav } from '@/components/academy/AcademyCourseNav';
import { AcademyProgress } from '@/components/academy/AcademyProgress';
import { AcademyLockOverlay } from '@/components/academy/AcademyLockOverlay';
import {
  fetchLesson,
  fetchParts,
  fetchUserProgress,
  updateProgress,
  isLessonUnlocked,
} from '@/lib/academy-api';
import { AcademyLesson, AcademyUserProgress, AcademyPart } from '@/lib/academy-types';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.lessonId as string;

  const [lesson, setLesson] = useState<AcademyLesson | null>(null);
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [userProgress, setUserProgress] = useState<AcademyUserProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUnlocked, setIsUnlocked] = useState(true);
  const [isCompleted, setIsCompleted] = useState(false);
  const [nextLessonId, setNextLessonId] = useState<string | null>(null);
  const [previousLessonId, setPreviousLessonId] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Load lesson data
        const lessonData = await fetchLesson(lessonId);
        setLesson(lessonData);

        // Load parts for navigation
        const partsData = await fetchParts();
        setParts(partsData);

        // TODO: Get actual user ID from auth context
        const userId = 'user_id';
        const progressData = await fetchUserProgress(userId);
        setUserProgress(progressData);

        // Check if unlocked
        const unlocked = await isLessonUnlocked(lessonId, userId);
        setIsUnlocked(unlocked);

        // Check if completed
        const completed = progressData.some(
          (p) => p.lesson_id === lessonId && p.status === 'completed'
        );
        setIsCompleted(completed);

        // Find next and previous lessons
        findAdjacentLessons(partsData, lessonId);
      } catch (error) {
        console.error('Failed to load lesson:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [lessonId]);

  const findAdjacentLessons = (parts: AcademyPart[], currentLessonId: string) => {
    let foundCurrent = false;
    let prevLesson: string | null = null;
    let nextLesson: string | null = null;

    for (const part of parts) {
      for (const module of part.modules || []) {
        for (const lesson of module.lessons || []) {
          if (foundCurrent) {
            nextLesson = lesson.id;
            break;
          }
          if (lesson.id === currentLessonId) {
            foundCurrent = true;
            prevLesson = prevLesson;
          } else if (!foundCurrent) {
            prevLesson = lesson.id;
          }
        }
        if (nextLesson) break;
      }
      if (nextLesson) break;
    }

    setNextLessonId(nextLesson);
    setPreviousLessonId(prevLesson);
  };

  const handleLessonComplete = async (score?: number) => {
    try {
      // TODO: Get actual user ID from auth context
      await updateProgress('user_id', lessonId, 'completed', score);
      setIsCompleted(true);
    } catch (error) {
      console.error('Failed to mark lesson as complete:', error);
    }
  };

  const handleExerciseComplete = (score: number) => {
    handleLessonComplete(score);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Chargement de la leçon...</p>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Leçon non trouvée</p>
      </div>
    );
  }

  const lessonProgress = userProgress.find((p) => p.lesson_id === lessonId);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <div
        className={cn(
          'hidden md:flex md:w-64 flex-col overflow-y-auto',
          'bg-bg-primary border-r border-glass-border'
        )}
      >
        <div className="p-4 border-b border-glass-border">
          <h2 className="text-sm font-semibold text-text-primary">Navigation</h2>
        </div>
        <AcademyCourseNav
          parts={parts}
          currentLessonId={lessonId}
          userProgress={userProgress}
          onLessonSelect={(id) => router.push(`/academy/cours/${id}`)}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6 md:p-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            {/* Header */}
            <div>
              <button
                onClick={() => router.back()}
                className={cn(
                  'flex items-center gap-2 text-accent hover:text-accent/80 transition-colors mb-4'
                )}
              >
                <ChevronLeft className="w-4 h-4" />
                Retour
              </button>

              <h1 className="text-4xl font-bold text-text-primary mb-2">{lesson.title_fr}</h1>
              {lesson.description_fr && (
                <p className="text-text-primary/70 text-lg">{lesson.description_fr}</p>
              )}
            </div>

            {/* Lock Overlay */}
            {!isUnlocked && (
              <div className="relative p-8 rounded-lg bg-surface border border-glass-border">
                <AcademyLockOverlay
                  isLocked={true}
                  message="Vous devez d'abord terminer la leçon précédente"
                />
              </div>
            )}

            {isUnlocked && (
              <>
                {/* Video Player */}
                {lesson.video_url && (
                  <div>
                    <h2 className="text-xl font-semibold text-text-primary mb-4">
                      Contenu de la leçon
                    </h2>
                    <AcademyVideoPlayer
                      src={lesson.video_url}
                      onComplete={handleLessonComplete}
                    />
                  </div>
                )}

                {/* Lesson Content */}
                {lesson.content_html && (
                  <div
                    className={cn(
                      'lesson-content prose prose-invert max-w-none',
                      'space-y-4 text-text-primary'
                    )}
                  >
                    <div
                      dangerouslySetInnerHTML={{
                        __html: lesson.content_html,
                      }}
                    />
                  </div>
                )}

                {/* Exercises */}
                {lesson.exercises && lesson.exercises.length > 0 && (
                  <div>
                    <h2 className="text-2xl font-bold text-text-primary mb-6">Exercices</h2>
                    <div className="space-y-6">
                      {lesson.exercises.map((exercise) => (
                        <AcademyExercise
                          key={exercise.id}
                          exercise={exercise}
                          onComplete={handleExerciseComplete}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Completion Button */}
                {!isCompleted && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleLessonComplete()}
                    className={cn(
                      'w-full py-4 px-6 rounded-lg font-semibold transition-all',
                      'bg-accent hover:bg-accent/90 text-black',
                      'flex items-center justify-center gap-2'
                    )}
                  >
                    <Check className="w-5 h-5" />
                    Marquer comme terminé
                  </motion.button>
                )}

                {isCompleted && (
                  <div
                    className={cn(
                      'p-4 rounded-lg text-center',
                      'bg-accent/20 border border-accent/50 text-accent'
                    )}
                  >
                    <p className="font-semibold">Leçon terminée !</p>
                  </div>
                )}

                {/* Navigation Buttons */}
                <div className="flex items-center justify-between gap-4 pt-8 border-t border-glass-border">
                  {previousLessonId ? (
                    <button
                      onClick={() => router.push(`/academy/cours/${previousLessonId}`)}
                      className={cn(
                        'flex items-center gap-2 px-6 py-3 rounded-lg',
                        'bg-surface hover:bg-glass-border text-text-primary transition-all'
                      )}
                    >
                      <ChevronLeft className="w-5 h-5" />
                      Précédent
                    </button>
                  ) : (
                    <div />
                  )}

                  {nextLessonId && (
                    <button
                      onClick={() => router.push(`/academy/cours/${nextLessonId}`)}
                      className={cn(
                        'flex items-center gap-2 px-6 py-3 rounded-lg',
                        'bg-accent hover:bg-accent/90 text-black font-semibold transition-all'
                      )}
                    >
                      Suivant
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </>
            )}
          </motion.div>
        </div>
      </div>
    </div>
  );
}
