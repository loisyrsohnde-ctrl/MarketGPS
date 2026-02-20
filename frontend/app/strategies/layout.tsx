'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// STRATEGIES LAYOUT
// Uses the shared AppShell with guest access enabled
// Guests can browse strategy templates but not create/backtest
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function StrategiesLayout({ children }: LayoutProps) {
  return <AppShell allowGuest={true}>{children}</AppShell>;
}
