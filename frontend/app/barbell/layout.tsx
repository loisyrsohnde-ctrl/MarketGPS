'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// BARBELL LAYOUT
// Uses the shared AppShell for consistent navigation across devices
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function BarbellLayout({ children }: LayoutProps) {
  return <AppShell>{children}</AppShell>;
}
