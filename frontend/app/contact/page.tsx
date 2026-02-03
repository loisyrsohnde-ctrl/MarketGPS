'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { GlassCard } from '@/components/ui/glass-card';
import {
  ArrowLeft,
  Mail,
  MapPin,
  Clock,
  Send,
  CheckCircle2,
  Loader2,
  MessageSquare,
  CreditCard,
  Handshake,
  HelpCircle,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// CONTACT PAGE - MARKETGPS
// ═══════════════════════════════════════════════════════════════════════════

const SUBJECT_OPTIONS = [
  { value: 'support', label: 'Support Technique', icon: HelpCircle },
  { value: 'billing', label: 'Facturation', icon: CreditCard },
  { value: 'partnership', label: 'Partenariat', icon: Handshake },
  { value: 'feedback', label: 'Suggestion / Feedback', icon: MessageSquare },
];

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    setIsSubmitting(false);
    setIsSubmitted(true);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-accent/5 via-transparent to-transparent" />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-bg-primary/80 backdrop-blur-xl border-b border-glass-border">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
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
              Retour à l&apos;accueil
            </Button>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h1 className="text-4xl md:text-5xl font-bold text-text-primary mb-4">
            Contactez-nous
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Une question, un problème technique ou une opportunité de partenariat ? 
            Notre équipe est là pour vous répondre.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-5 gap-12">
          {/* Left: Contact Info */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-2 space-y-8"
          >
            <GlassCard className="p-6">
              <h2 className="text-xl font-semibold text-text-primary mb-6">
                Informations de contact
              </h2>
              
              <div className="space-y-6">
                <ContactInfo
                  icon={<Mail className="w-5 h-5" />}
                  label="Email"
                  value="hello@marketgps.online"
                  href="mailto:hello@marketgps.online"
                />
                <ContactInfo
                  icon={<MapPin className="w-5 h-5" />}
                  label="Adresse"
                  value="MarketGPS HQ, Paris, France"
                />
                <ContactInfo
                  icon={<Clock className="w-5 h-5" />}
                  label="Support technique"
                  value="Lun-Ven : 9h-18h (CET)"
                />
              </div>
            </GlassCard>

            <GlassCard className="p-6 bg-accent/5 border-accent/20">
              <h3 className="text-lg font-semibold text-text-primary mb-3">
                ⚡ Réponse rapide
              </h3>
              <p className="text-sm text-text-secondary">
                Nous nous engageons à répondre à toutes les demandes dans un délai 
                de <span className="text-accent font-medium">24-48 heures ouvrées</span>.
              </p>
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-3">
                📧 Emails spécialisés
              </h3>
              <ul className="space-y-3 text-sm">
                <li className="flex items-center gap-3">
                  <span className="text-text-muted">Support :</span>
                  <a href="mailto:support@marketgps.online" className="text-accent hover:underline">
                    support@marketgps.online
                  </a>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-text-muted">Données personnelles :</span>
                  <a href="mailto:dpo@marketgps.online" className="text-accent hover:underline">
                    dpo@marketgps.online
                  </a>
                </li>
                <li className="flex items-center gap-3">
                  <span className="text-text-muted">Partenariats :</span>
                  <a href="mailto:partners@marketgps.online" className="text-accent hover:underline">
                    partners@marketgps.online
                  </a>
                </li>
              </ul>
            </GlassCard>
          </motion.div>

          {/* Right: Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-3"
          >
            <GlassCard className="p-8">
              {isSubmitted ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-12"
                >
                  <div className="w-16 h-16 rounded-full bg-accent/20 flex items-center justify-center mx-auto mb-6">
                    <CheckCircle2 className="w-8 h-8 text-accent" />
                  </div>
                  <h3 className="text-2xl font-bold text-text-primary mb-3">
                    Message envoyé !
                  </h3>
                  <p className="text-text-secondary mb-8">
                    Merci de nous avoir contacté. Nous vous répondrons dans les plus brefs délais.
                  </p>
                  <Button
                    onClick={() => {
                      setIsSubmitted(false);
                      setFormData({ name: '', email: '', subject: '', message: '' });
                    }}
                    variant="outline"
                  >
                    Envoyer un autre message
                  </Button>
                </motion.div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <h2 className="text-xl font-semibold text-text-primary mb-2">
                    Envoyez-nous un message
                  </h2>
                  <p className="text-sm text-text-muted mb-6">
                    Tous les champs marqués d&apos;un * sont obligatoires.
                  </p>

                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <label htmlFor="contact-name" className="block text-sm font-medium text-text-secondary mb-2">
                        Nom complet <span className="text-score-red" aria-label="requis">*</span>
                      </label>
                      <input
                        type="text"
                        id="contact-name"
                        name="name"
                        required
                        aria-required="true"
                        value={formData.name}
                        onChange={handleChange}
                        className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim transition-colors"
                        placeholder="John Doe"
                      />
                    </div>

                    <div>
                      <label htmlFor="contact-email" className="block text-sm font-medium text-text-secondary mb-2">
                        Email <span className="text-score-red" aria-label="requis">*</span>
                      </label>
                      <input
                        type="email"
                        id="contact-email"
                        name="email"
                        required
                        aria-required="true"
                        value={formData.email}
                        onChange={handleChange}
                        className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim transition-colors"
                        placeholder="john@example.com"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="contact-subject" className="block text-sm font-medium text-text-secondary mb-2">
                      Sujet <span className="text-score-red" aria-label="requis">*</span>
                    </label>
                    <select
                      id="contact-subject"
                      name="subject"
                      required
                      aria-required="true"
                      value={formData.subject}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim transition-colors appearance-none cursor-pointer"
                    >
                      <option value="" disabled>Sélectionnez un sujet</option>
                      {SUBJECT_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="contact-message" className="block text-sm font-medium text-text-secondary mb-2">
                      Message <span className="text-score-red" aria-label="requis">*</span>
                    </label>
                    <textarea
                      id="contact-message"
                      name="message"
                      required
                      aria-required="true"
                      rows={6}
                      value={formData.message}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-surface border border-glass-border rounded-xl text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-dim transition-colors resize-none"
                      placeholder="Décrivez votre demande en détail..."
                    />
                  </div>

                  <Button
                    type="submit"
                    size="lg"
                    className="w-full"
                    disabled={isSubmitting}
                    rightIcon={isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  >
                    {isSubmitting ? 'Envoi en cours...' : 'Envoyer le message'}
                  </Button>

                  <p className="text-xs text-text-dim text-center">
                    En soumettant ce formulaire, vous acceptez notre{' '}
                    <Link href="/legal/privacy" className="text-accent hover:underline">
                      Politique de Confidentialité
                    </Link>.
                  </p>
                </form>
              )}
            </GlassCard>
          </motion.div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative py-8 px-6 border-t border-glass-border mt-16">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-text-muted">
            © 2024 MarketGPS. Tous droits réservés.
          </p>
          <nav className="flex gap-6 text-sm text-text-muted">
            <Link href="/legal/privacy" className="hover:text-text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-accent-dim rounded px-2 py-1">
              Confidentialité
            </Link>
            <Link href="/legal/terms" className="hover:text-text-primary transition-colors focus:outline-none focus:ring-2 focus:ring-accent-dim rounded px-2 py-1">
              CGU
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// HELPER COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function ContactInfo({
  icon,
  label,
  value,
  href,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  href?: string;
}) {
  const Content = (
    <div className="flex items-start gap-4">
      <div className="p-2.5 rounded-lg bg-accent/10 text-accent">
        {icon}
      </div>
      <div>
        <p className="text-sm text-text-muted mb-1">{label}</p>
        <p className={`text-text-primary font-medium ${href ? 'hover:text-accent transition-colors' : ''}`}>
          {value}
        </p>
      </div>
    </div>
  );

  return href ? <a href={href}>{Content}</a> : Content;
}
