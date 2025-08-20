export type Channel = 'instagram' | 'whatsapp' | 'reddit';

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