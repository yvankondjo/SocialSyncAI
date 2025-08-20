-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TYPE social_platform AS ENUM ('facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'whatsapp', 'reddit', 'x', 'website');


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

-- Indexes for inbox tables
CREATE INDEX idx_conversations_social_account ON conversations(social_account_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_priority ON conversations(priority);
CREATE INDEX idx_conversations_assigned_to ON conversations(assigned_to);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at);
CREATE INDEX idx_conversations_customer ON conversations(customer_identifier);

CREATE INDEX idx_conversation_messages_conversation ON conversation_messages(conversation_id);
CREATE INDEX idx_conversation_messages_direction ON conversation_messages(direction);
CREATE INDEX idx_conversation_messages_created_at ON conversation_messages(created_at);
CREATE INDEX idx_conversation_messages_status ON conversation_messages(status);
CREATE INDEX idx_conversation_messages_agent ON conversation_messages(agent_id);

CREATE INDEX idx_web_widgets_user_id ON web_widgets(user_id);
CREATE INDEX idx_web_widgets_widget_key ON web_widgets(widget_key);
CREATE INDEX idx_web_widgets_active ON web_widgets(is_active);

CREATE INDEX idx_response_templates_user_id ON response_templates(user_id);
CREATE INDEX idx_response_templates_active ON response_templates(is_active);
CREATE INDEX idx_response_templates_platforms ON response_templates USING GIN(platforms);

CREATE INDEX idx_automation_rules_user_id ON automation_rules(user_id);
CREATE INDEX idx_automation_rules_active ON automation_rules(is_active);
CREATE INDEX idx_automation_rules_platforms ON automation_rules USING GIN(platforms);

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

-- Conversations table for inbox (WhatsApp, Instagram DM, Website chat)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    social_account_id UUID NOT NULL REFERENCES social_accounts(id) ON DELETE CASCADE,
    external_conversation_id VARCHAR(255), -- ID WhatsApp/Instagram/Web
    customer_identifier VARCHAR(255) NOT NULL, -- Numéro/username/email
    customer_name VARCHAR(255),
    customer_avatar_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'open', -- open, closed, pending, archived
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high, urgent
    assigned_to UUID REFERENCES users(id), -- Agent assigné
    tags TEXT[], -- Tags pour organisation
    metadata JSONB DEFAULT '{}', -- Infos spécifiques par plateforme
    last_message_at TIMESTAMP WITH TIME ZONE,
    unread_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(social_account_id, external_conversation_id)
);

-- Messages table for individual messages in conversations
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    external_message_id VARCHAR(255), -- ID du message sur la plateforme
    direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound'
    message_type VARCHAR(50) DEFAULT 'text', -- text, image, file, template, audio, video, location
    content TEXT NOT NULL,
    media_url VARCHAR(500),
    media_type VARCHAR(50), -- image/jpeg, video/mp4, etc.
    sender_id VARCHAR(255), -- ID de l'expéditeur
    sender_name VARCHAR(255),
    sender_avatar_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'sent', -- sent, delivered, read, failed, pending
    is_from_agent BOOLEAN DEFAULT false,
    agent_id UUID REFERENCES users(id), -- Si envoyé par un agent
    reply_to_message_id UUID REFERENCES conversation_messages(id), -- Pour les réponses
    metadata JSONB DEFAULT '{}', -- Données spécifiques (localisation, réactions, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Web widgets table for embeddable chat widgets
CREATE TABLE web_widgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    widget_key VARCHAR(100) UNIQUE NOT NULL, -- Clé publique pour l'embed
    allowed_domains TEXT[], -- Domaines autorisés (CORS)
    settings JSONB DEFAULT '{}', -- Configuration du widget (couleurs, textes, position, etc.)
    is_active BOOLEAN DEFAULT true,
    social_account_id UUID REFERENCES social_accounts(id), -- Compte lié pour les analytics
    api_endpoint VARCHAR(500), -- URL personnalisée pour les webhooks
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table pour les templates de réponses automatiques
CREATE TABLE response_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    platforms social_platform[], -- Plateformes compatibles
    trigger_keywords TEXT[], -- Mots-clés déclencheurs
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table pour les règles d'automatisation
CREATE TABLE automation_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_conditions JSONB NOT NULL, -- Conditions de déclenchement
    actions JSONB NOT NULL, -- Actions à exécuter
    platforms social_platform[], -- Plateformes concernées
    is_active BOOLEAN DEFAULT true,
    execution_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversation_messages_updated_at BEFORE UPDATE ON conversation_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_web_widgets_updated_at BEFORE UPDATE ON web_widgets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_response_templates_updated_at BEFORE UPDATE ON response_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_automation_rules_updated_at BEFORE UPDATE ON automation_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();



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
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE web_widgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE response_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE automation_rules ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ai_insights ENABLE ROW LEVEL SECURITY;

-- RLS policies for inbox tables
CREATE POLICY "Users manage their conversations" ON conversations FOR ALL USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        WHERE sa.id = social_account_id
    )
);

CREATE POLICY "Users manage their messages" ON conversation_messages FOR ALL USING (
    auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        JOIN conversations c ON c.social_account_id = sa.id 
        WHERE c.id = conversation_id
    )
);

CREATE POLICY "Users manage their widgets" ON web_widgets FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users manage their templates" ON response_templates FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users manage their automation rules" ON automation_rules FOR ALL USING (auth.uid() = user_id);

-- Trigger function to update conversation last_message_at
CREATE OR REPLACE FUNCTION update_conversation_last_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET 
        last_message_at = NEW.created_at,
        unread_count = CASE 
            WHEN NEW.direction = 'inbound' AND NEW.is_from_agent = false 
            THEN unread_count + 1 
            ELSE unread_count 
        END
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update conversation when new message is added
CREATE TRIGGER trg_update_conversation_last_message 
    AFTER INSERT ON conversation_messages
    FOR EACH ROW 
    EXECUTE FUNCTION update_conversation_last_message();

-- Function to mark conversation as read
CREATE OR REPLACE FUNCTION mark_conversation_as_read(conversation_uuid UUID)
RETURNS void AS $$
BEGIN
    UPDATE conversations 
    SET unread_count = 0 
    WHERE id = conversation_uuid 
    AND auth.uid() IN (
        SELECT sa.user_id FROM social_accounts sa 
        WHERE sa.id = social_account_id
    );
END;
$$ language 'plpgsql' SECURITY DEFINER;

