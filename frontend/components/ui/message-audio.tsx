import { cn } from "@/lib/utils"
import { PauseCircle, PlayCircle, Volume2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState } from "react"

interface MessageAudioProps {
  label?: string
  className?: string
}

export function MessageAudio({ label = "Audio reçu", className }: MessageAudioProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border border-dashed border-muted-foreground/40 bg-muted/40 px-4 py-3 transition-all",
        isHovered ? "border-muted-foreground/80 bg-muted/60" : "",
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-full bg-primary/10 animate-pulse" />
        <PlayCircle className="relative z-10 h-10 w-10 text-primary" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-xs text-muted-foreground">Tap to listen · 0:48</p>
      </div>
      <Button variant="ghost" size="icon" className="text-muted-foreground">
        <Volume2 className="h-5 w-5" />
      </Button>
      <Button variant="ghost" size="icon" className="text-muted-foreground">
        <PauseCircle className="h-5 w-5" />
      </Button>
    </div>
  )}

