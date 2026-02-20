'use client';

import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Lock, Crown, UserPlus, ArrowRight, Sparkles, Eye } from 'lucide-react';
import Link from 'next/link';
import { useAccessLevel, AccessLevel } from '@/hooks/useAccessLevel';

// ═══════════════════════════════════════════════════════════════════════════
// ACCESS GATE
// Flexible content gating component with 3 access levels:
// - guest: Not logged in → Show signup prompt
// - free: Logged in, no subscription → Show upgrade prompt  
// - subscriber: Paid user → Full access
//
// Inspired by TradingView, Coursera, and Binance Academy patterns
// ═══════════════════════════════════════════════════════════════════════════

interface AccessGateProps {
  /** Minimum access level required */
  requiredLevel: AccessLevel;
  /** The protected content */
  children: ReactNode;
  /** Optional preview content shown to lower access levels */
  preview?: ReactNode;
  /** Feature name for contextual messaging */
  feature?: string;
  /** Custom message for the gate */
  message?: string;
  /** If true, shows a blurred overlay instead of replacing content */
  blurContent?: boolean;
  /** If true, shows inline prompt instead of full-page gate */
  inline?: boolean;
}

export function AccessGate({
  requiredLevel,
  children,
  preview,
  feature,
  message,
  blurContent = false,
  inline = false,
}: AccessGateProps) {
  const { level, isLoading } = useAccessLevel();

  // Loading state
  if (isLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-32 bg-surface rounded-xl" />
      </div>
    );
  }

  // Check if user has sufficient access
  const levelHierarchy: Record<AccessLevel, number> = {
    guest: 0,
    free: 1,
    subscriber: 2,
  };

  if (levelHierarchy[level] >= levelHierarchy[requiredLevel]) {
    return <>{children}</>;
  }

  // Show preview content if available
  if (preview) {
    return (
      <>
        {preview}
        {blurContent ? (
          <BlurOverlayGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />
        ) : inline ? (
          <InlineGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />
        ) : (
          <InlineGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />
        )}
      </>
    );
  }

  // Blur overlay mode
  if (blurContent) {
    return (
      <div className="relative">
        <div className="filter blur-md pointer-events-none select-none opacity-50">
          {children}
        </div>
        <BlurOverlayGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />
      </div>
    );
  }

  // Full gate mode
  if (inline) {
    return <InlineGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />;
  }

  return <FullGate level={level} requiredLevel={requiredLevel} feature={feature} message={message} />;
}

// ═══════════════════════════════════════════════════════════════════════════
// GATE VARIANTS
// ═══════════════════════════════════════════════════════════════════════════

interface GateProps {
  level: AccessLevel;
  requiredLevel: AccessLevel;
  feature?: string;
  message?: string;
}

