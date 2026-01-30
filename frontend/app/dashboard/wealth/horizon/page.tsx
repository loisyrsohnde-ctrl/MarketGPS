'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  Eye,
  EyeOff,
  RefreshCw,
  Settings,
  ChevronRight,
  Target,
  BarChart3,
  Bell,
  TrendingUp,
  TrendingDown,
  Wallet,
  Building2,
  Globe,
  Zap,
  Calendar,
  ArrowRight,
} from 'lucide-react';

import PortfolioHealthRing, { type PortfolioHealth } from '@/components/wealth/PortfolioHealthRing';
import IntelligenceCards, { type IntelligenceCard } from '@/components/wealth/IntelligenceCards';

// =============================================================================
// Types
// =============================================================================

interface PortfolioAsset {
  id: string;
  name: string;
  ticker: string;
  type: 'equity' | 'etf' | 'real_estate' | 'bond' | 'crypto';
  value: number;
  allocation: number;
  score: number;
  change_24h: number;
  change_ytd: number;
}

interface WatchlistAlert {
  asset_id: string;
  asset_name: string;
  alert_type: 'price_drop' | 'score_change' | 'news' | 'rebalance';
  message: string;
  timestamp: string;
}

// =============================================================================
// Demo Data Generator
// =============================================================================

function generateDemoData() {
  const health: PortfolioHealth = {
    overall_score: 72,
    yield_score: 78,
    growth_score: 65,
    risk_score: 80,
    liquidity_score: 68,
    trend: 'up',
    trend_value: 2.3,
    alerts_count: 3,
  };

  const assets: PortfolioAsset[] = [
    { id: '1', name: 'Apple Inc.', ticker: 'AAPL', type: 'equity', value: 45000, allocation: 18, score: 82, change_24h: 1.2, change_ytd: 12.5 },
    { id: '2', name: 'Microsoft Corp', ticker: 'MSFT', type: 'equity', value: 38000, allocation: 15, score: 78, change_24h: 0.8, change_ytd: 8.3 },
    { id: '3', name: 'S&P 500 ETF', ticker: 'SPY', type: 'etf', value: 52000, allocation: 21, score: 75, change_24h: 0.5, change_ytd: 15.2 },
    { id: '4', name: 'Studio Paris 11e', ticker: 'IMMO-1', type: 'real_estate', value: 85000, allocation: 34, score: 71, change_24h: 0, change_ytd: 3.2 },
    { id: '5', name: 'US Treasury Bond', ticker: 'TLT', type: 'bond', value: 30000, allocation: 12, score: 68, change_24h: -0.2, change_ytd: -1.5 },
  ];

  const cards: IntelligenceCard[] = [
    {
      id: '1',
      type: 'alert',
      priority: 'high',
      title: 'Baisse de 5% détectée sur AAPL',
      summary: 'Le cours a chuté suite aux résultats trimestriels. Votre seuil d\'alerte a été atteint.',
      detail: 'Apple a publié des résultats Q4 en dessous des attentes. Les analystes révisent leurs objectifs de cours à la baisse. Considérez si cette correction représente une opportunité d\'achat ou un signal de rééquilibrage.',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      asset_id: '1',
      asset_name: 'AAPL',
      metrics: [
        { label: 'Prix', value: '$178.50', change: -5.2 },
        { label: 'Score', value: '82', change: -3 },
        { label: 'Volume', value: '2.5M' },
      ],
      actions: [
        { label: 'Voir le détail', type: 'secondary', action: 'view_asset' },
        { label: 'Renforcer', type: 'primary', action: 'buy_more' },
      ],
    },
    {
      id: '2',
      type: 'opportunity',
      priority: 'medium',
      title: 'Opportunité de rééquilibrage détectée',
      summary: 'Votre allocation actions dépasse le seuil cible de 60%. Considérez un rééquilibrage vers les obligations.',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      metrics: [
        { label: 'Actions', value: '68%' },
        { label: 'Cible', value: '60%' },
        { label: 'Écart', value: '+8%' },
      ],
      actions: [
        { label: 'Voir suggestion', type: 'primary', action: 'view_rebalance' },
      ],
    },
    {
      id: '3',
      type: 'insight',
      priority: 'low',
      title: 'Performance YTD supérieure au benchmark',
      summary: 'Votre portefeuille surperforme le S&P 500 de 2.3% depuis le début de l\'année.',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      metrics: [
        { label: 'Votre perf', value: '+17.5%' },
        { label: 'S&P 500', value: '+15.2%' },
        { label: 'Alpha', value: '+2.3%' },
      ],
    },
    {
      id: '4',
      type: 'news',
      priority: 'info',
      title: 'BCE : maintien des taux directeurs',
      summary: 'La BCE a décidé de maintenir ses taux. Impact limité sur votre portefeuille obligataire.',
      timestamp: new Date(Date.now() - 172800000).toISOString(),
      asset_name: 'Macro',
    },
    {
      id: '5',
      type: 'action',
      priority: 'medium',
      title: 'Dividende MSFT à réinvestir',
      summary: '€420 de dividendes disponibles. Suggestion: renforcer votre position ETF.',
      timestamp: new Date(Date.now() - 259200000).toISOString(),
      asset_name: 'MSFT',
      actions: [
        { label: 'Réinvestir', type: 'primary', action: 'reinvest_dividend' },
        { label: 'Encaisser', type: 'secondary', action: 'cash_out' },
      ],
    },
  ];

  return { health, assets, cards };
}

