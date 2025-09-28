"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { MessageSquare, Users, Clock, TrendingUp, Download, Smile, Meh, Frown, Edit3 } from "lucide-react"

// Mock analytics data
const kpiData = {
  totalChats: 12847,
  totalChatsChange: 12.5,
  activeUsers: 3421,
  activeUsersChange: 8.2,
  avgResponseTime: "2.3s",
  avgResponseTimeChange: -15.3,
  aiAccuracy: 87.4,
  aiAccuracyChange: 5.1,
}

const chatsByDayData = [
  { date: "2024-01-08", chats: 145, web: 89, whatsapp: 34, instagram: 22 },
  { date: "2024-01-09", chats: 167, web: 102, whatsapp: 41, instagram: 24 },
  { date: "2024-01-10", chats: 189, web: 115, whatsapp: 45, instagram: 29 },
  { date: "2024-01-11", chats: 156, web: 94, whatsapp: 38, instagram: 24 },
  { date: "2024-01-12", chats: 203, web: 125, whatsapp: 48, instagram: 30 },
  { date: "2024-01-13", chats: 178, web: 108, whatsapp: 42, instagram: 28 },
  { date: "2024-01-14", chats: 234, web: 142, whatsapp: 56, instagram: 36 },
  { date: "2024-01-15", chats: 198, web: 121, whatsapp: 47, instagram: 30 },
]

const topicsData = [
  { topic: "Account Support", count: 1247, percentage: 32.1 },
  { topic: "Product Inquiry", count: 892, percentage: 23.0 },
  { topic: "Technical Issue", count: 634, percentage: 16.3 },
  { topic: "Billing Question", count: 456, percentage: 11.7 },
  { topic: "Feature Request", count: 298, percentage: 7.7 },
  { topic: "General Info", count: 234, percentage: 6.0 },
  { topic: "Other", count: 127, percentage: 3.2 },
]

const sentimentData = [
  { name: "Positive", value: 45.2, count: 1756, color: "#10b981" },
  { name: "Neutral", value: 38.7, count: 1503, color: "#f59e0b" },
  { name: "Negative", value: 16.1, count: 625, color: "#ef4444" },
]

const channelData = [
  { channel: "Web", chats: 2847, percentage: 45.2 },
  { channel: "WhatsApp", chats: 1923, percentage: 30.5 },
  { channel: "Instagram", chats: 1034, percentage: 16.4 },
  { channel: "X (Twitter)", chats: 498, percentage: 7.9 },
]

const topQuestionsData = [
  {
    question: "How do I reset my password?",
    count: 234,
    avgResponseTime: "1.2s",
    sentiment: "neutral",
    edited: 12,
  },
  {
    question: "What payment methods do you accept?",
    count: 189,
    avgResponseTime: "0.8s",
    sentiment: "positive",
    edited: 3,
  },
  {
    question: "How do I cancel my subscription?",
    count: 156,
    avgResponseTime: "2.1s",
    sentiment: "negative",
    edited: 28,
  },
  {
    question: "Is there a mobile app available?",
    count: 134,
    avgResponseTime: "1.5s",
    sentiment: "neutral",
    edited: 7,
  },
  {
    question: "How do I upgrade my plan?",
    count: 98,
    avgResponseTime: "1.0s",
    sentiment: "positive",
    edited: 2,
  },
]

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState("7d")
  const [channelFilter, setChannelFilter] = useState("all")
  const [languageFilter, setLanguageFilter] = useState("all")

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return <Smile className="w-4 h-4 text-green-400" />
      case "negative":
        return <Frown className="w-4 h-4 text-red-400" />
      default:
        return <Meh className="w-4 h-4 text-yellow-400" />
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-500/20 text-green-400"
      case "negative":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-yellow-500/20 text-yellow-400"
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
              <p className="text-muted-foreground">Monitor your chatbot performance and user interactions</p>
            </div>
            <div className="flex gap-2">
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1d">Today</SelectItem>
                  <SelectItem value="7d">7 Days</SelectItem>
                  <SelectItem value="30d">30 Days</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
              <Select value={channelFilter} onValueChange={setChannelFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Channels</SelectItem>
                  <SelectItem value="web">Web</SelectItem>
                  <SelectItem value="whatsapp">WhatsApp</SelectItem>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="x">X</SelectItem>
                </SelectContent>
              </Select>
              <Select value={languageFilter} onValueChange={setLanguageFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Languages</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Chats</CardTitle>
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{kpiData.totalChats.toLocaleString()}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 mr-1 text-green-400" />
                  <span className="text-green-400">+{kpiData.totalChatsChange}%</span>
                  <span className="ml-1">from last period</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{kpiData.activeUsers.toLocaleString()}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 mr-1 text-green-400" />
                  <span className="text-green-400">+{kpiData.activeUsersChange}%</span>
                  <span className="ml-1">from last period</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{kpiData.avgResponseTime}</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 mr-1 text-green-400 rotate-180" />
                  <span className="text-green-400">{kpiData.avgResponseTimeChange}%</span>
                  <span className="ml-1">improvement</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">AI Accuracy</CardTitle>
                <Edit3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{kpiData.aiAccuracy}%</div>
                <div className="flex items-center text-xs text-muted-foreground">
                  <TrendingUp className="w-3 h-3 mr-1 text-green-400" />
                  <span className="text-green-400">+{kpiData.aiAccuracyChange}%</span>
                  <span className="ml-1">from last period</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chats Over Time */}
            <Card>
              <CardHeader>
                <CardTitle>Chats Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={chatsByDayData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={(value) => new Date(value).toLocaleDateString()}
                      stroke="#9ca3af"
                    />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                    />
                    <Area
                      type="monotone"
                      dataKey="chats"
                      stackId="1"
                      stroke="#8b5cf6"
                      fill="#8b5cf6"
                      fillOpacity={0.3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Chats by Channel */}
            <Card>
              <CardHeader>
                <CardTitle>Chats by Channel</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={channelData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="channel" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar dataKey="chats" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Sentiment Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={sentimentData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={120}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {sentimentData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1f2937",
                          border: "1px solid #374151",
                          borderRadius: "8px",
                        }}
                        formatter={(value, name) => [`${value}%`, name]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Top Topics */}
            <Card>
              <CardHeader>
                <CardTitle>Top Topics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topicsData.slice(0, 6).map((topic, index) => (
                    <div key={topic.topic} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium">{topic.topic}</div>
                          <div className="text-sm text-muted-foreground">{topic.count} conversations</div>
                        </div>
                      </div>
                      <Badge variant="outline">{topic.percentage}%</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Questions Table */}
          <Card>
            <CardHeader>
              <CardTitle>Top Questions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {topQuestionsData.map((question, index) => (
                  <div
                    key={question.question}
                    className="flex items-center justify-between p-4 border border-border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="font-medium mb-2">{question.question}</div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{question.count} times asked</span>
                        <span>Avg response: {question.avgResponseTime}</span>
                        <div className="flex items-center gap-1">
                          {getSentimentIcon(question.sentiment)}
                          <Badge variant="outline" className={getSentimentColor(question.sentiment)}>
                            {question.sentiment}
                          </Badge>
                        </div>
                        {question.edited > 0 && (
                          <div className="flex items-center gap-1">
                            <Edit3 className="w-3 h-3 text-yellow-400" />
                            <span className="text-yellow-400">{question.edited} edits</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
