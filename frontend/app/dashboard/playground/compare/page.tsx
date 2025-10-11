"use client"

import { useState } from "react"
import { useAISettings } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import Image from "next/image"
import { logos } from "@/lib/logos"
import {
  Send,
  RefreshCw,
  ChevronRight,
  DownloadIcon,
  User,
  Clock,
  MessageSquare,
  Hash,
  MessageCircle,
} from "lucide-react"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  latency?: number
  tokens?: number
}

interface Conversation {
  messages: Message[]
  totalLatency: number
  totalTokens: number
}

const availableModels = [
  { 
    id: "x-ai/grok-4", 
    name: "Grok 4", 
    provider: "xAI", 
    logoKey: "xai-logo.svg",
    description: "Modèle avancé d'xAI avec capacités de raisonnement exceptionnelles et créativité élevée"
  },
  { 
    id: "x-ai/grok-4-fast", 
    name: "Grok 4 Fast", 
    provider: "xAI", 
    logoKey: "xai-logo.svg",
    description: "Version rapide de Grok 4, optimisée pour la vitesse tout en maintenant une qualité élevée"
  },
  { 
    id: "openai/gpt-4o", 
    name: "GPT-4o", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Modèle multimodal avancé d'OpenAI avec capacités visuelles et textuelles exceptionnelles"
  },
  { 
    id: "openai/gpt-4o-mini", 
    name: "GPT-4o mini", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Version compacte et économique de GPT-4o, parfaite pour les tâches courantes"
  },
  { 
    id: "openai/gpt-5", 
    name: "GPT-5", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Dernière génération d'OpenAI avec des capacités de raisonnement et de créativité révolutionnaires"
  },
  { 
    id: "openai/gpt-5-mini", 
    name: "GPT-5 mini", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Version allégée de GPT-5, optimisée pour l'efficacité et la rapidité"
  },
  { 
    id: "anthropic/claude-3.5-sonnet", 
    name: "Claude 3.5 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Modèle équilibré d'Anthropic, excellent pour l'analyse et la génération de contenu de qualité"
  },
  { 
    id: "anthropic/claude-sonnet-4", 
    name: "Claude 4 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Modèle avancé d'Anthropic avec des capacités de raisonnement et de créativité supérieures"
  },
  { 
    id: "anthropic/claude-sonnet-4.5", 
    name: "Claude 4.5 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Dernière version de Claude avec des améliorations significatives en précision et créativité"
  },
  { 
    id: "google/gemini-2.5-flash", 
    name: "Gemini 2.5 Flash", 
    provider: "Google", 
    logoKey: "google-logo.svg",
    description: "Modèle ultra-rapide de Google, optimisé pour la vitesse et l'efficacité"
  },
  { 
    id: "google/gemini-2.5-pro", 
    name: "Gemini 2.5 Pro", 
    provider: "Google", 
    logoKey: "google-logo.svg",
    description: "Modèle professionnel de Google avec des capacités avancées et une précision exceptionnelle"
  },
]

