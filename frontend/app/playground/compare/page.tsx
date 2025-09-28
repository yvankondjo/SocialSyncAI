"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  MessageSquare,
  Send,
  RotateCcw,
  ArrowLeftRight,
  Download,
  Bot,
  User,
  Clock,
  Hash,
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
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4", name: "GPT-4", provider: "OpenAI" },
  { id: "gpt-3.5-turbo", name: "GPT-3.5 Turbo", provider: "OpenAI" },
  { id: "gemini-pro", name: "Gemini Pro", provider: "Google" },
  { id: "claude-3", name: "Claude 3", provider: "Anthropic" },
]

export default function ComparePage() {
  const [input, setInput] = useState("")
  const [leftModel, setLeftModel] = useState("gpt-4o")
  const [rightModel, setRightModel] = useState("gpt-3.5-turbo")
  const [isLoading, setIsLoading] = useState(false)
  
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

    // Simulate responses from both models with different latencies
    const leftLatency = Math.random() * 2000 + 500 // 500-2500ms
    const rightLatency = Math.random() * 2000 + 500

    const leftTokens = Math.floor(Math.random() * 100) + 50
    const rightTokens = Math.floor(Math.random() * 100) + 50

    setTimeout(() => {
      const leftResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: generateMockResponse(input.trim(), leftModel),
        timestamp: new Date().toISOString(),
        latency: Math.round(leftLatency),
        tokens: leftTokens,
      }

      setConversations(prev => ({
        ...prev,
        left: {
          messages: [...prev.left.messages, leftResponse],
          totalLatency: prev.left.totalLatency + leftLatency,
          totalTokens: prev.left.totalTokens + leftTokens,
        }
      }))
    }, leftLatency)

    setTimeout(() => {
      const rightResponse: Message = {
        id: (Date.now() + 2).toString(),
        role: "assistant",
        content: generateMockResponse(input.trim(), rightModel),
        timestamp: new Date().toISOString(),
        latency: Math.round(rightLatency),
        tokens: rightTokens,
      }

      setConversations(prev => ({
        ...prev,
        right: {
          messages: [...prev.right.messages, rightResponse],
          totalLatency: prev.right.totalLatency + rightLatency,
          totalTokens: prev.right.totalTokens + rightTokens,
        }
      }))

      setIsLoading(false)
    }, rightLatency)
  }

  const generateMockResponse = (userInput: string, model: string): string => {
    const responses = {
      "gpt-4o": [
        "As GPT-4o, I can provide you with a comprehensive analysis. Based on your question, here's my detailed response with advanced reasoning...",
        "I understand your query completely. Let me break this down systematically with multiple perspectives...",
        "This is an interesting question that requires careful consideration. Here's my thorough analysis...",
      ],
      "gpt-3.5-turbo": [
        "Thanks for your question! Here's a quick and efficient response to help you...",
        "I can help with that. Here's a straightforward answer based on the information provided...",
        "That's a good question. Let me give you a clear and concise response...",
      ],
      "gemini-pro": [
        "As Gemini Pro, I'll analyze this from multiple angles. Here's my comprehensive response...",
        "I can help you with that. Let me provide you with a well-structured answer...",
        "That's an interesting question. Here's my analysis with supporting details...",
      ],
      "claude-3": [
        "I appreciate your question. As Claude, I'll provide a thoughtful and nuanced response...",
        "Thank you for asking. Let me give you a careful and detailed analysis...",
        "That's a thoughtful question. Here's my considered response with multiple viewpoints...",
      ],
      "gpt-4": [
        "As GPT-4, I'll provide you with a detailed and well-reasoned response to your query...",
        "I understand what you're asking. Let me give you a comprehensive answer...",
        "That's a great question. Here's my thorough analysis of the situation...",
      ]
    }

    const modelResponses = responses[model as keyof typeof responses] || responses["gpt-3.5-turbo"]
    return modelResponses[Math.floor(Math.random() * modelResponses.length)]
  }

  const handleReset = () => {
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
                  <Bot className="w-4 h-4 text-primary" />
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
                <Bot className="w-4 h-4 text-primary" />
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
              <div className="font-medium text-lg">{avgLatency}ms</div>
              <div className="text-muted-foreground">Avg Latency</div>
            </div>
            <div className="text-center">
              <div className="font-medium text-lg">{conversation.totalTokens}</div>
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
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button variant="outline" onClick={handleSwapModels}>
            <ArrowLeftRight className="w-4 h-4 mr-2" />
            Swap
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Model Selection */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Model A (Left)</label>
              <Select value={leftModel} onValueChange={setLeftModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.filter(m => m.id !== rightModel).map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div>
                        <div className="font-medium">{model.name}</div>
                        <div className="text-xs text-muted-foreground">{model.provider}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Model B (Right)</label>
              <Select value={rightModel} onValueChange={setRightModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.filter(m => m.id !== leftModel).map((model) => (
                    <SelectItem key={model.id} value={model.id}>
                      <div>
                        <div className="font-medium">{model.name}</div>
                        <div className="text-xs text-muted-foreground">{model.provider}</div>
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
      <div className="grid grid-cols-2 gap-4 h-[600px]">
        {/* Left Model */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
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
              <MessageSquare className="w-5 h-5" />
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
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter your message to test both models..."
              className="flex-1 min-h-[80px]"
              onKeyPress={(e) => {
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