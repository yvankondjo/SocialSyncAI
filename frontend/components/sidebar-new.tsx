"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useSidebarStore } from '@/hooks/useSidebarStore'
import Image from "next/image"
import { useAuth } from "@/hooks/useAuth"
import { ApiClient } from "@/lib/api"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  X,
  ChevronDown,
  Plus,
  LogOut,
  User,
  Settings as SettingsIcon,
  Crown,
  Sparkles,
  HardDrive,
} from "lucide-react"

const navigation = [
  {
    name: "Playground",
    href: "/dashboard/playground",
    logoPath: "/logos/logo-playground.svg",
    type: "main"
  },
  {
    name: "Activity",
    href: "/dashboard/activity",
    logoPath: "/logos/logo-activity.svg",
    type: "section",
    children: [
      { name: "Chat", href: "/dashboard/activity/chat", type: "sub" }
    ]
  },
  {
    name: "Analytics",
    href: "/dashboard/analytics",
    logoPath: "/logos/logo-analytic.svg",
    type: "main"
  },
  {
    name: "Sources",
    href: "/dashboard/sources",
    logoPath: "/logos/logo-sources.svg",
    type: "section",
    children: [
      { name: "DATA", href: "/dashboard/sources/data", type: "sub" },
      { name: "FAQ", href: "/dashboard/sources/faq", type: "sub" }
    ]
  },
  {
    name: "Connect",
    href: "/dashboard/connect",
    logoPath: "/logos/logo-connect.svg",
    type: "main"
  },
  {
    name: "Settings",
    href: "/dashboard/settings",
    logoPath: "/logos/logo-settings.svg",
    type: "section",
    children: [
      { name: "AI", href: "/dashboard/settings/ai", type: "sub" },
      { name: "Chat Interface", href: "/dashboard/settings/chat-interface", type: "sub" },
      { name: "Custom domains", href: "/dashboard/settings/custom-domains", type: "sub" }
    ]
  }
]

