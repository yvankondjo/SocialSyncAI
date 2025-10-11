"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  MessageCircle,
  Palette,
  Settings,
  Eye,
  Save,
  RotateCcw,
  Upload,
  Monitor,
  Smartphone,
  Tablet,
} from "lucide-react"

const themes = [
  { id: "light", name: "Light", primary: "#ffffff", secondary: "#f8fafc", accent: "#3b82f6" },
  { id: "dark", name: "Dark", primary: "#1f2937", secondary: "#111827", accent: "#3b82f6" },
  { id: "blue", name: "Ocean Blue", primary: "#1e40af", secondary: "#3b82f6", accent: "#60a5fa" },
  { id: "green", name: "Forest Green", primary: "#166534", secondary: "#16a34a", accent: "#4ade80" },
  { id: "purple", name: "Royal Purple", primary: "#7c3aed", secondary: "#a855f7", accent: "#c084fc" },
]

const messageTemplates = [
  {
    id: "welcome",
    name: "Welcome Message",
    default: "Hello! Welcome to our support chat. How can I help you today?",
  },
  {
    id: "offline",
    name: "Offline Message", 
    default: "We're currently offline. Please leave a message and we'll get back to you soon!",
  },
  {
    id: "error",
    name: "Error Message",
    default: "I'm sorry, I encountered an error. Please try again or contact support.",
  },
  {
    id: "escalation",
    name: "Escalation Message",
    default: "Let me connect you with a human agent who can better assist you.",
  },
]

