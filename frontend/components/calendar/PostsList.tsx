"use client"

import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { PostListItem } from './PostListItem';
import { ChevronRight, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ScheduledPost } from '@/types/scheduled-posts';
import { useState } from 'react';

interface PostsListProps {
  title: string;
  posts: ScheduledPost[];
  isLoading: boolean;
  defaultOpen?: boolean;
  onEditPost: (post: ScheduledPost) => void;
  onPreviewPost: (post: ScheduledPost) => void;
  onHistoryPost: (post: ScheduledPost) => void;
  onDeletePost: (post: ScheduledPost) => void;
}

export function PostsList({
  title,
  posts,
  isLoading,
  defaultOpen = false,
  onEditPost,
  onPreviewPost,
  onHistoryPost,
  onDeletePost,
}: PostsListProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="space-y-3">
      <CollapsibleTrigger className="flex items-center justify-between w-full group hover:bg-muted/50 rounded-lg px-2 py-1.5 transition-colors">
        <div className="flex items-center gap-2.5">
          <ChevronRight
            className={cn(
              "w-4 h-4 transition-transform duration-200 text-muted-foreground",
              isOpen && "rotate-90"
            )}
            aria-hidden="true"
          />
          <span className="text-sm font-semibold text-foreground">
            {title}
          </span>
          <Badge variant="secondary" className="h-5 px-2 text-xs font-medium">
            {posts.length}
          </Badge>
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="pl-1">
        <div className="space-y-2">
          {isLoading ? (
            <>
              <Skeleton className="h-24 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg" />
            </>
          ) : posts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 px-4 text-center rounded-lg border border-dashed border-border/60 bg-muted/20">
              <FileText className="h-8 w-8 text-muted-foreground/50 mb-2" aria-hidden="true" />
              <p className="text-sm text-muted-foreground">
                No {title.toLowerCase()} yet
              </p>
            </div>
          ) : (
            posts.map((post) => (
              <PostListItem
                key={post.id}
                post={post}
                onEdit={() => onEditPost(post)}
                onPreview={() => onPreviewPost(post)}
                onHistory={() => onHistoryPost(post)}
                onDelete={() => onDeletePost(post)}
              />
            ))
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
