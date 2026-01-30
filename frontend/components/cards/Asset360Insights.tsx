'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Lightbulb,
  TrendingUp,
  TrendingDown,
  Minus,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Newspaper,
  Users,
  Target,
  Zap,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import Link from 'next/link';

// =============================================================================
// Types
// =============================================================================

interface AssetInsight {
  type: 'strength' | 'weakness' | 'opportunity' | 'risk';
  text: string;
  score_impact?: number; // +/- points on score
}

interface PeerComparison {
  ticker: string;
  name: string;
  score: number;
  score_diff: number; // vs current asset
  price_change_ytd: number;
}

interface RelatedNews {
  id: string;
  title: string;
  source: string;
  published_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
}

interface Asset360InsightsProps {
  ticker: string;
  score: number;
  sector?: string;
  industry?: string;
  className?: string;
}

// =============================================================================
// Demo Data Generator (would be replaced by API calls)
// =============================================================================

function generateInsights(ticker: string, score: number): AssetInsight[] {
  const insights: AssetInsight[] = [];
  
  if (score >= 70) {
    insights.push({
      type: 'strength',
      text: `${ticker} affiche un momentum technique solide avec un RSI dans la zone neutre-haute, suggérant une tendance haussière soutenue.`,
      score_impact: 8,
    });
  } else if (score < 40) {
    insights.push({
      type: 'weakness',
      text: `La volatilité élevée et le drawdown récent pèsent sur le score. Une stabilisation est nécessaire avant de renforcer.`,
      score_impact: -12,
    });
  }
  
  if (score >= 50) {
    insights.push({
      type: 'opportunity',
      text: `Position au-dessus de la SMA200, ce qui historiquement précède des performances supérieures au marché sur 12 mois.`,
      score_impact: 5,
    });
  }
  
  insights.push({
    type: score < 50 ? 'risk' : 'strength',
    text: score < 50 
      ? `Couverture données limitée (${Math.round(30 + Math.random() * 20)}%). L'incertitude sur les fondamentaux augmente le risque.`
      : `Liquidité élevée et spread serré permettent une exécution optimale des ordres.`,
    score_impact: score < 50 ? -5 : 3,
  });
  
  return insights.slice(0, 3);
}

function generatePeers(ticker: string, score: number): PeerComparison[] {
  const peerNames: Record<string, string[]> = {
    AAPL: ['MSFT', 'GOOGL', 'META', 'AMZN'],
    MSFT: ['AAPL', 'GOOGL', 'CRM', 'ORCL'],
    GOOGL: ['META', 'MSFT', 'AMZN', 'NFLX'],
    TSLA: ['RIVN', 'NIO', 'GM', 'F'],
    default: ['SPY', 'QQQ', 'IWM', 'VTI'],
  };
  
  const peers = peerNames[ticker] || peerNames.default;
  
  return peers.slice(0, 4).map((peerTicker, i) => ({
    ticker: peerTicker,
    name: peerTicker,
    score: Math.max(20, Math.min(95, score + (Math.random() - 0.5) * 30)),
    score_diff: Math.round((Math.random() - 0.5) * 20),
    price_change_ytd: Math.round((Math.random() - 0.3) * 40 * 10) / 10,
  }));
}

function generateNews(ticker: string): RelatedNews[] {
  return [
    {
      id: '1',
      title: `${ticker} dépasse les attentes au Q4 avec une croissance de 12%`,
      source: 'MarketWatch',
      published_at: new Date(Date.now() - 86400000).toISOString(),
      sentiment: 'positive',
    },
    {
      id: '2',
      title: `Analystes : objectif de cours relevé pour ${ticker}`,
      source: 'Bloomberg',
      published_at: new Date(Date.now() - 172800000).toISOString(),
      sentiment: 'positive',
    },
    {
      id: '3',
      title: `Secteur tech : volatilité attendue suite aux annonces Fed`,
      source: 'Reuters',
      published_at: new Date(Date.now() - 259200000).toISOString(),
      sentiment: 'neutral',
    },
  ];
}

// =============================================================================
// Sub-Components
// =============================================================================

