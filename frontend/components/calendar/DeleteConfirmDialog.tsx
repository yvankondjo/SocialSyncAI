"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useDeleteScheduledPost } from '@/lib/api/scheduled-posts';
import { AlertCircle } from 'lucide-react';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  post: ScheduledPost;
}

export function DeleteConfirmDialog({ open, onOpenChange, post }: DeleteConfirmDialogProps) {
  const deleteMutation = useDeleteScheduledPost();

  const handleDelete = () => {
    deleteMutation.mutate(post.id, {
      onSuccess: () => {
        onOpenChange(false);
      },
    });
  };

  const isPublished = post.status === 'published';

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader className="space-y-2">
          <DialogTitle className="text-xl font-semibold flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            Delete Scheduled Post
          </DialogTitle>
          <DialogDescription className="text-sm">
            This action cannot be undone. The post will be permanently removed from your schedule.
          </DialogDescription>
        </DialogHeader>

        <div className="pt-2 space-y-4">
          {isPublished && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This post has already been published and cannot be deleted.
              </AlertDescription>
            </Alert>
          )}

          {!isPublished && (
            <div className="rounded-lg border border-border/60 bg-muted/30 p-4">
              <p className="text-sm font-semibold text-foreground mb-2">Post Preview</p>
              <p className="text-sm text-foreground/80 leading-relaxed line-clamp-4">
                {post.content_json.text}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="h-10">
            Cancel
          </Button>
          {!isPublished && (
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="h-10"
            >
              {deleteMutation.isPending ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-destructive-foreground border-t-transparent" />
                  Deleting...
                </>
              ) : (
                'Delete Post'
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
