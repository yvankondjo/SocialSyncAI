"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useEffect } from "react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    if (error) {
      console.error(error)
    }
  }, [error])

  const getErrorMessage = () => {
    if (!error) {
      return "Une erreur inattendue s'est produite"
    }
    if (typeof error === 'string') {
      return error
    }
    if (error instanceof Error) {
      return error.message || error.toString()
    }
    if (error.message && typeof error.message === 'string') {
      return error.message
    }
    if (typeof error.toString === 'function') {
      const str = error.toString()
      if (str !== '[object Object]') {
        return str
      }
    }
    return "Une erreur inattendue s'est produite"
  }

  const errorMessage = getErrorMessage()

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold">500</h1>
        <h2 className="text-2xl font-semibold">Une erreur s'est produite</h2>
        <p className="text-muted-foreground">
          {errorMessage}
        </p>
        <div className="flex gap-4 justify-center">
          <Button onClick={reset}>
            Réessayer
          </Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard">Retour au tableau de bord</Link>
          </Button>
        </div>
      </div>
    </div>
  )
}

