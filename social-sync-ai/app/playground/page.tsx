"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, RefreshCw } from "lucide-react"
import Link from "next/link"

export default function PlaygroundPage() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string; timestamp: string }>>([
    {
      role: "assistant",
      content: "Hi! What can I help you with?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ])
  const [input, setInput] = useState("")
  const [model, setModel] = useState("gpt-4o")
  const [temperature, setTemperature] = useState([0])
  const [systemInstruction, setSystemInstruction] = useState(`### Role
- Primary Function: You are an AI chatbot who helps users with their inquiries, issues and requests. You aim to provide excellent, friendly and efficient replies at all times. Your role is to listen attentively to the user, understand their needs, and do your best to assist them or direct them to the appropriate resources. If a question is not clear, ask clarifying questions. Make sure to end your replies with a positive note.`)
  const [agentStatus, setAgentStatus] = useState("trained")

  const handleSend = () => {
    if (!input.trim()) return

    const newMessages = [
      ...messages,
      {
        role: "user",
        content: input,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]
    setMessages(newMessages)
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "This is a simulated response from the AI model. In a real implementation, this would connect to your chosen AI model.",
          timestamp: new Date().toLocaleTimeString(),
        },
      ])
    }, 1000)
  }

  const saveToAgent = () => {
    console.log("Saving configuration to agent...")
    // In real implementation, this would save the current settings
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 flex">
          {/* Left Configuration Panel */}
          <div className="w-96 border-r border-border p-6 space-y-6 overflow-y-auto">
            {/* Agent Status */}
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Agent status:</span>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <Badge variant="outline" className="bg-green-500/20 text-green-400 capitalize">
                    {agentStatus}
                  </Badge>
                </div>
              </div>

              <Button onClick={saveToAgent} className="w-full bg-gray-600 hover:bg-gray-700">
                Save to agent
              </Button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border">
              <button className="px-4 py-2 text-sm font-medium border-b-2 border-primary text-primary">
                Configure & test agents
              </button>
              <Link href="/playground/compare">
                <button className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground">
                  Compare
                </button>
              </Link>
            </div>

            {/* Model */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Model</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger className="w-full">
                  <div className="flex items-center gap-2">
                    <Bot className="w-4 h-4" />
                    <SelectValue />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                  <SelectItem value="claude-3">Claude 3</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Temperature */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Temperature</Label>
              <div className="px-3">
                <Slider
                  value={temperature}
                  onValueChange={setTemperature}
                  max={2}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>Reserved</span>
                  <span className="font-medium">{temperature[0]}</span>
                  <span>Creative</span>
                </div>
              </div>
            </div>

            {/* AI Actions */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">AI Actions</Label>
              <Card>
                <CardContent className="p-4 text-center text-muted-foreground">
                  <p className="text-sm">No actions found</p>
                </CardContent>
              </Card>
            </div>

            {/* Instructions */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Instructions (System prompt)</Label>
              <Select defaultValue="base">
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="base">Base instructions</SelectItem>
                  <SelectItem value="custom">Custom instructions</SelectItem>
                </SelectContent>
              </Select>

              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Instructions</Label>
                <Textarea
                  value={systemInstruction}
                  onChange={(e) => setSystemInstruction(e.target.value)}
                  className="min-h-[200px] text-sm font-mono resize-none"
                  placeholder="Enter system instructions..."
                />
              </div>
            </div>
          </div>

          {/* Right Chat Panel */}
          <div className="flex-1 flex flex-col">
            {/* Chat Header */}
            <div className="p-4 border-b border-border">
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">Agent 9/27/2025, 9:02:30 AM</div>
                <Button variant="ghost" size="sm">
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 p-6 space-y-4 overflow-y-auto">
              {messages.map((message, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {message.role === "assistant" ? (
                      <>
                        <Bot className="w-3 h-3" />
                        <span>Agent 9/27/2025, {message.timestamp}</span>
                      </>
                    ) : (
                      <>
                        <User className="w-3 h-3" />
                        <span>User</span>
                      </>
                    )}
                  </div>
                  <div
                    className={`p-3 rounded-lg max-w-[80%] ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground ml-auto"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <div className="p-4 border-t border-border">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <span>Powered by Chatbase</span>
              </div>
              <div className="flex gap-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Message..."
                  className="flex-1"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                />
                <Button onClick={handleSend} size="sm">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
