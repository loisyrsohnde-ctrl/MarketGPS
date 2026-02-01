-- ═══════════════════════════════════════════════════════════════════════════════
-- MarketGPS News Module - Engagement & Notifications Schema (ADDITIVE)
-- Created: 2026-02-01
--
-- This migration adds engagement scoring and notification support.
-- All statements are idempotent (IF NOT EXISTS).
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- STEP 1: Add engagement columns to news_articles
-- ═══════════════════════════════════════════════════════════════════════════════

-- Engagement score (0.0 to 1.0) - calculated from multiple signals
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we use a workaround
CREATE TABLE IF NOT EXISTS _news_migration_check (id INTEGER PRIMARY KEY);

-- Add columns if they don't exist (SQLite workaround using INSERT OR IGNORE pattern)
-- We'll handle this in Python code instead

-- ═══════════════════════════════════════════════════════════════════════════════
-- STEP 2: News Alerts Table - for Breaking News notifications
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,                -- FK to news_articles
    alert_type TEXT NOT NULL,                   -- 'breaking', 'high_importance', 'trending'
    title TEXT NOT NULL,                        -- Alert title
    message TEXT,                               -- Alert message/excerpt
    importance_score REAL DEFAULT 0.0,          -- Score that triggered the alert
    sent_count INTEGER DEFAULT 0,               -- Number of users notified
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
);

CREATE INDEX IF NOT EXISTS idx_news_alerts_article ON news_alerts(article_id);
CREATE INDEX IF NOT EXISTS idx_news_alerts_type ON news_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_news_alerts_created ON news_alerts(created_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STEP 3: User Alert Preferences - per-user notification settings
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_news_alert_prefs (
    user_id TEXT PRIMARY KEY,
    receive_breaking_news INTEGER DEFAULT 1,     -- 1=yes, 0=no
    receive_high_importance INTEGER DEFAULT 1,   -- 1=yes, 0=no
    receive_trending INTEGER DEFAULT 0,          -- 1=yes, 0=no (off by default)
    email_enabled INTEGER DEFAULT 1,             -- 1=send emails, 0=in-app only
    min_importance_score REAL DEFAULT 0.7,       -- Minimum score to notify
    preferred_regions TEXT,                      -- JSON array: ["WEST", "PAN"]
    preferred_countries TEXT,                    -- JSON array: ["NG", "KE", "CI"]
    quiet_hours_start TEXT,                      -- e.g., "22:00"
    quiet_hours_end TEXT,                        -- e.g., "07:00"
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STEP 4: User Alert History - track sent notifications
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_news_alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    alert_id INTEGER NOT NULL,                   -- FK to news_alerts
    channel TEXT NOT NULL,                       -- 'email', 'in_app', 'push'
    status TEXT DEFAULT 'pending',               -- 'pending', 'sent', 'read', 'failed'
    sent_at TEXT,
    read_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (alert_id) REFERENCES news_alerts(id)
);

CREATE INDEX IF NOT EXISTS idx_alert_history_user ON user_news_alert_history(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert ON user_news_alert_history(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_history_status ON user_news_alert_history(status);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STEP 5: Indexes for engagement-based queries
-- ═══════════════════════════════════════════════════════════════════════════════
-- These will be created after the columns are added via Python migration
