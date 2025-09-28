"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Send, RotateCcw, ArrowLeftRight, Download } from "lucide-react"

export default function ComparePage() {
  const [input, setInput] = useState("")
  const [leftModel, setLeftModel] = useState("gpt-4o")
  const [rightModel, setRightModel] = useState("gemini-pro")
  const [conversations, setConversations] = useState<{
    left: Array<{ role: string; content: string; latency?: number; tokens?: number }>
    right: Array<{ role: string; content: string; latency?: number; tokens?: number }>
  }>({ left: [], right: [] })

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage = { role: "user", content: input }
    const newConversations = {
      left: [...conversations.left, userMessage],
      right: [...conversations.right, userMessage],
    }
    setConversations(newConversations)
    setInput("")

    // Simulate AI responses with different latencies
    setTimeout(
      () => {
        setConversations((prev) => ({
          ...prev,
          left: [
            ...prev.left,
            {
              role: "assistant",
              content: `Response from ${leftModel}: This is a simulated response with different characteristics.`,
              latency: Math.floor(Math.random() * 2000) + 500,
              tokens: Math.floor(Math.random() * 200) + 50,
            },
          ],
        }))
      },
      Math.random() * 1000 + 500,
    )

    setTimeout(
      () => {
        setConversations((prev) => ({
          ...prev,
          right: [
            ...prev.right,
            {
              role: "assistant",
              content: `Response from ${rightModel}: This is another simulated response with different approach and style.`,
              latency: Math.floor(Math.random() * 2000) + 500,
              tokens: Math.floor(Math.random() * 200) + 50,
            },
          ],
        }))
      },
      Math.random() * 1000 + 500,
    )
  }

  const resetChats = () => {
    setConversations({ left: [], right: [] })
  }

  const swapModels = () => {
    const temp = leftModel
    setLeftModel(rightModel)
    setRightModel(temp)
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 flex flex-col gap-6 p-6">
          {/* Controls */}
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Model Comparison</h1>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={resetChats}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
              <Button variant="outline" size="sm" onClick={swapModels}>
                <ArrowLeftRight className="w-4 h-4 mr-2" />
                Swap
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>

          {/* Model Selection */}
          <div className="flex gap-4">
            <div className="flex-1">
              <Select value={leftModel} onValueChange={setLeftModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                  <SelectItem value="claude-3">Claude 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <Select value={rightModel} onValueChange={setRightModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                  <SelectItem value="gpt-4">GPT-4</SelectItem>
                  <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
                  <SelectItem value="claude-3">Claude 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Comparison Panels */}
          <div className="flex-1 flex gap-6">
            {/* Left Model */}
            <Card className="flex-1 flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    {leftModel}
                  </span>
                  <Badge variant="outline">Model A</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto min-h-0">
                  {conversations.left.map((message, index) => (
                    <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <div>{message.content}</div>
                        {message.latency && (
                          <div className="text-xs mt-2 opacity-70">
                            {message.latency}ms • {message.tokens} tokens
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Right Model */}
            <Card className="flex-1 flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    {rightModel}
                  </span>
                  <Badge variant="outline">Model B</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <div className="flex-1 space-y-4 overflow-y-auto min-h-0">
                  {conversations.right.map((message, index) => (
                    <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          message.role === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground"
                        }`}
                      >
                        <div>{message.content}</div>
                        {message.latency && (
                          <div className="text-xs mt-2 opacity-70">
                            {message.latency}ms • {message.tokens} tokens
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter a message to compare both models..."
              className="flex-1 min-h-[60px] resize-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
            />
            <Button onClick={handleSend} className="self-end">
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
