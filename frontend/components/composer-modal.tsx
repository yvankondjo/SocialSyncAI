"use client"

import { useState, useEffect, useRef } from "react"
import { useToast } from "@/hooks/use-toast"
import { SchedulingService, SocialAccountsService, type PlatformPreview, type SocialAccount } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { logos } from "@/lib/logos"
import {
  X,
  CalendarIcon,
  Bold,
  Italic,
  Underline,
  Smile,
  ImageIcon,
  Video,
  Sparkles,
  Plus,
  Trash2,
  Eye,
  Send,
  Save,
  Clock,
  ChevronDown,
  AlertCircle,
  CheckCircle,
} from "lucide-react"

// Types
interface Channel {
  id: string
  name: string
  platform: string
  username?: string
  logo: string
}

interface ComposerModalProps {
  isOpen: boolean
  onClose: () => void
  scheduledAt?: Date
  onSuccess?: () => void
}

const platformConfigs = {
  instagram: {
    name: "Instagram",
    logo: logos.instagram,
    bgColor: "bg-gradient-to-br from-purple-100 to-pink-100",
    characterLimit: 2200,
    requiresMedia: true,
    previewStyle: "square"
  },
  reddit: {
    name: "Reddit",
    logo: logos.reddit,
    bgColor: "bg-orange-100",
    characterLimit: 40000,
    requiresMedia: false,
    previewStyle: "title_and_text"
  },
  whatsapp: {
    name: "WhatsApp",
    logo: logos.whatsapp,
    bgColor: "bg-green-100",
    characterLimit: 4096,
    requiresMedia: false,
    previewStyle: "message"
  },
  linkedin: {
    name: "LinkedIn",
    logo: logos.linkedin,
    bgColor: "bg-blue-100",
    characterLimit: 3000,
    requiresMedia: false,
    previewStyle: "professional",
    disabled: true
  }
}

