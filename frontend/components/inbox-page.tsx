"use client"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Switch } from "@/components/ui/switch"
import { SocialAccountsService, ConversationsService, type SocialAccount, type Conversation, type Message } from "@/lib/api"
import {
  Search,
  Send,
  User,
  ChevronDown,
  ChevronRight,
  Copy,
  StickyNote,
  RefreshCw,
} from "lucide-react"
import { logos } from "@/lib/logos"

export function InboxPage() {
  const [selectedChannel, setSelectedChannel] = useState("tous")
  const [selectedConversation, setSelectedConversation] = useState("")
  const [aiEnabled, setAiEnabled] = useState(false) // Désactivé par défaut
  const [autoReplyEnabled, setAutoReplyEnabled] = useState(false) // Désactivé par défaut
  const [socialExpanded, setSocialExpanded] = useState(true)
  const [message, setMessage] = useState("")
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [selectedChannelFilters, setSelectedChannelFilters] = useState<string[]>([])
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [loadingConversations, setLoadingConversations] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [sendingMessage, setSendingMessage] = useState(false)
  const { toast } = useToast()

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

  // Charger les comptes sociaux connectés
  useEffect(() => {
    loadSocialAccounts()
  }, [])

  // Charger toutes les conversations au démarrage
  useEffect(() => {
    loadConversations()
  }, [])

  // Filtrer les conversations par canal (frontend)
  const filteredConversations = conversations.filter(conv => {
    if (selectedChannel === "tous") return true
    return conv.channel === selectedChannel
  })

  // Sélectionner automatiquement la première conversation filtrée
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
      // Charger TOUTES les conversations (sans filtre backend)
      const response = await ConversationsService.getConversations()
      console.log('📞 Conversations loaded:', response.conversations) // Debug
      setConversations(response.conversations)
      
      // Sélectionner automatiquement la première conversation s'il n'y en a pas de sélectionnée
      // (Cette logique sera mise à jour après le filtrage frontend)
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
      
      // Charger l'état de la conversation (ai_mode)
      const selectedConv = conversations.find(conv => conv.id === conversationId)
      if (selectedConv) {
        console.log('🔍 Conversation data:', selectedConv) // Debug
        setAiEnabled(selectedConv.ai_mode === 'ON')
        setAutoReplyEnabled(selectedConv.ai_mode === 'ON')
      }
      
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

  const handleToggleAI = async () => {
    if (!selectedConversation) return

    try {
      const newMode = aiEnabled ? 'OFF' : 'ON'
      await ConversationsService.updateAIMode(selectedConversation, newMode)
      setAiEnabled(!aiEnabled)
      setAutoReplyEnabled(!aiEnabled)
      
      toast({
        title: "Succès",
        description: `IA ${newMode === 'ON' ? 'activée' : 'désactivée'} pour cette conversation`,
      })
    } catch (error) {
      console.error('Error toggling AI:', error)
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour le mode IA",
        variant: "destructive",
      })
    }
  }

  const handleToggleAutoReply = async () => {
    if (!selectedConversation) return

    try {
      const newMode = autoReplyEnabled ? 'OFF' : 'ON'
      await ConversationsService.updateAIMode(selectedConversation, newMode)
      setAutoReplyEnabled(!autoReplyEnabled)
      setAiEnabled(!autoReplyEnabled)
      
      toast({
        title: "Succès",
        description: `Réponse automatique ${newMode === 'ON' ? 'activée' : 'désactivée'}`,
      })
    } catch (error) {
      console.error('Error toggling auto reply:', error)
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour la réponse automatique",
        variant: "destructive",
      })
    }
  }

  // Créer les canaux sociaux à partir des comptes connectés
  const socialChannels = socialAccounts
    .filter(account => account.is_active)
    .map(account => ({
      id: account.platform.toLowerCase(),
      name: getPlatformDisplayName(account.platform),
      unread: 0, // TODO: Récupérer le nombre de messages non lus
      hasNew: false, // TODO: Déterminer s'il y a de nouveaux messages
    }))

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedConversation || selectedConversation === "") return

    const selectedConv = conversations.find(conv => conv.id === selectedConversation)
    if (!selectedConv) return

    try {
      setSendingMessage(true)
      console.log('Envoi du message:', message.trim(), 'vers conversation:', selectedConversation)
      
      const newMessage = await ConversationsService.sendMessage(
        selectedConv.customer_name || selectedConv.customer_identifier,
        selectedConv.channel,
        message.trim()
      )
      
      console.log('Message reçu du backend:', newMessage)
      console.log('Messages actuels avant ajout:', messages)
      
      setMessages(prev => {
        const updated = [...prev, newMessage]
        console.log('Messages après ajout:', updated)
        return updated
      })
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
      console.log('📅 Date formatée:', dateString, '→', formatted)
      return formatted
    } catch (error) {
      console.error('❌ Erreur formatage date:', error, dateString)
      return dateString
    }
  }

  const selectedConv = conversations.find(conv => conv.id === selectedConversation)

  return (
    <div className="flex flex-col lg:flex-row h-full bg-white">
      <div className="w-full lg:w-64 bg-white border-r border-gray-200 flex flex-col lg:min-h-0">
        <div className="px-6 py-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">CANAUX</p>
              <Button 
                onClick={loadSocialAccounts} 
                variant="outline" 
                size="sm"
                disabled={loading}
                className="h-6 w-6 p-0"
              >
                <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>

            {/* Tous les canaux */}
            <button
              onClick={() => setSelectedChannel("tous")}
              className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors mb-2 ${
                selectedChannel === "tous"
                  ? "bg-emerald-50 border-l-2 border-emerald-500 text-slate-900"
                  : "hover:bg-gray-50 text-slate-700"
              }`}
            >
              <span className="font-medium">Tous les canaux</span>
            </button>

            {/* Réseaux sociaux collapsible section */}
            <div className="mb-4">
              <button
                onClick={() => setSocialExpanded(!socialExpanded)}
                className="w-full flex items-center justify-between px-3 py-2 text-slate-700 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <span className="font-medium">Réseaux sociaux</span>
                {socialExpanded ? (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                )}
              </button>

              {socialExpanded && (
                <div className="ml-4 mt-2 space-y-1">
                  {loading ? (
                    <div className="space-y-1">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="animate-pulse">
                          <div className="w-full flex items-center px-3 py-2 rounded-lg">
                            <div className="w-4 h-4 bg-gray-200 rounded mr-3"></div>
                            <div className="h-4 bg-gray-200 rounded w-20"></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : socialChannels.length === 0 ? (
                    <div className="px-3 py-2 text-center">
                      <p className="text-xs text-gray-500">Aucun compte connecté</p>
                      <p className="text-xs text-gray-400 mt-1">Connectez vos comptes dans les paramètres</p>
                    </div>
                  ) : (
                    socialChannels.map((channel) => (
                      <button
                        key={channel.id}
                        onClick={() => setSelectedChannel(channel.id)}
                        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-colors ${
                          selectedChannel === channel.id
                            ? "bg-emerald-50 border-l-2 border-emerald-500 text-slate-900"
                            : "hover:bg-gray-50 text-slate-700"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <img src={getPlatformLogoSrc(channel.id)} alt={channel.name} className="w-4 h-4" />
                          <span className="text-sm">{channel.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {channel.hasNew && (
                            <Badge className="bg-emerald-500 text-white text-xs px-2 py-0.5 rounded-full">
                              NOUVEAU
                            </Badge>
                          )}
                          {channel.unread > 0 && (
                            <Badge className="bg-emerald-500 text-white text-xs px-2 py-0.5 rounded-full">
                              {channel.unread}
                            </Badge>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Toggles section */}
          <div className="space-y-6 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-700">Réponse automatique</span>
                <p className="text-xs text-slate-500">Active/désactive pour cette conversation</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${autoReplyEnabled ? 'text-emerald-700' : 'text-red-700'}`}>
                  {autoReplyEnabled ? 'ON' : 'OFF'}
                </span>
                <button
                  onClick={handleToggleAutoReply}
                  disabled={!selectedConversation}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    autoReplyEnabled 
                      ? 'bg-emerald-600 border-emerald-600 focus:ring-emerald-500' 
                      : 'bg-red-600 border-red-600 focus:ring-red-500'
                  } ${!selectedConversation ? 'opacity-30 cursor-not-allowed' : 'shadow-lg'}`}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform duration-200 ${
                      autoReplyEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-slate-700">IA On/Off</span>
                <p className="text-xs text-slate-500">Contrôle général de l'IA</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-medium ${aiEnabled ? 'text-emerald-700' : 'text-red-700'}`}>
                  {aiEnabled ? 'ON' : 'OFF'}
                </span>
                <button
                  onClick={handleToggleAI}
                  disabled={!selectedConversation}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full border-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                    aiEnabled 
                      ? 'bg-emerald-600 border-emerald-600 focus:ring-emerald-500' 
                      : 'bg-red-600 border-red-600 focus:ring-red-500'
                  } ${!selectedConversation ? 'opacity-30 cursor-not-allowed' : 'shadow-lg'}`}
                >
                  <span
                    className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-md transition-transform duration-200 ${
                      aiEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Middle Column - Conversations (unchanged) */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input placeholder="Rechercher une conversation..." className="pl-10 rounded-xl border-gray-200 bg-white" />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loadingConversations ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="animate-pulse">
                  <div className="flex items-center space-x-3 p-3">
                    <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500">
              <p>Aucune conversation trouvée</p>
              <p className="text-sm">Connectez vos comptes sociaux pour voir vos conversations</p>
            </div>
          ) : (
            filteredConversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => setSelectedConversation(conversation.id)}
                className={`w-full p-4 border-b border-gray-100 text-left hover:bg-gray-50 transition-colors ${
                  selectedConversation === conversation.id ? "bg-gray-50" : ""
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="relative">
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={conversation.customer_avatar_url || "/placeholder.svg"} />
                      <AvatarFallback className="bg-gray-100 text-slate-700 font-medium">
                        {conversation.customer_name?.charAt(0) || "?"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full border-2 border-white flex items-center justify-center">
                      <img src={getPlatformLogoSrc(conversation.channel)} alt={conversation.channel} className="w-3 h-3" />
                    </div>
                    {conversation.unread_count > 0 && (
                      <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-emerald-500 text-white text-xs rounded-full">
                        {conversation.unread_count}
                      </Badge>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-medium text-slate-900 truncate">
                        {conversation.customer_name || conversation.customer_identifier}
                      </h3>
                      <span className="text-xs text-gray-500">
                        {conversation.last_message_at ? formatTime(conversation.last_message_at) : "N/A"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 truncate">
                      {conversation.last_message_snippet}
                    </p>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-white">
        {selectedConv ? (
          <>
            {/* Chat Header */}
            <div className="p-4 border-b border-gray-200 bg-white">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src="/placeholder.svg" />
                    <AvatarFallback className="bg-gray-100 text-slate-700 font-medium">
                      {selectedConv.customer_name?.charAt(0) || "?"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full border-2 border-white flex items-center justify-center">
                    <img src={getPlatformLogoSrc(selectedConv.channel)} alt={selectedConv.channel} className="w-3 h-3" />
                  </div>
                </div>
                <div>
                  <h3 className="font-medium text-slate-900">
                    {selectedConv.customer_name || selectedConv.customer_identifier}
                  </h3>
                  <p className="text-sm text-gray-500 capitalize">
                    {selectedConv.channel}
                  </p>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
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
                    className={`flex gap-4 group ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.direction === 'inbound' && (
                      <div className="relative">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-gray-100 text-gray-600">
                            <User className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-full border border-white flex items-center justify-center">
                          <img src={getPlatformLogoSrc(selectedConv.channel)} alt={selectedConv.channel} className="w-2.5 h-2.5" />
                        </div>
                      </div>
                    )}

                    <div className={`max-w-md relative ${msg.direction === 'outbound' ? "order-1" : ""}`}>
                      {/* Hover actions */}
                      <div className="absolute -top-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <Copy className="w-4 h-4 text-gray-500" />
                        </button>
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <StickyNote className="w-4 h-4 text-gray-500" />
                        </button>
                      </div>

                      <div
                        className={`px-4 py-3 rounded-2xl shadow-sm ${
                          msg.direction === 'outbound'
                            ? 'bg-sky-100 text-slate-900 rounded-br-md'
                            : 'bg-white border border-gray-200 text-slate-900 rounded-bl-md'
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{msg.content}</p>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 px-1">
                        {formatTime(msg.created_at)}
                      </p>
                    </div>

                    {msg.direction === 'outbound' && (
                      <div className="relative order-2">
                        <Avatar className="w-8 h-8">
                          <AvatarFallback className="bg-emerald-100 text-emerald-700">
                            <User className="w-4 h-4" />
                          </AvatarFallback>
                        </Avatar>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Input
                    value={message}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMessage(e.target.value)}
                    placeholder="Tapez votre message..."
                    className="rounded-full pr-12 border-gray-200 bg-white"
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
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 rounded-full w-8 h-8 p-0 bg-emerald-500 hover:bg-emerald-600 text-white disabled:opacity-50"
                  >
                    {sendingMessage ? (
                      <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
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
