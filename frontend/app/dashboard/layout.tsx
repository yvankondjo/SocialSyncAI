'use client'

import { AuthGuard } from '@/components/AuthGuard'
import { Sidebar } from '@/components/sidebar-new'
import { Header } from '@/components/header'
import { useSidebarStore } from '@/hooks/useSidebarStore'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useSidebarStore()
  const pathname = usePathname()

  // Pages with their own custom headers
  const pagesWithCustomHeader = ['/dashboard/ai-studio']
  const hasCustomHeader = pagesWithCustomHeader.some(page => pathname.startsWith(page))

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
          {!hasCustomHeader && <Header />}
          <div className={cn(
            "flex-1 space-y-3 sm:space-y-4 lg:space-y-6 overflow-auto",
            !hasCustomHeader && "p-3 sm:p-4 lg:p-6"
          )}>
            {children}
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
