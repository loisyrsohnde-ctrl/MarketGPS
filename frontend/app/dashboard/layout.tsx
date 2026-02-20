'use client';

import { AppShell } from '@/components/layout/AppShell';

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD LAYOUT
// Authenticated layout with guest preview mode
// Guests can view the dashboard with limited data
// ═══════════════════════════════════════════════════════════════════════════

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return <AppShell allowGuest={true}>{children}</AppShell>;
}
