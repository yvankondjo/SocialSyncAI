"use client"

import { createContext, useContext, useEffect, ReactNode } from 'react'

// OPEN-SOURCE VERSION: Light theme only
type Theme = 'light'

type ThemeProviderProps = {
  children: ReactNode
}

type ThemeProviderState = {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light'
}

const ThemeProviderContext = createContext<ThemeProviderState | undefined>(undefined)

export function ThemeProvider({
  children,
  ...props
}: ThemeProviderProps) {
  // Always use light theme
  const theme: Theme = 'light'
  const resolvedTheme: 'light' = 'light'

  useEffect(() => {
    const root = window.document.documentElement

    // Force light theme
    root.setAttribute('data-moat-theme', 'light')
    root.classList.remove('dark')
    root.classList.add('light')
  }, [])

  const value = {
    theme,
    setTheme: () => {
      // No-op: theme is locked to light mode
      console.log('[OPEN-SOURCE] Theme is locked to light mode')
    },
    resolvedTheme,
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext)

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }

  return context
}
