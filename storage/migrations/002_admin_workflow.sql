-- Migration 002: Admin Editorial Workflow & Activity Log
-- Adds editorial workflow columns to news_articles and creates admin_activity_log

-- Editorial workflow columns on news_articles
ALTER TABLE news_articles ADD COLUMN editorial_status TEXT DEFAULT 'pending';
ALTER TABLE news_articles ADD COLUMN french_content_md TEXT;
ALTER TABLE news_articles ADD COLUMN editorial_notes TEXT;
ALTER TABLE news_articles ADD COLUMN approved_at TEXT;
ALTER TABLE news_articles ADD COLUMN approved_by TEXT;

-- Admin activity log table
CREATE TABLE IF NOT EXISTS admin_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id TEXT DEFAULT 'admin',
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details TEXT,
    changes_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_log_action ON admin_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_log_resource ON admin_activity_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON admin_activity_log(created_at);

-- Admin settings table
CREATE TABLE IF NOT EXISTS admin_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for editorial workflow
CREATE INDEX IF NOT EXISTS idx_news_editorial_status ON news_articles(editorial_status);
CREATE INDEX IF NOT EXISTS idx_news_approved_at ON news_articles(approved_at);

-- FTS table for global search (if not exists)
-- Note: SQLite FTS5 for full-text search across articles
CREATE VIRTUAL TABLE IF NOT EXISTS news_articles_fts USING fts5(
    title, content_md, summary, source_name, country,
    content='news_articles',
    content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS news_articles_ai AFTER INSERT ON news_articles BEGIN
    INSERT INTO news_articles_fts(rowid, title, content_md, summary, source_name, country)
    VALUES (new.id, new.title, new.content_md, new.summary, new.source_name, new.country);
END;

CREATE TRIGGER IF NOT EXISTS news_articles_ad AFTER DELETE ON news_articles BEGIN
    INSERT INTO news_articles_fts(news_articles_fts, rowid, title, content_md, summary, source_name, country)
    VALUES ('delete', old.id, old.title, old.content_md, old.summary, old.source_name, old.country);
END;

CREATE TRIGGER IF NOT EXISTS news_articles_au AFTER UPDATE ON news_articles BEGIN
    INSERT INTO news_articles_fts(news_articles_fts, rowid, title, content_md, summary, source_name, country)
    VALUES ('delete', old.id, old.title, old.content_md, old.summary, old.source_name, old.country);
    INSERT INTO news_articles_fts(rowid, title, content_md, summary, source_name, country)
    VALUES (new.id, new.title, new.content_md, new.summary, new.source_name, new.country);
END;