export function Sidebar() {
  const { isCollapsed, toggleCollapsed } = useSidebarStore()
  const { user, signOut } = useAuth()
  const pathname = usePathname()
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Activity: true,
    Sources: false,
    Settings: false,
  })
  const [subscription, setSubscription] = useState<any>(null)
  const [storageUsage, setStorageUsage] = useState<any>(null)
  const [availableModels, setAvailableModels] = useState<any[]>([])

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }))
  }

  const handleSignOut = async () => {
    await signOut()
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        const [subData, storageData, modelsData] = await Promise.all([
          ApiClient.get('/api/subscriptions/me'),
          ApiClient.get('/api/subscriptions/storage/usage'),
          ApiClient.get('/api/subscriptions/models')
        ])
        setSubscription(subData)
        setStorageUsage(storageData)
        setAvailableModels(modelsData)
      } catch (error) {
        console.error("Erreur chargement données:", error)
      }
    }

    loadData()
  }, [])

  return (
    <div
      className={cn(
        "flex flex-col h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 fixed left-0 top-0 z-30",
        isCollapsed ? "w-16" : "w-64",
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center overflow-hidden">
              <Image
                src="/logos/logo-connect.svg"
                alt="ConversAI"
                width={20}
                height={20}
                className="w-5 h-5"
              />
            </div>
            <span className="font-semibold text-sidebar-foreground">ConversAI</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleCollapsed}
          className="text-sidebar-foreground hover:bg-sidebar-accent"
        >
          {isCollapsed ? <Plus className="w-4 h-4" /> : <X className="w-4 h-4" />}
        </Button>
      </div>

      {/* Search */}
      {!isCollapsed && (
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search... (⌘K)"
              className="w-full pl-10 pr-4 py-2 bg-input border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          if (item.type === "main") {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link key={item.name} href={item.href}>
                <div
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-primary text-sidebar-primary-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    isCollapsed && "justify-center",
                  )}
                >
                  <Image
                    src={item.logoPath}
                    alt={item.name}
                    width={20}
                    height={20}
                    className="w-5 h-5 flex-shrink-0"
                  />
                  {!isCollapsed && <span>{item.name}</span>}
                </div>
              </Link>
            )
          }

          if (item.type === "section") {
            const isSectionActive = pathname.startsWith(item.href)
            const isExpanded = expandedSections[item.name]

            return (
              <div key={item.name}>
                {/* Section Header */}
                <button
                  onClick={() => toggleSection(item.name)}
                  className={cn(
                    "flex items-center justify-between w-full px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isSectionActive
                      ? "bg-sidebar-primary/50 text-sidebar-primary-foreground"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    isCollapsed && "justify-center",
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Image
                      src={item.logoPath}
                      alt={item.name}
                      width={20}
                      height={20}
                      className="w-5 h-5 flex-shrink-0"
                    />
                    {!isCollapsed && <span>{item.name}</span>}
                  </div>
                  {!isCollapsed && (
                    <ChevronDown
                      className={cn(
                        "w-4 h-4 transition-transform duration-200",
                        isExpanded ? "rotate-180" : ""
                      )}
                    />
                  )}
                </button>

                {/* Section Children */}
                {isExpanded && !isCollapsed && item.children && (
                  <div className="ml-6 mt-1 space-y-1">
                    {item.children.map((child) => {
                      const isChildActive = pathname === child.href || pathname.startsWith(child.href + "/")
                      const childLogoPath = (child as any).logoPath
                      const hasIcon = childLogoPath && !["Chat", "DATA", "FAQ", "AI", "Chat Interface", "Custom domains"].includes(child.name)

                      return (
                        <Link key={child.name} href={child.href}>
                          <div
                            className={cn(
                              "flex items-center px-3 py-1.5 rounded-lg text-sm transition-colors",
                              isChildActive
                                ? "bg-sidebar-primary text-sidebar-primary-foreground font-medium"
                                : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                            )}
                          >
                            {hasIcon && childLogoPath ? (
                              <Image
                                src={childLogoPath}
                                alt={child.name}
                                width={16}
                                height={16}
                                className="w-4 h-4 flex-shrink-0 mr-3"
                              />
                            ) : (
                              <div className="w-4 h-4 flex-shrink-0 mr-3"></div>
                            )}
                            <span>{child.name}</span>
                          </div>
                        </Link>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          }

          return null
        })}
      </nav>

      {/* User Profile Menu - En bas de la sidebar */}
      <div className="mt-auto border-t border-sidebar-border p-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start hover:bg-sidebar-accent",
                isCollapsed ? "px-2" : "px-3"
              )}
            >
              <div className="flex items-center gap-3 w-full">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.user_metadata?.avatar_url} />
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {user?.email?.charAt(0)?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                {!isCollapsed && (
                  <div className="flex-1 text-left overflow-hidden">
                    <p className="text-sm font-medium truncate">{user?.user_metadata?.full_name || 'Utilisateur'}</p>
                    <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                  </div>
                )}
                {!isCollapsed && <ChevronDown className="h-4 w-4 text-muted-foreground" />}
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent 
            className="w-80" 
            align={isCollapsed ? "end" : "end"}
            side="top"
          >
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {user?.user_metadata?.full_name || 'Utilisateur'}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.email}
                </p>
              </div>
            </DropdownMenuLabel>
            
            <DropdownMenuSeparator />

            {/* Plan Info */}
            {subscription && (
              <div className="px-2 py-2">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Crown className="w-4 h-4 text-yellow-500" />
                    <span className="text-sm font-medium">
                      Plan {subscription.plan?.name || subscription.plan_name || "Active"}
                    </span>
                  </div>
                  <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                    Active
                  </Badge>
                </div>

                {/* Credits */}
                {subscription.credits_balance !== undefined && (
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        <span>Crédits</span>
                      </div>
                      <span className="font-bold">
                        {subscription.credits_balance} / {subscription.credits_included}
                      </span>
                    </div>
                    <Progress 
                      value={(subscription.credits_balance / subscription.credits_included) * 100} 
                      className="h-2"
                    />
                  </div>
                )}

                {/* Storage */}
                {storageUsage && (
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4" />
                        <span>Storage</span>
                      </div>
                      <span className="font-bold">
                        {storageUsage.used_mb?.toFixed(1)} / {storageUsage.quota_mb} MB
                      </span>
                    </div>
                    <Progress 
                      value={storageUsage.percentage_used || 0} 
                      className="h-2"
                    />
                  </div>
                )}

                {/* Crédits par modèle */}
                {subscription.credits_balance !== undefined && availableModels.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-medium text-muted-foreground mb-2">
                      Crédits restants par modèle
                    </div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {availableModels.slice(0, 5).map((model) => {
                        const remainingCalls = Math.floor(subscription.credits_balance / model.credits_cost)
                        return (
                          <div key={model.id} className="flex items-center justify-between text-xs">
                            <span className="truncate flex-1">{model.name}</span>
                            <span className="text-muted-foreground ml-2">
                              {remainingCalls} appels
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}

            <DropdownMenuSeparator />

            <DropdownMenuItem>
              <Crown className="mr-2 h-4 w-4" />
              <span>Passer au plan supérieur</span>
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem onClick={handleSignOut} className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Se déconnecter</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}