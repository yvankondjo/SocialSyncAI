'use client'

import { CalendarPage } from '@/components/calendar-page'

export default function Calendar() {
  return (
    <div className="flex-1 overflow-auto bg-muted/30">
      <CalendarPage />
    </div>
  )
}