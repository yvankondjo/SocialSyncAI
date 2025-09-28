"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { SocialAccountsService, ConversationsService, type SocialAccount, type Conversation, type Message } from "@/lib/api"
import {
  Search,
  Send,
  Bot,
  User,
  Circle,
  Edit3,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Filter,
  MoreHorizontal,
  RefreshCw,
} from "lucide-react"
import { logos } from "@/lib/logos"

export default function ActivityChatPage() {
  // États pour les données
  const [selectedConversation, setSelectedConversation] = useState<string>("")
  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  
  // États pour les filtres et recherche
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [sourceFilter, setSourceFilter] = useState("all")
  
  // États pour l'édition des messages
  const [editingMessage, setEditingMessage] = useState<string | null>(null)
  const [editContent, setEditContent] = useState("")
  
  // États pour les contrôles
  const [conversationAutoReply, setConversationAutoReply] = useState<{ [key: string]: boolean }>({})
  const [message, setMessage] = useState("")
  
  // États de chargement
  const [loading, setLoading] = useState(true)
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [sendingMessage, setSendingMessage] = useState(false)
  
  const { toast } = useToast()

  // Fonctions utilitaires
  const getPlatformDisplayName = (platform: string) => {
    const names: Record<string, string> = {
      instagram: "Instagram",
      whatsapp: "WhatsApp", 
      facebook: "Facebook",
      twitter: "X (Twitter)",
      linkedin: "LinkedIn",
      tiktok: "TikTok",
      youtube: "YouTube",
    }
    return names[platform.toLowerCase()] || platform
  }

  const getPlatformLogoSrc = (platform: string) => {
    switch (platform) {
      case "instagram":
        return logos.instagram
      case "whatsapp":
        return logos.whatsapp
      case "facebook":
        return logos.facebook
      case "twitter":
      case "x":
        return logos.x
      case "linkedin":
        return logos.linkedin
      case "tiktok":
        return logos.tiktok
      case "youtube":
        return logos.youtube
      default:
        return logos.all
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
      case "facebook":
        return "bg-blue-600/20 text-blue-600"
      case "x":
      case "twitter":
        return "bg-gray-500/20 text-gray-400"
      default:
        return "bg-gray-500/20 text-gray-400"
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

  // Chargement des données
  useEffect(() => {
    loadSocialAccounts()
    loadConversations()
  }, [])

  // Filtrer les conversations
  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = 
      (conv.customer_name?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
      (conv.customer_identifier?.toLowerCase().includes(searchQuery.toLowerCase()) || false) ||
      (conv.last_message_snippet?.toLowerCase().includes(searchQuery.toLowerCase()) || false)
    
    const matchesStatus = statusFilter === "all" || 
      (statusFilter === "active" && conv.unread_count > 0) ||
      (statusFilter === "resolved" && conv.unread_count === 0)
    
    const matchesSource = sourceFilter === "all" || conv.channel === sourceFilter

    return matchesSearch && matchesStatus && matchesSource
  })

  // Sélectionner automatiquement la première conversation
  useEffect(() => {
    if (filteredConversations.length > 0 && !selectedConversation) {
      setSelectedConversation(filteredConversations[0].id)
    } else if (filteredConversations.length === 0) {
      setSelectedConversation("")
    }
  }, [filteredConversations, selectedConversation])

  // Charger les messages quand une conversation est sélectionnée
  useEffect(() => {
    if (selectedConversation && selectedConversation !== "") {
      loadMessages(selectedConversation)
    }
  }, [selectedConversation])

  const loadSocialAccounts = async () => {
    try {
      setLoading(true)
      const response = await SocialAccountsService.getSocialAccounts()
      setSocialAccounts(response.accounts)
    } catch (error) {
      console.error('Error loading social accounts:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les comptes sociaux",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadConversations = async () => {
    try {
      setLoadingConversations(true)
      const response = await ConversationsService.getConversations()
      setConversations(response.conversations)
    } catch (error) {
      console.error('Error loading conversations:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les conversations",
        variant: "destructive",
      })
    } finally {
      setLoadingConversations(false)
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
    if (!message.trim() || !selectedConversation || selectedConversation === "") return

    const selectedConv = conversations.find(conv => conv.id === selectedConversation)
    if (!selectedConv) return

    try {
      setSendingMessage(true)
      
      const newMessage = await ConversationsService.sendMessage(
        selectedConv.customer_name || selectedConv.customer_identifier,
        selectedConv.channel,
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

  const handleEditMessage = (messageId: string, currentContent: string) => {
    setEditingMessage(messageId)
    setEditContent(currentContent)
  }

  const handleSaveEdit = async () => {
    if (!editContent.trim()) return

    try {
      // Sauvegarder l'édition (à implémenter côté API)
      console.log("Saving edit:", editContent)
      
      // Mettre à jour les messages localement
      setMessages(prev => prev.map(msg => 
        msg.id === editingMessage 
          ? { ...msg, content: editContent, is_edited: true }
          : msg
      ))
      
      setEditingMessage(null)
      setEditContent("")
      
      toast({
        title: "Message modifié",
        description: "La réponse IA a été mise à jour et ajoutée à la FAQ",
      })
    } catch (error) {
      console.error('Error saving edit:', error)
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder les modifications",
        variant: "destructive",
      })
    }
  }

  const selectedConv = conversations.find(conv => conv.id === selectedConversation)

  // Créer les options de filtre source à partir des comptes connectés
  const sourceOptions = socialAccounts
    .filter(account => account.is_active)
    .map(account => ({
      value: account.platform.toLowerCase(),
      label: getPlatformDisplayName(account.platform),
    }))

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Chat Management</h1>
          <p className="text-muted-foreground">
            Manage conversations and AI responses across all your connected platforms
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="w-4 h-4" />
          New Chat
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="escalated">Escalated</SelectItem>
          </SelectContent>
        </Select>

        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Sources</SelectItem>
            <SelectItem value="web">Web Widget</SelectItem>
            {sourceOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" onClick={loadConversations} disabled={loadingConversations}>
          <RefreshCw className={`w-4 h-4 ${loadingConversations ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex gap-6 h-[calc(100vh-280px)]">
        {/* Conversations List */}
        <div className="w-96 flex flex-col bg-card rounded-lg border">
          <div className="p-4 border-b">
            <h2 className="font-semibold">Conversations</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto">
            {loadingConversations ? (
              <div className="p-4 space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="animate-pulse">
                    <div className="flex items-center space-x-3 p-3">
                      <div className="w-12 h-12 bg-muted rounded-full"></div>
                      <div className="flex-1 space-y-2">
                        <div className="h-4 bg-muted rounded w-3/4"></div>
                        <div className="h-3 bg-muted rounded w-1/2"></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-4 text-center text-muted-foreground">
                <Circle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No conversations found</p>
                <p className="text-sm">Try adjusting your filters or check back later for new conversations.</p>
              </div>
            ) : (
              <div className="space-y-1 p-2">
                {filteredConversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    onClick={() => setSelectedConversation(conversation.id)}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedConversation === conversation.id
                        ? "bg-primary/10 border border-primary/20"
                        : "hover:bg-muted/50"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="relative">
                        <Avatar className="w-10 h-10">
                          <AvatarImage src="/placeholder.svg" />
                          <AvatarFallback className="text-sm">
                            {conversation.customer_name?.charAt(0) || "?"}
                          </AvatarFallback>
                        </Avatar>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-background rounded-full border flex items-center justify-center">
                          <img src={getPlatformLogoSrc(conversation.channel)} alt={conversation.channel} className="w-2.5 h-2.5" />
                        </div>
                        {conversation.unread_count > 0 && (
                          <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-primary text-primary-foreground text-xs rounded-full">
                            {conversation.unread_count}
                          </Badge>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="font-medium text-sm truncate">
                            {conversation.customer_name || conversation.customer_identifier}
                          </h3>
                          <span className="text-xs text-muted-foreground">
                            {conversation.last_message_at ? formatTime(conversation.last_message_at) : "N/A"}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground truncate mb-2">
                          {conversation.last_message_snippet}
                        </p>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={getChannelColor(conversation.channel)}>
                            {getPlatformDisplayName(conversation.channel)}
                          </Badge>
                          {conversation.unread_count > 0 ? (
                            <AlertCircle className="w-3 h-3 text-yellow-400" />
                          ) : (
                            <CheckCircle className="w-3 h-3 text-green-400" />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Conversation Detail */}
        <div className="flex-1 flex flex-col bg-card rounded-lg border">
          {selectedConv ? (
            <>
              {/* Conversation Header */}
              <div className="p-4 border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="w-8 h-8">
                      <AvatarImage src="/placeholder.svg" />
                      <AvatarFallback className="text-sm">
                        {selectedConv.customer_name?.charAt(0) || "?"}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h2 className="font-semibold">
                        {selectedConv.customer_name || selectedConv.customer_identifier}
                      </h2>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant="outline" className={getChannelColor(selectedConv.channel)}>
                          {getPlatformDisplayName(selectedConv.channel)}
                        </Badge>
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
                      <MoreHorizontal className="w-4 h-4" />
                    </Button>
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
                          <div className="max-w-xs p-3 bg-muted rounded-lg">
                            <div className="h-4 bg-muted-foreground/20 rounded w-full mb-2"></div>
                            <div className="h-3 bg-muted-foreground/20 rounded w-1/2"></div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : messages.length === 0 ? (
                  <div className="text-center text-muted-foreground mt-8">
                    <Circle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-semibold mb-2">No messages yet</h3>
                    <p>Start the conversation by sending a message below.</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-4 group ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.direction === 'inbound' && (
                        <Avatar className="w-8 h-8 mt-1">
                          <AvatarFallback className="text-xs">
                            <User className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                      )}

                      <div className={`max-w-md space-y-1 ${msg.direction === 'outbound' ? "order-1" : ""}`}>
                        <div
                          className={`p-3 rounded-lg relative group ${
                            msg.direction === 'outbound'
                              ? 'bg-primary text-primary-foreground'
                              : 'bg-muted text-muted-foreground'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              {msg.content}
                            </div>
                            {msg.direction === 'outbound' && msg.is_from_agent && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditMessage(msg.id, msg.content)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                              >
                                <Edit3 className="w-3 h-3" />
                              </Button>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
                          {msg.direction === 'outbound' ? (
                            msg.is_from_agent ? <Bot className="w-3 h-3" /> : <User className="w-3 h-3" />
                          ) : (
                            <User className="w-3 h-3" />
                          )}
                          <span>{formatTime(msg.created_at)}</span>
                          {msg.is_edited && (
                            <span className="text-yellow-400">Edited</span>
                          )}
                        </div>
                      </div>

                      {msg.direction === 'outbound' && (
                        <Avatar className="w-8 h-8 mt-1 order-2">
                          <AvatarFallback className="text-xs">
                            {msg.is_from_agent ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* Input Bar */}
              <div className="p-4 border-t">
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative">
                    <Input
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Type your message..."
                      className="pr-12"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          handleSendMessage()
                        }
                      }}
                      disabled={sendingMessage}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={!message.trim() || sendingMessage}
                      size="sm"
                      className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
                    >
                      {sendingMessage ? (
                        <div className="w-4 h-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent"></div>
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <Circle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-semibold mb-2">Select a conversation</h3>
                <p>Choose a conversation from the list to view its details and messages.</p>
              </div>
            </div>
          )}
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