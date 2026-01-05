import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { logos } from "@/lib/logos"
import { useCurrentModel } from "@/hooks/useCurrentModel"
import Image from "next/image"

interface ModelDisplayProps {
  modelId?: string
  variant?: 'badge' | 'card' | 'compact'
  showProvider?: boolean
  showLogo?: boolean
  showSelectedLabel?: boolean
  className?: string
}

export const ModelDisplay = ({ 
  modelId,
  variant = 'card',
  showProvider = true,
  showLogo = true,
  showSelectedLabel = true,
  className = ""
}: ModelDisplayProps) => {
  const { currentModel, allModels, isLoading } = useCurrentModel()
  
  // Utiliser le modelId fourni ou celui du hook
  const targetModelId = modelId || currentModel?.id
  const model = allModels.find(m => m.id === targetModelId)
  
  if (isLoading) {
    return (
      <div className={`animate-pulse bg-muted rounded ${variant === 'card' ? 'h-16' : 'h-6'} ${className}`} />
    )
  }
  
  if (!model) {
    return (
      <Badge variant="secondary" className="bg-muted text-muted-foreground">
        Modèle inconnu
      </Badge>
    )
  }

  if (variant === 'badge') {
    return (
      <Badge variant="secondary" className={`bg-primary/10 text-primary ${className}`}>
        {model.name}
      </Badge>
    )
  }

  if (variant === 'compact') {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {showLogo && (
          <div className="w-5 h-5 flex-shrink-0">
            <Image
              src={logos[model.logoKey]}
              alt={model.provider}
              width={20}
              height={20}
              className="w-full h-full object-contain"
            />
          </div>
        )}
        <span className="font-medium text-sm">{model.name}</span>
        {showProvider && (
          <span className="text-xs text-muted-foreground">({model.provider})</span>
        )}
        {showSelectedLabel && (
          <Badge variant="outline" className="text-xs bg-primary/5 text-primary border-primary/20">
            Sélectionné
          </Badge>
        )}
      </div>
    )
  }

  // variant === 'card'
  return (
    <Card className={`border-primary/20 bg-primary/5 ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          {showLogo && (
            <div className="w-10 h-10 flex-shrink-0">
              <Image
                src={logos[model.logoKey]}
                alt={model.provider}
                width={40}
                height={40}
                className="w-full h-full object-contain"
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-sm text-primary">{model.name}</h4>
            {showProvider && (
              <p className="text-xs text-muted-foreground">{model.provider}</p>
            )}
            {showSelectedLabel && (
              <div className="flex items-center gap-1 mt-1">
                <div className="w-2 h-2 bg-primary rounded-full"></div>
                <span className="text-xs text-primary font-medium">Modèle sélectionné</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
