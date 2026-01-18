-- MarketGPS - Strategy Module Migration
-- Adds tables for institutional strategy templates, user strategies, and simulations
-- Non-destructive: only ADD, never modify existing tables

-- ═══════════════════════════════════════════════════════════════════════════
-- STRATEGY TEMPLATES (predefined institutional strategies)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS strategy_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'balanced',  -- 'defensive', 'balanced', 'growth', 'tactical'
    risk_level TEXT DEFAULT 'moderate', -- 'low', 'moderate', 'high'
    horizon_years INTEGER DEFAULT 10,
    rebalance_frequency TEXT DEFAULT 'annual', -- 'monthly', 'quarterly', 'annual'
    structure_json TEXT NOT NULL,  -- JSON: blocks definition with eligibility rules
    scope TEXT DEFAULT 'US_EU',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_strategy_templates_slug ON strategy_templates(slug);
CREATE INDEX IF NOT EXISTS idx_strategy_templates_category ON strategy_templates(category);

-- ═══════════════════════════════════════════════════════════════════════════
-- TEMPLATE COMPOSITIONS (default instruments per template)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS strategy_template_compositions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    instrument_ticker TEXT NOT NULL,
    block_name TEXT NOT NULL,
    weight REAL NOT NULL,  -- 0.0 to 1.0
    fit_score REAL,  -- Strategy Fit Score 0-100
    rationale TEXT,
    FOREIGN KEY (template_id) REFERENCES strategy_templates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_template_compositions_template ON strategy_template_compositions(template_id);
CREATE INDEX IF NOT EXISTS idx_template_compositions_ticker ON strategy_template_compositions(instrument_ticker);

