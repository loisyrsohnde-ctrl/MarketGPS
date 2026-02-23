'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { AcademyVideoPlayer } from '@/components/academy/AcademyVideoPlayer';
import { AcademyExercise } from '@/components/academy/AcademyExercise';
import { AcademyCourseNav } from '@/components/academy/AcademyCourseNav';
import {
  fetchLesson,
  fetchParts,
} from '@/lib/academy-api';
import { AcademyLesson, AcademyPart } from '@/lib/academy-types';

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = params.lessonId as string;

  const [lesson, setLesson] = useState<AcademyLesson | null>(null);
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCompleted, setIsCompleted] = useState(false);
  const [nextLessonId, setNextLessonId] = useState<string | null>(null);
  const [previousLessonId, setPreviousLessonId] = useState<string | null>(null);
  const dataLoaded = useRef(false);

  useEffect(() => {
    if (dataLoaded.current && lesson) return;

    const loadData = async () => {
      try {
        const lessonData = await fetchLesson(lessonId);
        setLesson(lessonData);
        const partsData = await fetchParts();
        setParts(partsData);
        findAdjacentLessons(partsData, lessonId);
        dataLoaded.current = true;
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
      for (const mod of part.modules || []) {
        for (const lesson of mod.lessons || []) {
          if (foundCurrent) {
            nextLesson = lesson.id;
            break;
          }
          if (lesson.id === currentLessonId) {
            foundCurrent = true;
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

  const handleLessonComplete = async () => {
    setIsCompleted(true);
  };

  const handleExerciseComplete = (score: number) => {
    setIsCompleted(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Chargement de la lecon...</p>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text-primary/60">Lecon non trouvee</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
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
          userProgress={[]}
          onLessonSelect={(id) => router.push(`/academy/cours/${id}`)}
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-6 md:p-8">
          <div className="space-y-8">
            <div>
              <button
                onClick={() => router.push('/academy/cours')}
                className={cn(
                  'flex items-center gap-2 text-accent hover:text-accent/80 transition-colors mb-4'
                )}
              >
                <ChevronLeft className="w-4 h-4" />
                Retour aux cours
              </button>

              <h1 className="text-4xl font-bold text-text-primary mb-2">{lesson.title_fr}</h1>
              {lesson.description_fr && (
                <p className="text-text-primary/70 text-lg">{lesson.description_fr}</p>
              )}
            </div>

            {lesson.video_url && (
              <div>
                <h2 className="text-xl font-semibold text-text-primary mb-4">
                  Contenu de la lecon
                </h2>
                <AcademyVideoPlayer
                  src={lesson.video_url}
                  subtitles={lesson.vtt_url ? [{ src: lesson.vtt_url, label: 'Français', lang: 'fr' }] : []}
                  onComplete={handleLessonComplete}
                />
              </div>
            )}

            {lesson.content_html && (
              <div
                className={cn(
                  'lesson-content prose prose-invert max-w-none',
                  'space-y-4 text-text-primary'
                )}
              >
                <div
                  dangerouslySetInnerHTML={{
                    __html: (() => {
                      // Sanitize HTML to prevent XSS attacks
                      if (typeof window !== 'undefined') {
                        const DOMPurify = require('isomorphic-dompurify');
                        return DOMPurify.sanitize(lesson.content_html);
                      }
                      return lesson.content_html;
                    })(),
                  }}
                />
              </div>
            )}

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

            {!isCompleted && (
              <button
                onClick={() => handleLessonComplete()}
                className={cn(
                  'w-full py-4 px-6 rounded-lg font-semibold transition-all',
                  'bg-accent hover:bg-accent/90 text-black',
                  'flex items-center justify-center gap-2'
                )}
              >
                <Check className="w-5 h-5" />
                Marquer comme termine
              </button>
            )}

            {isCompleted && (
              <div
                className={cn(
                  'p-4 rounded-lg text-center',
                  'bg-accent/20 border border-accent/50 text-accent'
                )}
              >
                <p className="font-semibold">Lecon terminee !</p>
              </div>
            )}

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
                  Precedent
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
          </div>
        </div>
      </div>
    </div>
  );
}
