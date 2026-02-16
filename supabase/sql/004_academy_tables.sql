-- ═══════════════════════════════════════════════════════════════════════════
-- QUANTAI ACADEMY - Tables & RLS Policies
-- Migration: 004_academy_tables.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY PARTS (10 parties du cours)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_parts (
  id SERIAL PRIMARY KEY,
  part_number INT UNIQUE NOT NULL,
  title_fr TEXT NOT NULL,
  description_fr TEXT,
  icon TEXT DEFAULT 'book',
  order_index INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY MODULES
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_modules (
  id SERIAL PRIMARY KEY,
  part_id INT NOT NULL REFERENCES academy_parts(id) ON DELETE CASCADE,
  module_number INT NOT NULL,
  title_fr TEXT NOT NULL,
  order_index INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(part_id, module_number)
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY LESSONS
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_lessons (
  id SERIAL PRIMARY KEY,
  module_id INT NOT NULL REFERENCES academy_modules(id) ON DELETE CASCADE,
  lesson_number INT NOT NULL,
  title_fr TEXT NOT NULL,
  title_original TEXT,
  description_fr TEXT,
  folder_name TEXT,
  order_index INT NOT NULL,
  is_project BOOLEAN DEFAULT false,
  is_coming_soon BOOLEAN DEFAULT false,
  estimated_duration_minutes INT DEFAULT 15,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(module_id, lesson_number)
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY LESSON CONTENTS (pages/vidéos dans chaque leçon)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_lesson_contents (
  id SERIAL PRIMARY KEY,
  lesson_id INT NOT NULL REFERENCES academy_lessons(id) ON DELETE CASCADE,
  title_fr TEXT NOT NULL,
  content_html TEXT,
  content_type TEXT NOT NULL CHECK (content_type IN ('video', 'text', 'quiz', 'project', 'workspace')),
  video_url TEXT,
  vtt_url TEXT,
  order_index INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY EXERCISES (exercices en français)
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_exercises (
  id SERIAL PRIMARY KEY,
  lesson_id INT NOT NULL REFERENCES academy_lessons(id) ON DELETE CASCADE,
  title_fr TEXT NOT NULL,
  description_fr TEXT,
  exercise_type TEXT NOT NULL CHECK (exercise_type IN ('qcm', 'code', 'reflexion', 'pratique')),
  questions JSONB NOT NULL DEFAULT '[]',
  order_index INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY USER PROGRESS
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_user_progress (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  lesson_id INT NOT NULL REFERENCES academy_lessons(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
  score INT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, lesson_id)
);

-- ─────────────────────────────────────────────────────────────────────────
-- ACADEMY USER EXERCISE ANSWERS
-- ─────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS academy_user_exercise_answers (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  exercise_id INT NOT NULL REFERENCES academy_exercises(id) ON DELETE CASCADE,
  answers JSONB NOT NULL DEFAULT '{}',
  score INT DEFAULT 0,
  completed_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, exercise_id)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_academy_modules_part ON academy_modules(part_id);
CREATE INDEX IF NOT EXISTS idx_academy_lessons_module ON academy_lessons(module_id);
CREATE INDEX IF NOT EXISTS idx_academy_contents_lesson ON academy_lesson_contents(lesson_id);
CREATE INDEX IF NOT EXISTS idx_academy_exercises_lesson ON academy_exercises(lesson_id);
CREATE INDEX IF NOT EXISTS idx_academy_progress_user ON academy_user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_academy_progress_lesson ON academy_user_progress(lesson_id);
CREATE INDEX IF NOT EXISTS idx_academy_answers_user ON academy_user_exercise_answers(user_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═══════════════════════════════════════════════════════════════════════════

-- Course content is readable by all authenticated users
ALTER TABLE academy_parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_lesson_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE academy_user_exercise_answers ENABLE ROW LEVEL SECURITY;

-- Read policies for course content (all authenticated users can read)
CREATE POLICY "Academy parts readable by authenticated" ON academy_parts
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Academy modules readable by authenticated" ON academy_modules
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Academy lessons readable by authenticated" ON academy_lessons
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Academy contents readable by authenticated" ON academy_lesson_contents
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "Academy exercises readable by authenticated" ON academy_exercises
  FOR SELECT TO authenticated USING (true);

-- User progress - users can only see and modify their own progress
CREATE POLICY "Users can view own progress" ON academy_user_progress
  FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own progress" ON academy_user_progress
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own progress" ON academy_user_progress
  FOR UPDATE TO authenticated USING (auth.uid() = user_id);

-- Exercise answers - users can only see and modify their own answers
CREATE POLICY "Users can view own answers" ON academy_user_exercise_answers
  FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own answers" ON academy_user_exercise_answers
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own answers" ON academy_user_exercise_answers
  FOR UPDATE TO authenticated USING (auth.uid() = user_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGER: Update updated_at on progress changes
-- ═══════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_academy_progress_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER academy_progress_updated
  BEFORE UPDATE ON academy_user_progress
  FOR EACH ROW
  EXECUTE FUNCTION update_academy_progress_timestamp();

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED: Course Parts (10 parts)
-- ═══════════════════════════════════════════════════════════════════════════
INSERT INTO academy_parts (part_number, title_fr, description_fr, icon, order_index) VALUES
  (1, 'Fondamentaux du Trading Quantitatif', 'Apprenez les bases du trading, les prix des actions, la mécanique des marchés, le traitement des données et les stratégies de momentum.', 'trending-up', 1),
  (2, 'IA et NLP pour la Finance', 'Découvrez le traitement du langage naturel, le deep learning avec PyTorch, et l''analyse de sentiment appliqués aux marchés financiers.', 'brain', 2),
  (3, 'Programmation Python', 'Maîtrisez Python : types de données, flux de contrôle, fonctions et scripting pour le trading algorithmique.', 'code', 3),
  (4, 'Algèbre Linéaire', 'Vecteurs, combinaisons linéaires, transformations et matrices — les fondements mathématiques de l''IA.', 'calculator', 4),
  (5, 'Outils de Data Science', 'Jupyter Notebooks, NumPy et Pandas — les outils essentiels pour l''analyse de données financières.', 'database', 5),
  (6, 'Statistiques et Probabilités', 'Statistiques descriptives, probabilités, distributions, tests d''hypothèse et intervalles de confiance.', 'bar-chart', 6),
  (7, 'Machine Learning', 'Régression linéaire, Naive Bayes, clustering, arbres de décision et filtres de Kalman.', 'cpu', 7),
  (8, 'Réseaux de Neurones', 'Introduction complète aux réseaux de neurones : perceptrons, gradient descent, backpropagation.', 'network', 8),
  (9, 'Vision par Ordinateur', 'Introduction à la vision par ordinateur et ses applications en finance.', 'eye', 9),
  (10, 'Traitement du Langage Naturel', 'NLP avancé pour l''analyse de textes financiers et l''extraction d''informations.', 'message-square', 10)
ON CONFLICT (part_number) DO NOTHING;
