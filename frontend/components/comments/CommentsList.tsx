"use client"

import { useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MessageSquare } from "lucide-react"
import { Comment } from "@/types/comments"
import { CommentItem } from "./CommentItem"
import { CommentReplyDialog } from "./CommentReplyDialog"

interface CommentsListProps {
  comments: Comment[]
  onReply: (commentId: string, text: string) => Promise<void>
  loading: boolean
  onLoadMore?: () => void
  hasMore?: boolean
}

export function CommentsList({
  comments,
  onReply,
  loading,
  onLoadMore,
  hasMore = false,
}: CommentsListProps) {
  const [replyDialogOpen, setReplyDialogOpen] = useState(false)
  const [selectedComment, setSelectedComment] = useState<Comment | null>(null)

  const handleOpenReplyDialog = (comment: Comment) => {
    setSelectedComment(comment)
    setReplyDialogOpen(true)
  }

  const handleSubmitReply = async (text: string) => {
    if (!selectedComment) return
    await onReply(selectedComment.id, text)
  }

  if (loading) {
    return (
      <div className="space-y-4 p-4" role="status" aria-label="Loading comments">
        <span className="sr-only">Loading comments feed...</span>
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-3">
            <div className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
            <Skeleton className="h-16 w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (comments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <MessageSquare className="w-8 h-8 text-muted-foreground opacity-50" />
        </div>
        <h3 className="font-semibold text-lg mb-2">No comments yet</h3>
        <p className="text-sm text-muted-foreground max-w-sm">
          Comments on your monitored posts will appear here. Make sure you have enabled monitoring
          for at least one post.
        </p>
      </div>
    )
  }

  return (
    <>
      <ScrollArea className="h-full">
        <div className="space-y-4 p-4">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              onReply={handleSubmitReply}
              onOpenReplyDialog={() => handleOpenReplyDialog(comment)}
            />
          ))}

          {hasMore && onLoadMore && (
            <div className="flex justify-center pt-4">
              <Button variant="outline" onClick={onLoadMore} className="w-full">
                Load More Comments
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>

      <CommentReplyDialog
        open={replyDialogOpen}
        onOpenChange={setReplyDialogOpen}
        comment={selectedComment}
        onSubmit={handleSubmitReply}
      />
    </>
  )
}
