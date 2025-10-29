"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card } from "@/components/ui/card"
import { Search, RefreshCw, ListFilter } from "lucide-react"
import { MonitoringService, CommentsService } from "@/lib/api"
import { MonitoredPost, MonitoringRules, Comment, CommentFilters } from "@/types/comments"
import { MonitoringRulesPanel } from "@/components/comments/MonitoringRulesPanel"
import { PostSelectionPanel } from "@/components/comments/PostSelectionPanel"
import { CommentsList } from "@/components/comments/CommentsList"

export default function CommentsPage() {
  // State for data
  const [posts, setPosts] = useState<MonitoredPost[]>([])
  const [comments, setComments] = useState<Comment[]>([])
  const [rules, setRules] = useState<MonitoringRules | null>(null)
  const [selectedPostId, setSelectedPostId] = useState<string | null>(null)

  // State for filters
  const [filters, setFilters] = useState<CommentFilters>({
    platform: 'all',
    triage: undefined,
    search: '',
  })

  // State for loading
  const [loading, setLoading] = useState(true)
  const [loadingPosts, setLoadingPosts] = useState(false)
  const [loadingComments, setLoadingComments] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const { toast } = useToast()

  // Load initial data
  useEffect(() => {
    loadInitialData()
  }, [])

  // Load comments when filters change
  useEffect(() => {
    loadComments()
  }, [filters, selectedPostId])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      await Promise.all([loadPosts(), loadRules()])
    } catch (error) {
      console.error("Error loading initial data:", error)
      toast({
        title: "Error",
        description: "Failed to load monitoring data",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadPosts = async () => {
    try {
      setLoadingPosts(true)
      const response = await MonitoringService.getMonitoredPosts()
      const posts = response.posts || []

      // Debug: Check for posts without IDs
      const postsWithoutId = posts.filter(p => !p.id)
      if (postsWithoutId.length > 0) {
        console.error("❌ Posts without ID detected:", postsWithoutId)
        console.error("Full response:", response)
      }

      // Filter out posts without IDs to prevent React errors
      const validPosts = posts.filter(p => p.id)
      if (validPosts.length !== posts.length) {
        console.warn(`⚠️ Filtered out ${posts.length - validPosts.length} posts without IDs`)
      }

      setPosts(validPosts)
    } catch (error) {
      console.error("Error loading posts:", error)
      toast({
        title: "Error",
        description: "Failed to load monitored posts",
        variant: "destructive",
      })
    } finally {
      setLoadingPosts(false)
    }
  }

  const loadRules = async () => {
    try {
      const data = await MonitoringService.getRules()
      setRules(data)
    } catch (error) {
      console.error("Error loading rules:", error)
      toast({
        title: "Error",
        description: "Failed to load monitoring rules",
        variant: "destructive",
      })
    }
  }

  const loadComments = async () => {
    try {
      setLoadingComments(true)
      const activeFilters: CommentFilters = {
        ...filters,
        post_id: selectedPostId || undefined,
        platform: filters.platform === 'all' ? undefined : filters.platform,
        limit: 50,
        offset: 0,
      }

      const response = await CommentsService.getComments(activeFilters)
      setComments(response.comments || [])
    } catch (error) {
      console.error("Error loading comments:", error)
      toast({
        title: "Error",
        description: "Failed to load comments",
        variant: "destructive",
      })
    } finally {
      setLoadingComments(false)
    }
  }

  const handleSyncPosts = async () => {
    try {
      setSyncing(true)
      const response = await MonitoringService.syncPosts()
      toast({
        title: "Sync Complete",
        description: `Imported ${response.posts_imported} posts from Instagram`,
      })
      await loadPosts()
    } catch (error) {
      console.error("Error syncing posts:", error)
      toast({
        title: "Sync Failed",
        description: "Failed to sync Instagram posts",
        variant: "destructive",
      })
    } finally {
      setSyncing(false)
    }
  }

  const handleUpdateRules = async (newRules: MonitoringRules) => {
    try {
      const updated = await MonitoringService.updateRules(newRules)
      setRules(updated)
      toast({
        title: "Settings Saved",
        description: "Monitoring rules updated successfully",
      })
    } catch (error) {
      console.error("Error updating rules:", error)
      toast({
        title: "Error",
        description: "Failed to update monitoring rules",
        variant: "destructive",
      })
    }
  }

  const handleToggleMonitoring = async (postId: string) => {
    if (!postId) {
      console.error("❌ Cannot toggle monitoring: postId is undefined")
      toast({
        title: "Error",
        description: "Invalid post ID",
        variant: "destructive",
      })
      return
    }

    try {
      const updated = await MonitoringService.toggleMonitoring(postId)
      setPosts((prev) =>
        prev.map((post) => (post.id === postId ? updated : post))
      )
      toast({
        title: updated.monitoring_enabled ? "Monitoring Enabled" : "Monitoring Disabled",
        description: updated.monitoring_enabled
          ? "Comments will be monitored for this post"
          : "Comments monitoring stopped for this post",
      })
    } catch (error) {
      console.error("Error toggling monitoring:", error)
      toast({
        title: "Error",
        description: "Failed to toggle monitoring",
        variant: "destructive",
      })
    }
  }

  const handleReplyToComment = async (commentId: string, text: string) => {
    try {
      const updated = await CommentsService.replyToComment(commentId, text)
      setComments((prev) =>
        prev.map((comment) => (comment.id === commentId ? updated : comment))
      )
      toast({
        title: "Reply Sent",
        description: "Your reply has been posted successfully",
      })
    } catch (error) {
      console.error("Error replying to comment:", error)
      toast({
        title: "Error",
        description: "Failed to send reply",
        variant: "destructive",
      })
    }
  }

  const handleSelectPost = (postId: string) => {
    setSelectedPostId(postId === selectedPostId ? null : postId)
  }

  const handleRefresh = () => {
    loadComments()
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Comments Management</h1>
        <p className="text-muted-foreground">
          Monitor and respond to comments across all platforms
        </p>
      </div>

      {/* Monitoring Settings Panel */}
      {rules && (
        <MonitoringRulesPanel
          rules={rules}
          onUpdate={handleUpdateRules}
          isSyncing={syncing}
          onSync={handleSyncPosts}
        />
      )}

      {/* Filters Bar */}
      <Card className="p-4 border">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search comments..."
              value={filters.search || ''}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, search: e.target.value }))
              }
              className="pl-10"
            />
          </div>

          <Select
            value={filters.platform || 'all'}
            onValueChange={(value) =>
              setFilters((prev) => ({ ...prev, platform: value }))
            }
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Platforms</SelectItem>
              <SelectItem value="instagram">Instagram</SelectItem>
              <SelectItem value="facebook">Facebook</SelectItem>
              <SelectItem value="twitter">Twitter</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={filters.triage || 'all'}
            onValueChange={(value) =>
              setFilters((prev) => ({
                ...prev,
                triage: value === 'all' ? undefined : (value as 'respond' | 'ignore' | 'escalate'),
              }))
            }
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Triage" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Triages</SelectItem>
              <SelectItem value="respond">Respond</SelectItem>
              <SelectItem value="ignore">Ignore</SelectItem>
              <SelectItem value="escalate">Escalate</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="icon"
            onClick={handleRefresh}
            disabled={loadingComments}
            aria-label="Refresh comments list"
          >
            <RefreshCw
              className={`w-4 h-4 ${loadingComments ? 'animate-spin' : ''}`}
              aria-hidden="true"
            />
          </Button>
        </div>
      </Card>

      {/* Split View: Posts + Comments */}
      <div className="grid grid-cols-1 lg:grid-cols-[35%_1fr] gap-6 h-[calc(100vh-400px)]">
        {/* Posts Panel */}
        <Card className="border flex flex-col overflow-hidden">
          <div className="p-4 border-b">
            <h2 className="font-semibold flex items-center gap-2">
              <ListFilter className="w-4 h-4" />
              Monitored Posts
            </h2>
            <p className="text-xs text-muted-foreground mt-1">
              {posts.filter((p) => p.monitoring_enabled).length} of {posts.length} posts monitored
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <PostSelectionPanel
              posts={posts}
              onToggleMonitoring={handleToggleMonitoring}
              loading={loadingPosts || loading}
              selectedPostId={selectedPostId || undefined}
              onSelectPost={handleSelectPost}
              onSync={handleSyncPosts}
              isSyncing={syncing}
            />
          </div>
        </Card>

        {/* Comments Feed */}
        <Card className="border flex flex-col overflow-hidden">
          <div className="p-4 border-b">
            <h2 className="font-semibold flex items-center gap-2">
              <Search className="w-4 h-4" />
              Comments Feed
            </h2>
            <p className="text-xs text-muted-foreground mt-1">
              {comments.length} comment{comments.length !== 1 ? 's' : ''} found
              {selectedPostId && ' (filtered by post)'}
            </p>
          </div>
          <div className="flex-1 overflow-hidden">
            <CommentsList
              comments={comments}
              onReply={handleReplyToComment}
              loading={loadingComments || loading}
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
