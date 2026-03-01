import { posthog } from './posthog';

/**
 * Centralized analytics tracking for MarketGPS.
 * All events go through PostHog.
 */
export const track = {
  // --- User lifecycle ---
  signupCompleted: () =>
    posthog.capture('signup_completed'),

  identifyUser: (userId: string, email: string, plan: string) =>
    posthog.identify(userId, { email, plan }),

  // --- Engagement ---
  scoreView: (ticker: string, score: number | null) =>
    posthog.capture('score_viewed', { ticker, score }),

  newsRead: (slug: string, country?: string) =>
    posthog.capture('news_read', { slug, country }),

  aiMessage: (provider: string) =>
    posthog.capture('ai_message_sent', { provider }),

  morningBriefView: () =>
    posthog.capture('morning_brief_viewed'),

  watchlistAdd: (ticker: string) =>
    posthog.capture('watchlist_add', { ticker }),

  // --- Conversion ---
  subscriptionCtaClick: (source: string) =>
    posthog.capture('subscription_cta_clicked', { source }),

  checkoutStarted: (plan: string) =>
    posthog.capture('checkout_started', { plan }),

  academyCtaClick: (pricingTier: string) =>
    posthog.capture('academy_cta_clicked', { pricing_tier: pricingTier }),

  // --- Sharing ---
  shareAction: (type: 'whatsapp' | 'native' | 'clipboard', content: 'asset' | 'news' | 'brief') =>
    posthog.capture('share_action', { type, content }),
};
