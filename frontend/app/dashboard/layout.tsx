'use client'

import { AuthGuard } from '@/components/AuthGuard'
import { Sidebar } from '@/components/sidebar/Sidebar'
import { useSidebarStore } from '@/hooks/useSidebarStore'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { isCollapsed } = useSidebarStore()

  return (
    <AuthGuard>
      <div className="h-screen bg-background">
        <Sidebar />
        <main 
          className={`h-screen flex flex-col overflow-hidden transition-all duration-300 ease-in-out ml-0 ${
            isCollapsed ? 'lg:ml-[72px]' : 'lg:ml-[280px]'
          }`}
        >
          {children}
        </main>
      </div>
    </AuthGuard>
  )
}