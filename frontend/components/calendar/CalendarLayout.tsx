"use client"

import { useState } from 'react';
import { CalendarHeader } from './CalendarHeader';
import { CalendarGrid } from './CalendarGrid';
import { SidebarPanel } from './SidebarPanel';
import { CreatePostDialog } from './CreatePostDialog';
import { EditPostDialog } from './EditPostDialog';
import { PreviewDialog } from './PreviewDialog';
import { HistoryDialog } from './HistoryDialog';
import { DeleteConfirmDialog } from './DeleteConfirmDialog';
import { startOfMonth, endOfMonth } from 'date-fns';
import { useScheduledPosts } from '@/lib/api/scheduled-posts';
import type { ScheduledPost } from '@/types/scheduled-posts';

export function CalendarLayout() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedPost, setSelectedPost] = useState<ScheduledPost | null>(null);
  const [dialogState, setDialogState] = useState<{
    create: boolean;
    edit: boolean;
    preview: boolean;
    history: boolean;
    delete: boolean;
  }>({
    create: false,
    edit: false,
    preview: false,
    history: false,
    delete: false,
  });

  const { data, isLoading } = useScheduledPosts({});
  const posts = data?.posts || [];

  const handleOpenDialog = (type: keyof typeof dialogState, post?: ScheduledPost) => {
    if (post) setSelectedPost(post);
    setDialogState(prev => ({ ...prev, [type]: true }));
  };

  const handleCloseDialog = (type: keyof typeof dialogState) => {
    setDialogState(prev => ({ ...prev, [type]: false }));
    if (type !== 'create') {
      setTimeout(() => setSelectedPost(null), 200);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <div className="flex flex-1 overflow-hidden">
        {/* Main Calendar Area - 70% */}
        <main className="flex-1 flex flex-col overflow-hidden" role="main" aria-label="Calendar view">
          <CalendarHeader
            currentDate={currentDate}
            onDateChange={setCurrentDate}
          />
          <CalendarGrid
            currentDate={currentDate}
            posts={posts}
            onPostClick={(post) => handleOpenDialog('preview', post)}
          />
        </main>

        {/* Sidebar Panel - 30% */}
        <div className="hidden lg:flex w-full lg:w-[32%] min-w-[320px] max-w-[420px] flex-col">
          <SidebarPanel
            posts={posts}
            isLoading={isLoading}
            onCreatePost={() => handleOpenDialog('create')}
            onEditPost={(post) => handleOpenDialog('edit', post)}
            onPreviewPost={(post) => handleOpenDialog('preview', post)}
            onHistoryPost={(post) => handleOpenDialog('history', post)}
            onDeletePost={(post) => handleOpenDialog('delete', post)}
          />
        </div>
      </div>

      {/* Dialogs */}
      <CreatePostDialog
        open={dialogState.create}
        onOpenChange={(open) => !open && handleCloseDialog('create')}
      />

      {selectedPost && (
        <>
          <EditPostDialog
            open={dialogState.edit}
            onOpenChange={(open) => !open && handleCloseDialog('edit')}
            post={selectedPost}
          />
          <PreviewDialog
            open={dialogState.preview}
            onOpenChange={(open) => !open && handleCloseDialog('preview')}
            post={selectedPost}
            onEdit={() => {
              handleCloseDialog('preview');
              handleOpenDialog('edit', selectedPost);
            }}
            onDelete={() => {
              handleCloseDialog('preview');
              handleOpenDialog('delete', selectedPost);
            }}
          />
          <HistoryDialog
            open={dialogState.history}
            onOpenChange={(open) => !open && handleCloseDialog('history')}
            post={selectedPost}
          />
          <DeleteConfirmDialog
            open={dialogState.delete}
            onOpenChange={(open) => !open && handleCloseDialog('delete')}
            post={selectedPost}
          />
        </>
      )}
    </div>
  );
}
