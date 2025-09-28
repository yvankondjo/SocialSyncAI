"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
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
} from "lucide-react"

// Mock integration data
const integrations = [
  {
    id: "meta",
    name: "Meta (Instagram & Facebook)",
    description: "Connect your Instagram and Facebook pages for automated responses",
    icon: Instagram,
    status: "connected",
    accounts: ["@mycompany", "My Company Page"],
    scopes: ["messages", "public_profile", "pages_messaging"],
    lastSync: "2024-01-15T10:30:00Z",
  },
  {
    id: "twitter",
    name: "X (Twitter)",
    description: "Respond to mentions and direct messages on X",
    icon: Twitter,
    status: "disconnected",
    accounts: [],
    scopes: ["read", "write", "direct_messages"],
    lastSync: null,
  },
  {
    id: "whatsapp",
    name: "WhatsApp Business",
    description: "Connect WhatsApp Business API for customer support",
    icon: MessageCircle,
    status: "needs_setup",
    accounts: ["+1234567890"],
    scopes: ["messages", "business_profile"],
    lastSync: "2024-01-14T16:20:00Z",
  },
  {
    id: "web",
    name: "Web Widget",
    description: "Embed chat widget on your website",
    icon: Globe,
    status: "connected",
    accounts: ["widget-abc123"],
    scopes: ["embed"],
    lastSync: "2024-01-15T11:00:00Z",
  },
]

const widgetThemes = [
  { id: "default", name: "Default", primary: "#8b5cf6", secondary: "#1f2937" },
  { id: "blue", name: "Ocean Blue", primary: "#3b82f6", secondary: "#1e40af" },
  { id: "green", name: "Forest Green", primary: "#10b981", secondary: "#065f46" },
  { id: "orange", name: "Sunset Orange", primary: "#f59e0b", secondary: "#92400e" },
]

