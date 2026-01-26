'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { SubscriptionRequired } from '@/components/subscription/SubscriptionGate';

// ═══════════════════════════════════════════════════════════════════════════
// PAYWALL COMPONENT
// Wraps content and shows paywall if user doesn't have active subscription
// ═══════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.marketgps.online';

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

  useEffect(() => {
    const fetchSubscription = async () => {
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
  }, [session, authLoading]);

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
