'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// STRATEGIES LAYOUT
// Uses the shared AppShell for consistent navigation across devices
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function StrategiesLayout({ children }: LayoutProps) {
  return <AppShell>{children}</AppShell>;
}
