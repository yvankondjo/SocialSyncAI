"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Upload, FileText, CheckCircle, Clock, AlertTriangle, Trash2 } from "lucide-react"

export function DataTab() {
  const [dragActive, setDragActive] = useState(false)

  const documents = [
    {
      id: "1",
      title: "FAQ Produits.pdf",
      type: "PDF",
      size: "1.2 MB",
      chunks: 25,
      lastSync: "Il y a 2h",
      status: "indexed",
    },
    {
      id: "2",
      title: "Politique Remboursement.docx",
      type: "DOCX",
      size: "890 KB",
      chunks: 15,
      lastSync: "Il y a 1j",
      status: "indexing",
    },
    {
      id: "3",
      title: "Guide Utilisateur.md",
      type: "MD",
      size: "2.1 MB",
      chunks: 42,
      lastSync: "Il y a 3j",
      status: "indexed",
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "indexed":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "indexing":
        return <Clock className="w-4 h-4 text-yellow-500" />
      case "failed":
        return <AlertTriangle className="w-4 h-4 text-red-500" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      indexed: "default",
      indexing: "secondary",
      failed: "destructive",
    } as const

    const labels = {
      indexed: "Indexé",
      indexing: "En cours...",
      failed: "Échec",
    }

    return (
      <Badge variant={variants[status as keyof typeof variants] || "default"} className="text-xs">
        {labels[status as keyof typeof labels] || status}
      </Badge>
    )
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
  }

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Upload Area - Simplified */}
      <Card className="shadow-soft">
        <CardContent className="p-6">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-semibold mb-2">Ajoutez vos documents</h3>
            <p className="text-muted-foreground mb-4">Glissez-déposez vos fichiers PDF, DOCX, MD (max 25MB)</p>
            <Button className="gradient-primary text-white border-0">
              <Upload className="w-4 h-4 mr-2" />
              Sélectionner des fichiers
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Documents List - Simplified */}
      <Card className="shadow-soft">
        <CardHeader>
          <CardTitle>Documents ({documents.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4 flex-1">
                  <FileText className="w-5 h-5 text-muted-foreground" />
                  <div className="flex-1">
                    <div className="font-medium">{doc.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {doc.type} • {doc.size} • {doc.chunks} sections
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <div className="text-sm text-muted-foreground">Dernière sync</div>
                    <div className="text-sm">{doc.lastSync}</div>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusIcon(doc.status)}
                    {getStatusBadge(doc.status)}
                  </div>

                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          {documents.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Aucun document</h3>
              <p className="text-muted-foreground">Ajoutez votre premier document pour commencer</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
