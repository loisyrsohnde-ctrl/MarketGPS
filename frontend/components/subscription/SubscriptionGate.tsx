'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Crown, Lock, Sparkles, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

// ═══════════════════════════════════════════════════════════════════════════
// SUBSCRIPTION GATE
// Blocks content for non-subscribed users with upgrade CTA
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

interface SubscriptionStatus {
  user_id: string;
  plan: string;
  status: string;
  is_active: boolean;
  current_period_end?: string;
  grace_period_remaining_hours?: number;
}

interface SubscriptionGateProps {
  children: React.ReactNode;
  feature?: string; // Optional feature name for messaging
  fallback?: React.ReactNode; // Custom fallback content
}

export function SubscriptionGate({ children, feature, fallback }: SubscriptionGateProps) {
  const { session, isLoading: authLoading } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSubscription = async () => {
      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/billing/me`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setSubscription(data);
        }
      } catch (error) {
        console.error('Error fetching subscription:', error);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) {
      fetchSubscription();
    }
  }, [session, authLoading]);

  // Loading state
  if (loading || authLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-32 bg-surface rounded-xl" />
      </div>
    );
  }

  // Not logged in
  if (!session) {
    return (
      <SubscriptionRequired 
        message="Connectez-vous pour accéder à cette fonctionnalité"
        showLogin
        feature={feature}
      />
    );
  }

  // Has active subscription
  if (subscription?.is_active) {
    return <>{children}</>;
  }

  // Show fallback or default paywall
  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <SubscriptionRequired 
      feature={feature}
      gracePeriod={subscription?.grace_period_remaining_hours}
    />
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// SUBSCRIPTION REQUIRED COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

interface SubscriptionRequiredProps {
  message?: string;
  showLogin?: boolean;
  feature?: string;
  gracePeriod?: number;
}

export function SubscriptionRequired({ 
  message,
  showLogin,
  feature,
  gracePeriod,
}: SubscriptionRequiredProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full"
    >
      <GlassCard className="text-center py-12 px-6">
        <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
          <Lock className="w-8 h-8 text-accent" />
        </div>
        
        <h3 className="text-xl font-bold text-text-primary mb-2">
          {showLogin ? 'Connexion requise' : 'Abonnement Pro requis'}
        </h3>
        
        <p className="text-text-secondary mb-6 max-w-md mx-auto">
          {message || (
            feature
              ? `Accédez à ${feature} et à toutes les fonctionnalités Pro avec un abonnement MarketGPS.`
              : 'Cette fonctionnalité nécessite un abonnement MarketGPS Pro.'
          )}
        </p>

        {gracePeriod && gracePeriod > 0 && (
          <div className="mb-6 p-3 rounded-lg bg-score-yellow/10 border border-score-yellow/30">
            <p className="text-sm text-score-yellow">
              ⚠️ Votre paiement a échoué. Il vous reste{' '}
              <strong>{gracePeriod}h</strong> pour mettre à jour votre moyen de paiement.
            </p>
          </div>
        )}

        {/* Features list */}
        <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto mb-8">
          {[
            'Calculs illimités',
            'Tous les indicateurs',
            'Export des données',
            'Support prioritaire',
          ].map((feat, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-sm text-text-muted"
            >
              <Sparkles className="w-4 h-4 text-accent" />
              {feat}
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {showLogin ? (
            <>
              <Link href="/login">
                <Button size="lg">
                  Se connecter
                </Button>
              </Link>
              <Link href="/signup">
                <Button variant="secondary" size="lg">
                  Créer un compte
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/settings/billing">
                <Button 
                  size="lg" 
                  leftIcon={<Crown className="w-5 h-5" />}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Passer à Pro
                </Button>
              </Link>
              <Link href="/dashboard">
                <Button variant="secondary" size="lg">
                  Retour au Dashboard
                </Button>
              </Link>
            </>
          )}
        </div>

        {/* Pricing hint */}
        <p className="mt-6 text-xs text-text-dim">
          À partir de <span className="text-accent font-semibold">9,99€/mois</span>
          {' · '}Annulation à tout moment
        </p>
      </GlassCard>
    </motion.div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HOOK: useSubscription
// ═══════════════════════════════════════════════════════════════════════════

export function useSubscription() {
  const { session } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchSubscription = async () => {
      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/billing/me`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch subscription');
        }

        const data = await response.json();
        setSubscription(data);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setLoading(false);
      }
    };

    fetchSubscription();
  }, [session]);

  return {
    subscription,
    loading,
    error,
    isActive: subscription?.is_active ?? false,
    plan: subscription?.plan ?? 'free',
    status: subscription?.status ?? 'inactive',
  };
}

export default SubscriptionGate;
