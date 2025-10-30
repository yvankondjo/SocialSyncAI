import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "@/components/ui/toaster"
import { QueryProvider } from "@/components/providers/QueryProvider"
import { ThemeProvider } from "@/components/providers/ThemeProvider"
import { demoEnabled, demoAnalytics } from "@/lib/demo-data"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "ConversAI – AI Studio",
  description: "Plateforme IA conversationnelle pour WhatsApp et Instagram",
  generator: "v0.app",
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"),
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="light">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // OPEN-SOURCE VERSION: Force light theme only
                document.documentElement.setAttribute('data-moat-theme', 'light');
                document.documentElement.classList.add('light');
                document.documentElement.classList.remove('dark');
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