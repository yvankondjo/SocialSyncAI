'use client';

import { Message } from '@/types/ai-studio';
import { ScheduledPostResult, PreviewPostResult } from '@/lib/api/ai-studio';
import { Bot, User, Calendar, Eye, Clock, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

interface MessageBubbleProps {
  message: Message;
}

function UserMessage({ content, timestamp }: { content: string; timestamp: string }) {
  return (
    <div className="flex gap-4 justify-end">
      <div className="flex flex-col items-end gap-2 max-w-[80%]">
        <div className="rounded-2xl bg-foreground text-background px-4 py-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
        <span className="text-xs text-muted-foreground">
          {format(new Date(timestamp), 'HH:mm')}
        </span>
      </div>
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
        <User className="w-4 h-4" />
      </div>
    </div>
  );
}

function AIMessage({ content, timestamp }: { content: string; timestamp: string }) {
  return (
    <div className="flex gap-4 justify-start">
      <div className="flex-shrink-0 w-8 h-8 rounded-full border-2 border-border flex items-center justify-center bg-background">
        <Bot className="w-4 h-4" />
      </div>
      <div className="flex flex-col items-start gap-2 max-w-[80%]">
        <div className="rounded-2xl bg-muted px-4 py-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
        <span className="text-xs text-muted-foreground">
          {format(new Date(timestamp), 'HH:mm')}
        </span>
      </div>
    </div>
  );
}

function ToolCallCard({ children, icon: Icon, title }: {
  children: React.ReactNode;
  icon: any;
  title: string;
}) {
  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center gap-2 px-4 py-3 border-b bg-muted/50">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm font-medium">{title}</span>
      </div>
      <div className="p-4">
        {children}
      </div>
    </div>
  );
}

function ScheduledPostCard({ post }: { post: ScheduledPostResult }) {
  return (
    <ToolCallCard icon={Calendar} title="Post Scheduled">
      <div className="space-y-3">
        {post.success ? (
          <>
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-2 flex-1">
                <p className="text-sm">{post.message}</p>
                {post.platform && (
                  <Badge variant="secondary" className="capitalize">
                    {post.platform}
                  </Badge>
                )}
              </div>
            </div>

            {post.scheduled_for && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 rounded px-3 py-2">
                <Clock className="w-4 h-4" />
                <span>{format(new Date(post.scheduled_for), 'PPp')}</span>
              </div>
            )}

            {post.post_id && (
              <p className="text-xs text-muted-foreground font-mono">
                ID: {post.post_id}
              </p>
            )}
          </>
        ) : (
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-destructive">Failed to schedule</p>
              <p className="text-sm text-muted-foreground">{post.message}</p>
            </div>
          </div>
        )}
      </div>
    </ToolCallCard>
  );
}

function PreviewCard({ preview }: { preview: PreviewPostResult }) {
  return (
    <ToolCallCard icon={Eye} title="Content Preview">
      <div className="space-y-4">
        {preview.preview_text && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Content</p>
            <div className="rounded-md bg-muted p-3 text-sm leading-relaxed">
              {preview.preview_text}
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Characters:</span>
            <span className="font-medium">{preview.character_count}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Est. Reach:</span>
            <span className="font-medium">{preview.estimated_reach}</span>
          </div>
        </div>

        {preview.platform_specific_notes && preview.platform_specific_notes.length > 0 && (
          <div className="space-y-2">
            <Separator />
            <p className="text-sm font-medium">Platform Notes</p>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {preview.platform_specific_notes.map((note, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-muted-foreground mt-1.5">•</span>
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {preview.suggestions && preview.suggestions.length > 0 && (
          <div className="space-y-2">
            <Separator />
            <p className="text-sm font-medium">Suggestions</p>
            <ul className="space-y-1.5 text-sm text-muted-foreground">
              {preview.suggestions.map((suggestion, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-muted-foreground mt-1.5">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </ToolCallCard>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className="space-y-4">
      {isUser ? (
        <UserMessage content={message.content} timestamp={message.timestamp} />
      ) : (
        <>
          <AIMessage content={message.content} timestamp={message.timestamp} />

          {/* Tool results */}
          {(message.scheduled_posts?.length || message.previews?.length) ? (
            <div className="ml-12 space-y-3">
              {message.previews?.map((preview, idx) => (
                <PreviewCard key={idx} preview={preview} />
              ))}

              {message.scheduled_posts?.map((post, idx) => (
                <ScheduledPostCard key={idx} post={post} />
              ))}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export function LoadingMessage() {
  return (
    <div className="flex gap-4 justify-start">
      <div className="flex-shrink-0 w-8 h-8 rounded-full border-2 border-border flex items-center justify-center bg-background">
        <Bot className="w-4 h-4" />
      </div>
      <div className="rounded-2xl bg-muted px-4 py-3">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce" />
          <div
            className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
            style={{ animationDelay: '0.15s' }}
          />
          <div
            className="w-2 h-2 bg-foreground/40 rounded-full animate-bounce"
            style={{ animationDelay: '0.3s' }}
          />
        </div>
      </div>
    </div>
  );
}
