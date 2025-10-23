/**
 * AI Studio Types
 * Type definitions for AI Studio conversations, messages, and state management
 */

import { ScheduledPostResult, PreviewPostResult } from '@/lib/api/ai-studio';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  scheduled_posts?: ScheduledPostResult[];
  previews?: PreviewPostResult[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  threadId: string;
  model: string;
}

export type DateGroup = 'today' | 'yesterday' | 'last7days' | 'last30days' | 'older';

export interface GroupedConversations {
  today: Conversation[];
  yesterday: Conversation[];
  last7days: Conversation[];
  last30days: Conversation[];
  older: Conversation[];
}

export interface ConversationUpdate {
  title?: string;
  messages?: Message[];
  updatedAt?: string;
}