-- ═══════════════════════════════════════════════════════════════════════════
-- USER STRATEGIES (customized by users)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default',
    template_id INTEGER,  -- NULL if fully custom
    name TEXT NOT NULL,
    description TEXT,
    is_template_copy INTEGER DEFAULT 0,  -- 1 if cloned from template
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (template_id) REFERENCES strategy_templates(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_strategies_user ON user_strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_user_strategies_template ON user_strategies(template_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- USER STRATEGY COMPOSITIONS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS user_strategy_compositions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_strategy_id INTEGER NOT NULL,
    instrument_ticker TEXT NOT NULL,
    block_name TEXT NOT NULL,
    weight REAL NOT NULL,
    fit_score REAL,
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_strategy_id) REFERENCES user_strategies(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_compositions_strategy ON user_strategy_compositions(user_strategy_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- STRATEGY SIMULATIONS (backtest results)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS strategy_simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_strategy_id INTEGER,
    template_id INTEGER,
    composition_hash TEXT NOT NULL,  -- Hash of composition for caching
    period_years INTEGER NOT NULL,
    initial_value REAL DEFAULT 10000,
    rebalance_frequency TEXT DEFAULT 'annual',
    executed_at TEXT DEFAULT (datetime('now')),
    -- Results
    cagr REAL,
    volatility REAL,
    sharpe REAL,
    max_drawdown REAL,
    final_value REAL,
    total_return REAL,
    -- Series storage (monthly downsampled)
    series_json TEXT,  -- JSON array of {date, value} monthly
    series_ref TEXT,   -- Path to parquet file if too large
    -- Metadata
    data_quality_score REAL,
    warnings TEXT,  -- JSON array of warnings
    FOREIGN KEY (user_strategy_id) REFERENCES user_strategies(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES strategy_templates(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_simulations_hash ON strategy_simulations(composition_hash, period_years);
CREATE INDEX IF NOT EXISTS idx_simulations_user ON strategy_simulations(user_strategy_id);

-- ═══════════════════════════════════════════════════════════════════════════
-- INSTRUMENT ELIGIBILITY CACHE (for strategy blocks)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS strategy_instrument_eligibility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_ticker TEXT NOT NULL,
    block_type TEXT NOT NULL,  -- 'defensive', 'growth', 'inflation_hedge', 'crisis_alpha', etc.
    fit_score REAL,
    fit_breakdown TEXT,  -- JSON breakdown
    liquidity_score REAL,
    data_quality_score REAL,
    last_updated TEXT DEFAULT (datetime('now')),
    UNIQUE(instrument_ticker, block_type)
);

CREATE INDEX IF NOT EXISTS idx_eligibility_block ON strategy_instrument_eligibility(block_type);
CREATE INDEX IF NOT EXISTS idx_eligibility_ticker ON strategy_instrument_eligibility(instrument_ticker);

-- ═══════════════════════════════════════════════════════════════════════════
-- SEED DATA: Insert default templates
-- ═══════════════════════════════════════════════════════════════════════════

INSERT OR IGNORE INTO strategy_templates (slug, name, description, category, risk_level, horizon_years, structure_json) VALUES
('barbell', 'Barbell (Haltère)', 
 'Stratégie de Nassim Taleb: 85-90% ultra-safe + 10-15% convexe/crisis alpha. Protection contre les cygnes noirs.',
 'defensive', 'moderate', 10,
 '{"blocks": [
   {"name": "ultra_safe", "label": "Ultra-Safe", "weight": 0.85, "description": "T-Bills, short treasuries, money market", "eligibility": {"max_vol": 5, "max_duration": 2, "min_liquidity": 80}},
   {"name": "crisis_alpha", "label": "Crisis Alpha", "weight": 0.15, "description": "Convexité, tail-risk hedges, managed futures", "eligibility": {"crisis_beta": "negative", "min_convexity": 0.5}}
 ]}'),

('permanent', 'Permanent Portfolio', 
 'Harry Browne: 25% actions, 25% long treasuries, 25% or, 25% cash. Résilience dans tous les régimes économiques.',
 'balanced', 'low', 20,
 '{"blocks": [
   {"name": "growth", "label": "Croissance (Actions)", "weight": 0.25, "description": "Equity exposure for prosperity", "eligibility": {"asset_type": "EQUITY", "min_market_cap": 1000000000}},
   {"name": "deflation", "label": "Déflation (Obligations)", "weight": 0.25, "description": "Long treasuries for deflation protection", "eligibility": {"asset_type": "BOND", "duration": "long"}},
   {"name": "inflation", "label": "Inflation (Or)", "weight": 0.25, "description": "Gold for inflation hedge", "eligibility": {"category": "gold"}},
   {"name": "liquidity", "label": "Liquidité (Cash)", "weight": 0.25, "description": "Cash/T-bills for recession", "eligibility": {"category": "money_market"}}
 ]}'),

('core_satellite', 'Core-Satellite', 
 '70-80% cœur diversifié (indices larges) + 20-30% satellites tactiques. Équilibre entre stabilité et alpha.',
 'balanced', 'moderate', 10,
 '{"blocks": [
   {"name": "core_equity", "label": "Core Equity", "weight": 0.50, "description": "Global diversified equity ETFs", "eligibility": {"asset_type": "ETF", "category": "broad_market", "min_aum": 500000000}},
   {"name": "core_bond", "label": "Core Bond", "weight": 0.25, "description": "Aggregate bond exposure", "eligibility": {"asset_type": "ETF", "category": "aggregate_bond"}},
   {"name": "satellite", "label": "Satellites", "weight": 0.25, "description": "Thematic, factor, or tactical picks", "eligibility": {"min_score": 60}}
 ]}'),

('risk_parity', 'Risk Parity', 
 'Allocation par contribution au risque égale. Réduit la dépendance aux actions.',
 'balanced', 'moderate', 15,
 '{"blocks": [
   {"name": "equities", "label": "Actions", "weight": 0.30, "description": "Global equities", "eligibility": {"asset_type": ["EQUITY", "ETF"], "category": "equity"}},
   {"name": "bonds", "label": "Obligations", "weight": 0.40, "description": "Government and corporate bonds", "eligibility": {"asset_type": ["BOND", "ETF"], "category": "bond"}},
   {"name": "commodities", "label": "Matières Premières", "weight": 0.20, "description": "Diversified commodities", "eligibility": {"asset_type": "ETF", "category": "commodity"}},
   {"name": "alternatives", "label": "Alternatifs", "weight": 0.10, "description": "REITs, infrastructure", "eligibility": {"category": "alternative"}}
 ]}'),

('dividend_growth', 'Dividend Growth', 
 'Focus sur les aristocrates du dividende. Revenus croissants et stabilité.',
 'growth', 'moderate', 15,
 '{"blocks": [
   {"name": "dividend_core", "label": "Dividend Core", "weight": 0.70, "description": "Dividend aristocrats and growers", "eligibility": {"dividend_growth": true, "min_yield": 0.02, "payout_ratio_max": 0.75}},
   {"name": "dividend_growth", "label": "High Growth Dividend", "weight": 0.20, "description": "Faster growing dividends", "eligibility": {"dividend_growth_rate": 0.10}},
   {"name": "yield_boost", "label": "Yield Boost", "weight": 0.10, "description": "Higher yield for income", "eligibility": {"min_yield": 0.04}}
 ]}'),

('factor_investing', 'Factor Investing', 
 'Exposition multi-factorielle: Value, Momentum, Quality, Low Vol.',
 'growth', 'moderate', 10,
 '{"blocks": [
   {"name": "value", "label": "Value", "weight": 0.25, "description": "Undervalued stocks", "eligibility": {"factor": "value"}},
   {"name": "momentum", "label": "Momentum", "weight": 0.25, "description": "Trending stocks", "eligibility": {"factor": "momentum"}},
   {"name": "quality", "label": "Quality", "weight": 0.25, "description": "High quality companies", "eligibility": {"factor": "quality"}},
   {"name": "low_vol", "label": "Low Volatility", "weight": 0.25, "description": "Defensive, low beta", "eligibility": {"factor": "low_vol"}}
 ]}');
