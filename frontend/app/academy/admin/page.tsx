'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  Users,
  BookOpen,
  Target,
  TrendingUp,
  Clock,
  Loader,
  AlertCircle,
  CheckCircle,
  Zap,
  Upload,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { fetchAdminStats, AdminStats } from '@/lib/academy-admin-api';

export default function AdminDashboard() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchAdminStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur de chargement');
        console.error('Failed to load stats:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-4xl font-bold text-text-primary">Tableau de Bord Administrateur</h1>
          <p className="mt-2 text-text-muted">Gérez l'académie QuantAI et suivez les progrès des étudiants</p>
        </div>

        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader className="h-8 w-8 animate-spin text-accent mx-auto mb-3" />
            <p className="text-text-secondary">Chargement des statistiques...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-text-primary">Tableau de Bord Administrateur</h1>
        <p className="mt-2 text-text-muted">
          Gérez l'académie QuantAI et suivez les progrès des étudiants
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-status-error/30 bg-status-error/10 p-4 flex items-center gap-3"
        >
          <AlertCircle className="h-5 w-5 text-status-error flex-shrink-0" />
          <p className="text-sm text-status-error">{error}</p>
        </motion.div>
      )}

      {/* Stats Grid */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5"
        >
          {/* Parties */}
          <StatCard
            title="Parties"
            value={stats.total_parts}
            icon={BookOpen}
            color="accent"
            delay={0}
          />

          {/* Modules */}
          <StatCard
            title="Modules"
            value={stats.total_modules}
            icon={BarChart3}
            color="accent"
            delay={0.1}
          />

          {/* Leçons */}
          <StatCard
            title="Leçons"
            value={stats.total_lessons}
            icon={Target}
            color="accent"
            delay={0.2}
          />

          {/* Étudiants */}
          <StatCard
            title="Étudiants"
            value={stats.total_students}
            icon={Users}
            color="accent"
            delay={0.3}
          />

          {/* Taux de Complétion */}
          <StatCard
            title="Complétion"
            value={`${stats.overall_completion_rate}%`}
            icon={TrendingUp}
            color="accent"
            delay={0.4}
          />
        </motion.div>
      )}

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.5 }}
      >
        <h2 className="text-lg font-semibold text-text-primary mb-4">Actions rapides</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <QuickActionCard
            title="Gérer le Contenu"
            description="Créez, modifiez ou supprimez les parties, modules et leçons"
            icon={BookOpen}
            href="/academy/admin/contenu"
          />
          <QuickActionCard
            title="Gérer les Étudiants"
            description="Consultez la progression des étudiants et exportez les données"
            icon={Users}
            href="/academy/admin/etudiants"
          />
          <QuickActionCard
            title="Créer des Exercices"
            description="Ajoutez des QCM, réflexions et exercices pratiques"
            icon={Zap}
            href="/academy/admin/exercices"
          />
          <QuickActionCard
            title="Importer des Données"
            description="Seedez la base de données avec du contenu d'exemple"
            icon={Upload}
            href="/academy/admin/seed"
          />
        </div>
      </motion.div>

      {/* Recent Activity */}
      {stats && stats.latest_activities.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.6 }}
        >
          <h2 className="text-lg font-semibold text-text-primary mb-4">Activité récente</h2>
          <div className="rounded-lg border border-glass-border bg-surface p-4 space-y-3">
            {stats.latest_activities.slice(0, 5).map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
                className="flex items-center justify-between py-2 border-b border-glass-border/50 last:border-b-0"
              >
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-accent"></div>
                  <div>
                    <p className="text-sm text-text-secondary font-medium">{activity.action}</p>
                    <p className="text-xs text-text-muted">
                      {new Date(activity.timestamp).toLocaleDateString('fr-FR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                </div>
                <CheckCircle className="h-4 w-4 text-accent/50" />
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Stats Summary */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.7 }}
          className="rounded-lg border border-glass-border bg-surface p-6"
        >
          <h2 className="text-lg font-semibold text-text-primary mb-4">Résumé de la Plateforme</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-text-muted mb-1">Contenu Total</p>
              <p className="text-2xl font-bold text-accent">
                {stats.total_parts + stats.total_modules + stats.total_lessons}
              </p>
              <p className="text-xs text-text-dim mt-1">
                {stats.total_parts} parties, {stats.total_modules} modules, {stats.total_lessons} leçons
              </p>
            </div>
            <div>
              <p className="text-sm text-text-muted mb-1">Engagement Étudiant</p>
              <p className="text-2xl font-bold text-accent">{stats.total_students}</p>
              <p className="text-xs text-text-dim mt-1">étudiants inscrits et actifs</p>
            </div>
            <div>
              <p className="text-sm text-text-muted mb-1">Performance Globale</p>
              <p className="text-2xl font-bold text-accent">{stats.overall_completion_rate}%</p>
              <p className="text-xs text-text-dim mt-1">taux de complétion moyen</p>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Stat Card Component
// ═══════════════════════════════════════════════════════════════════════════

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'accent' | 'status';
  delay: number;
}

function StatCard({ title, value, icon: Icon, color, delay }: StatCardProps) {
  const colors = {
    accent: 'from-accent/20 to-accent/10',
    status: 'from-status-success/20 to-status-success/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.3 }}
      className={cn(
        'rounded-lg border border-glass-border bg-gradient-to-br p-4',
        colors[color]
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-text-muted mb-2">{title}</p>
          <p className="text-3xl font-bold text-text-primary">{value}</p>
        </div>
        <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
          <Icon className="h-5 w-5 text-accent" />
        </div>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Quick Action Card Component
// ═══════════════════════════════════════════════════════════════════════════

import { useRouter } from 'next/navigation';

interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
}

function QuickActionCard({ title, description, icon: Icon, href }: QuickActionCardProps) {
  const router = useRouter();

  return (
    <motion.button
      onClick={() => router.push(href)}
      whileHover={{ y: -4 }}
      className="text-left rounded-lg border border-glass-border bg-surface hover:bg-surface-hover hover:border-glass-border-hover transition-all duration-200 p-5 group"
    >
      <div className="flex items-start gap-4">
        <div className="h-12 w-12 rounded-lg bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors flex-shrink-0">
          <Icon className="h-6 w-6 text-accent group-hover:text-accent-light transition-colors" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-text-primary group-hover:text-accent transition-colors">
            {title}
          </h3>
          <p className="text-sm text-text-muted mt-1">{description}</p>
        </div>
      </div>
    </motion.button>
  );
}
