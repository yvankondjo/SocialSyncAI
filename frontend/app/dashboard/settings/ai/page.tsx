"use client"

import React, { useState } from "react"
import { useAISettings } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ModelDisplay } from "@/components/ui/model-display"
import {
  Save,
  RefreshCw,
} from "lucide-react"
import { logos } from "@/lib/logos"
import Image from "next/image"

// Available AI models with cost indicators (synchronisés avec le backend)
const aiModels = [
  {
    id: "x-ai/grok-4",
    name: "Grok 4",
    provider: "xAI",
    cost: "high",
    description: "New generation Grok 4 : quick and contextual responses, optimized for multimodal creativity.",
    logoKey: "grok"
  },
  {
    id: "x-ai/grok-4-fast",
    name: "Grok 4 Fast",
    provider: "xAI",
    cost: "medium",
    description: "Fast version of Grok 4, balancing cost and speed for daily usage.",
    logoKey: "grok"
  },
  {
    id: "openai/gpt-4o",
    name: "GPT-4o",
    provider: "OpenAI",
    cost: "high",
    description: "GPT-4o offers high-end OpenAI precision with advanced multimodal reasoning.",
    logoKey: "openai"
  },
  {
    id: "openai/gpt-4o-mini",
    name: "GPT-4o mini",
    provider: "OpenAI",
    cost: "medium",
    description: "Mini version of GPT-4o : excellent text performance at a reduced cost.",
    logoKey: "openai"
  },
  {
    id: "openai/gpt-5",
    name: "GPT-5",
    provider: "OpenAI",
    cost: "high",
    description: "Featured GPT-5 : extreme contextual depth, designed for critical workloads.",
    logoKey: "openai"
  },
  {
    id: "openai/gpt-5-mini",
    name: "GPT-5 mini",
    provider: "OpenAI",
    cost: "medium",
    description: "Mini variant of GPT-5 : speed and robustness for massive integrations.",
    logoKey: "openai"
  },
  {
    id: "anthropic/claude-3.5-sonnet",
    name: "Claude 3.5 Sonnet",
    provider: "Anthropic",
    cost: "medium",
    description: "Claude 3.5 Sonnet combines style and logic : ideal for assistants and creative content.",
    logoKey: "claude"
  },
  {
    id: "anthropic/claude-sonnet-4",
    name: "Claude 4 Sonnet",
    provider: "Anthropic",
    cost: "high",
    description: "Claude 4 Sonnet provides reliable reasoning with great tone consistency.",
    logoKey: "claude"
  },
  {
    id: "anthropic/claude-sonnet-4.5",
    name: "Claude 4.5 Sonnet",
    provider: "Anthropic",
    cost: "high",
    description: "Evolution Sonnet 4.5 : best contextual responses and premium stability.",
    logoKey: "claude"
  },
  {
    id: "google/gemini-2.5-flash",
    name: "Gemini 2.5 Flash",
    provider: "Google",
    cost: "medium",
    description: "Gemini 2.5 Flash : ideal for rapid multimodal responses (text, image, audio).",
    logoKey: "googleGemini"
  },
  {
    id: "google/gemini-2.5-pro",
    name: "Gemini 2.5 Pro",
    provider: "Google",
    cost: "high",
    description: "Gemini 2.5 Pro : Google model with complete analytics and multimedia generation capabilities.",
    logoKey: "googleGemini"
  }
]

