'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// ACADEMY LAYOUT
// Guest-accessible layout for the academy catalog
// Course content requires authentication + subscription
// ═══════════════════════════════════════════════════════════════════════════

export default function AcademyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppShell allowGuest={true} bypassPaywall={true}>
      <div className={cn('academy-layout', 'relative')}>
        {children}
      </div>
    </AppShell>
  );
}
