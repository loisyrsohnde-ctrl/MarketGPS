'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { WealthIntelligence } from '@/components/wealth';
import { getWealthSummary } from '@/lib/api-real-estate';
import type { RealEstatePortfolio, AIAuditResult } from '@/types/wealth';

export default function WealthPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [realEstateData, setRealEstateData] = useState<RealEstatePortfolio | undefined>();
  const [liquidAssets, setLiquidAssets] = useState(450000);
  const [aiAlerts, setAiAlerts] = useState<AIAuditResult[]>([]);
  
  useEffect(() => {
    async function fetchData() {
      try {
        // TODO: Fetch real portfolio data from user profile
        // For now, using sample data
        
        // Sample real estate portfolio
        const sampleProperties = [
          {
            purchase_price: 350000,
            land_ratio: 0.20,
            annual_rent: 24000,
            annual_charges: 4800,
            annual_interests: 8400,
            state_province: 'FR',
          },
          {
            purchase_price: 445000,
            land_ratio: 0.15,
            annual_rent: 32000,
            annual_charges: 6400,
            annual_interests: 10600,
            state_province: 'CA',
          },
        ];
        
        const portfolioData = await getWealthSummary(
          sampleProperties,
          ['FR', 'US'],
          0.30
        );
        
        setRealEstateData(portfolioData);
        
        // Sample liquid assets (would come from existing MarketGPS data)
        setLiquidAssets(450000);
        
        // Sample AI alerts
        setAiAlerts([
          {
            id: '1',
            property_id: 'prop-1',
            audit_type: 'document',
            severity: 'warning',
            title: 'Optimisation Fiscale',
            description: 'L\'amortissement LMNP atteindra son point optimal au T3. Envisagez une stratégie de réinvestissement.',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
          },
          {
            id: '2',
            property_id: 'prop-2',
            audit_type: 'legal',
            severity: 'info',
            title: 'Alerte Marché',
            description: 'Les taux de capitalisation en Ontario ont baissé de 15 points. Votre portefeuille surperforme le benchmark.',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
          },
          {
            id: '3',
            property_id: '',
            audit_type: 'vision',
            severity: 'critical',
            title: 'Audit Énergétique',
            description: 'Le DPE du bien parisien expire dans 6 mois. Planifiez le renouvellement.',
            timestamp: new Date(Date.now() - 172800000).toISOString(),
          },
        ]);
        
      } catch (error) {
        console.error('Failed to fetch wealth data:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);
  
  const handleAnalyzeProperty = () => {
    router.push('/dashboard/wealth/analyze');
  };
  
  const handleViewReports = () => {
    router.push('/dashboard/wealth/reports');
  };
  
  // Historical net worth data (would come from backend)
  const netWorthHistory = [
    { name: 'Jan', value: 1100000 },
    { name: 'Feb', value: 1120000 },
    { name: 'Mar', value: 1105000 },
    { name: 'Apr', value: 1150000 },
    { name: 'May', value: 1180000 },
    { name: 'Jun', value: liquidAssets + (realEstateData?.total_real_estate_value || 795000) },
  ];
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Chargement des données patrimoniales...</div>
      </div>
    );
  }
  
  return (
    <WealthIntelligence
      liquidAssets={liquidAssets}
      liquidChange24h={0.023}
      realEstatePortfolio={realEstateData}
      overallRiskScore={18}
      netWorthHistory={netWorthHistory}
      aiAlerts={aiAlerts}
      onAnalyzeProperty={handleAnalyzeProperty}
      onViewReports={handleViewReports}
    />
  );
}
