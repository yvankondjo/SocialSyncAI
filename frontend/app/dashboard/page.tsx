'use client'

import { useState } from 'react'
import { DashboardPage } from '@/components/dashboard-page'
import { ComposerModal } from '@/components/composer-modal'

export default function Dashboard() {
  const [composerOpen, setComposerOpen] = useState(false)

  const handleComposerOpen = () => {
    console.log("[v0] composer_open", {
      source: "dashboard",
      timestamp: new Date().toISOString(),
    })
    setComposerOpen(true)
  }

  const handleComposerClose = () => {
    console.log("[v0] composer_close", {
      timestamp: new Date().toISOString(),
    })
    setComposerOpen(false)
  }

  return (
    <div className="h-full overflow-auto bg-muted/30">
      <DashboardPage />
      
      <ComposerModal
        isOpen={composerOpen}
        onClose={handleComposerClose}
        onSuccess={() => {
          console.log("[v0] composer_success")
          // Handle success - reload data, etc.
        }}
      />
    </div>
  )
}
