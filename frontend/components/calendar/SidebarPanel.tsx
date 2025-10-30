"use client"

import { useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { PostsList } from './PostsList';
import { Plus, Calendar } from 'lucide-react';
import type { ScheduledPost } from '@/types/scheduled-posts';

interface SidebarPanelProps {
  posts: ScheduledPost[];
  isLoading: boolean;
  onCreatePost: () => void;
  onEditPost: (post: ScheduledPost) => void;
  onPreviewPost: (post: ScheduledPost) => void;
  onHistoryPost: (post: ScheduledPost) => void;
  onDeletePost: (post: ScheduledPost) => void;
}

export function SidebarPanel({
  posts,
  isLoading,
  onCreatePost,
  onEditPost,
  onPreviewPost,
  onHistoryPost,
  onDeletePost,
}: SidebarPanelProps) {
  // Memoize filtered posts to prevent recalculation on every render
  const { draftPosts, scheduledPosts, publishedPosts } = useMemo(() => ({
    draftPosts: posts.filter(p => p.status === 'draft'),
    scheduledPosts: posts.filter(p => ['queued', 'publishing'].includes(p.status)),
    publishedPosts: posts.filter(p => p.status === 'published'),
  }), [posts]);

  return (
    <aside className="flex flex-col h-full bg-background/50 border-l border-border/60">
      {/* Header with Create Button */}
      <div className="p-4 space-y-3">
        <div className="flex items-center gap-2 px-1">
          <Calendar className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-foreground">Scheduled Posts</h2>
        </div>
        <Button
          onClick={onCreatePost}
          className="w-full h-10 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm transition-all duration-200 hover:shadow"
          size="default"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Post
        </Button>
      </div>

      <Separator className="opacity-60" />

      {/* Posts Lists */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Scheduled Section (default open) */}
          <PostsList
            title="Scheduled"
            posts={scheduledPosts}
            isLoading={isLoading}
            defaultOpen={true}
            onEditPost={onEditPost}
            onPreviewPost={onPreviewPost}
            onHistoryPost={onHistoryPost}
            onDeletePost={onDeletePost}
          />

          {/* Drafts Section */}
          <PostsList
            title="Drafts"
            posts={draftPosts}
            isLoading={isLoading}
            defaultOpen={false}
            onEditPost={onEditPost}
            onPreviewPost={onPreviewPost}
            onHistoryPost={onHistoryPost}
            onDeletePost={onDeletePost}
          />

          {/* Published Section (collapsible) */}
          <PostsList
            title="Published"
            posts={publishedPosts}
            isLoading={isLoading}
            defaultOpen={false}
            onEditPost={onEditPost}
            onPreviewPost={onPreviewPost}
            onHistoryPost={onHistoryPost}
            onDeletePost={onDeletePost}
          />
        </div>
      </ScrollArea>
    </aside>
  );
}
