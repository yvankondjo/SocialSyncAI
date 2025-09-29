"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useSidebarStore } from '@/hooks/useSidebarStore'
import Image from "next/image"
import {
  Search,
  X,
  ChevronDown,
  Plus,
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
  const pathname = usePathname()
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    Activity: true,
    Sources: false,
    Settings: false,
  })

  const toggleSection = (sectionName: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }))
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
                alt="SocialSync AI"
                width={20}
                height={20}
                className="w-5 h-5"
              />
            </div>
            <span className="font-semibold text-sidebar-foreground">SocialSync AI</span>
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
    </div>
  )
}