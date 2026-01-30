'use client';

import React, { useMemo } from 'react';
import {
  TrendingUp,
  Home,
  PieChart,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  AlertCircle,
  Building2,
  Wallet,
  Activity,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { formatCurrency, formatPercent, getScoreColor } from '@/lib/api-real-estate';
import type { WealthSummary, RealEstatePortfolio, AIAuditResult } from '@/types/wealth';

// =============================================================================
// Types
// =============================================================================

interface WealthIntelligenceProps {
  // Financial assets (stocks, ETFs, crypto)
  liquidAssets: number;
  liquidChange24h?: number;
  
  // Real estate portfolio
  realEstatePortfolio?: RealEstatePortfolio;
  
  // Risk score (0-100, lower is safer)
  overallRiskScore?: number;
  
  // Historical data for chart
  netWorthHistory?: { name: string; value: number }[];
  
  // AI alerts
  aiAlerts?: AIAuditResult[];
  
  // Callbacks
  onAnalyzeProperty?: () => void;
  onViewReports?: () => void;
}

// =============================================================================
// Sub-Components
// =============================================================================

function KPICard({
  label,
  value,
  icon,
  color = 'text-emerald-400',
  subtext,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  color?: string;
  subtext?: string;
}) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-xl hover:border-slate-700 transition-colors">
      <div className="flex justify-between items-center mb-4 text-slate-400">
        {icon}
        <span className="text-[10px] font-bold uppercase tracking-tighter">
          {subtext || 'Vérifié'}
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-medium tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

function AlertItem({
  title,
  description,
  time,
  severity,
}: {
  title: string;
  description: string;
  time: string;
  severity: 'critical' | 'warning' | 'info';
}) {
  const severityColors = {
    critical: 'text-red-400',
    warning: 'text-amber-400',
    info: 'text-blue-400',
  };

  return (
    <div className="group cursor-pointer">
      <div className="flex justify-between text-[10px] mb-1 text-slate-500 uppercase font-bold tracking-widest">
        <span className={severityColors[severity]}>{title}</span>
        <span>{time}</span>
      </div>
      <p className="text-sm text-slate-300 leading-relaxed group-hover:text-white transition-colors">
        {description}
      </p>
      <div className="h-px bg-slate-800 mt-4" />
    </div>
  );
}

function CashFlowWaterfall({ data }: { data: { name: string; value: number; fill: string }[] }) {
  return (
    <div className="h-[200px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
          <XAxis type="number" stroke="#64748b" fontSize={10} tickFormatter={(v) => `${v >= 0 ? '+' : ''}${(v / 1000).toFixed(0)}k`} />
          <YAxis type="category" dataKey="name" stroke="#64748b" fontSize={10} width={100} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
            formatter={(value: number) => formatCurrency(value)}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function WealthIntelligence({
  liquidAssets,
  liquidChange24h = 0,
  realEstatePortfolio,
  overallRiskScore = 25,
  netWorthHistory,
  aiAlerts = [],
  onAnalyzeProperty,
  onViewReports,
}: WealthIntelligenceProps) {
  // Calculate totals
  const realEstateValue = realEstatePortfolio?.total_real_estate_value || 0;
  const totalNetWorth = liquidAssets + realEstateValue;
  const annualCashflow = realEstatePortfolio?.total_annual_cashflow || 0;
  const portfolioYield = realEstatePortfolio?.portfolio_yield || 0;
  
  // Default historical data if not provided
  const chartData = useMemo(() => {
    if (netWorthHistory && netWorthHistory.length > 0) {
      return netWorthHistory;
    }
    // Generate sample data
    return [
      { name: 'Jan', value: totalNetWorth * 0.92 },
      { name: 'Feb', value: totalNetWorth * 0.95 },
      { name: 'Mar', value: totalNetWorth * 0.94 },
      { name: 'Apr', value: totalNetWorth * 0.98 },
      { name: 'May', value: totalNetWorth * 0.97 },
      { name: 'Jun', value: totalNetWorth },
    ];
  }, [netWorthHistory, totalNetWorth]);
  
  // Cash flow waterfall data
  const waterfallData = useMemo(() => {
    if (!realEstatePortfolio || realEstatePortfolio.properties.length === 0) {
      return [];
    }
    
    const avgProperty = realEstatePortfolio.properties[0];
    const grossRent = avgProperty.purchase_price * (portfolioYield / 100 + 0.03);
    
    return [
      { name: 'Loyer Brut', value: grossRent, fill: '#10b981' },
      { name: 'Charges', value: -grossRent * 0.25, fill: '#ef4444' },
      { name: 'Intérêts Emprunt', value: -grossRent * 0.35, fill: '#f97316' },
      { name: 'Impôts', value: -grossRent * 0.05, fill: '#eab308' },
      { name: 'Cash-Flow Net', value: avgProperty.annual_cashflow, fill: '#3b82f6' },
    ];
  }, [realEstatePortfolio, portfolioYield]);
  
  // Default alerts if none provided
  const displayAlerts = aiAlerts.length > 0 ? aiAlerts : [
    {
      id: '1',
      property_id: '',
      audit_type: 'document' as const,
      severity: 'critical' as const,
      title: 'Audit Immobilier',
      description: 'Analyse DPE en attente pour le bien parisien.',
      timestamp: new Date().toISOString(),
    },
    {
      id: '2',
      property_id: '',
      audit_type: 'legal' as const,
      severity: 'warning' as const,
      title: 'Optimisation Fiscale',
      description: 'Révision de l\'amortissement LMNP recommandée pour la clôture annuelle.',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: '3',
      property_id: '',
      audit_type: 'vision' as const,
      severity: 'info' as const,
      title: 'Actualité Marché',
      description: 'Les taux de capitalisation se sont comprimés de 25 points ce trimestre.',
      timestamp: new Date(Date.now() - 259200000).toISOString(),
    },
  ];

  const formatTimeAgo = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 24) return `il y a ${hours}h`;
    const days = Math.floor(hours / 24);
    return `il y a ${days}j`;
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-8 font-sans">
      {/* Header */}
      <header className="mb-10 flex flex-col lg:flex-row justify-between items-start lg:items-end gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Intelligence Patrimoniale</h1>
          <p className="text-slate-400 mt-1 text-sm uppercase tracking-widest">
            Portefeuille Consolidé • Moteur MarketGPS
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500 uppercase font-medium">Patrimoine Net (EUR)</p>
          <div className="text-4xl font-light tabular-nums">
            {formatCurrency(totalNetWorth, 'EUR', 'fr-FR')}
          </div>
          {liquidChange24h !== 0 && (
            <div className={`flex items-center justify-end gap-1 text-sm ${liquidChange24h > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {liquidChange24h > 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {formatPercent(Math.abs(liquidChange24h))} (24h)
            </div>
          )}
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <KPICard
          label="Actifs Liquides"
          value={formatCurrency(liquidAssets, 'EUR', 'fr-FR')}
          icon={<Wallet size={18} />}
          color="text-emerald-400"
        />
        <KPICard
          label="Immobilier"
          value={formatCurrency(realEstateValue, 'EUR', 'fr-FR')}
          icon={<Building2 size={18} />}
          color="text-indigo-400"
        />
        <KPICard
          label="Score de Risque GPS"
          value={`${overallRiskScore}/100`}
          icon={<ShieldCheck size={18} />}
          color={overallRiskScore < 30 ? 'text-emerald-400' : overallRiskScore < 60 ? 'text-amber-400' : 'text-red-400'}
          subtext="Plus bas = plus sûr"
        />
        <KPICard
          label="Rendement Portefeuille"
          value={`${portfolioYield.toFixed(1)}%`}
          icon={<Activity size={18} />}
          color="text-emerald-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Historical Net Worth Chart */}
        <div className="lg:col-span-2 bg-slate-900/30 border border-slate-800 rounded-2xl p-8">
          <div className="flex justify-between items-center mb-8">
            <h3 className="text-lg font-medium">Évolution du Patrimoine</h3>
            <div className="flex gap-2">
              {['1M', '6M', '1A', 'TOUT'].map((t) => (
                <button
                  key={t}
                  className="px-3 py-1 text-[10px] bg-slate-800 rounded hover:bg-slate-700 transition-colors uppercase"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" fontSize={10} axisLine={false} tickLine={false} />
                <YAxis 
                  stroke="#64748b" 
                  fontSize={10} 
                  axisLine={false} 
                  tickLine={false}
                  tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`}
                />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                  formatter={(value: number) => [formatCurrency(value), 'Net Worth']}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorVal)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* AI Intelligence Feed */}
        <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-medium mb-6 flex items-center gap-2">
            <AlertCircle size={20} className="text-indigo-400" />
            Intelligence IA
          </h3>
          <div className="space-y-6">
            {displayAlerts.slice(0, 4).map((alert) => (
              <AlertItem
                key={alert.id}
                title={alert.title}
                description={alert.description}
                time={formatTimeAgo(alert.timestamp)}
                severity={alert.severity}
              />
            ))}
          </div>
          <button
            onClick={onViewReports}
            className="w-full mt-8 py-3 text-xs bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium transition-all"
          >
            Voir Tous les Rapports
          </button>
        </div>
      </div>

      {/* Cash Flow Waterfall (if real estate data available) */}
      {waterfallData.length > 0 && (
        <div className="mt-8 bg-slate-900/30 border border-slate-800 rounded-2xl p-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-medium">Répartition du Cash-Flow (Bien Moyen)</h3>
            <span className="text-xs text-slate-500 uppercase">Annuel</span>
          </div>
          <CashFlowWaterfall data={waterfallData} />
        </div>
      )}

      {/* Analyze New Property CTA */}
      <div className="mt-8 flex justify-center">
        <button
          onClick={onAnalyzeProperty}
          className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl font-medium transition-all flex items-center gap-3"
        >
          <Home size={20} />
          Analyser une Nouvelle Opportunité
          <ArrowUpRight size={18} />
        </button>
      </div>
    </div>
  );
}