// =============================================================================
// Sub-Components
// =============================================================================

function QuickStatCard({
  icon: Icon,
  label,
  value,
  change,
  focusMode,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  change?: number;
  focusMode?: boolean;
}) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className="text-slate-400" />
        <span className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-lg font-semibold tabular-nums">
        {focusMode ? '•••••' : value}
      </p>
      {change !== undefined && !focusMode && (
        <p className={`text-xs ${change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {change >= 0 ? '+' : ''}{change.toFixed(2)}%
        </p>
      )}
    </div>
  );
}

function AssetRow({
  asset,
  focusMode,
  onClick,
}: {
  asset: PortfolioAsset;
  focusMode?: boolean;
  onClick?: () => void;
}) {
  const typeIcon: Record<string, React.ElementType> = {
    equity: TrendingUp,
    etf: BarChart3,
    real_estate: Building2,
    bond: Wallet,
    crypto: Globe,
  };
  const Icon = typeIcon[asset.type] || TrendingUp;

  return (
    <div 
      className="flex items-center gap-4 py-3 px-2 hover:bg-slate-800/30 rounded-lg cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
        <Icon size={14} className="text-slate-400" />
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{asset.ticker}</p>
        <p className="text-xs text-slate-500 truncate">{asset.name}</p>
      </div>
      
      <div className="text-right">
        <p className="text-sm font-semibold tabular-nums">
          {focusMode ? '•••' : `€${(asset.value / 1000).toFixed(1)}k`}
        </p>
        <p className={`text-xs ${asset.change_24h >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {asset.change_24h >= 0 ? '+' : ''}{asset.change_24h}%
        </p>
      </div>
      
      <div className="w-12 text-right">
        <div 
          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-semibold
            ${asset.score >= 70 ? 'bg-emerald-500/20 text-emerald-400' :
              asset.score >= 50 ? 'bg-amber-500/20 text-amber-400' :
              'bg-red-500/20 text-red-400'}`}
        >
          {asset.score}
        </div>
      </div>
      
      <ChevronRight size={14} className="text-slate-600" />
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function HorizonPage() {
  const router = useRouter();
  const [focusMode, setFocusMode] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Demo data
  const [data, setData] = useState<ReturnType<typeof generateDemoData> | null>(null);

  useEffect(() => {
    // Simulate API call
    const timer = setTimeout(() => {
      setData(generateDemoData());
      setIsLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      setData(generateDemoData());
      setLastRefresh(new Date());
      setIsLoading(false);
    }, 500);
  };

  const handleCardAction = (cardId: string, action: string) => {
    console.log('Card action:', cardId, action);
    // Handle different actions
    if (action === 'view_asset') {
      const card = data?.cards.find(c => c.id === cardId);
      if (card?.asset_id) {
        router.push(`/asset/${card.asset_name}`);
      }
    } else if (action === 'view_rebalance') {
      router.push('/strategies');
    }
  };

  if (isLoading || !data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Chargement de l'Horizon...</p>
        </div>
      </div>
    );
  }

  const totalValue = data.assets.reduce((sum, a) => sum + a.value, 0);
  const totalChange = data.assets.reduce((sum, a) => sum + (a.value * a.change_24h / 100), 0);
  const avgChange = (totalChange / totalValue) * 100;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-lg sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold flex items-center gap-2">
                <Globe className="text-indigo-400" size={24} />
                Horizon
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Vue d'ensemble • Mis à jour {lastRefresh.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Focus Mode Toggle */}
              <button
                onClick={() => setFocusMode(!focusMode)}
                className={`p-2 rounded-lg transition-colors ${
                  focusMode 
                    ? 'bg-indigo-600 text-white' 
                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                }`}
                title={focusMode ? 'Afficher les montants' : 'Masquer les montants'}
              >
                {focusMode ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
              
              {/* Refresh */}
              <button
                onClick={handleRefresh}
                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <RefreshCw size={18} className="text-slate-400" />
              </button>
              
              {/* Settings */}
              <button
                onClick={() => router.push('/settings')}
                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <Settings size={18} className="text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <QuickStatCard
            icon={Wallet}
            label="Valeur totale"
            value={`€${(totalValue / 1000).toFixed(0)}k`}
            change={avgChange}
            focusMode={focusMode}
          />
          <QuickStatCard
            icon={TrendingUp}
            label="Performance YTD"
            value="+17.5%"
            change={17.5}
            focusMode={focusMode}
          />
          <QuickStatCard
            icon={Target}
            label="Score moyen"
            value={`${Math.round(data.assets.reduce((s, a) => s + a.score, 0) / data.assets.length)}`}
            focusMode={false} // Always show score
          />
          <QuickStatCard
            icon={Bell}
            label="Alertes actives"
            value={`${data.cards.filter(c => c.priority === 'critical' || c.priority === 'high').length}`}
            focusMode={false}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Health Ring + Assets */}
          <div className="lg:col-span-1 space-y-6">
            <PortfolioHealthRing
              health={data.health}
              size="md"
              showDetails={true}
              focusMode={focusMode}
            />

            {/* Top Assets */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <BarChart3 size={14} className="text-indigo-400" />
                  Portefeuille
                </h3>
                <button 
                  onClick={() => router.push('/watchlist')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Voir tout
                </button>
              </div>
              
              <div className="divide-y divide-slate-800">
                {data.assets.slice(0, 5).map((asset) => (
                  <AssetRow
                    key={asset.id}
                    asset={asset}
                    focusMode={focusMode}
                    onClick={() => router.push(`/asset/${asset.ticker}`)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Right Column - Intelligence Feed */}
          <div className="lg:col-span-2">
            <IntelligenceCards
              cards={data.cards}
              focusMode={focusMode}
              maxVisible={6}
              onAction={handleCardAction}
              onDismiss={(id) => {
                setData(prev => prev ? {
                  ...prev,
                  cards: prev.cards.map(c => c.id === id ? { ...c, dismissed: true } : c)
                } : null);
              }}
            />

            {/* Quick Actions */}
            <div className="mt-6 grid grid-cols-2 gap-4">
              <button
                onClick={() => router.push('/dashboard/wealth/analyze')}
                className="p-4 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-xl text-left hover:border-indigo-500/50 transition-colors group"
              >
                <Eye size={20} className="text-indigo-400 mb-2" />
                <p className="text-sm font-medium">Analyser un bien</p>
                <p className="text-xs text-slate-500">IA Vision + Estimation</p>
                <ArrowRight size={14} className="text-indigo-400 mt-2 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button
                onClick={() => router.push('/dashboard/wealth/opportunities')}
                className="p-4 bg-gradient-to-r from-emerald-600/20 to-teal-600/20 border border-emerald-500/30 rounded-xl text-left hover:border-emerald-500/50 transition-colors group"
              >
                <Target size={20} className="text-emerald-400 mb-2" />
                <p className="text-sm font-medium">Opportunités</p>
                <p className="text-xs text-slate-500">Signaux du marché</p>
                <ArrowRight size={14} className="text-emerald-400 mt-2 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
