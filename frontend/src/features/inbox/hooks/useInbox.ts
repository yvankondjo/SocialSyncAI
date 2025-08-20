import { useQuery } from '@tanstack/react-query';
import { InboxApi } from '../services/inboxApi';
import { Conversation, ConversationsQueryParams, Message } from '../types/inbox';

export function useConversations(params: ConversationsQueryParams) {
  return useQuery<Conversation[]>({
    queryKey: ['conversations', params],
    queryFn: () => InboxApi.listConversations(params),
    staleTime: 30_000,
  });
}

export function useMessages(conversationId?: string) {
  return useQuery<Message[]>({
    queryKey: ['messages', conversationId],
    queryFn: () => InboxApi.getMessages(conversationId as string),
    enabled: Boolean(conversationId),
    refetchOnWindowFocus: false,
  });
}



