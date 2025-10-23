"use client"

import { format, isPast } from 'date-fns';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MoreHorizontal, Eye, Edit2, Clock, Trash2, Instagram, Facebook, Twitter, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScheduledPost, Platform, PostStatus } from '@/types/scheduled-posts';
import type { LucideIcon } from 'lucide-react';

interface PostListItemProps {
  post: ScheduledPost;
  onEdit: () => void;
  onPreview: () => void;
  onHistory: () => void;
  onDelete: () => void;
}

const PLATFORM_CONFIG: Record<Platform, { Icon: LucideIcon; color: string; label: string }> = {
  instagram: {
    Icon: Instagram,
    color: 'text-pink-600 dark:text-pink-400',
    label: 'Instagram',
  },
  facebook: {
    Icon: Facebook,
    color: 'text-blue-600 dark:text-blue-400',
    label: 'Facebook',
  },
  twitter: {
    Icon: Twitter,
    color: 'text-sky-600 dark:text-sky-400',
    label: 'Twitter',
  },
  whatsapp: {
    Icon: MessageCircle,
    color: 'text-green-600 dark:text-green-400',
    label: 'WhatsApp',
  },
};

const STATUS_CONFIG: Record<PostStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string; color: string }> = {
  draft: { variant: 'secondary', label: 'Draft', color: 'text-muted-foreground' },
  queued: { variant: 'default', label: 'Queued', color: 'text-blue-600' },
  publishing: { variant: 'outline', label: 'Publishing', color: 'text-orange-600' },
  published: { variant: 'outline', label: 'Published', color: 'text-green-600' },
  failed: { variant: 'destructive', label: 'Failed', color: 'text-destructive' },
  cancelled: { variant: 'secondary', label: 'Cancelled', color: 'text-muted-foreground' },
};

export function PostListItem({ post, onEdit, onPreview, onHistory, onDelete }: PostListItemProps) {
  const publishDate = new Date(post.publish_at);
  const isPostPast = isPast(publishDate) && post.status !== 'published';
  const hasMedia = post.content_json.media && post.content_json.media.length > 0;
  const textPreview = post.content_json.text.slice(0, 70) + (post.content_json.text.length > 70 ? '...' : '');

  const platformConfig = PLATFORM_CONFIG[post.platform];
  const statusConfig = STATUS_CONFIG[post.status];
  const PlatformIcon = platformConfig.Icon;

  return (
    <div
      className={cn(
        "group relative border border-border/60 rounded-lg p-3 bg-card transition-all duration-200",
        "hover:border-border hover:shadow-md hover:shadow-black/5",
        isPostPast && "opacity-60"
      )}
    >
      <div className="flex items-start gap-3">
        {/* Media Thumbnail or Platform Icon */}
        <div className="flex-shrink-0 w-10 h-10 rounded-md bg-muted/50 flex items-center justify-center overflow-hidden border border-border/40">
          {hasMedia && post.content_json.media?.[0]?.type === 'image' ? (
            <img
              src={post.content_json.media[0].url}
              alt="Post preview"
              className="w-full h-full object-cover"
            />
          ) : (
            <div className={platformConfig.color}>
              <PlatformIcon className="h-5 w-5" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1.5">
            <div className="flex items-center gap-2">
              <span className={cn("text-xs font-medium", platformConfig.color)}>
                {platformConfig.label}
              </span>
              <Badge variant={statusConfig.variant} className="h-5 text-xs px-2">
                {statusConfig.label}
              </Badge>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity focus-visible:opacity-100"
                >
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Open actions menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={onPreview}>
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </DropdownMenuItem>
                {!isPostPast && post.status !== 'published' && (
                  <DropdownMenuItem onClick={onEdit}>
                    <Edit2 className="w-4 h-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem onClick={onHistory}>
                  <Clock className="w-4 h-4 mr-2" />
                  History
                </DropdownMenuItem>
                {post.status !== 'published' && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={onDelete} className="text-destructive focus:text-destructive">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <p className="text-sm text-foreground/90 line-clamp-2 mb-2 leading-relaxed">
            {textPreview}
          </p>

          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" aria-hidden="true" />
            <time dateTime={publishDate.toISOString()}>
              {format(publishDate, 'MMM d, h:mm a')}
            </time>
            {post.retry_count > 0 && (
              <>
                <span className="text-muted-foreground/50">•</span>
                <span className="text-orange-600 dark:text-orange-400">
                  {post.retry_count} {post.retry_count === 1 ? 'retry' : 'retries'}
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
