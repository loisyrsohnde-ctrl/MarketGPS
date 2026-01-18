'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { GlassCard } from '@/components/ui/glass-card';
import { signIn } from '@/lib/supabase';
import { Mail, Lock, ArrowLeft, AlertCircle } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// LOGIN PAGE
// ═══════════════════════════════════════════════════════════════════════════

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await signIn(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Back button */}
      <div className="p-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour
        </Link>
      </div>

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center p-6">
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

          {/* Form card */}
          <GlassCard padding="lg">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-text-primary mb-2">
                Bon retour !
              </h1>
              <p className="text-text-secondary">
                Connectez-vous à votre compte
              </p>
            </div>

            {/* Error message */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 rounded-xl bg-score-red/10 border border-score-red/30 flex items-center gap-3"
              >
                <AlertCircle className="w-5 h-5 text-score-red flex-shrink-0" />
                <p className="text-sm text-score-red">{error}</p>
              </motion.div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-text-secondary">
                  Adresse email
                </label>
                <Input
                  type="email"
                  placeholder="vous@exemple.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  leftIcon={<Mail className="w-5 h-5" />}
                  required
                  autoComplete="email"
                />
              </div>

              {/* Password */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-text-secondary">
                    Mot de passe
                  </label>
                  <Link
                    href="/reset-password"
                    className="text-sm text-accent hover:text-accent-light transition-colors"
                  >
                    Oublié ?
                  </Link>
                </div>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  leftIcon={<Lock className="w-5 h-5" />}
                  required
                  autoComplete="current-password"
                />
              </div>

              {/* Submit */}
              <Button
                type="submit"
                className="w-full"
                size="lg"
                loading={loading}
              >
                Se connecter
              </Button>
            </form>

          </GlassCard>

          {/* Sign up link */}
          <p className="mt-6 text-center text-text-secondary">
            Pas encore de compte ?{' '}
            <Link
              href="/signup"
              className="text-accent hover:text-accent-light font-medium transition-colors"
            >
              Créer un compte
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="p-6 text-center">
        <p className="text-xs text-text-dim">
          © 2024 MarketGPS. Plateforme d&apos;analyse quantitative.
        </p>
      </footer>
    </div>
  );
}
