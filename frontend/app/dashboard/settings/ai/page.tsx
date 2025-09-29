"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Settings,
  Save,
  RotateCcw,
  Shield,
  Zap,
  AlertTriangle,
  DollarSign,
} from "lucide-react"

// Available AI models with cost indicators
const aiModels = [
  { 
    id: "gpt-4o", 
    name: "GPT-4o", 
    provider: "OpenAI", 
    cost: "high",
    description: "Most capable model, best for complex tasks"
  },
  { 
    id: "gpt-4", 
    name: "GPT-4", 
    provider: "OpenAI", 
    cost: "high",
    description: "Highly capable, great reasoning"
  },
  { 
    id: "gpt-3.5-turbo", 
    name: "GPT-3.5 Turbo", 
    provider: "OpenAI", 
    cost: "medium",
    description: "Fast and efficient for most tasks"
  },
  { 
    id: "gemini-pro", 
    name: "Gemini Pro", 
    provider: "Google", 
    cost: "medium",
    description: "Google's advanced AI model"
  },
  { 
    id: "claude-3", 
    name: "Claude 3", 
    provider: "Anthropic", 
    cost: "high",
    description: "Excellent for analysis and writing"
  },
  { 
    id: "llama-2", 
    name: "Llama 2", 
    provider: "Meta", 
    cost: "low",
    description: "Open source, cost-effective"
  },
]

const answerModes = [
  { 
    id: "faq_only", 
    name: "FAQ Only", 
    description: "Only use predefined FAQ answers"
  },
  { 
    id: "hybrid", 
    name: "Hybrid", 
    description: "Use FAQ first, then AI if no match"
  },
  { 
    id: "llm_only", 
    name: "AI Only", 
    description: "Always generate AI responses"
  },
]

