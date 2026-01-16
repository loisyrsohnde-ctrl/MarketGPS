'use client';

import { forwardRef, type HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { motion, type HTMLMotionProps } from 'framer-motion';

// ═══════════════════════════════════════════════════════════════════════════
// GLASS CARD COMPONENT
// Premium glassmorphism card with optional hover effects
// ═══════════════════════════════════════════════════════════════════════════

interface GlassCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'accent';
  hover?: boolean;
  glow?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = 'default', hover = true, glow = false, padding = 'md', children, ...props }, ref) => {
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const variantClasses = {
      default: 'bg-surface border-glass-border',
      elevated: 'bg-surface-hover border-glass-border-hover',
      accent: 'bg-surface border-glass-border-active',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'relative rounded-2xl border backdrop-blur-glass transition-all duration-200',
          variantClasses[variant],
          paddingClasses[padding],
          hover && 'hover:bg-surface-hover hover:border-glass-border-hover',
          glow && 'shadow-glow',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassCard.displayName = 'GlassCard';

// ═══════════════════════════════════════════════════════════════════════════
// ANIMATED GLASS CARD (with Framer Motion)
// ═══════════════════════════════════════════════════════════════════════════

interface AnimatedGlassCardProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  variant?: 'default' | 'elevated' | 'accent';
  hover?: boolean;
  glow?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const AnimatedGlassCard = forwardRef<HTMLDivElement, AnimatedGlassCardProps>(
  ({ className, variant = 'default', hover = true, glow = false, padding = 'md', children, ...props }, ref) => {
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const variantClasses = {
      default: 'bg-surface border-glass-border',
      elevated: 'bg-surface-hover border-glass-border-hover',
      accent: 'bg-surface border-glass-border-active',
    };

    return (
      <motion.div
        ref={ref}
        className={cn(
          'relative rounded-2xl border backdrop-blur-glass',
          variantClasses[variant],
          paddingClasses[padding],
          glow && 'shadow-glow',
          className
        )}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        whileHover={hover ? { 
          scale: 1.01,
          borderColor: 'rgba(255, 255, 255, 0.12)',
        } : undefined}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

AnimatedGlassCard.displayName = 'AnimatedGlassCard';

// ═══════════════════════════════════════════════════════════════════════════
// GLASS CARD WITH ACCENT LINE
// ═══════════════════════════════════════════════════════════════════════════

const GlassCardAccent = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <GlassCard
        ref={ref}
        className={cn('overflow-hidden', className)}
        {...props}
      >
        {/* Top accent line */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent-glow to-transparent" />
        {children}
      </GlassCard>
    );
  }
);

GlassCardAccent.displayName = 'GlassCardAccent';

export { GlassCard, AnimatedGlassCard, GlassCardAccent };
