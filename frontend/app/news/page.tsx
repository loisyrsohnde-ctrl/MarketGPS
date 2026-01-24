'use client';

import { Newspaper, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

// ═══════════════════════════════════════════════════════════════════════════
// NEWS PAGE
// Coming soon placeholder - will be replaced with full news feed
// ═══════════════════════════════════════════════════════════════════════════

export default function NewsPage() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
      {/* Icon */}
      <div className="relative mb-6">
        <div
          className={cn(
            'w-20 h-20 rounded-2xl',
            'bg-gradient-to-br from-accent/20 to-accent/5',
            'border border-accent/30',
            'flex items-center justify-center',
            'shadow-glow-sm'
          )}
        >
          <Newspaper className="w-10 h-10 text-accent" />
        </div>
        <div className="absolute -top-2 -right-2">
          <Sparkles className="w-6 h-6 text-score-yellow animate-pulse" />
        </div>
      </div>

      {/* Title */}
      <h1 className="text-2xl md:text-3xl font-bold text-text-primary mb-3">
        News Afrique Fintech
      </h1>

      {/* Subtitle */}
      <p className="text-text-secondary max-w-md mb-6">
        Actualités startups et fintech africaines, traduites et résumées en français.
        Bientôt disponible.
      </p>

      {/* Coming soon badge */}
      <div
        className={cn(
          'inline-flex items-center gap-2 px-4 py-2 rounded-full',
          'bg-accent/10 border border-accent/30',
          'text-accent text-sm font-medium'
        )}
      >
        <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
        Bientôt disponible
      </div>

      {/* Features preview */}
      <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
        {[
          { title: 'Sources vérifiées', desc: '100+ sources Afrique' },
          { title: 'Résumés FR', desc: 'TL;DR en 3 points' },
          { title: 'Partage facile', desc: 'WhatsApp, Twitter...' },
        ].map((feature) => (
          <div
            key={feature.title}
            className={cn(
              'p-4 rounded-xl',
              'bg-surface border border-glass-border',
              'text-left'
            )}
          >
            <p className="text-sm font-medium text-text-primary">
              {feature.title}
            </p>
            <p className="text-xs text-text-muted mt-1">{feature.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
