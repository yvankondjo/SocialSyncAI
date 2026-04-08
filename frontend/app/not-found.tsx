import Link from "next/link"

export default function NotFoundPage() {
  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "24px" }}>
      <div style={{ maxWidth: "480px", textAlign: "center" }}>
        <p>404</p>
        <h1>Cette page n&apos;existe pas</h1>
        <p>Le contenu demande est introuvable.</p>
        <Link href="/">Retour a l&apos;accueil</Link>
      </div>
    </main>
  )
}
