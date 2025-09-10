"use client"

import type React from "react"

import { useEffect, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { logos } from "@/lib/logos"
import { apiFetch } from "@/lib/api"
import {
  Plus,
  RefreshCw,
  Unlink,
  AlertCircle,
  CheckCircle,
  Clock,
} from "lucide-react"
import { AddChannelDialog } from "@/components/add-channel-dialog"

type ApiAccount = {
  id: string
  platform: string
  username: string
  profile_url?: string | null
  status?: string | null
  authorization_url?: string | null
  updated_at?: string
}

type UiAccount = {
  id: string
  platform: string
  username: string
  status: "connected" | "error" | "re-auth" | "pending_setup"
  lastSync: string
  logo: string
  bgColor: string
  textColor: string
}

const mockAccounts: UiAccount[] = [
  {
    id: "instagram",
    platform: "Instagram",
    username: "@alex_shop_official",
    status: "re-auth",
    lastSync: "5 days ago",
    logo: logos.instagram,
    bgColor: "bg-gradient-to-br from-purple-100 to-pink-100",
    textColor: "text-gray-900",
  },
  {
    id: "youtube",
    platform: "YouTube",
    username: "@AlexShopOfficial",
    status: "connected",
    lastSync: "2 hours ago",
    logo: logos.youtube,
    bgColor: "bg-red-100",
    textColor: "text-gray-900",
  },
  {
    id: "linkedin",
    platform: "LinkedIn",
    username: "@alexander-shop",
    status: "pending_setup",
    lastSync: "3 hours ago",
    logo: logos.linkedin,
    bgColor: "bg-blue-100",
    textColor: "text-gray-900",
  },
  {
    id: "x",
    platform: "X (Twitter)",
    username: "@alex_shop",
    status: "error",
    lastSync: "1 day ago",
    logo: logos.x,
    bgColor: "bg-gray-100",
    textColor: "text-gray-900",
  },
  {
    id: "whatsapp",
    platform: "WhatsApp",
    username: "+1 (555) 123-4567",
    status: "connected",
    lastSync: "1 hour ago",
    logo: logos.whatsapp,
    bgColor: "bg-green-100",
    textColor: "text-gray-900",
  },
]

const getStatusIcon = (status: string) => {
  switch (status) {
    case "connected":
      return <CheckCircle className="w-4 h-4 text-green-600" />
    case "error":
      return <AlertCircle className="w-4 h-4 text-red-600" />
    case "re-auth":
      return <Clock className="w-4 h-4 text-orange-600" />
    case "pending_setup":
      return <Clock className="w-4 h-4 text-blue-600" />
    default:
      return null
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "connected":
      return (
        <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200">
          Connected
        </Badge>
      )
    case "error":
      return (
        <Badge variant="destructive" className="bg-red-100 text-red-800 border-red-200">
          Error
        </Badge>
      )
    case "re-auth":
      return (
        <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-200">
          Re-auth
        </Badge>
      )
    case "pending_setup":
      return (
        <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
          Setup pending
        </Badge>
      )
    default:
      return null
  }
}

export default function SocialAccountsPage() {
  const [accounts, setAccounts] = useState<UiAccount[]>(mockAccounts)
  const [addOpen, setAddOpen] = useState(false)

  useEffect(() => {
    ;(async () => {
      try {
        const data = await apiFetch("/api/social-accounts/") as ApiAccount[]
        const mapped: UiAccount[] = data.map((acc) => {
          const platform = acc.platform.toLowerCase()
          const branding = getBranding(platform)
          const status = (acc.status as UiAccount["status"]) || (platform === "linkedin" ? "pending_setup" : "connected")
          return {
            id: acc.id,
            platform: capitalize(platform),
            username: acc.username,
            status,
            lastSync: new Date(acc.updated_at || Date.now()).toLocaleString(),
            logo: branding.logo,
            bgColor: branding.bg,
            textColor: "text-gray-900",
          }
        })
        if (mapped.length > 0) setAccounts(mapped)
      } catch (e) {
        console.warn("/social-accounts load failed, using mock", e)
      }
    })()
  }, [])

  const availablePlatforms = useMemo(() => [
    { id: "instagram", name: "Instagram", icon: logos.instagram },
    { id: "whatsapp", name: "WhatsApp", icon: logos.whatsapp },
    { id: "reddit", name: "Reddit", icon: "/logos/reddit.svg" },
    { id: "linkedin", name: "LinkedIn", icon: logos.linkedin },
  ], [])

  const handleConnect = (platformId: string) => {
    console.log("[v0] social_connect_click", { platform: platformId })
    setAccounts((prev) =>
      prev.map((account) =>
        account.id === platformId ? { ...account, status: "connected" as const, lastSync: "Just now" } : account,
      ),
    )
  }

  const handleDisconnect = (platformId: string) => {
    console.log("[v0] social_disconnect_click", { platform: platformId })
    // Remove account from list
    setAccounts((prev) => prev.filter((account) => account.id !== platformId))
  }

  const handleReSync = (platformId: string) => {
    console.log("[v0] social_resync_click", { platform: platformId })
    // Simulate re-sync
    setAccounts((prev) =>
      prev.map((account) => (account.id === platformId ? { ...account, lastSync: "Just now" } : account)),
    )
  }

  const handleAddAccount = () => setAddOpen(true)

  const startAuth = async (_platform: string) => {}

  function getBranding(platform: string): { logo: string; bg: string } {
    switch (platform) {
      case "instagram":
        return { logo: logos.instagram, bg: "bg-gradient-to-br from-purple-100 to-pink-100" }
      case "youtube":
        return { logo: logos.youtube, bg: "bg-red-100" }
      case "linkedin":
        return { logo: logos.linkedin, bg: "bg-blue-100" }
      case "x":
      case "twitter":
        return { logo: logos.x, bg: "bg-gray-100" }
      case "whatsapp":
        return { logo: logos.whatsapp, bg: "bg-green-100" }
      case "reddit":
        return { logo: "/logos/reddit.svg", bg: "bg-orange-50" }
      default:
        return { logo: logos.all, bg: "bg-gray-100" }
    }
  }

  function capitalize(s: string): string {
    if (!s) return s
    if (s === "x") return "X (Twitter)"
    return s.charAt(0).toUpperCase() + s.slice(1)
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900 mb-2">Social Accounts</h1>
        <p className="text-gray-600">Connect and manage your social media accounts</p>
      </div>

      {/* Accounts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts.map((account) => (
          <Card key={account.id} className="overflow-hidden hover:shadow-md transition-shadow">
            {/* Header with platform branding */}
            <div className={`${account.bgColor} ${account.textColor} p-4`}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <img src={account.logo} alt={`${account.platform} logo`} className="w-6 h-6" />
                  <div>
                    <h3 className="font-semibold">{account.platform}</h3>
                    <p className="text-sm opacity-90">{account.username}</p>
                  </div>
                </div>
                {getStatusIcon(account.status)}
              </div>
            </div>

            {/* Content */}
            <CardContent className="p-4">
              <div className="space-y-4">
                {/* Status and Last Sync */}
                <div className="flex items-center justify-between">
                  {getStatusBadge(account.status)}
                  <span className="text-sm text-gray-500">{account.lastSync}</span>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {account.status === "connected" && (
                    <>
                      <Button variant="outline" size="sm" onClick={() => handleReSync(account.id)} className="flex-1">
                        <RefreshCw className="w-4 h-4 mr-1" />
                        Re-sync
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDisconnect(account.id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Unlink className="w-4 h-4 mr-1" />
                        Disconnect
                      </Button>
                    </>
                  )}

                  {(account.status === "error" || account.status === "re-auth") && (
                    <Button
                      onClick={() => handleConnect(account.id)}
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    >
                      {account.status === "re-auth" ? "Re-authenticate" : "Reconnect"}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Add Account Card */}
        <Card className="border-2 border-dashed border-gray-300 hover:border-emerald-400 transition-colors cursor-pointer group">
          <CardContent
            className="p-8 flex flex-col items-center justify-center text-center h-full min-h-[200px]"
            onClick={handleAddAccount}
          >
            <div className="w-12 h-12 rounded-full bg-emerald-100 group-hover:bg-emerald-200 flex items-center justify-center mb-4 transition-colors">
              <Plus className="w-6 h-6 text-emerald-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Add Social Profile</h3>
            <p className="text-sm text-gray-500">Enhance your presence</p>
          </CardContent>
        </Card>
      </div>

      <AddChannelDialog open={addOpen} onOpenChange={setAddOpen} />
    </div>
  )
}
