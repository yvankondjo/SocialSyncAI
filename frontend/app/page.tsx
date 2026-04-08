import Link from "next/link"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <section className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-24 text-center">
        <div className="mx-auto inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-4 py-2 text-sm text-primary">
          SocialSyncAI
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            Automatisez WhatsApp et Instagram avec une IA exploitable en production
          </h1>
          <p className="mx-auto max-w-2xl text-base text-muted-foreground sm:text-lg">
            Centralisez vos conversations, orchestrez vos assistants et suivez
            vos performances depuis une interface unique.
          </p>
        </div>
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/auth/login"
            className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Ouvrir le studio
          </Link>
          <Link
            href="/pricing"
            className="inline-flex h-11 items-center justify-center rounded-md border border-border bg-background px-6 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Voir les tarifs
          </Link>
        </div>
      </section>
    </main>
  )
}