export function ComposerModal({ isOpen, onClose, scheduledAt, onSuccess }: ComposerModalProps) {
  const [content, setContent] = useState("")
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [availableChannels, setAvailableChannels] = useState<Channel[]>([])
  const [scheduledDate, setScheduledDate] = useState<Date | undefined>(scheduledAt)
  const [scheduledTime, setScheduledTime] = useState("12:00")
  const [mediaUrls, setMediaUrls] = useState<string[]>([])
  const [previews, setPreviews] = useState<PlatformPreview[]>([])
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const { toast } = useToast()

  useEffect(() => {
    if (isOpen) {
      loadAvailableChannels()
    }
  }, [isOpen])

  useEffect(() => {
    if (content && selectedPlatforms.length > 0) {
      generatePreviews()
    } else {
      setPreviews([])
    }
  }, [content, selectedPlatforms, mediaUrls])

  const loadAvailableChannels = async () => {
    try {
      const response = await SocialAccountsService.getSocialAccounts()
      const channels: Channel[] = response.accounts
        .filter(account => account.status === 'connected' || account.status === 'pending_setup')
        .map(account => ({
          id: account.id,
          name: account.display_name || account.platform,
          platform: account.platform.toLowerCase(),
          username: account.username,
          logo: platformConfigs[account.platform.toLowerCase() as keyof typeof platformConfigs]?.logo || logos.all
        }))
      
      setAvailableChannels(channels)
    } catch (error) {
      console.error('Error loading channels:', error)
      toast({
        title: "Erreur",
        description: "Impossible de charger les comptes connectés",
        variant: "destructive",
      })
    }
  }

  const generatePreviews = async () => {
    try {
      setPreviewLoading(true)
      const response = await SchedulingService.previewPost({
        content,
        platforms: selectedPlatforms,
        media_urls: mediaUrls,
        post_type: mediaUrls.length > 0 ? 'image' : 'text'
      })
      setPreviews(response.previews)
    } catch (error) {
      console.error('Error generating previews:', error)
      setPreviews([])
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleSchedule = async () => {
    if (!content.trim()) {
      toast({
        title: "Contenu requis",
        description: "Veuillez saisir du contenu pour votre post",
        variant: "destructive",
      })
      return
    }

    if (selectedPlatforms.length === 0) {
      toast({
        title: "Plateformes requises",
        description: "Veuillez sélectionner au moins une plateforme",
        variant: "destructive",
      })
      return
    }

    if (!scheduledDate) {
      toast({
        title: "Date requise",
        description: "Veuillez sélectionner une date de planification",
        variant: "destructive",
      })
      return
    }

    // Vérifier si LinkedIn est sélectionné
    if (selectedPlatforms.includes('linkedin')) {
      toast({
        title: "LinkedIn non disponible",
        description: "LinkedIn n'est pas encore disponible pour la planification",
        variant: "destructive",
      })
      return
    }

    try {
      setLoading(true)
      
      // Combiner date et heure
      const [hours, minutes] = scheduledTime.split(':').map(Number)
      const scheduledDateTime = new Date(scheduledDate)
      scheduledDateTime.setHours(hours, minutes, 0, 0)

      // Vérifier que la date est dans le futur (timezone Europe/Paris)
      const now = new Date()
      if (scheduledDateTime <= now) {
        toast({
          title: "Date invalide",
          description: "La date de planification doit être dans le futur",
          variant: "destructive",
        })
        return
      }

      const response = await SchedulingService.schedulePost({
        content: content.trim(),
        platforms: selectedPlatforms,
        scheduled_at: scheduledDateTime.toISOString(),
        media_urls: mediaUrls,
        post_type: mediaUrls.length > 0 ? 'image' : 'text',
        metadata: {
          character_counts: previews.reduce((acc, preview) => {
            acc[preview.platform] = preview.character_count
            return acc
          }, {} as Record<string, number>)
        }
      })

      toast({
        title: "Post planifié !",
        description: `Votre post sera publié le ${scheduledDateTime.toLocaleDateString('fr-FR')} à ${scheduledTime}`,
      })

      // Reset form
      setContent("")
      setSelectedPlatforms([])
      setScheduledDate(undefined)
      setScheduledTime("12:00")
      setMediaUrls([])
      setPreviews([])
      
      onSuccess?.()
      onClose()
      
    } catch (error) {
      console.error('Error scheduling post:', error)
      toast({
        title: "Erreur de planification",
        description: "Impossible de planifier le post",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const togglePlatform = (platform: string) => {
    setSelectedPlatforms(prev => 
      prev.includes(platform) 
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    )
  }

  const getCharacterCount = (platform: string) => {
    const preview = previews.find(p => p.platform === platform)
    return preview?.character_count || content.length
  }

  const getCharacterLimit = (platform: string) => {
    const config = platformConfigs[platform as keyof typeof platformConfigs]
    return config?.characterLimit || 500
  }

  const isCharacterLimitExceeded = (platform: string) => {
    return getCharacterCount(platform) > getCharacterLimit(platform)
  }

  const renderPreview = (preview: PlatformPreview) => {
    const config = platformConfigs[preview.platform as keyof typeof platformConfigs]
    
    return (
      <Card key={preview.platform} className={`p-4 ${config?.bgColor || 'bg-gray-100'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <img src={config?.logo} alt={preview.platform} className="w-5 h-5" />
            <span className="font-medium capitalize">{preview.platform}</span>
          </div>
          {preview.is_valid ? (
            <CheckCircle className="w-4 h-4 text-green-600" />
          ) : (
            <AlertCircle className="w-4 h-4 text-red-600" />
          )}
        </div>

        {/* Preview Content */}
        <div className="space-y-2">
          {preview.platform === 'reddit' && preview.preview_data.title && (
            <div className="font-semibold text-sm">
              {preview.preview_data.title}
            </div>
          )}
          
          <div className="text-sm text-gray-700 whitespace-pre-wrap">
            {preview.platform === 'reddit' 
              ? preview.preview_data.body || content
              : content
            }
          </div>

          {mediaUrls.length > 0 && (
            <div className="grid grid-cols-2 gap-2">
              {mediaUrls.slice(0, 2).map((url, index) => (
                <div key={index} className="aspect-square bg-gray-200 rounded flex items-center justify-center">
                  <ImageIcon className="w-6 h-6 text-gray-400" />
                </div>
              ))}
            </div>
          )}

          {/* Character Count */}
          <div className="flex justify-between items-center text-xs">
            <span className={`${preview.is_valid ? 'text-green-600' : 'text-red-600'}`}>
              {preview.character_count}/{preview.character_limit} caractères
            </span>
            {preview.validation_errors.length > 0 && (
              <span className="text-red-600">
                {preview.validation_errors.length} erreur(s)
              </span>
            )}
          </div>

          {/* Validation Errors */}
          {preview.validation_errors.length > 0 && (
            <div className="space-y-1">
              {preview.validation_errors.map((error, index) => (
                <div key={index} className="text-xs text-red-600 flex items-center space-x-1">
                  <AlertCircle className="w-3 h-3" />
                  <span>{error}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    )
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Créer un post</DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel - Composer */}
          <div className="space-y-4">
            {/* Platform Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Plateformes
              </label>
              <div className="grid grid-cols-2 gap-2">
                {availableChannels.map((channel) => {
                  const config = platformConfigs[channel.platform as keyof typeof platformConfigs]
                  const isSelected = selectedPlatforms.includes(channel.platform)
                  const isDisabled = (config as any)?.disabled
                  
                  return (
                    <button
                      key={channel.id}
                      onClick={() => !isDisabled && togglePlatform(channel.platform)}
                      disabled={isDisabled}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        isSelected 
                          ? 'border-green-500 bg-green-50' 
                          : 'border-gray-200 hover:border-gray-300'
                      } ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      <div className="flex items-center space-x-2">
                        <img src={channel.logo} alt={channel.platform} className="w-5 h-5" />
                        <div className="text-left">
                          <div className="text-sm font-medium capitalize">{channel.platform}</div>
                          <div className="text-xs text-gray-500">{channel.username}</div>
                        </div>
                      </div>
                      {isDisabled && (
                        <div className="text-xs text-blue-600 mt-1">Bientôt disponible</div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contenu
              </label>
              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Rédigez votre post..."
                rows={8}
                className="resize-none"
              />
            </div>

            {/* Media Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Médias (optionnel)
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
                <ImageIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">
                  Glissez vos images ici ou cliquez pour sélectionner
                </p>
                <Button variant="outline" size="sm" className="mt-2">
                  Sélectionner des fichiers
                </Button>
              </div>
            </div>

            {/* Scheduling */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date
                </label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="outline" className="w-full justify-start text-left">
                      <CalendarIcon className="w-4 h-4 mr-2" />
                      {scheduledDate ? scheduledDate.toLocaleDateString('fr-FR') : "Sélectionner une date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={scheduledDate}
                      onSelect={setScheduledDate}
                      disabled={(date) => date < new Date()}
                    />
                  </PopoverContent>
                </Popover>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Heure
                </label>
                <Input
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <Button
                onClick={handleSchedule}
                disabled={loading || !content.trim() || selectedPlatforms.length === 0}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                {loading ? (
                  <div className="w-4 h-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2"></div>
                ) : (
                  <Clock className="w-4 h-4 mr-2" />
                )}
                Planifier
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setShowPreview(!showPreview)}
                disabled={!content || selectedPlatforms.length === 0}
              >
                <Eye className="w-4 h-4 mr-2" />
                Preview
              </Button>
            </div>
          </div>

          {/* Right Panel - Preview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-gray-900">Aperçu des publications</h3>
              {previewLoading && (
                <div className="w-4 h-4 animate-spin rounded-full border-2 border-green-600 border-t-transparent"></div>
              )}
            </div>

            {previews.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {previews.map(renderPreview)}
              </div>
            ) : selectedPlatforms.length > 0 && content ? (
              <div className="text-center text-gray-500 py-8">
                <Sparkles className="w-8 h-8 mx-auto mb-2" />
                <p>Génération des aperçus...</p>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Eye className="w-8 h-8 mx-auto mb-2" />
                <p>Sélectionnez des plateformes et ajoutez du contenu pour voir les aperçus</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}