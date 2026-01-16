'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { cn } from '@/lib/utils';
import {
  Star,
  Zap,
  Crown,
  CheckCircle2,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// PRICING PAGE
// ═══════════════════════════════════════════════════════════════════════════

const plans = [
  {
    id: 'free',
    name: 'Gratuit',
    price: '0€',
    period: '',
    description: 'Pour découvrir MarketGPS',
    icon: Star,
    features: [
      '3 calculs de score par jour',
      'Accès à tous les marchés',
      'Graphiques de base',
      'Liste de suivi (5 actifs)',
    ],
    cta: 'Commencer gratuitement',
    ctaHref: '/signup',
  },
  {
    id: 'monthly',
    name: 'Pro Mensuel',
    price: '9,99€',
    period: '/mois',
    description: 'Pour les traders actifs',
    icon: Zap,
    features: [
      'Calculs illimités',
      'Tous les indicateurs',
      'Export des données CSV',
      'Liste de suivi illimitée',
      'Support prioritaire',
      'Alertes personnalisées',
    ],
    cta: 'S\'abonner',
    ctaHref: '/signup?plan=monthly',
  },
  {
    id: 'yearly',
    name: 'Pro Annuel',
    price: '99,99€',
    period: '/an',
    description: 'Meilleure valeur',
    icon: Crown,
    badge: 'Économisez 58%',
    features: [
      'Tout le plan Pro',
      'Économisez 70€/an',
      'Accès anticipé nouvelles features',
      'Support dédié',
      'Webinaires exclusifs',
      'API access (bientôt)',
    ],
    cta: 'Meilleure offre',
    ctaHref: '/signup?plan=yearly',
    highlighted: true,
  },
];

const faqs = [
  {
    question: 'Puis-je annuler à tout moment ?',
    answer: 'Oui, vous pouvez annuler votre abonnement à tout moment depuis vos paramètres. Vous conserverez l\'accès Pro jusqu\'à la fin de votre période de facturation actuelle.',
  },
  {
    question: 'Quels moyens de paiement acceptez-vous ?',
    answer: 'Nous acceptons les cartes bancaires Visa, Mastercard et American Express via Stripe, notre partenaire de paiement sécurisé.',
  },
  {
    question: 'Y a-t-il un remboursement possible ?',
    answer: 'Nous offrons un remboursement complet dans les 14 jours suivant votre souscription si vous n\'êtes pas satisfait.',
  },
  {
    question: 'Comment fonctionne le plan gratuit ?',
    answer: 'Le plan gratuit vous donne accès à toutes les fonctionnalités de base avec une limite de 3 calculs de score par jour. C\'est idéal pour découvrir MarketGPS.',
  },
  {
    question: 'Les données sont-elles à jour ?',
    answer: 'Oui, nos données sont mises à jour quotidiennement à partir de sources financières reconnues (EOD Historical Data, Yahoo Finance).',
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-bg-primary/80 backdrop-blur-glass border-b border-glass-border">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow-sm">
              <span className="text-white font-bold">◉</span>
            </div>
            <span className="text-lg font-bold text-text-primary">MarketGPS</span>
          </Link>

          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Connexion</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm">S&apos;inscrire</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-dim text-accent text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              Tarification simple et transparente
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-4">
              Choisissez votre plan
            </h1>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              Commencez gratuitement, passez Pro quand vous êtes prêt.
              Aucun engagement, annulation à tout moment.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Plans */}
      <section className="pb-20 px-6">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => {
            const Icon = plan.icon;
            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <GlassCardAccent
                  className={cn(
                    'h-full relative',
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
                      'w-14 h-14 rounded-xl mx-auto mb-4 flex items-center justify-center',
                      plan.highlighted ? 'bg-accent text-bg-primary' : 'bg-surface text-text-secondary'
                    )}>
                      <Icon className="w-7 h-7" />
                    </div>
                    <h3 className="text-xl font-semibold text-text-primary">{plan.name}</h3>
                    <p className="text-sm text-text-muted mt-1">{plan.description}</p>
                    <p className="text-4xl font-bold text-text-primary mt-4">
                      {plan.price}
                      <span className="text-lg text-text-muted">{plan.period}</span>
                    </p>
                  </div>

                  <ul className="space-y-3 mb-8">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-2 text-sm text-text-secondary">
                        <CheckCircle2 className="w-4 h-4 text-accent flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <Link href={plan.ctaHref} className="block">
                    <Button
                      variant={plan.highlighted ? 'primary' : 'secondary'}
                      className="w-full"
                      size="lg"
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </GlassCardAccent>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Comparison table */}
      <section className="pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-text-primary text-center mb-10">
            Comparaison détaillée
          </h2>
          <GlassCard padding="none">
            <table className="w-full">
              <thead>
                <tr className="border-b border-glass-border">
                  <th className="text-left p-4 text-text-muted font-medium">Fonctionnalité</th>
                  <th className="text-center p-4 text-text-muted font-medium">Gratuit</th>
                  <th className="text-center p-4 text-text-muted font-medium">Pro</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ['Calculs de score', '3/jour', 'Illimité'],
                  ['Marchés (US, Europe, Afrique)', '✓', '✓'],
                  ['Graphiques de prix', 'Base', 'Avancés'],
                  ['Liste de suivi', '5 actifs', 'Illimité'],
                  ['Export CSV', '—', '✓'],
                  ['Alertes personnalisées', '—', '✓'],
                  ['Support', 'Standard', 'Prioritaire'],
                  ['API access', '—', 'Bientôt'],
                ].map(([feature, free, pro], i) => (
                  <tr key={i} className="border-b border-glass-border last:border-0">
                    <td className="p-4 text-text-secondary">{feature}</td>
                    <td className="p-4 text-center text-text-muted">{free}</td>
                    <td className="p-4 text-center text-accent font-medium">{pro}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
        </div>
      </section>

      {/* FAQ */}
      <section className="pb-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-text-primary text-center mb-10">
            Questions fréquentes
          </h2>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <FaqItem key={i} question={faq.question} answer={faq.answer} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-20 px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="max-w-3xl mx-auto text-center"
        >
          <GlassCard className="border-accent">
            <h2 className="text-2xl font-bold text-text-primary mb-4">
              Prêt à naviguer les marchés ?
            </h2>
            <p className="text-text-secondary mb-6">
              Commencez gratuitement dès maintenant. Aucune carte bancaire requise.
            </p>
            <Link href="/signup">
              <Button size="lg">
                Créer mon compte gratuit
              </Button>
            </Link>
          </GlassCard>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-glass-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
              <span className="text-white font-bold text-sm">◉</span>
            </div>
            <span className="font-bold text-text-primary">MarketGPS</span>
          </div>
          <p className="text-xs text-text-dim">
            © 2024 MarketGPS. Outil d&apos;analyse statistique et éducatif.
          </p>
        </div>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// FAQ ITEM COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

import { useState } from 'react';

function FaqItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <GlassCard padding="none">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full p-5 text-left"
      >
        <span className="font-medium text-text-primary">{question}</span>
        <span className="text-text-muted text-xl">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="px-5 pb-5"
        >
          <p className="text-sm text-text-secondary">{answer}</p>
        </motion.div>
      )}
    </GlassCard>
  );
}
