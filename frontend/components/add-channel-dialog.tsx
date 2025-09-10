"use client"

import { useMemo } from "react"
import { Dialog, DialogContent, DialogHeader } from "@/components/ui/dialog"
import { logos } from "@/lib/logos"
import { apiFetch } from "@/lib/api"

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function AddChannelDialog({ open, onOpenChange }: Props) {
  const platforms = useMemo(
    () => [
      { id: "instagram", name: "Instagram", icon: logos.instagram },
      { id: "whatsapp", name: "WhatsApp", icon: logos.whatsapp },
      { id: "reddit", name: "Reddit", icon: "/reddit.svg" },
      { id: "linkedin", name: "LinkedIn", icon: logos.linkedin },
    ],
    [],
  )

  const startAuth = async (platform: string) => {
    try {
      const res = await apiFetch<{ platform: string; status: string; authorization_url?: string }>(
        "/api/social-accounts/add",
        { method: "POST", body: JSON.stringify({ platform }) },
      )
      if (res.authorization_url) {
        window.location.href = res.authorization_url
        return
      }
      onOpenChange(false)
    } catch (e) {
      console.error("add account failed", e)
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>Connect a channel</DialogHeader>
        <div className="grid grid-cols-2 gap-3">
          {platforms.map((p) => (
            <button
              key={p.id}
              onClick={() => startAuth(p.id)}
              className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50"
            >
              <img src={p.icon} className="w-5 h-5" />
              <span className="text-sm">{p.name}</span>
            </button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}

