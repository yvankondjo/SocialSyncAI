"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { SocialAccountsService, type SocialAccount } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AddChannelDialog } from "@/components/add-channel-dialog"
import { logos } from "@/lib/logos"
import {
  Plus,
  RefreshCw,
  Unlink,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react"

interface SocialAccountWithUI extends SocialAccount {
  logo: string
  bgColor: string
  textColor: string
}

const getPlatformConfig = (platform: string) => {
  const configs: Record<string, { logo: string, bgColor: string, textColor: string, description: string }> = {
    instagram: {
      logo: logos.instagram,
      bgColor: "bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200",
      textColor: "text-gray-900",
      description: "Publications et messages Instagram Business"
    },
    whatsapp: {
      logo: logos.whatsapp,
      bgColor: "bg-green-50 border-green-200",
      textColor: "text-gray-900",
      description: "Messages WhatsApp Business"
    },
    youtube: {
      logo: "https://upload.wikimedia.org/wikipedia/commons/0/09/YouTube_full-color_icon_%282017%29.svg",
      bgColor: "bg-red-50 border-red-200",
      textColor: "text-gray-900",
      description: "Vidéos et chaînes YouTube"
    },
    linkedin: {
      logo: "https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png",
      bgColor: "bg-blue-50 border-blue-200",
      textColor: "text-gray-900",
      description: "Réseau professionnel LinkedIn"
    },
    twitter: {
      logo: "https://upload.wikimedia.org/wikipedia/commons/6/6f/Logo_of_Twitter.svg",
      bgColor: "bg-white border-gray-200",
      textColor: "text-gray-900",
      description: "Messages et tweets Twitter/X"
    },
    facebook: {
      logo: "https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg",
      bgColor: "bg-blue-50 border-blue-200",
      textColor: "text-gray-900",
      description: "Publications Facebook"
    },
    tiktok: {
      logo: "https://upload.wikimedia.org/wikipedia/commons/a/a7/TikTok_logo.svg",
      bgColor: "bg-black border-gray-200",
      textColor: "text-white",
      description: "Vidéos courtes TikTok"
    }
  }
  
  return configs[platform.toLowerCase()] || {
    logo: logos.instagram,
    bgColor: "bg-gray-50 border-gray-200",
    textColor: "text-gray-900",
    description: "Plateforme sociale"
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case "connected":
      return <CheckCircle className="w-4 h-4 text-green-600" />
    case "error":
      return <AlertCircle className="w-4 h-4 text-red-600" />
    case "expired":
      return <Clock className="w-4 h-4 text-yellow-600" />
    case "pending_setup":
      return <Clock className="w-4 h-4 text-blue-600" />
    default:
      return <AlertCircle className="w-4 h-4 text-gray-600" />
  }
}

const getAccountStatus = (account: SocialAccount): 'connected' | 'expired' | 'error' | 'pending_setup' => {
  if (account.status) {
    return account.status
  }
  
  if (!account.is_active) {
    return 'error'
  }
  
  if (account.token_expires_at) {
    const expiryDate = new Date(account.token_expires_at)
    const now = new Date()
    if (expiryDate <= now) {
      return 'expired'
    }
  }
  
  if (!account.access_token) {
    return 'pending_setup'
  }
  
  return 'connected'
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "connected":
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">Connecté</Badge>
    case "error":
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">Erreur</Badge>
    case "expired":
      return <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">Expiré</Badge>
    case "pending_setup":
      return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Configuration</Badge>
    default:
      return <Badge variant="secondary">Inconnu</Badge>
  }
}

