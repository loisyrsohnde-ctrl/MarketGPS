/**
 * Sharing utilities for MarketGPS.
 * WhatsApp is the primary distribution channel for the African diaspora.
 */

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://marketgps.online';

export function shareViaWhatsApp(text: string, url: string): void {
  window.open(
    `https://wa.me/?text=${encodeURIComponent(text + '\n' + url)}`,
    '_blank'
  );
}

export function shareAssetOnWhatsApp(ticker: string, score: number | null): void {
  const scoreText = score !== null ? `Score ${score}/100` : '';
  const text = `${ticker} ${scoreText} sur MarketGPS`;
  shareViaWhatsApp(text, `${APP_URL}/asset/${ticker}`);
}

export function shareNewsOnWhatsApp(title: string, slug: string): void {
  shareViaWhatsApp(title, `${APP_URL}/news/${slug}`);
}

export function shareBriefOnWhatsApp(): void {
  shareViaWhatsApp(
    'Mon briefing MarketGPS du jour',
    `${APP_URL}/morning-brief`
  );
}
