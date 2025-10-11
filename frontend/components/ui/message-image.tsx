import { useState } from 'react'
import { useMediaUrl } from '@/hooks/useMediaUrl'
import { Loader2, ImageIcon, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface MessageImageProps {
  storageObjectName: string
  caption?: string
  className?: string
  maxWidth?: number
  maxHeight?: number
  showCaption?: boolean
  onClick?: () => void
}

export const MessageImage = ({ 
  storageObjectName, 
  caption, 
  className = "",
  maxWidth = 400,
  maxHeight = 300,
  showCaption = true,
  onClick
}: MessageImageProps) => {
  const { signedUrl, loading, error, refetch } = useMediaUrl(storageObjectName)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageError, setImageError] = useState(false)

  const handleImageLoad = () => {
    setImageLoaded(true)
    setImageError(false)
  }

  const handleImageError = () => {
    setImageLoaded(false)
    setImageError(true)
  }

  const handleRetry = () => {
    setImageError(false)
    setImageLoaded(false)
    refetch()
  }

  // État de chargement
  if (loading) {
    return (
      <div 
        className={`bg-muted animate-pulse rounded-lg flex items-center justify-center ${className}`} 
        style={{ width: maxWidth, height: maxHeight }}
      >
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span className="text-sm">Chargement...</span>
        </div>
      </div>
    )
  }

  // État d'erreur (API ou URL signée)
  if (error || !signedUrl) {
    return (
      <div className={`bg-muted border border-dashed rounded-lg p-4 ${className}`}>
        <div className="flex flex-col items-center justify-center text-muted-foreground space-y-2">
          <ImageIcon className="w-8 h-8" />
          <span className="text-sm text-center">
            {error || "Image non disponible"}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRetry}
            className="mt-2"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Réessayer
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div 
        className={`relative overflow-hidden rounded-lg ${onClick ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''}`}
        onClick={onClick}
      >
        {/* Skeleton pendant le chargement de l'image */}
        {!imageLoaded && !imageError && (
          <div 
            className="absolute inset-0 bg-muted animate-pulse flex items-center justify-center"
            style={{ width: maxWidth, height: maxHeight }}
          >
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        )}
        
        {/* Image principale */}
        <img
          src={signedUrl}
          alt={caption || "Image"}
          className={`max-w-full h-auto transition-opacity duration-300 ${
            imageLoaded && !imageError ? 'opacity-100' : 'opacity-0'
          }`}
          style={{ 
            maxWidth, 
            maxHeight,
            ...(imageLoaded ? {} : { position: 'absolute', top: 0, left: 0 })
          }}
          onLoad={handleImageLoad}
          onError={handleImageError}
          loading="lazy"
        />
        
        {/* Erreur de chargement d'image */}
        {imageError && (
          <div 
            className="flex items-center justify-center bg-muted border border-dashed rounded-lg"
            style={{ width: maxWidth, height: maxHeight }}
          >
            <div className="flex flex-col items-center text-muted-foreground space-y-2">
              <ImageIcon className="w-8 h-8" />
              <span className="text-sm">Erreur de chargement</span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleRetry}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Réessayer
              </Button>
            </div>
          </div>
        )}
      </div>
      
      {/* Caption */}
      {showCaption && caption && (
        <div className="bg-muted/50 p-2 rounded text-sm text-muted-foreground">
          {caption}
        </div>
      )}
    </div>
  )
}

// Variante compacte pour les aperçus
export const MessageImageCompact = ({ 
  storageObjectName, 
  className = "",
  size = 60,
  onClick
}: {
  storageObjectName: string
  className?: string
  size?: number
  onClick?: () => void
}) => {
  const { signedUrl, loading, error } = useMediaUrl(storageObjectName)
  const [imageLoaded, setImageLoaded] = useState(false)

  if (loading) {
    return (
      <div 
        className={`bg-muted animate-pulse rounded ${className}`}
        style={{ width: size, height: size }}
      />
    )
  }

  if (error || !signedUrl) {
    return (
      <div 
        className={`bg-muted border border-dashed rounded flex items-center justify-center ${className}`}
        style={{ width: size, height: size }}
      >
        <ImageIcon className="w-4 h-4 text-muted-foreground" />
      </div>
    )
  }

  return (
    <div 
      className={`relative overflow-hidden rounded ${onClick ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''} ${className}`}
      style={{ width: size, height: size }}
      onClick={onClick}
    >
      {!imageLoaded && (
        <div className="absolute inset-0 bg-muted animate-pulse" />
      )}
      <img
        src={signedUrl}
        alt="Image"
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          imageLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        onLoad={() => setImageLoaded(true)}
        loading="lazy"
      />
    </div>
  )
}
