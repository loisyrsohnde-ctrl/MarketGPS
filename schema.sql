-- MarketGPS v12.0 - Multi-Market Global Database Schema (SCOPE-AWARE + AUTH)
-- Supports: US_EU scope (USA, Europe) + AFRICA scope (Nigeria, BRVM, BVMAC, South Africa)
-- New: User authentication, profiles, subscriptions

-- Drop existing tables for clean migration
DROP TABLE IF EXISTS provider_logs;
DROP TABLE IF EXISTS user_interest;
DROP TABLE IF EXISTS scores_history;
DROP TABLE IF EXISTS scores_latest;
DROP TABLE IF EXISTS rotation_state;
DROP TABLE IF EXISTS gating_status;
DROP TABLE IF EXISTS watchlist;
DROP TABLE IF EXISTS jobs_queue;
DROP TABLE IF EXISTS usage_daily;
DROP TABLE IF EXISTS app_settings;
DROP TABLE IF EXISTS user_settings;
DROP TABLE IF EXISTS subscriptions_state;
DROP TABLE IF EXISTS navigation_history;
DROP TABLE IF EXISTS asset_logos;
DROP TABLE IF EXISTS calibration_params;
DROP TABLE IF EXISTS sessions;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS universe;

-- ═══════════════════════════════════════════════════════════════════════════════
-- USERS: Authentication (NEW v12)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,              -- UUID
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email_verified INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE INDEX idx_users_email ON users(email);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER PROFILES: Display name, avatar (NEW v12)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id),
    display_name TEXT,
    avatar_path TEXT,                      -- Local path: data/uploads/avatars/{user_id}.png
    bio TEXT,
    preferred_scope TEXT DEFAULT 'US_EU',
    preferred_asset_types TEXT DEFAULT 'EQUITY,ETF',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SESSIONS: User sessions (NEW v12)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    ip_address TEXT,
    user_agent TEXT
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- UNIVERSE: All known instruments (Multi-Market SCOPE-AWARE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE universe (
    asset_id TEXT PRIMARY KEY,              -- Unique ID: TICKER.EXCHANGE (e.g., AAPL.US, DANGOTE.NG)
    symbol TEXT NOT NULL,                   -- Ticker symbol
    name TEXT,                              -- Full name
    asset_type TEXT NOT NULL DEFAULT 'EQUITY',  -- EQUITY, ETF, CRYPTO, FUTURES, OPTIONS, BOND, INDEX
    market_scope TEXT NOT NULL DEFAULT 'US_EU', -- SCOPE: US_EU or AFRICA
    market_code TEXT NOT NULL DEFAULT 'US', -- US, EU, UK, FR, DE, NG, BRVM, BVMAC, JSE
    exchange_code TEXT DEFAULT 'US',        -- Exchange MIC code
    currency TEXT DEFAULT 'USD',
    country TEXT DEFAULT 'US',
    sector TEXT,
    industry TEXT,
    isin TEXT,                              -- International Securities Identification Number
    active INTEGER DEFAULT 1,
    tier INTEGER DEFAULT 2,                 -- 1=priority, 2=extended, 3=on-demand
    priority_level INTEGER DEFAULT 2,       -- 1=high, 2=normal, 3=low
    data_source TEXT DEFAULT 'EODHD',       -- Data provider
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for fast search and filtering (SCOPE-AWARE)
CREATE INDEX idx_universe_scope ON universe(market_scope);
CREATE INDEX idx_universe_scope_type ON universe(market_scope, asset_type);
CREATE INDEX idx_universe_scope_active ON universe(market_scope, active);
CREATE INDEX idx_universe_symbol ON universe(symbol);
CREATE INDEX idx_universe_name ON universe(name);
CREATE INDEX idx_universe_type ON universe(asset_type);
CREATE INDEX idx_universe_market ON universe(market_code);
CREATE INDEX idx_universe_type_market ON universe(asset_type, market_code);
CREATE INDEX idx_universe_type_active ON universe(asset_type, active);
CREATE INDEX idx_universe_tier ON universe(tier);
CREATE INDEX idx_universe_active ON universe(active);
CREATE INDEX idx_universe_search ON universe(symbol, name, market_code);
CREATE INDEX idx_universe_updated ON universe(updated_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- GATING STATUS: Data quality and eligibility (SCOPE-AWARE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE gating_status (
    asset_id TEXT PRIMARY KEY REFERENCES universe(asset_id),
    market_scope TEXT NOT NULL DEFAULT 'US_EU',  -- SCOPE
    coverage REAL DEFAULT 0.0,
    liquidity REAL DEFAULT 0.0,
    price_min REAL,
    stale_ratio REAL DEFAULT 0.0,
    eligible INTEGER DEFAULT 0,
    reason TEXT,
    data_confidence INTEGER DEFAULT 50,
    last_bar_date TEXT,
    data_available INTEGER DEFAULT 0,
    fx_risk REAL DEFAULT 0.0,               -- Africa: currency risk factor
    liquidity_risk REAL DEFAULT 0.0,        -- Africa: liquidity risk factor
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_gating_scope ON gating_status(market_scope);
CREATE INDEX idx_gating_scope_eligible ON gating_status(market_scope, eligible);
CREATE INDEX idx_gating_eligible ON gating_status(eligible);
CREATE INDEX idx_gating_data_available ON gating_status(data_available);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ROTATION STATE: Refresh scheduling (SCOPE-AWARE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE rotation_state (
    asset_id TEXT PRIMARY KEY REFERENCES universe(asset_id),
    market_scope TEXT NOT NULL DEFAULT 'US_EU',  -- SCOPE
    last_refresh_at TEXT,
    priority_level INTEGER DEFAULT 2,
    in_top50 INTEGER DEFAULT 0,
    cooldown_until TEXT,
    last_error TEXT,
    refresh_count INTEGER DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_rotation_scope ON rotation_state(market_scope);
CREATE INDEX idx_rotation_scope_refresh ON rotation_state(market_scope, last_refresh_at);
CREATE INDEX idx_rotation_refresh ON rotation_state(last_refresh_at);
CREATE INDEX idx_rotation_priority ON rotation_state(priority_level);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SCORES LATEST: Current scores (SCOPE-AWARE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE scores_latest (
    asset_id TEXT PRIMARY KEY REFERENCES universe(asset_id),
    market_scope TEXT NOT NULL DEFAULT 'US_EU',  -- SCOPE
    score_total REAL,
    score_value REAL,
    score_momentum REAL,
    score_safety REAL,
    score_fx_risk REAL,                     -- Africa: FX risk subscore
    score_liquidity_risk REAL,              -- Africa: liquidity risk subscore
    confidence INTEGER DEFAULT 50,
    state_label TEXT DEFAULT 'Équilibre',
    rsi REAL,
    zscore REAL,
    vol_annual REAL,
    max_drawdown REAL,
    sma200 REAL,
    last_price REAL,
    fundamentals_available INTEGER DEFAULT 0,
    json_breakdown TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_scores_scope ON scores_latest(market_scope);
CREATE INDEX idx_scores_scope_total ON scores_latest(market_scope, score_total DESC);
CREATE INDEX idx_scores_total ON scores_latest(score_total DESC);
CREATE INDEX idx_scores_total_notnull ON scores_latest(score_total) WHERE score_total IS NOT NULL;
CREATE INDEX idx_scores_confidence ON scores_latest(confidence);
CREATE INDEX idx_scores_updated ON scores_latest(updated_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SCORES HISTORY: Historical scores for audit
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE scores_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL REFERENCES universe(asset_id),
    market_scope TEXT NOT NULL DEFAULT 'US_EU',
    score_total REAL,
    confidence INTEGER,
    json_breakdown TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_history_asset ON scores_history(asset_id, created_at);
CREATE INDEX idx_history_scope ON scores_history(market_scope, created_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- CALIBRATION PARAMS: Scoring parameters by scope
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE calibration_params (
    market_scope TEXT PRIMARY KEY,          -- US_EU or AFRICA
    weight_momentum REAL DEFAULT 0.40,
    weight_safety REAL DEFAULT 0.30,
    weight_value REAL DEFAULT 0.30,
    weight_fx_risk REAL DEFAULT 0.0,        -- Africa only
    weight_liquidity_risk REAL DEFAULT 0.0, -- Africa only
    rsi_optimal_low REAL DEFAULT 40.0,
    rsi_optimal_high REAL DEFAULT 70.0,
    vol_target_max REAL DEFAULT 30.0,
    drawdown_target_max REAL DEFAULT 20.0,
    min_liquidity_usd REAL DEFAULT 1000000,
    params_json TEXT,                       -- Additional parameters
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Insert default calibration params
INSERT INTO calibration_params (market_scope, weight_momentum, weight_safety, weight_value, weight_fx_risk, weight_liquidity_risk, min_liquidity_usd)
VALUES 
    ('US_EU', 0.40, 0.30, 0.30, 0.0, 0.0, 2000000),
    ('AFRICA', 0.35, 0.25, 0.20, 0.10, 0.10, 100000);

-- ═══════════════════════════════════════════════════════════════════════════════
-- PROVIDER LOGS: API call tracking
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE provider_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    market_scope TEXT DEFAULT 'US_EU',
    endpoint TEXT,
    status TEXT,
    latency_ms INTEGER,
    error TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_logs_provider ON provider_logs(provider, created_at);
CREATE INDEX idx_logs_scope ON provider_logs(market_scope, created_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER INTEREST: Temporary priority boost
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE user_interest (
    asset_id TEXT PRIMARY KEY REFERENCES universe(asset_id),
    market_scope TEXT DEFAULT 'US_EU',
    requested_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    priority_boost REAL DEFAULT 1.0
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- WATCHLIST: User's saved instruments
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    market_code TEXT DEFAULT 'US',
    market_scope TEXT DEFAULT 'US_EU',
    user_id TEXT DEFAULT 'default',
    notes TEXT,
    alert_price_above REAL,
    alert_price_below REAL,
    alert_score_below INTEGER,
    added_at TEXT DEFAULT (datetime('now')),
    UNIQUE(asset_id, user_id)
);

CREATE INDEX idx_watchlist_user ON watchlist(user_id);
CREATE INDEX idx_watchlist_ticker ON watchlist(ticker);
CREATE INDEX idx_watchlist_asset ON watchlist(asset_id);
CREATE INDEX idx_watchlist_scope ON watchlist(market_scope);

-- ═══════════════════════════════════════════════════════════════════════════════
-- JOBS QUEUE: Async job processing (SCOPE-AWARE)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE jobs_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    market_scope TEXT NOT NULL DEFAULT 'US_EU',  -- SCOPE
    payload_json TEXT,
    priority INTEGER DEFAULT 2,
    status TEXT DEFAULT 'PENDING',
    user_id TEXT DEFAULT 'default',
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

CREATE INDEX idx_jobs_status ON jobs_queue(status, priority, created_at);
CREATE INDEX idx_jobs_scope ON jobs_queue(market_scope, status);
CREATE INDEX idx_jobs_pending ON jobs_queue(status) WHERE status = 'PENDING';

-- ═══════════════════════════════════════════════════════════════════════════════
-- USAGE DAILY: Quota tracking
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE usage_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',
    date TEXT NOT NULL,
    calculations_count INTEGER DEFAULT 0,
    calculations_limit INTEGER DEFAULT 200,
    api_calls_count INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'free',
    UNIQUE(user_id, date)
);

CREATE INDEX idx_usage_user_date ON usage_daily(user_id, date);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER SETTINGS: Per-user configuration
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE user_settings (
    user_id TEXT PRIMARY KEY DEFAULT 'default',
    theme TEXT DEFAULT 'dark',
    language TEXT DEFAULT 'fr',
    default_market TEXT DEFAULT 'US',
    default_scope TEXT DEFAULT 'US_EU',     -- Default scope to show
    default_top_n INTEGER DEFAULT 30,
    refresh_interval INTEGER DEFAULT 15,
    show_tutorial INTEGER DEFAULT 1,
    notifications_enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SUBSCRIPTIONS: User subscription info (UPDATED v12)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE subscriptions_state (
    user_id TEXT PRIMARY KEY,              -- FK to users or 'default'
    plan TEXT DEFAULT 'free',              -- free, monthly_9_99, yearly_50
    status TEXT DEFAULT 'inactive',        -- active, inactive, cancelled, expired
    daily_quota_used INTEGER DEFAULT 0,
    daily_quota_limit INTEGER DEFAULT 3,   -- FREE: 3, PRO: 200
    markets_access TEXT DEFAULT 'US,EU',   -- Comma-separated list
    scopes_access TEXT DEFAULT 'US_EU',    -- Comma-separated scopes
    features_json TEXT,
    started_at TEXT,
    renews_at TEXT,                        -- Next renewal date
    expires_at TEXT,
    stripe_customer_id TEXT,               -- For future Stripe integration
    stripe_subscription_id TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_subscriptions_status ON subscriptions_state(status);
CREATE INDEX idx_subscriptions_plan ON subscriptions_state(plan);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NAVIGATION HISTORY
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE navigation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT DEFAULT 'default',
    page TEXT NOT NULL,
    params_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_nav_user ON navigation_history(user_id, created_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ASSET LOGOS: Cached logo paths
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE asset_logos (
    asset_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    logo_path TEXT,
    logo_url TEXT,
    fetched_at TEXT DEFAULT (datetime('now')),
    fetch_status TEXT DEFAULT 'pending'
);

CREATE INDEX idx_logos_ticker ON asset_logos(ticker);
CREATE INDEX idx_logos_status ON asset_logos(fetch_status);

-- ═══════════════════════════════════════════════════════════════════════════════
-- APP SETTINGS: Global application configuration
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Insert default settings
INSERT OR REPLACE INTO app_settings (key, value) VALUES 
    ('pro_mode_enabled', 'false'),
    ('default_top_n', '50'),
    ('refresh_interval_minutes', '15'),
    ('tier1_size', '100'),
    ('tier2_batch_size', '50'),
    ('daily_quota_free', '10'),
    ('daily_quota_pro', '200'),
    ('daily_quota_premium', '2000'),
    ('enabled_markets', 'US,EU,NG,BRVM,JSE'),
    ('enabled_scopes', 'US_EU,AFRICA'),
    ('last_universe_update_us_eu', ''),
    ('last_universe_update_africa', ''),
    ('last_gating_run_us_eu', ''),
    ('last_gating_run_africa', ''),
    ('last_rotation_run_us_eu', ''),
    ('last_rotation_run_africa', '');

-- ═══════════════════════════════════════════════════════════════════════════════
-- JOB RUNS: Pipeline execution tracking (NEW - Production Grade)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS job_runs (
    run_id TEXT PRIMARY KEY,                  -- UUID for the job run
    market_scope TEXT NOT NULL,               -- US_EU or AFRICA
    job_type TEXT NOT NULL,                   -- gating, rotation, scoring, universe
    mode TEXT DEFAULT 'daily_full',           -- daily_full, hourly_overlay, on_demand
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    status TEXT DEFAULT 'running',            -- running, staging, success, failed, cancelled
    assets_processed INTEGER DEFAULT 0,
    assets_success INTEGER DEFAULT 0,
    assets_failed INTEGER DEFAULT 0,
    duration_seconds REAL,
    stats_json TEXT,                          -- Additional metrics as JSON
    error TEXT,
    created_by TEXT DEFAULT 'scheduler'       -- scheduler, manual, api
);

CREATE INDEX IF NOT EXISTS idx_job_runs_scope ON job_runs(market_scope);
CREATE INDEX IF NOT EXISTS idx_job_runs_type ON job_runs(job_type, market_scope);
CREATE INDEX IF NOT EXISTS idx_job_runs_status ON job_runs(status);
CREATE INDEX IF NOT EXISTS idx_job_runs_started ON job_runs(started_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SCORES STAGING: Staging table for atomic publish (NEW - Production Grade)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS scores_staging (
    run_id TEXT NOT NULL,                     -- FK to job_runs
    asset_id TEXT NOT NULL,
    market_scope TEXT NOT NULL DEFAULT 'US_EU',
    score_total REAL,
    score_value REAL,
    score_momentum REAL,
    score_safety REAL,
    score_fx_risk REAL,                       -- Africa only
    score_liquidity_risk REAL,                -- Africa only
    confidence INTEGER DEFAULT 50,
    state_label TEXT DEFAULT 'Équilibre',
    rsi REAL,
    zscore REAL,
    vol_annual REAL,
    max_drawdown REAL,
    sma200 REAL,
    last_price REAL,
    fundamentals_available INTEGER DEFAULT 0,
    json_breakdown TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_scores_staging_run ON scores_staging(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_staging_scope ON scores_staging(market_scope, asset_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- GATING STATUS STAGING: Staging table for atomic publish (NEW - Production Grade)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gating_status_staging (
    run_id TEXT NOT NULL,                     -- FK to job_runs
    asset_id TEXT NOT NULL,
    market_scope TEXT NOT NULL DEFAULT 'US_EU',
    coverage REAL DEFAULT 0.0,
    liquidity REAL DEFAULT 0.0,
    price_min REAL,
    stale_ratio REAL DEFAULT 0.0,
    eligible INTEGER DEFAULT 0,
    reason TEXT,
    data_confidence INTEGER DEFAULT 50,
    last_bar_date TEXT,
    data_available INTEGER DEFAULT 0,
    fx_risk REAL DEFAULT 0.0,                 -- Africa: currency risk factor
    liquidity_risk REAL DEFAULT 0.0,          -- Africa: liquidity risk factor
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_gating_staging_run ON gating_status_staging(run_id);
CREATE INDEX IF NOT EXISTS idx_gating_staging_scope ON gating_status_staging(market_scope, asset_id);

-- Insert default user settings
INSERT OR REPLACE INTO user_settings (user_id) VALUES ('default');

-- Insert default subscription state (for anonymous/demo users)
INSERT OR REPLACE INTO subscriptions_state (user_id, plan, status, daily_quota_limit) 
VALUES ('default', 'free', 'active', 3);

-- Insert demo user for testing (password: demo123)
INSERT OR REPLACE INTO users (user_id, email, password_hash) 
VALUES ('demo-user-001', 'demo@marketgps.io', 'pbkdf2:sha256:260000$demo$demohash');

INSERT OR REPLACE INTO user_profiles (user_id, display_name) 
VALUES ('demo-user-001', 'Demo User');

INSERT OR REPLACE INTO subscriptions_state (user_id, plan, status, daily_quota_limit, scopes_access)
VALUES ('demo-user-001', 'monthly_9_99', 'active', 200, 'US_EU,AFRICA');
