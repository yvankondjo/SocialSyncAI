'use client';

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { AIStudioService } from '@/lib/api/ai-studio';
import { useConversations } from '@/hooks/use-conversations';
import { ConversationHistory } from '@/components/ai-studio/conversation-history';
import { MessageBubble, LoadingMessage } from '@/components/ai-studio/messages';
import { ModelSelector } from '@/components/ai-studio/model-selector';
import { Message } from '@/types/ai-studio';
import {
  Send,
  Clock,
  Plus,
  Settings,
} from 'lucide-react';

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hello! I'm your AI content creation assistant. I can help you create and schedule social media posts across multiple platforms.\n\nWhat would you like to create today?",
  timestamp: new Date().toISOString(),
};

export default function AIStudioPage() {
  const queryClient = useQueryClient();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [tempSystemPrompt, setTempSystemPrompt] = useState('');
  const [tempModel, setTempModel] = useState('openai/gpt-4o');
  const [tempTemperature, setTempTemperature] = useState(0.7);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch AI Studio settings from API
  const {
    data: settings,
    isLoading: settingsLoading,
    error: settingsError,
  } = useQuery({
    queryKey: ['ai-studio', 'settings'],
    queryFn: () => AIStudioService.getSettings(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Mutation for updating settings
  const updateSettingsMutation = useMutation({
    mutationFn: (data: { default_system_prompt?: string | null; default_model?: string; temperature?: number }) =>
      AIStudioService.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-studio', 'settings'] });
    },
  });

  // Get current values from settings or defaults
  const systemPrompt = settings?.default_system_prompt || null;
  const defaultModel = settings?.default_model || 'openai/gpt-4o';
  const temperature = settings?.temperature || 0.7;

  // Local state for current session model (can be changed per conversation)
  const [selectedModel, setSelectedModel] = useState(defaultModel);

  // Update selectedModel when settings load
  useEffect(() => {
    if (settings?.default_model) {
      setSelectedModel(settings.default_model);
    }
  }, [settings?.default_model]);

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

  useEffect(() => {
    if (isLoaded && !currentConversationId) {
      const newConv = createConversation(selectedModel);
      updateConversation(newConv.id, {
        messages: [WELCOME_MESSAGE],
      });
    }
  }, [isLoaded, currentConversationId, createConversation, updateConversation, selectedModel]);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [currentConversation?.messages, isLoading]);

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
        system_prompt: systemPrompt || undefined, // Pass custom system prompt if set
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

      // Invalidate conversations list to sync with backend
      queryClient.invalidateQueries({ queryKey: ['ai-studio', 'conversations'] });
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

  const handleOpenSettings = () => {
    // Load current settings into temp state
    setTempSystemPrompt(systemPrompt || '');
    setTempModel(selectedModel);
    setTempTemperature(temperature);
    setSettingsOpen(true);
  };

  const handleSaveSettings = async () => {
    try {
      await updateSettingsMutation.mutateAsync({
        default_system_prompt: tempSystemPrompt || null,
        default_model: tempModel,
        temperature: tempTemperature,
      });
      setSettingsOpen(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const messages = currentConversation?.messages || [WELCOME_MESSAGE];

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="flex-shrink-0 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center justify-between h-14 px-6">
          <div className="flex items-center gap-3 min-w-0">
            <h1 className="font-semibold text-lg tracking-tight">AI Studio</h1>
          </div>

          <div className="flex items-center gap-1 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleNewConversation}
              className="h-9 w-9"
            >
              <Plus className="h-4 w-4" />
            </Button>

            <ModelSelector
              selectedModel={selectedModel}
              onModelChange={setSelectedModel}
              disabled={isLoading}
            />

            <Button
              variant="ghost"
              size="icon"
              onClick={() => setHistoryOpen(true)}
              className="h-9 w-9"
            >
              <Clock className="h-4 w-4" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={handleOpenSettings}
              className="h-9 w-9"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center overflow-hidden">
        <div className="w-full max-w-3xl flex flex-col h-full">
          {/* Messages */}
          <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0 px-4">
            <div className="py-8 space-y-6">
              {messages.map((message: Message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <LoadingMessage />}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t bg-background p-4">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message AI Studio..."
                  disabled={isLoading}
                  className="min-h-[52px] max-h-[200px] resize-none pr-4 focus-visible:ring-1"
                  rows={1}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                disabled={!input.trim() || isLoading}
                size="icon"
                className="h-[52px] w-[52px]"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-center text-muted-foreground mt-3">
              AI can make mistakes. Check important info.
            </p>
          </div>
        </div>
      </div>

      {/* History */}
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

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>AI Studio Settings</DialogTitle>
            <DialogDescription>
              Configure your AI assistant defaults for model, temperature, and system prompt.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="system-prompt">Custom System Prompt (Optional)</Label>
              <Textarea
                id="system-prompt"
                value={tempSystemPrompt}
                onChange={(e) => setTempSystemPrompt(e.target.value)}
                placeholder="Leave empty to use default content creation prompt..."
                className="min-h-[150px] resize-none"
              />
              <p className="text-xs text-muted-foreground">
                Custom system prompt to override the default behavior. Leave empty to use the built-in content creation assistant prompt.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSettingsOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={updateSettingsMutation.isPending}
            >
              {updateSettingsMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
