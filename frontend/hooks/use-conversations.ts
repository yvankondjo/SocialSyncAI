/**
 * useConversations Hook
 * Manages AI Studio conversation state with React Query and backend API
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Conversation,
  ConversationUpdate,
  GroupedConversations,
  Message,
} from '@/types/ai-studio';
import { AIStudioService } from '@/lib/api/ai-studio';
import {
  isToday,
  isYesterday,
  isWithinInterval,
  subDays,
  parseISO,
} from 'date-fns';

/**
 * Generate a title from the first user message
 */
function generateTitle(messages: Message[]): string {
  const firstUserMessage = messages.find((m) => m.role === 'user');
  if (!firstUserMessage) return 'New Conversation';

  const content = firstUserMessage.content;
  // Take first 50 chars or up to first newline
  const title = content.split('\n')[0].substring(0, 50);
  return title.length < content.length ? `${title}...` : title;
}

/**
 * Group conversations by date
 */
function groupConversationsByDate(conversations: Conversation[]): GroupedConversations {
  const now = new Date();
  const grouped: GroupedConversations = {
    today: [],
    yesterday: [],
    last7days: [],
    last30days: [],
    older: [],
  };

  conversations.forEach((conv) => {
    const date = parseISO(conv.updatedAt);

    if (isToday(date)) {
      grouped.today.push(conv);
    } else if (isYesterday(date)) {
      grouped.yesterday.push(conv);
    } else if (
      isWithinInterval(date, {
        start: subDays(now, 7),
        end: subDays(now, 2),
      })
    ) {
      grouped.last7days.push(conv);
    } else if (
      isWithinInterval(date, {
        start: subDays(now, 30),
        end: subDays(now, 7),
      })
    ) {
      grouped.last30days.push(conv);
    } else {
      grouped.older.push(conv);
    }
  });

  return grouped;
}

/**
 * Convert backend ConversationMetadata to frontend Conversation format
 */
function mapConversationMetadata(metadata: any): Conversation {
  return {
    id: metadata.thread_id,
    title: metadata.title,
    messages: [], // Messages loaded separately
    createdAt: metadata.created_at,
    updatedAt: metadata.updated_at,
    threadId: metadata.thread_id,
    model: metadata.model,
  };
}

