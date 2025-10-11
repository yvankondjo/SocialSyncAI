"use client"

import { useState, useEffect } from "react"
import { useAISettings } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Image from "next/image"
import { logos } from "@/lib/logos"
import {
  Settings as Cog,
  Send,
  Bot,
  User,
  RefreshCw,
  Save,
  ChevronUp as CompareIcon,
  BarChart3,
} from "lucide-react"
import Link from "next/link"
import { ApiClient } from "@/lib/api"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  confidence?: number
}

const availableModels = [
  { 
    id: "x-ai/grok-4", 
    name: "Grok 4", 
    provider: "xAI", 
    logoKey: "xai-logo.svg",
    description: "Advanced xAI model with exceptional reasoning and creativity capabilities"
  },
  { 
    id: "x-ai/grok-4-fast", 
    name: "Grok 4 Fast", 
    provider: "xAI", 
    logoKey: "xai-logo.svg",
    description: "Fast version of Grok 4, optimized for speed while maintaining high quality"
  },
  { 
    id: "openai/gpt-4o", 
    name: "GPT-4o", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Advanced multimodal OpenAI model with exceptional visual and text capabilities"
  },
  { 
    id: "openai/gpt-4o-mini", 
    name: "GPT-4o mini", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Compact and economical GPT-4o, perfect for common tasks"
  },
  { 
    id: "openai/gpt-5", 
    name: "GPT-5", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Latest generation of OpenAI with revolutionary reasoning and creativity capabilities"
  },
  { 
    id: "openai/gpt-5-mini", 
    name: "GPT-5 mini", 
    provider: "OpenAI", 
    logoKey: "openai-logo.svg",
    description: "Lightweight version of GPT-5, optimized for efficiency and speed"
  },
  { 
    id: "anthropic/claude-3.5-sonnet", 
    name: "Claude 3.5 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Balanced Anthropic model, excellent for analysis and content generation"
  },
  { 
    id: "anthropic/claude-sonnet-4", 
    name: "Claude 4 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Advanced Anthropic model with superior reasoning and creativity capabilities"
  },
  { 
    id: "anthropic/claude-sonnet-4.5", 
    name: "Claude 4.5 Sonnet", 
    provider: "Anthropic", 
    logoKey: "claude-logo.svg",
    description: "Latest version of Claude with significant improvements in precision and creativity"
  },
  { 
    id: "google/gemini-2.5-flash", 
    name: "Gemini 2.5 Flash", 
    provider: "Google", 
    logoKey: "google-logo.svg",
    description: "Ultra-fast Google model, optimized for speed and efficiency"
  },
  { 
    id: "google/gemini-2.5-pro", 
    name: "Gemini 2.5 Pro", 
    provider: "Google", 
    logoKey: "google-logo.svg",
    description: "Professional Google model with advanced capabilities and exceptional precision"
  },
]

// Instruction templates
const INSTRUCTION_TEMPLATES = {
  general: {
    name: "General Assistant",
    instructions: `You are a helpful AI assistant. Provide accurate, concise, and friendly responses to user questions. Always be polite and professional.`
  },
  creative: {
    name: "Creative Writer",
    instructions: `You are a creative writing assistant. Help users with creative writing tasks, brainstorming ideas, developing characters, and crafting engaging stories. Be imaginative and encouraging.`
  },
  technical: {
    name: "Technical Expert",
    instructions: `You are a technical expert assistant. Provide detailed, accurate technical information, code examples, and best practices. Explain complex concepts clearly and thoroughly.`
  },
  business: {
    name: "Business Consultant",
    instructions: `You are a business consultant assistant. Help with business strategy, marketing advice, financial planning, and operational improvements. Provide practical, actionable insights.`
  },
  educational: {
    name: "Educational Tutor",
    instructions: `You are an educational tutor assistant. Help students learn by explaining concepts clearly, providing examples, and guiding them through problem-solving processes. Be patient and encouraging.`
  }
}

