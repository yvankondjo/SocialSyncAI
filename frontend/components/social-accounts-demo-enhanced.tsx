"use client"

import type React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AddChannelDialog } from "@/components/add-channel-dialog"
import { TokenExpiryBar } from "@/components/token-expiry-bar"
import { logos } from "@/lib/logos"
import {
  Plus,
  RefreshCw,
  Unlink,
  AlertCircle,
  CheckCircle,
  Clock,
  User,
} from "lucide-react"

interface DemoSocialAccount {
  id: string
  platform: string
  username: string
  account_id: string
  display_name?: string
  profile_url?: string
  is_active: boolean
  status: 'connected' | 'expired' | 'error' | 'pending_setup'
  status_message?: string
  token_expires_at?: string
  created_at: string
  updated_at: string
}

// Données de démonstration avec différents scénarios
const mockAccounts: DemoSocialAccount[] = [
  {
    id: "acc_1",
    platform: "instagram",
    username: "@monbusiness",
    account_id: "17841400008460056",
    display_name: "Mon Business",
    profile_url: "https://instagram.com/monbusiness",
    is_active: true,
    status: "connected",
    token_expires_at: new Date(Date.now() + 45 * 24 * 60 * 60 * 1000).toISOString(), // 45 jours
    created_at: "2024-01-15T10:30:00Z",
    updated_at: "2024-01-15T10:30:00Z"
  },
  {
    id: "acc_2", 
    platform: "whatsapp",
    username: "+33123456789",
    account_id: "120363222425962637",
    display_name: "WhatsApp Business",
    is_active: true,
    status: "expired",
    status_message: "Le token a expiré. Reconnectez-vous pour continuer à recevoir les messages.",
    token_expires_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // Expiré il y a 5 jours
    created_at: "2024-01-10T14:20:00Z",
    updated_at: "2024-01-20T09:15:00Z"
  }
]

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

