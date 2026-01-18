-- ═══════════════════════════════════════════════════════════════════════════
-- MarketGPS - Institutional Liquidity & Data Quality Guard
-- Migration: ADD-ONLY (ZERO BREAKING CHANGE)
-- 
-- Purpose: Add institutional-grade scoring columns to scores_latest
-- These columns provide:
--   1) score_institutional: Adjusted score with liquidity/quality penalties
--   2) Liquidity tiers (A/B/C/D) with penalty tracking
--   3) Data quality flags and scores
--   4) Minimum recommended investment horizon
--
-- IMPORTANT: This migration is ADDITIVE ONLY - no existing columns are modified
-- ═══════════════════════════════════════════════════════════════════════════

-- Add institutional score (adjusted version of score_total)
ALTER TABLE scores_latest ADD COLUMN score_institutional REAL DEFAULT NULL;

-- Add liquidity tier classification (A = Institutional, B = Good, C = Limited, D = Illiquid)
ALTER TABLE scores_latest ADD COLUMN liquidity_tier TEXT DEFAULT NULL;

-- Add liquidity penalty applied (0-100 points deducted)
ALTER TABLE scores_latest ADD COLUMN liquidity_penalty REAL DEFAULT 0.0;

-- Add liquidity flag (1 = liquidity concerns, 0 = OK)
ALTER TABLE scores_latest ADD COLUMN liquidity_flag INTEGER DEFAULT 0;

-- Add data quality flag (1 = quality concerns, 0 = OK)
ALTER TABLE scores_latest ADD COLUMN data_quality_flag INTEGER DEFAULT 0;

-- Add data quality score (0-100, higher = better)
ALTER TABLE scores_latest ADD COLUMN data_quality_score REAL DEFAULT NULL;

-- Add stale price flag (1 = stale price detected, 0 = OK)
ALTER TABLE scores_latest ADD COLUMN stale_price_flag INTEGER DEFAULT 0;

-- Add minimum recommended investment horizon (years)
ALTER TABLE scores_latest ADD COLUMN min_recommended_horizon_years INTEGER DEFAULT NULL;

-- Add explanation text for penalties applied
ALTER TABLE scores_latest ADD COLUMN institutional_explanation TEXT DEFAULT NULL;

-- Add ADV_USD for easy reference (also stored in gating_status)
ALTER TABLE scores_latest ADD COLUMN adv_usd REAL DEFAULT NULL;

-- Add market_cap for easy reference
ALTER TABLE scores_latest ADD COLUMN market_cap REAL DEFAULT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- Create indexes for efficient querying
-- ═══════════════════════════════════════════════════════════════════════════

-- Index for institutional score ranking
CREATE INDEX IF NOT EXISTS idx_scores_institutional ON scores_latest(score_institutional DESC)
    WHERE score_institutional IS NOT NULL;

-- Index for liquidity tier filtering
CREATE INDEX IF NOT EXISTS idx_scores_liquidity_tier ON scores_latest(liquidity_tier);

-- Index for flagged assets
CREATE INDEX IF NOT EXISTS idx_scores_liquidity_flag ON scores_latest(liquidity_flag)
    WHERE liquidity_flag = 1;

CREATE INDEX IF NOT EXISTS idx_scores_data_quality_flag ON scores_latest(data_quality_flag)
    WHERE data_quality_flag = 1;

-- Composite index for institutional ranking with scope
CREATE INDEX IF NOT EXISTS idx_scores_scope_institutional 
    ON scores_latest(market_scope, score_institutional DESC)
    WHERE score_institutional IS NOT NULL;

-- ═══════════════════════════════════════════════════════════════════════════
-- Version tracking (optional)
-- ═══════════════════════════════════════════════════════════════════════════

-- Track migration in app_settings
INSERT OR REPLACE INTO app_settings (key, value, updated_at)
VALUES (
    'migration_institutional_guard',
    '{"version": "1.0.0", "applied_at": "' || datetime('now') || '", "status": "complete"}',
    datetime('now')
);
