"use client"

import { cn } from '@/lib/utils';
import { Instagram, Facebook, Twitter, MessageCircle } from 'lucide-react';
import type { ScheduledPost, Platform, PostStatus } from '@/types/scheduled-posts';
import type { LucideIcon } from 'lucide-react';

interface PostCardMiniProps {
  post: ScheduledPost;
  onClick: () => void;
  isPast?: boolean;
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

const STATUS_INDICATOR: Record<PostStatus, { color: string; label: string }> = {
  draft: { color: 'bg-slate-400', label: 'Draft' },
  queued: { color: 'bg-blue-500', label: 'Queued' },
  publishing: { color: 'bg-orange-500', label: 'Publishing' },
  published: { color: 'bg-green-500', label: 'Published' },
  failed: { color: 'bg-red-500', label: 'Failed' },
  cancelled: { color: 'bg-slate-400', label: 'Cancelled' },
};

export function PostCardMini({ post, onClick, isPast }: PostCardMiniProps) {
  const platformConfig = PLATFORM_CONFIG[post.platform];
  const statusConfig = STATUS_INDICATOR[post.status];
  const Icon = platformConfig.Icon;
  const textPreview = post.content_json.text.slice(0, 50) + (post.content_json.text.length > 50 ? '...' : '');

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left rounded-md border border-border/60 bg-card p-2 transition-all duration-150",
        "hover:border-border hover:shadow-sm hover:scale-[1.02]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1",
        isPast && "opacity-50 cursor-not-allowed hover:scale-100"
      )}
      disabled={isPast}
      aria-label={`${platformConfig.label} post: ${textPreview}`}
    >
      <div className="flex items-start gap-2">
        {/* Platform Icon */}
        <div className={cn("flex-shrink-0 mt-0.5", platformConfig.color)} aria-hidden="true">
          <Icon className="h-3.5 w-3.5" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-xs leading-relaxed line-clamp-2 text-foreground/90">
            {textPreview}
          </p>
        </div>

        {/* Status Indicator Dot */}
        <div
          className={cn("flex-shrink-0 mt-1.5 h-1.5 w-1.5 rounded-full", statusConfig.color)}
          title={statusConfig.label}
          aria-label={`Status: ${statusConfig.label}`}
        />
      </div>
    </button>
  );
}