export default function SocialAccountsDemoEnhanced() {
  const [accounts, setAccounts] = useState<DemoSocialAccount[]>(mockAccounts)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showMessage, setShowMessage] = useState("")

  const handleConnect = (platform: string) => {
    setShowMessage(`Connexion à ${platform} en cours... (Mode démo)`)
    setTimeout(() => setShowMessage(""), 3000)
  }

  const handleDisconnect = (accountId: string, platform: string) => {
    setAccounts(prev => prev.filter(acc => acc.id !== accountId))
    setShowMessage(`Compte ${platform} déconnecté (Mode démo)`)
    setTimeout(() => setShowMessage(""), 3000)
  }

  const handleReconnect = (platform: string) => {
    setAccounts(prev => prev.map(acc => 
      acc.platform === platform 
        ? { 
            ...acc, 
            status: 'connected' as const, 
            status_message: undefined,
            token_expires_at: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString() // 60 jours
          }
        : acc
    ))
    setShowMessage(`Compte ${platform} reconnecté avec succès (Mode démo)`)
    setTimeout(() => setShowMessage(""), 3000)
  }

  const supportedPlatforms = ['instagram', 'whatsapp']
  const connectedAccounts = accounts.filter(account => 
    supportedPlatforms.includes(account.platform.toLowerCase()) && 
    account.status !== 'pending_setup'
  )
  
  // Détecter les plateformes manquantes (pas connectées du tout)
  const availableToConnect = supportedPlatforms.filter(platform => 
    !accounts.some(account => account.platform.toLowerCase() === platform)
  )
  
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

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Comptes sociaux - Démonstration</h1>
          <p className="text-gray-600 mt-1">Connectez Instagram et WhatsApp pour gérer vos conversations</p>
          {showMessage && (
            <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm">{showMessage}</p>
            </div>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualiser
          </Button>
          {availableToConnect.length > 0 && (
            <Button 
              onClick={() => setShowAddDialog(true)} 
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Connecter un compte
            </Button>
          )}
        </div>
      </div>

      {/* Alerts for expired or soon-to-expire accounts */}
      {(expiredAccounts.length > 0 || soonToExpireAccounts.length > 0) && (
        <div className="space-y-4">
          {expiredAccounts.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
                <div>
                  <h3 className="text-sm font-medium text-red-800">
                    {expiredAccounts.length} compte{expiredAccounts.length > 1 ? 's' : ''} expiré{expiredAccounts.length > 1 ? 's' : ''}
                  </h3>
                  <p className="text-sm text-red-700">
                    Reconnectez vos comptes pour continuer à recevoir les messages.
                  </p>
                </div>
              </div>
            </div>
          )}
          
          {soonToExpireAccounts.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-yellow-600 mr-3" />
                <div>
                  <h3 className="text-sm font-medium text-yellow-800">
                    {soonToExpireAccounts.length} compte{soonToExpireAccounts.length > 1 ? 's' : ''} va{soonToExpireAccounts.length > 1 ? 'nt' : ''} bientôt expirer
                  </h3>
                  <p className="text-sm text-yellow-700">
                    Pensez à reconnecter vos comptes pour éviter l'interruption du service.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Connected Accounts */}
      {connectedAccounts.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900">Comptes connectés</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {connectedAccounts.map((account) => {
              const config = getPlatformConfig(account.platform)
              return (
                <Card key={account.id} className={`hover:shadow-lg transition-all duration-200 ${config.bgColor}`}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex items-center space-x-4">
                        <div className="p-3 bg-white rounded-lg shadow-sm">
                          <img
                            src={config.logo}
                            alt={account.platform}
                            className="w-8 h-8"
                          />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 capitalize">{account.platform}</h3>
                          <p className="text-gray-600">{account.username || account.display_name}</p>
                        </div>
                      </div>
                      {getStatusIcon(account.status)}
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        {getStatusBadge(account.status)}
                        <div className="flex items-center text-sm text-gray-600">
                          <User className="w-4 h-4 mr-1" />
                          Actif
                        </div>
                      </div>

                      {/* Barre de progression du token */}
                      {account.token_expires_at && account.status === 'connected' && (
                        <TokenExpiryBar 
                          tokenExpiresAt={account.token_expires_at}
                          className="bg-white/30 p-3 rounded-lg"
                        />
                      )}

                      {account.status_message && (
                        <p className="text-sm text-gray-600 bg-white/50 p-3 rounded-lg">{account.status_message}</p>
                      )}

                      <div className="flex space-x-3">
                        {account.status === 'expired' && (
                          <Button
                            size="sm"
                            onClick={() => handleReconnect(account.platform)}
                            className="flex-1 bg-red-600 hover:bg-red-700"
                          >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Reconnecter maintenant
                          </Button>
                        )}
                        
                        {account.status === 'connected' && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setShowAddDialog(true)}
                              className="flex-1 border-blue-200 text-blue-700 hover:bg-blue-50"
                            >
                              <RefreshCw className="w-4 h-4 mr-2" />
                              Renouveler
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDisconnect(account.id, account.platform)}
                              className="flex-1 border-red-200 text-red-700 hover:bg-red-50"
                            >
                              <Unlink className="w-4 h-4 mr-2" />
                              Déconnecter
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Available Platforms */}
      {availableToConnect.length > 0 && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Plateformes manquantes</h2>
            <Badge variant="outline" className="text-orange-600 border-orange-200">
              {availableToConnect.length} manquante{availableToConnect.length > 1 ? 's' : ''}
            </Badge>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {availableToConnect.map((platform) => {
              const config = getPlatformConfig(platform)
              
              return (
                <Card key={platform} className={`hover:shadow-lg transition-all duration-200 cursor-pointer ${config.bgColor} border-orange-200`} 
                      onClick={() => setShowAddDialog(true)}>
                  <CardContent className="p-6">
                    <div className="flex items-center space-x-4 mb-6">
                      <div className="p-3 bg-white rounded-lg shadow-sm">
                        <img
                          src={config.logo}
                          alt={platform}
                          className="w-8 h-8"
                        />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 capitalize">{platform}</h3>
                        <p className="text-gray-600">{config.description}</p>
                        <p className="text-sm text-orange-600 font-medium mt-1">
                          Non connecté
                        </p>
                      </div>
                    </div>

                    <Button
                      size="sm"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation()
                        setShowAddDialog(true)
                      }}
                      className="w-full bg-orange-600 hover:bg-orange-700"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Connecter maintenant
                    </Button>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Empty State */}
      {connectedAccounts.length === 0 && availableToConnect.length === 0 && (
        <Card className="p-12 text-center">
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
              <User className="w-8 h-8 text-gray-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Tous les comptes sont connectés</h3>
              <p className="text-gray-600">Vous avez connecté tous les comptes sociaux disponibles.</p>
            </div>
          </div>
        </Card>
      )}

      {connectedAccounts.length === 0 && availableToConnect.length > 0 && (
        <Card className="p-12 text-center border-orange-200 bg-orange-50">
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center">
              <Plus className="w-8 h-8 text-orange-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Aucun compte connecté</h3>
              <p className="text-gray-600 mb-2">Connectez Instagram et WhatsApp pour commencer à gérer vos conversations.</p>
              <p className="text-sm text-orange-600 font-medium">
                {availableToConnect.length} plateforme{availableToConnect.length > 1 ? 's' : ''} disponible{availableToConnect.length > 1 ? 's' : ''} : {availableToConnect.join(', ')}
              </p>
            </div>
            <Button onClick={() => setShowAddDialog(true)} className="bg-orange-600 hover:bg-orange-700">
              <Plus className="w-4 h-4 mr-2" />
              Connecter mes comptes
            </Button>
          </div>
        </Card>
      )}

      <AddChannelDialog 
        open={showAddDialog} 
        onOpenChange={(open) => {
          setShowAddDialog(open)
          if (!open) {
            // Simuler l'ajout d'un compte après fermeture du dialog
            setTimeout(() => {
              if (availableToConnect.length > 0) {
                const newAccount: DemoSocialAccount = {
                  id: `acc_${Date.now()}`,
                  platform: availableToConnect[0],
                  username: `@demo_${availableToConnect[0]}`,
                  account_id: `demo_${Date.now()}`,
                  display_name: `Demo ${availableToConnect[0]}`,
                  is_active: true,
                  status: 'connected',
                  token_expires_at: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString()
                }
                setAccounts(prev => [...prev, newAccount])
                setShowMessage(`Compte ${availableToConnect[0]} connecté avec succès (Mode démo)`)
                setTimeout(() => setShowMessage(""), 3000)
              }
            }, 1000)
          }
        }}
      />
    </div>
  )
}
