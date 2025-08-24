export type Channel = 'instagram' | 'whatsapp';

export interface Participant {
  id: string;
  displayName: string;
  avatarUrl?: string;
}

export interface Conversation {
  id: string;
  participants: Participant[];
  channel: Channel;
  lastMessageAt: string;
  lastMessageSnippet: string;
  unreadCount: number;
}

export interface Message {
  id: string;
  conversationId: string;
  authorId: string;
  text: string;
  createdAt: string;
  attachments?: string[];
}

export interface ConversationsQueryParams {
  channel?: Channel | 'all';
  status?: 'open' | 'closed' | 'all';
  search?: string;
}