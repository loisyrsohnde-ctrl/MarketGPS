'use client';

/**
 * MarketGPS - Asset Inspector Slide-Over Panel
 * =============================================
 * A global slide-over panel that displays detailed asset information.
 * Triggered from anywhere in the app via the useAssetInspector store.
 * 
 * Features:
 * - Score gauge with on-demand recalculation
 * - Watchlist toggle
 * - Strategy assignment
 * - Fundamentals & Technical tabs
 */

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, Star, Zap, TrendingUp, TrendingDown, Loader2, 
  Building2, Globe, BarChart3, Activity, RefreshCw,
  ChevronRight, Plus, Briefcase, AlertCircle
} from 'lucide-react';
import { useAssetInspector } from '@/store/useAssetInspector';
import { cn } from '@/lib/utils';
import { getApiBaseUrl } from '@/lib/config';
import { ScoreGauge } from '@/components/charts/score-gauge';

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

interface AssetDetail {
  asset_id: string;
  ticker: string;
  symbol: string;
  name: string;
  asset_type: string;
  market_scope: string;
  market_code: string;
  exchange?: string;
  currency?: string;
  country?: string;
  sector?: string;
  industry?: string;
  // Scores
  score_total?: number;
  score_value?: number;
  score_momentum?: number;
  score_safety?: number;
  confidence?: number;
  // Price data
  price?: number;
  change_pct?: number;
  volume?: number;
  market_cap?: number;
  // Technical
  rsi?: number;
  volatility?: number;
  trend?: string;
}

interface UserStrategy {
  id: number;
  name: string;
  template_id?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// SUB-COMPONENTS
// ═══════════════════════════════════════════════════════════════════════════

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center px-4">
      <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
      <p className="text-zinc-400 mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors"
        >
          Réessayer
        </button>
      )}
    </div>
  );
}

function TabButton({ 
  active, 
  onClick, 
  children 
}: { 
  active: boolean; 
  onClick: () => void; 
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-4 py-2 text-sm font-medium rounded-lg transition-all",
        active 
          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" 
          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
      )}
    >
      {children}
    </button>
  );
}

