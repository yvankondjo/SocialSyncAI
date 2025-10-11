"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Check, Zap, Shield, Users, MessageSquare, Image as ImageIcon, Mic, Database } from "lucide-react"
import { usePricing } from "@/hooks/usePricing"
import { useAuth } from "@/hooks/useAuth"
import { ApiClient } from "@/lib/api"
import { PricingPlan } from "@/hooks/usePricing"

export default function PricingPage() {
  const router = useRouter()
  const { user } = useAuth()
  const { pricing, loading } = usePricing()
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  // Fonction handleStartTrial supprimée - Stripe gère automatiquement les essais
  // via trial_period_days dans les prix

  const handleSubscribe = async (priceId: string) => {
    if (!user) {
      router.push(`/auth/login?redirect=/pricing&plan=${priceId}`)
      return
    }

    setSelectedPlan(priceId)

    try {
      const data = await ApiClient.post('/api/stripe/create-checkout-session', {
        price_id: priceId,
        success_url: `${window.location.origin}/dashboard?payment=success`,
        cancel_url: `${window.location.origin}/pricing`,
      })

      window.location.href = data.checkout_url
    } catch (error) {
      alert(`Erreur lors de la création de la session de paiement: ${error instanceof Error ? error.message : 'Erreur inconnue'}`)
      setSelectedPlan(null)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  const plans = pricing?.plans || []

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-2xl font-bold">ConversAI</span>
            </div>
            <div className="flex items-center space-x-4">
              {user ? (
                <Button variant="outline" onClick={() => router.push("/dashboard")}>
                  Dashboard
                </Button>
              ) : (
                <>
                  <Button variant="ghost" onClick={() => router.push("/auth/login")}>
                    Se connecter
                  </Button>
                  <Button onClick={() => router.push("/")}>
                    Accueil
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12 text-center">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold mb-4">Choisissez le plan parfait pour vous</h1>
          <p className="text-xl text-muted-foreground mb-8">
            Tous les plans incluent 7 jours d'essai gratuit. Annulez à tout moment.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="container mx-auto px-4 pb-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {plans.map((plan) => (
            <PricingCard
              key={plan.id}
              plan={plan}
              onSubscribe={handleSubscribe}
              selectedPlan={selectedPlan}
              user={user}
              isPopular={plan.name.toLowerCase().includes('pro')}
            />
          ))}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto mt-20">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>

          <div className="space-y-6">
            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">How does the free trial work?</h3>
              <p className="text-muted-foreground">
                The free trial lasts 7 days and gives you access to all features of the selected plan.
                No credit card is required to get started. You will only be charged if you continue after the trial period.
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Can I change plans at any time?</h3>
              <p className="text-muted-foreground">
                Yes, you can upgrade to a higher plan at any time. The change takes effect immediately and you will be charged prorated.
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">What happens if I reach my credit limit?</h3>
              <p className="text-muted-foreground">
                If you reach your monthly credit limit, the AI will be temporarily disabled until the next monthly renewal.
                You can upgrade to a higher plan to get more credits.
              </p>
            </div>

            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Can I cancel my subscription?</h3>
              <p className="text-muted-foreground">
                Yes, you can cancel your subscription at any time from your dashboard.
                The cancellation takes effect at the end of your current billing period.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

interface PricingCardProps {
  plan: PricingPlan
  onSubscribe: (priceId: string) => void
  selectedPlan: string | null
  user: any
  isPopular?: boolean
}

function PricingCard({ plan, onSubscribe, selectedPlan, user, isPopular }: PricingCardProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: plan.currency.toUpperCase(),
      minimumFractionDigits: 0,
    }).format(price)
  }

  const getFeatures = (plan: PricingPlan) => {
    const features = []

    if (plan.features.text) features.push({
      icon: MessageSquare,
      text: "AI handling text"
    })

    if (plan.features.images) features.push({
      icon: ImageIcon,
      text: "AI handling images"
    })

    if (plan.features.audio) features.push({
      icon: Mic,
      text: "AI handling audio"
    })

    features.push({
      icon: Zap,
      text: `${plan.credits_monthly.toLocaleString()} credits per month`
    })

    features.push({
      icon: Database,
      text: `${plan.storage_quota_mb} MB storage`
    })

    features.push({
      icon: Users,
      text: `Up to ${plan.max_ai_calls_per_batch} actions messages`
    })

    return features
  }

  const isLoading = selectedPlan === plan.id || selectedPlan === plan.stripe_price_id

  return (
    <Card className={`relative h-full ${isPopular ? 'ring-2 ring-primary shadow-lg' : ''}`}>
      {isPopular && (
        <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">
            Plus populaire
        </Badge>
      )}

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-2xl">{plan.name}</CardTitle>
        <CardDescription className="text-base">{plan.description}</CardDescription>

        <div className="mt-6">
          <div className="text-4xl font-bold">{formatPrice(plan.price)}</div>
          <div className="text-muted-foreground">par {plan.interval}</div>
        </div>

        {plan.trial_duration_days && (
          <Badge variant="secondary" className="mt-4">
            {plan.trial_duration_days} days free trial
          </Badge>
        )}
      </CardHeader>

      <CardContent className="flex-grow">
        <ul className="space-y-4">
          {getFeatures(plan).map((feature, index) => (
            <li key={index} className="flex items-start space-x-3">
              <feature.icon className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
              <span className="text-sm">{feature.text}</span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter className="pt-6">
        <div className="w-full space-y-2">
        <Button
          className="w-full"
          onClick={() => onSubscribe(plan.stripe_price_id!)}
          disabled={isLoading}
          variant={user ? "default" : "outline"}
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
              Chargement...
            </>
          ) : user ? (
            "Subscribe with free trial"
          ) : (
            "Sign in to subscribe"
          )}
        </Button>

          {/* Bouton S'abonner maintenant supprimé - un seul bouton suffit */}
        </div>
      </CardFooter>
    </Card>
  )
}
