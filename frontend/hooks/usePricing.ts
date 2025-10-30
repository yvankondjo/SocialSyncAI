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
  // Open-Source V3.0: No pricing plans, everything is unlimited
  const [pricing] = useState<PublicPricingResponse | null>(null)
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)

  const fetchPricing = async () => {
    // No-op in open-source version
  }

  return { pricing, loading, error, refetch: fetchPricing }
}

export function useSubscriptionPlans() {
  // Open-Source V3.0: No subscription plans, everything is unlimited
  const [plans] = useState<SubscriptionPlan[]>([])
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)

  const fetchPlans = async () => {
    // No-op in open-source version
  }

  return { plans, loading, error, refetch: fetchPlans }
}

export function useUserSubscription() {
  const { user } = useAuth()
  // Open-Source V3.0: Return unlimited subscription data
  const [subscription] = useState<UserSubscription | null>(
    user ? {
      id: 'open-source',
      status: 'active',
      current_period_end: '2099-12-31T23:59:59Z',
      plan: {
        name: 'Open Source',
        price_eur: 0,
        credits_included: Infinity,
      },
      can_upgrade: false,
    } : null
  )
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)

  const fetchSubscription = async () => {
    // No-op in open-source version
  }

  return { subscription, loading, error, refetch: fetchSubscription }
}

export function useCredits() {
  const { user } = useAuth()
  // Open-Source V3.0: Return unlimited credits
  const [credits] = useState<CreditsBalance | null>(
    user ? {
      credits_balance: Infinity,
      plan_credits: Infinity,
      credits_used_this_month: 0,
      last_refill_at: new Date().toISOString(),
    } : null
  )
  const [loading] = useState(false)
  const [error] = useState<string | null>(null)

  const fetchCredits = async () => {
    // No-op in open-source version
  }

  return { credits, loading, error, refetch: fetchCredits }
}
