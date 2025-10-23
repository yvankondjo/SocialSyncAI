"use client"

import { useState } from "react"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Checkbox } from "@/components/ui/checkbox"
import { Clock, MessageSquare, Image as ImageIcon, RefreshCw } from "lucide-react"
import { type MonitoredPost } from "@/lib/api"
import { cn } from "@/lib/utils"

interface PostSelectionPanelProps {
  posts: MonitoredPost[]
  onToggleMonitoring: (postId: string) => Promise<void>
  loading: boolean
  selectedPostId?: string
  onSelectPost?: (postId: string) => void
  onSync?: () => Promise<void>
  isSyncing?: boolean
}

export function PostSelectionPanel({
  posts,
  onToggleMonitoring,
  loading,
  selectedPostId,
  onSelectPost,
  onSync,
  isSyncing
}: PostSelectionPanelProps) {
  const [togglingPost, setTogglingPost] = useState<string | null>(null)

  // Handle checkbox toggle - no event needed from onCheckedChange
  const handleToggle = async (postId: string) => {
    setTogglingPost(postId)
    try {
      await onToggleMonitoring(postId)
    } finally {
      setTogglingPost(null)
    }
  }

  // Handle post selection
  const handlePostClick = (postId: string) => {
    if (togglingPost === postId) return // Don't select while toggling
    onSelectPost?.(postId)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const truncateText = (text: string, maxLength: number = 60) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  if (loading) {
    return (
      <div className="space-y-3 p-3" role="status" aria-label="Loading posts">
        <span className="sr-only">Loading monitored posts...</span>
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-20 w-full rounded-lg" />
          </div>
        ))}
      </div>
    )
  }

  if (posts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
          <ImageIcon className="w-8 h-8 text-muted-foreground" aria-hidden="true" />
        </div>
        <h3 className="font-semibold text-lg mb-2">No posts to monitor</h3>
        <p className="text-sm text-muted-foreground max-w-sm mb-4">
          Import your Instagram posts to start monitoring comments and engaging with your audience.
        </p>
        {onSync && (
          <Button
            onClick={onSync}
            disabled={isSyncing}
            className="gap-2"
          >
            {isSyncing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" aria-hidden="true" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" aria-hidden="true" />
                Sync Instagram Posts
              </>
            )}
          </Button>
        )}
      </div>
    )
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2 p-3">
        {posts.map((post) => (
          <div
            key={post.id}
            onClick={() => handlePostClick(post.id)}
            className={cn(
              "w-full text-left p-3 rounded-lg border transition-all cursor-pointer group",
              "focus-within:outline focus-within:outline-2 focus-within:outline-ring focus-within:outline-offset-2",
              selectedPostId === post.id
                ? "bg-primary/10 border-primary/50 shadow-sm"
                : "hover:bg-muted/50 hover:border-border",
              togglingPost === post.id && "opacity-60 pointer-events-none"
            )}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                handlePostClick(post.id)
              }
            }}
            aria-pressed={selectedPostId === post.id}
            aria-label={`Select post: ${post.caption || 'Untitled'}`}
          >
            <div className="flex items-start gap-3">
              {/* Checkbox */}
              <div
                className="pt-1 flex items-center justify-center min-w-[44px] min-h-[44px]"
                onClick={(e) => e.stopPropagation()} // Prevent post selection when clicking checkbox
              >
                <Checkbox
                  checked={post.monitoring_enabled}
                  onCheckedChange={() => handleToggle(post.id)}
                  disabled={togglingPost === post.id}
                  className="h-5 w-5"
                  aria-label={`${post.monitoring_enabled ? 'Disable' : 'Enable'} monitoring for ${post.caption || 'untitled post'}`}
                />
              </div>

              {/* Post thumbnail (if available) */}
              {post.media_url && (
                <div className="w-12 h-12 rounded-md overflow-hidden flex-shrink-0 bg-muted">
                  <img
                    src={post.media_url}
                    alt="Post thumbnail"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Post info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-sm font-medium truncate">
                    {post.caption ? truncateText(post.caption) : 'Untitled post'}
                  </p>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                  <span>{formatDate(post.posted_at)}</span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" />
                    {post.comments_count || 0}
                  </span>
                </div>

                {/* Status badges */}
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs font-semibold",
                      post.monitoring_enabled
                        ? "bg-emerald-100 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-700"
                        : "bg-slate-100 dark:bg-slate-900/50 text-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700"
                    )}
                  >
                    {post.monitoring_enabled ? 'Monitoring ON' : 'Monitoring OFF'}
                  </Badge>

                  {post.monitoring_enabled && post.days_remaining !== undefined && (
                    <Badge variant="outline" className="text-xs flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {post.days_remaining}d left
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  )
}
