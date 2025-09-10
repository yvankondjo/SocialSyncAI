'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarState {
  isCollapsed: boolean
  isMobileOpen: boolean
  toggleCollapsed: () => void
  setCollapsed: (collapsed: boolean) => void
  toggleMobile: () => void
  setMobileOpen: (open: boolean) => void
}

export const useSidebarStore = create<SidebarState>()(
  persist(
    (set) => ({
      isCollapsed: false,
      isMobileOpen: false,
      
      toggleCollapsed: () => 
        set((state) => ({ isCollapsed: !state.isCollapsed })),
      
      setCollapsed: (collapsed: boolean) => 
        set({ isCollapsed: collapsed }),
      
      toggleMobile: () => 
        set((state) => ({ isMobileOpen: !state.isMobileOpen })),
      
      setMobileOpen: (open: boolean) => 
        set({ isMobileOpen: open }),
    }),
    {
      name: 'socialsync-sidebar',
      partialize: (state) => ({ 
        isCollapsed: state.isCollapsed 
      }),
    }
  )
)


