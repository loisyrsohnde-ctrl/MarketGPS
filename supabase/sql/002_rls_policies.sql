-- ============================================================================
-- MarketGPS / AfriStocks - Row Level Security Policies
-- ============================================================================
-- Run this AFTER 001_tables.sql in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- ENABLE RLS ON ALL TABLES
-- ============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entitlements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PROFILES POLICIES
-- ============================================================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile (display_name, photo_url only)
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Service role can do anything (for backend/webhooks)
CREATE POLICY "Service role full access to profiles"
    ON public.profiles
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- ENTITLEMENTS POLICIES
-- ============================================================================

-- Users can view their own entitlements
CREATE POLICY "Users can view own entitlements"
    ON public.entitlements
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users CANNOT update their own entitlements (only backend can via service_role)
-- This prevents users from modifying their own plan/status

-- Service role can do anything (for Stripe webhooks)
CREATE POLICY "Service role full access to entitlements"
    ON public.entitlements
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- USAGE LOGS POLICIES
-- ============================================================================

-- Users can view their own usage logs
CREATE POLICY "Users can view own usage logs"
    ON public.usage_logs
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own usage logs
CREATE POLICY "Users can insert own usage logs"
    ON public.usage_logs
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role can do anything
CREATE POLICY "Service role full access to usage logs"
    ON public.usage_logs
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant permissions on tables
GRANT SELECT, UPDATE ON public.profiles TO authenticated;
GRANT SELECT ON public.entitlements TO authenticated;
GRANT SELECT, INSERT ON public.usage_logs TO authenticated;

-- Service role gets full access (used by backend)
GRANT ALL ON public.profiles TO service_role;
GRANT ALL ON public.entitlements TO service_role;
GRANT ALL ON public.usage_logs TO service_role;
