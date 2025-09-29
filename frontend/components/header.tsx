"use client"

import { useState } from "react"
import { useAuth } from '@/hooks/useAuth'
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Sidebar } from '@/components/sidebar-new'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
    "/dashboard/settings/chat-interface": "Interface Chat",
    "/dashboard/settings/custom-domains": "Domaines Personnalisés",
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
  const { user, signOut } = useAuth()
  const pathname = usePathname()
  const currentPageName = getPageName(pathname)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleSignOut = async () => {
    await signOut()
  }

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

          <h1 className="text-base sm:text-lg font-semibold text-foreground truncate">{currentPageName}</h1>
        </div>

        <div className="flex items-center gap-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                <Avatar className="h-6 w-6" style={{ backgroundColor: '#4285F4' }}>
                  <AvatarImage src={user?.user_metadata?.avatar_url} />
                  <AvatarFallback className="text-xs">
                    {user?.user_metadata?.full_name?.charAt(0)?.toUpperCase() ||
                     user?.email?.charAt(0)?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
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
              <DropdownMenuItem onClick={handleSignOut}>
                <span>Se déconnecter</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}