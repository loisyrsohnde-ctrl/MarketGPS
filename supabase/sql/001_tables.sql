-- ============================================================================
-- MarketGPS / AfriStocks - Supabase Tables
-- ============================================================================
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- PROFILES TABLE
-- Stores user profile information, linked to auth.users
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    display_name TEXT,
    photo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- ============================================================================
-- ENTITLEMENTS TABLE
-- Stores subscription/plan information for each user
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.entitlements (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    plan TEXT NOT NULL DEFAULT 'FREE' CHECK (plan IN ('FREE', 'MONTHLY', 'YEARLY')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'canceled', 'inactive', 'trialing')),
    current_period_end TIMESTAMPTZ,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    daily_requests_used INT DEFAULT 0,
    daily_requests_limit INT DEFAULT 10,  -- FREE users get 10/day, PAID get 200/day
    daily_reset_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Stripe lookups
CREATE INDEX IF NOT EXISTS idx_entitlements_stripe_customer ON public.entitlements(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_entitlements_stripe_subscription ON public.entitlements(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_entitlements_plan ON public.entitlements(plan);
CREATE INDEX IF NOT EXISTS idx_entitlements_status ON public.entitlements(status);

-- ============================================================================
-- USAGE LOGS TABLE (optional - for detailed tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user ON public.usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created ON public.usage_logs(created_at);

-- ============================================================================
-- COMMENTS
-- ============================================================================
COMMENT ON TABLE public.profiles IS 'User profile information, synced from auth.users';
COMMENT ON TABLE public.entitlements IS 'Subscription and plan entitlements for each user';
COMMENT ON TABLE public.usage_logs IS 'Optional usage tracking for analytics';

COMMENT ON COLUMN public.entitlements.plan IS 'FREE, MONTHLY, or YEARLY subscription plan';
COMMENT ON COLUMN public.entitlements.status IS 'active, past_due, canceled, inactive, or trialing';
COMMENT ON COLUMN public.entitlements.daily_requests_limit IS 'FREE=10, PAID=200';
