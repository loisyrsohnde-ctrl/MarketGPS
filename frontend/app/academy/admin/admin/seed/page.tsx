'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Upload,
  Loader,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Layers,
  Award,
  Zap,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { seedAcademyData, SeedResult } from '@/lib/academy-admin-api';

export default function SeedDataPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SeedResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSeedData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setResult(null);

      const seedResult = await seedAcademyData();
      setResult(seedResult);

      if (!seedResult.success) {
        setError(seedResult.message);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du seeding');
      console.error('Failed to seed data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-text-primary">Importer des Données</h1>
        <p className="mt-2 text-text-muted">
          Remplissez la base de données avec du contenu d'exemple pour tester la plateforme
        </p>
      </div>

      {/* Info Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-lg border border-status-info/30 bg-status-info/10 p-4 flex gap-3"
      >
        <Info className="h-5 w-5 text-status-info flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-status-info font-medium">À propos du seeding</p>
          <p className="text-sm text-status-info/80 mt-1">
            Le seeding créera un ensemble complet de données d'exemple incluant 10 parties, 3 modules par partie,
            et 4 leçons par module. Parfait pour tester la plateforme.
          </p>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="space-y-6">
        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FeatureCard
            icon={Layers}
            title="10 Parties"
            description="Couvrant tous les domaines du trading"
          />
          <FeatureCard
            icon={BookOpen}
            title="30 Modules"
            description="3 modules par partie pour une progression logique"
          />
          <FeatureCard
            icon={Award}
            title="120 Leçons"
            description="4 leçons par module pour un apprentissage complet"
          />
          <FeatureCard
            icon={Zap}
            title="Contenu Réaliste"
            description="Données structurées pour un vrai environnement de test"
          />
        </div>

        {/* Action Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-glass-border bg-surface p-8"
        >
          <div className="text-center">
            <div className="mb-6 flex justify-center">
              <div className="h-16 w-16 rounded-full bg-accent/20 flex items-center justify-center">
                <Upload className="h-8 w-8 text-accent" />
              </div>
            </div>

            <h2 className="text-2xl font-bold text-text-primary mb-2">Prêt à Commencer?</h2>
            <p className="text-text-muted mb-6">
              Cliquez sur le bouton ci-dessous pour remplir la base de données avec des données d'exemple
            </p>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSeedData}
              disabled={isLoading}
              className={cn(
                'flex items-center justify-center gap-2 rounded-lg px-6 py-3 font-medium transition-colors',
                isLoading
                  ? 'bg-accent/50 text-bg-primary cursor-not-allowed'
                  : 'bg-accent text-bg-primary hover:bg-accent-light'
              )}
            >
              {isLoading ? (
                <>
                  <Loader className="h-5 w-5 animate-spin" />
                  Seeding en cours...
                </>
              ) : (
                <>
                  <Upload className="h-5 w-5" />
                  Démarrer le Seeding
                </>
              )}
            </motion.button>

            <p className="text-xs text-text-dim mt-4">
              Cette action peut prendre quelques secondes à quelques minutes selon la connexion
            </p>
          </div>
        </motion.div>

        {/* Results */}
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              'rounded-lg border p-6',
              result.success
                ? 'border-status-success/30 bg-status-success/10'
                : 'border-status-error/30 bg-status-error/10'
            )}
          >
            <div className="flex items-start gap-4">
              {result.success ? (
                <CheckCircle className="h-6 w-6 text-status-success flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-6 w-6 text-status-error flex-shrink-0 mt-0.5" />
              )}

              <div className="flex-1">
                <h3 className={cn(
                  'text-lg font-semibold mb-2',
                  result.success ? 'text-status-success' : 'text-status-error'
                )}>
                  {result.success ? 'Seeding Réussi!' : 'Erreur lors du Seeding'}
                </h3>

                <p className={cn(
                  'text-sm mb-4',
                  result.success ? 'text-status-success/80' : 'text-status-error/80'
                )}>
                  {result.message}
                </p>

                {result.success && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <ResultStat
                      label="Parties Créées"
                      value={result.parts_created}
                      icon={Layers}
                    />
                    <ResultStat
                      label="Modules Créés"
                      value={result.modules_created}
                      icon={BookOpen}
                    />
                    <ResultStat
                      label="Leçons Créées"
                      value={result.lessons_created}
                      icon={Award}
                    />
                    <ResultStat
                      label="Exercices Créés"
                      value={result.exercises_created}
                      icon={Zap}
                    />
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Error */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-status-error/30 bg-status-error/10 p-6 flex items-start gap-4"
          >
            <AlertCircle className="h-6 w-6 text-status-error flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-status-error mb-1">Erreur</h3>
              <p className="text-sm text-status-error/80">{error}</p>
            </div>
          </motion.div>
        )}

        {/* FAQ */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-lg border border-glass-border bg-surface p-6"
        >
          <h3 className="text-lg font-bold text-text-primary mb-4">Questions Fréquentes</h3>

          <div className="space-y-4">
            <FAQItem
              question="Que se passe-t-il quand j'exécute le seeding?"
              answer="Le seeding crée un ensemble complet de données de test dans votre base de données, y compris des parties, des modules, des leçons et des exercices. Cela vous permet de tester la plateforme avec du contenu réaliste."
            />
            <FAQItem
              question="Puis-je exécuter le seeding plusieurs fois?"
              answer="Oui, vous pouvez exécuter le seeding plusieurs fois. Cependant, cela créera des données dupliquées. Si vous souhaitez recommencer à zéro, vous devrez d'abord nettoyer manuellement les données existantes."
            />
            <FAQItem
              question="Les données seeding sont-elles permanentes?"
              answer="Oui, une fois créées, les données sont permanentes dans votre base de données jusqu'à ce que vous les supprimiez manuellement. Assurez-vous que vous êtes sûr avant d'exécuter le seeding en production."
            />
            <FAQItem
              question="Puis-je personnaliser le contenu du seeding?"
              answer="Le seeding crée du contenu d'exemple standard. Pour créer du contenu personnalisé, utilisez les pages de gestion du contenu (Contenu, Exercices, etc.) dans le panneau d'administration."
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Feature Card Component
// ═══════════════════════════════════════════════════════════════════════════

interface FeatureCardProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}