// Fonction utilitaire pour générer un ID de session unique
const generateSessionId = () => {
  return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export default function ComparePage() {
  const { testAIResponse, settings } = useAISettings()
  const [input, setInput] = useState("")
  const [leftModel, setLeftModel] = useState("openai/gpt-4o")
  const [rightModel, setRightModel] = useState("anthropic/claude-3.5-haiku")
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(generateSessionId())
  
  const [conversations, setConversations] = useState<{
    left: Conversation
    right: Conversation
  }>({
    left: { messages: [], totalLatency: 0, totalTokens: 0 },
    right: { messages: [], totalLatency: 0, totalTokens: 0 }
  })

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    // Add user message to both conversations
    setConversations(prev => ({
      left: {
        ...prev.left,
        messages: [...prev.left.messages, userMessage]
      },
      right: {
        ...prev.right,
        messages: [...prev.right.messages, userMessage]
      }
    }))

    setInput("")
    setIsLoading(true)

    // Create test requests for both models using the current session ID
    const leftTestRequest = {
      thread_id: `${sessionId}-left`,
      message: input.trim(),
      settings: {
        system_prompt: settings?.system_prompt || "You are a helpful AI assistant.",
        ai_model: leftModel,
        temperature: settings?.temperature || 0.7,
        top_p: settings?.top_p || 1.0,
        lang: settings?.lang || "en",
        tone: settings?.tone || "friendly",
        is_active: true,
        doc_lang: settings?.doc_lang || []
      }
    }

    const rightTestRequest = {
      thread_id: `${sessionId}-right`,
      message: input.trim(),
      settings: {
        system_prompt: settings?.system_prompt || "You are a helpful AI assistant.",
        ai_model: rightModel,
        temperature: settings?.temperature || 0.7,
        top_p: settings?.top_p || 1.0,
        lang: settings?.lang || "en",
        tone: settings?.tone || "friendly",
        is_active: true,
        doc_lang: settings?.doc_lang || []
      }
    }

    // Test both models in parallel
    const [leftResponse, rightResponse] = await Promise.all([
      testAIResponse(leftTestRequest).catch(error => {
        console.error("Error with left model:", error)
        return { response: "Erreur lors de la génération de la réponse.", response_time: 0, confidence: 0 }
      }),
      testAIResponse(rightTestRequest).catch(error => {
        console.error("Error with right model:", error)
        return { response: "Erreur lors de la génération de la réponse.", response_time: 0, confidence: 0 }
      })
    ])

    // Add responses to conversations
    const leftMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: leftResponse.response,
      timestamp: new Date().toISOString(),
      latency: Math.round(leftResponse.response_time * 1000), // Convert to ms
      tokens: Math.floor(leftResponse.confidence * 100), // Approximate tokens from confidence
    }

    const rightMessage: Message = {
      id: (Date.now() + 2).toString(),
      role: "assistant",
      content: rightResponse.response,
      timestamp: new Date().toISOString(),
      latency: Math.round(rightResponse.response_time * 1000), // Convert to ms
      tokens: Math.floor(rightResponse.confidence * 100), // Approximate tokens from confidence
    }

    setConversations(prev => ({
      left: {
        messages: [...prev.left.messages, leftMessage],
        totalLatency: prev.left.totalLatency + leftMessage.latency!,
        totalTokens: prev.left.totalTokens + leftMessage.tokens!,
      },
      right: {
        messages: [...prev.right.messages, rightMessage],
        totalLatency: prev.right.totalLatency + rightMessage.latency!,
        totalTokens: prev.right.totalTokens + rightMessage.tokens!,
      }
    }))

    setIsLoading(false)
  }


  const handleReset = () => {
    // Générer un nouveau session ID pour une nouvelle session de comparaison
    setSessionId(generateSessionId())

    setConversations({
      left: { messages: [], totalLatency: 0, totalTokens: 0 },
      right: { messages: [], totalLatency: 0, totalTokens: 0 }
    })
  }

  const handleSwapModels = () => {
    const temp = leftModel
    setLeftModel(rightModel)
    setRightModel(temp)
  }

  const handleExport = () => {
    const exportData = {
      comparison: {
        leftModel,
        rightModel,
        timestamp: new Date().toISOString(),
      },
      conversations,
      metrics: {
        left: {
          avgLatency: conversations.left.messages.length > 0 
            ? Math.round(conversations.left.totalLatency / conversations.left.messages.filter(m => m.role === 'assistant').length)
            : 0,
          totalTokens: conversations.left.totalTokens,
        },
        right: {
          avgLatency: conversations.right.messages.length > 0 
            ? Math.round(conversations.right.totalLatency / conversations.right.messages.filter(m => m.role === 'assistant').length)
            : 0,
          totalTokens: conversations.right.totalTokens,
        }
      }
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `model-comparison-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getModelDisplayName = (modelId: string) => {
    return availableModels.find(m => m.id === modelId)?.name || modelId
  }

  const renderConversation = (conversation: Conversation, side: "left" | "right") => {
    const model = side === "left" ? leftModel : rightModel
    const avgLatency = conversation.messages.filter(m => m.role === 'assistant').length > 0
      ? Math.round(conversation.totalLatency / conversation.messages.filter(m => m.role === 'assistant').length)
      : 0

    return (
      <div className="flex-1 flex flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {conversation.messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-primary" />
                </div>
              )}
              
              <div className={`max-w-[80%] space-y-1`}>
                <div
                  className={`px-4 py-3 rounded-lg ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground ml-auto"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                </div>
                <div className={`flex items-center gap-2 text-xs text-muted-foreground ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}>
                  <span>{formatTime(message.timestamp)}</span>
                  {message.latency && (
                    <>
                      <Clock className="w-3 h-3" />
                      <span>{message.latency}ms</span>
                    </>
                  )}
                  {message.tokens && (
                    <>
                      <Hash className="w-3 h-3" />
                      <span>{message.tokens} tokens</span>
                    </>
                  )}
                </div>
              </div>

              {message.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-secondary-foreground" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <User className="w-4 h-4 text-primary" />
              </div>
              <div className="bg-muted px-4 py-3 rounded-lg">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Performance Metrics */}
        <div className="border-t p-4 bg-muted/30">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-center">
              <div className="font-medium">{avgLatency}ms</div>
              <div className="text-muted-foreground">Avg Latency</div>
            </div>
            <div className="text-center">
              <div className="font-medium">{conversation.totalTokens}</div>
              <div className="text-muted-foreground">Total Tokens</div>
            </div>
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
          <h1 className="text-3xl font-bold tracking-tight">Model Comparison</h1>
          <p className="text-muted-foreground">
            Compare AI models side by side to find the best fit for your use case
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button variant="outline" onClick={handleSwapModels}>
            <ChevronRight className="w-4 h-4 mr-2" />
            Swap
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <DownloadIcon className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Model Selection */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Model A (Left)</label>
              <Select value={leftModel} onValueChange={setLeftModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.filter(m => m.id !== rightModel).map((model) => (
                    <SelectItem 
                      key={model.id} 
                      value={model.id}
                      title={model.description}
                      className="cursor-pointer hover:bg-accent"
                    >
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
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Model B (Right)</label>
              <Select value={rightModel} onValueChange={setRightModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.filter(m => m.id !== leftModel).map((model) => (
                    <SelectItem 
                      key={model.id} 
                      value={model.id}
                      title={model.description}
                      className="cursor-pointer hover:bg-accent"
                    >
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
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Comparison Interface */}
      <div className="grid grid-cols-2 gap-4 h-[500px]">
        {/* Left Model */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              {getModelDisplayName(leftModel)}
              <Badge variant="secondary">Model A</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            {renderConversation(conversations.left, "left")}
          </CardContent>
        </Card>

        {/* Right Model */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              {getModelDisplayName(rightModel)}
              <Badge variant="secondary">Model B</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            {renderConversation(conversations.right, "right")}
          </CardContent>
        </Card>
      </div>

      {/* Shared Input */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Textarea
              value={input}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
              placeholder="Enter your message to test both models..."
              className="flex-1 min-h-[60px]"
              onKeyPress={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              disabled={isLoading}
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={!input.trim() || isLoading}
              size="lg"
            >
              {isLoading ? (
                <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}