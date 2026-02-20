'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  Plus,
  Edit2,
  Trash2,
  Loader,
  AlertCircle,
  CheckCircle,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  fetchAllParts,
  createPart,
  updatePart,
  deletePart,
  createModule,
  updateModule,
  deleteModule,
  createLesson,
  updateLesson,
  deleteLesson,
  AcademyPart,
} from '@/lib/academy-admin-api';

export default function ContentManagement() {
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedParts, setExpandedParts] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modal states
  const [showAddPartModal, setShowAddPartModal] = useState(false);
  const [newPartTitle, setNewPartTitle] = useState('');
  const [newPartDescription, setNewPartDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const togglePartExpanded = (partId: string) => {
    const newSet = new Set(expandedParts);
    if (newSet.has(partId)) {
      newSet.delete(partId);
    } else {
      newSet.add(partId);
    }
    setExpandedParts(newSet);
  };

  const toggleModuleExpanded = (moduleId: string) => {
    const newSet = new Set(expandedModules);
    if (newSet.has(moduleId)) {
      newSet.delete(moduleId);
    } else {
      newSet.add(moduleId);
    }
    setExpandedModules(newSet);
  };

  const handleAddPart = async () => {
    if (!newPartTitle.trim()) {
      showMessage('error', 'Veuillez entrer un titre');
      return;
    }

    try {
      setIsSubmitting(true);
      const newPart = await createPart(newPartTitle, newPartDescription || undefined);
      if (newPart) {
        setParts([...parts, newPart]);
        setNewPartTitle('');
        setNewPartDescription('');
        setShowAddPartModal(false);
        showMessage('success', 'Partie créée avec succès');
      } else {
        showMessage('error', 'Erreur lors de la création');
      }
    } catch (err) {
      showMessage('error', 'Erreur lors de la création');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeletePart = async (partId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette partie?')) return;

    try {
      const success = await deletePart(partId);
      if (success) {
        setParts(parts.filter((p) => p.id !== partId));
        showMessage('success', 'Partie supprimée');
      } else {
        showMessage('error', 'Erreur lors de la suppression');
      }
    } catch (err) {
      showMessage('error', 'Erreur lors de la suppression');
    }
  };

  const filteredParts = parts.filter(
    (part) =>
      part.title_fr.toLowerCase().includes(searchQuery.toLowerCase()) ||
      part.modules?.some((mod) =>
        mod.title_fr.toLowerCase().includes(searchQuery.toLowerCase())
      ) ||
      part.modules?.some((mod) =>
        mod.lessons?.some((lesson) =>
          lesson.title_fr.toLowerCase().includes(searchQuery.toLowerCase())
        )
      )
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-text-primary">Gestion du Contenu</h1>
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin text-accent" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-text-primary">Gestion du Contenu</h1>
          <p className="mt-2 text-text-muted">Gérez les parties, modules et leçons de l'académie</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowAddPartModal(true)}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 font-medium text-bg-primary hover:bg-accent-light transition-colors"
        >
          <Plus className="h-4 w-4" />
          Ajouter une Partie
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

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Rechercher dans le contenu..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 pl-10 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none transition-colors"
        />
      </div>

      {/* Parts List */}
      <div className="space-y-4">
        {filteredParts.length === 0 ? (
          <div className="rounded-lg border border-glass-border bg-surface p-8 text-center">
            <p className="text-text-muted">Aucune partie trouvée. Créez-en une pour commencer.</p>
          </div>
        ) : (
          filteredParts.map((part, partIndex) => (
            <motion.div
              key={part.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: partIndex * 0.05 }}
              className="rounded-lg border border-glass-border bg-surface overflow-hidden"
            >
              {/* Part Header */}
              <button
                onClick={() => togglePartExpanded(part.id)}
                className="w-full flex items-center gap-3 px-6 py-4 hover:bg-surface-hover transition-colors text-left"
              >
                <ChevronDown
                  className={cn(
                    'h-5 w-5 text-accent transition-transform',
                    expandedParts.has(part.id) && 'rotate-180'
                  )}
                />
                <div className="flex-1">
                  <h3 className="font-semibold text-text-primary">{part.title_fr}</h3>
                  {part.description_fr && (
                    <p className="text-sm text-text-muted mt-1">{part.description_fr}</p>
                  )}
                  <p className="text-xs text-text-dim mt-1">
                    {part.modules?.length || 0} modules • {part.modules?.reduce((sum, m) => sum + (m.lessons?.length || 0), 0) || 0} leçons
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle edit
                    }}
                    className="p-2 text-text-muted hover:text-accent transition-colors hover:bg-surface-hover rounded-lg"
                  >
                    <Edit2 className="h-4 w-4" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeletePart(part.id);
                    }}
                    className="p-2 text-text-muted hover:text-status-error transition-colors hover:bg-surface-hover rounded-lg"
                  >
                    <Trash2 className="h-4 w-4" />
                  </motion.button>
                </div>
              </button>

              {/* Part Content */}
              <AnimatePresence>
                {expandedParts.has(part.id) && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="border-t border-glass-border/50"
                  >
                    <div className="px-6 py-4 space-y-4 bg-bg-primary/30">
                      {part.modules && part.modules.length > 0 ? (
                        part.modules.map((module, moduleIndex) => (
                          <ModuleItem
                            key={module.id}
                            module={module}
                            isExpanded={expandedModules.has(module.id)}
                            onToggle={() => toggleModuleExpanded(module.id)}
                            onDelete={() => deleteModule(module.id)}
                            moduleIndex={moduleIndex}
                          />
                        ))
                      ) : (
                        <p className="text-sm text-text-muted text-center py-4">Aucun module dans cette partie</p>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>

      {/* Add Part Modal */}
      <AnimatePresence>
        {showAddPartModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="rounded-lg bg-bg-primary border border-glass-border p-6 max-w-md w-full mx-4"
            >
              <h2 className="text-xl font-bold text-text-primary mb-4">Ajouter une Partie</h2>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Titre</label>
                  <input
                    type="text"
                    value={newPartTitle}
                    onChange={(e) => setNewPartTitle(e.target.value)}
                    placeholder="Titre de la partie"
                    className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-secondary mb-2">Description</label>
                  <textarea
                    value={newPartDescription}
                    onChange={(e) => setNewPartDescription(e.target.value)}
                    placeholder="Description optionnelle"
                    rows={3}
                    className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowAddPartModal(false);
                    setNewPartTitle('');
                    setNewPartDescription('');
                  }}
                  className="flex-1 rounded-lg border border-glass-border px-4 py-2 font-medium text-text-primary hover:bg-surface transition-colors"
                >
                  Annuler
                </button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleAddPart}
                  disabled={isSubmitting}
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
// Module Item Component
// ═══════════════════════════════════════════════════════════════════════════

interface ModuleItemProps {
  module: any;
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  moduleIndex: number;
}

function ModuleItem({ module, isExpanded, onToggle, onDelete, moduleIndex }: ModuleItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: moduleIndex * 0.05 }}
      className="rounded-lg border border-glass-border/50 bg-surface/50"
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors text-left"
      >
        <ChevronDown
          className={cn(
            'h-4 w-4 text-accent transition-transform',
            isExpanded && 'rotate-180'
          )}
        />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-text-primary text-sm truncate">{module.title_fr}</p>
          <p className="text-xs text-text-dim">
            {module.lessons?.length || 0} leçons
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.stopPropagation();
              // Handle edit
            }}
            className="p-1 text-text-muted hover:text-accent transition-colors hover:bg-surface-hover rounded"
          >
            <Edit2 className="h-3 w-3" />
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={(e) => {
              e.stopPropagation();
              if (confirm('Supprimer ce module?')) onDelete();
            }}
            className="p-1 text-text-muted hover:text-status-error transition-colors hover:bg-surface-hover rounded"
          >
            <Trash2 className="h-3 w-3" />
          </motion.button>
        </div>
      </button>

      <AnimatePresence>
        {isExpanded && module.lessons && module.lessons.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-glass-border/30 px-4 py-2 space-y-1 bg-bg-primary/20"
          >
            {module.lessons.map((lesson: any, lessonIndex: number) => (
              <motion.div
                key={lesson.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: lessonIndex * 0.05 }}
                className="flex items-center justify-between rounded px-3 py-2 hover:bg-surface-hover transition-colors group"
              >
                <p className="text-xs text-text-secondary font-medium truncate flex-1">
                  {lesson.title_fr}
                </p>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  <button className="p-1 text-text-muted hover:text-accent transition-colors">
                    <Edit2 className="h-3 w-3" />
                  </button>
                  <button className="p-1 text-text-muted hover:text-status-error transition-colors">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
