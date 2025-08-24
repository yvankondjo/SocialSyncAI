import { Conversation, ConversationsQueryParams, Message } from '../types/inbox';
import { createClient } from '@/lib/supabase/client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const InboxApi = {
  async getAuthHeaders(): Promise<HeadersInit> {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  },

  async getConversation(conversationId: string) {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('conversations')
      .select(
        `id, customer_identifier, metadata,
         social_accounts: social_account_id ( platform, account_id, access_token, page_id )`
      )
      .eq('id', conversationId)
      .single();
    if (error) throw error;
    return data as {
      id: string;
      customer_identifier: string;
      metadata: Record<string, unknown> | null;
      social_accounts: { platform: 'whatsapp' | 'instagram'; account_id: string | null; access_token: string | null; page_id: string | null }[];
    };
  },
  async listConversations(params: ConversationsQueryParams): Promise<Conversation[]> {
    const supabase = createClient();

    const { data, error } = await supabase
      .from('conversations')
      .select(
        `id, customer_name, customer_identifier, last_message_at, unread_count,
         social_accounts: social_account_id ( platform ),
         last_message: conversation_messages!conversation_messages_conversation_id_fkey ( content, created_at )`
      )
      .order('last_message_at', { ascending: false });

    if (error) throw error;

    const allowedChannels: Array<'whatsapp' | 'instagram'> = ['whatsapp', 'instagram'];

    type Row = {
      id: string;
      customer_name: string | null;
      customer_identifier: string;
      last_message_at: string | null;
      unread_count: number | null;
      social_accounts: { platform: 'whatsapp' | 'instagram' }[];
      last_message?: { content: string; created_at: string }[] | null;
    };

    const rawRows = (data as unknown as Row[]) || [];
    let rows: Row[] = rawRows.filter((row) => allowedChannels.includes((row.social_accounts?.[0]?.platform) as 'whatsapp' | 'instagram'));

    if (params.channel && params.channel !== 'all') {
      rows = rows.filter((r) => r.social_accounts?.[0]?.platform === params.channel);
    }

    const conversations: Conversation[] = rows.map((r) => ({
      id: r.id,
      channel: r.social_accounts?.[0]?.platform || 'whatsapp',
      participants: [
        {
          id: r.customer_identifier,
          displayName: r.customer_name || r.customer_identifier,
        },
      ],
      lastMessageAt: r.last_message_at || r.last_message?.[0]?.created_at || new Date().toISOString(),
      lastMessageSnippet: r.last_message?.[0]?.content || '',
      unreadCount: r.unread_count || 0,
    }));

    return conversations;
  },

  async getMessages(conversationId: string): Promise<Message[]> {
    const supabase = createClient();
    const { data, error } = await supabase
      .from('conversation_messages')
      .select('id, conversation_id, direction, content, created_at, sender_id, is_from_agent')
      .eq('conversation_id', conversationId)
      .order('created_at', { ascending: true });

    if (error) throw error;

    type RowMsg = {
      id: string;
      conversation_id: string;
      direction: 'inbound' | 'outbound';
      content: string;
      created_at: string;
      sender_id: string | null;
      is_from_agent: boolean | null;
    };

    const items: Message[] = (data as RowMsg[] | null)?.map((m) => ({
      id: m.id,
      conversationId: m.conversation_id,
      authorId: m.is_from_agent ? 'me' : m.sender_id || 'customer',
      text: m.content,
      createdAt: m.created_at,
    })) || [];
    return items;
  },

  async sendMessage(conversationId: string, text: string): Promise<void> {
    const supabase = createClient();
    const conv = await this.getConversation(conversationId);
    const social = conv.social_accounts?.[0];
    const platform = social?.platform;

    if (platform === 'whatsapp') {
      const headers = await this.getAuthHeaders();
      await fetch(`${API_BASE_URL}/api/whatsapp/send-text`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ to: conv.customer_identifier, text }),
      });
    } else if (platform === 'instagram') {
      await fetch(`${API_BASE_URL}/api/messaging/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: 'instagram',
          message_type: 'text',
          recipient: conv.customer_identifier,
          content: text,
          access_token: social?.access_token,
          page_id: social?.page_id,
        }),
      });
    }

    await supabase.from('conversation_messages').insert({
      conversation_id: conversationId,
      direction: 'outbound',
      message_type: 'text',
      content: text,
      is_from_agent: true,
    });
  },
};


