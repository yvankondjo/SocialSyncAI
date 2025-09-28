"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { MessageCircle, Palette, Eye, Save, RotateCcw, Upload, Copy } from "lucide-react"

const colorPresets = [
  { name: "Purple", primary: "#8b5cf6", secondary: "#1f2937", accent: "#a855f7" },
  { name: "Blue", primary: "#3b82f6", secondary: "#1e40af", accent: "#60a5fa" },
  { name: "Green", primary: "#10b981", secondary: "#065f46", accent: "#34d399" },
  { name: "Orange", primary: "#f59e0b", secondary: "#92400e", accent: "#fbbf24" },
  { name: "Red", primary: "#ef4444", secondary: "#991b1b", accent: "#f87171" },
  { name: "Pink", primary: "#ec4899", secondary: "#be185d", accent: "#f472b6" },
]

export default function ChatInterfaceSettingsPage() {
  const [settings, setSettings] = useState({
    // Theme
    primaryColor: "#8b5cf6",
    secondaryColor: "#1f2937",
    accentColor: "#a855f7",
    borderRadius: "8",

    // Branding
    companyName: "SocialSync AI",
    logoUrl: "",
    showLogo: true,
    showBranding: true,

    // Messages
    welcomeMessage: "Hi! How can I help you today?",
    placeholderText: "Type your message...",
    offlineMessage: "We're currently offline. Leave a message and we'll get back to you!",

    // Behavior
    showTypingIndicator: true,
    showTimestamps: false,
    enableSoundNotifications: true,
    autoExpand: false,

    // Position & Size
    position: "bottom-right",
    widgetSize: "medium",

    // Avatar
    showAvatar: true,
    avatarUrl: "",
    avatarStyle: "circle",
  })

  const [hasChanges, setHasChanges] = useState(false)

  const updateSetting = (key: string, value: any) => {
    setSettings({ ...settings, [key]: value })
    setHasChanges(true)
  }

  const applyColorPreset = (preset: any) => {
    setSettings({
      ...settings,
      primaryColor: preset.primary,
      secondaryColor: preset.secondary,
      accentColor: preset.accent,
    })
    setHasChanges(true)
  }

  const handleSave = () => {
    console.log("Saving chat interface settings:", settings)
    setHasChanges(false)
  }

  const widgetCode = `<script>
  (function() {
    var widget = document.createElement('script');
    widget.src = 'https://widget.socialsyncai.com/widget.js';
    widget.setAttribute('data-widget-id', 'your-widget-id');
    widget.setAttribute('data-primary-color', '${settings.primaryColor}');
    widget.setAttribute('data-position', '${settings.position}');
    document.head.appendChild(widget);
  })();
</script>`

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <MessageCircle className="w-6 h-6" />
                Chat Interface
              </h1>
              <p className="text-muted-foreground">Customize the appearance and behavior of your chat widget</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" disabled={!hasChanges}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <Button onClick={handleSave} disabled={!hasChanges}>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Settings */}
            <div className="space-y-6">
              {/* Theme & Colors */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Palette className="w-5 h-5" />
                    Theme & Colors
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="mb-3 block">Color Presets</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {colorPresets.map((preset) => (
                        <Button
                          key={preset.name}
                          variant="outline"
                          size="sm"
                          onClick={() => applyColorPreset(preset)}
                          className="flex items-center gap-2 justify-start"
                        >
                          <div className="w-4 h-4 rounded-full" style={{ backgroundColor: preset.primary }} />
                          {preset.name}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    <div className="space-y-2">
                      <Label>Primary Color</Label>
                      <div className="flex gap-2">
                        <Input
                          type="color"
                          value={settings.primaryColor}
                          onChange={(e) => updateSetting("primaryColor", e.target.value)}
                          className="w-16 h-10 p-1"
                        />
                        <Input
                          value={settings.primaryColor}
                          onChange={(e) => updateSetting("primaryColor", e.target.value)}
                          placeholder="#8b5cf6"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Border Radius</Label>
                      <Select
                        value={settings.borderRadius}
                        onValueChange={(value) => updateSetting("borderRadius", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="4">Small (4px)</SelectItem>
                          <SelectItem value="8">Medium (8px)</SelectItem>
                          <SelectItem value="12">Large (12px)</SelectItem>
                          <SelectItem value="16">Extra Large (16px)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Branding */}
              <Card>
                <CardHeader>
                  <CardTitle>Branding</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Company Name</Label>
                    <Input
                      value={settings.companyName}
                      onChange={(e) => updateSetting("companyName", e.target.value)}
                      placeholder="Your Company Name"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Logo URL</Label>
                    <div className="flex gap-2">
                      <Input
                        value={settings.logoUrl}
                        onChange={(e) => updateSetting("logoUrl", e.target.value)}
                        placeholder="https://example.com/logo.png"
                      />
                      <Button variant="outline" size="sm">
                        <Upload className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Show Logo</Label>
                    <Switch
                      checked={settings.showLogo}
                      onCheckedChange={(checked) => updateSetting("showLogo", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Show "Powered by" Branding</Label>
                    <Switch
                      checked={settings.showBranding}
                      onCheckedChange={(checked) => updateSetting("showBranding", checked)}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Messages */}
              <Card>
                <CardHeader>
                  <CardTitle>Messages</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Welcome Message</Label>
                    <Textarea
                      value={settings.welcomeMessage}
                      onChange={(e) => updateSetting("welcomeMessage", e.target.value)}
                      placeholder="Hi! How can I help you today?"
                      className="min-h-[60px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Input Placeholder</Label>
                    <Input
                      value={settings.placeholderText}
                      onChange={(e) => updateSetting("placeholderText", e.target.value)}
                      placeholder="Type your message..."
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Offline Message</Label>
                    <Textarea
                      value={settings.offlineMessage}
                      onChange={(e) => updateSetting("offlineMessage", e.target.value)}
                      placeholder="We're currently offline..."
                      className="min-h-[60px]"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Behavior */}
              <Card>
                <CardHeader>
                  <CardTitle>Behavior</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Show Typing Indicator</Label>
                    <Switch
                      checked={settings.showTypingIndicator}
                      onCheckedChange={(checked) => updateSetting("showTypingIndicator", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Show Timestamps</Label>
                    <Switch
                      checked={settings.showTimestamps}
                      onCheckedChange={(checked) => updateSetting("showTimestamps", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Sound Notifications</Label>
                    <Switch
                      checked={settings.enableSoundNotifications}
                      onCheckedChange={(checked) => updateSetting("enableSoundNotifications", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Auto Expand on Load</Label>
                    <Switch
                      checked={settings.autoExpand}
                      onCheckedChange={(checked) => updateSetting("autoExpand", checked)}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Preview & Code */}
            <div className="space-y-6">
              {/* Live Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Live Preview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-6 rounded-lg">
                    <div
                      className="bg-background border rounded-lg p-4 max-w-sm mx-auto shadow-lg"
                      style={{ borderRadius: `${settings.borderRadius}px` }}
                    >
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-4 pb-3 border-b">
                        {settings.showLogo && settings.logoUrl && (
                          <img src={settings.logoUrl || "/placeholder.svg"} alt="Logo" className="w-8 h-8 rounded" />
                        )}
                        {settings.showAvatar && (
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                            style={{ backgroundColor: settings.primaryColor }}
                          >
                            AI
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-sm">{settings.companyName}</div>
                          <div className="text-xs text-muted-foreground">Online</div>
                        </div>
                      </div>

                      {/* Messages */}
                      <div className="space-y-3 mb-4">
                        <div
                          className="bg-muted p-3 rounded-lg text-sm"
                          style={{ borderRadius: `${settings.borderRadius}px` }}
                        >
                          {settings.welcomeMessage}
                        </div>
                        <div className="flex justify-end">
                          <div
                            className="text-white p-3 rounded-lg text-sm max-w-[80%]"
                            style={{
                              backgroundColor: settings.primaryColor,
                              borderRadius: `${settings.borderRadius}px`,
                            }}
                          >
                            Hello, I need help with my account
                          </div>
                        </div>
                        {settings.showTypingIndicator && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <div className="flex gap-1">
                              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce" />
                              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce delay-100" />
                              <div className="w-1 h-1 bg-muted-foreground rounded-full animate-bounce delay-200" />
                            </div>
                            AI is typing...
                          </div>
                        )}
                      </div>

                      {/* Input */}
                      <div className="flex gap-2">
                        <Input
                          placeholder={settings.placeholderText}
                          className="flex-1 text-sm"
                          style={{ borderRadius: `${settings.borderRadius}px` }}
                        />
                        <Button
                          size="sm"
                          style={{
                            backgroundColor: settings.primaryColor,
                            borderRadius: `${settings.borderRadius}px`,
                          }}
                        >
                          Send
                        </Button>
                      </div>

                      {settings.showBranding && (
                        <div className="text-xs text-muted-foreground text-center mt-3">Powered by SocialSync AI</div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Integration Code */}
              <Card>
                <CardHeader>
                  <CardTitle>Integration Code</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="relative">
                      <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                        <code>{widgetCode}</code>
                      </pre>
                      <Button
                        variant="outline"
                        size="sm"
                        className="absolute top-2 right-2 bg-transparent"
                        onClick={() => navigator.clipboard.writeText(widgetCode)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Copy this code and paste it into your website's HTML, just before the closing {"</body>"} tag.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