function StatRow({ label, value, icon: Icon }: { label: string; value: React.ReactNode; icon?: any }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-zinc-800/50 last:border-0">
      <div className="flex items-center gap-2 text-zinc-400">
        {Icon && <Icon className="w-4 h-4" />}
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm font-medium text-zinc-100">{value}</span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export function AssetInspector() {
  const { isOpen, selectedTicker, selectedAssetId, closeInspector } = useAssetInspector();
  
  // Local state
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'fundamentals' | 'technical'>('fundamentals');
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistLoading, setWatchlistLoading] = useState(false);
  const [recalculating, setRecalculating] = useState(false);
  const [strategies, setStrategies] = useState<UserStrategy[]>([]);
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);

  const API_BASE = getApiBaseUrl();

  // Fetch asset details when ticker changes
  const fetchAssetDetails = useCallback(async () => {
    if (!selectedTicker) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Try to fetch by asset_id first, fallback to ticker search
      const searchParam = selectedAssetId || selectedTicker;
      const res = await fetch(`${API_BASE}/api/assets/${encodeURIComponent(searchParam)}`);
      
      if (!res.ok) {
        // Try searching by ticker
        const searchRes = await fetch(`${API_BASE}/api/assets/search?q=${encodeURIComponent(selectedTicker)}&limit=1`);
        if (searchRes.ok) {
          const searchData = await searchRes.json();
          if (searchData.assets?.length > 0 || searchData.data?.length > 0) {
            setAsset(searchData.assets?.[0] || searchData.data?.[0]);
            return;
          }
        }
        throw new Error('Asset not found');
      }
      
      const data = await res.json();
      setAsset(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load asset');
    } finally {
      setLoading(false);
    }
  }, [selectedTicker, selectedAssetId, API_BASE]);

  // Check watchlist status
  const checkWatchlist = useCallback(async () => {
    if (!selectedTicker) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/watchlist/check/${encodeURIComponent(selectedAssetId || selectedTicker)}`);
      if (res.ok) {
        const data = await res.json();
        setInWatchlist(data.in_watchlist || false);
      }
    } catch (err) {
      console.error('Failed to check watchlist:', err);
    }
  }, [selectedTicker, selectedAssetId, API_BASE]);

  // Fetch user strategies
  const fetchStrategies = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/strategies/user?user_id=default`);
      if (res.ok) {
        const data = await res.json();
        setStrategies(data.strategies || data || []);
      }
    } catch (err) {
      console.error('Failed to fetch strategies:', err);
    }
  }, [API_BASE]);

  // Toggle watchlist
  const toggleWatchlist = async () => {
    if (!asset) return;
    
    setWatchlistLoading(true);
    try {
      if (inWatchlist) {
        await fetch(`${API_BASE}/api/watchlist/${encodeURIComponent(asset.asset_id)}?user_id=default`, {
          method: 'DELETE',
        });
      } else {
        await fetch(`${API_BASE}/api/watchlist?user_id=default`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ asset_id: asset.asset_id }),
        });
      }
      setInWatchlist(!inWatchlist);
    } catch (err) {
      console.error('Failed to toggle watchlist:', err);
    } finally {
      setWatchlistLoading(false);
    }
  };

  // Recalculate score on-demand
  const recalculateScore = async () => {
    if (!asset) return;
    
    setRecalculating(true);
    try {
      const res = await fetch(`${API_BASE}/api/assets/${encodeURIComponent(asset.ticker)}/score?force=true`, {
        method: 'POST',
      });
      
      if (res.ok) {
        const newScore = await res.json();
        setAsset(prev => prev ? {
          ...prev,
          score_total: newScore.score_total,
          score_value: newScore.score_value,
          score_momentum: newScore.score_momentum,
          score_safety: newScore.score_safety,
          confidence: newScore.confidence,
        } : null);
      } else if (res.status === 403) {
        // Quota exceeded
        alert('Quota de calculs atteint. Passez Pro pour des analyses illimitées.');
      }
    } catch (err) {
      console.error('Failed to recalculate score:', err);
    } finally {
      setRecalculating(false);
    }
  };

  // Add to strategy
  const addToStrategy = async (strategyId: number) => {
    if (!asset) return;
    
    try {
      await fetch(`${API_BASE}/api/strategies/${strategyId}/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          asset_id: asset.asset_id,
          weight: 0.05,
          block: 'satellite'
        }),
      });
      setShowStrategyDropdown(false);
    } catch (err) {
      console.error('Failed to add to strategy:', err);
    }
  };

  // Effects
  useEffect(() => {
    if (isOpen && selectedTicker) {
      fetchAssetDetails();
      checkWatchlist();
      fetchStrategies();
    }
  }, [isOpen, selectedTicker, fetchAssetDetails, checkWatchlist, fetchStrategies]);

  // Close on escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeInspector();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, closeInspector]);

  // Format helpers
  const formatPrice = (price?: number) => {
    if (!price) return '—';
    return new Intl.NumberFormat('fr-FR', { 
      style: 'currency', 
      currency: asset?.currency || 'USD',
      minimumFractionDigits: 2,
    }).format(price);
  };

  const formatNumber = (num?: number) => {
    if (!num) return '—';
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toLocaleString('fr-FR');
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
            onClick={closeInspector}
          />

          {/* Slide-over Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className={cn(
              "fixed top-0 right-0 h-full z-[101]",
              "w-full sm:w-[500px] max-w-full",
              "bg-zinc-950 border-l border-zinc-800",
              "flex flex-col overflow-hidden",
              "shadow-2xl shadow-black/50"
            )}
          >
            {/* Header */}
            <div className="flex-shrink-0 px-6 py-4 border-b border-zinc-800 bg-zinc-900/50">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  {loading ? (
                    <div className="animate-pulse">
                      <div className="h-8 w-24 bg-zinc-800 rounded mb-2" />
                      <div className="h-4 w-48 bg-zinc-800 rounded" />
                    </div>
                  ) : asset ? (
                    <>
                      <div className="flex items-center gap-3 mb-1">
                        <h2 className="text-2xl font-bold text-white tracking-tight">
                          {asset.ticker || asset.symbol}
                        </h2>
                        <span className="px-2 py-0.5 text-xs font-medium bg-zinc-800 text-zinc-400 rounded">
                          {asset.asset_type}
                        </span>
                      </div>
                      <p className="text-sm text-zinc-400 truncate">{asset.name}</p>
                      
                      {/* Price & Change */}
                      <div className="flex items-center gap-3 mt-2">
                        <span className="text-xl font-semibold text-white">
                          {formatPrice(asset.price)}
                        </span>
                        {asset.change_pct !== undefined && (
                          <span className={cn(
                            "flex items-center gap-1 text-sm font-medium",
                            asset.change_pct >= 0 ? "text-emerald-400" : "text-red-400"
                          )}>
                            {asset.change_pct >= 0 ? (
                              <TrendingUp className="w-4 h-4" />
                            ) : (
                              <TrendingDown className="w-4 h-4" />
                            )}
                            {asset.change_pct >= 0 ? '+' : ''}{asset.change_pct.toFixed(2)}%
                          </span>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className="text-zinc-500">Chargement...</div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2 ml-4">
                  {/* Watchlist Star */}
                  <button
                    onClick={toggleWatchlist}
                    disabled={watchlistLoading || !asset}
                    className={cn(
                      "p-2 rounded-lg transition-all",
                      inWatchlist 
                        ? "bg-amber-500/20 text-amber-400" 
                        : "bg-zinc-800 text-zinc-400 hover:text-amber-400"
                    )}
                    title={inWatchlist ? 'Retirer de la watchlist' : 'Ajouter à la watchlist'}
                  >
                    {watchlistLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Star className={cn("w-5 h-5", inWatchlist && "fill-current")} />
                    )}
                  </button>

                  {/* Close */}
                  <button
                    onClick={closeInspector}
                    className="p-2 rounded-lg bg-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <LoadingSpinner />
              ) : error ? (
                <ErrorState message={error} onRetry={fetchAssetDetails} />
              ) : asset ? (
                <div className="p-6 space-y-6">
                  {/* Score Section */}
                  <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">
                        Intelligence Score
                      </h3>
                      <button
                        onClick={recalculateScore}
                        disabled={recalculating}
                        className={cn(
                          "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                          "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20",
                          "disabled:opacity-50 disabled:cursor-not-allowed"
                        )}
                      >
                        {recalculating ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Calcul...
                          </>
                        ) : (
                          <>
                            <Zap className="w-4 h-4" />
                            Recalculer
                          </>
                        )}
                      </button>
                    </div>

                    <div className="flex items-center justify-center py-4">
                      <ScoreGauge 
                        score={asset.score_total || 0} 
                        size="xl"
                        showLabel
                      />
                    </div>

                    {/* Sub-scores */}
                    <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-zinc-800">
                      <div className="text-center">
                        <div className="text-xs text-zinc-500 mb-1">Value</div>
                        <div className="text-lg font-semibold text-blue-400">
                          {asset.score_value?.toFixed(0) || '—'}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-zinc-500 mb-1">Momentum</div>
                        <div className="text-lg font-semibold text-purple-400">
                          {asset.score_momentum?.toFixed(0) || '—'}
                        </div>
                      </div>
                      <div className="text-center">
                        <div className="text-xs text-zinc-500 mb-1">Safety</div>
                        <div className="text-lg font-semibold text-emerald-400">
                          {asset.score_safety?.toFixed(0) || '—'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Strategy Section */}
                  <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
                    <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">
                      Ajouter à une stratégie
                    </h3>
                    
                    <div className="relative">
                      <button
                        onClick={() => setShowStrategyDropdown(!showStrategyDropdown)}
                        className="w-full flex items-center justify-between px-4 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                      >
                        <span className="flex items-center gap-2 text-sm text-zinc-300">
                          <Briefcase className="w-4 h-4" />
                          Sélectionner une stratégie
                        </span>
                        <ChevronRight className={cn(
                          "w-4 h-4 text-zinc-500 transition-transform",
                          showStrategyDropdown && "rotate-90"
                        )} />
                      </button>

                      {/* Dropdown */}
                      <AnimatePresence>
                        {showStrategyDropdown && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute top-full left-0 right-0 mt-2 bg-zinc-800 rounded-lg border border-zinc-700 shadow-xl overflow-hidden z-10"
                          >
                            {strategies.length > 0 ? (
                              strategies.map((strategy) => (
                                <button
                                  key={strategy.id}
                                  onClick={() => addToStrategy(strategy.id)}
                                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-zinc-700 transition-colors text-left"
                                >
                                  <Plus className="w-4 h-4 text-emerald-400" />
                                  <span className="text-sm text-zinc-200">{strategy.name}</span>
                                </button>
                              ))
                            ) : (
                              <div className="px-4 py-3 text-sm text-zinc-500">
                                Aucune stratégie créée
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* Tabs */}
                  <div className="flex gap-2">
                    <TabButton 
                      active={activeTab === 'fundamentals'} 
                      onClick={() => setActiveTab('fundamentals')}
                    >
                      Fondamentaux
                    </TabButton>
                    <TabButton 
                      active={activeTab === 'technical'} 
                      onClick={() => setActiveTab('technical')}
                    >
                      Technique
                    </TabButton>
                  </div>

                  {/* Tab Content */}
                  <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
                    {activeTab === 'fundamentals' ? (
                      <div>
                        <StatRow label="Secteur" value={asset.sector || '—'} icon={Building2} />
                        <StatRow label="Industrie" value={asset.industry || '—'} />
                        <StatRow label="Pays" value={asset.country || '—'} icon={Globe} />
                        <StatRow label="Bourse" value={asset.exchange || asset.market_code || '—'} />
                        <StatRow label="Devise" value={asset.currency || '—'} />
                        <StatRow label="Market Cap" value={formatNumber(asset.market_cap)} icon={BarChart3} />
                      </div>
                    ) : (
                      <div>
                        <StatRow label="RSI (14)" value={asset.rsi?.toFixed(1) || '—'} icon={Activity} />
                        <StatRow label="Volatilité" value={asset.volatility ? `${asset.volatility.toFixed(1)}%` : '—'} />
                        <StatRow label="Tendance" value={asset.trend || '—'} icon={TrendingUp} />
                        <StatRow label="Volume" value={formatNumber(asset.volume)} />
                        <StatRow label="Confiance" value={asset.confidence ? `${asset.confidence}%` : '—'} />
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>

            {/* Footer */}
            <div className="flex-shrink-0 px-6 py-4 border-t border-zinc-800 bg-zinc-900/50">
              <button
                onClick={() => {
                  if (asset) {
                    window.location.href = `/asset/${asset.ticker}`;
                  }
                }}
                className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
              >
                Voir page complète
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default AssetInspector;
