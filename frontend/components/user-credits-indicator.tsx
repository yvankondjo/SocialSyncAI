"use client"

import { useUserSubscription, useCredits } from "@/hooks"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { HardDrive, Sparkles, Crown } from "lucide-react"
import { cn } from "@/lib/utils"

export function UserCreditsIndicator({ isCollapsed }: { isCollapsed: boolean }) {
  const { subscription, loading: subLoading } = useUserSubscription()
  const { credits, loading: creditsLoading } = useCredits()

  const isLoading = subLoading || creditsLoading

  if (isLoading || !subscription || !credits) {
    return null
  }

  const creditsPercentage = credits.plan_credits > 0 ? (credits.credits_balance / credits.plan_credits) * 100 : 0
  const creditColor =
    creditsPercentage > 50 ? "text-green-500" :
    creditsPercentage > 20 ? "text-orange-500" :
    "text-red-500"

  if (isCollapsed) {
    return (
      <div className="p-2 space-y-2">
        {/* Cercle crédits collapsed */}
        <div className="flex items-center justify-center">
          <div className="relative w-10 h-10">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="20"
                cy="20"
                r="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                className="text-gray-700"
              />
              <circle
                cx="20"
                cy="20"
                r="16"
                fill="none"
                stroke="currentColor"
                strokeWidth="4"
                className={cn(creditColor, "transition-all")}
                strokeDasharray={`${2 * Math.PI * 16}`}
                strokeDashoffset={`${2 * Math.PI * 16 * (1 - creditsPercentage / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className={cn("w-4 h-4", creditColor)} />
            </div>
          </div>
        </div>

        {/* Plan badge collapsed */}
        <div className="flex items-center justify-center">
          <Crown className="w-4 h-4 text-yellow-500" />
        </div>
      </div>
    )
  }

  return (
    <Card className="border-t border-sidebar-border rounded-none bg-sidebar/50">
      <CardContent className="p-4 space-y-3">
        {/* Plan Badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Crown className="w-4 h-4 text-yellow-500" />
            <span className="text-sm font-medium">
              Plan {subscription.plan?.name || "Active"}
            </span>
          </div>
          <Badge
            variant="outline"
            className={cn(
              "border-yellow-500/20",
              subscription.status === 'active' ? "bg-green-500/10 text-green-500 border-green-500/20" :
              subscription.status === 'trialing' ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
              subscription.status === 'cancelled' ? "bg-red-500/10 text-red-500 border-red-500/20" :
              "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
            )}
          >
            {subscription.status === 'active' && 'Actif'}
            {subscription.status === 'trialing' && 'Essai'}
            {subscription.status === 'cancelled' && 'Annulé'}
            {!['active', 'trialing', 'cancelled'].includes(subscription.status || '') && 'Actif'}
          </Badge>
        </div>

        {/* Credits Indicator */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <Sparkles className={cn("w-4 h-4", creditColor)} />
              <span className="font-medium">Crédits</span>
            </div>
            <span className={cn("font-bold", creditColor)}>
              {Math.round(creditsPercentage)}%
            </span>
          </div>
          <div className="relative">
            <Progress
              value={creditsPercentage}
              className={cn(
                "h-2",
                creditsPercentage > 50 ? "[&>div]:bg-green-500" :
                creditsPercentage > 20 ? "[&>div]:bg-orange-500" :
                "[&>div]:bg-red-500"
              )}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            {credits.credits_balance} / {credits.plan_credits} crédits restants
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

