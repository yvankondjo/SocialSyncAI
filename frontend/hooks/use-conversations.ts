/**
 * useConversations Hook
 * Manages AI Studio conversation state with localStorage persistence
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Conversation,
  ConversationUpdate,
  GroupedConversations,
  Message,
  DateGroup,
} from '@/types/ai-studio';
import {
  isToday,
  isYesterday,
  isWithinInterval,
  subDays,
  parseISO,
} from 'date-fns';

const STORAGE_KEY = 'ai-studio-conversations';
const MAX_CONVERSATIONS = 100;

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
 * Load conversations from localStorage
 */
function loadConversations(): Conversation[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored) as Conversation[];
    // Sort by updatedAt descending
    return parsed.sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  } catch (error) {
    console.error('Failed to load conversations:', error);
    return [];
  }
}

/**
 * Save conversations to localStorage
 */
function saveConversations(conversations: Conversation[]): void {
  if (typeof window === 'undefined') return;

  try {
    // Keep only the most recent MAX_CONVERSATIONS
    const toSave = conversations.slice(0, MAX_CONVERSATIONS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch (error) {
    console.error('Failed to save conversations:', error);
  }
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    const loaded = loadConversations();
    setConversations(loaded);
    setIsLoaded(true);
  }, []);

  // Save conversations whenever they change
  useEffect(() => {
    if (isLoaded) {
      saveConversations(conversations);
    }
  }, [conversations, isLoaded]);

  /**
   * Create a new conversation
   */
  const createConversation = useCallback(
    (model: string = 'openai/gpt-4o'): Conversation => {
      const now = new Date().toISOString();
      const newConversation: Conversation = {
        id: `conv-${Date.now()}`,
        title: 'New Conversation',
        messages: [],
        createdAt: now,
        updatedAt: now,
        threadId: `thread-${Date.now()}`,
        model,
      };

      setConversations((prev) => [newConversation, ...prev]);
      setCurrentConversationId(newConversation.id);

      return newConversation;
    },
    []
  );

  /**
   * Update a conversation
   */
  const updateConversation = useCallback(
    (id: string, update: ConversationUpdate): void => {
      setConversations((prev) => {
        const updated = prev.map((conv) => {
          if (conv.id !== id) return conv;

          const updatedConv = {
            ...conv,
            ...update,
            updatedAt: new Date().toISOString(),
          };

          // Auto-generate title if messages changed and title is still default
          if (
            update.messages &&
            (conv.title === 'New Conversation' || !update.title)
          ) {
            updatedConv.title = generateTitle(update.messages);
          }

          return updatedConv;
        });

        // Re-sort by updatedAt
        return updated.sort(
          (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        );
      });
    },
    []
  );

  /**
   * Delete a conversation
   */
  const deleteConversation = useCallback((id: string): void => {
    setConversations((prev) => prev.filter((conv) => conv.id !== id));
    setCurrentConversationId((prev) => (prev === id ? null : prev));
  }, []);

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
   * Get current conversation
   */
  const currentConversation = currentConversationId
    ? getConversation(currentConversationId)
    : null;

  /**
   * Group conversations by date
   */
  const groupedConversations = groupConversationsByDate(conversations);

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
    isLoaded,
  };
}
