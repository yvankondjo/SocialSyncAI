'use client'

import { InboxPage } from '@/components/inbox-page'

export default function Inbox() {
  return (
    <div className="flex-1 overflow-auto bg-muted/30">
      <InboxPage />
    </div>
  )
}