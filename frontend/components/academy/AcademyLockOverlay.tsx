'use client';

import React from 'react';
import { Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AcademyLockOverlayProps {
  isLocked: boolean;
  message?: string;
}

export function AcademyLockOverlay({
  isLocked,
  message = 'Terminez la leçon précédente pour débloquer',
}: AcademyLockOverlayProps) {
  if (!isLocked) return null;

  return (
    <div
      className={cn(
        'absolute inset-0 flex flex-col items-center justify-center',
        'bg-black/40 backdrop-blur-md rounded-lg',
        'border border-glass-border z-40'
      )}
    >
      <Lock className="w-12 h-12 text-white/60 mb-4" />
      <p className="text-center text-text-primary text-sm px-4">{message}</p>
    </div>
  );
}
