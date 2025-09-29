'use client'

export default function Settings() {
  return (
    <div className="flex-1 overflow-auto bg-muted/30 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Paramètres</h1>
        <div className="grid gap-6">
          <div className="bg-card rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Configuration générale</h2>
            <p className="text-muted-foreground">Gérez les paramètres de votre compte et de votre organisation.</p>
          </div>
          <div className="bg-card rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Sécurité</h2>
            <p className="text-muted-foreground">Configurez les paramètres de sécurité et les permissions.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
