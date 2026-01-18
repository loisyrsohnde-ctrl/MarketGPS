'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import { ScoreGauge } from '@/components/charts/score-gauge';
import {
  ArrowRight,
  ChevronRight,
  Check,
  FileText,
  RefreshCw,
  Target,
  Shield,
  TrendingUp,
  BarChart3,
  Globe2,
  Sparkles,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// LANDING PAGE - MARKETGPS PREMIUM
// ═══════════════════════════════════════════════════════════════════════════

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-primary overflow-hidden relative">
      {/* Global Background Image - World Map */}
      <div 
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          backgroundImage: 'url(/images/world-map-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center top',
          backgroundRepeat: 'no-repeat',
          backgroundAttachment: 'fixed',
          opacity: 0.6,
        }}
      />
      {/* Gradient overlay for readability */}
      <div className="fixed inset-0 bg-gradient-to-b from-bg-primary/40 via-bg-primary/60 to-bg-primary pointer-events-none z-0" />
      {/* ─────────────────────────────────────────────────────────────────
         NAVBAR
         ───────────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-bg-primary/80 backdrop-blur-xl border-b border-glass-border">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
              <span className="text-white font-bold text-sm">◉</span>
            </div>
            <span className="text-lg font-semibold">
              Market<span className="text-text-muted">GPS</span>
            </span>
          </Link>

          {/* Nav links */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Produit
            </Link>
            <Link href="#markets" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Marchés
            </Link>
            <Link href="#pricing" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Tarifs
            </Link>
            <Link href="#security" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Sécurité
            </Link>
            <Link href="#support" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
              Support
            </Link>
          </div>

          {/* Auth buttons */}
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="outline" size="sm">Se connecter</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm">Créer un compte</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* ─────────────────────────────────────────────────────────────────
         HERO SECTION
         ───────────────────────────────────────────────────────────────── */}
      <section className="relative pt-32 pb-20 px-6 z-10">
        {/* Background chart effect */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.15 }}
            transition={{ duration: 2 }}
            className="absolute bottom-0 left-0 right-0 h-[60%]"
            style={{
              background: `linear-gradient(180deg, transparent 0%, rgba(25, 211, 140, 0.05) 50%, rgba(25, 211, 140, 0.1) 100%)`,
            }}
          />
          {/* Animated chart lines */}
          <svg className="absolute bottom-0 left-0 right-0 h-[400px] w-full opacity-20" preserveAspectRatio="none">
            <motion.path
              d="M0,350 Q200,300 400,320 T800,280 T1200,300 T1600,250"
              fill="none"
              stroke="url(#chartGradient)"
              strokeWidth="2"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 3, ease: "easeInOut" }}
            />
            <motion.path
              d="M0,380 Q300,340 600,360 T1000,320 T1400,340 T1800,290"
              fill="none"
              stroke="url(#chartGradient)"
              strokeWidth="1.5"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 0.6 }}
              transition={{ duration: 3.5, ease: "easeInOut", delay: 0.3 }}
            />
            <defs>
              <linearGradient id="chartGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#19D38C" stopOpacity="0" />
                <stop offset="50%" stopColor="#19D38C" stopOpacity="1" />
                <stop offset="100%" stopColor="#19D38C" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <div className="max-w-7xl mx-auto relative">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            {/* Left: Text */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h1 className="text-4xl md:text-5xl lg:text-[3.5rem] font-bold text-text-primary leading-[1.1] tracking-tight">
                Le score /100 qui rend
                <br />
                les marchés lisibles.
              </h1>
              <p className="mt-6 text-lg text-text-secondary max-w-lg leading-relaxed">
                Des notes claires. Des explications simples. Des données de niveau institutionnel — sans bruit.
              </p>
              <div className="mt-10 flex flex-wrap gap-4">
                <Link href="/signup">
                  <Button size="lg">
                    Commencer gratuitement
                  </Button>
                </Link>
                <Link href="/pricing">
                  <Button variant="outline" size="lg">
                    Voir les offres
                  </Button>
                </Link>
              </div>
            </motion.div>

            {/* Right: Score card preview */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="relative"
            >
              {/* Glow effect behind card */}
              <div className="absolute -inset-4 bg-accent/10 rounded-3xl blur-3xl" />
              
              <GlassCard className="relative p-6 border-glass-border-hover">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-xl font-bold text-text-primary">AAPL</h3>
                    <p className="text-sm text-text-secondary">Apple Inc.</p>
                  </div>
                </div>

                {/* Score Gauge */}
                <div className="flex justify-center mb-6">
                  <ScoreGauge score={87} size="lg" />
                </div>

                {/* Progress bars */}
                <div className="space-y-4">
                  <ScoreBar label="Valeur" value={75} />
                  <ScoreBar label="Momentum" value={92} />
                  <ScoreBar label="Sécurité" value={85} />
                </div>

                {/* Badges */}
                <div className="mt-6 flex flex-wrap gap-2">
                  <Badge icon={<Check className="w-3 h-3" />} variant="success">Données OK</Badge>
                  <Badge icon={<TrendingUp className="w-3 h-3" />} variant="neutral">Liquidité</Badge>
                  <Badge icon={<Shield className="w-3 h-3" />} variant="neutral">Risque FX</Badge>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────────
         MARKETS SECTION
         ───────────────────────────────────────────────────────────────── */}
      <section id="markets" className="relative py-32 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-center"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-10">
              Marchés couverts
            </h2>

            {/* Market Pills */}
            <div className="flex flex-wrap justify-center gap-3 mb-20">
              <MarketPill icon="🇺🇸" label="USA" />
              <MarketPill icon={<Globe2 className="w-4 h-4" />} label="Europe" />
              <MarketPill icon="🌍" label="Afrique" />
              <MarketPill icon={<TrendingUp className="w-4 h-4" />} label="Actions" active />
              <MarketPill icon={<BarChart3 className="w-4 h-4" />} label="ETF" />
              <MarketPill icon="💱" label="Forex" />
              <MarketPill icon="📜" label="Obligations" />
              <MarketPill icon="📊" label="Options" />
              <MarketPill icon="⏳" label="Futures" />
              <MarketPill icon="₿" label="Crypto" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────────
         PRICING SECTION
         ───────────────────────────────────────────────────────────────── */}
      <section id="pricing" className="relative py-24 px-6 bg-bg-secondary/50 z-10">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
              Tarifs
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Monthly Plan */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <PricingCard
                name="Mensuel"
                price="9,99 €"
                period="/mois"
                features={[
                  { icon: <FileText className="w-4 h-4" />, text: "Features essentielles" },
                  { icon: <RefreshCw className="w-4 h-4" />, text: "Features en temps réel" },
                  { icon: <Target className="w-4 h-4" />, text: "Couverture marchés clés" },
                  { icon: <Shield className="w-4 h-4" />, text: "Suivi des actifs" },
                ]}
                ctaText="S'abonner"
                ctaHref="/signup?plan=monthly"
              />
            </motion.div>

            {/* Annual Plan */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <PricingCard
                name="Annuel"
                price="99,99 €"
                period="/an"
                featured
                badge="Meilleure offre"
                features={[
                  { icon: <FileText className="w-4 h-4" />, text: "Features essentielles" },
                  { icon: <RefreshCw className="w-4 h-4" />, text: "Features en temps réel" },
                  { icon: <Target className="w-4 h-4" />, text: "Couverture valeurs de données" },
                  { icon: <Sparkles className="w-4 h-4" />, text: "Risque avancés" },
                  { icon: <Shield className="w-4 h-4" />, text: "Notifications actifs" },
                ]}
                ctaText="S'abonner"
                ctaHref="/signup?plan=yearly"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────────────────────────
         CTA SECTION
         ───────────────────────────────────────────────────────────────── */}
      <section className="relative py-24 px-6 z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto text-center"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-6">
            Prêt à naviguer les marchés ?
          </h2>
          <p className="text-text-secondary text-lg mb-10">
            Rejoignez des milliers d&apos;investisseurs qui utilisent MarketGPS pour prendre des décisions éclairées.
          </p>
          <Link href="/signup">
            <Button size="xl" rightIcon={<ArrowRight className="w-5 h-5" />}>
              Créer mon compte gratuit
            </Button>
          </Link>
        </motion.div>
      </section>

      {/* ─────────────────────────────────────────────────────────────────
         FOOTER
         ───────────────────────────────────────────────────────────────── */}
      <footer className="relative py-12 px-6 border-t border-glass-border bg-bg-secondary/30 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                <span className="text-white font-bold text-xs">◉</span>
              </div>
              <span className="font-semibold">Market<span className="text-text-muted">GPS</span></span>
            </div>

            <div className="flex gap-8 text-sm text-text-muted">
              <Link href="/privacy" className="hover:text-text-primary transition-colors">
                Confidentialité
              </Link>
              <Link href="/terms" className="hover:text-text-primary transition-colors">
                CGU
              </Link>
              <Link href="/contact" className="hover:text-text-primary transition-colors">
                Contact
              </Link>
            </div>

            <p className="text-xs text-text-dim">
              © 2024 MarketGPS. Plateforme d&apos;analyse quantitative.
            </p>
          </div>

          <p className="mt-8 text-center text-xs text-text-dim">
            ⚠️ Capital à risque. Les performances passées ne garantissent pas le futur.
          </p>
        </div>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPER COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-4">
      <span className="w-24 text-sm text-text-secondary">{label}</span>
      <div className="flex-1 h-2 bg-glass-border rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full bg-accent"
          initial={{ width: 0 }}
          whileInView={{ width: `${value}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
        />
      </div>
      <span className="w-8 text-right text-sm font-semibold text-accent">
        {value}
      </span>
    </div>
  );
}

function Badge({ 
  children, 
  icon, 
  variant = 'neutral' 
}: { 
  children: React.ReactNode; 
  icon?: React.ReactNode;
  variant?: 'success' | 'neutral';
}) {
  const bgClass = variant === 'success' 
    ? 'bg-accent/10 border-accent/20' 
    : 'bg-surface border-glass-border';
  const textClass = variant === 'success' ? 'text-accent' : 'text-text-secondary';

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${bgClass} ${textClass}`}>
      {icon}
      {children}
    </span>
  );
}

