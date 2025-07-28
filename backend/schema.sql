-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE social_platform AS ENUM ('facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'whatsapp');


-- Users table
CREATE TABLE users (
    id uuid references auth.users not null primary key,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
/**
* This trigger automatically creates a user entry when a new user signs up via Supabase Auth.
*/
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email, full_name)
  values (
    new.id, 
    new.email, -- Utilise directement new.email
    new.raw_user_meta_data->>'full_name'-- Peut être NULL
  );
  return new;
end;
$$;

create OR REPLACE trigger on_auth_user_created
  after insert on auth.users
  for each row
    execute procedure public.handle_new_user();

-- Social accounts table
CREATE TABLE social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform social_platform NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    profile_url VARCHAR(500),
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(platform, account_id),
    UNIQUE(user_id, platform)
);

-- Content table for social media posts
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    status VARCHAR(50) DEFAULT 'draft',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    media_url VARCHAR(500),
    social_account_id UUID NOT NULL REFERENCES social_accounts(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE content
    ADD CONSTRAINT chk_schedule_publish
    CHECK (published_at IS NULL OR scheduled_at IS NULL OR scheduled_at <= published_at);

-- Analytics table for storing engagement metrics
CREATE TABLE analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    platform social_platform NOT NULL,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    raw_metrics JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);



-- -- AI insights table for storing AI-generated content and insights
-- CREATE TABLE ai_insights (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
--     title VARCHAR(255) NOT NULL,
--     content TEXT NOT NULL,
--     confidence_score DECIMAL(3,2),
--     metadata JSONB,
--     embedding vector(1536), -- For OpenAI embeddings
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );

-- ALTER TABLE ai_insights
--     ADD CONSTRAINT chk_confidence_score CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));

-- CREATE INDEX idx_ai_insights_embedding ON ai_insights USING hnsw (embedding vector_cosine_ops);

-- Indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX idx_social_accounts_platform ON social_accounts(platform);
CREATE INDEX idx_content_social_account_id ON content(social_account_id);
CREATE INDEX idx_content_status ON content(status);
CREATE INDEX idx_content_scheduled_at ON content(scheduled_at);
CREATE INDEX idx_analytics_content_id ON analytics(content_id);
CREATE INDEX idx_analytics_platform ON analytics(platform);
CREATE INDEX idx_analytics_recorded_at ON analytics(recorded_at);
-- CREATE INDEX idx_ai_insights_user_id ON ai_insights(user_id);
-- CREATE INDEX idx_ai_insights_type ON ai_insights(insight_type);

-- Analytics history table (time-series)
CREATE TABLE analytics_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_id UUID NOT NULL REFERENCES content(id) ON DELETE CASCADE,
    platform social_platform NOT NULL,
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,2) DEFAULT 0,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    raw_metrics JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analytics_history
CREATE INDEX idx_analytics_history_content_id ON analytics_history(content_id);
CREATE INDEX idx_analytics_history_recorded_at ON analytics_history(recorded_at);
CREATE INDEX idx_analytics_history_user_id ON analytics_history(user_id);

-- Enable RLS
ALTER TABLE analytics_history ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY "Users manage their analytics history" ON analytics_history FOR ALL USING (auth.uid() = user_id);
-- Basic RLS policies (can be customized based on requirements)
CREATE POLICY "Users can view their own profile" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update their own profile" ON users FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users own their accounts" ON social_accounts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage their accounts" ON social_accounts FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view their content" ON content FOR SELECT USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        WHERE sa.id = social_account_id
    )
);
CREATE POLICY "Users can manage their content" ON content FOR ALL USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        WHERE sa.id = social_account_id
    )
); 

-- RLS policies for analytics table
CREATE POLICY "Users can view their analytics" ON analytics FOR SELECT USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        JOIN content c ON c.social_account_id = sa.id 
        WHERE c.id = content_id
    )
);
CREATE POLICY "Users can manage their analytics" ON analytics FOR ALL USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        JOIN content c ON c.social_account_id = sa.id 
        WHERE c.id = content_id
    )
);

-- -- RLS policies for ai_insights table
-- CREATE POLICY "Users can view their ai_insights" ON ai_insights FOR SELECT USING (auth.uid() = user_id);
-- CREATE POLICY "Users can manage their ai_insights" ON ai_insights FOR ALL USING (auth.uid() = user_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_social_accounts_updated_at BEFORE UPDATE ON social_accounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_content_updated_at BEFORE UPDATE ON content FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analytics_updated_at BEFORE UPDATE ON analytics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



-- Trigger to auto-set published_at when status devient 'published'
CREATE OR REPLACE FUNCTION set_published_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'published' AND NEW.published_at IS NULL THEN
        NEW.published_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_set_published_at BEFORE UPDATE ON content
FOR EACH ROW WHEN (NEW.status <> OLD.status)
EXECUTE FUNCTION set_published_at();



-- Row Level Security (RLS) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE content ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;

