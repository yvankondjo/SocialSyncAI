"use client"

import { useState, useEffect, useRef } from "react"
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
import { SocialAccountsService, ConversationsService, WhatsAppService, InstagramService, type SocialAccount, type Conversation, type Message, useAISettings } from "@/lib/api"
import {
  Search,
  Send,
  User,
  X,
  Clock,
  Plus,
  CheckCircle,
  RefreshCw,
} from "lucide-react"
import { ModelDisplay } from "@/components/ui/model-display"
import { MessageImage } from "@/components/ui/message-image"
import { MessageAudio } from "@/components/ui/message-audio"
import { logos } from "@/lib/logos"

export default function ActivityChatPage() {
  // États pour les données
  const [selectedConversation, setSelectedConversation] = useState<string>("")
  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [previousMessagesLength, setPreviousMessagesLength] = useState<number>(0)
  
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

  // Référence pour le scroll automatique
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  
  const { toast } = useToast()
  const { settings: aiSettings, isLoading: aiSettingsLoading } = useAISettings()

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

  // Fonction pour scroller vers le bas
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end"
      })
    }

    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }

  const formatTime = (dateString: string) => {
    if (!dateString) return "N/A"

    try {
      const date = new Date(dateString)

      // Vérifier si la date est valide
      if (isNaN(date.getTime())) {
        console.warn('⚠️ Date invalide:', dateString)
        return dateString // Retourner la chaîne originale si invalide
      }

      const hours = date.getHours().toString().padStart(2, '0')
      const minutes = date.getMinutes().toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const month = (date.getMonth() + 1).toString().padStart(2, '0')

      const formatted = `${hours}:${minutes} ${day}/${month}`
      return formatted
    } catch (error) {
      console.error('❌ Erreur formatage date:', error, dateString)
      return dateString
    }
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

  // Scroll vers le bas quand on change de conversation
  useEffect(() => {
    if (messages.length > 0 && !loadingMessages) {
      setTimeout(scrollToBottom, 100)
    }
  }, [selectedConversation, loadingMessages, messages.length])

  // Mettre à jour la longueur précédente des messages
  useEffect(() => {
    setPreviousMessagesLength(messages.length)
  }, [messages.length])

  // Scroll automatique vers le bas quand un nouveau message est ajouté
  useEffect(() => {
    if (messages.length > previousMessagesLength && messages.length > 0) {
      setTimeout(scrollToBottom, 50)
    }
  }, [messages.length, previousMessagesLength])

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
      console.log('Conversations loaded:', response.conversations.length)
      setConversations(response.conversations)

      // Initialiser l'état auto-reply basé sur ai_mode de chaque conversation
      const autoReplyState: { [key: string]: boolean } = {}
      response.conversations.forEach(conv => {
        autoReplyState[conv.id] = conv.ai_mode !== 'OFF'
      })
      setConversationAutoReply(autoReplyState)
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

  const handleSendWhatsAppMessage = async () => {
    if (!message.trim() || !selectedConversation || selectedConversation === "") return

    const selectedConv = conversations.find(conv => conv.id === selectedConversation)
    if (!selectedConv || selectedConv.channel !== 'whatsapp') return

    try {
      setSendingMessage(true)

      await WhatsAppService.sendTextMessage({
        recipient: selectedConv.customer_identifier,
        message: message.trim()
      })

      setMessage("")

      toast({
        title: "Message WhatsApp envoyé",
        description: "Votre message WhatsApp a été envoyé avec succès",
      })
    } catch (error) {
      console.error('Error sending WhatsApp message:', error)
      toast({
        title: "Erreur WhatsApp",
        description: "Impossible d'envoyer le message WhatsApp",
        variant: "destructive",
      })
    } finally {
      setSendingMessage(false)
    }
  }

  const handleSendInstagramMessage = async () => {
    if (!message.trim() || !selectedConversation || selectedConversation === "") return

    const selectedConv = conversations.find(conv => conv.id === selectedConversation)
    if (!selectedConv || selectedConv.channel !== 'instagram') return

    try {
      setSendingMessage(true)

      await InstagramService.sendDirectMessage({
        recipient_username: selectedConv.customer_identifier,
        message: message.trim()
      })

      setMessage("")

      toast({
        title: "Message Instagram envoyé",
        description: "Votre message Instagram a été envoyé avec succès",
      })
    } catch (error) {
      console.error('Error sending Instagram message:', error)
      toast({
        title: "Erreur Instagram",
        description: "Impossible d'envoyer le message Instagram",
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

  const handleToggleAutoReply = async (conversationId: string) => {
    // Si l'IA globale est désactivée, on ne permet pas le changement
    if (aiSettings?.is_active === false) return

    const currentState = conversationAutoReply[conversationId] || false
    const newState = !currentState

    try {
      // Mettre à jour le backend
      await ConversationsService.updateAIMode(conversationId, newState ? 'ON' : 'OFF')

      // Mettre à jour l'état local
      setConversationAutoReply(prev => ({
        ...prev,
        [conversationId]: newState,
      }))

      toast({
        title: "Auto-reply mis à jour",
        description: `La réponse automatique est maintenant ${newState ? 'activée' : 'désactivée'} pour cette conversation`,
      })
    } catch (error) {
      console.error('Error updating auto-reply:', error)
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour la réponse automatique",
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
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chat Management</h1>
        <p className="text-muted-foreground">
          Manage conversations and AI responses across all your connected platforms
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
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
                <User className="w-12 h-12 mx-auto mb-4 opacity-50" />
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
                          <AvatarImage src={conversation.customer_avatar_url || "/placeholder.svg"} />
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
                            <X className="w-3 h-3 text-yellow-400" />
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
                      <AvatarImage src={selectedConv.customer_avatar_url || "/placeholder.svg"} />
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
                        <ModelDisplay variant="badge" showSelectedLabel={false} />
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2">
                      <div>
                        <Label className="text-sm font-medium">Auto-reply</Label>
                        <p className="text-xs text-muted-foreground">
                          {aiSettings?.is_active === false
                            ? "IA globale désactivée - réponse automatique impossible"
                            : "Active/désactive pour cette conversation"
                          }
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium ${
                          aiSettings?.is_active === false
                            ? 'text-gray-500'
                            : (conversationAutoReply[selectedConv.id] || false) ? 'text-emerald-700' : 'text-red-700'
                        }`}>
                          {aiSettings?.is_active === false ? 'OFF' : ((conversationAutoReply[selectedConv.id] || false) ? 'ON' : 'OFF')}
                        </span>
                        <button
                          disabled={aiSettings?.is_active === false}
                          onClick={() => handleToggleAutoReply(selectedConv.id)}
                          className={`relative inline-flex h-8 w-14 items-center rounded-full border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                            aiSettings?.is_active === false
                              ? 'bg-gray-400 border-gray-400 cursor-not-allowed'
                              : (conversationAutoReply[selectedConv.id] || false)
                                ? 'bg-emerald-600 border-emerald-600 focus:ring-emerald-500'
                                : 'bg-red-600 border-red-600 focus:ring-red-500'
                          } shadow-lg ${aiSettings?.is_active === false ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                        >
                          <span
                            className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform duration-200 ${
                              aiSettings?.is_active === false
                                ? 'translate-x-1'
                                : (conversationAutoReply[selectedConv.id] || false) ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                    <Button variant="outline" size="sm">
                      <User className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
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
                    {/* Élément invisible pour le scroll automatique */}
                    <div ref={messagesEndRef} />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="text-center text-muted-foreground mt-8">
                    <User className="w-16 h-16 mx-auto mb-4 opacity-50" />
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
                              {/* Affichage conditionnel selon le type de message */}
                              {(() => {
                                // Si c'est une image avec storage_object_name (nouveau format)
                                if (msg.message_type === 'image') {
                                  try {
                                    const parsedContent = JSON.parse(msg.content)
                                    if (Array.isArray(parsedContent)) {
                                      const imageItem = parsedContent.find(item => item.type === 'image_url')
                                      const captionItem = parsedContent.find(item => item.type === 'text')
                                      if (imageItem?.image_url?.url) {
                                        return (
                                          <div className="space-y-2">
                                            <img
                                              src={imageItem.image_url.url}
                                              alt={captionItem?.text || 'Image envoyée'}
                                              className="max-w-full rounded-lg"
                                              style={{ maxWidth: 320 }}
                                            />
                                            {captionItem?.text && (
                                              <div className="text-xs text-muted-foreground bg-muted/40 px-2 py-1 rounded">
                                                {captionItem.text}
                                              </div>
                                            )}
                                          </div>
                                        )
                                      }
                                    }
                                  } catch (error) {
                                    return <div className="text-sm">{msg.content}</div>
                                  }
                                }

                                if (msg.message_type === 'audio') {
                                  try {
                                    const parsedContent = JSON.parse(msg.content)
                                    if (Array.isArray(parsedContent)) {
                                      const audioItem = parsedContent.find(item => item.type === 'audio')
                                      const captionItem = parsedContent.find(item => item.type === 'text')
                                      return (
                                        <MessageAudio label={captionItem?.text || 'Audio reçu'} />
                                      )
                                    }
                                  } catch (error) {
                                    return <MessageAudio label="Audio (non lisible)" />
                                  }
                                }

                                if (typeof msg.content === 'string') {
                                  return <div>{msg.content}</div>
                                }

                                return <div>Message non pris en charge</div>
                              })()}
                            </div>
                            {msg.direction === 'outbound' && msg.is_from_agent && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditMessage(msg.id, msg.content)}
                                className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0"
                              >
                                <User className="w-3 h-3" />
                              </Button>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
                          {msg.direction === 'outbound' ? (
                            <User className="w-3 h-3" />
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
                            <User className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                      )}
                    </div>
                  ))
                )}

                {/* Élément invisible pour le scroll automatique */}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Bar */}
              <div className="p-4 border-t">
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative">
                    <Input
                      value={message}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMessage(e.target.value)}
                      placeholder="Type your message..."
                      className="pr-12"
                      onKeyPress={(e: React.KeyboardEvent) => {
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
                  {/* Boutons d'envoi direct par plateforme */}
                  <div className="flex items-center gap-2">
                    {(() => {
                      const selectedConv = conversations.find(conv => conv.id === selectedConversation)
                      if (!selectedConv) return null

                      return (
                        <>
                          {selectedConv.channel === 'whatsapp' && (
                            <Button
                              onClick={handleSendWhatsAppMessage}
                              disabled={!message.trim() || sendingMessage}
                              size="sm"
                              variant="outline"
                              className="flex items-center gap-1"
                              title="Envoyer via WhatsApp Business API"
                            >
                              <img src={logos.whatsapp} alt="WhatsApp" className="w-4 h-4" />
                              WhatsApp
                            </Button>
                          )}
                          {selectedConv.channel === 'instagram' && (
                            <Button
                              onClick={handleSendInstagramMessage}
                              disabled={!message.trim() || sendingMessage}
                              size="sm"
                              variant="outline"
                              className="flex items-center gap-1"
                              title="Envoyer via Instagram Direct"
                            >
                              <img src={logos.instagram} alt="Instagram" className="w-4 h-4" />
                              Instagram
                            </Button>
                          )}
                        </>
                      )
                    })()}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <User className="w-16 h-16 mx-auto mb-4 opacity-50" />
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
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setEditContent(e.target.value)}
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