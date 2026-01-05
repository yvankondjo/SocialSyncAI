"use client"

import { useMemo } from "react"

interface TokenExpiryBarProps {
  tokenExpiresAt: string
  className?: string
}

export function TokenExpiryBar({ tokenExpiresAt, className = "" }: TokenExpiryBarProps) {
  const { daysRemaining, percentage, color, status } = useMemo(() => {
    const now = new Date()
    const expiryDate = new Date(tokenExpiresAt)
    const diffTime = expiryDate.getTime() - now.getTime()
    const daysRemaining = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    // Calculer le pourcentage (60 jours = 100%, 0 jours = 0%)
    const maxDays = 60
    const percentage = Math.max(0, Math.min(100, (daysRemaining / maxDays) * 100))
    
    // Déterminer la couleur et le statut
    let color = "bg-green-500"
    let status = "excellent"
    
    if (daysRemaining <= 0) {
      color = "bg-red-500"
      status = "expired"
    } else if (daysRemaining <= 7) {
      color = "bg-red-400"
      status = "critical"
    } else if (daysRemaining <= 14) {
      color = "bg-orange-400"
      status = "warning"
    } else if (daysRemaining <= 30) {
      color = "bg-yellow-400"
      status = "attention"
    } else {
      color = "bg-green-500"
      status = "excellent"
    }
    
    return { daysRemaining, percentage, color, status }
  }, [tokenExpiresAt])

  const getStatusText = () => {
    if (daysRemaining <= 0) return "Token expiré"
    if (daysRemaining === 1) return "1 jour restant"
    return `${daysRemaining} jours restants`
  }

  const getStatusColor = () => {
    switch (status) {
      case "expired":
        return "text-red-600"
      case "critical":
        return "text-red-600"
      case "warning":
        return "text-orange-600"
      case "attention":
        return "text-yellow-600"
      default:
        return "text-green-600"
    }
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
        <span className="text-gray-500">
          Expire le {new Date(tokenExpiresAt).toLocaleDateString('fr-FR')}
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      {status === "critical" && (
        <p className="text-xs text-red-600 font-medium">
          ⚠️ Reconnectez-vous rapidement pour éviter l'interruption du service
        </p>
      )}
      
      {status === "warning" && (
        <p className="text-xs text-orange-600 font-medium">
          ⚠️ Pensez à reconnecter votre compte bientôt
        </p>
      )}
    </div>
  )
}
