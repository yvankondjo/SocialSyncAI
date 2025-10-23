"use client"

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { useCreateScheduledPost } from '@/lib/api/scheduled-posts';
import { SocialAccountsService, type SocialAccount } from '@/lib/api';
import { format } from 'date-fns';
import { Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CreatePostDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreatePostDialog({ open, onOpenChange }: CreatePostDialogProps) {
  const [channels, setChannels] = useState<SocialAccount[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState('');
  const [content, setContent] = useState('');
  const [publishDate, setPublishDate] = useState<Date | undefined>(undefined);
  const [publishTime, setPublishTime] = useState('12:00');
  const [mediaUrl, setMediaUrl] = useState('');
  const [isLoadingChannels, setIsLoadingChannels] = useState(true);

  const createMutation = useCreateScheduledPost();

  useEffect(() => {
    if (open) {
      loadChannels();
    }
  }, [open]);

  const loadChannels = async () => {
    try {
      setIsLoadingChannels(true);
      const { accounts } = await SocialAccountsService.getSocialAccounts();
      setChannels(accounts.filter(a => a.is_active));
    } catch (error) {
      console.error('Failed to load channels:', error);
    } finally {
      setIsLoadingChannels(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedChannelId || !content || !publishDate) {
      return;
    }

    const [hours, minutes] = publishTime.split(':').map(Number);
    const publishAt = new Date(publishDate);
    publishAt.setHours(hours, minutes, 0, 0);

    const postData = {
      channel_id: selectedChannelId,
      content: {
        text: content,
        media: mediaUrl ? [{ type: 'image' as const, url: mediaUrl }] : undefined,
      },
      publish_at: publishAt.toISOString(),
    };

    createMutation.mutate(postData, {
      onSuccess: () => {
        handleClose();
      },
    });
  };

  const handleClose = () => {
    setSelectedChannelId('');
    setContent('');
    setPublishDate(undefined);
    setPublishTime('12:00');
    setMediaUrl('');
    onOpenChange(false);
  };

  const minDate = new Date();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px]">
        <DialogHeader className="space-y-1">
          <DialogTitle className="text-xl font-semibold">Create Scheduled Post</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Schedule a new post to publish across your connected social media accounts
          </p>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5 pt-2">
          {/* Channel Selection */}
          <div className="space-y-2.5">
            <Label htmlFor="channel" className="text-sm font-medium">
              Channel <span className="text-destructive">*</span>
            </Label>
            <Select
              value={selectedChannelId}
              onValueChange={setSelectedChannelId}
              disabled={isLoadingChannels}
            >
              <SelectTrigger id="channel" className="h-11">
                <SelectValue placeholder="Select a channel to post to" />
              </SelectTrigger>
              <SelectContent>
                {channels.map((channel) => (
                  <SelectItem key={channel.id} value={channel.id}>
                    <div className="flex items-center gap-2">
                      <span className="capitalize font-medium">{channel.platform}</span>
                      <span className="text-muted-foreground">•</span>
                      <span className="text-muted-foreground">{channel.username}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

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
              required
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                {content.length} character{content.length !== 1 ? 's' : ''}
              </p>
              {content.length > 280 && (
                <p className="text-xs text-orange-600 dark:text-orange-400">
                  Note: Twitter has a 280 character limit
                </p>
              )}
            </div>
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
                    disabled={(date: Date) => date < minDate}
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
                required
              />
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0 pt-4 border-t">
            <Button type="button" variant="outline" onClick={handleClose} className="h-10">
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending || !selectedChannelId || !content || !publishDate}
              className="h-10 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
            >
              {createMutation.isPending ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  Scheduling...
                </>
              ) : (
                'Schedule Post'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
