import Link from "next/link"

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-bold">404</h1>
        <h2 className="text-2xl font-semibold">Page non trouvée</h2>
        <p className="text-muted-foreground">
          La page que vous recherchez n'existe pas.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Retour au tableau de bord
        </Link>
      </div>
    </div>
  )
}

