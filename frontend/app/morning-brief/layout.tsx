import type { Metadata } from 'next';

// ═══════════════════════════════════════════════════════════════════════════
// MORNING BRIEF LAYOUT
// ═══════════════════════════════════════════════════════════════════════════

export const metadata: Metadata = {
  title: 'Morning Brief Dashboard | MarketGPS',
  description: 'Your personalized daily market briefing with portfolio performance, alerts, opportunities, and news.',
};

export default function MorningBriefLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
