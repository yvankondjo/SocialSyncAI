'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const aiStudioSubItems = [
  { id: "prompt-tuning", label: "Prompt Tuning", href: "/dashboard/ai-studio/prompt-tuning", isNew: false },
  { id: "data", label: "Data", href: "/dashboard/ai-studio/data", isNew: false },
  { id: "qa-examples", label: "Q&A Examples", href: "/dashboard/ai-studio/qa-examples", isNew: false },
]

export default function AIStudioLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()


  return (
    <div className="h-full flex flex-col bg-background">
      {/* AI Studio Header - Fixed */}
      <div className="flex-shrink-0 border-b border-border bg-background px-6 py-4 shadow-soft">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">AI Studio</h1>
            <p className="text-muted-foreground mt-1 text-sm">Configure and optimize your AI assistant</p>
          </div>
        </div>
      </div>

      {/* Sub Navigation - Fixed */}
      <div className="flex-shrink-0 border-b border-border bg-background px-6 py-3">
        <div className="flex space-x-1">
          {aiStudioSubItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-4 py-2 rounded-md text-sm transition-all hover-lift',
                pathname === item.href
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium shadow-soft'
                  : 'text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50'
              )}
            >
              <span>{item.label}</span>
              {item.isNew && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-primary text-primary-foreground rounded-full">
                  NEW
                </span>
              )}
            </Link>
          ))}
        </div>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-auto bg-muted/30">
        {children}
      </div>
    </div>
  )
}