"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import {
  CheckCircle,
  AlertCircle,
  Settings,
  ExternalLink,
  Loader2,
  Unlink,
} from "lucide-react"
import { SocialAccountsService, SocialAccount } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

// Plateformes sociales supportées
const socialPlatforms = [
  {
    id: "whatsapp",
    name: "WhatsApp Business",
    description: "Connectez votre compte WhatsApp Business pour gérer le support client",
    logoPath: "/logos/whatsapp.svg",
    color: "bg-green-500",
  },
  {
    id: "instagram",
    name: "Instagram",
    description: "Connectez votre compte Instagram pour répondre aux messages directs",
    logoPath: "/logos/instagram.svg",
    color: "bg-pink-500",
  },
]

export default function ConnectPage() {
  const [socialAccounts, setSocialAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [disconnecting, setDisconnecting] = useState<string | null>(null)
  const { toast } = useToast()

  // Charger les comptes sociaux au montage du composant
  useEffect(() => {
    loadSocialAccounts()
  }, [])

  const loadSocialAccounts = async () => {
    try {
      setLoading(true)
      const { accounts } = await SocialAccountsService.getSocialAccounts()
      setSocialAccounts(accounts)
    } catch (error) {
      console.error("Erreur lors du chargement des comptes sociaux:", error)
      toast({
        title: "Erreur",
        description: "Impossible de charger vos comptes sociaux",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusForPlatform = (platformId: string) => {
    const account = socialAccounts.find(account => account.platform === platformId)
    return account ? account.status || "connected" : "disconnected"
  }

  const getConnectedAccount = (platformId: string) => {
    return socialAccounts.find(account => account.platform === platformId)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-500/20 text-green-400"
      case "expired":
        return "bg-yellow-500/20 text-yellow-400"
      case "error":
        return "bg-red-500/20 text-red-400"
      case "pending_setup":
        return "bg-blue-500/20 text-blue-400"
      case "disconnected":
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "expired":
      case "error":
      case "pending_setup":
        return <AlertCircle className="w-4 h-4 text-yellow-400" />
      case "disconnected":
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const handleConnect = async (platformId: string) => {
    try {
      setConnecting(platformId)
      const { authorization_url } = await SocialAccountsService.getConnectUrl(platformId)
      // Ouvrir la fenêtre OAuth
      window.location.href = authorization_url
    } catch (error) {
      console.error(`Erreur lors de la connexion à ${platformId}:`, error)
      toast({
        title: "Erreur de connexion",
        description: `Impossible d'initier la connexion ${platformId}`,
        variant: "destructive",
      })
    } finally {
      setConnecting(null)
    }
  }

  const handleDisconnect = async (accountId: string) => {
    try {
      setDisconnecting(accountId)
      await SocialAccountsService.deleteSocialAccount(accountId)
      // Recharger les comptes après suppression
      await loadSocialAccounts()
      toast({
        title: "Compte déconnecté",
        description: "Votre compte a été déconnecté avec succès",
      })
    } catch (error) {
      console.error("Erreur lors de la déconnexion:", error)
      toast({
        title: "Erreur de déconnexion",
        description: "Impossible de déconnecter le compte",
        variant: "destructive",
      })
    } finally {
      setDisconnecting(null)
    }
  }

  const formatLastSync = (dateString: string | null) => {
    if (!dateString) return "Jamais"
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

    if (diffInMinutes < 60) return `il y a ${diffInMinutes}min`
    if (diffInMinutes < 1440) return `il y a ${Math.floor(diffInMinutes / 60)}h`
    return `il y a ${Math.floor(diffInMinutes / 1440)}j`
  }

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Connexions Sociales</h1>
        <p className="text-muted-foreground">
          Connectez vos comptes WhatsApp et Instagram pour gérer vos messages
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Chargement des comptes...</span>
        </div>
      )}

      {/* Social Platforms Grid */}
      {!loading && (
        <div className="grid gap-6 md:grid-cols-2">
          {socialPlatforms.map((platform) => {
            const status = getStatusForPlatform(platform.id)
            const connectedAccount = getConnectedAccount(platform.id)

            return (
                <Card key={platform.id} className="relative">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 flex items-center justify-center">
                      <img
                        src={platform.logoPath}
                        alt={platform.name}
                        className="w-6 h-6"
                      />
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-lg">{platform.name}</CardTitle>
                      <p className="text-sm text-muted-foreground">{platform.description}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(status)}
                      <Badge variant="outline" className={getStatusColor(status)}>
                        {status === "connected" ? "Connecté" :
                         status === "expired" ? "Expiré" :
                         status === "error" ? "Erreur" :
                         status === "pending_setup" ? "Configuration" :
                         "Déconnecté"}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {connectedAccount && (
                    <div>
                      <Label className="text-sm font-medium">Compte connecté</Label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        <Badge variant="secondary" className="flex items-center gap-2">
                          {connectedAccount.display_name || connectedAccount.username}
                          {connectedAccount.username && connectedAccount.username !== connectedAccount.display_name && (
                            <span className="text-xs opacity-70">@{connectedAccount.username}</span>
                          )}
                        </Badge>
                      </div>
                    </div>
                  )}

                  {connectedAccount?.status_message && (
                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                      <p className="text-sm text-yellow-800 dark:text-yellow-200">
                        {connectedAccount.status_message}
                      </p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-sm text-muted-foreground">
                      Dernière synchro: {connectedAccount ? formatLastSync(connectedAccount.created_at) : "Jamais"}
                    </span>
                    <div className="flex gap-2">
                      {connectedAccount ? (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDisconnect(connectedAccount.id)}
                          disabled={disconnecting === connectedAccount.id}
                        >
                          {disconnecting === connectedAccount.id ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <Unlink className="w-4 h-4 mr-2" />
                          )}
                          Déconnecter
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleConnect(platform.id)}
                          disabled={connecting === platform.id}
                        >
                          {connecting === platform.id ? (
                            <Loader2 className="w-4 h-4 animate-spin mr-2" />
                          ) : (
                            <ExternalLink className="w-4 h-4 mr-2" />
                          )}
                          Connecter
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}