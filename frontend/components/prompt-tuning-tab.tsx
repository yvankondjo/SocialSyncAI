"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Clock, Zap, Save, RotateCcw, Sparkles } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { useAISettings } from "@/lib/api"
import { logos } from "@/lib/logos"
import Image from "next/image"

// AI Settings interface
interface AISettings {
  id?: string
  system_prompt: string
  ai_model: string
  temperature: number
  top_p: number
  lang: string
  tone: string
  is_active: boolean
}

interface AIModel {
  id: string
  name: string
  logoKey: keyof typeof logos
  description: string
  provider: string
}

// Available AI models with official logos and OpenRouter identifiers
const AI_MODELS: AIModel[] = [
  {
    id: "anthropic/claude-3.5-haiku",
    name: "Claude 3.5 Haiku",
    logoKey: "claude",
    description: "Fast and efficient for everyday tasks",
    provider: "Anthropic"
  },
  {
    id: "openai/gpt-4o",
    name: "GPT-4o",
    logoKey: "openai",
    description: "Powerful and versatile for all types of tasks",
    provider: "OpenAI"
  },
  {
    id: "openai/gpt-4o-mini",
    name: "GPT-4o Mini", 
    logoKey: "openai",
    description: "Optimized and cost-effective version",
    provider: "OpenAI"
  },
  {
    id: "google/gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    logoKey: "gemini",
    description: "Google's latest multimodal AI model",
    provider: "Google"
  },
  {
    id: "x-ai/grok-2",
    name: "Grok 2",
    logoKey: "grok",
    description: "Innovative model with unique approach",
    provider: "xAI"
  }
]

// Prompt templates by industry
const PROMPT_TEMPLATES = {
  social: {
    name: "Social Media",
    prompt: `You are an AI assistant specialized in social media management for {{brand_name}}.

Your responsibilities:
- Create engaging and viral content for social media
- Analyze trending hashtags and topics
- Optimize posts for each platform (Instagram, TikTok, Facebook, Twitter)
- Propose growth and engagement strategies
- Respond in {{lang}} with a {{tone}} tone
- Provide creative and authentic advice`
  },
  ecommerce: {
    name: "E-commerce", 
    prompt: `You are an AI expert in e-commerce for {{brand_name}}.

Your responsibilities:
- Optimize product descriptions to increase conversions
- Analyze customer buying behavior
- Propose pricing and promotion strategies
- Create targeted marketing campaigns
- Improve customer experience and purchase journey
- Respond in {{lang}} with a {{tone}} tone
- Provide data-driven sales insights`
  },
  support: {
    name: "Customer Support",
    prompt: `You are an AI assistant dedicated to customer support for {{brand_name}}.

Your responsibilities:
- Quickly resolve customer issues
- Provide accurate and empathetic responses
- Escalate complex cases to human team
- Maintain high customer satisfaction levels
- Follow company procedures and policies
- Respond in {{lang}} with a {{tone}} tone
- Document interactions to improve service`
  }
}

