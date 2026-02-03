-- Migration: Add viral news system tables
-- Created: 2024
-- Description: Adds tables for viral news detection and video script generation

-- Table pour les statistiques de source (moyennes d'interactions)
CREATE TABLE IF NOT EXISTS news_source_stats (
    source_id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    region TEXT,
    language TEXT,
    avg_interactions REAL DEFAULT 0,
    median_interactions REAL DEFAULT 0,
    total_articles INTEGER DEFAULT 0,
    last_calculated TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_name)
);

-- Table pour les scripts vidéo
CREATE TABLE IF NOT EXISTS video_scripts (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,
    hook TEXT,
    script_text TEXT NOT NULL,
    word_count INTEGER,
    estimated_duration_seconds INTEGER,
    sources_json TEXT,
    key_facts_json TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES news_articles(id)
);

-- Index pour recherche rapide sur video_scripts
CREATE INDEX IF NOT EXISTS idx_video_scripts_status ON video_scripts(status);
CREATE INDEX IF NOT EXISTS idx_video_scripts_article ON video_scripts(article_id);
CREATE INDEX IF NOT EXISTS idx_video_scripts_created ON video_scripts(created_at DESC);

-- Ajouter colonne estimated_interactions à news_articles si elle n'existe pas
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so this is handled in Python code

-- Index pour améliorer les requêtes de viralité
CREATE INDEX IF NOT EXISTS idx_news_articles_interactions ON news_articles(total_interactions DESC);
CREATE INDEX IF NOT EXISTS idx_news_articles_source_date ON news_articles(source_name, created_at DESC);
