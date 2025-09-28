"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { MessageSquare, Search, Edit3, Trash2, Clock, User, Bot, CheckCircle, AlertCircle } from "lucide-react"

// Mock data for conversations
const mockConversations = [
  {
    id: "1",
    contact: "john.doe@example.com",
    lastMessage: "Thank you for your help!",
    channel: "Web",
    sentiment: "positive",
    topic: "Support",
    date: "2024-01-15T10:30:00Z",
    duration: "5m 32s",
    messageCount: 8,
    status: "closed",
    messages: [
      { id: "1", role: "user", content: "I need help with my account", timestamp: "2024-01-15T10:25:00Z" },
      {
        id: "2",
        role: "assistant",
        content: "I'd be happy to help you with your account. What specific issue are you experiencing?",
        timestamp: "2024-01-15T10:25:30Z",
        confidence: 0.95,
        edited: false,
      },
      { id: "3", role: "user", content: "I can't log in", timestamp: "2024-01-15T10:26:00Z" },
      {
        id: "4",
        role: "assistant",
        content: "Let me help you troubleshoot the login issue. Can you try resetting your password?",
        timestamp: "2024-01-15T10:26:15Z",
        confidence: 0.88,
        edited: true,
        editedBy: "Admin",
        editedAt: "2024-01-15T10:27:00Z",
      },
    ],
  },
  {
    id: "2",
    contact: "sarah.wilson@company.com",
    lastMessage: "Is this feature available?",
    channel: "WhatsApp",
    sentiment: "neutral",
    topic: "Product Inquiry",
    date: "2024-01-15T09:15:00Z",
    duration: "3m 45s",
    messageCount: 5,
    status: "open",
    messages: [
      { id: "1", role: "user", content: "Is this feature available?", timestamp: "2024-01-15T09:15:00Z" },
      {
        id: "2",
        role: "assistant",
        content: "Yes, this feature is available in our Pro plan. Would you like to know more about it?",
        timestamp: "2024-01-15T09:15:30Z",
        confidence: 0.92,
        edited: false,
      },
    ],
  },
  {
    id: "3",
    contact: "mike.johnson@startup.io",
    lastMessage: "This doesn't work as expected",
    channel: "Instagram",
    sentiment: "negative",
    topic: "Bug Report",
    date: "2024-01-15T08:45:00Z",
    duration: "12m 18s",
    messageCount: 15,
    status: "open",
    messages: [
      { id: "1", role: "user", content: "This doesn't work as expected", timestamp: "2024-01-15T08:45:00Z" },
      {
        id: "2",
        role: "assistant",
        content: "I understand your frustration. Let me help you resolve this issue step by step.",
        timestamp: "2024-01-15T08:45:45Z",
        confidence: 0.85,
        edited: false,
      },
    ],
  },
]

