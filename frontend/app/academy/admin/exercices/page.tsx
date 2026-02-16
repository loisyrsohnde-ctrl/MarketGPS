'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Edit2,
  Trash2,
  Eye,
  Loader,
  AlertCircle,
  CheckCircle,
  Search,
  Zap,
  HelpCircle,
  Code,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchAllParts, createExercise, deleteExercise, AcademyPart } from '@/lib/academy-admin-api';

type ExerciseType = 'qcm' | 'reflexion' | 'pratique';

export default function ExerciseManagement() {
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [selectedExerciseType, setSelectedExerciseType] = useState<ExerciseType>('qcm');

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    type: 'qcm' as ExerciseType,
    questions: [] as any[],
  });

  useEffect(() => {
    loadParts();
  }, []);

  const loadParts = async () => {
    try {
      setIsLoading(true);
      const data = await fetchAllParts();
      setParts(data);
    } catch (err) {
      showMessage('error', 'Erreur lors du chargement des données');
      console.error('Failed to load parts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const handleAddExercise = async () => {
    if (!formData.title.trim() || !selectedLesson) {
      showMessage('error', 'Veuillez remplir tous les champs');
      return;
    }

    try {
      setIsSubmitting(true);
      const newExercise = await createExercise(
        selectedLesson.id,
        formData.title,
        formData.type,
        formData.questions,
        formData.description
      );

      if (newExercise) {
        setFormData({ title: '', description: '', type: 'qcm', questions: [] });
        setSelectedLesson(null);
        setShowAddModal(false);
        showMessage('success', 'Exercice créé avec succès');
        // Reload parts to see the new exercise
        loadParts();
      } else {
        showMessage('error', 'Erreur lors de la création');
      }
    } catch (err) {
      showMessage('error', 'Erreur lors de la création');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteExercise = async (exerciseId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet exercice?')) return;

    try {
      const success = await deleteExercise(exerciseId);
      if (success) {
        showMessage('success', 'Exercice supprimé');
        loadParts();
      } else {
        showMessage('error', 'Erreur lors de la suppression');
      }
    } catch (err) {
      showMessage('error', 'Erreur lors de la suppression');
    }
  };

  const getAllExercises = () => {
    const exercises: any[] = [];
    parts.forEach((part) => {
      part.modules?.forEach((module) => {
        module.lessons?.forEach((lesson) => {
          if (lesson.exercises) {
            lesson.exercises.forEach((ex) => {
              exercises.push({
                ...ex,
                lesson_title: lesson.title_fr,
                module_title: module.title_fr,
                part_title: part.title_fr,
              });
            });
          }
        });
      });
    });
    return exercises.filter(
      (ex) =>
        ex.lesson_title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ex.title_fr?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  const allExercises = getAllExercises();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-text-primary">Gestion des Exercices</h1>
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin text-accent" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Gestion des Exercices</h1>
          <p className="mt-2 text-text-muted">
            Créez et gérez des QCM, exercices de réflexion et exercices pratiques
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 font-medium text-bg-primary hover:bg-accent-light transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nouvel Exercice
        </motion.button>
      </div>

      {/* Message */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={cn(
              'rounded-lg border p-4 flex items-center gap-3',
              message.type === 'success'
                ? 'border-status-success/30 bg-status-success/10'
                : 'border-status-error/30 bg-status-error/10'
            )}
          >
            {message.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-status-success flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-status-error flex-shrink-0" />
            )}
            <p className={cn('text-sm', message.type === 'success' ? 'text-status-success' : 'text-status-error')}>
              {message.text}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ExerciseStatsCard
          label="QCM"
          count={allExercises.filter((e) => e.exercise_type === 'qcm').length}
          icon={HelpCircle}
          color="bg-blue-500"
        />
        <ExerciseStatsCard
          label="Réflexion"
          count={allExercises.filter((e) => e.exercise_type === 'reflexion').length}
          icon={Zap}
          color="bg-purple-500"
        />
        <ExerciseStatsCard
          label="Pratique"
          count={allExercises.filter((e) => e.exercise_type === 'pratique').length}
          icon={Code}
          color="bg-orange-500"
        />
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Rechercher des exercices..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 pl-10 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
        />
      </div>

      {/* Exercises List */}
      {allExercises.length === 0 ? (
        <div className="rounded-lg border border-glass-border bg-surface p-8 text-center">
          <p className="text-text-muted">
            {searchQuery ? 'Aucun exercice ne correspond à votre recherche.' : 'Aucun exercice créé. Créez-en un pour commencer.'}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {allExercises.map((exercise, index) => (
            <motion.div
              key={exercise.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="rounded-lg border border-glass-border bg-surface overflow-hidden hover:border-glass-border-hover transition-colors group"
            >
              <div className="p-5">
                {/* Type Badge */}
                <div className="flex items-start justify-between mb-3">
                  <span
                    className={cn(
                      'inline-block px-3 py-1 rounded-full text-xs font-semibold',
                      exercise.exercise_type === 'qcm'
                        ? 'bg-blue-500/20 text-blue-300'
                        : exercise.exercise_type === 'reflexion'
                          ? 'bg-purple-500/20 text-purple-300'
                          : 'bg-orange-500/20 text-orange-300'
                    )}
                  >
                    {exercise.exercise_type === 'qcm'
                      ? 'QCM'
                      : exercise.exercise_type === 'reflexion'
                        ? 'Réflexion'
                        : 'Pratique'}
                  </span>
                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-2 text-text-muted hover:text-accent transition-colors hover:bg-surface-hover rounded-lg"
                    >
                      <Eye className="h-4 w-4" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      className="p-2 text-text-muted hover:text-accent transition-colors hover:bg-surface-hover rounded-lg"
                    >
                      <Edit2 className="h-4 w-4" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleDeleteExercise(exercise.id)}
                      className="p-2 text-text-muted hover:text-status-error transition-colors hover:bg-surface-hover rounded-lg"
                    >
                      <Trash2 className="h-4 w-4" />
                    </motion.button>
                  </div>
                </div>

                {/* Title */}
                <h3 className="font-semibold text-text-primary mb-2 truncate">{exercise.title_fr}</h3>

                {/* Description */}
                {exercise.instructions && (
                  <p className="text-sm text-text-muted mb-3 line-clamp-2">{exercise.instructions}</p>
                )}

                {/* Metadata */}
                <div className="space-y-1 text-xs text-text-dim">
                  <p>
                    <span className="text-text-muted">Partie:</span> {exercise.part_title}
                  </p>
                  <p>
                    <span className="text-text-muted">Module:</span> {exercise.module_title}
                  </p>
                  <p>
                    <span className="text-text-muted">Leçon:</span> {exercise.lesson_title}
                  </p>
                  {exercise.questions && exercise.questions.length > 0 && (
                    <p>
                      <span className="text-text-muted">Questions:</span> {exercise.questions.length}
                    </p>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Add Exercise Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="rounded-lg bg-bg-primary border border-glass-border p-6 max-w-lg w-full mx-4 max-h-96 overflow-y-auto"
            >
              <h2 className="text-xl font-bold text-text-primary mb-4">Créer un Nouvel Exercice</h2>

              <div className="space-y-4 mb-6">
                {/* Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Type d'Exercice</label>
                  <div className="grid grid-cols-3 gap-2">
                    {(['qcm', 'reflexion', 'pratique'] as ExerciseType[]).map((type) => (
                      <button
                        key={type}
                        onClick={() => setFormData({ ...formData, type })}
                        className={cn(
                          'px-3 py-2 rounded-lg border font-medium text-sm transition-colors',
                          formData.type === type
                            ? 'border-accent bg-accent-dim text-accent'
                            : 'border-glass-border text-text-secondary hover:text-text-primary'
                        )}
                      >
                        {type === 'qcm' ? 'QCM' : type === 'reflexion' ? 'Réflexion' : 'Pratique'}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Lesson Selection */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Sélectionner une Leçon</label>
                  <select
                    value={selectedLesson?.id || ''}
                    onChange={(e) => {
                      const lessonId = e.target.value;
                      let lesson = null;
                      parts.forEach((part) => {
                        part.modules?.forEach((module) => {
                          const foundLesson = module.lessons?.find((l) => l.id === lessonId);
                          if (foundLesson) lesson = foundLesson;
                        });
                      });
                      setSelectedLesson(lesson);
                    }}
                    className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary focus:border-accent focus:outline-none"
                  >
                    <option value="">Choisir une leçon...</option>
                    {parts.flatMap((part) =>
                      (part.modules || []).flatMap((mod) =>
                        (mod.lessons || []).map((lesson) => (
                          <option key={lesson.id} value={lesson.id}>
                            {part.title_fr} {'>'} {mod.title_fr} {'>'} {lesson.title_fr}
                          </option>
                        ))
                      )
                    )}
                  </select>
                </div>

                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Titre</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Titre de l'exercice"
                    className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
                  />
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Description optionnelle"
                    rows={3}
                    className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setFormData({ title: '', description: '', type: 'qcm', questions: [] });
                    setSelectedLesson(null);
                  }}
                  className="flex-1 rounded-lg border border-glass-border px-4 py-2 font-medium text-text-primary hover:bg-surface transition-colors"
                >
                  Annuler
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAddExercise}
                  disabled={isSubmitting || !selectedLesson}
                  className="flex-1 rounded-lg bg-accent px-4 py-2 font-medium text-bg-primary hover:bg-accent-light transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Création...' : 'Créer'}
                </motion.button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Exercise Stats Card
// ═══════════════════════════════════════════════════════════════════════════

interface ExerciseStatsCardProps {
  label: string;
  count: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}

function ExerciseStatsCard({ label, count, icon: Icon, color }: ExerciseStatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-lg border border-glass-border bg-surface p-4"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-text-muted mb-1">{label}</p>
          <p className="text-3xl font-bold text-text-primary">{count}</p>
        </div>
        <div className={cn(color, 'h-10 w-10 rounded-lg flex items-center justify-center')}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
    </motion.div>
  );
}
