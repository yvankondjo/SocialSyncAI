'use client'

import * as React from 'react'
import {
  ThemeProvider as NextThemesProvider,
  type ThemeProviderProps,
} from 'next-themes'

export function ThemeProvider({ children, ...props }: ThemeProviderProps & { children: any }) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
