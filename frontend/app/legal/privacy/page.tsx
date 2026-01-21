'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import {
  ArrowLeft,
  Shield,
  Database,
  Eye,
  Lock,
  UserCheck,
  Mail,
  Calendar,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// PRIVACY POLICY PAGE - MARKETGPS
// ═══════════════════════════════════════════════════════════════════════════

const LAST_UPDATED = '21 janvier 2026';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-accent/5 via-transparent to-transparent" />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-xl border-b border-glass-border">
        <div className="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
              <span className="text-white font-bold text-sm">◉</span>
            </div>
            <span className="text-lg font-semibold">
              Market<span className="text-text-muted">GPS</span>
            </span>
          </Link>
          <Link href="/">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Retour
            </Button>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-4xl mx-auto px-6 py-16">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/10 mb-6">
            <Shield className="w-8 h-8 text-accent" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-4">
            Politique de Confidentialité
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Chez MarketGPS, nous vendons de l&apos;intelligence, pas vos données. 
            Votre vie privée est notre actif le plus précieux.
          </p>
          <div className="flex items-center justify-center gap-2 mt-6 text-sm text-text-muted">
            <Calendar className="w-4 h-4" />
            <span>Dernière mise à jour : {LAST_UPDATED}</span>
          </div>
        </motion.div>

        {/* Content */}
        <div className="space-y-8">
          {/* Section 1 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Database className="w-5 h-5" />} 
                number="1" 
                title="Collecte des données" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Nous collectons uniquement les données strictement nécessaires au fonctionnement 
                  du service MarketGPS :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Email et informations de compte</strong> — 
                      Pour l&apos;authentification et la gestion de votre abonnement.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Données d&apos;utilisation</strong> — 
                      Pages visitées, fonctionnalités utilisées, pour améliorer nos algorithmes de scoring 
                      et votre expérience utilisateur.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Préférences de stratégie</strong> — 
                      Vos watchlists, stratégies personnalisées et paramètres d&apos;affichage.
                    </span>
                  </li>
                </ul>
              </div>
            </GlassCard>
          </motion.div>

          {/* Section 2 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Eye className="w-5 h-5" />} 
                number="2" 
                title="Utilisation des données" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Vos données servent exclusivement à :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Personnaliser votre dashboard et vos recommandations de stratégies.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Améliorer la précision de nos scores et de notre système de gating.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Vous envoyer des notifications importantes concernant votre compte ou vos alertes configurées.
                    </span>
                  </li>
                </ul>
                <div className="mt-6 p-4 rounded-xl bg-accent/10 border border-accent/20">
                  <p className="text-accent font-semibold mb-2">🔒 Engagement fort</p>
                  <p className="text-slate-300 text-sm">
                    Vos données ne sont <strong className="text-text-primary">jamais vendues</strong> à 
                    des tiers publicitaires. Nous ne pratiquons pas le profilage commercial. 
                    Notre modèle économique repose uniquement sur les abonnements.
                  </p>
                </div>
              </div>
            </GlassCard>
          </motion.div>

          {/* Section 3 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Lock className="w-5 h-5" />} 
                number="3" 
                title="Sécurité des données" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  La sécurité de vos données est notre priorité absolue. Nous mettons en œuvre 
                  les mesures suivantes :
                </p>
                <div className="grid md:grid-cols-2 gap-4">
                  <SecurityBadge 
                    title="Chiffrement AES-256" 
                    description="Données au repos chiffrées avec le standard le plus élevé de l'industrie." 
                  />
                  <SecurityBadge 
                    title="TLS 1.3" 
                    description="Toutes les communications sont chiffrées de bout en bout." 
                  />
                  <SecurityBadge 
                    title="Paiements Stripe" 
                    description="Nous ne stockons jamais vos informations bancaires. Stripe gère les transactions de manière sécurisée." 
                  />
                  <SecurityBadge 
                    title="Hébergement sécurisé" 
                    description="Infrastructure hébergée sur des serveurs conformes aux normes ISO 27001." 
                  />
                </div>
              </div>
            </GlassCard>
          </motion.div>

          {/* Section 4 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<UserCheck className="w-5 h-5" />} 
                number="4" 
                title="Vos droits (RGPD)" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Conformément au Règlement Général sur la Protection des Données (RGPD), 
                  vous disposez des droits suivants :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Droit d&apos;accès</strong> — 
                      Obtenir une copie de toutes les données que nous détenons sur vous.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Droit de rectification</strong> — 
                      Corriger des informations inexactes vous concernant.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Droit à l&apos;effacement</strong> — 
                      Demander la suppression intégrale de votre compte et de vos données.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Droit à la portabilité</strong> — 
                      Exporter vos données dans un format structuré et lisible par machine.
                    </span>
                  </li>
                </ul>
                <div className="mt-6 p-4 rounded-xl bg-surface border border-glass-border">
                  <div className="flex items-center gap-3 mb-2">
                    <Mail className="w-5 h-5 text-accent" />
                    <p className="text-text-primary font-semibold">Délégué à la Protection des Données</p>
                  </div>
                  <p className="text-slate-300 text-sm">
                    Pour exercer vos droits ou pour toute question relative à vos données personnelles, 
                    contactez notre DPO à l&apos;adresse : {' '}
                    <a href="mailto:dpo@marketgps.online" className="text-accent hover:underline">
                      dpo@marketgps.online
                    </a>
                  </p>
                </div>
              </div>
            </GlassCard>
          </motion.div>

          {/* Section 5 - Cookies */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Database className="w-5 h-5" />} 
                number="5" 
                title="Cookies et traceurs" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Nous utilisons des cookies strictement nécessaires au fonctionnement du site :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Cookies d&apos;authentification</strong> — 
                      Pour maintenir votre session active.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Cookies de préférences</strong> — 
                      Pour mémoriser vos paramètres d&apos;affichage.
                    </span>
                  </li>
                </ul>
                <p className="text-slate-300 leading-relaxed mt-4">
                  Nous n&apos;utilisons <strong className="text-text-primary">aucun cookie publicitaire</strong> ni 
                  aucun traceur de réseaux sociaux.
                </p>
              </div>
            </GlassCard>
          </motion.div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-12 text-center"
        >
          <p className="text-text-muted mb-4">
            Des questions sur notre politique de confidentialité ?
          </p>
          <Link href="/contact">
            <Button variant="outline" rightIcon={<Mail className="w-4 h-4" />}>
              Nous contacter
            </Button>
          </Link>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="relative py-8 px-6 border-t border-glass-border mt-16">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-text-muted">
            © 2024 MarketGPS. Tous droits réservés.
          </p>
          <div className="flex gap-6 text-sm text-text-muted">
            <Link href="/legal/terms" className="hover:text-text-primary transition-colors">
              CGU
            </Link>
            <Link href="/contact" className="hover:text-text-primary transition-colors">
              Contact
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPER COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function SectionHeader({ icon, number, title }: { icon: React.ReactNode; number: string; title: string }) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-accent/10 text-accent">
        {icon}
      </div>
      <div>
        <span className="text-xs text-text-muted uppercase tracking-wider">Section {number}</span>
        <h2 className="text-xl font-semibold text-text-primary">{title}</h2>
      </div>
    </div>
  );
}

function SecurityBadge({ title, description }: { title: string; description: string }) {
  return (
    <div className="p-4 rounded-xl bg-surface border border-glass-border">
      <p className="font-semibold text-text-primary mb-1">{title}</p>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}
