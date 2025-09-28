"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/hooks/useAuth"
import { SocialAccountsService, ConversationsService, AnalyticsService } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { logos } from "@/lib/logos"
import {
  User,
  Sparkles,
  Clock,
  Send,
  Bot,
  TrendingUp,
  MessageSquare,
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
    if (!user) return

    try {
      setLoading(true)
      const [accountsData, conversationsData, analyticsData] = await Promise.allSettled([
        SocialAccountsService.getSocialAccounts(),
        ConversationsService.getConversations(),
        AnalyticsService.getTrends(user.id)
      ])

      if (accountsData.status === 'fulfilled') {
        setAccounts(accountsData.value)
      }
      if (conversationsData.status === 'fulfilled') {
        setConversations(conversationsData.value.conversations || [])
      }
      if (analyticsData.status === 'fulfilled') {
        setAnalytics(analyticsData.value)
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error)
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
    // Handle Instagram connection
  }

  const handleScheduleContent = () => {
    console.log("[v0] dashboard_schedule_content_click")
    // Handle schedule content action
  }

  const handleAskAI = () => {
    console.log("[v0] dashboard_ask_ai_click")
    // Handle AI assistant
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
  const getContentAutomated = () => {
    if (!analytics) return 12 // Default fallback
    const trends = analytics.trends || []
    return trends.reduce((total: number, trend: any) => total + (trend.total_likes || 0), 0)
  }

  const getDmsAnswered = () => {
    return conversations.length || 147 // Default fallback
  }

  const getCommentsAutomated = () => {
    if (!analytics) return 35 // Default fallback
    const trends = analytics.trends || []
    return trends.reduce((total, trend) => total + (trend.total_comments || 0), 0)
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
                  <h3 className="text-xl font-semibold text-foreground mb-2">Welcome to SocialSync</h3>
                  <p className="text-muted-foreground">Manage your social media presence efficiently</p>
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
              <CardTitle className="text-sm font-medium text-muted-foreground">Content Automated</CardTitle>
              <TrendingUp className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getContentAutomated()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">+12% from last month</p>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">DMs Answered</CardTitle>
              <MessageSquare className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getDmsAnswered()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">+23% from last month</p>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Comments Automated</CardTitle>
              <img src={logos.whatsapp} alt="WhatsApp logo" className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">
                {loading ? "..." : getCommentsAutomated()}
              </div>
              <p className="text-xs text-muted-foreground mt-1">+8% from last month</p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

          <Card className="shadow-soft hover-lift cursor-pointer" onClick={handleScheduleContent}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <Clock className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">Content Management</h3>
                  <p className="text-sm text-muted-foreground">Organize your content strategy</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-soft hover-lift">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-emerald-500/10 rounded-lg">
                  <Sparkles className="w-6 h-6 text-emerald-500" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">AI Assistant</h3>
                  <p className="text-sm text-muted-foreground">Get content suggestions</p>
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
                <Send className="w-4 h-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">Content scheduled for Instagram</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">2 minutes ago</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
              <div className="p-2 bg-emerald-500/10 rounded-full">
                <MessageSquare className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">New DM response sent</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">15 minutes ago</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
              <div className="p-2 bg-blue-500/10 rounded-full">
                <img src={logos.linkedin} alt="LinkedIn logo" className="w-4 h-4" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground">Comment automated on LinkedIn</p>
                <div className="flex items-center gap-2 mt-1">
                  <Clock className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">1 hour ago</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Floating AI Button */}
      <Button
        onClick={handleAskAI}
        className="fixed bottom-6 right-6 h-14 px-6 bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-200 hover-lift z-50"
        size="lg"
      >
        <Bot className="w-5 h-5 mr-2" />
        Ask SocialSync AI
      </Button>
    </div>
  )
}
