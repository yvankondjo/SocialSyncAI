"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Globe,
  MessageCircle,
  Instagram,
  Twitter,
  CheckCircle,
  AlertCircle,
  Settings,
  Copy,
  Eye,
  Palette,
  Facebook,
  MessageSquare,
  ExternalLink,
  Smartphone,
  Monitor,
  Tablet,
} from "lucide-react"

// Mock data for integrations
const integrations = [
  {
    id: "meta",
    name: "Meta (Instagram & Facebook)",
    description: "Connect your Instagram and Facebook accounts for direct message responses",
    icon: Instagram,
    status: "connected",
    accounts: ["@mybusiness", "@mypage"],
    scopes: ["messages:read", "messages:write", "profile:read"],
    lastSync: "2024-01-15T10:30:00Z",
    color: "bg-pink-500",
  },
  {
    id: "x",
    name: "X (Twitter)",
    description: "Manage mentions and direct messages on X platform",
    icon: Twitter,
    status: "needs_setup",
    accounts: [],
    scopes: ["tweet:read", "dm:read", "dm:write"],
    lastSync: null,
    color: "bg-gray-900",
  },
  {
    id: "whatsapp",
    name: "WhatsApp Business",
    description: "Handle customer support through WhatsApp Business API",
    icon: MessageSquare,
    status: "disconnected",
    accounts: [],
    scopes: ["messages:read", "messages:write", "business:read"],
    lastSync: null,
    color: "bg-green-500",
  },
  {
    id: "facebook",
    name: "Facebook Pages",
    description: "Respond to messages and comments on your Facebook pages",
    icon: Facebook,
    status: "connected",
    accounts: ["My Business Page"],
    scopes: ["pages:read", "pages:messaging"],
    lastSync: "2024-01-15T09:15:00Z",
    color: "bg-blue-600",
  },
]

// Widget themes
const widgetThemes = [
  { id: "default", name: "Default", primary: "#8b5cf6", secondary: "#a78bfa" },
  { id: "ocean", name: "Ocean Blue", primary: "#0ea5e9", secondary: "#38bdf8" },
  { id: "forest", name: "Forest Green", primary: "#10b981", secondary: "#34d399" },
  { id: "sunset", name: "Sunset Orange", primary: "#f97316", secondary: "#fb923c" },
]

const widgetPositions = [
  { id: "bottom-right", name: "Bottom Right", icon: "↘️" },
  { id: "bottom-left", name: "Bottom Left", icon: "↙️" },
  { id: "top-right", name: "Top Right", icon: "↗️" },
  { id: "top-left", name: "Top Left", icon: "↖️" },
]

