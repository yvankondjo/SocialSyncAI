"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import {
  ChevronUp,
  User,
  Clock,
  Plus,
  X,
  Search,
  RotateCcw,
} from "lucide-react"
import { demoAnalytics, demoEnabled } from "@/lib/demo-data"

// Mock data for analytics
const metrics = demoEnabled
  ? {
      totalConversations: demoAnalytics.kpis.conversations,
      avgResponseTime: demoAnalytics.kpis.avgResponseTime,
      resolutionRate: demoAnalytics.kpis.resolutionRate,
      satisfaction: demoAnalytics.kpis.satisfaction,
    }
  : {
      totalConversations: {
        value: 2847,
        trend: 12.5,
        isPositive: true,
        trendLabel: "vs last month",
      },
      avgResponseTime: {
        value: "2m 34s",
        trend: -8.2,
        isPositive: true,
        trendLabel: "improvement",
      },
      resolutionRate: {
        value: "94.2%",
        trend: 3.1,
        isPositive: true,
        trendLabel: "vs last month",
      },
      satisfaction: {
        value: "4.8/5",
        trend: 2.4,
        isPositive: true,
        trendLabel: "from CSAT surveys",
      },
    }

const topQuestions = demoEnabled
  ? demoAnalytics.topQuestions
  : [
      { question: "How do I reset my password?", count: 89 },
      { question: "What payment methods do you accept?", count: 67 },
      { question: "How can I upgrade my plan?", count: 54 },
      { question: "Is there a mobile app available?", count: 43 },
      { question: "How do I cancel my subscription?", count: 38 },
    ]

const recentActivity = demoEnabled
  ? demoAnalytics.recentActivity
  : [
      {
        id: "1",
        type: "conversation",
        title: "New conversation from john.doe@example.com",
        time: "2 minutes ago",
        status: "active",
      },
      {
        id: "2",
        type: "resolution",
        title: "Conversation with sarah.wilson resolved",
        time: "15 minutes ago",
        status: "resolved",
      },
      {
        id: "3",
        type: "escalation",
        title: "Issue escalated: Technical problem",
        time: "1 hour ago",
        status: "escalated",
      },
    ]

const conversationTrend = demoEnabled ? demoAnalytics.conversationsOverTime : []
const responseTimeTrend = demoEnabled ? demoAnalytics.responseTimeDistribution : []
const sentimentBreakdown = demoEnabled ? demoAnalytics.sentiment : []
const topTopics = demoEnabled ? demoAnalytics.topTopics : []

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState("30d")
  const [isLoading, setIsLoading] = useState(false)

  const handleRefresh = () => {
    setIsLoading(true)
    setTimeout(() => setIsLoading(false), 2000)
  }

  const handleExport = () => {
    console.log("Exporting analytics data...")
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Track your chatbot performance and conversation insights
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
            <div className="text-2xl font-bold">{metrics.totalConversations.value.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metrics.totalConversations.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={metrics.totalConversations.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(metrics.totalConversations.trend)}%
              </span>
              <span className="ml-1">{metrics.totalConversations.trendLabel}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.avgResponseTime.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metrics.avgResponseTime.isPositive ? (
                <X className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <Plus className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={metrics.avgResponseTime.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(metrics.avgResponseTime.trend)}%
              </span>
              <span className="ml-1">{metrics.avgResponseTime.trendLabel}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.resolutionRate.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metrics.resolutionRate.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={metrics.resolutionRate.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(metrics.resolutionRate.trend)}%
              </span>
              <span className="ml-1">{metrics.resolutionRate.trendLabel}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">User Satisfaction</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.satisfaction.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {metrics.satisfaction.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={metrics.satisfaction.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(metrics.satisfaction.trend)}%
              </span>
              <span className="ml-1">{metrics.satisfaction.trendLabel}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Conversations Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={conversationTrend}>
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

        <Card>
          <CardHeader>
            <CardTitle>Average Response Time by Hour</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={responseTimeTrend}>
                <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
                <XAxis dataKey="hour" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <YAxis axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
                <Bar dataKey="avgSeconds" radius={[8, 8, 0, 0]} fill="#6ee7b7" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sentimentBreakdown}>
                <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
                <XAxis dataKey="label" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <YAxis axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} formatter={(value) => [`${value}%`, "Sentiment"]} />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {sentimentBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Topics</CardTitle>
          </CardHeader>
          <CardContent className="h-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topTopics} layout="vertical" margin={{ left: 60 }}>
                <CartesianGrid strokeDasharray="4 4" stroke="hsl(var(--muted))" opacity={0.4} />
                <XAxis type="number" axisLine={false} tickLine={false} stroke="hsl(var(--muted-foreground))" />
                <YAxis dataKey="topic" type="category" axisLine={false} tickLine={false} width={120} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ background: "hsl(var(--popover))", borderRadius: 8 }} />
                <Bar dataKey="count" fill="#c084fc" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Tables */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Top Questions */}
        <Card>
          <CardHeader>
            <CardTitle>Most Asked Questions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topQuestions.map((question, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium">{question.question}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Progress value={(question.count / topQuestions[0].count) * 100} className="flex-1 h-2" />
                      <span className="text-xs text-muted-foreground">{question.count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === "active" ? "bg-blue-500" :
                    activity.status === "resolved" ? "bg-green-500" :
                    "bg-orange-500"
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{activity.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {demoEnabled && activity.time
                        ? activity.time
                        : activity.time}
                    </p>
                  </div>
                  <Badge variant={
                    activity.status === "active" ? "default" :
                    activity.status === "resolved" ? "secondary" :
                    "destructive"
                  }>
                    {activity.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}