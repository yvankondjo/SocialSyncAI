-- Migration: Auto-create AI settings and credits for new users
-- Date: 2026-01-07
-- Issue: New users don't have default AI settings or credits
-- Solution: Create triggers to automatically initialize these records

-- =====================================================
-- TRIGGER 1: Auto-create AI settings for new users
-- =====================================================

CREATE OR REPLACE FUNCTION handle_new_user_ai_settings()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert default AI settings for the new user
  INSERT INTO ai_settings (
    user_id,
    system_prompt,
    ai_model,
    temperature,
    top_p,
    lang,
    tone,
    is_active,
    ai_enabled_for_conversations,
    ai_control_enabled,
    ai_enabled_for_chats,
    ai_enabled_for_comments,
    doc_lang,
    flagged_keywords,
    flagged_phrases,
    instructions,
    ignore_examples
  ) VALUES (
    NEW.id,
    'You are a helpful AI assistant specialized in social media management. Provide accurate, concise, and engaging responses to help users with their social media tasks.',
    'openai/gpt-4o',
    0.2,
    1.0,
    'en',
    'friendly',
    true,
    true,
    true,
    true,
    true,
    ARRAY[]::text[],
    ARRAY[]::text[],
    ARRAY[]::text[],
    NULL,
    ARRAY[]::text[]
  ) ON CONFLICT (user_id) DO NOTHING;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_user_created_ai_settings ON auth.users;

CREATE TRIGGER on_user_created_ai_settings
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user_ai_settings();

-- =====================================================
-- TRIGGER 2: Auto-create credits for new users
-- =====================================================

CREATE OR REPLACE FUNCTION handle_new_user_credits()
RETURNS TRIGGER AS $$
BEGIN
  -- Insert default credits (100 credits = Starter Plan)
  INSERT INTO user_credits (
    user_id,
    credits_balance,
    credits_used,
    storage_used_mb,
    storage_limit_mb,
    created_at,
    updated_at
  ) VALUES (
    NEW.id,
    100,  -- Default 100 credits
    0,
    0,
    100,  -- Default 100 MB storage limit
    NOW(),
    NOW()
  ) ON CONFLICT (user_id) DO NOTHING;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_user_created_credits ON auth.users;

CREATE TRIGGER on_user_created_credits
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user_credits();

-- =====================================================
-- BACKFILL: Create AI settings for existing users
-- =====================================================

INSERT INTO ai_settings (
  user_id,
  system_prompt,
  ai_model,
  temperature,
  top_p,
  lang,
  tone,
  is_active,
  ai_enabled_for_conversations,
  ai_control_enabled,
  ai_enabled_for_chats,
  ai_enabled_for_comments,
  doc_lang,
  flagged_keywords,
  flagged_phrases,
  instructions,
  ignore_examples
)
SELECT 
  id,
  'You are a helpful AI assistant specialized in social media management. Provide accurate, concise, and engaging responses to help users with their social media tasks.',
  'openai/gpt-4o',
  0.2,
  1.0,
  'en',
  'friendly',
  true,
  true,
  true,
  true,
  true,
  ARRAY[]::text[],
  ARRAY[]::text[],
  ARRAY[]::text[],
  NULL,
  ARRAY[]::text[]
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM ai_settings);

-- =====================================================
-- BACKFILL: Create credits for existing users
-- =====================================================

INSERT INTO user_credits (
  user_id,
  credits_balance,
  credits_used,
  storage_used_mb,
  storage_limit_mb,
  created_at,
  updated_at
)
SELECT 
  id,
  100,  -- Give 100 credits to existing users who have 0
  0,
  0,
  100,
  NOW(),
  NOW()
FROM auth.users
WHERE id NOT IN (SELECT user_id FROM user_credits WHERE credits_balance > 0);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ai_settings_user_id ON ai_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);

-- Add comments for documentation
COMMENT ON FUNCTION handle_new_user_ai_settings() IS 'Auto-creates default AI settings when a new user is created';
COMMENT ON FUNCTION handle_new_user_credits() IS 'Auto-creates default credits (100) and storage limits when a new user is created';
