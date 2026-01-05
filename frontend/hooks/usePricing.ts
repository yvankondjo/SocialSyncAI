"use client"

import { useState, useEffect } from "react"
import { useAuth } from "./useAuth"
import { ApiClient } from "@/lib/api"

export interface PricingPlan {
  id: string
  name: string
  description?: string
  price: number
  currency: string
  interval: string
  interval_count: number
  features: Record<string, boolean>
  credits_monthly: number
  max_ai_calls_per_batch: number
  storage_quota_mb: number
  trial_duration_days?: number
  source: string
  stripe_price_id?: string
  whop_product_id?: string
}

export interface PublicPricingResponse {
  plans: PricingPlan[]
  stripe_enabled: boolean
  whop_enabled: boolean
  currency: string
  updated_at: string
}

export interface UserSubscription {
  id: string
  status: string
  current_period_end: string
  plan: {
    name: string
    price_eur: number
    credits_included: number
  }
  can_upgrade: boolean
  days_until_renewal?: number
  trial_days_remaining?: number
}

export interface SubscriptionPlan {
  id: string
  name: string
  price_eur: number
  credits_included: number
  max_ai_calls_per_batch: number
  trial_duration_days?: number
  storage_quota_mb: number
  features: Record<string, boolean>
  stripe_price_id?: string
  whop_product_id?: string
  is_active: boolean
  is_trial: boolean
  created_at?: string
  updated_at?: string
  product?: any
  prices?: any[]
}

export interface CreditsBalance {
  credits_balance: number
  plan_credits: number
  credits_used_this_month: number
  last_refill_at: string
  subscription_id?: string
}

export function usePricing() {
  const [pricing, setPricing] = useState<PublicPricingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPricing = async () => {
    try {
      setLoading(true)
      // Note: L'API pricing publique ne nécessite pas d'authentification
      const data = await ApiClient.getPublic("/api/subscriptions/public/pricing")
      setPricing(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPricing()
  }, [])

  return { pricing, loading, error, refetch: fetchPricing }
}

export function useSubscriptionPlans() {
  const { user } = useAuth()
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPlans = async () => {
    if (!user) return

    try {
      setLoading(true)
      const data = await ApiClient.get("/api/subscriptions/plans")
      setPlans(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      fetchPlans()
    }
  }, [user])

  return { plans, loading, error, refetch: fetchPlans }
}

export function useUserSubscription() {
  const { user } = useAuth()
  const [subscription, setSubscription] = useState<UserSubscription | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSubscription = async () => {
    if (!user) return

    try {
      setLoading(true)
      const data = await ApiClient.get("/api/subscriptions/me")
      setSubscription(data)
      setError(null)
    } catch (err) {
      if (err instanceof Error && err.message.includes("404")) {
        setSubscription(null)
      } else {
        setError(err instanceof Error ? err.message : "Erreur inconnue")
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      fetchSubscription()
    }
  }, [user])

  return { subscription, loading, error, refetch: fetchSubscription }
}

export function useCredits() {
  const { user } = useAuth()
  const [credits, setCredits] = useState<CreditsBalance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCredits = async () => {
    if (!user) return

    try {
      setLoading(true)
      const data = await ApiClient.get("/api/subscriptions/credits/balance")
      setCredits(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      fetchCredits()
    }
  }, [user])

  return { credits, loading, error, refetch: fetchCredits }
}
