'use client'

export default function Ads() {
  return (
    <div className="flex-1 overflow-auto bg-muted/30 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Ads Manager</h1>
          <p className="text-lg text-muted-foreground">Manage your advertising campaigns across all platforms</p>
        </div>
        
        <div className="bg-card rounded-lg p-8 text-center">
          <h2 className="text-xl font-semibold text-card-foreground mb-4">Coming Soon</h2>
          <p className="text-muted-foreground">
            The Ads Manager feature is currently in development. Stay tuned for powerful advertising tools!
          </p>
        </div>
      </div>
    </div>
  )
}
