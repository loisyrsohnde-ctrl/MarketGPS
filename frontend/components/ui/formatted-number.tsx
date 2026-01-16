'use client';

import { useEffect, useState } from 'react';

interface FormattedNumberProps {
  value: number | null | undefined;
  locale?: string;
  options?: Intl.NumberFormatOptions;
  fallback?: string;
}

/**
 * Client-side number formatter to avoid hydration mismatches.
 * Formats numbers only on the client side to ensure consistency.
 */
export function FormattedNumber({ 
  value, 
  locale = 'fr-FR', 
  options,
  fallback = '—' 
}: FormattedNumberProps) {
  const [formatted, setFormatted] = useState<string>(fallback);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (value === null || value === undefined) {
      setFormatted(fallback);
      return;
    }

    if (isClient) {
      try {
        const formatter = new Intl.NumberFormat(locale, options);
        setFormatted(formatter.format(value));
      } catch (error) {
        // Fallback to simple string conversion
        setFormatted(value.toString());
      }
    } else {
      // Server-side: use simple format to avoid hydration mismatch
      setFormatted(value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' '));
    }
  }, [value, locale, options, isClient, fallback]);

  // On server, return simple format
  if (!isClient) {
    return <span suppressHydrationWarning>{value?.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ') || fallback}</span>;
  }

  return <span>{formatted}</span>;
}
