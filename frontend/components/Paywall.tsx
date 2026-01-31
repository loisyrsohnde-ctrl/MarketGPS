'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { SubscriptionRequired } from '@/components/subscription/SubscriptionGate';

// ═══════════════════════════════════════════════════════════════════════════
// PAYWALL COMPONENT
// Wraps content and shows paywall if user doesn't have active subscription
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

// Bypass paywall in development mode
const BYPASS_PAYWALL = process.env.NODE_ENV === 'development' || 
  process.env.NEXT_PUBLIC_BYPASS_PAYWALL === 'true';

interface SubscriptionStatus {
  user_id: string;
  plan: string;
  status: string;
  is_active: boolean;
  grace_period_remaining_hours?: number;
}

interface PaywallProps {
  children: React.ReactNode;
}

export function Paywall({ children }: PaywallProps) {
  const { session, isLoading: authLoading, isAuthenticated } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLocalhost, setIsLocalhost] = useState(false);

  // Check if running on localhost (client-side only)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsLocalhost(
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1'
      );
    }
  }, []);

  const shouldBypassPaywall = BYPASS_PAYWALL || isLocalhost;

  useEffect(() => {
    const fetchSubscription = async () => {
      // Skip if bypassing paywall
      if (shouldBypassPaywall) {
        setLoading(false);
        return;
      }

      if (!session?.access_token) {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/billing/me`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setSubscription(data);
        }
      } catch (error) {
        console.error('Error fetching subscription:', error);
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading) {
      if (session?.access_token) {
        fetchSubscription();
      } else {
        setLoading(false);
      }
    }
  }, [session, authLoading, shouldBypassPaywall]);

  // Bypass paywall in development - always show content
  if (shouldBypassPaywall) {
    return <>{children}</>;
  }

  // Show loading skeleton while checking
  if (loading || authLoading) {
    return <>{children}</>;
  }

  // Not logged in - show login prompt
  if (!isAuthenticated) {
    return (
      <div className="py-8">
        <SubscriptionRequired 
          message="Connectez-vous pour accéder à cette fonctionnalité"
          showLogin
        />
      </div>
    );
  }

  // Has active subscription - show content
  if (subscription?.is_active) {
    return <>{children}</>;
  }

  // No active subscription - show paywall
  return (
    <div className="py-8">
      <SubscriptionRequired 
        gracePeriod={subscription?.grace_period_remaining_hours}
      />
    </div>
  );
}

export default Paywall;
