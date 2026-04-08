"use client"

import Link from "next/link"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  console.error(error)

  return (
    <html lang="en">
      <body style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "24px" }}>
        <div style={{ maxWidth: "480px", textAlign: "center" }}>
          <p>Erreur</p>
          <h1>Un probleme inattendu est survenu</h1>
          <p>Vous pouvez reessayer ou revenir a la page d&apos;accueil.</p>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => reset()}
            >
              Reessayer
            </button>
            <Link href="/">
              Retour a l&apos;accueil
            </Link>
          </div>
        </div>
      </body>
    </html>
  )
}
