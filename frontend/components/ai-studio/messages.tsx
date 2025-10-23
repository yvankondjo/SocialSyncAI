/**
 * Message Components
 * Clean, minimalist message display components for AI Studio
 */

'use client';

import { Message } from '@/types/ai-studio';
import { ScheduledPostResult, PreviewPostResult } from '@/lib/api/ai-studio';
import { Bot, User, CheckCircle2, XCircle, Eye, Clock, Lightbulb, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface MessageBubbleProps {
  message: Message;
}

function UserMessage({ content, timestamp }: { content: string; timestamp: string }) {
  return (
    <div className="flex gap-3 justify-end group">
      <div className="flex flex-col items-end gap-2 max-w-[80%]">
        <div className="rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-3 shadow-sm">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
        <div className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
          {format(new Date(timestamp), 'HH:mm')}
        </div>
      </div>
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-slate-700 dark:to-slate-800 flex items-center justify-center shadow-sm">
        <User className="w-4 h-4 text-slate-600 dark:text-slate-300" />
      </div>
    </div>
  );
}

function AIMessage({ content, timestamp }: { content: string; timestamp: string }) {
  return (
    <div className="flex gap-3 justify-start group">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary/10 to-primary/20 flex items-center justify-center shadow-sm">
        <Bot className="w-4 h-4 text-primary" />
      </div>
      <div className="flex flex-col items-start gap-2 max-w-[80%]">
        <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3 shadow-sm">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap text-foreground">
            {content}
          </p>
        </div>
        <div className="text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity">
          {format(new Date(timestamp), 'HH:mm')}
        </div>
      </div>
    </div>
  );
}

function ScheduledPostCard({ post }: { post: ScheduledPostResult }) {
  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-all hover:shadow-md',
        post.success
          ? 'border-green-200 bg-green-50/50 dark:border-green-900/50 dark:bg-green-950/20'
          : 'border-red-200 bg-red-50/50 dark:border-red-900/50 dark:bg-red-950/20'
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center',
            post.success
              ? 'bg-green-500/10 dark:bg-green-500/20'
              : 'bg-red-500/10 dark:bg-red-500/20'
          )}
        >
          {post.success ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-500" />
          ) : (
            <XCircle className="w-5 h-5 text-red-600 dark:text-red-500" />
          )}
        </div>

        <div className="flex-1 min-w-0 space-y-2">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'text-sm font-semibold',
                post.success
                  ? 'text-green-900 dark:text-green-100'
                  : 'text-red-900 dark:text-red-100'
              )}
            >
              {post.success ? 'Successfully Scheduled' : 'Scheduling Failed'}
            </span>
            {post.platform && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-background border capitalize">
                {post.platform}
              </span>
            )}
          </div>

          <p className="text-sm text-muted-foreground leading-relaxed">
            {post.message}
          </p>

          {post.scheduled_for && post.success && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-background/50 rounded-md px-3 py-2 border">
              <Clock className="w-3.5 h-3.5" />
              <span className="font-medium">
                {format(new Date(post.scheduled_for), 'PPp')}
              </span>
            </div>
          )}

          {post.post_id && (
            <div className="text-xs text-muted-foreground font-mono bg-background/50 rounded px-2 py-1 inline-block border">
              ID: {post.post_id}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PreviewCard({ preview }: { preview: PreviewPostResult }) {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50/50 dark:border-blue-900/50 dark:bg-blue-950/20 p-4 transition-all hover:shadow-md">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-blue-500/10 dark:bg-blue-500/20 flex items-center justify-center">
          <Eye className="w-5 h-5 text-blue-600 dark:text-blue-500" />
        </div>

        <div className="flex-1 min-w-0 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-blue-900 dark:text-blue-100">
              Content Preview
            </span>
          </div>

          {preview.preview_text && (
            <p className="text-sm text-foreground leading-relaxed bg-background/50 rounded-md p-3 border">
              {preview.preview_text}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              <span className="font-medium">{preview.character_count}</span>
              <span className="text-xs">characters</span>
            </div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              <span className="text-xs">Est. Reach:</span>
              <span className="font-medium">{preview.estimated_reach}</span>
            </div>
          </div>

          {preview.platform_specific_notes && preview.platform_specific_notes.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 dark:text-blue-100">
                <Calendar className="w-3.5 h-3.5" />
                Platform Notes
              </div>
              <ul className="space-y-1">
                {preview.platform_specific_notes.map((note, i) => (
                  <li
                    key={i}
                    className="text-xs text-muted-foreground pl-5 relative before:content-['•'] before:absolute before:left-1.5"
                  >
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.suggestions && preview.suggestions.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 dark:text-blue-100">
                <Lightbulb className="w-3.5 h-3.5" />
                Suggestions
              </div>
              <ul className="space-y-1">
                {preview.suggestions.map((suggestion, i) => (
                  <li
                    key={i}
                    className="text-xs text-muted-foreground pl-5 relative before:content-['•'] before:absolute before:left-1.5"
                  >
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className="space-y-3">
      {/* Main message bubble */}
      {isUser ? (
        <UserMessage content={message.content} timestamp={message.timestamp} />
      ) : (
        <AIMessage content={message.content} timestamp={message.timestamp} />
      )}

      {/* Tool result cards (only for AI messages) */}
      {!isUser && (
        <div className="ml-11 space-y-3 max-w-[80%]">
          {/* Scheduled posts */}
          {message.scheduled_posts && message.scheduled_posts.length > 0 && (
            <div className="space-y-2">
              {message.scheduled_posts.map((post, idx) => (
                <ScheduledPostCard key={idx} post={post} />
              ))}
            </div>
          )}

          {/* Previews */}
          {message.previews && message.previews.length > 0 && (
            <div className="space-y-2">
              {message.previews.map((preview, idx) => (
                <PreviewCard key={idx} preview={preview} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function LoadingMessage() {
  return (
    <div className="flex gap-3 justify-start">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary/10 to-primary/20 flex items-center justify-center shadow-sm">
        <Bot className="w-4 h-4 text-primary" />
      </div>
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce" />
          <div
            className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"
            style={{ animationDelay: '0.1s' }}
          />
          <div
            className="w-2 h-2 bg-muted-foreground/40 rounded-full animate-bounce"
            style={{ animationDelay: '0.2s' }}
          />
        </div>
      </div>
    </div>
  );
}
