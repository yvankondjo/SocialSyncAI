"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { ConversationsService, type Conversation, type Message } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Switch } from "@/components/ui/switch"
import {
  Search,
  Send,
  Bot,
  User,
  ChevronDown,
  ChevronRight,
  Copy,
  StickyNote,
  RefreshCw,
} from "lucide-react"
import { logos } from "@/lib/logos"

export function InboxPage() {
  const [selectedChannel, setSelectedChannel] = useState("all")
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [sendingMessage, setSendingMessage] = useState(false)
  const [aiEnabled, setAiEnabled] = useState(true)
  const [autoReplyEnabled, setAutoReplyEnabled] = useState(false)
  const [socialExpanded, setSocialExpanded] = useState(true)
  const [message, setMessage] = useState("")
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [selectedChannelFilters, setSelectedChannelFilters] = useState<string[]>([])
  const [unreadOnly, setUnreadOnly] = useState(false)
  const { toast } = useToast()

  const socialChannels = [
    { id: "instagram", name: "Instagram", unread: 0, hasNew: false },
    { id: "whatsapp", name: "WhatsApp", unread: 0, hasNew: false },
    { id: "reddit", name: "Reddit", unread: 0, hasNew: false },
    { id: "linkedin", name: "LinkedIn", unread: 0, hasNew: false },
  ]

  useEffect(() => {
    loadConversations()
  }, [selectedChannel])

  useEffect(() => {
    if (selectedConversation) {
      loadMessages(selectedConversation)
    }
  }, [selectedConversation])

  const loadConversations = async () => {
    try {
      setLoading(true)
      const response = await ConversationsService.getConversations(
        selectedChannel === "all" ? undefined : selectedChannel
      )
      setConversations(response.conversations)
      
      // Sélectionner automatiquement la première conversation s'il n'y en a pas de sélectionnée
      if (response.conversations.length > 0 && !selectedConversation) {
        setSelectedConversation(response.conversations[0].id)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les conversations",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadMessages = async (conversationId: string) => {
    try {
      setLoadingMessages(true)
      const response = await ConversationsService.getMessages(conversationId)
      setMessages(response.messages)
      
      // Marquer comme lu
      await ConversationsService.markAsRead(conversationId)
    } catch (error) {
      console.error('Error loading messages:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les messages",
        variant: "destructive",
      })
    } finally {
      setLoadingMessages(false)
    }
  }

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedConversation) return

    try {
      setSendingMessage(true)
      const newMessage = await ConversationsService.sendMessage(
        selectedConversation,
        message.trim()
      )
      
      setMessages(prev => [...prev, newMessage])
      setMessage("")
      
      toast({
        title: "Message envoyé",
        description: "Votre message a été envoyé avec succès",
      })
    } catch (error) {
      console.error('Error sending message:', error)
      toast({
        title: "Erreur d'envoi",
        description: "Impossible d'envoyer le message",
        variant: "destructive",
      })
    } finally {
      setSendingMessage(false)
    }
  }

  const getPlatformLogoSrc = (platform: string) => {
    switch (platform.toLowerCase()) {
      case "instagram":
        return logos.instagram
      case "whatsapp":
        return logos.whatsapp
      case "reddit":
        return logos.reddit
      case "linkedin":
        return logos.linkedin
      default:
        return logos.all
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return "maintenant"
    if (diffInMinutes < 60) return `${diffInMinutes}m`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h`
    return `${Math.floor(diffInMinutes / 1440)}j`
  }

  const selectedConv = conversations.find(conv => conv.id === selectedConversation)

  return (
    <div className="flex h-full bg-white">
      {/* Sidebar */}
      <div className="w-80 border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-xl font-semibold text-gray-900">Inbox</h1>
            <Button onClick={loadConversations} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
          
          {/* Search */}
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Rechercher dans les conversations..."
              className="pl-10"
            />
          </div>

          {/* Channel Filter */}
          <div className="flex flex-wrap gap-2 mb-4">
            <Button
              variant={selectedChannel === "all" ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedChannel("all")}
              className="text-xs"
            >
              Tous
            </Button>
            {socialChannels.map((channel) => (
              <Button
                key={channel.id}
                variant={selectedChannel === channel.id ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedChannel(channel.id)}
                className="text-xs"
              >
                {channel.name}
                {channel.unread > 0 && (
                  <Badge className="ml-1 bg-red-500 text-white text-xs px-1 py-0">
                    {channel.unread}
                  </Badge>
                )}
              </Button>
            ))}
          </div>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="flex items-center space-x-3 p-3">
                    <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p>Aucune conversation trouvée</p>
              <p className="text-sm">Connectez vos comptes sociaux pour voir vos conversations</p>
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedConversation === conversation.id ? "bg-green-50 border-l-4 border-l-green-500" : ""
                }`}
                onClick={() => setSelectedConversation(conversation.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3 flex-1">
                    <div className="relative">
                      <Avatar className="w-10 h-10">
                        <AvatarImage src="" />
                        <AvatarFallback className="bg-gray-200 text-gray-700">
                          {conversation.customer_name?.charAt(0) || "?"}
                        </AvatarFallback>
                      </Avatar>
                      <img
                        src={getPlatformLogoSrc(conversation.channel)}
                        alt={conversation.channel}
                        className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-white p-0.5"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-gray-900 truncate">
                          {conversation.customer_name || conversation.customer_identifier}
                        </p>
                        <span className="text-xs text-gray-500">
                          {formatTime(conversation.last_message_at)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 truncate">
                        {conversation.last_message_snippet}
                      </p>
                    </div>
                  </div>
                  {conversation.unread_count > 0 && (
                    <Badge className="bg-green-500 text-white text-xs ml-2">
                      {conversation.unread_count}
                    </Badge>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedConv ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src="" />
                    <AvatarFallback className="bg-gray-200">
                      {selectedConv.customer_name?.charAt(0) || "?"}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h2 className="font-semibold text-gray-900">
                      {selectedConv.customer_name || selectedConv.customer_identifier}
                    </h2>
                    <p className="text-sm text-gray-500 capitalize">
                      {selectedConv.channel}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={aiEnabled}
                      onCheckedChange={setAiEnabled}
                      id="ai-enabled"
                    />
                    <label htmlFor="ai-enabled" className="text-sm text-gray-700">
                      IA activée
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {loadingMessages ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse">
                      <div className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
                        <div className="max-w-xs p-3 bg-gray-200 rounded-lg">
                          <div className="h-4 bg-gray-300 rounded w-full mb-2"></div>
                          <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  <p>Aucun message dans cette conversation</p>
                  <p className="text-sm">Commencez la conversation en envoyant un message</p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className="flex items-end space-x-2 max-w-xs lg:max-w-md">
                      {msg.direction === 'inbound' && (
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-gray-200 text-xs">
                            <User className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                      )}
                      <div
                        className={`p-3 rounded-lg ${
                          msg.direction === 'outbound'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-100 text-gray-900'
                        }`}
                      >
                        <p className="text-sm">{msg.content}</p>
                        <p className={`text-xs mt-1 ${
                          msg.direction === 'outbound' ? 'text-green-100' : 'text-gray-500'
                        }`}>
                          {formatTime(msg.created_at)}
                          {msg.is_from_agent && (
                            <Bot className="inline w-3 h-3 ml-1" />
                          )}
                        </p>
                      </div>
                      {msg.direction === 'outbound' && (
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-green-600 text-white text-xs">
                            {msg.is_from_agent ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Message Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <Input
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Tapez votre message..."
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleSendMessage()
                      }
                    }}
                    disabled={sendingMessage}
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!message.trim() || sendingMessage}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {sendingMessage ? (
                    <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <p className="text-lg mb-2">Sélectionnez une conversation</p>
              <p className="text-sm">Choisissez une conversation dans la liste pour commencer</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}