'use client';

/**
 * AI Studio - Modern Minimalist Interface
 * Inspired by ChatGPT's clean design with history in a side sheet
 */

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AIStudioService } from '@/lib/api/ai-studio';
import { useConversations } from '@/hooks/use-conversations';
import { ConversationHistory } from '@/components/ai-studio/conversation-history';
import { MessageBubble, LoadingMessage } from '@/components/ai-studio/messages';
import { ModelSelector } from '@/components/ai-studio/model-selector';
import { Message } from '@/types/ai-studio';
import {
  Send,
  Clock,
  Sparkles,
  Plus,
  SettingsIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hello! I'm your AI content creation assistant. I can help you:\n\n• Generate engaging social media posts\n• Schedule posts for Instagram, Twitter, WhatsApp, and Facebook\n• Preview and optimize your content\n• Suggest best practices for each platform\n\nWhat would you like to create today?",
  timestamp: new Date().toISOString(),
};

export default function AIStudioPage() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState('openai/gpt-4o');
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    currentConversation,
    currentConversationId,
    groupedConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    setCurrentConversationId,
    searchConversations,
    isLoaded,
  } = useConversations();

  // Initialize first conversation on load
  useEffect(() => {
    if (isLoaded && !currentConversationId) {
      const newConv = createConversation(selectedModel);
      updateConversation(newConv.id, {
        messages: [WELCOME_MESSAGE],
      });
    }
  }, [isLoaded, currentConversationId, createConversation, updateConversation, selectedModel]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [currentConversation?.messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading || !currentConversationId) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    const currentMessages = currentConversation?.messages || [];
    const updatedMessages = [...currentMessages, userMessage];

    updateConversation(currentConversationId, {
      messages: updatedMessages,
    });

    setInput('');
    setIsLoading(true);

    try {
      const response = await AIStudioService.createContent({
        thread_id: currentConversation?.threadId || `thread-${Date.now()}`,
        message: userMessage.content,
        model: selectedModel,
      });

      const aiMessage: Message = {
        id: `msg-${Date.now()}-ai`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        scheduled_posts: response.scheduled_posts,
        previews: response.previews,
      };

      updateConversation(currentConversationId, {
        messages: [...updatedMessages, aiMessage],
      });
    } catch (error) {
      console.error('Error creating content:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
      };

      updateConversation(currentConversationId, {
        messages: [...updatedMessages, errorMessage],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewConversation = () => {
    const newConv = createConversation(selectedModel);
    updateConversation(newConv.id, {
      messages: [WELCOME_MESSAGE],
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleRenameConversation = (id: string, newTitle: string) => {
    updateConversation(id, { title: newTitle });
  };

  const messages = currentConversation?.messages || [WELCOME_MESSAGE];

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Top Bar */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
        <div className="flex items-center justify-between h-14 px-4 sm:px-6 max-w-5xl mx-auto">
          {/* Left: Branding */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-primary" />
            </div>
            <h1 className="font-semibold text-base sm:text-lg tracking-tight">
              AI Studio
            </h1>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleNewConversation}
              className="gap-2"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New</span>
            </Button>

            <ModelSelector
              selectedModel={selectedModel}
              onModelChange={setSelectedModel}
              disabled={isLoading}
            />

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setHistoryOpen(true)}
              className="gap-2"
            >
              <Clock className="h-4 w-4" />
              <span className="hidden sm:inline">History</span>
            </Button>

            <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
              <SettingsIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center overflow-hidden">
        <div className="w-full max-w-3xl flex flex-col flex-1">
          {/* Messages Area */}
          <ScrollArea ref={scrollAreaRef} className="flex-1 px-4 sm:px-6">
            <div className="py-8 space-y-6">
              {messages.map((message: Message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <LoadingMessage />}
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t bg-background p-4 sm:p-6">
            <div className="space-y-4">
              {/* Input Box */}
              <div className="relative flex items-end gap-2">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Describe the content you want to create..."
                    disabled={isLoading}
                    className={cn(
                      'min-h-[52px] max-h-[200px] resize-none pr-12',
                      'focus-visible:ring-1 focus-visible:ring-primary',
                      'rounded-xl'
                    )}
                    rows={1}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!input.trim() || isLoading}
                    size="sm"
                    className="absolute right-2 bottom-2 rounded-lg h-8 w-8 p-0"
                  >
                    <Send className="h-4 w-4" />
                    <span className="sr-only">Send message</span>
                  </Button>
                </div>
              </div>

              {/* Example Prompts - Only show when no messages yet */}
              {messages.length <= 1 && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Try asking:</p>
                  <div className="flex flex-wrap gap-2">
                    {[
                      'Create an Instagram post about a new product launch',
                      'Write a Twitter thread about sustainability',
                      'Schedule a WhatsApp message for tomorrow',
                    ].map((example) => (
                      <Button
                        key={example}
                        variant="outline"
                        size="sm"
                        className="text-xs h-auto py-2 px-3 rounded-lg hover:bg-accent"
                        onClick={() => setInput(example)}
                        disabled={isLoading}
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {/* Footer Info */}
              <p className="text-xs text-center text-muted-foreground">
                AI can make mistakes. Check important info.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Conversation History Sheet */}
      <ConversationHistory
        open={historyOpen}
        onOpenChange={setHistoryOpen}
        groupedConversations={groupedConversations}
        currentConversationId={currentConversationId}
        onSelectConversation={setCurrentConversationId}
        onNewConversation={handleNewConversation}
        onDeleteConversation={deleteConversation}
        onRenameConversation={handleRenameConversation}
        onSearch={searchConversations}
      />
    </div>
  );
}
