"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Send, X } from "lucide-react"
import { Comment } from "@/types/comments"
import { cn } from "@/lib/utils"

interface CommentReplyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  comment: Comment | null
  onSubmit: (text: string) => Promise<void>
}

export function CommentReplyDialog({
  open,
  onOpenChange,
  comment,
  onSubmit,
}: CommentReplyDialogProps) {
  const [replyText, setReplyText] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const MIN_CHARS = 10
  const MAX_CHARS = 500

  // Reset reply text when dialog opens with a new comment
  useEffect(() => {
    if (comment && open) {
      setReplyText(comment.ai_reply_text || "")
    }
  }, [comment, open])

  const handleSubmit = async () => {
    if (!replyText.trim() || replyText.length < MIN_CHARS || replyText.length > MAX_CHARS) {
      return
    }

    try {
      setIsSubmitting(true)
      await onSubmit(replyText.trim())
      setReplyText("")
      onOpenChange(false)
    } catch (error) {
      console.error("Failed to submit reply:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setReplyText("")
      onOpenChange(false)
    }
  }

  const charsRemaining = MAX_CHARS - replyText.length
  const isValid = replyText.length >= MIN_CHARS && replyText.length <= MAX_CHARS

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Reply to Comment</DialogTitle>
          <DialogDescription>
            Review the original comment and compose your response below.
            Minimum {MIN_CHARS} characters required. Press ESC to cancel.
          </DialogDescription>
        </DialogHeader>

        {comment && (
          <div className="space-y-4">
            {/* Original Comment Context */}
            <div
              className="bg-muted/50 p-4 rounded-lg border space-y-3"
              role="region"
              aria-label="Original comment"
            >
              <div className="flex items-center gap-3">
                <Avatar className="w-8 h-8">
                  <AvatarImage src={comment.author_avatar_url} />
                  <AvatarFallback className="text-sm bg-primary/10 text-primary">
                    {comment.author_name?.charAt(0)?.toUpperCase() || '?'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-sm">@{comment.author_name}</p>
                    <Badge variant="outline" className="text-xs">
                      {comment.platform}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(comment.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
              <p className="text-sm pl-11">{comment.text}</p>
            </div>

            {/* Reply Text Area */}
            <div className="space-y-2">
              <Label htmlFor="reply-text" className="text-sm font-medium">
                Your Reply
              </Label>
              <Textarea
                id="reply-text"
                placeholder="Type your reply here..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="min-h-[120px] resize-none"
                disabled={isSubmitting}
                maxLength={MAX_CHARS}
                aria-invalid={!isValid && replyText.length > 0}
                aria-describedby="char-counter"
              />
              <div
                id="char-counter"
                className="flex items-center justify-between text-xs"
                role="status"
                aria-live="polite"
                aria-atomic="true"
              >
                <span
                  className={cn(
                    "text-muted-foreground",
                    replyText.length < MIN_CHARS && "text-yellow-600",
                    replyText.length >= MIN_CHARS && replyText.length <= MAX_CHARS && "text-green-600",
                    replyText.length > MAX_CHARS && "text-red-600"
                  )}
                >
                  {replyText.length < MIN_CHARS
                    ? `Minimum ${MIN_CHARS} characters required (${MIN_CHARS - replyText.length} more)`
                    : `${charsRemaining} characters remaining`}
                </span>
                <span className="text-muted-foreground" aria-hidden="true">
                  {replyText.length} / {MAX_CHARS}
                </span>
                {/* Annonce invisible pour screen readers */}
                <span className="sr-only">
                  {replyText.length} of {MAX_CHARS} characters used.
                  {replyText.length < MIN_CHARS && ` ${MIN_CHARS - replyText.length} more characters needed.`}
                  {replyText.length > MAX_CHARS && ' Maximum character count exceeded.'}
                </span>
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            className="gap-2"
            aria-label={isSubmitting ? 'Sending reply' : 'Send reply'}
          >
            {isSubmitting ? (
              <>
                <div
                  className="w-4 h-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent"
                  aria-hidden="true"
                />
                Sending...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" aria-hidden="true" />
                Send Reply
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