function MarketPill({ 
  icon, 
  label, 
  active = false 
}: { 
  icon: React.ReactNode | string; 
  label: string; 
  active?: boolean;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      className={`
        inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-medium
        border transition-all duration-200
        ${active 
          ? 'bg-accent/15 border-accent/30 text-accent' 
          : 'bg-surface/80 border-glass-border text-text-secondary hover:border-glass-border-hover hover:text-text-primary'
        }
      `}
    >
      <span className="text-base">{typeof icon === 'string' ? icon : icon}</span>
      {label}
    </motion.button>
  );
}

function PricingCard({
  name,
  price,
  period,
  features,
  ctaText,
  ctaHref,
  featured = false,
  badge,
}: {
  name: string;
  price: string;
  period: string;
  features: { icon: React.ReactNode; text: string }[];
  ctaText: string;
  ctaHref: string;
  featured?: boolean;
  badge?: string;
}) {
  return (
    <GlassCard
      className={`relative h-full ${featured ? 'border-accent/40 bg-accent/5' : ''}`}
      padding="lg"
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-accent text-bg-primary text-xs font-semibold">
          {badge}
        </div>
      )}
      
      <div className="text-center mb-8 pt-2">
        <h3 className="text-lg font-medium text-text-secondary mb-3">{name}</h3>
        <p className="text-4xl font-bold text-text-primary">
          {price}
          <span className="text-base font-normal text-text-muted">{period}</span>
        </p>
      </div>

      <Link href={ctaHref} className="block mb-8">
        <Button
          variant={featured ? 'primary' : 'outline'}
          className="w-full"
          size="lg"
        >
          {ctaText}
        </Button>
      </Link>

      <ul className="space-y-4">
        {features.map((feature, i) => (
          <li key={i} className="flex items-center gap-3 text-sm text-text-secondary">
            <span className="text-text-muted">{feature.icon}</span>
            {feature.text}
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}

