'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// WATCHLIST LAYOUT
// Uses the shared AppShell for consistent navigation across devices
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function WatchlistLayout({ children }: LayoutProps) {
  return <AppShell>{children}</AppShell>;
}
