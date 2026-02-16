import { supabase } from '@/lib/supabase';
import {
  AcademyPart,
  AcademyModule,
  AcademyLesson,
  AcademyExercise,
  AcademyUserProgress,
} from '@/lib/academy-types';

// ═══════════════════════════════════════════════════════════════════════════
// ADMIN STATISTICS
// ═══════════════════════════════════════════════════════════════════════════

export interface AdminStats {
  total_parts: number;
  total_modules: number;
  total_lessons: number;
  total_students: number;
  overall_completion_rate: number;
  latest_activities: ActivityLog[];
}

export interface ActivityLog {
  id: string;
  user_id: string;
  action: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

/**
 * Fetch comprehensive admin statistics
 */
export async function fetchAdminStats(): Promise<AdminStats> {
  try {
    // Get counts
    const { count: partsCount } = await supabase
      .from('academy_parts')
      .select('id', { count: 'exact', head: true });

    const { count: modulesCount } = await supabase
      .from('academy_modules')
      .select('id', { count: 'exact', head: true });

    const { count: lessonsCount } = await supabase
      .from('academy_lessons')
      .select('id', { count: 'exact', head: true });

    // Get unique students from progress table
    const { data: progressData } = await supabase
      .from('academy_user_progress')
      .select('user_id');

    const uniqueStudents = new Set(progressData?.map((p: any) => p.user_id) || []).size;

    // Calculate completion rate
    const { data: completionData } = await supabase
      .from('academy_user_progress')
      .select('status');

    const completedCount = (completionData || []).filter((p: any) => p.status === 'completed').length;
    const totalProgressRecords = completionData?.length || 0;
    const completionRate = totalProgressRecords > 0
      ? Math.round((completedCount / totalProgressRecords) * 100)
      : 0;

    // Fetch recent activity logs
    const { data: activityLogs } = await supabase
      .from('academy_activity_logs')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(10);

    return {
      total_parts: partsCount || 0,
      total_modules: modulesCount || 0,
      total_lessons: lessonsCount || 0,
      total_students: uniqueStudents,
      overall_completion_rate: completionRate,
      latest_activities: (activityLogs || []) as ActivityLog[],
    };
  } catch (err) {
    console.error('Failed to fetch admin stats:', err);
    return {
      total_parts: 0,
      total_modules: 0,
      total_lessons: 0,
      total_students: 0,
      overall_completion_rate: 0,
      latest_activities: [],
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// PARTS MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fetch all parts with their modules and lessons
 */
export async function fetchAllParts(): Promise<AcademyPart[]> {
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
 * Create a new part
 */
export async function createPart(
  title_fr: string,
  description_fr?: string,
  order_index?: number
): Promise<AcademyPart | null> {
  try {
    // Get the next order index if not provided
    let nextOrder = order_index;
    if (!nextOrder) {
      const { data, error: countError } = await supabase
        .from('academy_parts')
        .select('order_index')
        .order('order_index', { ascending: false })
        .limit(1);

      nextOrder = (data?.[0]?.order_index || 0) + 1;
    }

    const { data, error } = await supabase
      .from('academy_parts')
      .insert([
        {
          title_fr,
          description_fr,
          order_index: nextOrder,
        },
      ])
      .select()
      .single();

    if (error) {
      console.error('Error creating part:', error);
      return null;
    }

    return {
      id: data.id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      order: data.order_index,
      modules: [],
    } as AcademyPart;
  } catch (err) {
    console.error('Failed to create part:', err);
    return null;
  }
}

/**
 * Update a part
 */
export async function updatePart(
  partId: string,
  title_fr?: string,
  description_fr?: string,
  order_index?: number
): Promise<AcademyPart | null> {
  try {
    const updateData: any = {};
    if (title_fr !== undefined) updateData.title_fr = title_fr;
    if (description_fr !== undefined) updateData.description_fr = description_fr;
    if (order_index !== undefined) updateData.order_index = order_index;

    const { data, error } = await supabase
      .from('academy_parts')
      .update(updateData)
      .eq('id', partId)
      .select()
      .single();

    if (error) {
      console.error('Error updating part:', error);
      return null;
    }

    return {
      id: data.id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      order: data.order_index,
    } as AcademyPart;
  } catch (err) {
    console.error('Failed to update part:', err);
    return null;
  }
}

/**
 * Delete a part
 */
export async function deletePart(partId: string): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('academy_parts')
      .delete()
      .eq('id', partId);

    if (error) {
      console.error('Error deleting part:', error);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Failed to delete part:', err);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MODULES MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create a new module
 */
export async function createModule(
  partId: string,
  title_fr: string,
  description_fr?: string,
  order_index?: number
): Promise<AcademyModule | null> {
  try {
    let nextOrder = order_index;
    if (!nextOrder) {
      const { data } = await supabase
        .from('academy_modules')
        .select('order_index')
        .eq('part_id', partId)
        .order('order_index', { ascending: false })
        .limit(1);

      nextOrder = (data?.[0]?.order_index || 0) + 1;
    }

    const { data, error } = await supabase
      .from('academy_modules')
      .insert([
        {
          part_id: partId,
          title_fr,
          description_fr,
          order_index: nextOrder,
        },
      ])
      .select()
      .single();

    if (error) {
      console.error('Error creating module:', error);
      return null;
    }

    return {
      id: data.id,
      part_id: data.part_id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      order: data.order_index,
      lessons: [],
    } as AcademyModule;
  } catch (err) {
    console.error('Failed to create module:', err);
    return null;
  }
}

/**
 * Update a module
 */
export async function updateModule(
  moduleId: string,
  title_fr?: string,
  description_fr?: string,
  order_index?: number
): Promise<AcademyModule | null> {
  try {
    const updateData: any = {};
    if (title_fr !== undefined) updateData.title_fr = title_fr;
    if (description_fr !== undefined) updateData.description_fr = description_fr;
    if (order_index !== undefined) updateData.order_index = order_index;

    const { data, error } = await supabase
      .from('academy_modules')
      .update(updateData)
      .eq('id', moduleId)
      .select()
      .single();

    if (error) {
      console.error('Error updating module:', error);
      return null;
    }

    return {
      id: data.id,
      part_id: data.part_id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      order: data.order_index,
    } as AcademyModule;
  } catch (err) {
    console.error('Failed to update module:', err);
    return null;
  }
}

/**
 * Delete a module
 */
export async function deleteModule(moduleId: string): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('academy_modules')
      .delete()
      .eq('id', moduleId);

    if (error) {
      console.error('Error deleting module:', error);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Failed to delete module:', err);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// LESSONS MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create a new lesson
 */
export async function createLesson(
  moduleId: string,
  title_fr: string,
  description_fr?: string,
  estimated_duration_minutes?: number,
  order_index?: number
): Promise<AcademyLesson | null> {
  try {
    let nextOrder = order_index;
    if (!nextOrder) {
      const { data } = await supabase
        .from('academy_lessons')
        .select('order_index')
        .eq('module_id', moduleId)
        .order('order_index', { ascending: false })
        .limit(1);

      nextOrder = (data?.[0]?.order_index || 0) + 1;
    }

    const { data, error } = await supabase
      .from('academy_lessons')
      .insert([
        {
          module_id: moduleId,
          title_fr,
          description_fr,
          estimated_duration_minutes: estimated_duration_minutes || 30,
          order_index: nextOrder,
        },
      ])
      .select()
      .single();

    if (error) {
      console.error('Error creating lesson:', error);
      return null;
    }

    return {
      id: data.id,
      module_id: data.module_id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      duration_minutes: data.estimated_duration_minutes,
      order: data.order_index,
    } as AcademyLesson;
  } catch (err) {
    console.error('Failed to create lesson:', err);
    return null;
  }
}

/**
 * Update a lesson
 */
export async function updateLesson(
  lessonId: string,
  title_fr?: string,
  description_fr?: string,
  estimated_duration_minutes?: number,
  order_index?: number
): Promise<AcademyLesson | null> {
  try {
    const updateData: any = {};
    if (title_fr !== undefined) updateData.title_fr = title_fr;
    if (description_fr !== undefined) updateData.description_fr = description_fr;
    if (estimated_duration_minutes !== undefined) updateData.estimated_duration_minutes = estimated_duration_minutes;
    if (order_index !== undefined) updateData.order_index = order_index;

    const { data, error } = await supabase
      .from('academy_lessons')
      .update(updateData)
      .eq('id', lessonId)
      .select()
      .single();

    if (error) {
      console.error('Error updating lesson:', error);
      return null;
    }

    return {
      id: data.id,
      module_id: data.module_id,
      title_fr: data.title_fr,
      description_fr: data.description_fr,
      duration_minutes: data.estimated_duration_minutes,
      order: data.order_index,
    } as AcademyLesson;
  } catch (err) {
    console.error('Failed to update lesson:', err);
    return null;
  }
}

/**
 * Delete a lesson
 */
export async function deleteLesson(lessonId: string): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('academy_lessons')
      .delete()
      .eq('id', lessonId);

    if (error) {
      console.error('Error deleting lesson:', error);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Failed to delete lesson:', err);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// STUDENTS MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

export interface StudentProgress {
  user_id: string;
  email?: string;
  total_lessons: number;
  completed_lessons: number;
  completion_percentage: number;
  average_score: number;
  started_at: string;
  last_activity: string;
}

/**
 * Fetch all students with their progress
 */
export async function fetchAllStudents(): Promise<StudentProgress[]> {
  try {
    // Get all unique users from progress table
    const { data: progressData } = await supabase
      .from('academy_user_progress')
      .select('user_id, status, score, completed_at, updated_at')
      .order('updated_at', { ascending: false });

    // Get total lessons count
    const { count: totalLessons } = await supabase
      .from('academy_lessons')
      .select('id', { count: 'exact', head: true });

    // Group by user_id and calculate stats
    const userMap = new Map<string, StudentProgress>();

    (progressData || []).forEach((record: any) => {
      if (!userMap.has(record.user_id)) {
        userMap.set(record.user_id, {
          user_id: record.user_id,
          total_lessons: totalLessons || 0,
          completed_lessons: 0,
          completion_percentage: 0,
          average_score: 0,
          started_at: record.completed_at || new Date().toISOString(),
          last_activity: record.updated_at,
        });
      }

      const student = userMap.get(record.user_id)!;
      if (record.status === 'completed') {
        student.completed_lessons += 1;
      }
      student.last_activity = new Date(record.updated_at) > new Date(student.last_activity)
        ? record.updated_at
        : student.last_activity;
    });

    // Calculate completion percentage and average score
    userMap.forEach((student) => {
      if (student.total_lessons > 0) {
        student.completion_percentage = Math.round(
          (student.completed_lessons / student.total_lessons) * 100
        );
      }
    });

    return Array.from(userMap.values()).sort(
      (a, b) => new Date(b.last_activity).getTime() - new Date(a.last_activity).getTime()
    );
  } catch (err) {
    console.error('Failed to fetch students:', err);
    return [];
  }
}

/**
 * Fetch a single student's detailed progress
 */
export async function fetchStudentDetail(userId: string): Promise<StudentProgress | null> {
  try {
    const { data: progressData } = await supabase
      .from('academy_user_progress')
      .select('status, score, updated_at, completed_at')
      .eq('user_id', userId);

    const { count: totalLessons } = await supabase
      .from('academy_lessons')
      .select('id', { count: 'exact', head: true });

    if (!progressData || progressData.length === 0) {
      return null;
    }

    const completedCount = (progressData || []).filter((p: any) => p.status === 'completed').length;
    const scores = (progressData || [])
      .filter((p: any) => p.score !== null)
      .map((p: any) => p.score as number);
    const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

    return {
      user_id: userId,
      total_lessons: totalLessons || 0,
      completed_lessons: completedCount,
      completion_percentage: totalLessons ? Math.round((completedCount / totalLessons) * 100) : 0,
      average_score: avgScore,
      started_at: (progressData[progressData.length - 1] as any).completed_at || new Date().toISOString(),
      last_activity: (progressData[0] as any).updated_at,
    };
  } catch (err) {
    console.error('Failed to fetch student detail:', err);
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXERCISES MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create a new exercise
 */
export async function createExercise(
  lessonId: string,
  title_fr: string,
  exercise_type: 'qcm' | 'reflexion' | 'pratique',
  questions?: any[],
  description_fr?: string
): Promise<AcademyExercise | null> {
  try {
    const { data, error } = await supabase
      .from('academy_exercises')
      .insert([
        {
          lesson_id: lessonId,
          title_fr,
          exercise_type,
          questions: questions || [],
          description_fr,
        },
      ])
      .select()
      .single();

    if (error) {
      console.error('Error creating exercise:', error);
      return null;
    }

    return {
      id: data.id,
      title_fr: data.title_fr,
      exercise_type: data.exercise_type,
      questions: data.questions,
      instructions: data.description_fr,
    } as AcademyExercise;
  } catch (err) {
    console.error('Failed to create exercise:', err);
    return null;
  }
}

/**
 * Update an exercise
 */
export async function updateExercise(
  exerciseId: string,
  title_fr?: string,
  exercise_type?: string,
  questions?: any[],
  description_fr?: string
): Promise<AcademyExercise | null> {
  try {
    const updateData: any = {};
    if (title_fr !== undefined) updateData.title_fr = title_fr;
    if (exercise_type !== undefined) updateData.exercise_type = exercise_type;
    if (questions !== undefined) updateData.questions = questions;
    if (description_fr !== undefined) updateData.description_fr = description_fr;

    const { data, error } = await supabase
      .from('academy_exercises')
      .update(updateData)
      .eq('id', exerciseId)
      .select()
      .single();

    if (error) {
      console.error('Error updating exercise:', error);
      return null;
    }

    return {
      id: data.id,
      title_fr: data.title_fr,
      exercise_type: data.exercise_type,
      questions: data.questions,
      instructions: data.description_fr,
    } as AcademyExercise;
  } catch (err) {
    console.error('Failed to update exercise:', err);
    return null;
  }
}

/**
 * Delete an exercise
 */
export async function deleteExercise(exerciseId: string): Promise<boolean> {
  try {
    const { error } = await supabase
      .from('academy_exercises')
      .delete()
      .eq('id', exerciseId);

    if (error) {
      console.error('Error deleting exercise:', error);
      return false;
    }

    return true;
  } catch (err) {
    console.error('Failed to delete exercise:', err);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// SEED DATA MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════

export interface SeedResult {
  parts_created: number;
  modules_created: number;
  lessons_created: number;
  exercises_created: number;
  success: boolean;
  message: string;
}

/**
 * Seed the academy database with sample data
 */
export async function seedAcademyData(): Promise<SeedResult> {
  try {
    // This would typically read from a folder structure or import file
    // For now, we'll seed with sample data
    const sampleParts = 10;
    const sampleModulesPerPart = 3;
    const sampleLessonsPerModule = 4;

    let partsCreated = 0;
    let modulesCreated = 0;
    let lessonsCreated = 0;

    // Create parts
    for (let i = 1; i <= sampleParts; i++) {
      const part = await createPart(
        `Partie ${i}: Fondamentaux du Trading`,
        `Découvrez les bases du trading avec la Partie ${i}`,
        i
      );

      if (part) {
        partsCreated++;

        // Create modules for each part
        for (let j = 1; j <= sampleModulesPerPart; j++) {
          const mod = await createModule(
            part.id,
            `Module ${j}: Concepts Clés`,
            `Explorez les concepts clés dans le module ${j}`,
            j
          );

          if (mod) {
            modulesCreated++;

            // Create lessons for each module
            for (let k = 1; k <= sampleLessonsPerModule; k++) {
              const lesson = await createLesson(
                mod.id,
                `Leçon ${k}: Introduction`,
                `Leçon introductive ${k} de ce module`,
                30,
                k
              );

              if (lesson) {
                lessonsCreated++;
              }
            }
          }
        }
      }
    }

    return {
      parts_created: partsCreated,
      modules_created: modulesCreated,
      lessons_created: lessonsCreated,
      exercises_created: 0,
      success: true,
      message: `Données seeding complètes: ${partsCreated} parties, ${modulesCreated} modules, ${lessonsCreated} leçons`,
    };
  } catch (err) {
    console.error('Failed to seed academy data:', err);
    return {
      parts_created: 0,
      modules_created: 0,
      lessons_created: 0,
      exercises_created: 0,
      success: false,
      message: `Erreur lors du seeding: ${err instanceof Error ? err.message : 'Erreur inconnue'}`,
    };
  }
}