function InsightCard({ insight }: { insight: AssetInsight }) {
  const config = {
    strength: { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' },
    weakness: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30' },
    opportunity: { icon: Target, color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30' },
    risk: { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
  }[insight.type];
  
  const Icon = config.icon;
  
  return (
    <div className={`p-3 rounded-lg border ${config.bg}`}>
      <div className="flex items-start gap-2">
        <Icon size={16} className={`mt-0.5 ${config.color}`} />
        <div className="flex-1">
          <p className="text-sm text-slate-200 leading-relaxed">{insight.text}</p>
          {insight.score_impact !== undefined && (
            <p className={`text-xs mt-1 ${insight.score_impact >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              Impact score: {insight.score_impact >= 0 ? '+' : ''}{insight.score_impact} pts
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function PeerRow({ peer, onClick }: { peer: PeerComparison; onClick?: () => void }) {
  return (
    <div 
      className="flex items-center gap-3 py-2 px-2 hover:bg-slate-800/30 rounded-lg cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-semibold">
        {peer.ticker.slice(0, 2)}
      </div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{peer.ticker}</p>
      </div>
      
      <div className="text-right">
        <div 
          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-semibold
            ${peer.score >= 70 ? 'bg-emerald-500/20 text-emerald-400' :
              peer.score >= 50 ? 'bg-amber-500/20 text-amber-400' :
              'bg-red-500/20 text-red-400'}`}
        >
          {Math.round(peer.score)}
        </div>
      </div>
      
      <div className="w-16 text-right">
        <p className={`text-xs ${peer.price_change_ytd >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
          {peer.price_change_ytd >= 0 ? '+' : ''}{peer.price_change_ytd}%
        </p>
        <p className="text-[10px] text-slate-500">YTD</p>
      </div>
      
      <ChevronRight size={14} className="text-slate-600" />
    </div>
  );
}

function NewsRow({ news }: { news: RelatedNews }) {
  const sentimentColor = {
    positive: 'text-emerald-400',
    negative: 'text-red-400',
    neutral: 'text-slate-400',
  }[news.sentiment];
  
  const sentimentIcon = {
    positive: <TrendingUp size={12} />,
    negative: <TrendingDown size={12} />,
    neutral: <Minus size={12} />,
  }[news.sentiment];
  
  return (
    <div className="flex items-start gap-3 py-2">
      <div className={`mt-0.5 ${sentimentColor}`}>
        {sentimentIcon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-200 line-clamp-2">{news.title}</p>
        <p className="text-[10px] text-slate-500 mt-1">
          {news.source} • {new Date(news.published_at).toLocaleDateString('fr-FR')}
        </p>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function Asset360Insights({
  ticker,
  score,
  sector,
  industry,
  className = '',
}: Asset360InsightsProps) {
  const [insights, setInsights] = useState<AssetInsight[]>([]);
  const [peers, setPeers] = useState<PeerComparison[]>([]);
  const [news, setNews] = useState<RelatedNews[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate API call
    setIsLoading(true);
    const timer = setTimeout(() => {
      setInsights(generateInsights(ticker, score));
      setPeers(generatePeers(ticker, score));
      setNews(generateNews(ticker));
      setIsLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, [ticker, score]);

  if (isLoading) {
    return (
      <div className={`bg-slate-900/50 border border-slate-800 rounded-2xl p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
          <span className="ml-2 text-sm text-slate-400">Analyse en cours...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* AI Insights */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
        <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Lightbulb size={16} className="text-amber-400" />
          Analyse IA
          <span className="ml-auto text-[10px] text-slate-500 font-normal">
            ProphetIA v2.0
          </span>
        </h3>
        
        <div className="space-y-3">
          {insights.map((insight, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <InsightCard insight={insight} />
            </motion.div>
          ))}
        </div>
        
        {/* Quick Summary */}
        <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
          <p className="text-xs text-slate-400 leading-relaxed">
            <span className="font-semibold text-slate-300">En résumé :</span>{' '}
            {score >= 70 
              ? `${ticker} présente un profil solide avec des fondamentaux robustes et un momentum favorable.`
              : score >= 50
                ? `${ticker} offre un équilibre risque/rendement modéré. Surveillance recommandée.`
                : `${ticker} nécessite une attention particulière. Facteurs de risque élevés.`
            }
          </p>
        </div>
      </div>

      {/* Peer Comparison */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Users size={16} className="text-blue-400" />
            Comparaison {sector || 'secteur'}
          </h3>
          <button className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors">
            Voir tout
          </button>
        </div>
        
        <div className="divide-y divide-slate-800">
          {peers.map((peer, i) => (
            <motion.div
              key={peer.ticker}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Link href={`/asset/${peer.ticker}`}>
                <PeerRow peer={peer} />
              </Link>
            </motion.div>
          ))}
        </div>
        
        {/* Sector Average */}
        <div className="mt-3 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
          <span className="text-slate-500">Moyenne secteur</span>
          <span className="font-semibold text-slate-300">
            {Math.round(peers.reduce((s, p) => s + p.score, score) / (peers.length + 1))}
          </span>
        </div>
      </div>

      {/* Related News */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Newspaper size={16} className="text-purple-400" />
            Actualités liées
          </h3>
          <Link 
            href={`/news?q=${ticker}`}
            className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
          >
            Voir tout <ArrowRight size={10} />
          </Link>
        </div>
        
        <div className="divide-y divide-slate-800">
          {news.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.1 }}
            >
              <NewsRow news={item} />
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
