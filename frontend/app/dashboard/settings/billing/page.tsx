"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  CreditCard,
  Calendar,
  Zap,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Settings
} from "lucide-react"
import { useAuth, useUserSubscription, useCredits, useSubscriptionPlans } from "@/hooks"
import { ApiClient } from "@/lib/api"

export default function BillingPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { subscription, loading: subLoading, error: subError, refetch: refetchSub } = useUserSubscription()
  const { credits, loading: creditsLoading, error: creditsError, refetch: refetchCredits } = useCredits()
  const { plans, loading: plansLoading } = useSubscriptionPlans()

  const [cancelling, setCancelling] = useState(false)
  const [upgrading, setUpgrading] = useState(false)

  const handleCancelSubscription = async () => {
    if (!user || !subscription) return

    setCancelling(true)
    try {
      await ApiClient.post('/api/stripe/cancel-subscription')

      await refetchSub()
      alert("Subscription cancelled successfully. It will remain active until the end of the current billing period.")
    } catch (error) {
      alert(`Erreur lors de l'annulation: ${error instanceof Error ? error.message : 'Erreur inconnue'}`)
    } finally {
      setCancelling(false)
    }
  }

  const handleUpgrade = async (priceId: string) => {
    if (!user) return

    setUpgrading(true)
    try {
      const data = await ApiClient.post('/api/stripe/create-checkout-session', {
        price_id: priceId,
        success_url: `${window.location.origin}/dashboard/settings/billing?upgrade=success`,
        cancel_url: `${window.location.origin}/dashboard/settings/billing`,
      })

      window.location.href = data.checkout_url
    } catch (error) {
      alert(`Erreur lors de la mise à niveau: ${error instanceof Error ? error.message : 'Erreur inconnue'}`)
    } finally {
      setUpgrading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  if (subLoading || creditsLoading || plansLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (subError || creditsError) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Error loading billing data. Please try again.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Billing & Subscription</h1>
          <p className="text-muted-foreground mt-2">
            Manage your subscription and view your usage
          </p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Aperçu</TabsTrigger>
          <TabsTrigger value="usage">Utilisation</TabsTrigger>
          <TabsTrigger value="plans">Changer de plan</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Current Subscription */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CreditCard className="w-5 h-5" />
                <span>Current Subscription</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {subscription ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">{subscription.plan.name}</h3>
                      <p className="text-muted-foreground">
                        {formatCurrency(subscription.plan.price_eur)}/mois
                      </p>
                    </div>
                    <Badge
                      variant={
                        subscription.status === 'active' ? 'default' :
                        subscription.status === 'trialing' ? 'secondary' :
                        subscription.status === 'cancelled' ? 'destructive' : 'outline'
                      }
                    >
                      {subscription.status === 'active' && <CheckCircle className="w-3 h-3 mr-1" />}
                      {subscription.status === 'trialing' && <Clock className="w-3 h-3 mr-1" />}
                      {subscription.status === 'cancelled' && <AlertTriangle className="w-3 h-3 mr-1" />}
                      {subscription.status === 'active' ? 'Actif' :
                       subscription.status === 'trialing' ? 'Essai' :
                       subscription.status === 'cancelled' ? 'Annulé' : subscription.status}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Next billing:</span>
                      <div className="font-medium">
                        {subscription.days_until_renewal !== undefined ?
                          `In ${subscription.days_until_renewal} days` :
                          formatDate(subscription.current_period_end)
                        }
                      </div>
                    </div>

                    {subscription.trial_days_remaining !== undefined && (
                      <div>
                        <span className="text-muted-foreground">Essai restant:</span>
                        <div className="font-medium">
                          {subscription.trial_days_remaining} jours
                        </div>
                      </div>
                    )}
                  </div>

                  {subscription.status === 'cancelled' && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Your subscription is cancelled and will end on {formatDate(subscription.current_period_end)}.
                      </AlertDescription>
                    </Alert>
                  )}

                  {subscription.status !== 'cancelled' && (
                    <div className="flex space-x-2">
                      {subscription.can_upgrade && (
                        <Button
                          variant="outline"
                          onClick={() => document.querySelector('[data-tab="plans"]')?.click()}
                        >
                          <TrendingUp className="w-4 h-4 mr-2" />
                          Changer de plan
                        </Button>
                      )}

                      <Button
                        variant="destructive"
                        onClick={handleCancelSubscription}
                        disabled={cancelling}
                      >
                        {cancelling ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                            Annulation...
                          </>
                        ) : (
                          "Cancel Subscription"
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <CreditCard className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Subscription</h3>
                  <p className="text-muted-foreground mb-4">
                    Choose a plan to start using ConversAI
                  </p>
                  <Button onClick={() => router.push("/pricing")}>
                    View Plans
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Credits Overview */}
          {credits && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5" />
                  <span>Available Credits</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-primary">
                      {credits.credits_balance.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Remaining Credits</div>
                  </div>

                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {credits.plan_credits.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Plan Credits</div>
                  </div>

                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {credits.credits_used_this_month.toLocaleString()}
                    </div>
                    <div className="text-muted-foreground">Utilisés ce mois</div>
                  </div>
                </div>

                <div className="mt-6">
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{
                        width: `${Math.min((credits.credits_balance / credits.plan_credits) * 100, 100)}%`
                      }}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground mt-2">
                    {credits.credits_balance} / {credits.plan_credits} credits used
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Usage History</CardTitle>
              <CardDescription>
                View your recent credit transactions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Settings className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  Detailed history coming soon
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="plans" className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold mb-4">Changer de plan</h2>
            <p className="text-muted-foreground mb-6">
              Choisissez un nouveau plan. Les changements prennent effet immédiatement.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {plans
              .filter(plan => plan.price_eur > (subscription?.plan.price_eur || 0))
              .map((plan) => (
                <Card key={plan.id} className="relative">
                  <CardHeader>
                    <CardTitle>{plan.name}</CardTitle>
                    <CardDescription>{plan.description}</CardDescription>
                    <div className="text-2xl font-bold">
                      {formatCurrency(plan.price_eur)}
                      <span className="text-sm font-normal text-muted-foreground">/mois</span>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• {plan.credits_included.toLocaleString()} crédits/mois</li>
                      <li>• {plan.max_ai_calls_per_batch} messages simultanés</li>
                      <li>• {plan.storage_quota_mb} MB stockage</li>
                      {plan.features.images && <li>• Génération d'images</li>}
                      {plan.features.audio && <li>• Support audio</li>}
                    </ul>
                  </CardContent>

                  <CardFooter>
                    <Button
                      className="w-full"
                      onClick={() => plan.stripe_price_id && handleUpgrade(plan.stripe_price_id)}
                      disabled={upgrading || !plan.stripe_price_id}
                    >
                      {upgrading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                          Mise à niveau...
                        </>
                      ) : (
                        "Mettre à niveau"
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
          </div>

          {plans.filter(plan => plan.price_eur > (subscription?.plan.price_eur || 0)).length === 0 && (
            <div className="text-center py-8">
              <TrendingUp className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Vous avez le meilleur plan !</h3>
              <p className="text-muted-foreground">
                Aucun plan supérieur n'est disponible pour le moment.
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
