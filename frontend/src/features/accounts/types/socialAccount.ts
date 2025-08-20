export type SocialPlatform = 'facebook' | 'twitter' | 'instagram' | 'linkedin' | 'youtube' | 'tiktok' | 'whatsapp';

export interface SocialAccount {
  id: string;
  platform: SocialPlatform;
  account_id: string;
  username: string;
  display_name?: string;
  profile_url?: string;
  access_token: string;
  refresh_token?: string;
  token_expires_at?: string;
  is_active: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
}