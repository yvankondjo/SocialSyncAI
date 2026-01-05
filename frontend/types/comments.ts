// Types for Comment Monitoring System

export interface MonitoredPost {
  id: string
  user_id: string
  social_account_id: string
  platform_post_id: string
  platform: 'instagram' | 'facebook' | 'twitter'
  caption: string
  media_url?: string
  posted_at: string
  source: 'scheduled' | 'imported' | 'manual'
  monitoring_enabled: boolean
  monitoring_started_at?: string
  monitoring_ends_at?: string
  last_check_at?: string
  comments_count?: number
  days_remaining?: number
}

export interface MonitoringRules {
  auto_monitor_enabled: boolean
  auto_monitor_count: number
  monitoring_duration_days: number
}

export interface Comment {
  id: string
  post_id: string
  platform_comment_id: string
  author_name: string
  author_id: string
  author_avatar_url?: string
  text: string
  triage: 'respond' | 'ignore' | 'escalate'
  ai_decision_id?: string
  replied_at?: string
  ai_reply_text?: string
  created_at: string
  platform: 'instagram' | 'facebook' | 'twitter'
}

export interface CommentFilters {
  post_id?: string
  triage?: 'respond' | 'ignore' | 'escalate'
  platform?: string
  search?: string
  limit?: number
  offset?: number
}
