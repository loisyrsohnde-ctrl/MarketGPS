export type LessonStatus = 'completed' | 'in_progress' | 'available' | 'locked';
export type ExerciseType = 'qcm' | 'reflexion' | 'pratique';
export type QuestionType = 'single' | 'multiple';

export interface QCMQuestion {
  id: string;
  type: QuestionType;
  question_text: string;
  options: string[];
  correct_answer: string | string[];
  explanation?: string;
}

export interface OpenQuestion {
  id: string;
  question_text: string;
  hints?: string[];
}

export interface AcademyExercise {
  id: string;
  title_fr: string;
  exercise_type: ExerciseType;
  questions?: QCMQuestion[] | OpenQuestion[];
  instructions?: string;
  expected_output?: string;
}

export interface AcademyLessonContent {
  id: string;
  lesson_id: string;
  content_type: 'video' | 'text' | 'code';
  content_url?: string;
  content_html?: string;
  order: number;
}

export interface AcademyLesson {
  id: string;
  module_id: string;
  title_fr: string;
  description_fr?: string;
  video_url?: string;
  vtt_url?: string;
  content_html?: string;
  duration_minutes?: number;
  order: number;
  contents?: AcademyLessonContent[];
  exercises?: AcademyExercise[];
}

export interface AcademyModule {
  id: string;
  part_id: string;
  title_fr: string;
  description_fr?: string;
  order: number;
  lessons?: AcademyLesson[];
}

export interface AcademyPart {
  id: string;
  title_fr: string;
  description_fr?: string;
  order: number;
  modules?: AcademyModule[];
}

export interface AcademyUserProgress {
  id: string;
  user_id: string;
  lesson_id: string;
  status: LessonStatus;
  score?: number;
  started_at: string;
  completed_at?: string;
  updated_at: string;
}

export interface AcademyProgressStats {
  total_lessons: number;
  completed_lessons: number;
  average_score: number;
  estimated_time_remaining: number;
  overall_percentage: number;
}
