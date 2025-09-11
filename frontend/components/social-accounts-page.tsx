"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import { SocialAccountsService, type SocialAccount } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { logos } from "@/lib/logos"
import {
  Plus,
  RefreshCw,
  Unlink,
  AlertCircle,
  CheckCircle,
  Clock,
  Settings,
  ExternalLink,
} from "lucide-react"

interface SocialAccountWithUI extends SocialAccount {
  logo: string
  bgColor: string
  textColor: string
}

const getPlatformConfig = (platform: string) => {
  const configs: Record<string, { logo: string, bgColor: string, textColor: string }> = {
    instagram: {
      logo: logos.instagram,
      bgColor: "bg-gradient-to-br from-purple-100 to-pink-100",
      textColor: "text-gray-900",
    },
    whatsapp: {
      logo: logos.whatsapp,
      bgColor: "bg-green-100",
      textColor: "text-gray-900",
    },
    reddit: {
      logo: logos.reddit,
      bgColor: "bg-orange-100",
      textColor: "text-gray-900",
    },
    linkedin: {
      logo: logos.linkedin,
      bgColor: "bg-blue-100",
      textColor: "text-gray-900",
    },
    x: {
      logo: logos.x,
      bgColor: "bg-gray-100",
      textColor: "text-gray-900",
    },
    twitter: {
      logo: logos.twitter,
      bgColor: "bg-blue-100",
      textColor: "text-gray-900",
    },
    facebook: {
      logo: logos.facebook,
      bgColor: "bg-blue-100",
      textColor: "text-gray-900",
    },
    youtube: {
      logo: logos.youtube,
      bgColor: "bg-red-100",
      textColor: "text-gray-900",
    },
    tiktok: {
      logo: logos.tiktok,
      bgColor: "bg-gray-100",
      textColor: "text-gray-900",
    },
  }
  
  return configs[platform.toLowerCase()] || {
    logo: logos.all,
    bgColor: "bg-gray-100",
    textColor: "text-gray-900",
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
      return <Settings className="w-4 h-4 text-blue-600" />
    default:
      return <AlertCircle className="w-4 h-4 text-gray-600" />
  }
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
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      setLoading(true)
      const response = await SocialAccountsService.getSocialAccounts()
      
      const accountsWithUI = response.accounts.map(account => ({
        ...account,
        ...getPlatformConfig(account.platform)
      }))
      
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

  const handleConnect = async (platform: string) => {
    if (platform === 'linkedin') {
      toast({
        title: "LinkedIn",
        description: "LinkedIn sera disponible prochainement",
        variant: "default",
      })
      return
    }

    try {
      setConnectingPlatform(platform)
      const response = await SocialAccountsService.getConnectUrl(platform)
      
      // Ouvrir l'URL d'autorisation dans une nouvelle fenêtre
      window.open(response.authorization_url, '_blank', 'width=600,height=600')
      
      toast({
        title: "Connexion en cours",
        description: `Connectez-vous à ${platform} dans la nouvelle fenêtre`,
      })
      
      // Recharger les comptes après un délai pour voir les changements
      setTimeout(() => {
        loadAccounts()
      }, 3000)
      
    } catch (error) {
      console.error('Error connecting account:', error)
      toast({
        title: "Erreur de connexion",
        description: `Impossible de se connecter à ${platform}`,
        variant: "destructive",
      })
    } finally {
      setConnectingPlatform(null)
    }
  }

  const handleDisconnect = async (accountId: string, platform: string) => {
    if (platform === 'linkedin') {
      toast({
        title: "LinkedIn",
        description: "LinkedIn est en mode stub, impossible de déconnecter",
        variant: "default",
      })
      return
    }

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

  const availablePlatforms = [
    { id: 'instagram', name: 'Instagram', description: 'Gérez vos publications et messages' },
    { id: 'whatsapp', name: 'WhatsApp', description: 'Conversations et messages WhatsApp Business' },
    { id: 'reddit', name: 'Reddit', description: 'Publications et commentaires sur Reddit' },
    { id: 'linkedin', name: 'LinkedIn', description: 'Réseau professionnel (bientôt disponible)' },
  ]

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Comptes sociaux</h1>
            <p className="text-gray-600">Gérez vos connexions aux réseaux sociaux</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-20 bg-gray-200 rounded"></div>
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Comptes sociaux</h1>
          <p className="text-gray-600">Gérez vos connexions aux réseaux sociaux</p>
        </div>
        <Button onClick={loadAccounts} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Actualiser
        </Button>
      </div>

      {/* Connected Accounts */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Comptes connectés</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.filter(account => account.status !== 'pending_setup').map((account) => (
            <Card key={account.id} className="hover:shadow-md transition-shadow">
              <CardContent className={`p-6 ${account.bgColor}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <img
                      src={account.logo}
                      alt={account.platform}
                      className="w-10 h-10"
                    />
                    <div>
                      <h3 className="font-semibold text-gray-900 capitalize">{account.platform}</h3>
                      <p className="text-sm text-gray-600">{account.username || account.display_name}</p>
                    </div>
                  </div>
                  {getStatusIcon(account.status)}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    {getStatusBadge(account.status)}
                  </div>

                  {account.status_message && (
                    <p className="text-sm text-gray-600">{account.status_message}</p>
                  )}

                  <div className="flex space-x-2">
                    {account.status === 'expired' && (
                      <Button
                        size="sm"
                        onClick={() => handleConnect(account.platform)}
                        disabled={connectingPlatform === account.platform}
                        className="flex-1"
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        Reconnecter
                      </Button>
                    )}
                    
                    {account.status === 'connected' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDisconnect(account.id, account.platform)}
                        className="flex-1"
                      >
                        <Unlink className="w-4 h-4 mr-1" />
                        Déconnecter
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Available Platforms */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Plateformes disponibles</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {availablePlatforms.map((platform) => {
            const connectedAccount = accounts.find(acc => acc.platform.toLowerCase() === platform.id)
            const config = getPlatformConfig(platform.id)
            
            if (connectedAccount && connectedAccount.status !== 'pending_setup') {
              return null // Déjà affiché dans la section connectés
            }

            return (
              <Card key={platform.id} className="hover:shadow-md transition-shadow">
                <CardContent className={`p-6 ${config.bgColor}`}>
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <img
                        src={config.logo}
                        alt={platform.name}
                        className="w-10 h-10"
                      />
                      <div>
                        <h3 className="font-semibold text-gray-900">{platform.name}</h3>
                        <p className="text-sm text-gray-600">{platform.description}</p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {connectedAccount?.status === 'pending_setup' ? (
                      <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">
                        Configuration en cours
                      </Badge>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleConnect(platform.id)}
                        disabled={connectingPlatform === platform.id || platform.id === 'linkedin'}
                        className="w-full bg-green-600 hover:bg-green-700"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        {connectingPlatform === platform.id ? 'Connexion...' : 'Connecter'}
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}