import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { Providers } from './providers';

// ═══════════════════════════════════════════════════════════════════════════
// FONT
// ═══════════════════════════════════════════════════════════════════════════

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-inter',
  display: 'swap',
});

// ═══════════════════════════════════════════════════════════════════════════
// METADATA
// ═══════════════════════════════════════════════════════════════════════════

export const metadata: Metadata = {
  title: {
    default: 'MarketGPS - Le score /100 qui rend les marchés lisibles',
    template: '%s | MarketGPS',
  },
  description:
    'Analysez et comparez les actifs financiers avec un score unique sur 100. ETF, Actions, FX - Marchés US, Europe et Afrique.',
  keywords: ['finance', 'scoring', 'ETF', 'actions', 'analyse', 'marchés', 'investissement'],
  authors: [{ name: 'MarketGPS' }],
  creator: 'MarketGPS',
  openGraph: {
    type: 'website',
    locale: 'fr_FR',
    url: 'https://marketgps.io',
    title: 'MarketGPS - Le score /100 qui rend les marchés lisibles',
    description: 'Analysez et comparez les actifs financiers avec un score unique sur 100.',
    siteName: 'MarketGPS',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'MarketGPS',
    description: 'Le score /100 qui rend les marchés lisibles',
  },
  robots: {
    index: true,
    follow: true,
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// ROOT LAYOUT
// ═══════════════════════════════════════════════════════════════════════════

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${inter.className} dark`} suppressHydrationWarning>
      <body className="bg-bg-primary text-text-primary antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
