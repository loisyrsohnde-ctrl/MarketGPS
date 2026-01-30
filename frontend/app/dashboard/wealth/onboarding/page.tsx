'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { OnboardingWizard } from '@/components/wealth';
import { completeOnboarding } from '@/lib/api-wealth';
import type { OnboardingAnswers, OnboardingResult } from '@/types/wealth-agent';

export default function OnboardingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (answers: OnboardingAnswers): Promise<OnboardingResult> => {
    setIsLoading(true);
    try {
      const result = await completeOnboarding(answers);
      return result;
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = (result: OnboardingResult) => {
    // Store the result in local storage for now
    // In production, this would be persisted in the user profile
    localStorage.setItem('marketgps_onboarding_complete', 'true');
    localStorage.setItem('marketgps_investor_profile', JSON.stringify(result.profile));
    
    // Navigate to the main dashboard
    router.push('/dashboard/wealth/pulse');
  };

  return (
    <OnboardingWizard
      onSubmit={handleSubmit}
      onComplete={handleComplete}
      isLoading={isLoading}
    />
  );
}
