export type PostStatus = 'draft' | 'queued' | 'publishing' | 'published' | 'failed' | 'cancelled';
export type Platform = 'whatsapp' | 'instagram' | 'facebook' | 'twitter';
export type RunStatus = 'success' | 'failed';

export interface MediaItem {
  type: 'image' | 'video' | 'audio';
  url: string;
}

export interface PostContent {
  text: string;
  media?: MediaItem[];
}

export interface ScheduledPost {
  id: string;
  user_id: string;
  channel_id: string;
  platform: Platform;
  content_json: PostContent;
  publish_at: string;
  status: PostStatus;
  platform_post_id?: string;
  error_message?: string;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface PostRun {
  id: string;
  scheduled_post_id: string;
  started_at: string;
  finished_at?: string;
  status: RunStatus;
  error?: string;
  created_at: string;
}

export interface ScheduledPostCreate {
  channel_id: string;
  content: PostContent;
  publish_at: string;
}

export interface ScheduledPostUpdate {
  content?: PostContent;
  publish_at?: string;
}

export interface PostsListParams {
  status?: PostStatus;
  channel_id?: string;
  platform?: Platform;
  limit?: number;
  offset?: number;
}

export interface PostStatistics {
  total: number;
  draft: number;
  queued: number;
  published: number;
  failed: number;
}