export function useConversations() {
  const queryClient = useQueryClient();
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [localConversation, setLocalConversation] = useState<Conversation | null>(null);

  // Fetch conversations list from API
  const {
    data: conversationsResponse,
    isLoading: conversationsLoading,
    error: conversationsError,
  } = useQuery({
    queryKey: ['ai-studio', 'conversations'],
    queryFn: () => AIStudioService.listConversations(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Fetch messages for current conversation
  // Skip API call if this is a local conversation (not yet in database)
  const shouldFetchMessages = !!currentConversationId &&
    (!localConversation || localConversation.id !== currentConversationId);

  const {
    data: messagesResponse,
    isLoading: messagesLoading,
  } = useQuery({
    queryKey: ['ai-studio', 'conversations', currentConversationId, 'messages'],
    queryFn: () => AIStudioService.getConversationMessages(currentConversationId!),
    enabled: shouldFetchMessages,
    staleTime: 1000 * 30, // 30 seconds
  });

  // Mutation for updating conversation
  const updateConversationMutation = useMutation({
    mutationFn: ({ threadId, update }: { threadId: string; update: { title?: string } }) =>
      AIStudioService.updateConversation(threadId, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-studio', 'conversations'] });
    },
  });

  // Mutation for deleting conversation
  const deleteConversationMutation = useMutation({
    mutationFn: (threadId: string) => AIStudioService.deleteConversation(threadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-studio', 'conversations'] });
    },
  });

  // Map conversations from API response
  const conversations = useMemo(() => {
    if (!conversationsResponse?.conversations) return [];
    return conversationsResponse.conversations.map(mapConversationMetadata);
  }, [conversationsResponse]);

  /**
   * Create a new conversation
   * Note: Backend auto-creates conversations on first message, so we just generate a thread ID
   */
  const createConversation = useCallback(
    (model: string = 'openai/gpt-4o'): Conversation => {
      const now = new Date().toISOString();
      const threadId = `thread-${Date.now()}`;
      const newConversation: Conversation = {
        id: threadId,
        title: 'New Conversation',
        messages: [],
        createdAt: now,
        updatedAt: now,
        threadId,
        model,
      };

      setLocalConversation(newConversation);
      setCurrentConversationId(threadId);
      return newConversation;
    },
    []
  );

  /**
   * Update a conversation
   * Note: Only title updates are persisted to backend, messages are handled by LangGraph
   */
  const updateConversation = useCallback(
    (id: string, update: ConversationUpdate): void => {
      // Update local conversation if it's the current one
      if (localConversation && localConversation.id === id) {
        setLocalConversation((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            ...update,
            messages: update.messages || prev.messages,
            updatedAt: new Date().toISOString(),
          };
        });
      }

      // If updating title, persist to backend
      if (update.title) {
        updateConversationMutation.mutate({
          threadId: id,
          update: { title: update.title },
        });
      }

      // Optimistically update messages query cache for immediate UI feedback
      if (update.messages && currentConversationId === id) {
        queryClient.setQueryData(
          ['ai-studio', 'conversations', id, 'messages'],
          (old: any) => ({
            ...old,
            messages: update.messages?.map((msg) => ({
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp,
              metadata: {
                scheduled_posts: msg.scheduled_posts,
                previews: msg.previews,
              },
            })),
          })
        );
      }
    },
    [currentConversationId, queryClient, updateConversationMutation, localConversation]
  );

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback(
    (id: string): void => {
      deleteConversationMutation.mutate(id);
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setLocalConversation(null);
      }
    },
    [currentConversationId, deleteConversationMutation]
  );

  /**
   * Clear local conversation when switching to a different conversation
   */
  useEffect(() => {
    if (currentConversationId && localConversation && localConversation.id !== currentConversationId) {
      // Switching away from local conversation, invalidate queries to sync with backend
      queryClient.invalidateQueries({ queryKey: ['ai-studio', 'conversations'] });
      setLocalConversation(null);
    }
  }, [currentConversationId, localConversation, queryClient]);

  /**
   * Get a specific conversation
   */
  const getConversation = useCallback(
    (id: string): Conversation | undefined => {
      return conversations.find((conv) => conv.id === id);
    },
    [conversations]
  );

  /**
   * Get current conversation with messages
   */
  const currentConversation = useMemo(() => {
    if (!currentConversationId) return null;

    // If local conversation matches, use it (for new conversations not yet in DB)
    if (localConversation && localConversation.id === currentConversationId) {
      return localConversation;
    }

    // Otherwise, look in API conversations
    const metadata = conversations.find((conv) => conv.id === currentConversationId);
    if (!metadata) return null;

    // Add messages from separate query
    const messages = messagesResponse?.messages?.map((msg: any) => ({
      id: `${msg.role}-${Date.now()}-${Math.random()}`,
      role: msg.role as 'user' | 'assistant',
      content: msg.content,
      timestamp: msg.timestamp || new Date().toISOString(),
      scheduled_posts: msg.metadata?.scheduled_posts,
      previews: msg.metadata?.previews,
    })) || [];

    return {
      ...metadata,
      messages,
    };
  }, [currentConversationId, conversations, messagesResponse, localConversation]);

  /**
   * Group conversations by date
   */
  const groupedConversations = useMemo(
    () => groupConversationsByDate(conversations),
    [conversations]
  );

  /**
   * Search conversations
   */
  const searchConversations = useCallback(
    (query: string): Conversation[] => {
      if (!query.trim()) return conversations;

      const lowerQuery = query.toLowerCase();
      return conversations.filter((conv) => {
        // Search in title
        if (conv.title.toLowerCase().includes(lowerQuery)) return true;

        // Search in messages
        return conv.messages.some((msg) =>
          msg.content.toLowerCase().includes(lowerQuery)
        );
      });
    },
    [conversations]
  );

  return {
    conversations,
    groupedConversations,
    currentConversation,
    currentConversationId,
    setCurrentConversationId,
    createConversation,
    updateConversation,
    deleteConversation,
    getConversation,
    searchConversations,
    isLoaded: !conversationsLoading, // Loaded when conversations query is not loading
    isLoadingMessages: messagesLoading,
    error: conversationsError,
  };
}
