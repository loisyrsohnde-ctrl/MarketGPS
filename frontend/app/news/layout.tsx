'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// NEWS LAYOUT
// Uses the shared AppShell for consistent navigation across devices
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function NewsLayout({ children }: LayoutProps) {
  return <AppShell>{children}</AppShell>;
}
