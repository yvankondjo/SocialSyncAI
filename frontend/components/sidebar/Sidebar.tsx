'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useSidebarStore } from '@/hooks/useSidebarStore'
import { NavItem } from './NavItem'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  MessageSquare,
  Database,
  Play,
  BarChart3,
  Link,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  Menu,
  ChevronDown,
  Activity,
  FileText,
  HelpCircle,
  GitCompare,
  Bot,
  MessageCircle,
  Globe,
} from 'lucide-react'

const mainNavItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/dashboard' },
]

const activitySubItems = [
  { icon: MessageSquare, label: 'Chat', href: '/dashboard/activity/chat' },
]

const sourcesSubItems = [
  { icon: Database, label: 'Data', href: '/dashboard/sources/data' },
  { icon: HelpCircle, label: 'FAQ', href: '/dashboard/sources/faq' },
]

const playgroundSubItems = [
  { icon: GitCompare, label: 'Compare', href: '/dashboard/playground/compare' },
]

const settingsSubItems = [
  { icon: Bot, label: 'AI', href: '/dashboard/settings/ai' },
  { icon: MessageCircle, label: 'Chat Interfaces', href: '/dashboard/settings/chat-interfaces' },
  { icon: Globe, label: 'Custom Domain', href: '/dashboard/settings/custom-domain' },
]

