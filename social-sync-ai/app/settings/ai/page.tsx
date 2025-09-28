"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Bot, Save, RotateCcw, Shield, Zap } from "lucide-react"

export default function AISettingsPage() {
  const [settings, setSettings] = useState({
    defaultModel: "gpt-4o",
    temperature: [0.7],
    maxTokens: [2048],
    safeReplies: true,
    fallbackModel: "gpt-4",
    responseTimeout: [30],
    answerMode: "faq_only",
    systemPrompt: "You are a helpful AI assistant for customer support. Be friendly, professional, and concise.",
    customInstructions: "",
    disableAI: false,
  })

  const [hasChanges, setHasChanges] = useState(false)

  const models = [
    { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI", cost: "High" },
    { id: "gpt-4", name: "GPT-4", provider: "OpenAI", cost: "High" },
    { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", provider: "OpenAI", cost: "Medium" },
    { id: "gemini-pro", name: "Gemini Pro", provider: "Google", cost: "Medium" },
    { id: "claude-3", name: "Claude 3", provider: "Anthropic", cost: "High" },
    { id: "llama-2", name: "Llama 2", provider: "Meta", cost: "Low" },
  ]

  const handleSave = () => {
    // Save settings to backend
    console.log("Saving AI settings:", settings)
    setHasChanges(false)
  }

  const handleReset = () => {
    // Reset to defaults
    setHasChanges(false)
  }

  const updateSetting = (key: string, value: any) => {
    setSettings({ ...settings, [key]: value })
    setHasChanges(true)
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
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Bot className="w-6 h-6" />
                AI Settings
              </h1>
              <p className="text-muted-foreground">Configure your AI model behavior and preferences</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReset} disabled={!hasChanges}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <Button onClick={handleSave} disabled={!hasChanges}>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </div>
          </div>

          {hasChanges && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
              <p className="text-yellow-400 text-sm">You have unsaved changes. Don't forget to save your settings.</p>
            </div>
          )}

          {/* Model Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Model Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Default Model</Label>
                  <Select value={settings.defaultModel} onValueChange={(value) => updateSetting("defaultModel", value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div className="flex items-center justify-between w-full">
                            <span>{model.name}</span>
                            <div className="flex items-center gap-2 ml-4">
                              <Badge variant="outline" className="text-xs">
                                {model.provider}
                              </Badge>
                              <Badge
                                variant="outline"
                                className={`text-xs ${
                                  model.cost === "High"
                                    ? "text-red-400"
                                    : model.cost === "Medium"
                                      ? "text-yellow-400"
                                      : "text-green-400"
                                }`}
                              >
                                {model.cost}
                              </Badge>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Fallback Model</Label>
                  <Select
                    value={settings.fallbackModel}
                    onValueChange={(value) => updateSetting("fallbackModel", value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {models.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Temperature: {settings.temperature[0]}</Label>
                  <Slider
                    value={settings.temperature}
                    onValueChange={(value) => updateSetting("temperature", value)}
                    max={2}
                    min={0}
                    step={0.1}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">
                    Lower values make responses more focused, higher values more creative
                  </p>
                </div>

                <div className="space-y-2">
                  <Label>Max Tokens: {settings.maxTokens[0]}</Label>
                  <Slider
                    value={settings.maxTokens}
                    onValueChange={(value) => updateSetting("maxTokens", value)}
                    max={4096}
                    min={256}
                    step={256}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">Maximum length of AI responses</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Response Timeout: {settings.responseTimeout[0]}s</Label>
                <Slider
                  value={settings.responseTimeout}
                  onValueChange={(value) => updateSetting("responseTimeout", value)}
                  max={120}
                  min={5}
                  step={5}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">Maximum time to wait for AI response</p>
              </div>
            </CardContent>
          </Card>

          {/* Behavior Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Behavior & Safety
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Disable AI</Label>
                  <p className="text-sm text-muted-foreground">Prevent AI from responding to questions</p>
                </div>
                <Switch
                  checked={settings.disableAI}
                  onCheckedChange={(checked) => updateSetting("disableAI", checked)}
                />
              </div>

              <div className="space-y-2">
                <Label>Answer Mode</Label>
                <Select value={settings.answerMode} onValueChange={(value) => updateSetting("answerMode", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="faq_only">FAQ Only</SelectItem>
                    <SelectItem value="hybrid">Hybrid (FAQ + AI)</SelectItem>
                    <SelectItem value="llm_only">AI Only</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  How the AI should handle responses: use only FAQ, combine FAQ with AI, or use AI only
                </p>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Safe Replies</Label>
                  <p className="text-sm text-muted-foreground">Enable content filtering and safety checks</p>
                </div>
                <Switch
                  checked={settings.safeReplies}
                  onCheckedChange={(checked) => updateSetting("safeReplies", checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* System Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>System Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea
                  value={settings.systemPrompt}
                  onChange={(e) => updateSetting("systemPrompt", e.target.value)}
                  placeholder="Enter system prompt..."
                  className="min-h-[100px]"
                />
                <p className="text-xs text-muted-foreground">
                  Base instructions that define the AI's role and behavior
                </p>
              </div>

              <div className="space-y-2">
                <Label>Custom Instructions (Optional)</Label>
                <Textarea
                  value={settings.customInstructions}
                  onChange={(e) => updateSetting("customInstructions", e.target.value)}
                  placeholder="Add any additional custom instructions..."
                  className="min-h-[80px]"
                />
                <p className="text-xs text-muted-foreground">
                  Additional context or specific guidelines for your use case
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
