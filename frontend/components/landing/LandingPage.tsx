"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, Star, Zap, Shield, Users, MessageSquare, Image as ImageIcon, Mic } from "lucide-react"
import { usePricing } from "@/hooks/usePricing"
import { PricingPlan } from "@/hooks/usePricing"

export function LandingPage() {
  const router = useRouter()
  const { pricing, loading } = usePricing()
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  const handleStartTrial = (planId: string) => {
    setSelectedPlan(planId)
    router.push("/auth/login?redirect=/pricing")
  }

  const handleViewPricing = () => {
    router.push("/pricing")
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
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold">ConversAI</span>
          </div>
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => router.push("/auth/login")}>
              Se connecter
            </Button>
            <Button onClick={handleViewPricing}>
              Voir les tarifs
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            IA Conversationnelle pour WhatsApp & Instagram
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Automatisez vos conversations sociales avec l'intelligence artificielle.
            Répondez instantanément, générez du contenu engageant et boostez votre présence sociale.
          </p>
          <div className="flex items-center justify-center space-x-4 mb-12">
            <Button size="lg" onClick={handleViewPricing} className="px-8">
              <Zap className="w-5 h-5 mr-2" />
              Commencer l'essai gratuit
            </Button>
            <Button variant="outline" size="lg" onClick={() => router.push("/pricing")}>
              Voir les plans
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Réponses Automatiques</h3>
            <p className="text-muted-foreground">
              L'IA répond automatiquement à vos messages 24/7
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <ImageIcon className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Génération d'Images</h3>
            <p className="text-muted-foreground">
              Créez des images uniques avec l'IA pour vos posts
            </p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Gestion Multi-Plateformes</h3>
            <p className="text-muted-foreground">
              WhatsApp, Instagram et plus en un seul endroit
            </p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Choisissez votre plan</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Tous les plans incluent 7 jours d'essai gratuit. Pas de carte bancaire requise pour commencer.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {plans.slice(0, 4).map((plan) => (
            <PricingCard
              key={plan.id}
              plan={plan}
              onSelect={handleStartTrial}
              isPopular={plan.name.toLowerCase().includes('pro')}
              selectedPlan={selectedPlan}
            />
          ))}
        </div>

        <div className="text-center mt-12">
          <Button variant="outline" onClick={handleViewPricing}>
            Voir tous les plans
          </Button>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary/5 py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Prêt à révolutionner vos conversations ?</h2>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Rejoignez des milliers d'entreprises qui utilisent ConversAI pour automatiser leur présence sociale.
          </p>
          <Button size="lg" onClick={handleViewPricing} className="px-8">
            <Star className="w-5 h-5 mr-2" />
            Commencer maintenant
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center space-x-2">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-semibold">ConversAI</span>
          </div>
          <p className="text-center text-muted-foreground mt-4">
            © 2025 ConversAI. Tous droits réservés.
          </p>
        </div>
      </footer>
    </div>
  )
}

interface PricingCardProps {
  plan: PricingPlan
  onSelect: (planId: string) => void
  isPopular?: boolean
  selectedPlan: string | null
}

function PricingCard({ plan, onSelect, isPopular, selectedPlan }: PricingCardProps) {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: plan.currency.toUpperCase(),
      minimumFractionDigits: 0,
    }).format(price)
  }

  const getFeatures = (plan: PricingPlan) => {
    const features = []
    if (plan.features.text) features.push("Réponses texte IA")
    if (plan.features.images) features.push("Génération d'images")
    if (plan.features.audio) features.push("Support audio")
    features.push(`${plan.credits_monthly.toLocaleString()} crédits/mois`)
    features.push(`Jusqu'à ${plan.max_ai_calls_per_batch} messages simultanés`)
    return features
  }

  return (
    <Card className={`relative ${isPopular ? 'ring-2 ring-primary' : ''}`}>
      {isPopular && (
        <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">
          Plus populaire
        </Badge>
      )}

      <CardHeader className="text-center">
        <CardTitle className="text-xl">{plan.name}</CardTitle>
        <CardDescription>{plan.description}</CardDescription>
        <div className="mt-4">
          <span className="text-3xl font-bold">{formatPrice(plan.price)}</span>
          <span className="text-muted-foreground">/{plan.interval}</span>
        </div>
        {plan.trial_duration_days && (
          <Badge variant="secondary" className="mt-2">
            {plan.trial_duration_days} jours d'essai gratuit
          </Badge>
        )}
      </CardHeader>

      <CardContent>
        <ul className="space-y-2">
          {getFeatures(plan).map((feature, index) => (
            <li key={index} className="flex items-center space-x-2">
              <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
              <span className="text-sm">{feature}</span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          onClick={() => onSelect(plan.id)}
          disabled={plan.id === selectedPlan}
        >
          {plan.id === selectedPlan ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
              Chargement...
            </>
          ) : (
            "Commencer l'essai"
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
