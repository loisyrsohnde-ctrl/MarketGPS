'use client';

import { useState, useMemo, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { GlassCard, GlassCardAccent } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { ScoreBadge } from '@/components/ui/badge';
import { AssetLogo } from '@/components/cards/asset-card';
import { ScoreGauge, PillarBar, KpiBar } from '@/components/charts/score-gauge';
import { PriceChart } from '@/components/charts/price-chart';
import { api } from '@/lib/api';
import { cn, formatDate } from '@/lib/utils';
import type { Asset, ChartPeriod } from '@/types';
import {
  ArrowLeft,
  Star,
  StarOff,
  ExternalLink,
  Share2,
  TrendingUp,
  Calendar,
  Activity,
  BarChart3,
  Shield,
  Zap,
  Target,
  Percent,
  LineChart,
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════════════════════
// ASSET DETAIL PAGE - FULL METRICS DISPLAY
// ═══════════════════════════════════════════════════════════════════════════

// Default fallback asset
const defaultAsset: Asset = {
  asset_id: 'UNKNOWN',
  ticker: 'UNKNOWN',
  symbol: 'UNKNOWN',
  name: 'Asset non trouvé',
  asset_type: 'EQUITY',
  market_scope: 'US_EU',
  market_code: 'US',
  score_total: null,
  score_value: null,
  score_momentum: null,
  score_safety: null,
  coverage: 0,
  liquidity: 0,
  fx_risk: 0,
  updated_at: new Date().toISOString(),
};

// Extended chart periods
type ExtendedChartPeriod = '1d' | '1w' | '30d' | '3m' | '6m' | '1y' | '5y' | '10y' | 'max';

// Chart style types
type ChartStyle = 'line' | 'area' | 'candlestick';

export default function AssetDetailPage() {
  const params = useParams();
  const ticker = params.ticker as string;
  const [chartPeriod, setChartPeriod] = useState<ExtendedChartPeriod>('1y');
  const [chartStyle, setChartStyle] = useState<ChartStyle>('line');
  const [userId] = useState('default'); // In production, get from auth
  const queryClient = useQueryClient();

  // Fetch asset details
  const { data: asset, isLoading } = useQuery({
    queryKey: ['asset', ticker],
    queryFn: async () => {
      try {
        const data = await api.getAssetDetails(ticker);
        return data || { ...defaultAsset, ticker };
      } catch {
        return { ...defaultAsset, ticker };
      }
    },
  });

  // Fetch chart data from API - use period directly
  const { data: chartData = [], isLoading: chartLoading, refetch: refetchChart } = useQuery({
    queryKey: ['chart', ticker, chartPeriod],
    queryFn: async () => {
      try {
        // Map to API period format
        const apiPeriodMap: Record<ExtendedChartPeriod, string> = {
          '1d': '1d',
          '1w': '1w',
          '30d': '30d',
          '3m': '3m',
          '6m': '6m',
          '1y': '1y',
          '5y': '5y',
          '10y': '10y',
          'max': '10y',
        };
        const apiPeriod = apiPeriodMap[chartPeriod];
        console.log(`Fetching chart data for ${ticker}, period: ${apiPeriod}`);
        const data = await api.getAssetChart(ticker, apiPeriod);
        console.log(`Received ${data.length} data points`);
        
        // Sort by date ascending
        const sorted = data.sort((a: any, b: any) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        );
        return sorted;
      } catch (error) {
        console.error('Chart data fetch error:', error);
        return [];
      }
    },
    enabled: !!ticker,
    staleTime: 0, // Always refetch when period changes
    refetchOnWindowFocus: false,
  });

  // Refetch when period changes
  useEffect(() => {
    if (ticker && chartPeriod) {
      refetchChart();
    }
  }, [chartPeriod, ticker, refetchChart]);

  // Check if asset is in watchlist
  const { data: watchlistStatus } = useQuery({
    queryKey: ['watchlist-check', ticker, userId],
    queryFn: async () => {
      try {
        const result = await api.checkInWatchlist(ticker, userId);
        return result.in_watchlist;
      } catch {
        return false;
      }
    },
    enabled: !!ticker,
  });

  // Mutation to add/remove from watchlist
  const watchlistMutation = useMutation({
    mutationFn: async (add: boolean) => {
      if (add) {
        await api.addToWatchlist(
          ticker, 
          userId, 
          displayAsset.market_scope || 'US_EU'
        );
      } else {
        await api.removeFromWatchlist(ticker, userId);
      }
    },
    onSuccess: () => {
      // Invalidate watchlist queries
      queryClient.invalidateQueries({ queryKey: ['watchlist-check', ticker, userId] });
      queryClient.invalidateQueries({ queryKey: ['watchlist', userId] });
    },
    onError: (error) => {
      console.error('Watchlist operation failed:', error);
    },
  });

  // Use watchlist status from API
  const isWatchlisted = watchlistStatus ?? false;

  // Handle watchlist toggle
  const handleWatchlistToggle = () => {
    watchlistMutation.mutate(!isWatchlisted);
  };

  // Use asset data or default
  const displayAsset = asset || { ...defaultAsset, ticker };

  // Get current price from chart data if last_price is not available
  const currentPrice = useMemo(() => {
    // Priority 1: Use last_price from asset data (even if very small like 0.0001)
    if (displayAsset.last_price !== null && displayAsset.last_price !== undefined && !isNaN(displayAsset.last_price)) {
      return displayAsset.last_price;
    }
    // Fallback: get last price from chart data
    if (chartData && chartData.length > 0) {
      const lastDataPoint = chartData[chartData.length - 1];
      const chartPrice = lastDataPoint?.close;
      if (chartPrice !== null && chartPrice !== undefined && !isNaN(chartPrice)) {
        return chartPrice;
      }
    }
    return null;
  }, [displayAsset.last_price, chartData]);

  // Helper to display number or fallback
  const displayNumber = (value: number | null | undefined, suffix = '', decimals = 0): string => {
    if (value === null || value === undefined || isNaN(value)) return '—';
    return decimals > 0 ? `${value.toFixed(decimals)}${suffix}` : `${Math.round(value)}${suffix}`;
  };

  // Helper to format price with appropriate decimals
  const formatPrice = (price: number | null | undefined, currency?: string | null): string => {
    if (price === null || price === undefined || isNaN(price)) return '—';
    
    // Determine number of decimals based on price magnitude
    let decimals = 2;
    if (price < 0.01) {
      decimals = 6; // For very small prices (crypto, penny stocks)
    } else if (price < 1) {
      decimals = 4;
    } else if (price < 10) {
      decimals = 3;
    } else if (price < 100) {
      decimals = 2;
    } else {
      decimals = 2;
    }
    
    const formatted = price.toFixed(decimals);
    // Remove trailing zeros
    const cleaned = parseFloat(formatted).toString();
    return currency ? `${cleaned} ${currency}` : cleaned;
  };

  // Helper to get color based on value
  const getScoreColor = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'text-text-muted';
    if (value >= 70) return 'text-score-green';
    if (value >= 40) return 'text-score-yellow';
    return 'text-score-red';
  };

  // Calculate default values from available metrics
  const calculatedMetrics = useMemo(() => {
    // Calculate momentum from RSI if not available
    let momentum = displayAsset.score_momentum;
    if (momentum === null && displayAsset.rsi !== null) {
      const rsi = displayAsset.rsi;
      if (rsi >= 40 && rsi <= 70) {
        momentum = 100 - Math.abs(rsi - 55) * 2;
      } else if (rsi < 40) {
        momentum = Math.max(0, rsi * 2);
      } else {
        momentum = Math.max(0, (100 - rsi) * 2);
      }
    }

    // Calculate safety from volatility if not available
    let safety = displayAsset.score_safety;
    if (safety === null && displayAsset.vol_annual !== null) {
      const vol = displayAsset.vol_annual;
      // Lower volatility = higher safety (inverted)
      if (vol <= 5) safety = 100;
      else if (vol <= 20) safety = 100 - (vol - 5) * 3;
      else if (vol <= 40) safety = 55 - (vol - 20) * 1.5;
      else safety = Math.max(0, 25 - (vol - 40) * 0.5);
    }

    // Calculate value from fundamentals if not available (neutral)
    let value = displayAsset.score_value;
    if (value === null) {
      // Default neutral value if no fundamentals
      value = 50;
    }

    // Estimate coverage from data availability
    let coverage = displayAsset.coverage;
    if (coverage === null) {
      // If we have RSI, vol, price, etc., assume some coverage
      const hasData = displayAsset.rsi !== null || displayAsset.last_price !== null;
      coverage = hasData ? 50 : 0; // Default to 50% if we have some data, 0% if none
    }

    // Estimate liquidity from volume if available
    let liquidity = displayAsset.liquidity;
    if (liquidity === null) {
      // Default to low liquidity if unknown
      liquidity = 0.3; // 30% as default
    }

    // Estimate FX risk from currency
    let fxRisk = displayAsset.fx_risk;
    if (fxRisk === null) {
      // Default based on market code
      const isUSD = displayAsset.market_code === 'US' || displayAsset.currency === 'USD';
      fxRisk = isUSD ? 0.1 : 0.5; // Low risk for USD, medium for others
    }

    return {
      momentum: momentum ?? 0,
      safety: safety ?? 0,
      value: value ?? 50,
      coverage: coverage <= 1 ? coverage * 100 : coverage,
      liquidity,
      fxRisk: fxRisk <= 1 ? fxRisk * 100 : fxRisk,
    };
  }, [displayAsset]);

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="h-8 w-32 skeleton rounded-lg" />
        <div className="h-64 skeleton rounded-2xl" />
        <div className="h-64 skeleton rounded-2xl" />
      </div>
    );
  }

  // Chart period options
  const chartPeriods: { value: ExtendedChartPeriod; label: string }[] = [
    { value: '1d', label: '1J' },
    { value: '1w', label: '1S' },
    { value: '30d', label: '30J' },
    { value: '3m', label: '3M' },
    { value: '6m', label: '6M' },
    { value: '1y', label: '1A' },
    { value: '5y', label: '5A' },
    { value: '10y', label: '10A' },
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back link */}
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour au dashboard
      </Link>

      {/* Header card */}
      <GlassCardAccent padding="lg">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          {/* Asset info */}
          <div className="flex items-center gap-5">
            <AssetLogo ticker={displayAsset.ticker} assetType={displayAsset.asset_type} size="xl" />
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-3xl font-bold text-text-primary">{displayAsset.ticker}</h1>
                <span className="px-3 py-1 rounded-lg bg-surface text-sm text-text-secondary">
                  {displayAsset.asset_type}
                </span>
                <span className="px-3 py-1 rounded-lg bg-surface text-sm text-text-secondary">
                  {displayAsset.market_code}
                </span>
              </div>
              <p className="text-lg text-text-secondary">{displayAsset.name}</p>
              
              {/* Price display - ALWAYS VISIBLE */}
              <div className="flex items-baseline gap-3 mt-3">
                {currentPrice !== null && currentPrice !== undefined && !isNaN(currentPrice) ? (
                  <>
                    <span className="text-3xl font-bold text-text-primary">
                      {formatPrice(currentPrice, displayAsset.currency || undefined)}
                    </span>
                    {currentPrice > 0 && displayAsset.sma200 && displayAsset.sma200 > 0 && (
                      <span className={cn(
                        'text-sm font-medium',
                        currentPrice > displayAsset.sma200 ? 'text-score-green' : 'text-score-red'
                      )}>
                        {currentPrice > displayAsset.sma200 ? '↑' : '↓'} 
                        {Math.abs(((currentPrice - displayAsset.sma200) / displayAsset.sma200) * 100).toFixed(1)}% vs SMA200
                      </span>
                    )}
                  </>
                ) : (
                  <span className="text-xl text-text-muted">Prix en cours de chargement...</span>
                )}
              </div>
              
              <div className="flex items-center gap-3 mt-2 text-sm text-text-muted">
                <span>{displayAsset.market_scope}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  Mis à jour: {formatDate(displayAsset.updated_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3">
            <Button
              variant={isWatchlisted ? 'primary' : 'secondary'}
              onClick={handleWatchlistToggle}
              disabled={watchlistMutation.isPending}
              leftIcon={isWatchlisted ? <Star className="w-4 h-4 fill-current" /> : <StarOff className="w-4 h-4" />}
            >
              {watchlistMutation.isPending ? '...' : (isWatchlisted ? 'Suivi' : 'Suivre')}
            </Button>
            <Link
              href={`https://finance.yahoo.com/quote/${displayAsset.ticker}`}
              target="_blank"
              className="p-2 rounded-lg bg-surface hover:bg-surface-hover border border-glass-border transition-colors"
            >
              <ExternalLink className="w-5 h-5 text-text-secondary" />
            </Link>
          </div>
        </div>
      </GlassCardAccent>

      {/* Score section */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Score gauge */}
        <GlassCard className="flex flex-col items-center justify-center py-8">
          <ScoreGauge score={displayAsset.score_total} size="xl" />
        </GlassCard>

        {/* Pillars with NUMBERS */}
        <GlassCard>
          <h2 className="text-lg font-semibold text-text-primary mb-6">Piliers du score</h2>
          <div className="space-y-5">
            <PillarBar label="Valeur" value={calculatedMetrics.value} icon="📈" />
            <PillarBar label="Momentum" value={calculatedMetrics.momentum} icon="🚀" />
            <PillarBar label="Sécurité" value={calculatedMetrics.safety} icon="🛡️" />
          </div>

          <div className="mt-6 pt-6 border-t border-glass-border">
            <p className="text-sm text-text-muted">
              Le score MarketGPS combine trois piliers pour évaluer le potentiel d&apos;un actif:
              la valeur fondamentale, la dynamique de prix (momentum), et les métriques de sécurité.
            </p>
          </div>
        </GlassCard>
      </div>

      {/* KPIs - ALL NUMERIC */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard padding="md">
          <div className="space-y-2">
            <span className="text-xs text-text-muted uppercase tracking-wide flex items-center gap-1">
              <BarChart3 className="w-3 h-3" /> Couverture
            </span>
            {(() => {
              const coveragePercent = calculatedMetrics.coverage;
              return (
                <>
                  <p className={cn('text-2xl font-bold', getScoreColor(coveragePercent))}>
                    {displayNumber(coveragePercent, '%')}
                  </p>
                  <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-score-red via-score-yellow to-score-green rounded-full transition-all"
                      style={{ width: `${coveragePercent}%` }}
                    />
                  </div>
                </>
              );
            })()}
          </div>
        </GlassCard>
        
        <GlassCard padding="md">
          <div className="space-y-2">
            <span className="text-xs text-text-muted uppercase tracking-wide flex items-center gap-1">
              <Activity className="w-3 h-3" /> Liquidité
            </span>
            {(() => {
              const liq = calculatedMetrics.liquidity;
              const isRatio = liq <= 1;
              const displayValue = isRatio ? liq * 100 : Math.min(100, Math.log10(Math.max(1, liq)) * 10);
              const displayText = isRatio 
                ? `${Math.round(liq * 100)}%` 
                : liq > 1e9 ? `${(liq / 1e9).toFixed(1)}B` 
                : liq > 1e6 ? `${(liq / 1e6).toFixed(1)}M` 
                : liq > 1e3 ? `${(liq / 1e3).toFixed(1)}K` 
                : `${Math.round(liq)}`;
              return (
                <>
                  <p className={cn('text-2xl font-bold', displayValue >= 50 ? 'text-score-green' : 'text-score-yellow')}>
                    {displayText}
                  </p>
                  <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-score-red via-score-yellow to-score-green rounded-full transition-all"
                      style={{ width: `${Math.min(100, displayValue)}%` }}
                    />
                  </div>
                </>
              );
            })()}
          </div>
        </GlassCard>

        <GlassCard padding="md">
          <div className="space-y-2">
            <span className="text-xs text-text-muted uppercase tracking-wide flex items-center gap-1">
              <Shield className="w-3 h-3" /> Risque FX
            </span>
            {(() => {
              const fxRiskPercent = calculatedMetrics.fxRisk;
              return (
                <>
                  <p className={cn('text-2xl font-bold', 
                    fxRiskPercent > 50 ? 'text-score-red' : fxRiskPercent > 25 ? 'text-score-yellow' : 'text-score-green'
                  )}>
                    {displayNumber(fxRiskPercent, '%')}
                  </p>
                  <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-score-green via-score-yellow to-score-red rounded-full transition-all"
                      style={{ width: `${fxRiskPercent}%` }}
                    />
                  </div>
                </>
              );
            })()}
          </div>
        </GlassCard>

        <GlassCard padding="md">
          <div className="space-y-2">
            <span className="text-xs text-text-muted uppercase tracking-wide flex items-center gap-1">
              <Target className="w-3 h-3" /> Confiance
            </span>
            <p className={cn('text-2xl font-bold', getScoreColor(displayAsset.confidence))}>
              {displayNumber(displayAsset.confidence, '%')}
            </p>
            <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-score-red via-score-yellow to-score-green rounded-full transition-all"
                style={{ width: `${displayAsset.confidence ?? 0}%` }}
              />
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Detailed Metrics - Technical Indicators */}
      <GlassCard>
        <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-accent" />
          Métriques détaillées
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">RSI (14)</span>
            <p className={cn('text-xl font-bold mt-1', 
              (displayAsset.rsi ?? 50) > 70 ? 'text-score-red' : 
              (displayAsset.rsi ?? 50) < 30 ? 'text-score-green' : 'text-text-primary'
            )}>
              {displayNumber(displayAsset.rsi, '', 1)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">Volatilité ann.</span>
            <p className={cn('text-xl font-bold mt-1', 
              (displayAsset.vol_annual ?? 0) > 40 ? 'text-score-red' : 'text-text-primary'
            )}>
              {displayNumber(displayAsset.vol_annual, '%', 1)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">Max Drawdown</span>
            <p className={cn('text-xl font-bold mt-1', 
              Math.abs(displayAsset.max_drawdown ?? 0) > 20 ? 'text-score-red' : 'text-text-primary'
            )}>
              {displayNumber(displayAsset.max_drawdown, '%', 1)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">SMA 200</span>
            <p className="text-xl font-bold mt-1 text-text-primary">
              {displayNumber(displayAsset.sma200, '', 2)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">Dernier prix</span>
            <p className="text-xl font-bold mt-1 text-text-primary">
              {displayNumber(displayAsset.last_price, '', 2)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">Z-Score</span>
            <p className={cn('text-xl font-bold mt-1',
              Math.abs(displayAsset.zscore ?? 0) > 2 ? 'text-score-yellow' : 'text-text-primary'
            )}>
              {displayNumber(displayAsset.zscore, '', 2)}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">Risque liquidité</span>
            <p className={cn('text-xl font-bold mt-1',
              (displayAsset.liquidity_risk ?? 0) > 50 ? 'text-score-red' : 'text-score-green'
            )}>
              {displayNumber((displayAsset.liquidity_risk ?? 0) * 100, '%')}
            </p>
          </div>
          <div className="p-3 rounded-xl bg-surface/50">
            <span className="text-xs text-text-muted uppercase">État</span>
            <p className="text-xl font-bold mt-1 text-accent">
              {displayAsset.state_label || 'Équilibre'}
            </p>
          </div>
        </div>
      </GlassCard>

      {/* Chart with period selector */}
      <GlassCard>
        <div className="flex flex-col gap-4 mb-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
              <LineChart className="w-5 h-5 text-accent" />
              Évolution du prix
            </h2>
            
            {/* Chart style selector */}
            <div className="flex gap-1 p-1 rounded-xl bg-surface">
              <button
                onClick={() => setChartStyle('line')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  chartStyle === 'line'
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                )}
                title="Ligne"
              >
                📈
              </button>
              <button
                onClick={() => setChartStyle('area')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  chartStyle === 'area'
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                )}
                title="Aire"
              >
                📊
              </button>
              <button
                onClick={() => setChartStyle('candlestick')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  chartStyle === 'candlestick'
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                )}
                title="Chandeliers"
              >
                🕯️
              </button>
            </div>
          </div>
          
          {/* Period selector */}
          <div className="flex flex-wrap gap-1 p-1 rounded-xl bg-surface">
            {chartPeriods.map((period) => (
              <button
                key={period.value}
                onClick={() => {
                  setChartPeriod(period.value);
                }}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  chartPeriod === period.value
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                )}
              >
                {period.label}
              </button>
            ))}
          </div>
        </div>
        
        {chartLoading ? (
          <div className="h-[300px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent"></div>
            <span className="ml-3 text-text-muted">Chargement des données...</span>
          </div>
        ) : chartData.length > 0 ? (
          <PriceChart
            data={chartData}
            period={chartPeriod as ChartPeriod}
            onPeriodChange={(p) => setChartPeriod(p as ExtendedChartPeriod)}
            height={300}
            showPeriodSelector={false}
            chartStyle={chartStyle}
          />
        ) : (
          <div className="h-[300px] flex items-center justify-center text-text-muted">
            <p>Aucune donnée disponible pour cette période</p>
          </div>
        )}
      </GlassCard>

      {/* About */}
      <GlassCard>
        <h2 className="text-lg font-semibold text-text-primary mb-4">
          À propos de {asset.name}
        </h2>
        <p className="text-text-secondary leading-relaxed">
          {asset.asset_type === 'ETF'
            ? `${asset.name} est un Exchange-Traded Fund (ETF) qui offre aux investisseurs une exposition diversifiée à son marché de référence. Il combine la flexibilité de négociation d'une action avec les avantages de la diversification d'un fonds.`
            : `${asset.name} (${asset.ticker}) est une entreprise cotée sur les marchés financiers. Le score MarketGPS analyse les fondamentaux, le momentum de prix et les métriques de risque pour évaluer son potentiel d'investissement.`}
        </p>

        {/* External links */}
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href={`https://finance.yahoo.com/quote/${asset.ticker}`}
            target="_blank"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-all text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            Yahoo Finance
          </Link>
          <Link
            href={`https://www.google.com/finance/quote/${asset.ticker}:${asset.market_code === 'US' ? 'NASDAQ' : asset.market_code}`}
            target="_blank"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-all text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            Google Finance
          </Link>
          <Link
            href={`https://www.tradingview.com/symbols/${asset.ticker}`}
            target="_blank"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-all text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            TradingView
          </Link>
          <Link
            href={`https://www.google.com/search?q=${asset.ticker}+${asset.name}+news&tbm=nws`}
            target="_blank"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface text-text-secondary hover:text-accent hover:border-accent border border-glass-border transition-all text-sm"
          >
            📰 Actualités
          </Link>
        </div>
      </GlassCard>

      {/* Disclaimer */}
      <div className="p-4 rounded-xl bg-surface/50 border border-glass-border">
        <p className="text-xs text-text-dim text-center">
          ⚠️ MarketGPS est un outil d&apos;analyse statistique et éducatif. Les scores ne constituent pas
          des conseils financiers. Les performances passées ne garantissent pas les résultats futurs.
          Capital à risque.
        </p>
      </div>
    </div>
  );
}
