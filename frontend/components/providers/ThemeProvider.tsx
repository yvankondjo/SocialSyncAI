"use client"

import React, { useEffect, useState } from 'react'

type Theme = 'light' | 'dark' | 'system'

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}

type ThemeProviderState = {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
}

// Use React.createContext directly with type assertion
const ThemeProviderContext = (React as any).createContext(undefined) as React.Context<ThemeProviderState | undefined>

export function ThemeProvider({
  children,
  defaultTheme = 'light',
  storageKey = 'moat-theme',
  ...props
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>('light')
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted || typeof window === 'undefined') return
    
    const root = window.document.documentElement

    setResolvedTheme('light')

    root.setAttribute('data-moat-theme', 'light')
    root.classList.remove('light', 'dark')
    root.classList.add('light')

    localStorage.setItem(storageKey, 'light')
  }, [storageKey, mounted])

  const value = {
    theme,
    setTheme,
    resolvedTheme,
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = (React as any).useContext(ThemeProviderContext)

  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }

  return context
}
