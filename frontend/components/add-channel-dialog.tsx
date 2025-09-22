"use client"

import { useMemo } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { logos } from "@/lib/logos"
import { SocialAccountsService } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onAccountAdded?: () => void
  connectedPlatforms?: string[]
}

export function AddChannelDialog({ open, onOpenChange, onAccountAdded, connectedPlatforms = [] }: Props) {
  const { toast } = useToast()
  
  const platforms = useMemo(
    () => [
      { 
        id: "instagram", 
        name: "Instagram", 
        icon: logos.instagram,
        description: "Publications et messages Instagram Business",
        color: "from-purple-50 to-pink-50 border-purple-200",
        isConnected: connectedPlatforms.includes("instagram")
      },
      { 
        id: "whatsapp", 
        name: "WhatsApp", 
        icon: logos.whatsapp,
        description: "Messages WhatsApp Business",
        color: "from-green-50 to-green-100 border-green-200",
        isConnected: connectedPlatforms.includes("whatsapp")
      },
    ],
    [connectedPlatforms],
  )

  const startAuth = async (platform: string) => {
    try {
      const res = await SocialAccountsService.getConnectUrl(platform)
      if (res.authorization_url) {
        window.location.href = res.authorization_url
        return
      }
      onOpenChange(false)
    } catch (e) {
      console.error("add account failed", e)
      toast({
        title: "Erreur de connexion",
        description: `Impossible de se connecter à ${platform}`,
        variant: "destructive",
      })
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Ajouter un compte social</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Choisissez une plateforme pour ajouter un nouveau compte ou reconnecter un compte existant.
          </p>
          <div className="grid grid-cols-1 gap-3">
            {platforms.map((platform) => (
              <Button
                key={platform.id}
                onClick={() => !platform.isConnected && startAuth(platform.id)}
                variant="outline"
                disabled={platform.isConnected}
                className={`h-auto p-3 justify-start transition-all ${
                  platform.isConnected 
                    ? 'bg-gray-100 border-gray-200 cursor-not-allowed opacity-60' 
                    : `bg-gradient-to-r ${platform.color} hover:shadow-md`
                }`}
              >
                <div className="flex items-center space-x-3 w-full">
                  <div className={`p-2 rounded-lg shadow-sm ${
                    platform.isConnected ? 'bg-gray-200' : 'bg-white'
                  }`}>
                    <img 
                      src={platform.icon} 
                      className={`w-5 h-5 ${platform.isConnected ? 'grayscale' : ''}`} 
                      alt={platform.name} 
                    />
                  </div>
                  <div className="text-left flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={`font-semibold ${platform.isConnected ? 'text-gray-500' : 'text-gray-900'}`}>
                        {platform.name}
                      </span>
                      {platform.isConnected && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                          Connecté
                        </span>
                      )}
                    </div>
                    <div className={`text-sm ${platform.isConnected ? 'text-gray-400' : 'text-gray-600'}`}>
                      {platform.description}
                    </div>
                  </div>
                </div>
              </Button>
            ))}
          </div>
          {connectedPlatforms.length > 0 && (
            <p className="text-xs text-gray-500 text-center">
              Les comptes déjà connectés sont grisés. Cliquez sur "Renouveler" dans la liste des comptes pour les reconnecter.
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}


