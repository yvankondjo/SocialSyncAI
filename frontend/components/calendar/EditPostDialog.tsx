"use client"

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useUpdateScheduledPost } from '@/lib/api/scheduled-posts';
import { format, isPast } from 'date-fns';
import { Clock, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface EditPostDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  post: ScheduledPost;
}

export function EditPostDialog({ open, onOpenChange, post }: EditPostDialogProps) {
  const [content, setContent] = useState('');
  const [publishDate, setPublishDate] = useState<Date | undefined>(undefined);
  const [publishTime, setPublishTime] = useState('12:00');
  const [mediaUrl, setMediaUrl] = useState('');

  const updateMutation = useUpdateScheduledPost();

  const originalPublishDate = new Date(post.publish_at);
  const isPostPast = isPast(originalPublishDate);
  const isPublishedOrPublishing = ['published', 'publishing'].includes(post.status);
  const isReadOnly = isPostPast || isPublishedOrPublishing;

  useEffect(() => {
    if (open && post) {
      setContent(post.content_json.text);
      setPublishDate(originalPublishDate);
      setPublishTime(format(originalPublishDate, 'HH:mm'));
      setMediaUrl(post.content_json.media?.[0]?.url || '');
    }
  }, [open, post]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isReadOnly || !content || !publishDate) {
      return;
    }

    const [hours, minutes] = publishTime.split(':').map(Number);
    const publishAt = new Date(publishDate);
    publishAt.setHours(hours, minutes, 0, 0);

    const updateData = {
      content: {
        text: content,
        media: mediaUrl ? [{ type: 'image' as const, url: mediaUrl }] : undefined,
      },
      publish_at: publishAt.toISOString(),
    };

    updateMutation.mutate(
      { id: post.id, data: updateData },
      {
        onSuccess: () => {
          onOpenChange(false);
        },
      }
    );
  };

  const minDate = new Date();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px]">
        <DialogHeader className="space-y-1">
          <DialogTitle className="text-xl font-semibold">Edit Scheduled Post</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Update your post content and schedule
          </p>
        </DialogHeader>

        {isReadOnly && (
          <Alert variant="destructive" className="mt-2">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {isPublishedOrPublishing
                ? 'This post has already been published or is currently publishing. It cannot be edited.'
                : 'This post is scheduled in the past and cannot be edited.'}
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 pt-2">
          {/* Content */}
          <div className="space-y-2.5">
            <Label htmlFor="content" className="text-sm font-medium">
              Post Content <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="content"
              placeholder="Write your post content here..."
              value={content}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setContent(e.target.value)}
              rows={6}
              className="resize-none"
              disabled={isReadOnly}
              required
            />
            <p className="text-xs text-muted-foreground">
              {content.length} character{content.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Media URL (Optional) */}
          <div className="space-y-2.5">
            <Label htmlFor="media" className="text-sm font-medium">
              Media URL <span className="text-xs text-muted-foreground font-normal">(optional)</span>
            </Label>
            <Input
              id="media"
              type="url"
              placeholder="https://example.com/image.jpg"
              value={mediaUrl}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMediaUrl(e.target.value)}
              className="h-11"
              disabled={isReadOnly}
            />
          </div>

          {/* Publish Date & Time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2.5">
              <Label className="text-sm font-medium">
                Publish Date <span className="text-destructive">*</span>
              </Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "w-full h-11 justify-start text-left font-normal",
                      !publishDate && "text-muted-foreground"
                    )}
                    disabled={isReadOnly}
                  >
                    <Clock className="mr-2 h-4 w-4" />
                    {publishDate ? format(publishDate, 'PPP') : 'Pick a date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={publishDate}
                    onSelect={(date: Date | undefined) => setPublishDate(date)}
                    disabled={(date: Date) => date < minDate || isReadOnly}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2.5">
              <Label htmlFor="time" className="text-sm font-medium">
                Time <span className="text-destructive">*</span>
              </Label>
              <Input
                id="time"
                type="time"
                value={publishTime}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPublishTime(e.target.value)}
                className="h-11"
                disabled={isReadOnly}
                required
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} className="h-10">
              {isReadOnly ? 'Close' : 'Cancel'}
            </Button>
            {!isReadOnly && (
              <Button
                type="submit"
                disabled={updateMutation.isPending || !content || !publishDate}
                className="h-10 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
              >
                {updateMutation.isPending ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                    Updating...
                  </>
                ) : (
                  'Update Post'
                )}
              </Button>
            )}
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
