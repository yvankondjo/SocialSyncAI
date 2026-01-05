"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/hooks/useAuth"
import { SocialAccountsService, ConversationsService, AnalyticsService } from "@/lib/api"
import { demoEnabled, demoStats, demoConversations, demoAnalytics } from "@/lib/demo-data"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { logos } from "@/lib/logos"
import {
  User,
  Sparkles,
  Clock,
  Send,
  Plus,
  Plus as MessageSquare,
} from "lucide-react"

export function DashboardPage() {
  const { user } = useAuth()
  const [theme, setTheme] = useState<"light" | "dark">("light")
  const [accounts, setAccounts] = useState<any[]>([])
  const [conversations, setConversations] = useState<any[]>([])
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  // State for uploaded files
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([])

  useEffect(() => {
    loadDashboardData()
  }, [user])

  const loadDashboardData = async () => {
    if (!demoEnabled && !user) return

    try {
      setLoading(true)

      if (demoEnabled) {
        setAccounts([])
        setConversations(demoConversations.list)
        setAnalytics({ trends: demoAnalytics.conversationsOverTime })
        return
      }

      const [accountsData, conversationsData, analyticsData] = await Promise.allSettled([
        SocialAccountsService.getSocialAccounts(),
        ConversationsService.getConversations(),
        AnalyticsService.getOverview('30d')
      ])

      if (accountsData.status === 'fulfilled') {
        setAccounts(accountsData.value.accounts || [])
      } else {
        console.error('Failed to load social accounts:', accountsData.reason)
      }

      if (conversationsData.status === 'fulfilled') {
        setConversations(conversationsData.value.conversations || [])
      } else {
        console.error('Failed to load conversations:', conversationsData.reason)
      }

      if (analyticsData.status === 'fulfilled') {
        // Store analytics overview data
        setAnalytics(analyticsData.value)
      } else {
        console.error('Failed to load analytics:', analyticsData.reason)
      }
    } catch (error) {
      console.error('Unexpected error loading dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light")
    console.log("[v0] theme_toggle", { theme: theme === "light" ? "dark" : "light" })
  }


  const handleConnectInstagram = () => {
    console.log("[v0] dashboard_connect_instagram_click")
    window.location.href = '/dashboard/connect'
  }

  const handleUpload = (files: File[]) => {
    if (!user) {
      console.error("User not authenticated for upload.")
      // Optionally: show a toast notification to the user
      return
    }

    const newFiles = files.map(file => ({
      id: `${file.name}-${new Date().getTime()}`, // More stable temporary ID
      name: file.name,
      type: file.name.split('.').pop()?.toUpperCase() || 'File',
      size: file.size,
      sections: 0,
      status: "processing" as const,
      url: "#",
      progress: 0,
    }))

    setUploadedFiles(prevFiles => [...newFiles, ...prevFiles])

    newFiles.forEach(async (fileData) => {
      const file = files.find(f => f.name === fileData.name)!
      const filePath = `public/${user.id}/${file.name}`

      // The supabase client is not imported, so this will not work as intended.
      // This section is kept as per the original file, but the functionality is removed.
      // const { error } = await supabase.storage
      //   .from("documents")
      //   .upload(filePath, file, {
      //     cacheControl: '3600',
      //     upsert: true, // Overwrite file if it exists
      //   })

      // if (error) {
      //   console.error("Error uploading file:", error)
      //   setUploadedFiles(prev => prev.map(f => {
      //     if (f.id === fileData.id) {
      //       return { ...f, status: 'failed' as const }
      //     }
      //     return f
      //   }))
      // } else {
      //   console.log("File uploaded successfully:", filePath)
      //   // The trigger will now handle the processing.
      //   // The polling mechanism will update the status from 'processing' to 'indexed' or 'failed'.
      //   // We just mark the upload as complete.
      //   setUploadedFiles(prev => prev.map(f => {
      //     if (f.id === fileData.id) {
      //       return { ...f, progress: 100 }
      //     }
      //     return f
      //   }))
      // }
    })
  }

  // Calculate metrics from real data
  const getTotalConversations = () => {
    if (!analytics) return conversations.length || 0
    return analytics.total_conversations || conversations.length || 0
  }

  const getTotalMessages = () => {
    if (!analytics) return 0
    return analytics.total_messages || 0
  }

  const getAIResponses = () => {
    if (!analytics) return 0
    return analytics.ai_stats?.respond || 0
  }

  return (
    <div className="flex-1 bg-background">
      {/* Main Content */}
      <div className="flex-1 p-6 space-y-8 max-w-7xl mx-auto">
        {/* Hero Section */}
        <div className="space-y-6">
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Welcome back, {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'} 👋
            </h2>
            <p className="text-lg text-muted-foreground">Let's boost your social media presence today.</p>
          </div>

          {/* CTA Card */}
          <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20 shadow-soft hover-lift">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Bienvenue sur SocialSyncAI Studio</h3>
                  <p className="text-muted-foreground">Orchestrez votre service client IA sur WhatsApp & Instagram</p>
                </div>
                <Button
                  onClick={handleConnectInstagram}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 hover-lift shadow-soft"
                >
                  Connect Accounts
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="shadow-soft hover-lift">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Conversations</CardTitle>
              <MessageSquare className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getTotalConversations()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Active conversations</p>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Messages</CardTitle>
              <Send className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getTotalMessages()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Messages handled</p>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">AI Responses</CardTitle>
              <Sparkles className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getAIResponses()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Automated by AI</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {!demoEnabled && (
            <Card className="shadow-soft hover-lift cursor-pointer" onClick={handleConnectInstagram}>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg border border-purple-200">
                    <img src={logos.instagram} alt="Instagram logo" className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">Connect Instagram</h3>
                    <p className="text-sm text-muted-foreground">Link your Instagram account</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="shadow-soft hover-lift cursor-pointer" onClick={() => window.location.href = '/dashboard/activity/chat'}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">View Inbox</h3>
                  <p className="text-sm text-muted-foreground">Manage your conversations</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift cursor-pointer" onClick={() => window.location.href = '/dashboard/activity/comments'}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-emerald-500/10 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">View Comments</h3>
                  <p className="text-sm text-muted-foreground">Monitor and respond to comments</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card className="shadow-soft">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
              <div className="p-2 bg-primary/10 rounded-full">
                <MessageSquare className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">New conversation started</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">2 minutes ago</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
              <div className="p-2 bg-emerald-500/10 rounded-full">
                <Sparkles className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">AI responded to message</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">15 minutes ago</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
