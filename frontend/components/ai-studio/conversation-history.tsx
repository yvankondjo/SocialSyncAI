/**
 * ConversationHistory Component
 * Displays conversation history in a Sheet with search and grouping
 */

'use client';

import { useState, useMemo } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Conversation, GroupedConversations } from '@/types/ai-studio';
import {
  Search,
  Plus,
  MoreVertical,
  Trash2,
  Edit2,
  MessageSquare,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { format, formatDistanceToNow } from 'date-fns';

interface ConversationHistoryProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  groupedConversations: GroupedConversations;
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onSearch?: (query: string) => Conversation[];
}

const DATE_GROUP_LABELS: Record<keyof GroupedConversations, string> = {
  today: 'Today',
  yesterday: 'Yesterday',
  last7days: 'Last 7 days',
  last30days: 'Last 30 days',
  older: 'Older',
};

function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
}: {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: () => void;
}) {
  const [isRenaming, setIsRenaming] = useState(false);
  const [editedTitle, setEditedTitle] = useState(conversation.title);

  const handleRename = () => {
    if (editedTitle.trim() && editedTitle !== conversation.title) {
      onRename();
    }
    setIsRenaming(false);
  };

  const messageCount = conversation.messages.length;
  const lastUpdated = formatDistanceToNow(new Date(conversation.updatedAt), {
    addSuffix: true,
  });

  return (
    <div
      className={cn(
        'group relative flex items-start gap-3 rounded-lg p-3 transition-colors cursor-pointer',
        'hover:bg-accent',
        isActive && 'bg-accent'
      )}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
      aria-label={`Conversation: ${conversation.title}`}
      aria-current={isActive ? 'true' : 'false'}
    >
      <div className="mt-1 rounded-lg bg-primary/10 p-2 flex-shrink-0">
        <MessageSquare className="h-4 w-4 text-primary" />
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        {isRenaming ? (
          <Input
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleRename();
              } else if (e.key === 'Escape') {
                setEditedTitle(conversation.title);
                setIsRenaming(false);
              }
              e.stopPropagation();
            }}
            onClick={(e) => e.stopPropagation()}
            className="h-7 text-sm"
            autoFocus
          />
        ) : (
          <h4 className="text-sm font-medium leading-tight truncate">
            {conversation.title}
          </h4>
        )}

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{lastUpdated}</span>
          <span>•</span>
          <span>{messageCount} messages</span>
        </div>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
            aria-label="Conversation actions"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              setIsRenaming(true);
            }}
          >
            <Edit2 className="mr-2 h-4 w-4" />
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

function ConversationGroup({
  label,
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
}: {
  label: string;
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
}) {
  if (conversations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide px-3">
        {label}
      </h3>
      <div className="space-y-1">
        {conversations.map((conversation) => (
          <ConversationItem
            key={conversation.id}
            conversation={conversation}
            isActive={conversation.id === currentConversationId}
            onSelect={() => onSelectConversation(conversation.id)}
            onDelete={() => onDeleteConversation(conversation.id)}
            onRename={() =>
              onRenameConversation(
                conversation.id,
                conversation.title
              )
            }
          />
        ))}
      </div>
    </div>
  );
}

export function ConversationHistory({
  open,
  onOpenChange,
  groupedConversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
  onSearch,
}: ConversationHistoryProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const displayedConversations = useMemo(() => {
    if (!searchQuery.trim() || !onSearch) {
      return groupedConversations;
    }

    const searchResults = onSearch(searchQuery);
    // Group search results
    const grouped: GroupedConversations = {
      today: [],
      yesterday: [],
      last7days: [],
      last30days: [],
      older: [],
    };

    searchResults.forEach((conv) => {
      const found = Object.entries(groupedConversations).find(([_, convs]) =>
        convs.some((c) => c.id === conv.id)
      );
      if (found) {
        const [group] = found as [keyof GroupedConversations, Conversation[]];
        grouped[group].push(conv);
      }
    });

    return grouped;
  }, [searchQuery, groupedConversations, onSearch]);

  const totalConversations = Object.values(groupedConversations).reduce(
    (sum, convs) => sum + convs.length,
    0
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md p-0 flex flex-col">
        <SheetHeader className="px-6 pt-6 pb-4 space-y-1">
          <SheetTitle>Conversation History</SheetTitle>
          <SheetDescription>
            {totalConversations} conversation{totalConversations !== 1 ? 's' : ''}
          </SheetDescription>
        </SheetHeader>

        <div className="px-6 pb-4 space-y-4">
          <Button
            onClick={() => {
              onNewConversation();
              onOpenChange(false);
            }}
            className="w-full"
            size="lg"
          >
            <Plus className="mr-2 h-4 w-4" />
            New Conversation
          </Button>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        <ScrollArea className="flex-1 px-6">
          <div className="space-y-6 pb-6">
            {Object.entries(DATE_GROUP_LABELS).map(([group, label]) => (
              <ConversationGroup
                key={group}
                label={label}
                conversations={
                  displayedConversations[group as keyof GroupedConversations]
                }
                currentConversationId={currentConversationId}
                onSelectConversation={(id) => {
                  onSelectConversation(id);
                  onOpenChange(false);
                }}
                onDeleteConversation={onDeleteConversation}
                onRenameConversation={onRenameConversation}
              />
            ))}

            {totalConversations === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <MessageSquare className="mx-auto h-12 w-12 mb-4 opacity-20" />
                <p className="text-sm">No conversations yet</p>
                <p className="text-xs mt-1">Start a new conversation to begin</p>
              </div>
            )}

            {searchQuery && Object.values(displayedConversations).every(arr => arr.length === 0) && totalConversations > 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <Search className="mx-auto h-12 w-12 mb-4 opacity-20" />
                <p className="text-sm">No conversations found</p>
                <p className="text-xs mt-1">Try a different search term</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}
