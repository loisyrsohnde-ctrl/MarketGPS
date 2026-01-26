'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useSubscription } from '@/hooks/useSubscription';

// ═══════════════════════════════════════════════════════════════════════════
// PAYWALL COMPONENT
// Wraps protected content and redirects to choose-plan if no active subscription
// ═══════════════════════════════════════════════════════════════════════════

interface PaywallProps {
  children: React.ReactNode;
  /** If true, allow free users to see content (useful for partial paywalls) */
  allowFree?: boolean;
}

export function Paywall({ children, allowFree = false }: PaywallProps) {
  const router = useRouter();
  const { isActive, isLoading } = useSubscription();

  useEffect(() => {
    // Don't redirect while loading
    if (isLoading) return;

    // Allow access if subscription is active or if free users are allowed
    if (isActive || allowFree) return;

    // Redirect to choose plan page
    router.push('/billing/choose-plan');
  }, [isActive, isLoading, allowFree, router]);

  // Show loading while checking subscription
  if (isLoading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-accent" />
      </div>
    );
  }

  // Allow access if subscription is active or if free users are allowed
  if (isActive || allowFree) {
    return <>{children}</>;
  }

  // Show nothing while redirecting
  return (
    <div className="min-h-[400px] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-accent" />
    </div>
  );
}

export default Paywall;
