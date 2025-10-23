"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import {
  ChevronUp,
  User,
  Clock,
  Plus,
  X,
  RotateCcw,
  TrendingUp,
  AlertTriangle,
} from "lucide-react"
import {
  useAnalyticsOverview,
  useConversationsTimeline,
  useAIMetrics,
  useTopics,
  usePostsCommentsTimeline
} from "@/lib/api"

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState("30d")

  // Fetch real data from API
  const { data: overview, isLoading: overviewLoading, refetch: refetchOverview } = useAnalyticsOverview(dateRange)
  const { data: conversationsTimeline, isLoading: conversationsLoading } = useConversationsTimeline(dateRange)
  const { data: aiMetrics, isLoading: aiMetricsLoading } = useAIMetrics(dateRange)
  const { data: topics, isLoading: topicsLoading } = useTopics(dateRange)
  const { data: postsCommentsTimeline, isLoading: postsCommentsLoading } = usePostsCommentsTimeline(dateRange)

  const isLoading = overviewLoading || conversationsLoading || aiMetricsLoading || topicsLoading || postsCommentsLoading

  const handleRefresh = () => {
    refetchOverview()
  }

  const handleExport = () => {
    console.log("Exporting analytics data...")
    // TODO: Implement export functionality
  }

  // Prepare data for charts
  const aiDistributionData = aiMetrics ? [
    { name: "Respond", value: aiMetrics.distribution.respond, color: "#10b981" },
    { name: "Ignore", value: aiMetrics.distribution.ignore, color: "#f59e0b" },
    { name: "Escalate", value: aiMetrics.distribution.escalate, color: "#ef4444" },
  ] : []

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Track your AI performance and conversation insights
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
              <SelectItem value="90d">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={handleRefresh} disabled={isLoading}>
            <RotateCcw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={handleExport}>
            <Plus className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_conversations?.toLocaleString() || 0}</div>
            <p className="text-xs text-muted-foreground">
              {overview?.total_messages || 0} messages
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg AI Confidence</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(overview?.ai_stats?.avg_confidence || 0).toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground">
              {overview?.ai_stats?.respond || 0} responses
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Escalation Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview?.total_escalations || 0}</div>
            <p className="text-xs text-muted-foreground">
              {overview?.moderation_flags || 0} moderation flags
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Decisions</CardTitle>
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(overview?.ai_stats?.respond || 0) + (overview?.ai_stats?.ignore || 0) + (overview?.ai_stats?.escalate || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Total decisions made
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Conversations Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Conversations Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={conversationsTimeline || []}>
                <defs>
                  <linearGradient id="conversationGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.5} />
                <XAxis dataKey="date" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <YAxis axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
                <Line
                  type="monotone"
                  dataKey="conversations"
                  stroke="#7c3aed"
                  strokeWidth={3}
                  dot={{ r: 5, fill: "#7c3aed", strokeWidth: 0 }}
                  activeDot={{ r: 6 }}
                  fill="url(#conversationGradient)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AI Decision Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>AI Decision Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={aiDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {aiDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AI Confidence Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>AI Confidence Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={aiMetrics?.confidence_over_time || []}>
                <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
                <XAxis dataKey="date" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <YAxis domain={[0, 1]} axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} formatter={(value: number) => [(value * 100).toFixed(1) + '%', 'Confidence']} />
                <Line type="monotone" dataKey="avg_confidence" stroke="#6ee7b7" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Topics (BERTopic) */}
        <Card>
          <CardHeader>
            <CardTitle>Top Topics</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            {topics && topics.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topics.slice(0, 10)} layout="vertical" margin={{ left: 100 }}>
                  <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
                  <XAxis type="number" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                  <YAxis dataKey="topic_label" type="category" axisLine={false} tickLine={false} width={100} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
                  <Bar dataKey="message_count" fill="#c084fc" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                No topics data available. Run BERTopic analysis to see topics.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Posts, Comments, DMs Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Posts, Comments & DMs Activity</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={postsCommentsTimeline || []}>
              <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
              <XAxis dataKey="date" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
              <YAxis axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
              <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
              <Line type="monotone" dataKey="posts" stroke="#3b82f6" strokeWidth={2} name="Posts" />
              <Line type="monotone" dataKey="comments" stroke="#10b981" strokeWidth={2} name="Comments" />
              <Line type="monotone" dataKey="dms" stroke="#f59e0b" strokeWidth={2} name="DMs" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Top AI Rules Matched */}
      <Card>
        <CardHeader>
          <CardTitle>Top Matched AI Rules</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {aiMetrics?.top_rules?.slice(0, 5).map((rule, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium">{rule.rule}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex-1 bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${(rule.count / (aiMetrics.top_rules[0]?.count || 1)) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground w-12 text-right">{rule.count}</span>
                  </div>
                </div>
              </div>
            )) || <p className="text-muted-foreground text-sm">No rules data available</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