export default function ConnectPage() {
  const [customizeDialogOpen, setCustomizeDialogOpen] = useState(false)
  const [widgetConfig, setWidgetConfig] = useState({
    theme: "default",
    position: "bottom-right",
    welcomeMessage: "Hello! How can I help you today?",
    placeholder: "Type your message...",
    showAvatar: true,
    showBranding: true,
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-500/20 text-green-400"
      case "needs_setup":
        return "bg-yellow-500/20 text-yellow-400"
      case "disconnected":
        return "bg-gray-500/20 text-gray-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "needs_setup":
        return <AlertCircle className="w-4 h-4 text-yellow-400" />
      case "disconnected":
        return <AlertCircle className="w-4 h-4 text-gray-400" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const handleConnect = (integrationId: string) => {
    console.log(`Connecting to ${integrationId}`)
    // OAuth flow would be triggered here
  }

  const handleDisconnect = (integrationId: string) => {
    console.log(`Disconnecting from ${integrationId}`)
  }

  const generateWidgetCode = () => {
    const theme = widgetThemes.find(t => t.id === widgetConfig.theme)
    return `<!-- SocialSync AI Widget -->
<script>
  window.SocialSyncConfig = {
    theme: {
      primary: "${theme?.primary}",
      secondary: "${theme?.secondary}"
    },
    position: "${widgetConfig.position}",
    welcomeMessage: "${widgetConfig.welcomeMessage}",
    placeholder: "${widgetConfig.placeholder}",
    showAvatar: ${widgetConfig.showAvatar},
    showBranding: ${widgetConfig.showBranding}
  };
</script>
<script src="https://cdn.socialsync.ai/widget.js" async></script>`
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // Toast notification would be shown here
  }

  const formatLastSync = (dateString: string | null) => {
    if (!dateString) return "Never"
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Connect Integrations</h1>
        <p className="text-muted-foreground">
          Connect your social media accounts and configure your web widget
        </p>
      </div>

      {/* Integrations Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {integrations.map((integration) => (
          <Card key={integration.id} className="relative">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg ${integration.color} flex items-center justify-center`}>
                  <integration.icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1">
                  <CardTitle className="text-lg">{integration.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{integration.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(integration.status)}
                  <Badge variant="outline" className={getStatusColor(integration.status)}>
                    {integration.status.replace("_", " ")}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {integration.accounts.length > 0 && (
                <div>
                  <Label className="text-sm font-medium">Connected Accounts</Label>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {integration.accounts.map((account, index) => (
                      <Badge key={index} variant="secondary">
                        {account}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div>
                <Label className="text-sm font-medium">Permissions</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {integration.scopes.map((scope, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {scope}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-sm text-muted-foreground">
                  Last sync: {formatLastSync(integration.lastSync)}
                </span>
                <div className="flex gap-2">
                  {integration.status === "connected" ? (
                    <>
                      <Button variant="outline" size="sm">
                        <Settings className="w-4 h-4 mr-2" />
                        Settings
                      </Button>
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => handleDisconnect(integration.id)}
                      >
                        Disconnect
                      </Button>
                    </>
                  ) : (
                    <Button onClick={() => handleConnect(integration.id)}>
                      {integration.status === "needs_setup" ? "Complete Setup" : "Connect"}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Web Widget Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Globe className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <CardTitle>Web Widget</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Embed a chat widget on your website for customer support
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setCustomizeDialogOpen(true)}>
                <Palette className="w-4 h-4 mr-2" />
                Customize
              </Button>
              <Button variant="outline">
                <Eye className="w-4 h-4 mr-2" />
                Preview
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-sm font-medium">Installation Code</Label>
            <div className="relative mt-2">
              <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                <code>{generateWidgetCode()}</code>
              </pre>
              <Button
                size="sm"
                className="absolute top-2 right-2"
                onClick={() => copyToClipboard(generateWidgetCode())}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Current Theme</Label>
              <div className="flex items-center gap-2">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: widgetThemes.find(t => t.id === widgetConfig.theme)?.primary }}
                />
                <span className="text-sm">
                  {widgetThemes.find(t => t.id === widgetConfig.theme)?.name}
                </span>
              </div>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Position</Label>
              <span className="text-sm">
                {widgetPositions.find(p => p.id === widgetConfig.position)?.name}
              </span>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium">Status</Label>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">Active</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Widget Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Live Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-8 relative h-96">
            {/* Mock website content */}
            <div className="space-y-4">
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-2/3"></div>
            </div>
            
            {/* Widget preview */}
            <div 
              className={`absolute ${
                widgetConfig.position.includes("bottom") ? "bottom-4" : "top-4"
              } ${
                widgetConfig.position.includes("right") ? "right-4" : "left-4"
              }`}
            >
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border p-4 w-80">
                <div className="flex items-center gap-3 mb-3">
                  {widgetConfig.showAvatar && (
                    <div 
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                      style={{ backgroundColor: widgetThemes.find(t => t.id === widgetConfig.theme)?.primary }}
                    >
                      AI
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="text-sm font-medium">SocialSync AI</div>
                    <div className="text-xs text-muted-foreground">Online</div>
                  </div>
                </div>
                <div className="space-y-2 mb-3">
                  <div className="bg-gray-100 dark:bg-gray-700 rounded-lg p-2 text-sm">
                    {widgetConfig.welcomeMessage}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Input 
                    placeholder={widgetConfig.placeholder}
                    className="flex-1"
                    disabled
                  />
                  <Button 
                    size="sm"
                    style={{ backgroundColor: widgetThemes.find(t => t.id === widgetConfig.theme)?.primary }}
                  >
                    <MessageCircle className="w-4 h-4" />
                  </Button>
                </div>
                {widgetConfig.showBranding && (
                  <div className="text-xs text-muted-foreground text-center mt-2">
                    Powered by SocialSync AI
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Customize Widget Dialog */}
      <Dialog open={customizeDialogOpen} onOpenChange={setCustomizeDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Customize Widget</DialogTitle>
          </DialogHeader>
          <div className="grid gap-6 py-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Theme</Label>
                <div className="grid grid-cols-2 gap-2">
                  {widgetThemes.map((theme) => (
                    <button
                      key={theme.id}
                      onClick={() => setWidgetConfig(prev => ({ ...prev, theme: theme.id }))}
                      className={`p-3 rounded-lg border text-left transition-colors ${
                        widgetConfig.theme === theme.id 
                          ? "border-primary bg-primary/10" 
                          : "border-border hover:bg-muted"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <div 
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: theme.primary }}
                        />
                        <span className="font-medium text-sm">{theme.name}</span>
                      </div>
                      <div className="flex gap-1">
                        <div 
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: theme.primary }}
                        />
                        <div 
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: theme.secondary }}
                        />
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Position</Label>
                <div className="grid grid-cols-2 gap-2">
                  {widgetPositions.map((position) => (
                    <button
                      key={position.id}
                      onClick={() => setWidgetConfig(prev => ({ ...prev, position: position.id }))}
                      className={`p-3 rounded-lg border text-left transition-colors ${
                        widgetConfig.position === position.id 
                          ? "border-primary bg-primary/10" 
                          : "border-border hover:bg-muted"
                      }`}
                    >
                      <div className="text-lg mb-1">{position.icon}</div>
                      <div className="text-sm font-medium">{position.name}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Welcome Message</Label>
                <Textarea
                  value={widgetConfig.welcomeMessage}
                  onChange={(e) => setWidgetConfig(prev => ({ ...prev, welcomeMessage: e.target.value }))}
                  placeholder="Enter welcome message..."
                />
              </div>

              <div className="space-y-2">
                <Label>Input Placeholder</Label>
                <Input
                  value={widgetConfig.placeholder}
                  onChange={(e) => setWidgetConfig(prev => ({ ...prev, placeholder: e.target.value }))}
                  placeholder="Enter placeholder text..."
                />
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-avatar"
                  checked={widgetConfig.showAvatar}
                  onCheckedChange={(checked) => setWidgetConfig(prev => ({ ...prev, showAvatar: checked }))}
                />
                <Label htmlFor="show-avatar">Show Avatar</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-branding"
                  checked={widgetConfig.showBranding}
                  onCheckedChange={(checked) => setWidgetConfig(prev => ({ ...prev, showBranding: checked }))}
                />
                <Label htmlFor="show-branding">Show Branding</Label>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setCustomizeDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setCustomizeDialogOpen(false)}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}