-- Migration: Fix token column size for Instagram OAuth tokens
-- Date: 2026-01-07
-- Issue: Instagram access_token and refresh_token exceed VARCHAR(500) limit
-- Solution: Change to TEXT (unlimited length)

-- Modify social_accounts table columns to support long OAuth tokens
ALTER TABLE social_accounts 
  ALTER COLUMN access_token TYPE TEXT,
  ALTER COLUMN refresh_token TYPE TEXT,
  ALTER COLUMN profile_url TYPE TEXT;

-- Add comment to document the change
COMMENT ON COLUMN social_accounts.access_token IS 'OAuth access token (TEXT to support long tokens from providers like Meta/Instagram)';
COMMENT ON COLUMN social_accounts.refresh_token IS 'OAuth refresh token (TEXT to support long tokens)';
COMMENT ON COLUMN social_accounts.profile_url IS 'Profile URL (TEXT for flexibility)';