export function PromptTuningTab() {
  const { toast } = useToast()
  const { 
    data: currentSettings, 
    isLoading: apiLoading, 
    mutate
  } = useAISettings()
  
  const updateSettings = async (settings: any) => {
    // Mock implementation
    console.log('Updating settings:', settings)
    return mutate()
  }
  
  const testAIResponse = async (params: any) => {
    // Mock implementation
    console.log('Testing AI response with params:', params)
    return { 
      response: 'Test response from AI', 
      response_time: 1200,
      confidence: 0.85
    }
  }
  
  // Working settings state (unsaved modifications)
  const [workingSettings, setWorkingSettings] = useState<AISettings>({
    system_prompt: PROMPT_TEMPLATES.social.prompt,
    ai_model: "anthropic/claude-3.5-haiku",
    temperature: 0.20,
    top_p: 1.00,
    lang: "en",
    tone: "friendly",
    is_active: true
  })
  
  // UI states
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [testInput, setTestInput] = useState("How can I improve engagement on my Instagram posts?")
  const [testResponse, setTestResponse] = useState("")
  const [testMetrics, setTestMetrics] = useState({ responseTime: 0, confidence: 0 })

  // Sync loaded settings with working settings
  useEffect(() => {
    if (currentSettings) {
      setWorkingSettings(currentSettings)
      setHasUnsavedChanges(false)
    }
  }, [currentSettings])

  const variables = [
    { name: "brand_name", value: "SocialSync" },
    { name: "lang", value: workingSettings.lang },
    { name: "tone", value: workingSettings.tone },
  ]

  // Fonctions utilitaires
  const updateWorkingSetting = (key: keyof AISettings, value: any) => {
    setWorkingSettings(prev => ({ ...prev, [key]: value }))
    setHasUnsavedChanges(true)
  }

  const loadTemplate = (templateKey: keyof typeof PROMPT_TEMPLATES) => {
    updateWorkingSetting('system_prompt', PROMPT_TEMPLATES[templateKey].prompt)
  }

  const saveSettings = async () => {
    setIsLoading(true)
    try {
      await updateSettings(workingSettings)
      setHasUnsavedChanges(false)
    } catch (error) {
      // L'erreur est déjà gérée dans le hook
    } finally {
      setIsLoading(false)
    }
  }

  const handleTestAIResponse = async () => {
    setIsTesting(true)
    try {
      const result = await testAIResponse({
        message: testInput,
        settings: workingSettings
      })
      
      setTestResponse(result.response)
      setTestMetrics({
        responseTime: result.response_time,
        confidence: result.confidence
      })
    } catch (error) {
      // L'erreur est déjà gérée dans le hook
    } finally {
      setIsTesting(false)
    }
  }

  const resetToCurrentSettings = () => {
    if (currentSettings) {
      setWorkingSettings(currentSettings)
      setHasUnsavedChanges(false)
    }
  }

  const selectedModel = AI_MODELS.find(model => model.id === workingSettings.ai_model)

  return (
    <div className="flex flex-col xl:flex-row gap-6 p-4 lg:p-6">
      {/* Main Content */}
      <div className="flex-1 space-y-6">
        {/* Header with save buttons */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold">AI Configuration</h2>
            <p className="text-muted-foreground">Customize your AI assistant behavior</p>
          </div>
          <div className="flex gap-2">
            {hasUnsavedChanges && (
              <Button
                variant="outline"
                onClick={resetToCurrentSettings}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Cancel
              </Button>
            )}
            <Button
              onClick={saveSettings}
              disabled={!hasUnsavedChanges || isLoading || apiLoading}
              className="flex items-center gap-2 gradient-primary text-white border-0"
            >
              <Save className="w-4 h-4" />
              {isLoading || apiLoading ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        </div>

        {hasUnsavedChanges && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-sm text-amber-800">
              ⚠️ You have unsaved changes. Click "Save Changes" to keep them.
            </p>
          </div>
        )}

        {/* System Prompt - TOP PRIORITY */}
        <Card className="shadow-soft">
          <CardHeader>
            <CardTitle className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <span>System Prompt</span>
              <Select onValueChange={(value) => loadTemplate(value as keyof typeof PROMPT_TEMPLATES)}>
                <SelectTrigger className="w-full sm:w-48">
                  <SelectValue placeholder="Load template" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PROMPT_TEMPLATES).map(([key, template]) => (
                    <SelectItem key={key} value={key}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              value={workingSettings.system_prompt}
              onChange={(e) => updateWorkingSetting('system_prompt', e.target.value)}
              className="min-h-[300px] resize-none text-sm font-mono"
              placeholder="Enter your system prompt..."
            />
            <div className="flex flex-wrap gap-2">
              <p className="text-xs text-muted-foreground w-full mb-2">Available variables:</p>
              {variables.map((variable) => (
                <Badge 
                  key={variable.name} 
                  variant="secondary" 
                  className="cursor-pointer text-xs hover:bg-secondary/80"
                  onClick={() => {
                    const textarea = document.querySelector('textarea') as HTMLTextAreaElement
                    if (textarea) {
                      const cursorPos = textarea.selectionStart
                      const newValue = workingSettings.system_prompt.slice(0, cursorPos) + 
                                     `{{${variable.name}}}` + 
                                     workingSettings.system_prompt.slice(cursorPos)
                      updateWorkingSetting('system_prompt', newValue)
                    }
                  }}
                >
                  {`{{${variable.name}}}`}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Model Selection & Settings - BOTTOM */}
        <Card className="shadow-soft">
          <CardHeader>
            <CardTitle>AI Model & Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AI Model Selection */}
            <div className="space-y-4">
              <Label className="text-base font-medium">Choose AI Model</Label>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {AI_MODELS.map((model) => {
                  const isSelected = workingSettings.ai_model === model.id
                  return (
                    <div
                      key={model.id}
                      className={`border rounded-lg p-3 cursor-pointer transition-all hover:shadow-md ${
                        isSelected 
                          ? 'border-primary bg-primary/5 shadow-md' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => updateWorkingSetting('ai_model', model.id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 flex-shrink-0">
                          <Image
                            src={logos[model.logoKey]}
                            alt={model.provider}
                            width={32}
                            height={32}
                            className="w-full h-full object-contain"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className={`font-medium text-sm ${isSelected ? 'text-primary' : ''}`}>
                            {model.name}
                          </h4>
                          <p className="text-xs text-muted-foreground truncate">
                            {model.provider}
                          </p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            <Separator />

            {/* Tone and Language Settings */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="tone">Response Tone</Label>
                <Select 
                  value={workingSettings.tone} 
                  onValueChange={(value) => updateWorkingSetting('tone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="friendly">🙂 Friendly</SelectItem>
                    <SelectItem value="professional">👔 Professional</SelectItem>
                    <SelectItem value="casual">😎 Casual</SelectItem>
                    <SelectItem value="neutral">⚖️ Neutral</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <Select 
                  value={workingSettings.lang} 
                  onValueChange={(value) => updateWorkingSetting('lang', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">🇺🇸 English</SelectItem>
                    <SelectItem value="fr">🇫🇷 Français</SelectItem>
                    <SelectItem value="es">🇪🇸 Español</SelectItem>
                    <SelectItem value="auto">🌍 Auto</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

          </CardContent>
        </Card>
      </div>

      {/* Test Panel */}
      <div className="w-full xl:w-96">
        <Card className="shadow-soft xl:sticky xl:top-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              AI Test
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="test-input">Test Message</Label>
              <Textarea
                id="test-input"
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                placeholder="Type your test message..."
                className="text-sm"
                rows={3}
              />
              <Button 
                onClick={handleTestAIResponse}
                disabled={isTesting || !testInput.trim()}
                className="w-full gradient-primary text-white border-0"
              >
                {isTesting ? "Testing..." : "Test Response"}
              </Button>
            </div>

            {selectedModel && (
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <Image
                    src={logos[selectedModel.logoKey]}
                    alt={selectedModel.provider}
                    width={16}
                    height={16}
                    className="w-4 h-4"
                  />
                  <span className="text-sm font-medium">{selectedModel.name}</span>
                </div>
                <p className="text-xs text-muted-foreground">{selectedModel.description}</p>
              </div>
            )}

            {testResponse && (
              <div className="border rounded-lg p-4 bg-background">
                <div className="text-sm font-medium mb-2">AI Response:</div>
                <p className="text-sm leading-relaxed">{testResponse}</p>
                <div className="flex gap-2 mt-3">
                  <Badge variant="outline" className="text-xs">
                    <Clock className="w-3 h-3 mr-1" />
                    {testMetrics.responseTime.toFixed(1)}s
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    <Zap className="w-3 h-3 mr-1" />
                    {(testMetrics.confidence * 100).toFixed(0)}%
                  </Badge>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label>Current Configuration</Label>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model:</span>
                  <span className="font-medium">{selectedModel?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Language:</span>
                  <span className="font-medium">{workingSettings.lang}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tone:</span>
                  <span className="font-medium">{workingSettings.tone}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
