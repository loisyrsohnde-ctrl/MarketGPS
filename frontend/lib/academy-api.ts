import { supabase } from '@/lib/supabase';
import {
  AcademyPart,
  AcademyModule,
  AcademyLesson,
  AcademyUserProgress,
  AcademyExercise,
  AcademyProgressStats,
} from '@/lib/academy-types';

/**
 * Fetch all academy parts with their modules and lessons
 */
export async function fetchParts(): Promise<AcademyPart[]> {
  try {
    const { data, error } = await supabase
      .from('academy_parts')
      .select(
        `
        id,
        title_fr,
        description_fr,
        order_index,
        academy_modules (
          id,
          title_fr,
          order_index,
          academy_lessons (
            id,
            title_fr,
            description_fr,
            order_index
          )
        )
      `
      )
      .order('order_index', { ascending: true });

    if (error) {
      console.error('Error fetching parts:', error);
      return [];
    }

    // Map order_index to order for frontend compatibility
    const mapped = (data || []).map((part: any) => ({
      ...part,
      order: part.order_index,
      modules: (part.academy_modules || [])
        .sort((a: any, b: any) => a.order_index - b.order_index)
        .map((mod: any) => ({
          ...mod,
          order: mod.order_index,
          lessons: (mod.academy_lessons || [])
            .sort((a: any, b: any) => a.order_index - b.order_index)
            .map((lesson: any) => ({
              ...lesson,
              order: lesson.order_index,
            })),
        })),
    }));

    return mapped as AcademyPart[];
  } catch (err) {
    console.error('Failed to fetch parts:', err);
    return [];
  }
}

/**
 * Fetch a single lesson with its contents and exercises
 */
export async function fetchLesson(lessonId: string): Promise<AcademyLesson | null> {
  try {
    const { data: lessonData, error: lessonError } = await supabase
      .from('academy_lessons')
      .select(
        `
        id,
        title_fr,
        description_fr,
        order_index,
        module_id,
        academy_lesson_contents (
          id,
          title_fr,
          content_html,
          content_type,
          video_url,
          vtt_url,
          order_index
        )
      `
      )
      .eq('id', lessonId)
      .single();

    if (lessonError) {
      console.error('Error fetching lesson:', lessonError);
      return null;
    }

    // Fetch exercises for this lesson (questions stored as JSONB in exercises table)
    const { data: exercisesData } = await supabase
      .from('academy_exercises')
      .select(`*`)
      .eq('lesson_id', lessonId)
      .order('order_index', { ascending: true });

    // Map exercises - questions are in the JSONB column
    const exercises: AcademyExercise[] = (exercisesData || []).map((exercise: any) => ({
      id: exercise.id.toString(),
      title_fr: exercise.title_fr,
      exercise_type: exercise.exercise_type,
      questions: exercise.questions || [],
      instructions: exercise.description_fr,
    }));

    // Extract first video URL from contents
    const contents = (lessonData as any).academy_lesson_contents || [];
    const sortedContents = contents.sort((a: any, b: any) => a.order_index - b.order_index);
    const videoContent = sortedContents.find((c: any) => c.content_type === 'video');
    const textContents = sortedContents.filter((c: any) => c.content_type === 'text');
    const combinedHtml = textContents.map((c: any) => c.content_html || '').join('\n');

    return {
      id: (lessonData as any).id.toString(),
      module_id: (lessonData as any).module_id.toString(),
      title_fr: (lessonData as any).title_fr,
      description_fr: (lessonData as any).description_fr,
      video_url: videoContent?.video_url || undefined,
      vtt_url: videoContent?.vtt_url || undefined,
      content_html: combinedHtml || undefined,
      duration_minutes: undefined,
      order: (lessonData as any).order_index,
      contents: sortedContents.map((c: any) => ({
        id: c.id.toString(),
        lesson_id: lessonId,
        content_type: c.content_type,
        content_url: c.video_url,
        content_html: c.content_html,
        order: c.order_index,
      })),
      exercises,
    } as AcademyLesson;
  } catch (err) {
    console.error('Failed to fetch lesson:', err);
    return null;
  }
}

/**
 * Fetch all user progress records
 */
export async function fetchUserProgress(userId: string): Promise<AcademyUserProgress[]> {
  try {
    const { data, error } = await supabase
      .from('academy_user_progress')
      .select(`*`)
      .eq('user_id', userId)
      .order('updated_at', { ascending: false });

    if (error) {
      console.error('Error fetching user progress:', error);
      return [];
    }

    return (data || []) as AcademyUserProgress[];
  } catch (err) {
    console.error('Failed to fetch user progress:', err);
    return [];
  }
}

/**
 * Update lesson progress for a user
 */
