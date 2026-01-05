import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "@/components/ui/toaster"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { ThemeProvider } from "@/components/providers/ThemeProvider"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const getFrontendUrl = () => {
  const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || process.env.NEXT_PUBLIC_APP_URL || 'https://localhost:3000';
  return new URL(frontendUrl);
};

export const metadata: Metadata = {
  title: "SocialSyncAI – AI Studio",
  description: "Plateforme IA conversationnelle pour WhatsApp et Instagram",
  generator: "v0.app",
  metadataBase: getFrontendUrl(),
}

export const dynamic = 'force-dynamic'

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                if (typeof window === 'undefined') return;
                const storageKey = 'moat-theme';
                localStorage.setItem(storageKey, 'light');
                document.documentElement.setAttribute('data-moat-theme', 'light');
                document.documentElement.classList.remove('dark');
                document.documentElement.classList.add('light');
              })();
            `,
          }}
        />
      </head>
      <body className={`font-sans ${inter.variable} antialiased h-screen overflow-hidden`}>
        <ThemeProvider>
          <QueryProvider>
            {children}
            <Toaster />
            <div id="portal-root" />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}