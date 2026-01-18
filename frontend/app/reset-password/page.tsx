'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { GlassCard } from '@/components/ui/glass-card';
import { resetPassword, updatePassword } from '@/lib/supabase';
import { Mail, Lock, ArrowLeft, AlertCircle, CheckCircle2 } from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// RESET PASSWORD PAGE
// Handles both: request reset (email) + set new password (with token)
// ═══════════════════════════════════════════════════════════════════════════

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg-primary" />}>
      <ResetPasswordContent />
    </Suspense>
  );
}

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const hasToken = searchParams.has('access_token') || searchParams.has('token');

  // If token in URL, show "set new password" form
  // Otherwise, show "request reset" form
  return hasToken ? <SetNewPassword /> : <RequestReset />;
}

// ═══════════════════════════════════════════════════════════════════════════
// REQUEST RESET COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

function RequestReset() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await resetPassword(email);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de l\'envoi');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Back button */}
      <div className="p-6">
        <Link
          href="/login"
          className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour à la connexion
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
            {success ? (
              // Success state
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 rounded-full bg-score-green/15 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle2 className="w-8 h-8 text-score-green" />
                </div>
                <h2 className="text-xl font-bold text-text-primary mb-2">
                  Email envoyé !
                </h2>
                <p className="text-text-secondary mb-6">
                  Un lien de réinitialisation a été envoyé à{' '}
                  <span className="text-accent font-medium">{email}</span>
                </p>
                <p className="text-sm text-text-muted">
                  Vérifiez votre boîte de réception et cliquez sur le lien.
                </p>
                <Link href="/login" className="block mt-8">
                  <Button variant="secondary" className="w-full">
                    Retour à la connexion
                  </Button>
                </Link>
              </motion.div>
            ) : (
              // Form state
              <>
                <div className="text-center mb-8">
                  <h1 className="text-2xl font-bold text-text-primary mb-2">
                    Mot de passe oublié ?
                  </h1>
                  <p className="text-text-secondary">
                    Entrez votre email pour recevoir un lien de réinitialisation
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

                  {/* Submit */}
                  <Button
                    type="submit"
                    className="w-full"
                    size="lg"
                    loading={loading}
                  >
                    Envoyer le lien
                  </Button>
                </form>
              </>
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// SET NEW PASSWORD COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

function SetNewPassword() {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères');
      return;
    }

    if (password !== confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    setLoading(true);

    try {
      await updatePassword(password);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la mise à jour');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
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
            {success ? (
              // Success state
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                <div className="w-16 h-16 rounded-full bg-score-green/15 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle2 className="w-8 h-8 text-score-green" />
                </div>
                <h2 className="text-xl font-bold text-text-primary mb-2">
                  Mot de passe mis à jour !
                </h2>
                <p className="text-text-secondary mb-6">
                  Votre mot de passe a été changé avec succès.
                </p>
                <Link href="/login">
                  <Button className="w-full">
                    Se connecter
                  </Button>
                </Link>
              </motion.div>
            ) : (
              // Form state
              <>
                <div className="text-center mb-8">
                  <h1 className="text-2xl font-bold text-text-primary mb-2">
                    Nouveau mot de passe
                  </h1>
                  <p className="text-text-secondary">
                    Choisissez un nouveau mot de passe sécurisé
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
                  {/* Password */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-text-secondary">
                      Nouveau mot de passe
                    </label>
                    <Input
                      type="password"
                      placeholder="Minimum 8 caractères"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      leftIcon={<Lock className="w-5 h-5" />}
                      required
                      autoComplete="new-password"
                    />
                  </div>

                  {/* Confirm Password */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-text-secondary">
                      Confirmer le mot de passe
                    </label>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      leftIcon={<Lock className="w-5 h-5" />}
                      required
                      autoComplete="new-password"
                      error={confirmPassword !== '' && password !== confirmPassword}
                    />
                  </div>

                  {/* Submit */}
                  <Button
                    type="submit"
                    className="w-full"
                    size="lg"
                    loading={loading}
                  >
                    Mettre à jour
                  </Button>
                </form>
              </>
            )}
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
