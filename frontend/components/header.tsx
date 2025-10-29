"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Sidebar } from '@/components/sidebar-new'
import { Menu } from "lucide-react"
import { usePathname } from "next/navigation"

const getPageName = (pathname: string): string => {
  const pageMap: Record<string, string> = {
    "/dashboard": "Dashboard",
    "/dashboard/playground": "Playground",
    "/dashboard/playground/compare": "Comparaison",
    "/dashboard/activity": "Activité",
    "/dashboard/activity/chat": "Chat",
    "/dashboard/analytics": "Analytics",
    "/dashboard/sources": "Sources",
    "/dashboard/sources/data": "Données",
    "/dashboard/sources/faq": "FAQ",
    "/dashboard/connect": "Connexion",
    "/dashboard/settings": "Paramètres",
    "/dashboard/settings/ai": "IA",
  }

  // Chercher une correspondance exacte
  if (pageMap[pathname]) {
    return pageMap[pathname]
  }

  // Chercher une correspondance partielle pour les sous-pages
  for (const [path, name] of Object.entries(pageMap)) {
    if (pathname.startsWith(path + "/")) {
      return name
    }
  }

  // Valeur par défaut
  return "Dashboard"
}

export function Header() {
  const pathname = usePathname()
  const currentPageName = getPageName(pathname)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-3 sm:px-4 lg:px-6">
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Bouton hamburger pour mobile */}
          <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden text-muted-foreground hover:text-foreground p-2"
              >
                <Menu className="w-5 h-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-64">
              <Sidebar />
            </SheetContent>
          </Sheet>

          <h1 className="text-base sm:text-lg font-semibold text-foreground truncate">{currentPageName || "Dashboard"}</h1>
        </div>
      </div>
    </header>
  )
}