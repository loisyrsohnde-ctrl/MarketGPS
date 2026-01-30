'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { HomePulse } from '@/components/wealth';
import {
  getGeoContext,
  getOpportunitiesSummary,
  getPulseSummary,
} from '@/lib/api-wealth';
import type {
  GeoContext,
  OpportunitySummary,
  PulseSummary,
} from '@/types/wealth-agent';

export default function PulsePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [geoContext, setGeoContext] = useState<GeoContext | undefined>();
  const [opportunitySummary, setOpportunitySummary] = useState<OpportunitySummary | undefined>();
  const [pulseSummary, setPulseSummary] = useState<PulseSummary | undefined>();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch all data in parallel
        const [geoData, oppData, pulseData] = await Promise.all([
          getGeoContext().catch(() => null),
          getOpportunitiesSummary(['FR', 'BE']).catch(() => null),
          getPulseSummary(['FR', 'BE']).catch(() => null),
        ]);

        if (geoData) setGeoContext(geoData);
        if (oppData) setOpportunitySummary(oppData);
        if (pulseData) setPulseSummary(pulseData);

      } catch (err) {
        console.error('Failed to fetch pulse data:', err);
        setError('Impossible de charger les données. Vérifiez votre connexion.');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const handleNavigateOpportunities = () => {
    router.push('/dashboard/wealth/opportunities');
  };

  const handleNavigateAnalyze = () => {
    router.push('/dashboard/wealth/analyze');
  };

  const handleNavigatePulse = () => {
    router.push('/dashboard/wealth/news');
  };

  const handleSelectOpportunity = (id: string) => {
    router.push(`/dashboard/wealth/opportunities/${id}`);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <HomePulse
      geoContext={geoContext}
      opportunitySummary={opportunitySummary}
      pulseSummary={pulseSummary}
      onNavigateOpportunities={handleNavigateOpportunities}
      onNavigateAnalyze={handleNavigateAnalyze}
      onNavigatePulse={handleNavigatePulse}
      onSelectOpportunity={handleSelectOpportunity}
      isLoading={loading}
    />
  );
}
