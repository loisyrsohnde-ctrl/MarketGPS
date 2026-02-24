'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowRight, Lock, Crown, UserPlus, GraduationCap, CheckCircle2, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { AcademyProgress } from '@/components/academy/AcademyProgress';
import { AcademyLockOverlay } from '@/components/academy/AcademyLockOverlay';
import { useAccessLevel } from '@/hooks/useAccessLevel';
import { useSubscription } from '@/hooks/useSubscription';
import { useAuth } from '@/hooks/useAuth';
import { fetchParts, fetchUserProgress } from '@/lib/academy-api';
import { AcademyPart, AcademyUserProgress } from '@/lib/academy-types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

const PART_TITLES_FR = [
  'Fondamentaux du Trading Quantitatif',
  'IA et NLP pour la Finance',
  'Programmation Python',
  'Alg\u00e8bre Lin\u00e9aire',
  'Outils de Data Science',
  'Statistiques et Probabilit\u00e9s',
  'Machine Learning',
  'R\u00e9seaux de Neurones',
  'Vision par Ordinateur',
  'Traitement du Langage Naturel',
];

export default function AcademyPage() {
  const router = useRouter();
  const { isGuest, isFree, isSubscriber, isAuthenticated } = useAccessLevel();
  const { plan, hasAcademy, isActive: isSubscriptionActive } = useSubscription();
  const { session } = useAuth();
  const [parts, setParts] = useState<AcademyPart[]>([]);
  const [userProgress, setUserProgress] = useState<AcademyUserProgress[]>([]);
  const [loading, setLoading] = useState(true);
  const [overallProgress, setOverallProgress] = useState(0);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // Check for purchase success/cancel in URL params
  const [purchaseMessage, setPurchaseMessage] = useState<string | null>(null);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('purchased') === '1') {
      setPurchaseMessage('Achat r\u00e9ussi ! Bienvenue dans QuantAI Academy.');
      // Clean URL
      window.history.replaceState({}, '', '/academy');
    } else if (params.get('canceled') === '1') {
      setPurchaseMessage(null);
      window.history.replaceState({}, '', '/academy');
    }
  }, []);

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

  const handleAcademyCheckout = useCallback(async (pricingTier: 'standard' | 'diaspora' = 'standard') => {
    if (!session?.access_token) {
      router.push('/login?redirect=/academy');
      return;
    }
    // Subscribers already have access — no checkout needed
    if (isSubscriptionActive) {
      return;
    }
    setCheckoutLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/billing/academy/checkout-session`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pricing_tier: pricingTier }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Erreur lors de la cr\u00e9ation du paiement');
      }

      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error('Academy checkout error:', error);
      alert('Une erreur est survenue. Veuillez r\u00e9essayer.');
    } finally {
      setCheckoutLoading(false);
    }
  }, [session, router, isSubscriptionActive]);

  const getPartProgress = (partIndex: number) => {
    const partLessons = userProgress.filter((p) => {
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
    // Academy purchasers get full access to all modules
    if (hasAcademy) {
      router.push(`/academy/cours?part=${partIndex + 1}`);
      return;
    }
    // Free users can only access Module 1 (Part 1)
    if (partIndex > 0) {
      // Scroll to purchase section
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    router.push(`/academy/cours?part=${partIndex + 1}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="space-y-4 text-center">
          <div className="w-12 h-12 rounded-full bg-accent/20 animate-pulse mx-auto" />
          <p className="text-text-primary/60">Chargement de l&apos;Acad&eacute;mie...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pb-12">
      {/* Purchase success message */}
      {purchaseMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-6 py-3 text-center text-sm font-medium">
          <CheckCircle2 className="w-4 h-4 inline mr-2" />
          {purchaseMessage}
        </div>
      )}

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
                'bg-gradient-to-r from-purple-400 via-purple-500 to-purple-600 bg-clip-text text-transparent'
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
              Ma&icirc;trisez le Trading Algorithmique avec l&apos;Intelligence Artificielle
            </motion.p>
          </div>

          {/* Overall Progress (for Academy owners) */}
          {overallProgress > 0 && isAuthenticated && hasAcademy && (
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

          {/* Case 1: User already has Academy access (granted by admin or purchased) */}
          {hasAcademy && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/30"
            >
              <CheckCircle2 className="w-5 h-5 text-purple-400" />
              <span className="text-sm font-medium text-purple-300">Acc&egrave;s complet &agrave; la formation</span>
            </motion.div>
          )}

          {/* Case 2: Active subscriber WITHOUT academy → discounted price 199€ */}
          {!hasAcademy && isSubscriptionActive && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
              className="max-w-2xl"
            >
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-500/10 via-purple-600/5 to-transparent border border-purple-500/30 p-8">
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                <div className="relative space-y-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <GraduationCap className="w-6 h-6 text-purple-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-text-primary mb-2">
                        Acc&eacute;dez &agrave; la formation compl&egrave;te
                      </h3>
                      <p className="text-text-secondary text-sm leading-relaxed">
                        10 modules progressifs couvrant Python, Machine Learning, NLP, et les strat&eacute;gies de trading quantitatives. Acc&egrave;s &agrave; vie, mises &agrave; jour incluses.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-end gap-4">
                    <div>
                      <p className="text-sm text-text-muted line-through">499&nbsp;&euro;</p>
                      <p className="text-4xl font-bold text-purple-400">199&nbsp;&euro;</p>
                    </div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-semibold">
                        <Sparkles className="w-3.5 h-3.5" />
                        -60% abonn&eacute;
                      </span>
                      <span className="text-sm text-text-muted">Paiement unique</span>
                    </div>
                  </div>

                  <Button
                    size="lg"
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                    onClick={() => handleAcademyCheckout('standard')}
                    disabled={checkoutLoading}
                  >
                    {checkoutLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                        Redirection...
                      </>
                    ) : (
                      <>
                        <GraduationCap className="w-5 h-5 mr-2" />
                        Acheter la formation — 199&nbsp;&euro;
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Case 3: Non-subscriber without academy → full price 499€ */}
          {!hasAcademy && !isSubscriptionActive && !isGuest && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
              className="max-w-2xl"
            >
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-500/10 via-purple-600/5 to-transparent border border-purple-500/30 p-8">
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                <div className="relative space-y-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <GraduationCap className="w-6 h-6 text-purple-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-text-primary mb-2">
                        Formation compl&egrave;te en Trading Algorithmique &amp; IA
                      </h3>
                      <p className="text-text-secondary text-sm leading-relaxed">
                        10 modules progressifs couvrant Python, Machine Learning, NLP, et les strat&eacute;gies de trading quantitatives. Acc&egrave;s &agrave; vie, mises &agrave; jour incluses.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-end gap-4">
                    <p className="text-4xl font-bold text-purple-400">499&nbsp;&euro;</p>
                    <span className="text-sm text-text-muted mb-1">Paiement unique &middot; Acc&egrave;s &agrave; vie</span>
                  </div>

                  <p className="text-xs text-text-muted">
                    <Crown className="w-3.5 h-3.5 inline mr-1 text-amber-400" />
                    Les abonn&eacute;s Pro b&eacute;n&eacute;ficient d&apos;un tarif exclusif &agrave; <strong className="text-purple-400">199&nbsp;&euro;</strong>.
                    <Link href="/pricing" className="text-purple-400 ml-1 hover:underline">Voir les offres</Link>
                  </p>

                  <div className="flex flex-col gap-3">
                    <div className="flex gap-3">
                      <Button
                        size="lg"
                        className="bg-purple-600 hover:bg-purple-700 text-white"
                        onClick={() => handleAcademyCheckout('standard')}
                        disabled={checkoutLoading}
                      >
                        {checkoutLoading ? (
                          <>
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                            Redirection...
                          </>
                        ) : (
                          <>
                            <GraduationCap className="w-5 h-5 mr-2" />
                            Acheter la formation — 499&nbsp;&euro;
                          </>
                        )}
                      </Button>
                      <Link href="/pricing">
                        <Button variant="secondary" size="lg">S&apos;abonner (-60%)</Button>
                      </Link>
                    </div>
                    <Button
                      size="lg"
                      variant="secondary"
                      className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                      onClick={() => handleAcademyCheckout('diaspora')}
                      disabled={checkoutLoading}
                    >
                      Tarif diaspora africaine — 49&nbsp;&euro;
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Case 4: Guest → signup CTA */}
          {!hasAcademy && isGuest && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 }}
              className="max-w-2xl"
            >
              <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-purple-500/10 via-purple-600/5 to-transparent border border-purple-500/30 p-8">
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 rounded-full -translate-y-1/2 translate-x-1/2" />
                <div className="relative space-y-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <GraduationCap className="w-6 h-6 text-purple-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-text-primary mb-2">
                        Formation compl&egrave;te en Trading Algorithmique &amp; IA
                      </h3>
                      <p className="text-text-secondary text-sm leading-relaxed">
                        10 modules progressifs couvrant Python, Machine Learning, NLP, et les strat&eacute;gies de trading quantitatives. Acc&egrave;s &agrave; vie, mises &agrave; jour incluses.
                      </p>
                    </div>
                  </div>

                  <div className="flex items-end gap-4">
                    <p className="text-4xl font-bold text-purple-400">499&nbsp;&euro;</p>
                    <span className="text-sm text-text-muted mb-1">Paiement unique &middot; Acc&egrave;s &agrave; vie</span>
                  </div>

                  <div className="flex gap-3">
                    <Link href="/signup?redirect=/academy">
                      <Button size="lg" className="bg-purple-600 hover:bg-purple-700 text-white">
                        <GraduationCap className="w-5 h-5 mr-2" />
                        Cr&eacute;er un compte
                      </Button>
                    </Link>
                    <Link href="/pricing">
                      <Button variant="secondary" size="lg">Voir les offres</Button>
                    </Link>
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

            // Lock logic: Only Module 1 (Part 1) has free content (first 2 lessons)
            // All other modules require academy purchase (hasAcademy)
            const isLocked = isGuest || (!hasAcademy && index > 0);

            return (
              <motion.button
                key={`part-${index + 1}`}
                onClick={() => handlePartClick(index)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.05 * index }}
                className={cn(
                  'relative p-6 rounded-lg text-left transition-all group',
                  'bg-surface border border-glass-border hover:border-purple-500/50',
                  isLocked && 'opacity-60 cursor-not-allowed'
                )}
                disabled={isLocked}
              >
                {isLocked && (
                  <AcademyLockOverlay
                    isLocked={true}
                    message={isGuest ? 'Inscription requise' : 'Achetez la formation pour d\u00e9bloquer'}
                  />
                )}

                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="inline-block px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-semibold">
                          Module {index + 1}
                        </span>
                        {isGuest && (
                          <span className="inline-block px-2 py-0.5 rounded-full bg-surface text-text-muted text-xs">
                            <Lock className="w-3 h-3 inline mr-1" />
                            Inscription requise
                          </span>
                        )}
                        {!isGuest && !hasAcademy && index === 0 && (
                          <span className="inline-block px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 text-xs">
                            <GraduationCap className="w-3 h-3 inline mr-1" />
                            2 le&ccedil;ons gratuites
                          </span>
                        )}
                        {!isGuest && !hasAcademy && index > 0 && (
                          <span className="inline-block px-2 py-0.5 rounded-full bg-surface text-text-muted text-xs">
                            <Lock className="w-3 h-3 inline mr-1" />
                            Acc&egrave;s premium
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-text-primary group-hover:text-purple-400 transition-colors">
                        {title}
                      </h3>
                    </div>
                    <ArrowRight className="w-5 h-5 text-purple-400/60 group-hover:text-purple-400 transition-colors flex-shrink-0 mt-1" />
                  </div>

                  <AcademyProgress value={progress} showPercentage={true} />

                  <p className="text-sm text-text-primary/60">{lessonCount} le&ccedil;ons</p>
                </div>
              </motion.button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
