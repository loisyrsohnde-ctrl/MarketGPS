'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/glass-card';
import { CheckCircle2, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

// ═══════════════════════════════════════════════════════════════════════════
// BILLING SUCCESS PAGE
// Polls /api/billing/me until subscription is active, then redirects
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

export default function BillingSuccessPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <BillingSuccessContent />
    </Suspense>
  );
}

function LoadingState() {
  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-accent" />
    </div>
  );
}

function BillingSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { session } = useAuth();
  const sessionId = searchParams.get('session_id');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [pollCount, setPollCount] = useState(0);
  const [plan, setPlan] = useState<string>('');
  const maxPolls = 30; // Max 60 seconds (2s intervals)

  useEffect(() => {
    if (!session?.access_token) return;

    const checkSubscription = async () => {
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

        if (data.is_active) {
          setPlan(data.plan);
          setStatus('success');
          
          // Wait 2s to show success, then redirect
          setTimeout(() => {
            router.push('/dashboard');
          }, 2500);
        } else if (pollCount < maxPolls) {
          // Keep polling
          setPollCount(prev => prev + 1);
          setTimeout(checkSubscription, 2000);
        } else {
          // Timeout
          setStatus('error');
        }
      } catch (error) {
        console.error('Error checking subscription:', error);
        if (pollCount < maxPolls) {
          setPollCount(prev => prev + 1);
          setTimeout(checkSubscription, 2000);
        } else {
          setStatus('error');
        }
      }
    };

    checkSubscription();
  }, [session, pollCount, router]);

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-purple-500/5" />

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center p-6 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
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

          <GlassCard padding="lg" className="text-center">
            {status === 'loading' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-8"
              >
                <div className="w-20 h-20 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
                  <Loader2 className="w-10 h-10 text-accent animate-spin" />
                </div>
                <h2 className="text-xl font-bold text-text-primary mb-2">
                  Activation en cours...
                </h2>
                <p className="text-text-secondary">
                  Nous configurons votre abonnement. Cela ne prendra qu'un instant.
                </p>
                <div className="mt-6 flex items-center justify-center gap-1">
                  {[...Array(3)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="w-2 h-2 rounded-full bg-accent"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}
                </div>
              </motion.div>
            )}

            {status === 'success' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="py-8"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', delay: 0.2 }}
                  className="w-20 h-20 rounded-full bg-score-green/15 flex items-center justify-center mx-auto mb-6"
                >
                  <CheckCircle2 className="w-10 h-10 text-score-green" />
                </motion.div>
                <h2 className="text-xl font-bold text-text-primary mb-2">
                  Bienvenue dans MarketGPS Pro !
                </h2>
                <p className="text-text-secondary mb-4">
                  Votre abonnement{' '}
                  <span className="text-accent font-semibold">
                    {plan === 'annual' ? 'Annuel' : 'Mensuel'}
                  </span>{' '}
                  est maintenant actif.
                </p>
                <div className="flex items-center justify-center gap-2 text-score-green">
                  <Sparkles className="w-4 h-4" />
                  <span className="text-sm">Redirection vers le dashboard...</span>
                </div>
              </motion.div>
            )}

            {status === 'error' && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-8"
              >
                <div className="w-20 h-20 rounded-full bg-score-yellow/15 flex items-center justify-center mx-auto mb-6">
                  <AlertCircle className="w-10 h-10 text-score-yellow" />
                </div>
                <h2 className="text-xl font-bold text-text-primary mb-2">
                  Activation en attente
                </h2>
                <p className="text-text-secondary mb-6">
                  Votre paiement a bien été reçu. L'activation peut prendre quelques minutes.
                </p>
                <div className="space-y-3">
                  <Button
                    onClick={() => router.push('/dashboard')}
                    className="w-full"
                  >
                    Aller au Dashboard
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setStatus('loading');
                      setPollCount(0);
                    }}
                    className="w-full"
                  >
                    Réessayer
                  </Button>
                </div>
              </motion.div>
            )}
          </GlassCard>

          {/* Help text */}
          <p className="mt-6 text-center text-sm text-text-muted">
            Un problème ?{' '}
            <a href="mailto:support@marketgps.online" className="text-accent hover:underline">
              Contactez le support
            </a>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
