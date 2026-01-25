-- MarketGPS v13.0 - Subscription Tables Migration
-- Stripe as source of truth for billing/access control
-- Systeme.io for marketing only (never decides access)

-- ═══════════════════════════════════════════════════════════════════════════════
-- SUBSCRIPTIONS: Stripe subscription state (mirrors Stripe data)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id TEXT PRIMARY KEY,                    -- Supabase user_id
    stripe_customer_id TEXT,                     -- Stripe customer ID
    stripe_subscription_id TEXT,                 -- Stripe subscription ID
    plan TEXT DEFAULT 'free',                    -- 'free', 'monthly', 'annual'
    status TEXT DEFAULT 'inactive',              -- 'active', 'trialing', 'past_due', 'canceled', 'inactive'
    current_period_start TEXT,                   -- ISO timestamp
    current_period_end TEXT,                     -- ISO timestamp
    cancel_at_period_end INTEGER DEFAULT 0,      -- 1 if scheduled to cancel
    canceled_at TEXT,                            -- When cancellation was requested
    grace_period_end TEXT,                       -- past_due grace period end (48h after payment failure)
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end);

-- ═══════════════════════════════════════════════════════════════════════════════
-- STRIPE_EVENTS: Idempotency tracking for webhooks
-- Prevents duplicate processing of the same event
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS stripe_events (
    event_id TEXT PRIMARY KEY,                   -- Stripe event ID (evt_xxx)
    event_type TEXT NOT NULL,                    -- e.g., 'invoice.paid', 'customer.subscription.updated'
    processed_at TEXT DEFAULT (datetime('now')), -- When we processed it
    payload_hash TEXT,                           -- Optional: hash of payload for verification
    status TEXT DEFAULT 'processed'              -- 'processed', 'failed', 'skipped'
);

CREATE INDEX IF NOT EXISTS idx_stripe_events_type ON stripe_events(event_type);
CREATE INDEX IF NOT EXISTS idx_stripe_events_processed ON stripe_events(processed_at);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SYSTEMEIO_SYNC: Marketing sync queue (non-blocking)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS systemeio_sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    email TEXT NOT NULL,
    action TEXT NOT NULL,                        -- 'tag_add', 'tag_remove', 'contact_create'
    tag_name TEXT,                               -- Tag to apply/remove
    payload_json TEXT,                           -- Full payload as JSON
    status TEXT DEFAULT 'pending',               -- 'pending', 'sent', 'failed', 'skipped'
    attempts INTEGER DEFAULT 0,
    last_attempt_at TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_systemeio_queue_status ON systemeio_sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_systemeio_queue_created ON systemeio_sync_queue(created_at);
