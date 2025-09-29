"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Settings,
  Send,
  Settings as BotIcon,
  User,
  RotateCcw,
  Save,
  ChevronUp as CompareIcon,
} from "lucide-react"
import Link from "next/link"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

const availableModels = [
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4", name: "GPT-4", provider: "OpenAI" },
  { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", provider: "OpenAI" },
  { id: "gemini-pro", name: "Gemini Pro", provider: "Google" },
  { id: "claude-3", name: "Claude 3", provider: "Anthropic" },
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

  // Configuration state
  const [model, setModel] = useState("gpt-4o")
  const [temperature, setTemperature] = useState([0.7])
  const [systemInstruction, setSystemInstruction] = useState(
    "You are a helpful AI assistant. Provide accurate and concise answers to user questions."
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

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateMockResponse(input.trim()),
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, aiMessage])
      setIsLoading(false)
    }, 1500)
  }

  const generateMockResponse = (userInput: string): string => {
    const responses = [
      "I understand your question. Based on the information provided, here's what I can tell you...",
      "That's a great question! Let me break this down for you step by step.",
      "I'd be happy to help you with that. Here's my analysis of the situation...",
      "Thanks for asking! From my understanding, the best approach would be...",
      "I can see why you're asking about this. Let me provide you with some insights...",
    ]
    return responses[Math.floor(Math.random() * responses.length)]
  }

  const handleRefreshChat = () => {
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
    <div className="flex-1 p-6">
      <div className="flex h-[calc(100vh-120px)] gap-6">
        {/* Configuration Panel */}
        <div className="w-96 space-y-4">
          {/* Agent Status */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Settings className="w-5 h-5" />
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
                          <SelectItem key={m.id} value={m.id}>
                            <div className="font-medium">{m.name}</div>
                            <div className="text-xs text-muted-foreground">{m.provider}</div>
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
        <div className="flex-1 flex flex-col">
          <Card className="flex-1 flex flex-col">
            {/* Chat Header */}
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <BotIcon className="w-5 h-5" />
                    Playground Chat
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    Test your AI configuration in real-time
                  </p>
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{formatTime(new Date().toISOString())}</span>
                  <Button variant="outline" size="sm" onClick={handleRefreshChat}>
                    <RotateCcw className="w-4 h-4" />
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
                        {formatTime(message.timestamp)}
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
                      <Settings className="w-4 h-4 text-primary" />
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
                  Powered by <span className="font-medium">SocialSync AI</span>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
