-- ═══════════════════════════════════════════════════════════════════════════
-- MarketGPS - Barbell Portfolio Tables
-- Migration: add_barbell_tables.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- Barbell Portfolios (saved user portfolios)
CREATE TABLE IF NOT EXISTS barbell_portfolios (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(8)))),
    user_id TEXT NOT NULL DEFAULT 'default_user',
    name TEXT NOT NULL,
    description TEXT,
    risk_profile TEXT NOT NULL DEFAULT 'moderate',  -- conservative, moderate, aggressive
    market_scope TEXT NOT NULL DEFAULT 'US_EU',
    core_ratio REAL NOT NULL DEFAULT 0.75,
    satellite_ratio REAL NOT NULL DEFAULT 0.25,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Portfolio Items (assets in portfolio)
CREATE TABLE IF NOT EXISTS barbell_portfolio_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id TEXT NOT NULL,
    asset_id TEXT NOT NULL,
    block TEXT NOT NULL CHECK (block IN ('core', 'satellite')),
    weight REAL NOT NULL CHECK (weight >= 0 AND weight <= 1),
    notes TEXT,
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (portfolio_id) REFERENCES barbell_portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, asset_id)
);

-- Simulation Cache (to avoid re-computing)
CREATE TABLE IF NOT EXISTS barbell_simulation_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    composition_hash TEXT NOT NULL UNIQUE,
    period_years INTEGER NOT NULL,
    rebalance_frequency TEXT NOT NULL,
    initial_capital REAL NOT NULL,
    result_json TEXT NOT NULL,  -- JSON blob with full results
    computed_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,  -- Optional TTL
    data_quality_score REAL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_barbell_portfolios_user ON barbell_portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_barbell_portfolios_active ON barbell_portfolios(is_active);
CREATE INDEX IF NOT EXISTS idx_barbell_items_portfolio ON barbell_portfolio_items(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_barbell_cache_hash ON barbell_simulation_cache(composition_hash);

-- Insert default portfolios for demo
INSERT OR IGNORE INTO barbell_portfolios (id, user_id, name, description, risk_profile, core_ratio, satellite_ratio)
VALUES 
    ('demo_conservative', 'default_user', 'Conservateur Défaut', 'Allocation 85/15 défensive', 'conservative', 0.85, 0.15),
    ('demo_moderate', 'default_user', 'Modéré Défaut', 'Allocation 75/25 équilibrée', 'moderate', 0.75, 0.25),
    ('demo_aggressive', 'default_user', 'Dynamique Défaut', 'Allocation 65/35 croissance', 'aggressive', 0.65, 0.35);
