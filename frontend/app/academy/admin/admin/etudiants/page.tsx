'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  Download,
  Search,
  Filter,
  Eye,
  Loader,
  AlertCircle,
  CheckCircle,
  TrendingUp,
} from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { fetchAllStudents, StudentProgress } from '@/lib/academy-admin-api';

export default function StudentManagement() {
  const [students, setStudents] = useState<StudentProgress[]>([]);
  const [filteredStudents, setFilteredStudents] = useState<StudentProgress[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'in-progress' | 'not-started'>('all');
  const [selectedStudent, setSelectedStudent] = useState<StudentProgress | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadStudents();
  }, []);

  useEffect(() => {
    filterStudents();
  }, [students, searchQuery, filterStatus]);

  const loadStudents = async () => {
    try {
      setIsLoading(true);
      const data = await fetchAllStudents();
      setStudents(data);
    } catch (err) {
      showMessage('error', 'Erreur lors du chargement des étudiants');
      console.error('Failed to load students:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  const filterStudents = () => {
    let filtered = students.filter((student) =>
      student.user_id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (filterStatus === 'completed') {
      filtered = filtered.filter((s) => s.completion_percentage === 100);
    } else if (filterStatus === 'in-progress') {
      filtered = filtered.filter((s) => s.completion_percentage > 0 && s.completion_percentage < 100);
    } else if (filterStatus === 'not-started') {
      filtered = filtered.filter((s) => s.completion_percentage === 0);
    }

    setFilteredStudents(filtered);
  };

  const handleExport = () => {
    try {
      const csv = [
        ['ID Étudiant', 'Total Leçons', 'Leçons Complétées', 'Pourcentage', 'Score Moyen', 'Dernière Activité'],
        ...students.map((s) => [
          s.user_id,
          s.total_lessons,
          s.completed_lessons,
          `${s.completion_percentage}%`,
          s.average_score.toFixed(2),
          new Date(s.last_activity).toLocaleDateString('fr-FR'),
        ]),
      ]
        .map((row) => row.map((cell) => `"${cell}"`).join(','))
        .join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `etudiants-export-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      showMessage('success', 'Données exportées avec succès');
    } catch (err) {
      showMessage('error', 'Erreur lors de l\'export');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-text-primary">Gestion des Étudiants</h1>
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
          <h1 className="text-3xl font-bold text-text-primary">Gestion des Étudiants</h1>
          <p className="mt-2 text-text-muted">
            Suivez la progression de {students.length} étudiant{students.length > 1 ? 's' : ''}
          </p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleExport}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 font-medium text-bg-primary hover:bg-accent-light transition-colors"
        >
          <Download className="h-4 w-4" />
          Exporter en CSV
        </motion.button>
      </div>

      {/* Message */}
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

      {/* Filters */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher par ID étudiant..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-glass-border bg-surface px-4 py-2 pl-10 text-text-primary placeholder-text-muted focus:border-accent focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-text-muted" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="flex-1 rounded-lg border border-glass-border bg-surface px-4 py-2 text-text-primary focus:border-accent focus:outline-none"
          >
            <option value="all">Tous les étudiants</option>
            <option value="completed">Complété (100%)</option>
            <option value="in-progress">En cours</option>
            <option value="not-started">Non commencé</option>
          </select>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsSummaryCard
          label="Taux de Complétion Moyen"
          value={
            students.length > 0
              ? `${Math.round(students.reduce((sum, s) => sum + s.completion_percentage, 0) / students.length)}%`
              : '0%'
          }
          icon={TrendingUp}
          color="accent"
        />
        <StatsSummaryCard
          label="Score Moyen Global"
          value={
            students.length > 0
              ? `${(students.reduce((sum, s) => sum + s.average_score, 0) / students.length).toFixed(1)}/100`
              : '—'
          }
          icon={Users}
          color="accent"
        />
        <StatsSummaryCard
          label="Étudiants Actifs"
          value={students.filter((s) => s.completion_percentage > 0).length.toString()}
          icon={CheckCircle}
          color="accent"
        />
      </div>

      {/* Students Table */}
      <div className="overflow-x-auto rounded-lg border border-glass-border bg-surface">
        <table className="w-full">
          <thead>
            <tr className="border-b border-glass-border bg-surface-hover">
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">ID Étudiant</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">Progrès</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">Leçons</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">Score Moyen</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">Dernière Activité</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-text-secondary">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-glass-border">
            {filteredStudents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center">
                  <p className="text-text-muted">Aucun étudiant trouvé</p>
                </td>
              </tr>
            ) : (
              filteredStudents.map((student, index) => (
                <motion.tr
                  key={student.user_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="hover:bg-surface-hover transition-colors"
                >
                  <td className="px-6 py-4 text-sm text-text-primary font-medium truncate">
                    {student.user_id}
                  </td>
                  <td className="px-6 py-4">
                    <div className="w-24">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="h-2 flex-1 rounded-full bg-surface-dark overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${student.completion_percentage}%` }}
                            transition={{ duration: 0.5, delay: index * 0.05 }}
                            className="h-full bg-gradient-to-r from-accent to-accent-light"
                          />
                        </div>
                        <span className="text-xs font-semibold text-accent w-8 text-right">
                          {student.completion_percentage}%
                        </span>
                      </div>
                      <p className="text-xs text-text-dim">
                        {student.completed_lessons}/{student.total_lessons}
                      </p>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-text-secondary">
                    {student.completed_lessons}/{student.total_lessons}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className="px-3 py-1 rounded-full bg-accent/10 text-accent font-medium text-xs">
                      {student.average_score.toFixed(1)}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-text-muted">
                    {new Date(student.last_activity).toLocaleDateString('fr-FR')}
                  </td>
                  <td className="px-6 py-4">
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setSelectedStudent(student)}
                      className="p-2 text-text-muted hover:text-accent transition-colors hover:bg-surface-hover rounded-lg"
                    >
                      <Eye className="h-4 w-4" />
                    </motion.button>
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Student Detail Modal */}
      {selectedStudent && (
        <StudentDetailModal
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
        />
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Stats Summary Card
// ═══════════════════════════════════════════════════════════════════════════

interface StatsSummaryCardProps {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  color: 'accent';
}

function StatsSummaryCard({ label, value, icon: Icon, color }: StatsSummaryCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-lg border border-glass-border bg-surface p-4"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-text-muted mb-1">{label}</p>
          <p className="text-2xl font-bold text-text-primary">{value}</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center">
          <Icon className="h-5 w-5 text-accent" />
        </div>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Student Detail Modal
// ═══════════════════════════════════════════════════════════════════════════

interface StudentDetailModalProps {
  student: StudentProgress;
  onClose: () => void;
}

function StudentDetailModal({ student, onClose }: StudentDetailModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        onClick={(e) => e.stopPropagation()}
        className="rounded-lg bg-bg-primary border border-glass-border p-8 max-w-md w-full mx-4 max-h-96 overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Détails de l'Étudiant</h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            ×
          </button>
        </div>

        <div className="space-y-6">
          {/* Identity */}
          <div>
            <p className="text-sm text-text-muted mb-2">ID Étudiant</p>
            <p className="text-lg font-semibold text-text-primary font-mono">{student.user_id}</p>
          </div>

          {/* Progress */}
          <div>
            <p className="text-sm text-text-muted mb-3">Progression Générale</p>
            <div className="h-3 rounded-full bg-surface-dark overflow-hidden mb-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${student.completion_percentage}%` }}
                transition={{ duration: 0.5 }}
                className="h-full bg-gradient-to-r from-accent to-accent-light"
              />
            </div>
            <p className="text-lg font-bold text-accent">{student.completion_percentage}%</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <StatItem label="Leçons Complétées" value={`${student.completed_lessons}/${student.total_lessons}`} />
            <StatItem label="Score Moyen" value={`${student.average_score.toFixed(1)}/100`} />
            <StatItem
              label="Débuté le"
              value={new Date(student.started_at).toLocaleDateString('fr-FR')}
            />
            <StatItem
              label="Dernière Activité"
              value={new Date(student.last_activity).toLocaleDateString('fr-FR')}
            />
          </div>

          {/* Close Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onClose}
            className="w-full rounded-lg bg-accent px-4 py-2 font-medium text-bg-primary hover:bg-accent-light transition-colors"
          >
            Fermer
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Stat Item Component
// ═══════════════════════════════════════════════════════════════════════════

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface p-3">
      <p className="text-xs text-text-muted mb-1">{label}</p>
      <p className="font-semibold text-text-primary text-sm">{value}</p>
    </div>
  );
}
