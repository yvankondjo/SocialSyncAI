'use client'

import { AuthGuard } from '@/components/AuthGuard'
import { Sidebar } from '@/components/sidebar-new'
import { Header } from '@/components/header'
import { useSidebarStore } from '@/hooks/useSidebarStore'
import { cn } from '@/lib/utils'

export default function TestNewUILayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useSidebarStore()

  return (
    <AuthGuard>
      <div className="flex h-screen bg-background">
        <Sidebar />
        <div 
          className={cn(
            "flex-1 flex flex-col transition-all duration-300",
            isCollapsed ? "ml-16" : "ml-64"
          )}
        >
          <Header />
          {children}
        </div>
      </div>
    </AuthGuard>
  )
}