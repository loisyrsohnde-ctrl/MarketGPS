/**
 * Safe redirect utilities to prevent open redirect vulnerabilities.
 */

/** Allowed internal redirect paths */
const ALLOWED_REDIRECT_PATHS = [
  '/dashboard',
  '/billing/choose-plan',
  '/settings/billing',
  '/settings',
  '/academy',
  '/news',
  '/strategies',
  '/portfolio',
];

/** Allowed external domains for payment redirects */
const ALLOWED_EXTERNAL_DOMAINS = [
  'checkout.stripe.com',
  'billing.stripe.com',
];

/**
 * Validate an internal redirect path.
 * Returns the path if it's in the allowlist, otherwise returns '/dashboard'.
 */
export function validateRedirectPath(path: string | null | undefined): string {
  if (!path) return '/dashboard';

  // Must start with / (relative path)
  if (!path.startsWith('/')) return '/dashboard';

  // Check against allowlist
  const isAllowed = ALLOWED_REDIRECT_PATHS.some(
    (allowed) => path === allowed || path.startsWith(allowed + '/')
  );

  return isAllowed ? path : '/dashboard';
}

/**
 * Validate an external redirect URL (e.g., from Stripe checkout).
 * Returns the URL if the domain is trusted, otherwise returns null.
 */
export function validateExternalUrl(url: string | null | undefined): string | null {
  if (!url) return null;

  try {
    const parsed = new URL(url);

    // Must be HTTPS
    if (parsed.protocol !== 'https:') return null;

    // Check against allowed domains
    const isAllowed = ALLOWED_EXTERNAL_DOMAINS.some(
      (domain) => parsed.hostname === domain || parsed.hostname.endsWith('.' + domain)
    );

    return isAllowed ? url : null;
  } catch {
    return null;
  }
}
