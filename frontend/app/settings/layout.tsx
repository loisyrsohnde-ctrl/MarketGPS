'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// SETTINGS LAYOUT
// Uses the shared AppShell for consistent navigation across devices
// ═══════════════════════════════════════════════════════════════════════════

interface LayoutProps {
  children: React.ReactNode;
}

export default function SettingsLayout({ children }: LayoutProps) {
  return <AppShell>{children}</AppShell>;
}
