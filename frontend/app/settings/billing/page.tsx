'use client';

export const dynamic = 'force-dynamic';

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  CreditCard,
  CheckCircle2,
  Star,
  Zap,
  Crown,
  ArrowLeft,
  ExternalLink,
} from 'lucide-react';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════
// BILLING PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function BillingPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg-primary" />}>
      <BillingContent />
    </Suspense>
  );
}

function BillingContent() {
  const searchParams = useSearchParams();
  const success = searchParams.get('success') === '1';
  const canceled = searchParams.get('canceled') === '1';

  const [currentPlan] = useState<'free' | 'monthly' | 'yearly'>('free');
  const [loading, setLoading] = useState<string | null>(null);

  const handleSubscribe = async (plan: 'monthly' | 'yearly') => {
    setLoading(plan);
    
    try {
      // Get session token (assuming useAuth hook exists)
      const token = typeof window !== 'undefined' 
        ? localStorage.getItem('supabase.auth.token') 
        : null;
      
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online'}/api/billing/checkout-session`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ plan: plan === 'yearly' ? 'annual' : plan }),
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }
      
      const data = await response.json();
      
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Erreur lors de la création de la session de paiement. Veuillez réessayer.');
    } finally {
      setLoading(null);
    }
  };

  const plans = [
    {
      id: 'free',
      name: 'Gratuit',
      price: '0€',
      period: '',
      icon: Star,
      features: [
        '3 calculs de score par jour',
        'Accès à tous les marchés',
        'Graphiques de base',
        'Liste de suivi (5 actifs)',
      ],
      current: currentPlan === 'free',
    },
    {
      id: 'monthly',
      name: 'Pro Mensuel',
      price: '9,99€',
      period: '/mois',
      icon: Zap,
      features: [
        'Calculs illimités',
        'Tous les indicateurs',
        'Export des données',
        'Liste de suivi illimitée',
        'Support prioritaire',
      ],
      current: currentPlan === 'monthly',
    },
    {
      id: 'yearly',
      name: 'Pro Annuel',
      price: '99,99€',
      period: '/an',
      icon: Crown,
      badge: 'Économisez 80%',
      features: [
        'Tout le plan Pro',
        'Économisez 109,89€/an',
        'Accès anticipé nouvelles features',
        'Support dédié',
      ],
      current: currentPlan === 'yearly',
      highlighted: true,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Back link */}
      <Link
        href="/settings"
        className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux paramètres
      </Link>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary flex items-center gap-3">
          <CreditCard className="w-7 h-7 text-accent" />
          Abonnement
        </h1>
        <p className="text-text-secondary mt-1">Gérez votre plan et votre facturation</p>
      </div>

      {/* Success/Cancel messages */}
      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-score-green/10 border border-score-green/30 flex items-center gap-3"
        >
          <CheckCircle2 className="w-5 h-5 text-score-green" />
          <p className="text-sm text-score-green">
            Merci pour votre abonnement ! Votre compte a été mis à jour.
          </p>
        </motion.div>
      )}

      {canceled && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl bg-score-yellow/10 border border-score-yellow/30 flex items-center gap-3"
        >
          <Star className="w-5 h-5 text-score-yellow" />
          <p className="text-sm text-score-yellow">
            Paiement annulé. Vous pouvez réessayer à tout moment.
          </p>
        </motion.div>
      )}

      {/* Current plan */}
      <GlassCard>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text-muted uppercase tracking-wide">Plan actuel</p>
            <p className="text-xl font-bold text-text-primary mt-1">
              {currentPlan === 'free' ? 'Gratuit' : currentPlan === 'monthly' ? 'Pro Mensuel' : 'Pro Annuel'}
            </p>
          </div>
          {currentPlan !== 'free' && (
            <div className="text-right">
              <p className="text-sm text-text-muted">Prochain renouvellement</p>
              <p className="text-text-secondary">15 février 2025</p>
            </div>
          )}
        </div>

        {currentPlan !== 'free' && (
          <div className="mt-4 pt-4 border-t border-glass-border flex gap-3">
            <Button variant="secondary" size="sm" leftIcon={<ExternalLink className="w-4 h-4" />}>
              Gérer sur Stripe
            </Button>
            <Button variant="danger" size="sm">
              Annuler l&apos;abonnement
            </Button>
          </div>
        )}
      </GlassCard>

      {/* Plans */}
      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const Icon = plan.icon;
          return (
            <GlassCardAccent
              key={plan.id}
              className={cn(
                'relative',
                plan.highlighted && 'border-accent shadow-glow'
              )}
              padding="lg"
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-accent text-bg-primary text-xs font-semibold">
                  {plan.badge}
                </div>
              )}

              <div className="text-center mb-6">
                <div className={cn(
                  'w-12 h-12 rounded-xl mx-auto mb-3 flex items-center justify-center',
                  plan.current ? 'bg-accent text-bg-primary' : 'bg-surface text-text-secondary'
                )}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary">{plan.name}</h3>
                <p className="text-3xl font-bold text-text-primary mt-2">
                  {plan.price}
                  <span className="text-lg text-text-muted">{plan.period}</span>
                </p>
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-text-secondary">
                    <CheckCircle2 className="w-4 h-4 text-accent flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              {plan.current ? (
                <Button variant="secondary" className="w-full" disabled>
                  Plan actuel
                </Button>
              ) : plan.id === 'free' ? (
                <Button variant="outline" className="w-full" disabled>
                  —
                </Button>
              ) : (
                <Button
                  variant={plan.highlighted ? 'primary' : 'secondary'}
                  className="w-full"
                  loading={loading === plan.id}
                  onClick={() => handleSubscribe(plan.id as 'monthly' | 'yearly')}
                >
                  Passer à {plan.name}
                </Button>
              )}
            </GlassCardAccent>
          );
        })}
      </div>

      {/* FAQ */}
      <GlassCard className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">Questions fréquentes</h2>

        <div className="space-y-4">
          <FaqItem
            question="Puis-je annuler à tout moment ?"
            answer="Oui, vous pouvez annuler votre abonnement à tout moment. Vous conserverez l'accès Pro jusqu'à la fin de votre période de facturation."
          />
          <FaqItem
            question="Comment fonctionne le paiement ?"
            answer="Les paiements sont gérés de manière sécurisée par Stripe. Nous acceptons les cartes bancaires Visa, Mastercard et American Express."
          />
          <FaqItem
            question="Y a-t-il une période d'essai ?"
            answer="Le plan gratuit vous permet de tester MarketGPS avec 3 calculs de score par jour. Passez Pro quand vous êtes prêt !"
          />
        </div>
      </GlassCard>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// FAQ ITEM COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-glass-border pb-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-left"
      >
        <span className="font-medium text-text-primary">{question}</span>
        <span className="text-text-muted">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <motion.p
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-2 text-sm text-text-secondary"
        >
          {answer}
        </motion.p>
      )}
    </div>
  );
}
