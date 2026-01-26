'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  CheckCircle2,
  Zap,
  Crown,
  Shield,
  Loader2,
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

// ═══════════════════════════════════════════════════════════════════════════
// CHOOSE PLAN PAGE
// Displayed after signup or when accessing protected routes without subscription
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

export default function ChoosePlanPage() {
  const router = useRouter();
  const { session, isLoading: authLoading, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/billing/choose-plan');
    }
  }, [authLoading, isAuthenticated, router]);

  const handleSubscribe = async (plan: 'monthly' | 'annual') => {
    if (!session?.access_token) {
      router.push('/login?redirect=/billing/choose-plan');
      return;
    }

    setLoading(plan);

    try {
      const response = await fetch(`${API_URL}/api/billing/checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ plan }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create checkout session');
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
      id: 'monthly',
      name: 'Pro Mensuel',
      price: '9,99€',
      period: '/mois',
      description: 'Parfait pour commencer',
      icon: Zap,
      features: [
        'Calculs de score illimités',
        'Tous les indicateurs avancés',
        'Export des données (CSV, Excel)',
        'Liste de suivi illimitée',
        'Alertes personnalisées',
        'Support prioritaire',
      ],
    },
    {
      id: 'annual',
      name: 'Pro Annuel',
      price: '99,99€',
      period: '/an',
      description: 'Économisez 17%',
      icon: Crown,
      badge: 'Meilleure offre',
      features: [
        'Tout le plan Pro Mensuel',
        'Économisez 19,89€/an',
        'Accès anticipé nouvelles features',
        'Support dédié',
        '2 mois gratuits',
      ],
      highlighted: true,
    },
  ];

  if (authLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-purple-500/5" />

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-4xl"
        >
          {/* Logo */}
          <div className="text-center mb-8">
            <Link href="/" className="inline-flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow">
                <span className="text-xl text-white font-bold">◉</span>
              </div>
              <span className="text-2xl font-bold text-text-primary">MarketGPS</span>
            </Link>
          </div>

          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-text-primary mb-3">
              Choisissez votre plan
            </h1>
            <p className="text-text-secondary text-lg max-w-xl mx-auto">
              Débloquez tout le potentiel de MarketGPS avec un abonnement Pro
            </p>
          </div>

          {/* Plans */}
          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
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
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-accent text-bg-primary text-sm font-semibold">
                      {plan.badge}
                    </div>
                  )}

                  <div className="text-center mb-6">
                    <div className={cn(
                      'w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center',
                      plan.highlighted ? 'bg-accent text-bg-primary' : 'bg-surface text-accent'
                    )}>
                      <Icon className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-bold text-text-primary">{plan.name}</h3>
                    <p className="text-sm text-text-muted mt-1">{plan.description}</p>
                    <p className="text-4xl font-bold text-text-primary mt-4">
                      {plan.price}
                      <span className="text-lg text-text-muted">{plan.period}</span>
                    </p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-text-secondary">
                        <CheckCircle2 className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Button
                    variant={plan.highlighted ? 'primary' : 'secondary'}
                    className="w-full"
                    size="lg"
                    loading={loading === plan.id}
                    onClick={() => handleSubscribe(plan.id as 'monthly' | 'annual')}
                  >
                    Commencer avec {plan.name}
                  </Button>
                </GlassCardAccent>
              );
            })}
          </div>

          {/* Trust badges */}
          <div className="flex flex-wrap items-center justify-center gap-6 mt-10 text-text-muted text-sm">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Paiement sécurisé
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Annulation à tout moment
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Activation instantanée
            </div>
          </div>

          {/* Help text */}
          <p className="mt-8 text-center text-sm text-text-muted">
            Des questions ?{' '}
            <a href="mailto:support@marketgps.online" className="text-accent hover:underline">
              Contactez-nous
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
