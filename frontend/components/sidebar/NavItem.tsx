'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useSidebarStore } from '@/hooks/useSidebarStore'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface NavItemProps {
  icon: LucideIcon
  label: string
  href: string
  badge?: string
  isNew?: boolean
}

export function NavItem({ icon: Icon, label, href, badge, isNew }: NavItemProps) {
  const pathname = usePathname()
  const { isCollapsed } = useSidebarStore()
  
  // Détermine si l'item est actif
  const isActive = pathname === href || 
    (href !== '/dashboard' && pathname.startsWith(href))

  const itemContent = (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 hover-lift group relative',
        isActive
          ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-soft'
          : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
        isCollapsed && 'justify-center px-2'
      )}
      aria-current={isActive ? 'page' : undefined}
    >
      <Icon className={cn(
        'w-5 h-5 flex-shrink-0 transition-all duration-200',
        isCollapsed ? 'w-6 h-6' : 'w-5 h-5'
      )} />
      
      {!isCollapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {(badge || isNew) && (
            <div className="flex items-center gap-1">
              {badge && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-primary/10 text-primary rounded-full">
                  {badge}
                </span>
              )}
              {isNew && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-primary text-primary-foreground rounded-full">
                  NEW
                </span>
              )}
            </div>
          )}
        </>
      )}
      
      {/* Indicateur actif pour mode collapsed */}
      {isCollapsed && isActive && (
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-sidebar-primary rounded-l-full" />
      )}
    </Link>
  )

  // En mode collapsed, wrap avec tooltip
  if (isCollapsed) {
    return (
      <TooltipProvider delayDuration={300}>
        <Tooltip>
          <TooltipTrigger asChild className="w-full">
            {itemContent}
          </TooltipTrigger>
          <TooltipContent side="right" className="font-medium">
            <div className="flex items-center gap-2">
              {label}
              {(badge || isNew) && (
                <div className="flex items-center gap-1">
                  {badge && (
                    <span className="px-1.5 py-0.5 text-xs font-semibold bg-primary/10 text-primary rounded">
                      {badge}
                    </span>
                  )}
                  {isNew && (
                    <span className="px-1.5 py-0.5 text-xs font-semibold bg-primary text-primary-foreground rounded">
                      NEW
                    </span>
                  )}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return itemContent
}
