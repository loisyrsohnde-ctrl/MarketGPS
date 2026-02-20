'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { X, UserPlus, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useAccessLevel } from '@/hooks/useAccessLevel';

// ═══════════════════════════════════════════════════════════════════════════
// GUEST CONVERSION BANNER
// Sticky bottom banner for guest users encouraging signup
// Inspired by TradingView's persistent signup banner
// ═══════════════════════════════════════════════════════════════════════════

export function GuestConversionBanner() {
  const { isGuest } = useAccessLevel();
  const [dismissed, setDismissed] = useState(false);

  // Only show for guests, and only if not dismissed
  if (!isGuest || dismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 100, opacity: 0 }}
        transition={{ delay: 3, duration: 0.4 }}
        className="fixed bottom-0 left-0 right-0 z-50 md:left-[240px]"
      >
        <div className="bg-gradient-to-r from-bg-secondary via-bg-primary to-bg-secondary border-t border-accent/30 backdrop-blur-glass">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-4">
            {/* Icon */}
            <div className="hidden sm:flex w-10 h-10 rounded-full bg-accent/10 items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-accent" />
            </div>
            
            {/* Text */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary">
                Vous explorez MarketGPS en mode invité
              </p>
              <p className="text-xs text-text-muted hidden sm:block">
                Créez un compte gratuit pour sauvegarder vos analyses, suivre des actifs et accéder à plus de fonctionnalités.
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 flex-shrink-0">
              <Link href="/signup">
                <Button size="sm" leftIcon={<UserPlus className="w-4 h-4" />}>
                  S'inscrire gratuitement
                </Button>
              </Link>
              <Link href="/login" className="hidden sm:block">
                <Button variant="ghost" size="sm">
                  Connexion
                </Button>
              </Link>
              <button 
                onClick={() => setDismissed(true)}
                className="p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-text-primary transition-colors"
                aria-label="Fermer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

export default GuestConversionBanner;
