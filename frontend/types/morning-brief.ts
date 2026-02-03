// ═══════════════════════════════════════════════════════════════════════════
// MORNING BRIEF TYPES
// Type definitions for the Morning Brief Dashboard
// ═══════════════════════════════════════════════════════════════════════════

import type { Asset, WatchlistItem } from './index';

// ─────────────────────────────────────────────────────────────────────────────
// Alert Types
// ─────────────────────────────────────────────────────────────────────────────

export type AlertType = 'price' | 'score' | 'news' | 'opportunity' | 'risk';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  assetId?: string;
  ticker?: string;
  isRead: boolean;
  createdAt: string;
  metadata?: {
    oldValue?: number;
    newValue?: number;
    change?: number;
    changePercent?: number;
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// News Types
// ─────────────────────────────────────────────────────────────────────────────

export type NewsSentiment = 'positive' | 'negative' | 'neutral';

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  sentiment: NewsSentiment;
  tickers: string[];
  isBreaking: boolean;
  importance: 'low' | 'medium' | 'high';
  publishedAt: string;
  imageUrl?: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Opportunity Types
// ─────────────────────────────────────────────────────────────────────────────

export type OpportunityType = 'high_score' | 'trending' | 'undervalued' | 'breakout';

export interface Opportunity {
  asset: Asset;
  type: OpportunityType;
  scoreImprovement?: number;
  trend?: 'up' | 'down' | 'stable';
  confidence: number;
  reason: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Gamification Types
// ─────────────────────────────────────────────────────────────────────────────

export type GamificationLevel = 'novice' | 'apprentice' | 'analyst' | 'expert' | 'legend';

export interface Objective {
  id: string;
  title: string;
  description: string;
  progress: number; // 0-100
  target: number;
  category: 'portfolio' | 'learning' | 'engagement' | 'diversity';
  reward: number; // points
  isCompleted: boolean;
  dueDate?: string;
}

export interface GamificationStatus {
  level: GamificationLevel;
  points: number;
  weeklyPoints: number;
  weeklyTarget: number;
  objectives: Objective[];
  streakDays: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Portfolio Performance Types
// ─────────────────────────────────────────────────────────────────────────────

export interface PortfolioMetrics {
  totalValue: number;
  dayChange: number;
  dayChangePercent: number;
  weekChange: number;
  weekChangePercent: number;
  monthChange: number;
  monthChangePercent: number;
  averageScore: number;
  topGainers: Asset[];
  topLosers: Asset[];
  diversificationScore: number;
  riskScore: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Morning Brief Data
// ─────────────────────────────────────────────────────────────────────────────

export interface MorningBriefData {
  greeting: {
    firstName: string;
    timeOfDay: 'morning' | 'afternoon' | 'evening';
  };
  portfolio: PortfolioMetrics;
  alerts: {
    unreadCount: number;
    recent: Alert[];
    criticalCount: number;
  };
  opportunities: Opportunity[];
  news: {
    breaking: NewsItem[];
    important: NewsItem[];
  };
  gamification: GamificationStatus;
  lastUpdated: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook Response Type
// ─────────────────────────────────────────────────────────────────────────────

export interface UseMorningBriefResponse {
  data: MorningBriefData | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}