export default function ConnectPage() {
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null)
  const [showWidgetConfig, setShowWidgetConfig] = useState(false)
  const [widgetConfig, setWidgetConfig] = useState({
    theme: "default",
    position: "bottom-right",
    welcomeMessage: "Hi! How can I help you today?",
    placeholder: "Type your message...",
    showAvatar: true,
    showBranding: true,
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case "needs_setup":
        return <AlertCircle className="w-5 h-5 text-yellow-400" />
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-500/20 text-green-400"
      case "needs_setup":
        return "bg-yellow-500/20 text-yellow-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "connected":
        return "Connected"
      case "needs_setup":
        return "Needs Setup"
      default:
        return "Disconnected"
    }
  }

  const selectedTheme = widgetThemes.find((theme) => theme.id === widgetConfig.theme)

  const widgetSnippet = `<script>
  (function() {
    var widget = document.createElement('script');
    widget.src = 'https://widget.socialsyncai.com/widget.js';
    widget.setAttribute('data-widget-id', 'widget-abc123');
    widget.setAttribute('data-theme', '${widgetConfig.theme}');
    widget.setAttribute('data-position', '${widgetConfig.position}');
    document.head.appendChild(widget);
  })();
</script>`

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Connect Integrations</h1>
              <p className="text-muted-foreground">Connect your social accounts and communication channels</p>
            </div>
          </div>

          {/* Integrations Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {integrations.map((integration) => (
              <Card key={integration.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                        <integration.icon className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{integration.name}</CardTitle>
                        <p className="text-sm text-muted-foreground">{integration.description}</p>
                      </div>
                    </div>
                    {getStatusIcon(integration.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className={getStatusColor(integration.status)}>
                      {getStatusText(integration.status)}
                    </Badge>
                    {integration.lastSync && (
                      <span className="text-xs text-muted-foreground">
                        Last sync: {new Date(integration.lastSync).toLocaleString()}
                      </span>
                    )}
                  </div>

                  {integration.accounts.length > 0 && (
                    <div>
                      <div className="text-sm font-medium mb-2">Connected Accounts:</div>
                      <div className="space-y-1">
                        {integration.accounts.map((account) => (
                          <div key={account} className="text-sm text-muted-foreground">
                            • {account}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <div className="text-sm font-medium mb-2">Permissions:</div>
                    <div className="flex flex-wrap gap-1">
                      {integration.scopes.map((scope) => (
                        <Badge key={scope} variant="outline" className="text-xs">
                          {scope}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    {integration.status === "connected" ? (
                      <>
                        <Button variant="outline" size="sm" className="flex-1 bg-transparent">
                          Disconnect
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            integration.id === "web"
                              ? setShowWidgetConfig(true)
                              : setSelectedIntegration(integration.id)
                          }
                        >
                          <Settings className="w-4 h-4" />
                        </Button>
                      </>
                    ) : (
                      <Button size="sm" className="flex-1">
                        {integration.status === "needs_setup" ? "Complete Setup" : "Connect"}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Web Widget Preview */}
          {integrations.find((i) => i.id === "web")?.status === "connected" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5" />
                  Web Widget Integration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-3">Installation Code</h3>
                    <div className="relative">
                      <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                        <code>{widgetSnippet}</code>
                      </pre>
                      <Button
                        variant="outline"
                        size="sm"
                        className="absolute top-2 right-2 bg-transparent"
                        onClick={() => navigator.clipboard.writeText(widgetSnippet)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold mb-3">Widget Preview</h3>
                    <div className="bg-muted p-4 rounded-lg">
                      <div className="bg-background border border-border rounded-lg p-4 max-w-sm">
                        <div className="flex items-center gap-2 mb-3">
                          {widgetConfig.showAvatar && (
                            <div
                              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm"
                              style={{ backgroundColor: selectedTheme?.primary }}
                            >
                              AI
                            </div>
                          )}
                          <div className="font-medium">SocialSync AI</div>
                        </div>
                        <div className="bg-muted p-3 rounded-lg mb-3 text-sm">{widgetConfig.welcomeMessage}</div>
                        <div className="flex gap-2">
                          <Input placeholder={widgetConfig.placeholder} className="flex-1" />
                          <Button size="sm" style={{ backgroundColor: selectedTheme?.primary }}>
                            Send
                          </Button>
                        </div>
                        {widgetConfig.showBranding && (
                          <div className="text-xs text-muted-foreground mt-2 text-center">Powered by SocialSync AI</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setShowWidgetConfig(true)}>
                    <Palette className="w-4 h-4 mr-2" />
                    Customize
                  </Button>
                  <Button variant="outline">
                    <Eye className="w-4 h-4 mr-2" />
                    Preview
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Widget Configuration Dialog */}
      <Dialog open={showWidgetConfig} onOpenChange={setShowWidgetConfig}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Customize Web Widget</DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Theme</Label>
                <div className="grid grid-cols-2 gap-2">
                  {widgetThemes.map((theme) => (
                    <div
                      key={theme.id}
                      onClick={() => setWidgetConfig({ ...widgetConfig, theme: theme.id })}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        widgetConfig.theme === theme.id ? "border-primary bg-primary/10" : "border-border"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-4 h-4 rounded-full" style={{ backgroundColor: theme.primary }} />
                        <span className="text-sm font-medium">{theme.name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Position</Label>
                <div className="grid grid-cols-2 gap-2">
                  {["bottom-right", "bottom-left", "top-right", "top-left"].map((position) => (
                    <Button
                      key={position}
                      variant={widgetConfig.position === position ? "default" : "outline"}
                      size="sm"
                      onClick={() => setWidgetConfig({ ...widgetConfig, position })}
                    >
                      {position.replace("-", " ")}
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Welcome Message</Label>
                <Textarea
                  value={widgetConfig.welcomeMessage}
                  onChange={(e) => setWidgetConfig({ ...widgetConfig, welcomeMessage: e.target.value })}
                  placeholder="Enter welcome message..."
                />
              </div>

              <div className="space-y-2">
                <Label>Input Placeholder</Label>
                <Input
                  value={widgetConfig.placeholder}
                  onChange={(e) => setWidgetConfig({ ...widgetConfig, placeholder: e.target.value })}
                  placeholder="Enter placeholder text..."
                />
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Show Avatar</Label>
                <Switch
                  checked={widgetConfig.showAvatar}
                  onCheckedChange={(checked) => setWidgetConfig({ ...widgetConfig, showAvatar: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label>Show Branding</Label>
                <Switch
                  checked={widgetConfig.showBranding}
                  onCheckedChange={(checked) => setWidgetConfig({ ...widgetConfig, showBranding: checked })}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowWidgetConfig(false)}>
                Cancel
              </Button>
              <Button onClick={() => setShowWidgetConfig(false)}>Save Changes</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