function FeatureCard({ icon: Icon, title, description }: FeatureCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-glass-border bg-surface p-4"
    >
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
          <Icon className="h-5 w-5 text-accent" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-text-primary">{title}</h4>
          <p className="text-sm text-text-muted mt-1">{description}</p>
        </div>
      </div>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// Result Stat Component
// ═══════════════════════════════════════════════════════════════════════════

interface ResultStatProps {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
}

function ResultStat({ label, value, icon: Icon }: ResultStatProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-lg bg-status-success/10 border border-status-success/20 p-3 text-center"
    >
      <div className="flex justify-center mb-2">
        <Icon className="h-5 w-5 text-status-success" />
      </div>
      <p className="text-2xl font-bold text-status-success">{value}</p>
      <p className="text-xs text-text-muted mt-1">{label}</p>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// FAQ Item Component
// ═══════════════════════════════════════════════════════════════════════════

interface FAQItemProps {
  question: string;
  answer: string;
}

function FAQItem({ question, answer }: FAQItemProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="border-b border-glass-border/50 last:border-b-0 pb-4 last:pb-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full text-left flex items-start justify-between gap-3 py-2 group"
      >
        <p className="font-medium text-text-primary group-hover:text-accent transition-colors">{question}</p>
        <span
          className={cn(
            'text-accent mt-1 transition-transform flex-shrink-0',
            isOpen && 'rotate-180'
          )}
        >
          ▼
        </span>
      </button>
      {isOpen && (
        <motion.p
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="text-sm text-text-muted mt-2 pb-2"
        >
          {answer}
        </motion.p>
      )}
    </div>
  );
}