export default function AISettingsPage() {
  const {
    settings: aiSettings,
    isLoading,
    error,
    updateSettings,
    fetchSettings
  } = useAISettings()

  // État local pour les modifications non sauvegardées
  const [localSettings, setLocalSettings] = useState<any>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  // Initialiser les settings locaux quand les vrais settings sont chargés
  React.useEffect(() => {
    if (aiSettings && !localSettings) {
      setLocalSettings({
        ai_model: aiSettings.ai_model,
        temperature: aiSettings.temperature,
        system_prompt: aiSettings.system_prompt,
        is_active: aiSettings.is_active,
        top_p: aiSettings.top_p,
        lang: aiSettings.lang,
        tone: aiSettings.tone,
        doc_lang: aiSettings.doc_lang,
      })
    }
  }, [aiSettings, localSettings])

  // Les settings à afficher (locaux si modifiés, sinon depuis la BD)
  const currentSettings = localSettings || aiSettings

  const handleSettingChange = (key: string, value: any) => {
    setLocalSettings((prev: any) => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const handleSave = async () => {
    if (!localSettings) return

    setIsSaving(true)
    try {
      await updateSettings(localSettings)
      setHasChanges(false)
      // Recharger les settings depuis la BD pour s'assurer de la synchronisation
      await fetchSettings()
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error)
      // Le toast d'erreur sera affiché par le hook useAISettings
    } finally {
      setIsSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      // Recharger les settings depuis la BD
      await fetchSettings()
      // Remettre les settings locaux à null pour utiliser les données de la BD
      setLocalSettings(null)
      setHasChanges(false)
    } catch (error) {
      console.error('Erreur lors du reset:', error)
    }
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
    return "$".repeat(count)
  }

  const getTemperatureLabel = (value: number) => {
    if (value <= 0.3) return "Precise"
    if (value <= 0.7) return "Balanced"
    if (value <= 1.2) return "Creative"
    return "Very Creative"
  }

  // Afficher un état de chargement si les données ne sont pas encore chargées
  if (isLoading) {
    return (
      <div className="flex-1 p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Chargement des paramètres IA...</p>
          </div>
        </div>
      </div>
    )
  }

  // Afficher une erreur si le chargement a échoué
  if (error) {
    return (
      <div className="flex-1 p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-6xl mb-4">❌</p>
            <p className="text-red-500 mb-4">Erreur lors du chargement des paramètres IA</p>
            <Button onClick={fetchSettings} variant="outline">
              Réessayer
            </Button>
          </div>
        </div>
      </div>
    )
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
            <RefreshCw className="w-4 h-4 mr-2" />
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
          <AlertDescription className="text-yellow-500">
            ⚠️ You have unsaved changes. Don't forget to save your configuration.
          </AlertDescription>
        </Alert>
      )}

      {/* AI Status Alert */}
      {currentSettings && !currentSettings.is_active && (
        <Alert className="border-red-500/50 bg-red-500/10">
          <AlertDescription className="text-red-500">
            🚫 L'IA est actuellement désactivée. Aucune réponse automatique ne sera générée.
          </AlertDescription>
        </Alert>
      )}

      {/* Current AI Model Display */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Modèle IA Actuel</CardTitle>
        </CardHeader>
        <CardContent>
          <ModelDisplay variant="card" />
        </CardContent>
      </Card>

      {/* AI Global Toggle */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="text-base font-medium">Activer l'IA</Label>
              <p className="text-sm text-muted-foreground">
                Active ou désactive l'IA pour toutes les conversations
              </p>
            </div>
            <button
              disabled={!currentSettings}
              onClick={() => handleSettingChange("is_active", !currentSettings?.is_active)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                currentSettings?.is_active
                  ? 'bg-green-500 focus:ring-green-500'
                  : 'bg-red-500 focus:ring-red-500'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  currentSettings?.is_active ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Model Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            ⚙️ Model Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>Default Model</Label>
            <Select
              value={currentSettings?.ai_model || ""}
              onValueChange={(value: string) => handleSettingChange("ai_model", value)}
              disabled={!currentSettings?.is_active}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {aiModels.map((model) => (
                  <SelectItem 
                    key={model.id} 
                    value={model.id}
                    title={model.description}
                    className="cursor-pointer hover:bg-accent"
                  >
                    <div className="flex items-center justify-between w-full gap-3">
                      <div className="flex items-center gap-3">
                        {model.logoKey && logos[model.logoKey as keyof typeof logos] && (
                          <div className="relative w-6 h-6 flex-shrink-0">
                            <Image
                              src={logos[model.logoKey as keyof typeof logos]}
                              alt={`${model.provider} logo`}
                              width={24}
                              height={24}
                              className="object-contain"
                            />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate">{model.name}</div>
                          <div className="text-xs text-muted-foreground truncate">{model.provider}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
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
              {aiModels.find(m => m.id === currentSettings?.ai_model)?.description}
            </p>
          </div>

          <div className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Temperature</Label>
                <Badge variant="outline">{getTemperatureLabel(currentSettings?.temperature || 0.7)}</Badge>
              </div>
              <Slider
                value={[currentSettings?.temperature || 0.7]}
                onValueChange={(value: number[]) => handleSettingChange("temperature", value[0])}
                max={2}
                min={0}
                step={0.1}
                disabled={!currentSettings?.is_active}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Precise (0)</span>
                <span>Current: {currentSettings?.temperature?.toFixed(1) || "0.7"}</span>
                <span>Creative (2)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Instructions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            💬 System Instructions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label>System Prompt</Label>
            <Textarea
              value={currentSettings?.system_prompt || ""}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => handleSettingChange("system_prompt", (e.target as HTMLTextAreaElement).value)}
              placeholder="Enter system prompt..."
              className="min-h-[100px]"
              disabled={!currentSettings?.is_active}
            />
            <p className="text-xs text-muted-foreground">
              This prompt defines the AI's role and behavior. It's sent with every conversation.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}