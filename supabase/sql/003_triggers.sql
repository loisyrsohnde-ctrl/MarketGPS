-- ============================================================================
-- MarketGPS / AfriStocks - Triggers and Functions
-- ============================================================================
-- Run this AFTER 002_rls_policies.sql in Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- FUNCTION: Create profile and entitlements on user signup
-- ============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    -- Insert into profiles
    INSERT INTO public.profiles (id, email, display_name, created_at, updated_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
        NOW(),
        NOW()
    );
    
    -- Insert into entitlements with FREE plan
    INSERT INTO public.entitlements (
        user_id,
        plan,
        status,
        daily_requests_limit,
        daily_requests_used,
        daily_reset_at,
        created_at,
        updated_at
    )
    VALUES (
        NEW.id,
        'FREE',
        'active',
        10,  -- FREE users get 10 requests/day
        0,
        NOW(),
        NOW(),
        NOW()
    );
    
    RETURN NEW;
END;
$$;

-- ============================================================================
-- TRIGGER: On auth.users insert, create profile + entitlements
-- ============================================================================
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- FUNCTION: Update updated_at timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- ============================================================================
-- TRIGGERS: Auto-update updated_at on profiles and entitlements
-- ============================================================================
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_entitlements_updated_at ON public.entitlements;
CREATE TRIGGER update_entitlements_updated_at
    BEFORE UPDATE ON public.entitlements
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================================
-- FUNCTION: Reset daily usage counters
-- Call this via Supabase CRON or pg_cron extension
-- ============================================================================
CREATE OR REPLACE FUNCTION public.reset_daily_usage()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    UPDATE public.entitlements
    SET 
        daily_requests_used = 0,
        daily_reset_at = NOW(),
        updated_at = NOW()
    WHERE daily_reset_at < NOW() - INTERVAL '24 hours';
END;
$$;

-- ============================================================================
-- FUNCTION: Increment usage counter
-- ============================================================================
CREATE OR REPLACE FUNCTION public.increment_usage(p_user_id UUID)
RETURNS TABLE(allowed BOOLEAN, remaining INT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_limit INT;
    v_used INT;
    v_reset_at TIMESTAMPTZ;
BEGIN
    -- Get current usage
    SELECT daily_requests_limit, daily_requests_used, daily_reset_at
    INTO v_limit, v_used, v_reset_at
    FROM public.entitlements
    WHERE user_id = p_user_id;
    
    -- Reset if needed (more than 24h since last reset)
    IF v_reset_at < NOW() - INTERVAL '24 hours' THEN
        UPDATE public.entitlements
        SET daily_requests_used = 0, daily_reset_at = NOW()
        WHERE user_id = p_user_id;
        v_used := 0;
    END IF;
    
    -- Check if allowed
    IF v_used >= v_limit THEN
        RETURN QUERY SELECT FALSE, 0;
        RETURN;
    END IF;
    
    -- Increment
    UPDATE public.entitlements
    SET daily_requests_used = daily_requests_used + 1
    WHERE user_id = p_user_id;
    
    RETURN QUERY SELECT TRUE, (v_limit - v_used - 1);
END;
$$;

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION public.increment_usage(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.reset_daily_usage() TO service_role;