export default function PlaygroundPage() {
  const { testAIResponse, settings } = useAISettings()

  // Utiliser un thread_id constant pour la session playground
  const [playgroundThreadId, setPlaygroundThreadId] = useState(() => `playground-session-${Date.now()}`)

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?",
      timestamp: new Date().toISOString(),
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  // Configuration state - use settings from API if available, otherwise defaults
  const [model, setModel] = useState(settings?.ai_model || "openai/gpt-4o")
  const [temperature, setTemperature] = useState([settings?.temperature || 0.7])
  const [systemInstruction, setSystemInstruction] = useState(
    settings?.system_prompt || "You are a helpful AI assistant. Provide accurate and concise answers to user questions."
  )
  const [agentStatus, setAgentStatus] = useState("trained")

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const testRequest = {
        thread_id: playgroundThreadId,
        message: input.trim(),
        settings: {
          system_prompt: systemInstruction,
          ai_model: model,
          temperature: temperature[0],
          top_p: 1.0,
          lang: "en",
          tone: "friendly",
          is_active: true,
          doc_lang: []
        }
      }

      const response = await testAIResponse(testRequest)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date().toISOString(),
        confidence: response.confidence,
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error("Error testing AI response:", error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Désolé, une erreur s'est produite lors de la génération de la réponse. Veuillez réessayer.",
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  // Synchroniser les états locaux avec les settings de l'API
  useEffect(() => {
    if (settings) {
      setModel(settings.ai_model)
      setTemperature([settings.temperature])
      setSystemInstruction(settings.system_prompt)
    }
  }, [settings])

  const handleRefreshChat = () => {
    // Générer un nouveau thread_id pour une nouvelle conversation
    const newThreadId = `playground-session-${Date.now()}`
    setPlaygroundThreadId(newThreadId)

    setMessages([
      {
        id: "1",
        role: "assistant",
        content: "Hello! I'm your AI assistant. How can I help you today?",
        timestamp: new Date().toISOString(),
      }
    ])
  }

  const handleSaveToAgent = () => {
    // Simulate saving configuration to agent
    console.log("Saving configuration to agent:", {
      model,
      temperature: temperature[0],
      systemInstruction,
    })
    // Toast notification would be shown here
  }

  const loadInstructionTemplate = (templateKey: keyof typeof INSTRUCTION_TEMPLATES) => {
    setSystemInstruction(INSTRUCTION_TEMPLATES[templateKey].instructions)
  }

  const getTemperatureLabel = (value: number) => {
    if (value <= 0.3) return "Precise"
    if (value <= 0.7) return "Balanced"
    if (value <= 1.2) return "Creative"
    return "Very Creative"
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="flex-1 p-3 sm:p-4 lg:p-6">
      <div className="flex flex-col lg:flex-row h-[calc(100vh-120px)] gap-3 sm:gap-4 lg:gap-6">
        {/* Configuration Panel */}
        <div className="w-full lg:w-96 space-y-3 sm:space-y-4">
          {/* Agent Status */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Cog className="w-5 h-5" />
                  <span className="font-medium">Agent Status</span>
                </div>
                <Badge variant="secondary" className="bg-green-500/20 text-green-400">
                  {agentStatus}
                </Badge>
              </div>
              <Button onClick={handleSaveToAgent} className="w-full">
                <Save className="w-4 h-4 mr-2" />
                Save to Agent
              </Button>
            </CardContent>
          </Card>

          {/* Navigation Tabs */}
          <Tabs defaultValue="configure">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="configure">Configure & Test</TabsTrigger>
              <TabsTrigger value="compare">
                <Link href="/dashboard/playground/compare" className="flex items-center gap-2">
                  <CompareIcon className="w-4 h-4" />
                  Compare
                </Link>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="configure" className="space-y-4">
              {/* Model Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Model Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Model</Label>
                    <Select value={model} onValueChange={setModel}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {availableModels.map((m) => (
                          <SelectItem 
                            key={m.id} 
                            value={m.id}
                            title={m.description}
                            className="cursor-pointer hover:bg-accent"
                          >
                            <div className="flex items-center justify-between w-full gap-3">
                              <div className="flex items-center gap-3">
                                {m.logoKey && logos[m.logoKey as keyof typeof logos] && (
                                  <div className="relative w-6 h-6 flex-shrink-0">
                                    <Image
                                      src={logos[m.logoKey as keyof typeof logos]}
                                      alt={`${m.provider} logo`}
                                      width={24}
                                      height={24}
                                      className="object-contain"
                                    />
                                  </div>
                                )}
                                <div className="flex-1 min-w-0">
                                  <div className="font-medium truncate">{m.name}</div>
                                  <div className="text-xs text-muted-foreground truncate">{m.provider}</div>
                                </div>
                              </div>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Label>Temperature</Label>
                      <Badge variant="outline">{getTemperatureLabel(temperature[0])}</Badge>
                    </div>
                    <Slider
                      value={temperature}
                      onValueChange={setTemperature}
                      max={2}
                      min={0}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Precise</span>
                      <span>{temperature[0]}</span>
                      <span>Creative</span>
                    </div>
                  </div>

                </CardContent>
              </Card>


              {/* Instructions */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Instructions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>System Prompt</Label>
                      <Select onValueChange={(value: string) => loadInstructionTemplate(value as keyof typeof INSTRUCTION_TEMPLATES)}>
                        <SelectTrigger className="w-48">
                          <SelectValue placeholder="Load template" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(INSTRUCTION_TEMPLATES).map(([key, template]) => (
                            <SelectItem key={key} value={key}>
                              {template.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <Textarea
                      value={systemInstruction}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setSystemInstruction(e.target.value)}
                      placeholder="Enter system instructions..."
                      className="min-h-[120px]"
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 flex flex-col min-h-[400px] lg:min-h-0">
          <Card className="flex-1 flex flex-col">
            {/* Chat Header */}
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Bot className="w-5 h-5" />
                    Playground Chat
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Test your AI configuration in real-time
                  </p>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{formatTime(new Date().toISOString())}</span>
                  <Button variant="outline" size="sm" onClick={handleRefreshChat}>
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 space-y-4 overflow-y-auto mb-4">
                {messages.map((message) => (
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

                    <div className={`max-w-[70%] space-y-1`}>
                      <div
                        className={`px-4 py-3 rounded-lg ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground ml-auto"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{message.content}</p>
                      </div>
                      <div className={`text-xs text-muted-foreground ${
                        message.role === "user" ? "text-right" : "text-left"
                      }`}>
                        <div className="flex items-center gap-2">
                          <span>{formatTime(message.timestamp)}</span>
                          {message.role === "assistant" && message.confidence !== undefined && (
                            <Badge variant="outline" className="text-xs px-2 py-0.5">
                              <BarChart3 className="w-3 h-3 mr-1" />
                              {(message.confidence * 100).toFixed(0)}%
                            </Badge>
                          )}
                        </div>
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
                      <Cog className="w-4 h-4 text-primary" />
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

              {/* Input */}
              <div className="flex items-center gap-2 pt-4 border-t">
                <Input
                  value={input}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1"
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => {
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
                  size="sm"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>

              {/* Branding */}
              <div className="text-center mt-4">
                <p className="text-xs text-muted-foreground">
                  Powered by <span className="font-medium">ConversAI</span>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
