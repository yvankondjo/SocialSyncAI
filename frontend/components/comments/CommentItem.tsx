"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { MessageSquare, AlertTriangle, CheckCircle, XCircle, Edit } from "lucide-react"
import { Comment } from "@/types/comments"
import { cn } from "@/lib/utils"

interface CommentItemProps {
  comment: Comment
  onReply: (text: string) => Promise<void>
  onOpenReplyDialog: () => void
}

export function CommentItem({ comment, onReply, onOpenReplyDialog }: CommentItemProps) {
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffInSeconds < 60) return `${diffInSeconds}s ago`
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    return `${Math.floor(diffInSeconds / 86400)}d ago`
  }

  const getTriageBadgeConfig = (triage: Comment['triage']) => {
    switch (triage) {
      case 'respond':
        return {
          label: 'RESPOND',
          className: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700',
          icon: CheckCircle,
        }
      case 'ignore':
        return {
          label: 'IGNORE',
          className: 'bg-slate-100 dark:bg-slate-900/50 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700',
          icon: XCircle,
        }
      case 'escalate':
        return {
          label: 'ESCALATE',
          className: 'bg-red-100 dark:bg-red-950/40 text-red-900 dark:text-red-300 border-red-300 dark:border-red-700',
          icon: AlertTriangle,
        }
      default:
        return {
          label: 'PENDING',
          className: 'bg-slate-100 dark:bg-slate-900/50 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700',
          icon: MessageSquare,
        }
    }
  }

  const getPlatformColor = (platform: string) => {
    // Utiliser chart tokens au lieu de hard-coded colors
    switch (platform) {
      case 'instagram':
        return 'bg-chart-5/20 text-chart-5 border-chart-5/30'
      case 'facebook':
        return 'bg-chart-1/20 text-chart-1 border-chart-1/30'
      case 'twitter':
        return 'bg-chart-3/20 text-chart-3 border-chart-3/30'
      default:
        return 'bg-muted text-muted-foreground border-border'
    }
  }

  const badgeConfig = getTriageBadgeConfig(comment.triage)
  const BadgeIcon = badgeConfig.icon

  return (
    <Card
      className="p-4 hover:shadow-md transition-shadow border
                 focus-visible:outline focus-visible:outline-2
                 focus-visible:outline-ring focus-visible:outline-offset-2"
      tabIndex={0}
      role="article"
      aria-label={`Comment from ${comment.author_name}`}
    >
      <div className="space-y-3">
        {/* Header: Author info + timestamp + triage badge */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <Avatar className="w-10 h-10">
              <AvatarImage src={comment.author_avatar_url} />
              <AvatarFallback className="text-sm bg-primary/10 text-primary">
                {comment.author_name?.charAt(0)?.toUpperCase() || '?'}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-semibold text-sm truncate">
                  @{comment.author_name}
                </p>
                <Badge variant="outline" className={cn("text-xs", getPlatformColor(comment.platform))}>
                  {comment.platform}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                {formatTimeAgo(comment.created_at)}
              </p>
            </div>
          </div>

          <Badge
            variant="outline"
            className={cn("text-xs font-medium flex items-center gap-1", badgeConfig.className)}
          >
            <BadgeIcon className="w-3 h-3" />
            {badgeConfig.label}
          </Badge>
        </div>

        {/* Comment text */}
        <div className="pl-[52px]">
          <p className="text-sm leading-relaxed">{comment.text}</p>
        </div>

        {/* Conditional rendering based on triage */}
        <div className="pl-[52px] space-y-2">
          {comment.triage === 'respond' && comment.ai_reply_text && (
            <div className="bg-muted/50 p-3 rounded-lg border border-border space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-primary" />
                  <span className="text-xs font-medium text-muted-foreground">AI Reply</span>
                </div>
                {comment.replied_at && (
                  <div className="flex items-center gap-1 text-xs text-green-600">
                    <CheckCircle className="w-3 h-3" />
                    <span>Sent {formatTimeAgo(comment.replied_at)}</span>
                  </div>
                )}
              </div>
              <p className="text-sm">{comment.ai_reply_text}</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={onOpenReplyDialog}
                className="h-7 text-xs"
              >
                <Edit className="w-3 h-3 mr-1" />
                Edit Reply
              </Button>
            </div>
          )}

          {comment.triage === 'ignore' && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <XCircle className="w-4 h-4" />
              <span>No action taken</span>
            </div>
          )}

          {comment.triage === 'escalate' && (
            <div className="bg-red-500/10 border border-red-500/30 p-3 rounded-lg">
              <div className="flex items-center gap-2 text-xs text-red-700">
                <AlertTriangle className="w-4 h-4" />
                <span className="font-medium">Escalated to email</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                This comment requires manual review
              </p>
            </div>
          )}

          {comment.triage === 'respond' && !comment.ai_reply_text && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenReplyDialog}
              className="h-8 text-xs"
            >
              <MessageSquare className="w-3 h-3 mr-1" />
              Reply manually
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}
