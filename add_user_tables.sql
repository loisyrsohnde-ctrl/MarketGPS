-- Add missing user management tables to MarketGPS schema
-- These tables are needed for the user settings page

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER SECURITY: Password and security info
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_security (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id),
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER PREFERENCES: Notification and display preferences
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id),
    email_notifications INTEGER DEFAULT 1,
    market_alerts INTEGER DEFAULT 1,
    price_alerts INTEGER DEFAULT 1,
    portfolio_updates INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER ENTITLEMENTS: Plan and quota info
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_entitlements (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id),
    plan TEXT DEFAULT 'FREE',                 -- FREE, MONTHLY, YEARLY
    status TEXT DEFAULT 'active',             -- active, inactive, cancelled
    daily_requests_limit INTEGER DEFAULT 10,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USER SESSIONS: Session tracking (different from sessions table - for API)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_sessions (
    user_id TEXT NOT NULL REFERENCES users(user_id),
    session_token TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- Initialize default data for demo user
-- ═══════════════════════════════════════════════════════════════════════════════

INSERT OR REPLACE INTO user_security (user_id, password_hash)
VALUES ('default_user', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');

INSERT OR REPLACE INTO user_preferences (user_id, email_notifications, market_alerts, price_alerts, portfolio_updates)
VALUES ('default_user', 1, 1, 1, 1);

INSERT OR REPLACE INTO user_entitlements (user_id, plan, status, daily_requests_limit)
VALUES ('default_user', 'FREE', 'active', 10);

-- Also for demo user if exists
INSERT OR IGNORE INTO user_security (user_id, password_hash)
VALUES ('demo-user-001', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');

INSERT OR IGNORE INTO user_preferences (user_id, email_notifications, market_alerts, price_alerts, portfolio_updates)
VALUES ('demo-user-001', 1, 1, 1, 1);

INSERT OR IGNORE INTO user_entitlements (user_id, plan, status, daily_requests_limit)
VALUES ('demo-user-001', 'FREE', 'active', 10);
