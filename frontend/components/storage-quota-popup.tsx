"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Database, AlertCircle } from "lucide-react"

interface StorageQuotaPopupProps {
  usedMb: number;
  quotaMb: number;
  availableMb: number;
  percentageUsed: number;
  isFull: boolean;
}

export function StorageQuotaPopup({
  usedMb,
  quotaMb,
  availableMb,
  percentageUsed,
  isFull
}: StorageQuotaPopupProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm bg-muted hover:bg-muted/80 rounded-md transition-colors">
          <Database className="h-4 w-4" />
          <span className="text-xs">
            {usedMb.toFixed(1)} / {quotaMb} MB
          </span>
          {isFull && <AlertCircle className="h-4 w-4 text-destructive" />}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h4 className="font-semibold">Quota de stockage</h4>
            <Badge variant={isFull ? "destructive" : "secondary"}>
              {percentageUsed.toFixed(0)}%
            </Badge>
          </div>

          <Progress value={percentageUsed} className="h-2" />

          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Utilisé:</span>
              <span className="font-medium">{usedMb.toFixed(2)} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Disponible:</span>
              <span className="font-medium">{availableMb.toFixed(2)} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Quota total:</span>
              <span className="font-medium">{quotaMb} MB</span>
            </div>
          </div>

          {isFull && (
            <div className="flex items-start gap-2 p-2 bg-destructive/10 rounded-md">
              <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
              <p className="text-sm text-destructive">
                Quota atteint. Supprimez des fichiers ou FAQ pour libérer de l'espace.
              </p>
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}


