'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════
// AUTH CALLBACK PAGE
// Handles Supabase email confirmation redirect
// Supabase redirects here with hash fragments (#access_token=...&refresh_token=...)
// The Supabase client auto-detects tokens and establishes the session
// ═══════════════════════════════════════════════════════════════════════════

export default function AuthCallbackPage() {
  const router = useRouter();
  const [error, setError] = useState(false);

  useEffect(() => {
    // Listen for auth state change (Supabase client detects hash tokens automatically)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          // Session established — redirect to morning brief
          router.push('/morning-brief');
        }
      }
    );

    // Timeout: if no session after 5s, show error
    const timeout = setTimeout(() => {
      setError(true);
    }, 5000);

    return () => {
      subscription.unsubscribe();
      clearTimeout(timeout);
    };
  }, [router]);

  if (error) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-score-red/15 flex items-center justify-center mx-auto mb-6">
            <span className="text-2xl">⚠️</span>
          </div>
          <h1 className="text-xl font-bold text-text-primary mb-2">
            Erreur de connexion
          </h1>
          <p className="text-text-secondary mb-6">
            Le lien de confirmation a expiré ou est invalide. Veuillez vous connecter manuellement.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-accent text-white font-medium hover:bg-accent-dark transition-colors"
          >
            Se connecter
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-6">
      <div className="text-center">
        <div className="w-12 h-12 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-secondary">Connexion en cours...</p>
      </div>
    </div>
  );
}
