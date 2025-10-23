-- Migration: Create monitored_posts and monitoring_rules tables
-- Purpose: Enable comment monitoring on all posts (scheduled + imported)
-- Date: 2025-10-19

-- =====================================================
-- Table: monitored_posts
-- Purpose: Track all posts for comment monitoring
-- =====================================================

CREATE TABLE IF NOT EXISTS public.monitored_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    social_account_id UUID NOT NULL REFERENCES public.social_accounts(id) ON DELETE CASCADE,

    -- Platform data
    platform_post_id TEXT NOT NULL,
    platform TEXT NOT NULL CHECK (platform IN ('instagram', 'facebook', 'twitter')),
    caption TEXT,
    media_url TEXT,
    posted_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('scheduled', 'imported', 'manual')),

    -- Monitoring state
    monitoring_enabled BOOLEAN DEFAULT FALSE,
    monitoring_started_at TIMESTAMPTZ,
    monitoring_ends_at TIMESTAMPTZ,
    last_check_at TIMESTAMPTZ,
    next_check_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_user_platform_post UNIQUE (user_id, platform_post_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_monitored_posts_user_id ON public.monitored_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_monitored_posts_social_account_id ON public.monitored_posts(social_account_id);
CREATE INDEX IF NOT EXISTS idx_monitored_posts_monitoring_enabled ON public.monitored_posts(monitoring_enabled);
CREATE INDEX IF NOT EXISTS idx_monitored_posts_next_check ON public.monitored_posts(next_check_at) WHERE monitoring_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_monitored_posts_posted_at ON public.monitored_posts(posted_at DESC);

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION update_monitored_posts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_monitored_posts_updated_at
    BEFORE UPDATE ON public.monitored_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_monitored_posts_updated_at();

-- RLS (Row Level Security)
ALTER TABLE public.monitored_posts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own monitored posts
CREATE POLICY "Users can manage their own monitored posts"
    ON public.monitored_posts
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =====================================================
-- Table: monitoring_rules
-- Purpose: Auto-monitoring rules per user/account
-- =====================================================

CREATE TABLE IF NOT EXISTS public.monitoring_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    social_account_id UUID REFERENCES public.social_accounts(id) ON DELETE CASCADE,

    -- Rules configuration
    auto_monitor_enabled BOOLEAN DEFAULT TRUE,
    auto_monitor_count INTEGER DEFAULT 5 CHECK (auto_monitor_count >= 1 AND auto_monitor_count <= 20),
    monitoring_duration_days INTEGER DEFAULT 7 CHECK (monitoring_duration_days >= 1 AND monitoring_duration_days <= 30),

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints: One rule per user/account combo (null account = global)
    CONSTRAINT unique_user_account_rules UNIQUE (user_id, social_account_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_monitoring_rules_user_id ON public.monitoring_rules(user_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_rules_social_account_id ON public.monitoring_rules(social_account_id);

-- Trigger: auto-update updated_at
CREATE OR REPLACE FUNCTION update_monitoring_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_monitoring_rules_updated_at
    BEFORE UPDATE ON public.monitoring_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_monitoring_rules_updated_at();

-- RLS (Row Level Security)
ALTER TABLE public.monitoring_rules ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own rules
CREATE POLICY "Users can manage their own monitoring rules"
    ON public.monitoring_rules
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- =====================================================
-- Update: Add monitored_post_id to comments table
-- Purpose: Link comments to monitored posts
-- =====================================================

-- Add column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'comments'
        AND column_name = 'monitored_post_id'
    ) THEN
        ALTER TABLE public.comments
        ADD COLUMN monitored_post_id UUID REFERENCES public.monitored_posts(id) ON DELETE CASCADE;

        CREATE INDEX idx_comments_monitored_post_id ON public.comments(monitored_post_id);
    END IF;
END $$;

-- Grant permissions (if using service role)
GRANT ALL ON public.monitored_posts TO postgres, anon, authenticated, service_role;
GRANT ALL ON public.monitoring_rules TO postgres, anon, authenticated, service_role;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully: monitored_posts and monitoring_rules tables created';
END $$;
