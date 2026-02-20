'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowRight, Lock, Crown, UserPlus } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { AcademyProgress } from '@/components/academy/AcademyProgress';
import { AcademyLockOverlay } from '@/components/academy/AcademyLockOverlay';
import { useAccessLevel } from '@/hooks/useAccessLevel';
import { fetchParts, fetchUserProgress } from '@/lib/academy-api';
import { AcademyPart, AcademyUserProgress } from '@/lib/academy-types';

const PART_TITLES_FR = [
  'Fondamentaux du Trading Quantitatif',
  'IA et NLP pour la Finance',
  'Programmation Python',
  'Algèbre Linéaire',
  'Outils de Data Science',
  'Statistiques et Probabilités',
  'Machine Learning',
  'Réseaux de Neurones',
  'Vision par Ordinateur',
  'Traitement du Langage Naturel',
];

export default function AcademyPage() {
  const router = useRouter();
  const { isGuest, isFree, isSubscriber, isAuthenticated } = useAccessLevel();
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [userProgress, setUserProgress] = useState<AcademyUserProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [overallProgress, setOverallProgress] = useState(0);

  useEffect(() => {
    const loadData = async () => {
      try {
        const partsData = await fetchParts();
        setParts(partsData);

        // TODO: Get actual user ID from auth context
        const progressData = await fetchUserProgress('user_id');
        setUserProgress(progressData);

        // Calculate overall progress
        if (progressData.length > 0) {
          const completedCount = progressData.filter((p) => p.status === 'completed').length;
          setOverallProgress(Math.round((completedCount / progressData.length) * 100));
        }
      } catch (error) {
        console.error('Failed to load academy data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const getPartProgress = (partIndex: number) => {
    const partLessons = userProgress.filter((p) => {
      // Filter lessons belonging to this part
      const partNum = partIndex + 1;
      return p.lesson_id.toString().startsWith(String(partNum));
    });

    if (partLessons.length === 0) return 0;
    const completed = partLessons.filter((p) => p.status === 'completed').length;
    return Math.round((completed / partLessons.length) * 100);
  };

  const getPartLessonCount = (part: AcademyPart) => {
    return (
      part.modules?.reduce((sum, module) => sum + (module.lessons?.length || 0), 0) || 0
    );
  };

  const handlePartClick = (partIndex: number) => {
    if (isGuest) {
      router.push('/signup');
      return;
    }
    if (!isSubscriber) {
      // Free users can access first 2 lessons preview, redirect to pricing for full access
      router.push(`/academy/cours?part=${partIndex + 1}`);
      return;
    }
    router.push(`/academy/cours?part=${partIndex + 1}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="space-y-4 text-center">
          <div className="w-12 h-12 rounded-full bg-accent/20 animate-pulse mx-auto" />
          <p className="text-text-primary/60">Chargement de l'Académie...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-12">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-12 md:py-20">
        <div className="max-w-6xl mx-auto px-4 md:px-6 space-y-6">
          <div className="space-y-4">
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className={cn(
                'text-4xl md:text-6xl font-bold tracking-tight',
                'bg-gradient-to-r from-accent via-accent/80 to-accent/60 bg-clip-text text-transparent'
              )}
            >
              QuantAI Academy
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-xl text-text-primary/80"
            >
              Maîtrisez le Trading Algorithmique avec l'Intelligence Artificielle
            </motion.p>
          </div>

          {/* Overall Progress */}
          {overallProgress > 0 && isAuthenticated && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={cn('max-w-md p-6 rounded-lg', 'bg-surface border border-glass-border')}
            >
              <AcademyProgress
                value={overallProgress}
                label="Progression globale"
                showPercentage={true}
              />
            </motion.div>
          )}

          {/* CTA for guests/free users */}
          {!isSubscriber && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
              className="max-w-lg p-6 rounded-lg bg-accent/5 border border-accent/30"
            >
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
                  {isGuest ? <UserPlus className="w-5 h-5 text-accent" /> : <Crown className="w-5 h-5 text-accent" />}
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-text-primary mb-1">
                    {isGuest 
                      ? 'Accédez à la formation en trading algorithmique'
                      : 'Débloquez la formation complète'
                    }
                  </h3>
                  <p className="text-sm text-text-secondary mb-3">
                    {isGuest
                      ? 'Créez un compte gratuit pour prévisualiser les premières leçons, ou souscrivez pour un accès complet.'
                      : 'Passez à Pro pour accéder à tous les modules, exercices et certifications.'
                    }
                  </p>
                  <div className="flex gap-2">
                    {isGuest ? (
                      <>
                        <Link href="/signup">
                          <Button size="sm">Créer un compte</Button>
                        </Link>
                        <Link href="/pricing">
                          <Button variant="secondary" size="sm">Voir les offres</Button>
                        </Link>
                      </>
                    ) : (
                      <Link href="/pricing">
                        <Button size="sm">
                          <Crown className="w-4 h-4 mr-2" />
                          Passer à Pro — 9,99€/mois
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Parts Grid */}
      <section className="max-w-6xl mx-auto px-4 md:px-6">
        <h2 className="text-2xl font-bold text-text-primary mb-8">Tous les Modules</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {PART_TITLES_FR.map((title, index) => {
            const part = parts[index];
            const progress = getPartProgress(index);
            const lessonCount = part ? getPartLessonCount(part) : 0;
            const isLocked = isGuest 
              ? true 
              : !isSubscriber 
                ? index > 1  // Free users can preview first 2 modules
                : index > 0 && getPartProgress(index - 1) < 100;

            return (
              <motion.button
                key={`part-${index + 1}`}
                onClick={() => handlePartClick(index)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.05 * index }}
                className={cn(
                  'relative p-6 rounded-lg text-left transition-all group',
                  'bg-surface border border-glass-border hover:border-accent/50',
                  isLocked && 'opacity-60 cursor-not-allowed'
                )}
                disabled={isLocked}
              >
                {isLocked && <AcademyLockOverlay isLocked={true} />}

                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="inline-block px-3 py-1 rounded-full bg-accent/20 text-accent text-xs font-semibold">
                          Module {index + 1}
                        </span>
                        {isGuest && (
                          <span className="inline-block px-2 py-0.5 rounded-full bg-surface text-text-muted text-xs">
                            <Lock className="w-3 h-3 inline mr-1" />
                            Inscription requise
                          </span>
                        )}
                        {!isGuest && !isSubscriber && index > 1 && (
                          <span className="inline-block px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-xs">
                            <Crown className="w-3 h-3 inline mr-1" />
                            Pro
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-text-primary group-hover:text-accent transition-colors">
                        {title}
                      </h3>
                    </div>
                    <ArrowRight className="w-5 h-5 text-accent/60 group-hover:text-accent transition-colors flex-shrink-0 mt-1" />
                  </div>

                  <AcademyProgress value={progress} showPercentage={true} />

                  <p className="text-sm text-text-primary/60">{lessonCount} leçons</p>
                </div>
              </motion.button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