export default function SocialAccountsPage() {
  const [accounts, setAccounts] = useState<SocialAccountWithUI[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await SocialAccountsService.getSocialAccounts()
      
      const accountsWithUI = response.accounts.map(account => {
        const config = getPlatformConfig(account.platform)
        const status = getAccountStatus(account)
        return {
          ...account,
          ...config,
          status
        }
      })
      
      setAccounts(accountsWithUI)
    } catch (error) {
      console.error('Error loading accounts:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les comptes sociaux",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async (accountId: string, platform: string) => {
    try {
      await SocialAccountsService.deleteSocialAccount(accountId)
      toast({
        title: "Compte déconnecté",
        description: `Le compte ${platform} a été déconnecté avec succès`,
      })
      loadAccounts()
    } catch (error) {
      console.error('Error disconnecting account:', error)
      toast({
        title: "Erreur",
        description: `Impossible de déconnecter le compte ${platform}`,
        variant: "destructive",
      })
    }
  }

  const supportedPlatforms = ['instagram', 'whatsapp', 'youtube', 'linkedin', 'twitter', 'facebook', 'tiktok']
  const connectedAccounts = accounts.filter(account => 
    supportedPlatforms.includes(account.platform.toLowerCase()) && 
    account.status !== 'pending_setup'
  )
  
  // Détecter les plateformes manquantes (pas connectées du tout)
  const availableToConnect = supportedPlatforms.filter(platform => 
    !accounts.some(account => account.platform.toLowerCase() === platform)
  )
  
  // Toutes les plateformes supportées (pour le dialog d'ajout)
  const allSupportedPlatforms = supportedPlatforms
  
  // Détecter les comptes expirés qui ont besoin d'être reconnectés
  const expiredAccounts = connectedAccounts.filter(account => account.status === 'expired')
  
  // Détecter les comptes qui vont bientôt expirer (moins de 30 jours)
  const soonToExpireAccounts = connectedAccounts.filter(account => {
    if (!account.token_expires_at || account.status !== 'connected') return false
    const now = new Date()
    const expiryDate = new Date(account.token_expires_at)
    const daysRemaining = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
    return daysRemaining <= 30 && daysRemaining > 0
  })

  if (loading) {
    return (
      <div className="p-4 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Comptes sociaux</h1>
            <p className="text-gray-600 text-sm">Connectez Instagram et WhatsApp pour gérer vos conversations</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map(i => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-4">
                <div className="h-16 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Social Accounts</h1>
        <p className="text-gray-600 text-sm mt-1">Connect and manage your social media accounts</p>
      </div>

      {/* Social Accounts Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* Connected Accounts */}
        {connectedAccounts.map((account) => {
          const config = getPlatformConfig(account.platform)
          const status = getAccountStatus(account)
          
          return (
            <Card key={account.id} className={`relative overflow-hidden hover:shadow-lg transition-all duration-200 ${config.bgColor} border-0`}>
              {/* Colored Header Strip */}
              <div className={`h-16 ${config.bgColor} flex items-center justify-between px-4`}>
                <div className="flex items-center space-x-2">
                  <img
                    src={config.logo}
                    alt={account.platform}
                    className="w-6 h-6"
                  />
                  <div>
                    <p className="text-sm font-medium capitalize">{account.platform}</p>
                    <p className="text-xs text-gray-600">@{account.username || account.display_name}</p>
                  </div>
                </div>
                {status === 'connected' ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : status === 'expired' ? (
                  <Clock className="w-4 h-4 text-yellow-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-600" />
                )}
              </div>

              {/* White Content Area */}
              <div className="p-4 bg-white">
                <div className="space-y-3">
                  {/* Status Badge */}
                  <div className="flex justify-center">
                    {status === 'connected' ? (
                      <Badge className="bg-green-100 text-green-800 hover:bg-green-100 text-xs">Connecté</Badge>
                    ) : status === 'expired' ? (
                      <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100 text-xs">Re-auth</Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-800 hover:bg-red-100 text-xs">Erreur</Badge>
                    )}
                  </div>

                  {/* Last Activity */}
                  <p className="text-xs text-gray-500 text-center">
                    {account.token_expires_at ? 
                      `${Math.ceil((new Date(account.token_expires_at).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} jours restants` : 
                      'Récemment'
                    }
                  </p>

                  {/* Action Buttons */}
                  <div className="space-y-2">
                    {status === 'expired' ? (
                      <Button
                        size="sm"
                        onClick={() => setShowAddDialog(true)}
                        className="w-full bg-green-600 hover:bg-green-700 text-xs h-8"
                      >
                        Re-authenticate
                      </Button>
                    ) : status === 'connected' ? (
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setShowAddDialog(true)}
                          className="flex-1 text-xs h-8"
                        >
                          <RefreshCw className="w-3 h-3 mr-1" />
                          Re-sync
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDisconnect(account.id, account.platform)}
                          className="flex-1 text-xs h-8"
                        >
                          <Unlink className="w-3 h-3 mr-1" />
                          Disconnect
                        </Button>
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => setShowAddDialog(true)}
                        className="w-full bg-green-600 hover:bg-green-700 text-xs h-8"
                      >
                        Connect
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          )
        })}

        {/* Add Social Profile Card */}
        <Card className="relative overflow-hidden hover:shadow-lg transition-all duration-200 border-2 border-dashed border-gray-300 bg-white">
          <div className="h-full flex flex-col items-center justify-center p-6 cursor-pointer" onClick={() => setShowAddDialog(true)}>
            <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center mb-3">
              <Plus className="w-6 h-6 text-white" />
            </div>
            <p className="text-sm font-medium text-gray-900 text-center">Add Social Profile</p>
            <p className="text-xs text-gray-500 text-center mt-1">Enhance your presence</p>
          </div>
        </Card>
      </div>

      <AddChannelDialog 
        open={showAddDialog} 
        onOpenChange={(open) => {
          setShowAddDialog(open)
          if (!open) {
            setTimeout(() => loadAccounts(), 1000)
          }
        }}
        connectedPlatforms={connectedAccounts.map(acc => acc.platform.toLowerCase())}
      />
    </div>
  )
}