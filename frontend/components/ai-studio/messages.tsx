'use client';

import { Message } from '@/types/ai-studio';
import { ScheduledPostResult, PreviewPostResult } from '@/lib/api/ai-studio';
import { Bot, User, Calendar, Eye, Clock, AlertCircle, CheckCircle2, Lightbulb, Info } from 'lucide-react';
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

function ScheduledPostCard({ post }: { post: ScheduledPostResult }) {
  const isSuccess = post.success;

  return (
    <div className={cn(
      "rounded-lg border-2 overflow-hidden",
      isSuccess
        ? "border-green-500/50 bg-green-50/50 dark:bg-green-950/20"
        : "border-red-500/50 bg-red-50/50 dark:bg-red-950/20"
    )}>
      {/* Header */}
      <div className={cn(
        "flex items-center gap-2 px-4 py-3 border-b",
        isSuccess
          ? "bg-green-100/50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
          : "bg-red-100/50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
      )}>
        {isSuccess ? (
          <>
            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
            <span className="text-sm font-medium text-green-900 dark:text-green-100">
              Post Scheduled Successfully
            </span>
          </>
        ) : (
          <>
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400" />
            <span className="text-sm font-medium text-red-900 dark:text-red-100">
              Scheduling Failed
            </span>
          </>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {isSuccess ? (
          <div className="space-y-3">
            {/* Success Message */}
            <div className="flex items-start gap-3">
              <div className="flex-1 space-y-2">
                <p className="text-sm text-foreground leading-relaxed">{post.message}</p>

                {/* Platform Badge */}
                {post.platform && (
                  <Badge
                    variant="secondary"
                    className="capitalize bg-green-100 dark:bg-green-900/30 text-green-900 dark:text-green-100 border-green-300 dark:border-green-700"
                  >
                    {post.platform}
                  </Badge>
                )}
              </div>
            </div>

            {/* Scheduled Time */}
            {post.scheduled_for && (
              <div className="flex items-center gap-2 text-sm bg-background/50 rounded-md px-3 py-2.5 border border-green-200 dark:border-green-800">
                <Clock className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
                <div className="flex-1">
                  <p className="font-medium text-foreground">
                    {format(new Date(post.scheduled_for), 'EEEE, MMMM d, yyyy')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    at {format(new Date(post.scheduled_for), 'h:mm a')}
                  </p>
                </div>
              </div>
            )}

            {/* Post ID */}
            {post.post_id && (
              <div className="pt-2 border-t border-green-200 dark:border-green-800">
                <p className="text-xs text-muted-foreground font-mono">
                  Post ID: {post.post_id.slice(0, 8)}...
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {/* Error Message */}
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1 space-y-2">
                <p className="text-sm font-medium text-red-900 dark:text-red-100">
                  Unable to schedule post
                </p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {post.message}
                </p>
              </div>
            </div>

            {/* Help Text */}
            <div className="flex items-start gap-2 text-xs bg-background/50 rounded-md px-3 py-2 border border-red-200 dark:border-red-800">
              <Info className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <p className="text-muted-foreground">
                Make sure you have an active social media account connected and the scheduled time is in the future.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function PreviewCard({ preview }: { preview: PreviewPostResult }) {
  return (
    <div className="rounded-lg border-2 border-blue-500/50 bg-blue-50/50 dark:bg-blue-950/20 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b bg-blue-100/50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <Eye className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
          Content Preview
        </span>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Preview Text */}
        {preview.preview_text && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Content</p>
            <div className="rounded-md bg-background border border-blue-200 dark:border-blue-800 p-3 text-sm leading-relaxed">
              {preview.preview_text}
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1 bg-background/50 rounded-md px-3 py-2 border border-blue-200 dark:border-blue-800">
            <span className="text-xs text-muted-foreground">Characters</span>
            <span className="text-lg font-semibold text-foreground">{preview.character_count}</span>
          </div>
          <div className="flex flex-col gap-1 bg-background/50 rounded-md px-3 py-2 border border-blue-200 dark:border-blue-800">
            <span className="text-xs text-muted-foreground">Est. Reach</span>
            <span className="text-sm font-medium text-foreground">{preview.estimated_reach}</span>
          </div>
        </div>

        {/* Platform Notes */}
        {preview.platform_specific_notes && preview.platform_specific_notes.length > 0 && (
          <div className="space-y-2">
            <Separator className="bg-blue-200 dark:bg-blue-800" />
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Platform Notes</p>
            </div>
            <ul className="space-y-2">
              {preview.platform_specific_notes.map((note, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-blue-600 dark:text-blue-400 mt-0.5">•</span>
                  <span className="text-muted-foreground">{note}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Suggestions */}
        {preview.suggestions && preview.suggestions.length > 0 && preview.suggestions.filter(s => s !== "Post looks good!").length > 0 && (
          <div className="space-y-2">
            <Separator className="bg-blue-200 dark:bg-blue-800" />
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400" />
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Suggestions</p>
            </div>
            <ul className="space-y-2">
              {preview.suggestions.map((suggestion, i) => (
                <li key={i} className="flex items-start gap-2 text-sm bg-amber-50/50 dark:bg-amber-950/20 rounded-md px-3 py-2 border border-amber-200 dark:border-amber-800">
                  <Lightbulb className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                  <span className="text-foreground">{suggestion}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* All Good Message */}
        {preview.suggestions && preview.suggestions.length === 1 && preview.suggestions[0] === "Post looks good!" && (
          <div className="flex items-center gap-2 text-sm bg-green-50/50 dark:bg-green-950/20 rounded-md px-3 py-2.5 border border-green-200 dark:border-green-800">
            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" />
            <span className="text-green-900 dark:text-green-100 font-medium">Post looks good!</span>
          </div>
        )}
      </div>
    </div>
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
