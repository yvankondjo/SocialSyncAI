'use client'

import { PromptTuningTab } from '@/components/prompt-tuning-tab'

export default function Playground() {
  return (
    <div className="flex-1 overflow-auto bg-muted/30">
      <PromptTuningTab />
    </div>
  )
}
