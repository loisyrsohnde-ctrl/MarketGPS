'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, useEffect, type ReactNode } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { initPostHog } from '@/lib/posthog';

// ═══════════════════════════════════════════════════════════════════════════
// PROVIDERS
// ═══════════════════════════════════════════════════════════════════════════

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            gcTime: 5 * 60 * 1000, // 5 minutes (previously cacheTime)
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  useEffect(() => {
    initPostHog();
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
