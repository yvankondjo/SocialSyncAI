"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { usePostRuns } from '@/lib/api/scheduled-posts';
import { format } from 'date-fns';
import { CheckCircle, X as XCircle, Clock } from 'lucide-react';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface HistoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  post: ScheduledPost;
}

export function HistoryDialog({ open, onOpenChange, post }: HistoryDialogProps) {
  const { data: runs = [], isLoading } = usePostRuns(post.id, undefined, open);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[650px]">
        <DialogHeader className="space-y-1">
          <DialogTitle className="text-xl font-semibold">Execution History</DialogTitle>
          <p className="text-sm text-muted-foreground">
            View all publishing attempts for this post
          </p>
        </DialogHeader>

        <ScrollArea className="max-h-[450px] pr-4 pt-2">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
            </div>
          ) : runs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="rounded-full bg-muted/50 p-4 mb-4">
                <Clock className="w-8 h-8 text-muted-foreground/50" aria-hidden="true" />
              </div>
              <h3 className="font-medium text-foreground mb-1">No execution history yet</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                This post has not been attempted to publish. History will appear here once publishing begins.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {runs.map((run, index) => {
                const startedAt = new Date(run.started_at);
                const finishedAt = run.finished_at ? new Date(run.finished_at) : null;
                const duration = finishedAt
                  ? Math.round((finishedAt.getTime() - startedAt.getTime()) / 1000)
                  : null;
                const isSuccess = run.status === 'success';

                return (
                  <div
                    key={run.id}
                    className="border border-border/60 rounded-lg p-4 space-y-3 bg-card hover:border-border transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 ${isSuccess ? 'text-green-600 dark:text-green-400' : 'text-destructive'}`}>
                          {isSuccess ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <XCircle className="w-5 h-5" />
                          )}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-foreground">
                              Attempt {runs.length - index}
                            </span>
                            <Badge
                              variant={isSuccess ? 'outline' : 'destructive'}
                              className="capitalize"
                            >
                              {run.status}
                            </Badge>
                          </div>
                          <div className="space-y-1 text-sm text-muted-foreground">
                            <p>
                              <span className="font-medium">Started:</span> {format(startedAt, 'PPp')}
                            </p>
                            {finishedAt && (
                              <p>
                                <span className="font-medium">Finished:</span> {format(finishedAt, 'PPp')}
                                {duration !== null && (
                                  <span className="ml-2 text-xs bg-muted px-2 py-0.5 rounded">
                                    {duration}s
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {run.error && (
                      <div className="rounded-lg bg-destructive/10 border border-destructive/30 p-3">
                        <p className="text-sm text-destructive font-semibold mb-1.5">Error Details</p>
                        <p className="text-sm text-destructive/90 leading-relaxed">{run.error}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
