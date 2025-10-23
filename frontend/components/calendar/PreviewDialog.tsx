"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { format, isPast } from 'date-fns';
import { Trash2, Clock, Edit2, Instagram, Facebook, Twitter, MessageCircle, Image as ImageIcon, AlertCircle } from 'lucide-react';
import type { ScheduledPost, Platform, PostStatus } from '@/types/scheduled-posts';
import type { LucideIcon } from 'lucide-react';

interface PreviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  post: ScheduledPost;
  onEdit: () => void;
  onDelete: () => void;
}

const PLATFORM_INFO: Record<Platform, { Icon: LucideIcon; label: string; color: string; bgColor: string }> = {
  instagram: {
    Icon: Instagram,
    label: 'Instagram',
    color: 'text-pink-600 dark:text-pink-400',
    bgColor: 'bg-pink-50 dark:bg-pink-950/20',
  },
  facebook: {
    Icon: Facebook,
    label: 'Facebook',
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
  },
  twitter: {
    Icon: Twitter,
    label: 'Twitter',
    color: 'text-sky-600 dark:text-sky-400',
    bgColor: 'bg-sky-50 dark:bg-sky-950/20',
  },
  whatsapp: {
    Icon: MessageCircle,
    label: 'WhatsApp',
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
  },
};

const STATUS_STYLES: Record<PostStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
  draft: { variant: 'secondary', label: 'Draft' },
  queued: { variant: 'default', label: 'Queued' },
  publishing: { variant: 'outline', label: 'Publishing' },
  published: { variant: 'outline', label: 'Published' },
  failed: { variant: 'destructive', label: 'Failed' },
  cancelled: { variant: 'secondary', label: 'Cancelled' },
};

export function PreviewDialog({ open, onOpenChange, post, onEdit, onDelete }: PreviewDialogProps) {
  const publishDate = new Date(post.publish_at);
  const isPostPast = isPast(publishDate);
  const canEdit = !isPostPast && !['published', 'publishing'].includes(post.status);
  const canDelete = post.status !== 'published';

  const platformInfo = PLATFORM_INFO[post.platform];
  const statusStyle = STATUS_STYLES[post.status];
  const PlatformIcon = platformInfo.Icon;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px]">
        <DialogHeader className="space-y-3">
          <DialogTitle className="text-xl font-semibold">Post Preview</DialogTitle>

          {/* Platform & Status */}
          <div className="flex items-center justify-between">
            <div className={`flex items-center gap-2.5 px-3 py-2 rounded-lg ${platformInfo.bgColor}`}>
              <div className={platformInfo.color}>
                <PlatformIcon className="h-5 w-5" />
              </div>
              <span className="font-medium text-sm">{platformInfo.label}</span>
            </div>
            <Badge variant={statusStyle.variant} className="px-3 py-1">
              {statusStyle.label}
            </Badge>
          </div>
        </DialogHeader>

        <div className="space-y-5 pt-2">
          {/* Publish Date */}
          <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-muted/50 text-sm">
            <Clock className="w-4 h-4 text-muted-foreground" aria-hidden="true" />
            <span className="text-foreground/90">
              Scheduled for <span className="font-medium">{format(publishDate, 'PPP')}</span> at{' '}
              <span className="font-medium">{format(publishDate, 'p')}</span>
            </span>
          </div>

          {/* Content */}
          <div className="space-y-2.5">
            <h4 className="text-sm font-semibold text-foreground">Content</h4>
            <div className="rounded-lg border border-border/60 bg-muted/30 p-4">
              <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                {post.content_json.text}
              </p>
            </div>
          </div>

          {/* Media */}
          {post.content_json.media && post.content_json.media.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <ImageIcon className="w-4 h-4" aria-hidden="true" />
                Media ({post.content_json.media.length})
              </h4>
              <div className="grid grid-cols-2 gap-3">
                {post.content_json.media.map((media, index) => (
                  <div
                    key={index}
                    className="aspect-video rounded-lg overflow-hidden bg-muted border border-border/60"
                  >
                    {media.type === 'image' && (
                      <img
                        src={media.url}
                        alt={`Media ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Message */}
          {post.error_message && (
            <div className="space-y-2.5">
              <h4 className="text-sm font-semibold text-destructive flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Error Details
              </h4>
              <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-4">
                <p className="text-sm text-destructive leading-relaxed">{post.error_message}</p>
              </div>
            </div>
          )}

          {/* Metadata */}
          <Separator className="opacity-60" />
          <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
            <div className="space-y-1">
              <p className="font-medium text-foreground/70">Created</p>
              <p>{format(new Date(post.created_at), 'PPp')}</p>
            </div>
            <div className="space-y-1">
              <p className="font-medium text-foreground/70">Last Updated</p>
              <p>{format(new Date(post.updated_at), 'PPp')}</p>
            </div>
            {post.retry_count > 0 && (
              <div className="space-y-1 col-span-2">
                <p className="font-medium text-foreground/70">Retry Count</p>
                <p className="text-orange-600 dark:text-orange-400">
                  {post.retry_count} {post.retry_count === 1 ? 'attempt' : 'attempts'}
                </p>
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="h-10">
            Close
          </Button>
          {canEdit && (
            <Button variant="outline" onClick={onEdit} className="h-10">
              <Edit2 className="w-4 h-4 mr-2" />
              Edit
            </Button>
          )}
          {canDelete && (
            <Button variant="destructive" onClick={onDelete} className="h-10">
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
