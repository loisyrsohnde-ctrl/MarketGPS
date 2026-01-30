'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Shield,
  AlertTriangle,
  CheckCircle,
  Activity,
} from 'lucide-react';

// =============================================================================
// Types
// =============================================================================

interface PortfolioHealth {
  overall_score: number; // 0-100
  yield_score: number;
  growth_score: number;
  risk_score: number;
  liquidity_score: number;
  trend: 'up' | 'down' | 'stable';
  trend_value: number; // Change vs last period
  alerts_count: number;
}

interface PortfolioHealthRingProps {
  health: PortfolioHealth;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  focusMode?: boolean; // Hide actual values
  className?: string;
}

// =============================================================================
// Utils
// =============================================================================

function getScoreColor(score: number): string {
  if (score >= 75) return '#10b981'; // emerald-500
  if (score >= 50) return '#f59e0b'; // amber-500
  if (score >= 25) return '#f97316'; // orange-500
  return '#ef4444'; // red-500
}

function getScoreLabel(score: number): string {
  if (score >= 80) return 'Excellent';
  if (score >= 65) return 'Bon';
  if (score >= 50) return 'Moyen';
  if (score >= 35) return 'Faible';
  return 'Critique';
}

function getScoreEmoji(score: number): string {
  if (score >= 80) return '🟢';
  if (score >= 65) return '🔵';
  if (score >= 50) return '🟡';
  if (score >= 35) return '🟠';
  return '🔴';
}

// =============================================================================
// SVG Ring Component
// =============================================================================

function AnimatedRing({
  score,
  size,
  strokeWidth,
}: {
  score: number;
  size: number;
  strokeWidth: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(100, Math.max(0, score));
  const offset = circumference - (progress / 100) * circumference;
  const color = getScoreColor(score);

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      {/* Background ring */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        className="text-slate-800"
      />
      
      {/* Progress ring */}
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
      />
      
      {/* Glow effect */}
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth + 4}
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={{ strokeDashoffset: circumference, opacity: 0 }}
        animate={{ strokeDashoffset: offset, opacity: 0.2 }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
        style={{ filter: 'blur(8px)' }}
      />
    </svg>
  );
}

// =============================================================================
// Pillar Indicator
// =============================================================================

function PillarIndicator({
  label,
  value,
  icon,
  focusMode,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  focusMode?: boolean;
}) {
  const color = getScoreColor(value);
  
  return (
    <div className="flex items-center gap-2">
      <div 
        className="w-8 h-8 rounded-lg flex items-center justify-center"
        style={{ backgroundColor: `${color}20` }}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-400 uppercase tracking-wide">{label}</p>
        <div className="flex items-center gap-2">
          {focusMode ? (
            <div className="h-1.5 flex-1 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: color }}
                initial={{ width: 0 }}
                animate={{ width: `${value}%` }}
                transition={{ duration: 1, ease: 'easeOut' }}
              />
            </div>
          ) : (
            <>
              <span className="text-sm font-semibold tabular-nums" style={{ color }}>
                {value}
              </span>
              <span className="text-xs text-slate-500">/100</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// Main Component
// =============================================================================

export default function PortfolioHealthRing({
  health,
  size = 'md',
  showDetails = true,
  focusMode = false,
  className = '',
}: PortfolioHealthRingProps) {
  const dimensions = useMemo(() => {
    switch (size) {
      case 'sm': return { ring: 120, stroke: 8 };
      case 'lg': return { ring: 220, stroke: 14 };
      default: return { ring: 180, stroke: 12 };
    }
  }, [size]);

  const TrendIcon = health.trend === 'up' 
    ? TrendingUp 
    : health.trend === 'down' 
      ? TrendingDown 
      : Minus;

  const trendColor = health.trend === 'up' 
    ? 'text-emerald-400' 
    : health.trend === 'down' 
      ? 'text-red-400' 
      : 'text-slate-400';

  return (
    <div className={`bg-slate-900/50 border border-slate-800 rounded-2xl p-6 ${className}`}>
      <div className="flex flex-col items-center">
        {/* Ring */}
        <div className="relative mb-6">
          <AnimatedRing
            score={health.overall_score}
            size={dimensions.ring}
            strokeWidth={dimensions.stroke}
          />
          
          {/* Center Content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {focusMode ? (
              <>
                <span className="text-2xl mb-1">{getScoreEmoji(health.overall_score)}</span>
                <p className="text-sm font-medium text-slate-300">
                  {getScoreLabel(health.overall_score)}
                </p>
              </>
            ) : (
              <>
                <motion.p
                  className="text-4xl font-bold tabular-nums"
                  style={{ color: getScoreColor(health.overall_score) }}
                  initial={{ scale: 0.5, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.5, duration: 0.5 }}
                >
                  {health.overall_score}
                </motion.p>
                <p className="text-xs text-slate-400 uppercase tracking-wide mt-1">
                  Score Santé
                </p>
              </>
            )}
          </div>
        </div>

        {/* Trend & Alerts */}
        <div className="flex items-center gap-4 mb-6">
          <div className={`flex items-center gap-1 ${trendColor}`}>
            <TrendIcon size={14} />
            <span className="text-xs font-medium">
              {health.trend === 'stable' ? 'Stable' : 
                `${health.trend_value > 0 ? '+' : ''}${health.trend_value}%`}
            </span>
          </div>
          
          {health.alerts_count > 0 && (
            <div className="flex items-center gap-1 text-amber-400">
              <AlertTriangle size={14} />
              <span className="text-xs font-medium">
                {health.alerts_count} alerte{health.alerts_count > 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>

        {/* Pillar Details */}
        {showDetails && (
          <div className="w-full grid grid-cols-2 gap-4">
            <PillarIndicator
              label="Rendement"
              value={health.yield_score}
              icon={<Activity size={14} className="text-emerald-400" />}
              focusMode={focusMode}
            />
            <PillarIndicator
              label="Croissance"
              value={health.growth_score}
              icon={<TrendingUp size={14} className="text-blue-400" />}
              focusMode={focusMode}
            />
            <PillarIndicator
              label="Risque"
              value={health.risk_score}
              icon={<Shield size={14} className="text-purple-400" />}
              focusMode={focusMode}
            />
            <PillarIndicator
              label="Liquidité"
              value={health.liquidity_score}
              icon={<CheckCircle size={14} className="text-cyan-400" />}
              focusMode={focusMode}
            />
          </div>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Export Types
// =============================================================================

export type { PortfolioHealth, PortfolioHealthRingProps };