export function Sidebar() {
  const { user, signOut } = useAuth()
  const { isCollapsed, toggleCollapsed } = useSidebarStore()
  const [activityExpanded, setActivityExpanded] = useState(true)
  const [sourcesExpanded, setSourcesExpanded] = useState(true)
  const [playgroundExpanded, setPlaygroundExpanded] = useState(true)
  const [settingsExpanded, setSettingsExpanded] = useState(true)

  const handleSignOut = async () => {
    await signOut()
  }

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'hidden lg:flex flex-col bg-sidebar border-r border-sidebar-border shadow-soft transition-all duration-300 ease-in-out h-screen fixed left-0 top-0 z-30',
          isCollapsed ? 'w-[72px]' : 'w-[280px]'
        )}
        aria-label="Sidebar navigation"
        role="complementary"
      >
        {/* Header */}
        <div className={cn(
          'p-6 border-b border-sidebar-border transition-all duration-300',
          isCollapsed && 'px-4 py-6'
        )}>
          {isCollapsed ? (
            <div className="flex justify-center">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">S</span>
              </div>
            </div>
          ) : (
            <h1 className="text-xl font-bold text-sidebar-foreground">SocialSync</h1>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto" aria-label="Main navigation">
          {/* Main Navigation */}
          {mainNavItems.map((item) => (
            <NavItem
              key={item.href}
              icon={item.icon}
              label={item.label}
              href={item.href}
            />
          ))}

          {/* Activity Section */}
          <div className="pt-4">
            <div
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer hover:bg-sidebar-accent',
                isCollapsed && 'justify-center px-2'
              )}
              onClick={() => setActivityExpanded(!activityExpanded)}
            >
              <Activity className={cn(
                'w-5 h-5 flex-shrink-0 transition-all duration-200',
                isCollapsed ? 'w-6 h-6' : 'w-5 h-5'
              )} />
              
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-sidebar-foreground">Activity</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    activityExpanded ? 'rotate-180' : ''
                  )} />
                </>
              )}
            </div>

            {/* Activity Sub Items */}
            {(!isCollapsed && activityExpanded) && (
              <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                {activitySubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}

            {/* Activity collapsed tooltips */}
            {isCollapsed && (
              <div className="space-y-1 mt-1">
                {activitySubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Sources Section */}
          <div className="pt-2">
            <div
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer hover:bg-sidebar-accent',
                isCollapsed && 'justify-center px-2'
              )}
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
            >
              <Database className={cn(
                'w-5 h-5 flex-shrink-0 transition-all duration-200',
                isCollapsed ? 'w-6 h-6' : 'w-5 h-5'
              )} />
              
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-sidebar-foreground">Sources</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    sourcesExpanded ? 'rotate-180' : ''
                  )} />
                </>
              )}
            </div>

            {/* Sources Sub Items */}
            {(!isCollapsed && sourcesExpanded) && (
              <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                {sourcesSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}

            {/* Sources collapsed tooltips */}
            {isCollapsed && (
              <div className="space-y-1 mt-1">
                {sourcesSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Playground Section */}
          <div className="pt-2">
            <div
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer hover:bg-sidebar-accent',
                isCollapsed && 'justify-center px-2'
              )}
              onClick={() => setPlaygroundExpanded(!playgroundExpanded)}
            >
              <Play className={cn(
                'w-5 h-5 flex-shrink-0 transition-all duration-200',
                isCollapsed ? 'w-6 h-6' : 'w-5 h-5'
              )} />
              
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-sidebar-foreground">Playground</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    playgroundExpanded ? 'rotate-180' : ''
                  )} />
                </>
              )}
            </div>

            {/* Playground Sub Items */}
            {(!isCollapsed && playgroundExpanded) && (
              <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                {playgroundSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}

            {/* Playground collapsed tooltips */}
            {isCollapsed && (
              <div className="space-y-1 mt-1">
                {playgroundSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Analytics Section */}
          <div className="pt-2">
            <NavItem
              icon={BarChart3}
              label="Analytics"
              href="/dashboard/analytics"
            />
          </div>

          {/* Connect Section */}
          <div className="pt-2">
            <NavItem
              icon={Link}
              label="Connect"
              href="/dashboard/connect"
            />
          </div>

          {/* Settings Section */}
          <div className="pt-2">
            <div
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer hover:bg-sidebar-accent',
                isCollapsed && 'justify-center px-2'
              )}
              onClick={() => setSettingsExpanded(!settingsExpanded)}
            >
              <Settings className={cn(
                'w-5 h-5 flex-shrink-0 transition-all duration-200',
                isCollapsed ? 'w-6 h-6' : 'w-5 h-5'
              )} />
              
              {!isCollapsed && (
                <>
                  <span className="flex-1 text-sidebar-foreground">Settings</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    settingsExpanded ? 'rotate-180' : ''
                  )} />
                </>
              )}
            </div>

            {/* Settings Sub Items */}
            {(!isCollapsed && settingsExpanded) && (
              <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                {settingsSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}

            {/* Settings collapsed tooltips */}
            {isCollapsed && (
              <div className="space-y-1 mt-1">
                {settingsSubItems.map((item) => (
                  <NavItem
                    key={item.href}
                    icon={item.icon}
                    label={item.label}
                    href={item.href}
                  />
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* User Section */}
        <div className={cn(
          'p-4 border-t border-sidebar-border transition-all duration-300',
          isCollapsed && 'px-2'
        )}>
          {isCollapsed ? (
            <TooltipProvider delayDuration={300}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="w-full h-12 p-0">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={user?.user_metadata?.avatar_url} />
                          <AvatarFallback>
                            {user?.user_metadata?.full_name?.charAt(0)?.toUpperCase() ||
                             user?.email?.charAt(0)?.toUpperCase() || 'U'}
                          </AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent side="right" className="w-56">
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
                      <DropdownMenuItem>
                        <User className="mr-2 h-4 w-4" />
                        <span>Profil</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem>
                        <Settings className="mr-2 h-4 w-4" />
                        <span>Paramètres</span>
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleSignOut}>
                        <LogOut className="mr-2 h-4 w-4" />
                        <span>Se déconnecter</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TooltipTrigger>
                <TooltipContent side="right">
                  {user?.user_metadata?.full_name || user?.email || 'Utilisateur'}
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start p-2 h-auto">
                  <div className="flex items-center space-x-3 w-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user?.user_metadata?.avatar_url} />
                      <AvatarFallback>
                        {user?.user_metadata?.full_name?.charAt(0)?.toUpperCase() ||
                         user?.email?.charAt(0)?.toUpperCase() || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 text-left">
                      <p className="text-sm font-medium text-sidebar-foreground truncate">
                        {user?.user_metadata?.full_name || 'Utilisateur'}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {user?.email}
                      </p>
                    </div>
                  </div>
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
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  <span>Profil</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Paramètres</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleSignOut}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Se déconnecter</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>

        {/* Toggle Button */}
        <div className={cn(
          'p-4 border-t border-sidebar-border/50',
          isCollapsed && 'px-2'
        )}>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleCollapsed}
            className={cn(
              'w-full flex items-center justify-center hover:bg-sidebar-accent transition-all duration-200',
              isCollapsed ? 'px-2' : 'justify-start px-3'
            )}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 mr-2" />
                <span className="text-sm">Réduire</span>
              </>
            )}
          </Button>
        </div>
      </aside>

      {/* Mobile Sidebar */}
      <div className="lg:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="sm" className="fixed top-4 left-4 z-50">
              <Menu className="w-5 h-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[280px] p-0">
            <SheetHeader className="p-6 border-b border-sidebar-border">
              <SheetTitle className="text-left">SocialSync</SheetTitle>
            </SheetHeader>
            
            <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
              {mainNavItems.map((item) => (
                <NavItem
                  key={item.href}
                  icon={item.icon}
                  label={item.label}
                  href={item.href}
                />
              ))}

              {/* Activity Section */}
              <div className="pt-4">
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer hover:bg-sidebar-accent"
                  onClick={() => setActivityExpanded(!activityExpanded)}
                >
                  <Activity className="w-5 h-5 flex-shrink-0" />
                  <span className="flex-1 text-sidebar-foreground">Activity</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    activityExpanded ? 'rotate-180' : ''
                  )} />
                </div>

                {activityExpanded && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                    {activitySubItems.map((item) => (
                      <NavItem
                        key={item.href}
                        icon={item.icon}
                        label={item.label}
                        href={item.href}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Sources Section */}
              <div className="pt-2">
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer hover:bg-sidebar-accent"
                  onClick={() => setSourcesExpanded(!sourcesExpanded)}
                >
                  <Database className="w-5 h-5 flex-shrink-0" />
                  <span className="flex-1 text-sidebar-foreground">Sources</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    sourcesExpanded ? 'rotate-180' : ''
                  )} />
                </div>

                {sourcesExpanded && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                    {sourcesSubItems.map((item) => (
                      <NavItem
                        key={item.href}
                        icon={item.icon}
                        label={item.label}
                        href={item.href}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Playground Section */}
              <div className="pt-2">
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer hover:bg-sidebar-accent"
                  onClick={() => setPlaygroundExpanded(!playgroundExpanded)}
                >
                  <Play className="w-5 h-5 flex-shrink-0" />
                  <span className="flex-1 text-sidebar-foreground">Playground</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    playgroundExpanded ? 'rotate-180' : ''
                  )} />
                </div>

                {playgroundExpanded && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                    {playgroundSubItems.map((item) => (
                      <NavItem
                        key={item.href}
                        icon={item.icon}
                        label={item.label}
                        href={item.href}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Analytics Section */}
              <div className="pt-2">
                <NavItem
                  icon={BarChart3}
                  label="Analytics"
                  href="/dashboard/analytics"
                />
              </div>

              {/* Connect Section */}
              <div className="pt-2">
                <NavItem
                  icon={Link}
                  label="Connect"
                  href="/dashboard/connect"
                />
              </div>

              {/* Settings Section */}
              <div className="pt-2">
                <div
                  className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium cursor-pointer hover:bg-sidebar-accent"
                  onClick={() => setSettingsExpanded(!settingsExpanded)}
                >
                  <Settings className="w-5 h-5 flex-shrink-0" />
                  <span className="flex-1 text-sidebar-foreground">Settings</span>
                  <ChevronDown className={cn(
                    'w-4 h-4 text-sidebar-foreground transition-transform duration-200',
                    settingsExpanded ? 'rotate-180' : ''
                  )} />
                </div>

                {settingsExpanded && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-sidebar-border pl-4">
                    {settingsSubItems.map((item) => (
                      <NavItem
                        key={item.href}
                        icon={item.icon}
                        label={item.label}
                        href={item.href}
                      />
                    ))}
                  </div>
                )}
              </div>
            </nav>

            <div className="p-4 border-t border-sidebar-border">
              <div className="flex items-center space-x-3">
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user?.user_metadata?.avatar_url} />
                  <AvatarFallback>
                    {user?.user_metadata?.full_name?.charAt(0)?.toUpperCase() ||
                     user?.email?.charAt(0)?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <p className="text-sm font-medium text-sidebar-foreground">
                    {user?.user_metadata?.full_name || 'Utilisateur'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSignOut}
                  className="text-sidebar-foreground hover:bg-sidebar-accent"
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  )
}