export default function ChatInterfacePage() {
  const [config, setConfig] = useState({
    // Appearance
    theme: "light",
    primaryColor: "#3b82f6",
    secondaryColor: "#f8fafc",
    accentColor: "#1d4ed8",
    fontFamily: "Inter",
    fontSize: "14",
    borderRadius: "8",
    
    // Messages
    templates: {
      welcome: "Hello! Welcome to our support chat. How can I help you today?",
      offline: "We're currently offline. Please leave a message and we'll get back to you soon!",
      error: "I'm sorry, I encountered an error. Please try again or contact support.",
      escalation: "Let me connect you with a human agent who can better assist you.",
    },
    
    // Behavior
    showTypingIndicator: true,
    showReadReceipts: true,
    enableFileUpload: true,
    maxFileSize: "10",
    allowedFileTypes: ["pdf", "doc", "docx", "txt", "jpg", "png"],
    enableEmojis: true,
    autoExpand: false,
    soundNotifications: true,
  })

  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [previewDevice, setPreviewDevice] = useState<"desktop" | "tablet" | "mobile">("desktop")

  const handleConfigChange = (key: string, value: any) => {
    if (key.includes('.')) {
      const [parent, child] = key.split('.')
      setConfig(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent as keyof typeof prev],
          [child]: value
        }
      }))
    } else {
      setConfig(prev => ({ ...prev, [key]: value }))
    }
    setHasChanges(true)
  }

  const handleSave = async () => {
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
      setHasChanges(false)
    }, 2000)
  }

  const handleReset = () => {
    setConfig({
      theme: "light",
      primaryColor: "#3b82f6",
      secondaryColor: "#f8fafc", 
      accentColor: "#1d4ed8",
      fontFamily: "Inter",
      fontSize: "14",
      borderRadius: "8",
      templates: {
        welcome: "Hello! Welcome to our support chat. How can I help you today?",
        offline: "We're currently offline. Please leave a message and we'll get back to you soon!",
        error: "I'm sorry, I encountered an error. Please try again or contact support.",
        escalation: "Let me connect you with a human agent who can better assist you.",
      },
      showTypingIndicator: true,
      showReadReceipts: true,
      enableFileUpload: true,
      maxFileSize: "10",
      allowedFileTypes: ["pdf", "doc", "docx", "txt", "jpg", "png"],
      enableEmojis: true,
      autoExpand: false,
      soundNotifications: true,
    })
    setHasChanges(false)
  }

  const getDeviceWidth = () => {
    switch (previewDevice) {
      case "mobile": return "w-80"
      case "tablet": return "w-96" 
      case "desktop": return "w-[500px]"
    }
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chat Interface</h1>
          <p className="text-muted-foreground">
            Customize the appearance and behavior of your chat widget
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleReset} disabled={!hasChanges}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button onClick={handleSave} disabled={!hasChanges || isSaving}>
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Configuration Panel */}
        <div className="space-y-6">
          <Tabs defaultValue="appearance">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="appearance">Appearance</TabsTrigger>
              <TabsTrigger value="behavior">Behavior</TabsTrigger>
            </TabsList>

            {/* Appearance Tab */}
            <TabsContent value="appearance" className="space-y-6">
              <Card className="max-w-2xl">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Palette className="w-5 h-5" />
                    Theme & Colors
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Primary Color</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="color"
                          value={config.primaryColor}
                          onChange={(e) => handleConfigChange("primaryColor", e.target.value)}
                          className="w-12 h-10 p-1 rounded cursor-pointer"
                        />
                        <Input
                          value={config.primaryColor}
                          onChange={(e) => handleConfigChange("primaryColor", e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Secondary Color</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="color"
                          value={config.secondaryColor}
                          onChange={(e) => handleConfigChange("secondaryColor", e.target.value)}
                          className="w-12 h-10 p-1 rounded cursor-pointer"
                        />
                        <Input
                          value={config.secondaryColor}
                          onChange={(e) => handleConfigChange("secondaryColor", e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Accent Color</Label>
                      <div className="flex items-center gap-2">
                        <Input
                          type="color"
                          value={config.accentColor}
                          onChange={(e) => handleConfigChange("accentColor", e.target.value)}
                          className="w-12 h-10 p-1 rounded cursor-pointer"
                        />
                        <Input
                          value={config.accentColor}
                          onChange={(e) => handleConfigChange("accentColor", e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Font Family</Label>
                      <Select value={config.fontFamily} onValueChange={(value) => handleConfigChange("fontFamily", value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Inter">Inter</SelectItem>
                          <SelectItem value="Roboto">Roboto</SelectItem>
                          <SelectItem value="Open Sans">Open Sans</SelectItem>
                          <SelectItem value="Poppins">Poppins</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Font Size</Label>
                      <Select value={config.fontSize} onValueChange={(value) => handleConfigChange("fontSize", value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="12">12px</SelectItem>
                          <SelectItem value="14">14px</SelectItem>
                          <SelectItem value="16">16px</SelectItem>
                          <SelectItem value="18">18px</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Border Radius</Label>
                      <Select value={config.borderRadius} onValueChange={(value) => handleConfigChange("borderRadius", value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="0">None</SelectItem>
                          <SelectItem value="4">Small</SelectItem>
                          <SelectItem value="8">Medium</SelectItem>
                          <SelectItem value="12">Large</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t text-center">
                    <p className="text-xs text-muted-foreground">Powered by ConversAI</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Behavior Tab */}
            <TabsContent value="behavior" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Chat Behavior</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">Typing Indicator</Label>
                      <p className="text-sm text-muted-foreground">Show when AI is typing</p>
                    </div>
                    <Switch
                      checked={config.showTypingIndicator}
                      onCheckedChange={(checked) => handleConfigChange("showTypingIndicator", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">Read Receipts</Label>
                      <p className="text-sm text-muted-foreground">Show when messages are read</p>
                    </div>
                    <Switch
                      checked={config.showReadReceipts}
                      onCheckedChange={(checked) => handleConfigChange("showReadReceipts", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">File Upload</Label>
                      <p className="text-sm text-muted-foreground">Allow users to upload files</p>
                    </div>
                    <Switch
                      checked={config.enableFileUpload}
                      onCheckedChange={(checked) => handleConfigChange("enableFileUpload", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">Emojis</Label>
                      <p className="text-sm text-muted-foreground">Enable emoji picker</p>
                    </div>
                    <Switch
                      checked={config.enableEmojis}
                      onCheckedChange={(checked) => handleConfigChange("enableEmojis", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">Auto Expand</Label>
                      <p className="text-sm text-muted-foreground">Automatically expand chat on page load</p>
                    </div>
                    <Switch
                      checked={config.autoExpand}
                      onCheckedChange={(checked) => handleConfigChange("autoExpand", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="font-semibold text-foreground">Sound Notifications</Label>
                      <p className="text-sm text-muted-foreground">Play sound for new messages</p>
                    </div>
                    <Switch
                      checked={config.soundNotifications}
                      onCheckedChange={(checked) => handleConfigChange("soundNotifications", checked)}
                      className="data-[state=checked]:bg-primary data-[state=unchecked]:bg-gray-300"
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Live Preview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Live Preview</h3>
            <div className="flex items-center gap-2">
              <Button
                variant={previewDevice === "desktop" ? "default" : "outline"}
                size="sm"
                onClick={() => setPreviewDevice("desktop")}
              >
                <Monitor className="w-4 h-4" />
              </Button>
              <Button
                variant={previewDevice === "tablet" ? "default" : "outline"}
                size="sm"
                onClick={() => setPreviewDevice("tablet")}
              >
                <Tablet className="w-4 h-4" />
              </Button>
              <Button
                variant={previewDevice === "mobile" ? "default" : "outline"}
                size="sm"
                onClick={() => setPreviewDevice("mobile")}
              >
                <Smartphone className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex justify-center">
            <div className={`${getDeviceWidth()} bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-lg p-4 min-h-[600px] relative`}>
              {/* Chat Widget Preview */}
              <div 
                className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border h-full flex flex-col"
                style={{ 
                  borderRadius: `${config.borderRadius}px`,
                  fontFamily: config.fontFamily,
                  fontSize: `${config.fontSize}px`
                }}
              >
                {/* Chat Header */}
                <div 
                  className="p-4 border-b flex items-center gap-3 rounded-t-lg"
                  style={{ backgroundColor: config.primaryColor, borderRadius: `${config.borderRadius}px ${config.borderRadius}px 0 0` }}
                >
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                    <MessageCircle className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-white font-medium">Support Chat</div>
                    <div className="text-white/80 text-xs">Online</div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 p-4 space-y-3 overflow-y-auto">
                  <div className="flex justify-start">
                    <div 
                      className="max-w-[80%] p-3 rounded-lg text-sm"
                      style={{ 
                        backgroundColor: config.secondaryColor,
                        borderRadius: `${config.borderRadius}px`
                      }}
                    >
                      {config.templates.welcome}
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <div 
                      className="max-w-[80%] p-3 rounded-lg text-sm text-white"
                      style={{ 
                        backgroundColor: config.accentColor,
                        borderRadius: `${config.borderRadius}px`
                      }}
                    >
                      Hello! I need help with my account.
                    </div>
                  </div>

                  {config.showTypingIndicator && (
                    <div className="flex justify-start">
                      <div 
                        className="p-3 rounded-lg"
                        style={{ 
                          backgroundColor: config.secondaryColor,
                          borderRadius: `${config.borderRadius}px`
                        }}
                      >
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        placeholder="Type your message..."
                        className="w-full p-3 border rounded-lg pr-12 text-sm"
                        style={{ borderRadius: `${config.borderRadius}px` }}
                        disabled
                      />
                      <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                        {config.enableFileUpload && (
                          <Upload className="w-4 h-4 text-gray-400" />
                        )}
                        {config.enableEmojis && (
                          <span className="text-gray-400">😊</span>
                        )}
                      </div>
                    </div>
                    <Button 
                      size="sm"
                      style={{ backgroundColor: config.primaryColor }}
                      disabled
                    >
                      <MessageCircle className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}