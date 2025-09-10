"use client"

import { useState } from "react"
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
} from "lucide-react"
import { logos } from "@/lib/logos"

export function InboxPage() {
  const [selectedChannel, setSelectedChannel] = useState("tous")
  const [selectedConversation, setSelectedConversation] = useState("1")
  const [aiEnabled, setAiEnabled] = useState(true)
  const [autoReplyEnabled, setAutoReplyEnabled] = useState(false)
  const [socialExpanded, setSocialExpanded] = useState(true)
  const [message, setMessage] = useState("")
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [selectedChannelFilters, setSelectedChannelFilters] = useState<string[]>([])
  const [unreadOnly, setUnreadOnly] = useState(false)

  const socialChannels = [
    { id: "instagram", name: "Instagram", unread: 5, hasNew: true },
    { id: "whatsapp", name: "WhatsApp", unread: 12, hasNew: false },
    { id: "facebook", name: "Facebook", unread: 3, hasNew: false },
    { id: "twitter", name: "X (Twitter)", unread: 0, hasNew: false },
    { id: "linkedin", name: "LinkedIn", unread: 2, hasNew: true },
    { id: "tiktok", name: "TikTok", unread: 1, hasNew: false },
    { id: "youtube", name: "YouTube", unread: 0, hasNew: false },
  ]

  const conversations = [
    {
      id: "1",
      name: "Marie Dubois",
      avatar: "/diverse-woman-portrait.png",
      lastMessage: "Merci pour votre réponse rapide !",
      time: "2m",
      unread: 2,
      initials: "MD",
      platform: "instagram",
    },
    {
      id: "2",
      name: "Jean Martin",
      avatar: "/thoughtful-man.png",
      lastMessage: "Pouvez-vous m'envoyer plus d'infos ?",
      time: "15m",
      unread: 0,
      initials: "JM",
      platform: "whatsapp",
    },
    {
      id: "3",
      name: "Sophie Laurent",
      avatar: "/woman-blonde.png",
      lastMessage: "Parfait, je prends rendez-vous",
      time: "1h",
      unread: 1,
      initials: "SL",
      platform: "facebook",
    },
    {
      id: "4",
      name: "Pierre Durand",
      avatar: "/man-beard.png",
      lastMessage: "Merci beaucoup pour votre aide",
      time: "3h",
      unread: 0,
      initials: "PD",
      platform: "linkedin",
    },
  ]

  const messages = [
    {
      id: "1",
      type: "user",
      content: "Bonjour, j'aimerais avoir des informations sur vos services",
      time: "14:30",
      sender: "Marie Dubois",
      platform: "instagram",
    },
    {
      id: "2",
      type: "agent",
      content:
        "Bonjour Marie ! Je serais ravi de vous aider. Nous proposons plusieurs services de marketing digital. Quel domaine vous intéresse le plus ?",
      time: "14:31",
      sender: "Assistant IA",
      platform: "instagram",
    },
    {
      id: "3",
      type: "user",
      content: "Je cherche surtout de l'aide pour les réseaux sociaux",
      time: "14:32",
      sender: "Marie Dubois",
      platform: "instagram",
    },
    {
      id: "4",
      type: "agent",
      content:
        "Excellent choix ! Nous avons une expertise particulière en gestion de réseaux sociaux. Nous pouvons vous aider avec la création de contenu, la planification des posts, et l'engagement avec votre audience. Souhaitez-vous planifier un appel pour discuter de vos besoins spécifiques ?",
      time: "14:33",
      sender: "Assistant IA",
      platform: "instagram",
    },
    {
      id: "5",
      type: "user",
      content: "Merci pour votre réponse rapide !",
      time: "14:35",
      sender: "Marie Dubois",
      platform: "instagram",
    },
  ]

  const handleSendMessage = () => {
    if (message.trim()) {
      setMessage("")
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

  return (
    <div className="flex h-full bg-white">
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-6 py-6">
          <div className="mb-6">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-4">CANAUX</p>

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
                  {socialChannels.map((channel) => (
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
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Toggles section */}
          <div className="space-y-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">Réponse automatique</span>
              <Switch
                checked={autoReplyEnabled}
                onCheckedChange={setAutoReplyEnabled}
                className="data-[state=checked]:bg-emerald-500"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700">IA On/Off</span>
              <Switch
                checked={aiEnabled}
                onCheckedChange={setAiEnabled}
                className="data-[state=checked]:bg-emerald-500"
              />
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
          {conversations.map((conversation) => (
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
                    <AvatarImage src={conversation.avatar || "/placeholder.svg"} />
                    <AvatarFallback className="bg-gray-100 text-slate-700 font-medium">
                      {conversation.initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full border-2 border-white flex items-center justify-center">
                    <img src={getPlatformLogoSrc(conversation.platform)} alt={conversation.platform} className="w-3 h-3" />
                  </div>
                  {conversation.unread > 0 && (
                    <Badge className="absolute -top-1 -right-1 w-5 h-5 p-0 flex items-center justify-center bg-emerald-500 text-white text-xs rounded-full">
                      {conversation.unread}
                    </Badge>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium text-slate-900 truncate">{conversation.name}</h3>
                    <span className="text-xs text-gray-500">{conversation.time}</span>
                  </div>
                  <p className="text-sm text-gray-600 truncate">{conversation.lastMessage}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Avatar className="w-10 h-10">
                <AvatarImage src="/diverse-woman-portrait.png" />
                <AvatarFallback className="bg-gray-100 text-slate-700 font-medium">MD</AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-white rounded-full border-2 border-white flex items-center justify-center">
                <img src={logos.instagram} alt="instagram" className="w-3 h-3" />
              </div>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">Marie Dubois</h3>
              <p className="text-sm text-gray-500">En ligne</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg, index) => (
            <div key={msg.id} className={`flex gap-4 group ${msg.type === "agent" ? "justify-end" : "justify-start"}`}>
              {msg.type === "user" && (
                <div className="relative">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-gray-100 text-gray-600">
                      <User className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-white rounded-full border border-white flex items-center justify-center">
                    <img src={getPlatformLogoSrc(msg.platform)} alt={msg.platform} className="w-2.5 h-2.5" />
                  </div>
                </div>
              )}

              <div className={`max-w-md relative ${msg.type === "agent" ? "order-1" : ""}`}>
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
                    msg.type === "agent"
                      ? "bg-sky-100 text-slate-900 rounded-br-md"
                      : "bg-white border border-gray-200 text-slate-900 rounded-bl-md"
                  }`}
                >
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
                <p className="text-xs text-gray-500 mt-2 px-1">{msg.time}</p>
              </div>

              {msg.type === "agent" && (
                <div className="relative order-2">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-emerald-100 text-emerald-700">
                      <Bot className="w-4 h-4" />
                    </AvatarFallback>
                  </Avatar>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Tapez votre message..."
                className="rounded-full pr-12 border-gray-200 bg-white"
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
              />
              <Button
                onClick={handleSendMessage}
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 rounded-full w-8 h-8 p-0 bg-emerald-500 hover:bg-emerald-600 text-white"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
