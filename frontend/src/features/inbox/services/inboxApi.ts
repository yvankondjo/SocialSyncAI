import { Conversation, ConversationsQueryParams, Message } from '../types/inbox';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const res = await fetch(input, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText} - ${text}`);
  }
  return res.json();
}

export const InboxApi = {
  async listConversations(params: ConversationsQueryParams): Promise<Conversation[]> {
    const url = new URL(`${API_BASE_URL}/api/inbox/conversations`);
    if (params.channel && params.channel !== 'all') url.searchParams.set('channel', params.channel);
    if (params.status && params.status !== 'all') url.searchParams.set('status', params.status);
    if (params.search) url.searchParams.set('q', params.search);

    try {
      const data = await getJson<Conversation[]>(url.toString(), { method: 'GET' });
      return data
        .slice()
        .sort((a, b) => new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime());
    } catch {
      // Fallback mock for offline demo
      const now = new Date();
      let sample: Conversation[] = [
        {
          id: 'c1',
          channel: 'instagram',
          subject: 'IG DM',
          participants: [{ id: 'u1', displayName: 'Marie' }],
          lastMessageAt: new Date(now.getTime() - 1 * 60 * 1000).toISOString(),
          lastMessageSnippet: 'Hello! Is this available?',
          lastMessageSender: 'Marie',
          unreadCount: 2,
          assignedTo: null,
          status: 'open',
        },
        {
          id: 'c2',
          channel: 'tiktok',
          subject: 'Comment',
          participants: [{ id: 'u2', displayName: 'Adam' }],
          lastMessageAt: new Date(now.getTime() - 12 * 60 * 1000).toISOString(),
          lastMessageSnippet: 'Can you share price?',
          lastMessageSender: 'Adam',
          unreadCount: 0,
          assignedTo: 'agent_1',
          status: 'open',
        },
        {
          id: 'c3',
          channel: 'linkedin',
          subject: 'Partnership',
          participants: [{ id: 'u3', displayName: 'Lisa' }],
          lastMessageAt: new Date(now.getTime() - 60 * 60 * 1000).toISOString(),
          lastMessageSnippet: 'Thanks for your time',
          lastMessageSender: 'Lisa',
          unreadCount: 0,
          assignedTo: null,
          status: 'closed',
        },
      ];
      if (params.channel && params.channel !== 'all') {
        sample = sample.filter((c) => c.channel === params.channel);
      }
      if (params.status && params.status !== 'all') {
        sample = sample.filter((c) => c.status === params.status);
      }
      return sample;
    }
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    try {
      const data = await getJson<Message[]>(
        `${API_BASE_URL}/api/inbox/conversations/${conversationId}/messages`,
        { method: 'GET' }
      );
      return data.slice().sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime());
    } catch {
      const now = new Date();
      const sample: Message[] = [
        {
          id: 'm1',
          conversationId,
          authorType: 'customer',
          authorDisplayName: 'Marie',
          text: 'Hello! Is this available?',
          createdAt: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
        },
        {
          id: 'm2',
          conversationId,
          authorType: 'agent',
          authorDisplayName: 'You',
          text: 'Oui, bien sûr. Vous cherchez quelle taille ?',
          createdAt: new Date(now.getTime() - 3 * 60 * 1000).toISOString(),
        },
      ];
      return sample;
    }
  },
};


