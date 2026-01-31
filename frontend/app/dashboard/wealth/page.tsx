'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { WealthIntelligence } from '@/components/wealth';
import { getWealthSummary } from '@/lib/api-real-estate';
import type { RealEstatePortfolio, AIAuditResult } from '@/types/wealth';
import { useHasPortfolio } from '@/hooks/usePortfolio';
import { Upload, PlusCircle, ArrowRight, Wallet, TrendingUp, PieChart, Shield } from 'lucide-react';
import Link from 'next/link';

// ═══════════════════════════════════════════════════════════════════════════════
// ONBOARDING PROMPT - Shown when user has no portfolio data
// ═══════════════════════════════════════════════════════════════════════════════

function PortfolioOnboardingPrompt() {

  return (
    <div className="min-h-screen bg-bg-primary py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center shadow-glow">
            <Wallet className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-text-primary mb-3">
            Bienvenue dans Mon Patrimoine
          </h1>
          <p className="text-lg text-text-secondary max-w-xl mx-auto">
            Synchronisez votre portefeuille pour visualiser vos positions, 
            performances et expositions avec les scores MarketGPS.
          </p>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-surface rounded-2xl border border-glass-border p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-accent/10 flex items-center justify-center">
              <PieChart className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold text-text-primary mb-2">Vue consolidée</h3>
            <p className="text-sm text-text-muted">
              Visualisez l&apos;ensemble de vos positions sur tous vos comptes
            </p>
          </div>

          <div className="bg-surface rounded-2xl border border-glass-border p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-accent/10 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold text-text-primary mb-2">Scores & Analyses</h3>
            <p className="text-sm text-text-muted">
              Chaque position enrichie avec les indicateurs MarketGPS
            </p>
          </div>

          <div className="bg-surface rounded-2xl border border-glass-border p-6 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-xl bg-accent/10 flex items-center justify-center">
              <Shield className="w-6 h-6 text-accent" />
            </div>
            <h3 className="font-semibold text-text-primary mb-2">Lecture seule</h3>
            <p className="text-sm text-text-muted">
              Aucune connexion à vos comptes, pas de trading
            </p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/dashboard/wealth/connect"
            className="inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-accent text-white font-medium hover:bg-accent-dark transition-colors shadow-glow-sm"
          >
            <Upload className="w-5 h-5" />
            Importer un fichier CSV
            <ArrowRight className="w-4 h-4" />
          </Link>

          <Link
            href="/dashboard/wealth/connect/manual"
            className="inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-surface border border-glass-border text-text-primary font-medium hover:bg-surface/80 transition-colors"
          >
            <PlusCircle className="w-5 h-5" />
            Saisir manuellement
          </Link>
        </div>

        {/* Info box */}
        <div className="mt-12 bg-surface/50 rounded-xl border border-glass-border p-4 text-center">
          <p className="text-sm text-text-muted">
            <Shield className="w-4 h-4 inline mr-1" />
            MarketGPS est un outil de recherche et statistiques. 
            Les scores affichés ne constituent pas des conseils d&apos;investissement.
          </p>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

export default function WealthPage() {
  const router = useRouter();
  
  // Check if user has portfolio data
  const { hasData, isChecking } = useHasPortfolio();
  
  const [loading, setLoading] = useState(true);
  const [realEstateData, setRealEstateData] = useState<RealEstatePortfolio | undefined>();
  const [liquidAssets, setLiquidAssets] = useState(0);
  const [aiAlerts, setAiAlerts] = useState<AIAuditResult[]>([]);
  
  useEffect(() => {
    async function fetchData() {
      // Skip if still checking or no data
      if (isChecking || hasData === false) {
        setLoading(false);
        return;
      }
      
      try {
        // Fetch real portfolio data
        const { getPortfolioSummary } = await import('@/lib/api-portfolio');
        const portfolioSummary = await getPortfolioSummary();
        
        // Set liquid assets from real portfolio
        setLiquidAssets(portfolioSummary.total_value || 0);
        
        // Fetch real estate data (if any)
        // For now, keep the real estate logic as-is since that's a different module
        const sampleProperties: Array<{
          purchase_price: number;
          land_ratio: number;
          annual_rent: number;
          annual_charges: number;
          annual_interests: number;
          state_province: string;
        }> = [];
        
        if (sampleProperties.length > 0) {
          const portfolioData = await getWealthSummary(
            sampleProperties,
            ['FR', 'US'],
            0.30
          );
          setRealEstateData(portfolioData);
        }
        
        // Generate alerts based on portfolio data
        const alerts: AIAuditResult[] = [];
        
        // Alert for negative P&L
        if (portfolioSummary.total_pnl < 0) {
          alerts.push({
            id: 'pnl-alert',
            property_id: '',
            audit_type: 'document',
            severity: 'warning',
            title: 'Performance négative',
            description: `Votre portefeuille affiche une moins-value de ${Math.abs(portfolioSummary.total_pnl_percent).toFixed(1)}%. Analysez vos positions les plus impactées.`,
            timestamp: new Date().toISOString(),
          });
        }
        
        // Alert for concentration
        if (portfolioSummary.top_holdings.length > 0) {
          const topHolding = portfolioSummary.top_holdings[0];
          const topWeight = (topHolding.value / portfolioSummary.total_value) * 100;
          if (topWeight > 30) {
            alerts.push({
              id: 'concentration-alert',
              property_id: '',
              audit_type: 'legal',
              severity: 'info',
              title: 'Concentration élevée',
              description: `${topHolding.symbol} représente ${topWeight.toFixed(0)}% de votre portefeuille. Considérez une diversification.`,
              timestamp: new Date().toISOString(),
            });
          }
        }
        
        // Alert for last sync
        if (portfolioSummary.last_sync_at) {
          const lastSync = new Date(portfolioSummary.last_sync_at);
          const daysSinceSync = Math.floor((Date.now() - lastSync.getTime()) / (1000 * 60 * 60 * 24));
          if (daysSinceSync > 7) {
            alerts.push({
              id: 'sync-alert',
              property_id: '',
              audit_type: 'vision',
              severity: 'info',
              title: 'Synchronisation',
              description: `Dernière mise à jour il y a ${daysSinceSync} jours. Pensez à resynchroniser votre portefeuille.`,
              timestamp: new Date().toISOString(),
            });
          }
        }
        
        setAiAlerts(alerts);
        
      } catch (error) {
        console.error('Failed to fetch wealth data:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, [isChecking, hasData]);
  
  const handleAnalyzeProperty = () => {
    router.push('/dashboard/wealth/analyze');
  };
  
  const handleViewReports = () => {
    router.push('/dashboard/wealth/reports');
  };
  
  // Historical net worth data
  // Generate based on current value with slight variations (simulated history)
  const currentValue = liquidAssets + (realEstateData?.total_real_estate_value || 0);
  const netWorthHistory = currentValue > 0 ? [
    { name: 'Jan', value: Math.round(currentValue * 0.92) },
    { name: 'Feb', value: Math.round(currentValue * 0.94) },
    { name: 'Mar', value: Math.round(currentValue * 0.93) },
    { name: 'Apr', value: Math.round(currentValue * 0.96) },
    { name: 'May', value: Math.round(currentValue * 0.98) },
    { name: 'Jun', value: currentValue },
  ] : [];
  
  // Show loading while checking portfolio status
  if (isChecking) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="animate-pulse text-text-muted">Vérification de votre portefeuille...</div>
      </div>
    );
  }
  
  // Show onboarding if user has no portfolio data
  if (hasData === false) {
    return <PortfolioOnboardingPrompt />;
  }
  
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