/** Full-page gate with rich UI */
function FullGate({ level, requiredLevel, feature, message }: GateProps) {
  const isGuestNeedsFree = level === 'guest' && requiredLevel === 'free';
  const needsSubscription = requiredLevel === 'subscriber';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-lg mx-auto py-8"
    >
      <GlassCard className="text-center py-10 px-6">
        <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-6">
          {isGuestNeedsFree ? (
            <UserPlus className="w-8 h-8 text-accent" />
          ) : (
            <Crown className="w-8 h-8 text-accent" />
          )}
        </div>

        <h3 className="text-xl font-bold text-text-primary mb-2">
          {isGuestNeedsFree ? 'Créez votre compte gratuit' : 'Abonnement Pro requis'}
        </h3>

        <p className="text-text-secondary mb-6 max-w-md mx-auto">
          {message || (isGuestNeedsFree
            ? feature
              ? \`Créez un compte gratuit pour accéder à \${feature} et découvrir MarketGPS.\`
              : 'Créez un compte gratuit pour débloquer cette fonctionnalité et bien plus encore.'
            : feature
              ? \`Passez à Pro pour accéder à \${feature} et profiter de toutes les fonctionnalités avancées.\`
              : 'Cette fonctionnalité est réservée aux abonnés Pro.'
          )}
        </p>

        {/* Benefits */}
        <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto mb-8">
          {(isGuestNeedsFree ? [
            'Dashboard personnalisé',
            'Liste de suivi (5 actifs)',
            '10 analyses / jour',
            'Aperçu Academy',
          ] : [
            'Analyses illimitées',
            'Toutes les stratégies',
            'Formation complète',
            'Support prioritaire',
          ]).map((feat, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-text-muted">
              <Sparkles className="w-4 h-4 text-accent flex-shrink-0" />
              {feat}
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {isGuestNeedsFree ? (
            <>
              <Link href="/signup">
                <Button size="lg" leftIcon={<UserPlus className="w-5 h-5" />}>
                  Créer un compte gratuit
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary" size="lg">
                  Se connecter
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link href="/pricing">
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

        {needsSubscription && (
          <p className="mt-6 text-xs text-text-dim">
            À partir de <span className="text-accent font-semibold">9,99€/mois</span>
            {' · '}Annulation à tout moment
          </p>
        )}
      </GlassCard>
    </motion.div>
  );
}

/** Inline compact gate for embedding within pages */
function InlineGate({ level, requiredLevel, feature, message }: GateProps) {
  const isGuestNeedsFree = level === 'guest' && requiredLevel === 'free';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="my-4"
    >
      <div className="flex items-center gap-4 p-4 rounded-xl border border-accent/30 bg-accent/5">
        <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0">
          {isGuestNeedsFree ? (
            <UserPlus className="w-5 h-5 text-accent" />
          ) : (
            <Lock className="w-5 h-5 text-accent" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary">
            {isGuestNeedsFree
              ? 'Créez un compte gratuit pour continuer'
              : feature
                ? \`\${feature} — réservé aux abonnés Pro\`
                : 'Fonctionnalité Pro'
            }
          </p>
          <p className="text-xs text-text-muted mt-0.5">
            {message || (isGuestNeedsFree
              ? 'Inscription rapide, sans engagement'
              : 'À partir de 9,99€/mois'
            )}
          </p>
        </div>
        <Link href={isGuestNeedsFree ? '/signup' : '/pricing'}>
          <Button size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
            {isGuestNeedsFree ? "S'inscrire" : 'Voir les offres'}
          </Button>
        </Link>
      </div>
    </motion.div>
  );
}

/** Blur overlay gate positioned over blurred content */
function BlurOverlayGate({ level, requiredLevel, feature, message }: GateProps) {
  const isGuestNeedsFree = level === 'guest' && requiredLevel === 'free';

  return (
    <div className="absolute inset-0 flex items-center justify-center z-10">
      <div className="text-center p-6 rounded-2xl bg-bg-primary/80 backdrop-blur-sm border border-glass-border shadow-xl max-w-sm mx-4">
        <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-4">
          <Eye className="w-6 h-6 text-accent" />
        </div>
        <h4 className="font-bold text-text-primary mb-2">
          {isGuestNeedsFree ? 'Aperçu limité' : 'Contenu Pro'}
        </h4>
        <p className="text-sm text-text-secondary mb-4">
          {message || (feature
            ? \`\${feature} nécessite \${isGuestNeedsFree ? 'un compte gratuit' : 'un abonnement Pro'}\`
            : \`\${isGuestNeedsFree ? 'Créez un compte' : 'Passez à Pro'} pour accéder au contenu complet\`
          )}
        </p>
        <Link href={isGuestNeedsFree ? '/signup' : '/pricing'}>
          <Button size="sm" leftIcon={isGuestNeedsFree ? <UserPlus className="w-4 h-4" /> : <Crown className="w-4 h-4" />}>
            {isGuestNeedsFree ? "S'inscrire gratuitement" : 'Passer à Pro'}
          </Button>
        </Link>
      </div>
    </div>
  );
}

export default AccessGate;
