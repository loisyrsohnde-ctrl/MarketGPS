-- Migration: Add interactions tracking columns to news_articles
-- Date: February 2026
-- Description: Adds columns to track estimated interactions and virality

-- Add estimated interactions columns
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS estimated_views INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS estimated_shares INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS estimated_likes INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS estimated_comments INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS total_interactions INTEGER DEFAULT 0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS virality_score REAL DEFAULT 0.0;
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS interactions_source TEXT DEFAULT 'estimated';
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS interactions_updated_at TEXT;

-- Create index for querying by virality
CREATE INDEX IF NOT EXISTS idx_news_articles_virality ON news_articles(virality_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_total_interactions ON news_articles(total_interactions DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_importance ON news_articles(importance_level);

-- Create interactions history table for tracking changes over time
CREATE TABLE IF NOT EXISTS news_interactions_history (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    total_interactions INTEGER,
    virality_score REAL,
    source TEXT,
    recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
);

CREATE INDEX IF NOT EXISTS idx_interactions_history_article ON news_interactions_history(article_id);
CREATE INDEX IF NOT EXISTS idx_interactions_history_date ON news_interactions_history(recorded_at);
