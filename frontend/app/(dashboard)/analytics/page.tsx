"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import {
  Bot,
  User,
  Clock,
  Plus,
  X,
  Search,
} from "lucide-react"

// Mock data for analytics
const kpiData = {
  totalConversations: { value: 2847, trend: 12.5, isPositive: true },
  avgResponseTime: { value: "2m 34s", trend: -8.2, isPositive: true },
  resolutionRate: { value: "94.2%", trend: 3.1, isPositive: true },
  satisfaction: { value: "4.8/5", trend: 2.4, isPositive: true },
}

const topQuestions = [
  { question: "How do I reset my password?", count: 89 },
  { question: "What payment methods do you accept?", count: 67 },
  { question: "How can I upgrade my plan?", count: 54 },
  { question: "Is there a mobile app available?", count: 43 },
  { question: "How do I cancel my subscription?", count: 38 },
]

const recentActivity = [
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
            <Bot className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
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
            <div className="text-2xl font-bold">{kpiData.totalConversations.value.toLocaleString()}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {kpiData.totalConversations.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={kpiData.totalConversations.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(kpiData.totalConversations.trend)}%
              </span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.avgResponseTime.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {kpiData.avgResponseTime.isPositive ? (
                <X className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <Plus className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={kpiData.avgResponseTime.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(kpiData.avgResponseTime.trend)}%
              </span>
              <span className="ml-1">improvement</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolution Rate</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.resolutionRate.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {kpiData.resolutionRate.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={kpiData.resolutionRate.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(kpiData.resolutionRate.trend)}%
              </span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">User Satisfaction</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{kpiData.satisfaction.value}</div>
            <div className="flex items-center text-xs text-muted-foreground">
              {kpiData.satisfaction.isPositive ? (
                <Plus className="mr-1 h-3 w-3 text-green-500" />
              ) : (
                <X className="mr-1 h-3 w-3 text-red-500" />
              )}
              <span className={kpiData.satisfaction.isPositive ? "text-green-500" : "text-red-500"}>
                {Math.abs(kpiData.satisfaction.trend)}%
              </span>
              <span className="ml-1">from last month</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Simplified Charts Placeholder */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Conversations Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] bg-muted rounded-lg flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Bot className="w-12 h-12 mx-auto mb-4" />
                <p>Graphique Recharts sera ajouté</p>
                <p className="text-sm">Icônes temporaires - à corriger</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Response Times</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] bg-muted rounded-lg flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Clock className="w-12 h-12 mx-auto mb-4" />
                <p>Graphique Recharts sera ajouté</p>
                <p className="text-sm">Icônes temporaires - à corriger</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] bg-muted rounded-lg flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <User className="w-12 h-12 mx-auto mb-4" />
                <p>Graphique Recharts sera ajouté</p>
                <p className="text-sm">Icônes temporaires - à corriger</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] bg-muted rounded-lg flex items-center justify-center">
              <div className="text-center text-muted-foreground">
                <Plus className="w-12 h-12 mx-auto mb-4" />
                <p>Graphique Recharts sera ajouté</p>
                <p className="text-sm">Icônes temporaires - à corriger</p>
              </div>
            </div>
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
                    <p className="text-xs text-muted-foreground">{activity.time}</p>
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