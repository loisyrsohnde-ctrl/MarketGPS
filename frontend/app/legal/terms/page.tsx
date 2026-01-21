'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import {
  ArrowLeft,
  FileText,
  AlertTriangle,
  Database,
  CreditCard,
  Scale,
  Calendar,
  Briefcase,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// TERMS OF SERVICE PAGE - MARKETGPS
// ═══════════════════════════════════════════════════════════════════════════

const LAST_UPDATED = '21 janvier 2026';

export default function TermsOfServicePage() {
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
            <FileText className="w-8 h-8 text-accent" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-4">
            Conditions Générales d&apos;Utilisation
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Les présentes CGU régissent l&apos;utilisation de la plateforme MarketGPS. 
            En utilisant nos services, vous acceptez ces conditions.
          </p>
          <div className="flex items-center justify-center gap-2 mt-6 text-sm text-text-muted">
            <Calendar className="w-4 h-4" />
            <span>Dernière mise à jour : {LAST_UPDATED}</span>
          </div>
        </motion.div>

        {/* Critical Disclaimer Banner */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mb-8"
        >
          <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30">
            <div className="flex items-start gap-4">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-amber-400 mb-2">
                  ⚠️ Avertissement Important
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  <strong className="text-text-primary">MarketGPS n&apos;est pas un conseiller financier.</strong> Les 
                  informations, scores et analyses fournis sur cette plateforme sont destinés à des fins 
                  éducatives et informatives uniquement. Ils ne constituent en aucun cas des conseils en 
                  investissement, des recommandations d&apos;achat ou de vente, ou une incitation à investir.
                </p>
                <p className="text-slate-300 leading-relaxed mt-3">
                  <strong className="text-amber-400">L&apos;utilisateur est seul responsable de ses décisions d&apos;investissement.</strong> Nous 
                  vous recommandons de consulter un conseiller financier agréé avant toute décision d&apos;investissement.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Content */}
        <div className="space-y-8">
          {/* Clause 1 - Disclaimer */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<AlertTriangle className="w-5 h-5" />} 
                number="1" 
                title="Avertissement sur les risques (Disclaimer)" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  MarketGPS est un outil d&apos;analyse quantitative et de visualisation de données financières. 
                  En utilisant ce service, vous reconnaissez et acceptez que :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Les scores, analyses et informations fournis le sont <strong className="text-text-primary">à titre indicatif uniquement</strong> et 
                      ne constituent pas des conseils financiers personnalisés.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Les marchés financiers comportent des <strong className="text-text-primary">risques de perte en capital</strong>. 
                      Les performances passées ne préjugent pas des performances futures.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      MarketGPS <strong className="text-text-primary">ne peut être tenu responsable</strong> des 
                      pertes financières résultant de l&apos;utilisation des informations fournies sur la plateforme.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Vous devez <strong className="text-text-primary">effectuer vos propres recherches</strong> et, 
                      si nécessaire, consulter un professionnel financier agréé avant de prendre toute décision d&apos;investissement.
                    </span>
                  </li>
                </ul>
              </div>
            </GlassCard>
          </motion.div>

          {/* Clause 2 - Market Data */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Database className="w-5 h-5" />} 
                number="2" 
                title="Données de marché" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Les données financières affichées sur MarketGPS proviennent de fournisseurs tiers 
                  réputés (EODHD, Yahoo Finance, etc.). Nous nous efforçons de fournir des données 
                  de qualité institutionnelle, cependant :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Nous <strong className="text-text-primary">ne garantissons pas l&apos;absence d&apos;erreurs</strong> dans 
                      les données, les cours, les volumes ou les indicateurs financiers.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Les données peuvent subir des <strong className="text-text-primary">délais de diffusion</strong> (généralement 
                      15 minutes à 24 heures selon les marchés et les sources).
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Les scores et indicateurs propriétaires sont le résultat de nos algorithmes quantitatifs. 
                      Bien que nous visions l&apos;excellence (vision Jim Simons), ils ne constituent pas une garantie de résultats.
                    </span>
                  </li>
                </ul>
              </div>
            </GlassCard>
          </motion.div>

          {/* Clause 3 - Subscriptions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<CreditCard className="w-5 h-5" />} 
                number="3" 
                title="Abonnements et facturation" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  L&apos;accès aux fonctionnalités premium de MarketGPS nécessite un abonnement payant.
                </p>
                <h4 className="text-text-primary font-semibold mt-6 mb-3">3.1 Modalités de paiement</h4>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Abonnement mensuel</strong> : Facturé chaque mois à date anniversaire.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Abonnement annuel</strong> : Facturé en une fois pour 12 mois (économie de 2 mois).
                    </span>
                  </li>
                </ul>
                
                <h4 className="text-text-primary font-semibold mt-6 mb-3">3.2 Résiliation</h4>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      L&apos;abonnement est <strong className="text-text-primary">résiliable à tout moment</strong> depuis 
                      l&apos;espace &quot;Mon Compte&quot; &gt; &quot;Abonnement&quot;.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      La résiliation prend effet à la fin de la période déjà payée. Aucun remboursement prorata n&apos;est effectué.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      Après résiliation, l&apos;accès aux fonctionnalités premium est maintenu jusqu&apos;à la fin de la période en cours.
                    </span>
                  </li>
                </ul>

                <h4 className="text-text-primary font-semibold mt-6 mb-3">3.3 Droit de rétractation</h4>
                <p className="text-slate-300">
                  Conformément à l&apos;article L221-28 du Code de la consommation, le droit de rétractation 
                  ne s&apos;applique pas aux contenus numériques dont l&apos;exécution a commencé avec l&apos;accord 
                  préalable du consommateur.
                </p>
              </div>
            </GlassCard>
          </motion.div>

          {/* Clause 4 - Intellectual Property */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Briefcase className="w-5 h-5" />} 
                number="4" 
                title="Propriété intellectuelle" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  L&apos;ensemble des éléments constituant la plateforme MarketGPS sont protégés par les 
                  lois relatives à la propriété intellectuelle :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Algorithmes de Scoring</strong> — 
                      La méthodologie de calcul des scores (ScoringModel, PoolState, Gating Engine) 
                      est propriétaire et confidentielle.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Interface graphique</strong> — 
                      Le design, les graphiques, les icônes et l&apos;interface utilisateur sont protégés.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Marque MarketGPS</strong> — 
                      Le nom, le logo et l&apos;identité visuelle sont des marques déposées.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      <strong className="text-text-primary">Contenus éditoriaux</strong> — 
                      Les textes, analyses et documentations sont la propriété exclusive de l&apos;éditeur.
                    </span>
                  </li>
                </ul>
                <p className="text-slate-300 mt-4">
                  Toute reproduction, représentation, modification ou exploitation non autorisée est interdite 
                  et pourra donner lieu à des poursuites judiciaires.
                </p>
              </div>
            </GlassCard>
          </motion.div>

          {/* Clause 5 - Liability */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<Scale className="w-5 h-5" />} 
                number="5" 
                title="Limitation de responsabilité" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed mb-4">
                  Dans les limites autorisées par la loi applicable :
                </p>
                <ul className="space-y-3 text-slate-300">
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      MarketGPS <strong className="text-text-primary">décline toute responsabilité</strong> pour 
                      les dommages directs ou indirects résultant de l&apos;utilisation ou de l&apos;impossibilité d&apos;utiliser 
                      le service.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      La responsabilité totale de MarketGPS ne peut excéder le montant des 
                      abonnements payés au cours des 12 derniers mois.
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-accent mt-1">•</span>
                    <span>
                      MarketGPS ne peut être tenu responsable des interruptions de service dues à 
                      des maintenances programmées ou des circonstances de force majeure.
                    </span>
                  </li>
                </ul>
              </div>
            </GlassCard>
          </motion.div>

          {/* Clause 6 - Applicable Law */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.7 }}
          >
            <GlassCard className="p-8">
              <SectionHeader 
                icon={<FileText className="w-5 h-5" />} 
                number="6" 
                title="Droit applicable et juridiction" 
              />
              <div className="prose prose-invert prose-slate max-w-none">
                <p className="text-slate-300 leading-relaxed">
                  Les présentes Conditions Générales d&apos;Utilisation sont régies par le <strong className="text-text-primary">droit français</strong>. 
                  En cas de litige, et après tentative de résolution amiable, compétence exclusive est 
                  attribuée aux <strong className="text-text-primary">tribunaux de Paris</strong>, France.
                </p>
              </div>
            </GlassCard>
          </motion.div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-12 text-center"
        >
          <p className="text-text-muted mb-4">
            Des questions sur nos conditions d&apos;utilisation ?
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/contact">
              <Button variant="outline">
                Nous contacter
              </Button>
            </Link>
            <Link href="/legal/privacy">
              <Button variant="ghost">
                Politique de confidentialité
              </Button>
            </Link>
          </div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="relative py-8 px-6 border-t border-glass-border mt-16">
        <div className="max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-text-muted">
            © 2024 MarketGPS. Tous droits réservés.
          </p>
          <div className="flex gap-6 text-sm text-text-muted">
            <Link href="/legal/privacy" className="hover:text-text-primary transition-colors">
              Confidentialité
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
        <span className="text-xs text-text-muted uppercase tracking-wider">Clause {number}</span>
        <h2 className="text-xl font-semibold text-text-primary">{title}</h2>
      </div>
    </div>
  );
}