export async function updateProgress(
  userId: string,
  lessonId: string,
  status: 'completed' | 'in_progress' | 'available',
  score?: number
): Promise<AcademyUserProgress | null> {
  try {
    const { data: existingData } = await supabase
      .from('academy_user_progress')
      .select('id')
      .eq('user_id', userId)
      .eq('lesson_id', lessonId)
      .single();

    const now = new Date().toISOString();
    const updateData: any = {
      user_id: userId,
      lesson_id: lessonId,
      status,
      updated_at: now,
    };

    if (score !== undefined) {
      updateData.score = score;
    }

    if (status === 'completed') {
      updateData.completed_at = now;
    }

    let result;

    if (existingData) {
      // Update existing progress
      const { data, error } = await supabase
        .from('academy_user_progress')
        .update(updateData)
        .eq('user_id', userId)
        .eq('lesson_id', lessonId)
        .select()
        .single();

      if (error) {
        console.error('Error updating progress:', error);
        return null;
      }
      result = data;
    } else {
      // Insert new progress record
      updateData.started_at = now;

      const { data, error } = await supabase
        .from('academy_user_progress')
        .insert([updateData])
        .select()
        .single();

      if (error) {
        console.error('Error inserting progress:', error);
        return null;
      }
      result = data;
    }

    return result as AcademyUserProgress;
  } catch (err) {
    console.error('Failed to update progress:', err);
    return null;
  }
}

/**
 * Save exercise answer and score
 */
export async function saveExerciseAnswer(
  userId: string,
  exerciseId: string,
  answers: Record<string, string | string[]>,
  score: number
): Promise<boolean> {
  try {
    const { error } = await supabase.from('academy_exercise_answers').insert([
      {
        user_id: userId,
        exercise_id: exerciseId,
        answers,
        score,
        submitted_at: new Date().toISOString(),
      },
    ]);

    if (error) {
      console.error('Error saving exercise answer:', error);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Failed to save exercise answer:', err);
    return false;
  }
}

/**
 * Check if a lesson is unlocked for a user
 * A lesson is unlocked if the previous lesson is completed or if it's the first lesson
 */
export async function isLessonUnlocked(lessonId: string, userId: string): Promise<boolean> {
  try {
    // Get the lesson's module
    const { data: lessonData } = await supabase
      .from('academy_lessons')
      .select('module_id, order_index')
      .eq('id', lessonId)
      .single();

    if (!lessonData) {
      return false;
    }

    // If it's the first lesson in the module, it's unlocked
    if (lessonData.order_index === 1) {
      return true;
    }

    // Get the previous lesson
    const { data: prevLessonData } = await supabase
      .from('academy_lessons')
      .select('id')
      .eq('module_id', lessonData.module_id)
      .eq('order_index', lessonData.order_index - 1)
      .single();

    if (!prevLessonData) {
      return true; // No previous lesson found
    }

    // Check if previous lesson is completed
    const { data: progressData } = await supabase
      .from('academy_user_progress')
      .select('status')
      .eq('user_id', userId)
      .eq('lesson_id', prevLessonData.id)
      .single();

    return progressData?.status === 'completed';
  } catch (err) {
    console.error('Failed to check lesson unlock status:', err);
    return false;
  }
}

/**
 * Fetch aggregated progress statistics for a user
 */
export async function fetchProgressStats(userId: string): Promise<AcademyProgressStats> {
  try {
    // Get all lessons count
    const { count: totalLessons } = await supabase
      .from('academy_lessons')
      .select('id', { count: 'exact', head: true });

    // Get user progress
    const { data: progressData } = await supabase
      .from('academy_user_progress')
      .select('status, score')
      .eq('user_id', userId);

    const completedLessons = (progressData || []).filter(
      (p) => p.status === 'completed'
    ).length;
    const avgScore =
      (progressData || [])
        .filter((p) => p.score !== null)
        .reduce((sum, p) => sum + (p.score || 0), 0) / Math.max(1, completedLessons);

    const completedPercent =
      totalLessons && totalLessons > 0 ? Math.round((completedLessons / totalLessons) * 100) : 0;

    // Estimate time remaining (assuming ~30 minutes per lesson average)
    const estimatedMinutesRemaining = ((totalLessons || 0) - completedLessons) * 30;

    return {
      total_lessons: totalLessons || 0,
      completed_lessons: completedLessons,
      average_score: isNaN(avgScore) ? 0 : avgScore,
      estimated_time_remaining: estimatedMinutesRemaining,
      overall_percentage: completedPercent,
    };
  } catch (err) {
    console.error('Failed to fetch progress stats:', err);
    return {
      total_lessons: 0,
      completed_lessons: 0,
      average_score: 0,
      estimated_time_remaining: 0,
      overall_percentage: 0,
    };
  }
}
