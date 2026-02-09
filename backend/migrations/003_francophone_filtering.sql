-- ═══════════════════════════════════════════════════════════════════════════════
-- MarketGPS Francophone Filtering - Database Schema Migration (ADDITIVE)
-- Created: 2026-02-09
--
-- Adds strict filtering columns to news_articles for TOP 20 daily selection.
-- All statements are idempotent (ALTER TABLE IF NOT EXISTS pattern).
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- Add Francophone Filtering Columns to news_articles
-- ═══════════════════════════════════════════════════════════════════════════════

-- Francophone relevance score (0.0-100.0) - calculated from interaction, language,
-- region, recency, and topic relevance components
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS francophone_relevance_score REAL DEFAULT 0.0;

-- Featured flag - manual override to always include in top 20
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS is_featured INTEGER DEFAULT 0;

-- Detailed scoring components (for reporting and debugging)
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS interaction_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS language_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS region_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS recency_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS topic_score REAL DEFAULT 0.0;

-- Daily ranking (1-20 for top 20 articles each day)
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS daily_rank INTEGER DEFAULT NULL;

-- Last score calculation timestamp
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS score_calculated_at TEXT DEFAULT NULL;

-- ═══════════════════════════════════════════════════════════════════════════════
-- Create Indexes for Fast Filtering and Ranking
-- ═══════════════════════════════════════════════════════════════════════════════

-- Index for TOP 20 selection (most critical)
CREATE INDEX IF NOT EXISTS idx_news_articles_relevance ON news_articles(
    francophone_relevance_score DESC,
    published_at DESC
);

-- Index for featured articles
CREATE INDEX IF NOT EXISTS idx_news_articles_featured ON news_articles(
    is_featured DESC,
    francophone_relevance_score DESC
);

-- Index for daily ranking queries
CREATE INDEX IF NOT EXISTS idx_news_articles_daily_rank ON news_articles(
    daily_rank
) WHERE daily_rank IS NOT NULL;

-- Index for component scores (reporting)
CREATE INDEX IF NOT EXISTS idx_news_articles_interaction_score ON news_articles(
    interaction_score DESC
);

-- Index for score calculation timestamp
CREATE INDEX IF NOT EXISTS idx_news_articles_score_calculated ON news_articles(
    score_calculated_at DESC
);

-- Combined index for strict filtering queries
CREATE INDEX IF NOT EXISTS idx_news_articles_strict_filter ON news_articles(
    language,
    status,
    francophone_relevance_score DESC,
    published_at DESC
) WHERE status = 'published' AND language = 'fr';

-- ═══════════════════════════════════════════════════════════════════════════════
-- Create Francophone Daily Top 20 Table
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS francophone_daily_top20 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                        -- YYYY-MM-DD format
    article_id INTEGER NOT NULL,               -- FK to news_articles
    rank INTEGER NOT NULL,                     -- 1-20
    francophone_relevance_score REAL NOT NULL,
    interaction_score REAL,
    language_score REAL,
    region_score REAL,
    recency_score REAL,
    topic_score REAL,
    is_featured INTEGER DEFAULT 0,
    calculated_at TEXT DEFAULT (datetime('now')),

    UNIQUE(date, rank),
    UNIQUE(date, article_id),
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
);

CREATE INDEX IF NOT EXISTS idx_daily_top20_date ON francophone_daily_top20(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_top20_rank ON francophone_daily_top20(date, rank);
CREATE INDEX IF NOT EXISTS idx_daily_top20_article ON francophone_daily_top20(article_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Create Source Metrics Cache Table
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS source_metrics_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_date TEXT NOT NULL,            -- When the metrics were calculated
    source_name TEXT NOT NULL,
    country TEXT,
    language TEXT,
    total_articles INTEGER DEFAULT 0,
    median_interactions REAL DEFAULT 0.0,
    avg_interactions REAL DEFAULT 0.0,
    articles_above_2x_median INTEGER DEFAULT 0,
    calculated_at TEXT DEFAULT (datetime('now')),

    UNIQUE(calculation_date, source_name)
);

CREATE INDEX IF NOT EXISTS idx_source_metrics_date ON source_metrics_cache(calculation_date DESC);
CREATE INDEX IF NOT EXISTS idx_source_metrics_source ON source_metrics_cache(source_name);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Create Francophone Filtering Log
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS francophone_filter_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                        -- Date of filtering
    articles_analyzed INTEGER DEFAULT 0,
    articles_qualified INTEGER DEFAULT 0,      -- Articles > 2x median
    articles_top20 INTEGER DEFAULT 0,          -- Final top 20 count
    featured_count INTEGER DEFAULT 0,          -- Featured articles in top 20
    avg_relevance_score REAL DEFAULT 0.0,
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    status TEXT DEFAULT 'running',             -- 'running', 'success', 'error'
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_filter_log_date ON francophone_filter_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_filter_log_status ON francophone_filter_log(status);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Summary and Documentation
-- ═══════════════════════════════════════════════════════════════════════════════

-- New Schema Components:
--
-- 1. news_articles columns added:
--    - francophone_relevance_score: 0-100, combined relevance score
--    - is_featured: manual override flag
--    - Component scores: interaction, language, region, recency, topic
--    - daily_rank: 1-20 position in daily top 20
--    - score_calculated_at: timestamp of last calculation
--
-- 2. francophone_daily_top20 table:
--    - Stores the daily TOP 20 articles
--    - Immutable historical record
--    - Indexed by date and rank for fast retrieval
--
-- 3. source_metrics_cache table:
--    - Caches source statistics (median, average interactions)
--    - Speeds up filtering without recalculating each time
--    - Indexed by calculation date
--
-- 4. francophone_filter_log table:
--    - Tracks filtering runs and statistics
--    - Useful for monitoring and debugging
--    - Records qualifications and rejections

-- Example query to get today's TOP 20:
-- SELECT * FROM francophone_daily_top20
-- WHERE date = date('now')
-- ORDER BY rank ASC;

-- Example query to get all featured articles:
-- SELECT id, title, francophone_relevance_score, is_featured
-- FROM news_articles
-- WHERE is_featured = 1 AND status = 'published'
-- ORDER BY francophone_relevance_score DESC;
