"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useSidebarStore } from '@/hooks/useSidebarStore'
import {
  Bot,
  User,
  Search,
  Plus,
  X,
  Clock,
} from "lucide-react"

const navigation = [
  { name: "Playground", href: "/playground", icon: Bot },
  { name: "Activity", href: "/activity", icon: User },
  { name: "Chat", href: "/activity/chat", icon: Bot },
  { name: "Data", href: "/sources/data", icon: Plus },
  { name: "FAQ", href: "/sources/faq", icon: User },
  { name: "Analytics", href: "/analytics", icon: Clock },
  { name: "Connect", href: "/connect", icon: Plus },
  { name: "AI", href: "/settings/ai", icon: Bot },
  { name: "Chat Interface", href: "/settings/chat-interface", icon: Bot },
  { name: "Custom Domains", href: "/settings/custom-domains", icon: User },
  { name: "Settings", href: "/settings", icon: User },
]

export function Sidebar() {
  const { isCollapsed, toggleCollapsed } = useSidebarStore()
  const pathname = usePathname()

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
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
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
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
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
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!isCollapsed && <span>{item.name}</span>}
              </div>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}