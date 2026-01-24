-- ═══════════════════════════════════════════════════════════════════════════════
-- MarketGPS News Module - Database Schema (ADDITIVE)
-- Created: 2026-01-24
-- 
-- This migration adds tables for the News/Actualités feature.
-- All statements are idempotent (CREATE TABLE IF NOT EXISTS).
-- ═══════════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEWS_SOURCES: Registry of news sources (RSS feeds, APIs, websites)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                      -- Source name (e.g., "TechCabal")
    url TEXT NOT NULL UNIQUE,                -- Base URL of the source
    type TEXT NOT NULL DEFAULT 'rss',        -- 'rss', 'api', 'html'
    rss_url TEXT,                            -- RSS/Atom feed URL if available
    country TEXT,                            -- Country code (NG, ZA, KE, CI, etc.)
    language TEXT DEFAULT 'en',              -- Primary language (en, fr)
    tags TEXT,                               -- JSON array of tags ["fintech", "startup"]
    trust_score REAL DEFAULT 0.7,            -- 0.0 to 1.0 reliability score
    enabled INTEGER DEFAULT 1,               -- 1=active, 0=disabled
    last_fetched_at TEXT,                    -- Last successful fetch
    fetch_error TEXT,                        -- Last error message if any
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_news_sources_enabled ON news_sources(enabled);
CREATE INDEX IF NOT EXISTS idx_news_sources_type ON news_sources(type);
CREATE INDEX IF NOT EXISTS idx_news_sources_country ON news_sources(country);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEWS_RAW_ITEMS: Raw fetched items before processing
-- Stores original content for audit trail and reprocessing
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,              -- FK to news_sources
    url TEXT NOT NULL,                       -- Article URL
    title TEXT,                              -- Original title
    published_at TEXT,                       -- Original publish date
    raw_payload TEXT,                        -- JSON: full raw data (RSS entry, HTML, etc.)
    content_hash TEXT NOT NULL,              -- SHA256 of (url + title) for dedup
    fetched_at TEXT DEFAULT (datetime('now')),
    processed INTEGER DEFAULT 0,             -- 1=processed into article, 0=pending
    process_error TEXT,                      -- Error message if processing failed
    UNIQUE(content_hash)
);

CREATE INDEX IF NOT EXISTS idx_news_raw_source ON news_raw_items(source_id);
CREATE INDEX IF NOT EXISTS idx_news_raw_hash ON news_raw_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_news_raw_processed ON news_raw_items(processed);
CREATE INDEX IF NOT EXISTS idx_news_raw_fetched ON news_raw_items(fetched_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEWS_ARTICLES: Processed and translated articles ready for display
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,               -- URL-friendly slug
    raw_item_id INTEGER,                     -- FK to news_raw_items (optional)
    
    -- Content (French)
    title TEXT NOT NULL,                     -- Title in French
    excerpt TEXT,                            -- Short excerpt (150-200 chars)
    content_md TEXT,                         -- Full content in Markdown
    tldr_json TEXT,                          -- JSON array: ["point1", "point2", "point3"]
    
    -- Metadata
    tags_json TEXT,                          -- JSON array: ["fintech", "nigeria", "funding"]
    country TEXT,                            -- Primary country (NG, ZA, KE, etc.)
    language TEXT DEFAULT 'fr',              -- Content language
    
    -- Media
    image_url TEXT,                          -- Featured image URL
    
    -- Source attribution
    source_name TEXT NOT NULL,               -- Source name for display
    source_url TEXT NOT NULL,                -- Original article URL
    canonical_url TEXT,                      -- Canonical URL if different
    
    -- Timestamps
    published_at TEXT,                       -- Original publish date
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    
    -- Status
    status TEXT DEFAULT 'published',         -- 'draft', 'published', 'archived'
    view_count INTEGER DEFAULT 0,
    
    -- AI Processing (NEW)
    category TEXT,                           -- 'Fintech', 'Finance', 'Startup', etc.
    sentiment TEXT DEFAULT 'neutral',        -- 'positive', 'negative', 'neutral'
    is_ai_processed INTEGER DEFAULT 0        -- 1 if processed by AI, 0 if fallback
);

CREATE INDEX IF NOT EXISTS idx_news_articles_slug ON news_articles(slug);
CREATE INDEX IF NOT EXISTS idx_news_articles_published ON news_articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_country ON news_articles(country);
CREATE INDEX IF NOT EXISTS idx_news_articles_status ON news_articles(status);
CREATE INDEX IF NOT EXISTS idx_news_articles_source ON news_articles(source_name);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEWS_USER_SAVES: User saved/bookmarked articles
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_user_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,                   -- User ID (or 'default' for anonymous)
    article_id INTEGER NOT NULL,             -- FK to news_articles
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_news_saves_user ON news_user_saves(user_id);
CREATE INDEX IF NOT EXISTS idx_news_saves_article ON news_user_saves(article_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NEWS_FETCH_LOG: Track fetch operations for monitoring
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS news_fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,                       -- NULL for full batch
    fetch_type TEXT NOT NULL,                -- 'rss', 'html', 'full'
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    items_fetched INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    items_error INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',           -- 'running', 'success', 'error'
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_news_fetch_log_started ON news_fetch_log(started_at DESC);
