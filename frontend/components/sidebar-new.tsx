"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { useAuth } from "@/hooks/useAuth"
import { useSidebarStore } from '@/hooks/useSidebarStore'
import { cn } from "@/lib/utils"
import {
  ChevronDown,
  Crown,
  HardDrive,
  LogOut,
  Plus,
  Sparkles,
  X
} from "lucide-react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"

const navigation = [
  {
    name: "Calendar",
    href: "/dashboard/calendar",
    logoPath: "/logos/logo-activity.svg",
    type: "main"
  },
  {
    name: "AI Studio",
    href: "/dashboard/ai-studio",
    logoPath: "/logos/logo-playground.svg",
    type: "main"
  },
  {
    name: "Activity",
    href: "/dashboard/activity",
    logoPath: "/logos/logo-activity.svg",
    type: "section",
    children: [
      { name: "Chat", href: "/dashboard/activity/chat", type: "sub" },
      { name: "Comments", href: "/dashboard/activity/comments", type: "sub" }
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
      { name: "Playground", href: "/dashboard/playground", type: "sub" },
      { name: "AI", href: "/dashboard/settings/ai", type: "sub" }
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

  // Open-Source V3.0: Unlimited credits, no API calls needed
  const subscription = {
    plan_name: "Open Source",
    credits_balance: Infinity,
    credits_included: Infinity,
  }

  const storageUsage = {
    used_mb: 0,
    quota_mb: Infinity,
    percentage_used: 0,
  }

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }))
  }

  const handleSignOut = async () => {
    await signOut()
  }

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
                alt="SocialSyncAI"
                width={20}
                height={20}
                className="w-5 h-5"
              />
            </div>
            <span className="font-semibold text-sidebar-foreground">SocialSyncAI</span>
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
                      const hasIcon = childLogoPath && !["Chat", "DATA", "FAQ", "AI"].includes(child.name)

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
                        <Sparkles className="w-4 h-4 text-yellow-500" />
                        <span>Crédits</span>
                      </div>
                      <span className="font-bold text-green-600">
                        ∞ Illimités
                      </span>
                    </div>
                    <Progress
                      value={100}
                      className="h-2 bg-green-500/20"
                    />
                  </div>
                )}

                {/* Storage */}
                {storageUsage && (
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <HardDrive className="w-4 h-4 text-blue-500" />
                        <span>Storage</span>
                      </div>
                      <span className="font-bold text-green-600">
                        ∞ Illimité
                      </span>
                    </div>
                    <Progress
                      value={100}
                      className="h-2 bg-green-500/20"
                    />
                  </div>
                )}

              </div>
            )}

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