export default function ActivityChatPage() {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [channelFilter, setChannelFilter] = useState("all")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sentimentFilter, setSentimentFilter] = useState("all")
  const [editingMessage, setEditingMessage] = useState<string | null>(null)
  const [editContent, setEditContent] = useState("")
  const [conversationAutoReply, setConversationAutoReply] = useState<{ [key: string]: boolean }>({
    "1": true,
    "2": true,
    "3": false,
  })

  const filteredConversations = mockConversations.filter((conv) => {
    const matchesSearch =
      conv.contact.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conv.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesChannel = channelFilter === "all" || conv.channel.toLowerCase() === channelFilter
    const matchesStatus = statusFilter === "all" || conv.status === statusFilter
    const matchesSentiment = sentimentFilter === "all" || conv.sentiment === sentimentFilter

    return matchesSearch && matchesChannel && matchesStatus && matchesSentiment
  })

  const selectedConv = mockConversations.find((conv) => conv.id === selectedConversation)

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive":
        return "bg-green-500/20 text-green-400"
      case "negative":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-yellow-500/20 text-yellow-400"
    }
  }

  const getChannelColor = (channel: string) => {
    switch (channel.toLowerCase()) {
      case "web":
        return "bg-blue-500/20 text-blue-400"
      case "whatsapp":
        return "bg-green-500/20 text-green-400"
      case "instagram":
        return "bg-pink-500/20 text-pink-400"
      case "x":
        return "bg-gray-500/20 text-gray-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const handleEditMessage = (messageId: string, currentContent: string) => {
    setEditingMessage(messageId)
    setEditContent(currentContent)
  }

  const handleSaveEdit = () => {
    // In a real app, this would save to the backend and create FAQ entry
    console.log("Saving edit:", editContent)
    setEditingMessage(null)
    setEditContent("")
    // Show success toast and link to FAQ
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 flex">
          {/* Conversations List */}
          <div className="w-96 border-r border-border flex flex-col">
            {/* Filters */}
            <div className="p-4 border-b border-border space-y-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search conversations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              <div className="flex gap-2">
                <Select value={channelFilter} onValueChange={setChannelFilter}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Channel" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Channels</SelectItem>
                    <SelectItem value="web">Web</SelectItem>
                    <SelectItem value="whatsapp">WhatsApp</SelectItem>
                    <SelectItem value="instagram">Instagram</SelectItem>
                    <SelectItem value="x">X</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="open">Open</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="Sentiment" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sentiments</SelectItem>
                  <SelectItem value="positive">Positive</SelectItem>
                  <SelectItem value="neutral">Neutral</SelectItem>
                  <SelectItem value="negative">Negative</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Conversations */}
            <div className="flex-1 overflow-y-auto">
              {filteredConversations.length === 0 ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No conversations found</p>
                    <p className="text-sm">Try adjusting your filters or check back later for new conversations.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {filteredConversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      onClick={() => setSelectedConversation(conversation.id)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedConversation === conversation.id
                          ? "bg-primary/20 border border-primary/30"
                          : "hover:bg-muted/50"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4 text-muted-foreground" />
                          <span className="font-medium text-sm">{conversation.contact}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Badge variant="outline" className={getChannelColor(conversation.channel)}>
                            {conversation.channel}
                          </Badge>
                          {conversation.status === "open" ? (
                            <AlertCircle className="w-3 h-3 text-yellow-400" />
                          ) : (
                            <CheckCircle className="w-3 h-3 text-green-400" />
                          )}
                        </div>
                      </div>

                      <p className="text-sm text-muted-foreground mb-2 line-clamp-2">{conversation.lastMessage}</p>

                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className={getSentimentColor(conversation.sentiment)}>
                            {conversation.sentiment}
                          </Badge>
                          <span>{conversation.topic}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3" />
                          <span>{conversation.duration}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Conversation Detail */}
          <div className="flex-1 flex flex-col">
            {selectedConv ? (
              <>
                {/* Conversation Header */}
                <div className="p-4 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <User className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <h2 className="font-semibold">{selectedConv.contact}</h2>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="outline" className={getChannelColor(selectedConv.channel)}>
                            {selectedConv.channel}
                          </Badge>
                          <Badge variant="outline" className={getSentimentColor(selectedConv.sentiment)}>
                            {selectedConv.sentiment}
                          </Badge>
                          <span>{selectedConv.topic}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-2">
                        <Label className="text-sm">Auto-reply</Label>
                        <Switch
                          checked={conversationAutoReply[selectedConv.id] || false}
                          onCheckedChange={(checked) =>
                            setConversationAutoReply((prev) => ({
                              ...prev,
                              [selectedConv.id]: checked,
                            }))
                          }
                        />
                      </div>
                      <Button variant="outline" size="sm">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {selectedConv.messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div className="max-w-[70%] space-y-2">
                        <div
                          className={`p-3 rounded-lg ${
                            message.role === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              {message.content}
                              {message.role === "assistant" && message.confidence && (
                                <div className="text-xs mt-2 opacity-70">
                                  Confidence: {Math.round(message.confidence * 100)}%
                                </div>
                              )}
                            </div>
                            {message.role === "assistant" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditMessage(message.id, message.content)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                              >
                                <Edit3 className="w-3 h-3" />
                              </Button>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          {message.role === "assistant" ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />}
                          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                          {message.edited && (
                            <span className="text-yellow-400">
                              Edited by {message.editedBy} at {new Date(message.editedAt!).toLocaleTimeString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-semibold mb-2">Select a conversation</h3>
                  <p>Choose a conversation from the list to view its details and messages.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Message Dialog */}
      <Dialog open={!!editingMessage} onOpenChange={() => setEditingMessage(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit AI Response</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              placeholder="Edit the AI response..."
              className="min-h-[120px]"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setEditingMessage(null)}>
                Cancel
              </Button>
              <Button onClick={handleSaveEdit}>Save & Add to FAQ</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
