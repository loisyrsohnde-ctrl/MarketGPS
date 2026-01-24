'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD LAYOUT
// Authenticated layout with responsive shell (sidebar/topbar on desktop,
// compact topbar + bottom tabs on mobile)
// ═══════════════════════════════════════════════════════════════════════════

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return <AppShell>{children}</AppShell>;
}
