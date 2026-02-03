-- ═══════════════════════════════════════════════════════════════════════════
-- MarketGPS Gamification System - Database Schema
-- ═══════════════════════════════════════════════════════════════════════════

-- User Gamification Progress
CREATE TABLE IF NOT EXISTS user_gamification (
    user_id TEXT PRIMARY KEY,
    total_points INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- User Earned Badges
CREATE TABLE IF NOT EXISTS user_badges (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    badge_id TEXT NOT NULL,
    earned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
);

-- User Objectives (Daily, Weekly, etc.)
CREATE TABLE IF NOT EXISTS user_objectives (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    objective_type TEXT NOT NULL DEFAULT 'weekly',  -- daily, weekly, monthly, special
    title TEXT NOT NULL,
    description TEXT,
    action TEXT NOT NULL,  -- Action type to track
    target INTEGER NOT NULL,
    current INTEGER DEFAULT 0,
    points_reward INTEGER NOT NULL,
    expires_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
);

-- User Actions (for tracking and analytics)
CREATE TABLE IF NOT EXISTS user_actions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    metadata_json TEXT,
    points_earned INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_gamification(user_id) ON DELETE CASCADE
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_user_badges_badge_id ON user_badges(badge_id);
CREATE INDEX IF NOT EXISTS idx_user_objectives_user_id ON user_objectives(user_id);
CREATE INDEX IF NOT EXISTS idx_user_objectives_type ON user_objectives(objective_type);
CREATE INDEX IF NOT EXISTS idx_user_objectives_completed ON user_objectives(completed_at);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id ON user_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_actions_action ON user_actions(action);
CREATE INDEX IF NOT EXISTS idx_user_actions_date ON user_actions(created_at);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_date ON user_actions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_gamification_points ON user_gamification(total_points DESC);
CREATE INDEX IF NOT EXISTS idx_user_gamification_level ON user_gamification(current_level DESC);