export default function AISettingsPage() {
  const [settings, setSettings] = useState({
    defaultModel: "gpt-4o",
    fallbackModel: "gpt-3.5-turbo",
    temperature: [0.7],
    maxTokens: [2048],
    responseTimeout: [30],
    safeReplies: true,
    answerMode: "hybrid",
    systemPrompt: "You are a helpful AI assistant. Provide accurate and concise answers to user questions.",
    customInstructions: "",
    disableAI: false, // NEW FEATURE
  })

  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    setIsSaving(true)
    // Simulate API call
    setTimeout(() => {
      setIsSaving(false)
      setHasChanges(false)
      // Toast notification would be shown here
    }, 2000)
  }

  const handleReset = () => {
    setSettings({
      defaultModel: "gpt-4o",
      fallbackModel: "gpt-3.5-turbo",
      temperature: [0.7],
      maxTokens: [2048],
      responseTimeout: [30],
      safeReplies: true,
      answerMode: "hybrid",
      systemPrompt: "You are a helpful AI assistant. Provide accurate and concise answers to user questions.",
      customInstructions: "",
      disableAI: false,
    })
    setHasChanges(false)
  }

  const getCostColor = (cost: string) => {
    switch (cost) {
      case "high":
        return "bg-red-500/20 text-red-400"
      case "medium":
        return "bg-yellow-500/20 text-yellow-400"
      case "low":
        return "bg-green-500/20 text-green-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getCostIcon = (cost: string) => {
    const count = cost === "high" ? 3 : cost === "medium" ? 2 : 1
    return Array.from({ length: count }).map((_, i) => (
      <DollarSign key={i} className="w-3 h-3" />
    ))
  }

  const getTemperatureLabel = (value: number) => {
    if (value <= 0.3) return "Precise"
    if (value <= 0.7) return "Balanced"
    if (value <= 1.2) return "Creative"
    return "Very Creative"
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Configuration</h1>
          <p className="text-muted-foreground">
            Configure AI models, behavior, and response settings
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

      {/* Unsaved Changes Alert */}
      {hasChanges && (
        <Alert className="border-yellow-500/50 bg-yellow-500/10">
          <AlertTriangle className="h-4 w-4 text-yellow-500" />
          <AlertDescription className="text-yellow-500">
            You have unsaved changes. Don't forget to save your configuration.
          </AlertDescription>
        </Alert>
      )}

      {/* AI Disable Toggle */}
      {settings.disableAI && (
        <Alert className="border-red-500/50 bg-red-500/10">
          <AlertTriangle className="h-4 w-4 text-red-500" />
          <AlertDescription className="text-red-500">
            AI responses are currently disabled. Your chatbot will only use predefined FAQ answers.
          </AlertDescription>
        </Alert>
      )}

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Model Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Default Model</Label>
              <Select 
                value={settings.defaultModel} 
                onValueChange={(value) => handleSettingChange("defaultModel", value)}
                disabled={settings.disableAI}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {aiModels.map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center justify-between w-full">
                        <div>
                          <div className="font-medium">{model.name}</div>
                          <div className="text-xs text-muted-foreground">{model.provider}</div>
                        </div>
                        <div className="flex items-center gap-1 ml-4">
                          <Badge variant="outline" className={getCostColor(model.cost)}>
                            <div className="flex items-center gap-1">
                              {getCostIcon(model.cost)}
                            </div>
                          </Badge>
                        </div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                {aiModels.find(m => m.id === settings.defaultModel)?.description}
              </p>
            </div>

            <div className="space-y-2">
              <Label>Fallback Model</Label>
              <Select 
                value={settings.fallbackModel} 
                onValueChange={(value) => handleSettingChange("fallbackModel", value)}
                disabled={settings.disableAI}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {aiModels.filter(m => m.id !== settings.defaultModel).map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div className="flex items-center justify-between w-full">
                        <div>
                          <div className="font-medium">{model.name}</div>
                          <div className="text-xs text-muted-foreground">{model.provider}</div>
                        </div>
                        <Badge variant="outline" className={getCostColor(model.cost)}>
                          <div className="flex items-center gap-1">
                            {getCostIcon(model.cost)}
                          </div>
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Temperature</Label>
                <Badge variant="outline">{getTemperatureLabel(settings.temperature[0])}</Badge>
              </div>
              <Slider
                value={settings.temperature}
                onValueChange={(value) => handleSettingChange("temperature", value)}
                max={2}
                min={0}
                step={0.1}
                disabled={settings.disableAI}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Precise (0)</span>
                <span>Current: {settings.temperature[0]}</span>
                <span>Creative (2)</span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Max Tokens</Label>
                <Badge variant="outline">{settings.maxTokens[0]} tokens</Badge>
              </div>
              <Slider
                value={settings.maxTokens}
                onValueChange={(value) => handleSettingChange("maxTokens", value)}
                max={4096}
                min={256}
                step={256}
                disabled={settings.disableAI}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>256</span>
                <span>4096</span>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Response Timeout</Label>
                <Badge variant="outline">{settings.responseTimeout[0]}s</Badge>
              </div>
              <Slider
                value={settings.responseTimeout}
                onValueChange={(value) => handleSettingChange("responseTimeout", value)}
                max={120}
                min={5}
                step={5}
                disabled={settings.disableAI}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>5s</span>
                <span>120s</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Behavior & Safety */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Behavior & Safety
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Disable AI Responses</Label>
              <p className="text-sm text-muted-foreground">
                Turn off AI completely and only use predefined FAQ answers
              </p>
            </div>
            <Switch
              checked={settings.disableAI}
              onCheckedChange={(checked) => handleSettingChange("disableAI", checked)}
            />
          </div>

          <div className="space-y-2">
            <Label>Answer Mode</Label>
            <Select 
              value={settings.answerMode} 
              onValueChange={(value) => handleSettingChange("answerMode", value)}
              disabled={settings.disableAI}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {answerModes.map((mode) => (
                  <SelectItem key={mode.id} value={mode.id}>
                    <div>
                      <div className="font-medium">{mode.name}</div>
                      <div className="text-xs text-muted-foreground">{mode.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Safe Replies</Label>
              <p className="text-sm text-muted-foreground">
                Enable content filtering and safety checks
              </p>
            </div>
            <Switch
              checked={settings.safeReplies}
              onCheckedChange={(checked) => handleSettingChange("safeReplies", checked)}
              disabled={settings.disableAI}
            />
          </div>
        </CardContent>
      </Card>

      {/* System Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            System Instructions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>System Prompt</Label>
            <Textarea
              value={settings.systemPrompt}
              onChange={(e) => handleSettingChange("systemPrompt", e.target.value)}
              placeholder="Enter system prompt..."
              className="min-h-[100px]"
              disabled={settings.disableAI}
            />
            <p className="text-xs text-muted-foreground">
              This prompt defines the AI's role and behavior. It's sent with every conversation.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Custom Instructions</Label>
            <Textarea
              value={settings.customInstructions}
              onChange={(e) => handleSettingChange("customInstructions", e.target.value)}
              placeholder="Enter additional instructions..."
              className="min-h-[100px]"
              disabled={settings.disableAI}
            />
            <p className="text-xs text-muted-foreground">
              Additional instructions or context specific to your use case.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}