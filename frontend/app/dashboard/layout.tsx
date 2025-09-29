'use client'

import { AuthGuard } from '@/components/AuthGuard'
import { Sidebar } from '@/components/sidebar-new'
import { Header } from '@/components/header'
import { useSidebarStore } from '@/hooks/useSidebarStore'
import { cn } from '@/lib/utils'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useSidebarStore()

  return (
    <AuthGuard>
      <div className="flex h-screen bg-background">
        {/* Sidebar - masquée sur mobile, visible sur desktop */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>

        <div
          className={cn(
            "flex-1 flex flex-col transition-all duration-300",
            // Sur desktop: ajustement selon l'état collapsed
            "lg:ml-16 lg:ml-64",
            isCollapsed ? "lg:ml-16" : "lg:ml-64"
          )}
        >
          <Header />
          <div className="flex-1 p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4 lg:space-y-6 overflow-auto">
            {children}
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
