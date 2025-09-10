'use client'

import { redirect } from 'next/navigation'

export default function AIStudio() {
  // Redirect to prompt-tuning by default
  redirect('/dashboard/ai-studio/prompt-tuning')
}