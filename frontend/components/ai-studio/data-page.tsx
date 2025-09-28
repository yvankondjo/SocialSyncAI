"use client"

import React, { useState, useEffect, useRef } from "react"
import { useAuth } from "@/hooks/useAuth"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  File,
  Upload as UploadIcon,
  CheckCircle,
  XCircle,
  Loader2,
  Download,
  Trash2,
  Eye,
} from "lucide-react"
import { useDropzone } from "react-dropzone"
import { supabase } from "@/lib/supabase"
import { KnowledgeDocumentsService, KnowledgeDocument } from "@/lib/api"

type FileStatus = "processing" | "indexed" | "failed"

const statusIcons: Record<FileStatus, React.ReactNode> = {
  processing: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
  indexed: <CheckCircle className="h-4 w-4 text-green-500" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
}

const statusText: Record<FileStatus, string> = {
  processing: "Processing...",
  indexed: "Indexed",
  failed: "Failed",
}

function FileUploadArea({ onUpload }: { onUpload: (files: File[]) => void }) {
  const onDrop = (acceptedFiles: File[]) => {
    onUpload(acceptedFiles)
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
    },
    maxSize: 10 * 1024 * 1024, // 10 MB
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed border-muted-foreground/30 rounded-lg p-8 text-center bg-muted/20 hover:bg-muted/40 transition-colors cursor-pointer ${isDragActive ? 'border-primary bg-primary/10' : ''}`}
    >
      <input {...getInputProps()} />
      <UploadIcon className="mx-auto h-12 w-12 text-muted-foreground" />
      <p className="mt-4 text-sm text-muted-foreground">
        {isDragActive ?
          "Drop the files here ..." :
          <><span className="font-semibold text-primary">Click to upload</span> or drag and drop</>
        }
      </p>
      <p className="text-xs text-muted-foreground/80 mt-1">
        PDF, DOCX, MD, TXT (max 10MB)
      </p>
    </div>
  )
}

function FileListItem({
  file,
  onDelete
}: {
  file: KnowledgeDocument & { progress?: number }
  onDelete: (documentId: string, title: string) => void
}) {
  const { toast } = useToast()
  // Extract file type from object_key or title
  const getFileType = (objectKey?: string | null, title?: string) => {
    if (objectKey) {
      const extension = objectKey.split('.').pop()?.toUpperCase()
      return extension || 'FILE'
    }
    // Fallback to title extension
    if (title) {
      const extension = title.split('.').pop()?.toUpperCase()
      return extension || 'FILE'
    }
    return 'FILE'
  }

  // Format file size
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Inconnue'

    const units = ['B', 'KB', 'MB', 'GB']
    let size = bytes
    let unitIndex = 0

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }

    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  // Generate download URL for indexed files
  const getDownloadUrl = (bucketName?: string | null, objectKey?: string | null) => {
    if (file.status !== 'indexed' || !bucketName || !objectKey) return null

    try {
      const { data } = supabase.storage
        .from(bucketName)
        .getPublicUrl(objectKey)

      if (!data.publicUrl) {
        console.error('Failed to generate download URL for:', objectKey)
        return null
      }

      return data.publicUrl
    } catch (error) {
      console.error('Error generating download URL:', error)
      return null
    }
  }

  return (
    <div className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
      <File className="w-6 h-6 text-primary" />
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{file.title}</p>
        <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-muted-foreground">
          <span className="px-2 py-1 bg-muted rounded text-xs font-medium">
            {getFileType(file.object_key, file.title)}
          </span>
          <span>•</span>
          <span>Taille inconnue</span>
          <span>•</span>
          <span>Créé: {new Date(file.created_at).toLocaleDateString('fr-FR')}</span>
          {file.last_ingested_at && (
            <>
              <span>•</span>
              <span>Indexé: {new Date(file.last_ingested_at).toLocaleDateString('fr-FR')}</span>
            </>
          )}
        </div>
        {file.progress !== undefined && file.progress < 100 && (
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2 dark:bg-gray-700">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${file.progress}%` }}
            ></div>
            <p className="text-xs text-muted-foreground mt-1">Progression: {file.progress}%</p>
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {statusIcons[file.status]}
        <span>{statusText[file.status]}</span>
      </div>
      <div className="flex gap-1">
        {file.status === 'indexed' && file.bucket_name && file.object_key && (
          <>
            <Button
              variant="ghost"
              size="icon"
              asChild
              className="text-green-500 hover:text-green-600 hover:bg-green-50"
              title="Prévisualiser le document"
            >
              <a
                href={getDownloadUrl(file.bucket_name, file.object_key) || '#'}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => {
                  const url = getDownloadUrl(file.bucket_name, file.object_key)
                  if (!url) {
                    e.preventDefault()
                    toast({
                      title: "Erreur de prévisualisation",
                      description: "Impossible de générer le lien de prévisualisation",
                      variant: "destructive",
                    })
                  } else {
                    toast({
                      title: "Prévisualisation ouverte",
                      description: `${file.title} s'ouvre dans un nouvel onglet`,
                    })
                  }
                }}
              >
                <Eye className="h-4 w-4" />
              </a>
            </Button>

            <Button
              variant="ghost"
              size="icon"
              asChild
              className="text-blue-500 hover:text-blue-600 hover:bg-blue-50"
              title="Télécharger le document"
            >
              <a
                href={getDownloadUrl(file.bucket_name, file.object_key) || '#'}
                target="_blank"
                rel="noopener noreferrer"
                download={file.title}
                onClick={(e) => {
                  const url = getDownloadUrl(file.bucket_name, file.object_key)
                  if (!url) {
                    e.preventDefault()
                    toast({
                      title: "Erreur de téléchargement",
                      description: "Impossible de générer le lien de téléchargement",
                      variant: "destructive",
                    })
                  } else {
                    toast({
                      title: "Téléchargement démarré",
                      description: `Téléchargement de ${file.title} en cours...`,
                    })
                  }
                }}
              >
                <Download className="h-4 w-4" />
              </a>
            </Button>
          </>
        )}

        {file.status !== 'indexed' && (
          <>
            <Button
              variant="ghost"
              size="icon"
              disabled
              title="Prévisualisation indisponible"
            >
              <Eye className="h-4 w-4 text-gray-400" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              disabled
              title="Téléchargement indisponible"
            >
              <Download className="h-4 w-4 text-gray-400" />
            </Button>
          </>
        )}

        <Button
          variant="ghost"
          size="icon"
          onClick={() => onDelete(file.id, file.title)}
          className="text-red-500 hover:text-red-700 hover:bg-red-50"
          title="Supprimer le document"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

export function DataSourcesPage() {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const documentsRef = useRef<KnowledgeDocument[]>([])

  // Keep ref in sync with state
  useEffect(() => {
    documentsRef.current = documents
  }, [documents])
  
  // Fetch documents from API
  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const docs = await KnowledgeDocumentsService.list()
      setDocuments(docs)
    } catch (err) {
      console.error('Error fetching documents:', err)
      setError(err instanceof Error ? err.message : 'Failed to load documents')
    } finally {
      setIsLoading(false)
    }
  }

  // Écoute en temps réel des changements de documents + polling de secours
  useEffect(() => {
    if (!user) return

    // Initial load
    loadDocuments()

    // 1. Écoute Realtime pour les changements de statut
    const subscription = supabase
      .channel('knowledge_documents_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'knowledge_documents',
          filter: `user_id=eq.${user.id}`
        },
        (payload) => {
          console.log('📡 Realtime update received:', payload)
          // Recharger les documents quand il y a un changement
          loadDocuments()
        }
      )
      .subscribe((status) => {
        console.log('📡 Realtime subscription status:', status)
      })

    // 2. Polling de secours (moins fréquent) au cas où Realtime ne marche pas
    let fallbackInterval: NodeJS.Timeout | null = null
    
    const startFallbackPolling = () => {
      fallbackInterval = setInterval(() => {
        const currentDocs = documentsRef.current
        const hasProcessingDocs = currentDocs.some(doc => doc.status === 'processing')
        
        if (hasProcessingDocs) {
          console.log('🔄 Fallback polling check...')
          loadDocuments()
        }
      }, 30000) // Polling de secours toutes les 30 secondes seulement
    }

    // Démarrer le polling de secours après 10 secondes
    const fallbackTimeout = setTimeout(startFallbackPolling, 10000)

    return () => {
      // Nettoyer la subscription Realtime
      subscription.unsubscribe()
      
      // Nettoyer le polling de secours
      if (fallbackInterval) {
        clearInterval(fallbackInterval)
      }
      clearTimeout(fallbackTimeout)
    }
  }, [user])

  // Test de la configuration Supabase au montage du composant
  useEffect(() => {
    const testSupabaseConnection = async () => {
      try {
        console.log("Testing Supabase connection...")
        const { data, error } = await supabase.storage.listBuckets()

        if (error) {
          console.error("Supabase connection error:", error)
          console.log("Assuming kb bucket exists despite permission error...")
        } else {
          console.log("Available buckets:", data?.map(b => b.name))
          const kbBucket = data?.find(b => b.name === 'kb')
          if (kbBucket) {
            console.log("✅ kb bucket found:", kbBucket)
          } else {
            console.log("⚠️ kb bucket not found in list, but assuming it exists")
          }
        }
      } catch (err) {
        console.error("Failed to test Supabase connection:", err)
        console.log("Continuing with assumption that kb bucket exists...")
      }
    }

    testSupabaseConnection()
  }, [])

  const handleUpload = (files: File[]) => {
    console.log("🚀 Starting upload process for files:", files.map(f => f.name))
    console.log("📁 Files details:", files.map(f => ({
      name: f.name,
      size: f.size,
      type: f.type
    })))

    if (!user) {
      console.error("User not authenticated for upload.")
      return
    }

    console.log("User authenticated:", user.id)

    files.forEach(async (file) => {
      const filePath = `${crypto.randomUUID()}/${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`

      console.log("🚀 Uploading to path:", filePath)
      console.log("📊 File details:", {
        name: file.name,
        size: file.size,
        type: file.type,
        userId: user.id
      })

      const { error } = await supabase.storage
        .from("kb")
        .upload(filePath, file, {
          cacheControl: '3600',
          upsert: true,
        })

      if (error) {
        console.error("❌ Error uploading file:", error)
        console.error("🔍 Error details:", {
          message: error.message,
          name: error.name,
          filePath: filePath,
          fileName: file.name,
          fileSize: file.size
        })
      } else {
        console.log("✅ File uploaded successfully:", filePath)
        console.log("🔄 Trigger should activate now...")
        console.log("⏳ Document will appear with 'processing' status")
        console.log("📡 Refreshing documents list...")
        
        // Refresh documents after successful upload
        setTimeout(() => {
          loadDocuments()
        }, 1000) // Small delay to allow trigger to execute
      }
    })
  }

  // Handle document deletion with confirmation
  const handleDeleteDocument = async (documentId: string, title: string) => {
    if (!window.confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) {
      return
    }

    try {
      console.log(`🗑️ Deleting document: ${title} (${documentId})`)
      await KnowledgeDocumentsService.remove(documentId)

      // Remove from local state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId))

      console.log(`✅ Document deleted successfully: ${title}`)
    } catch (err) {
      console.error('❌ Error deleting document:', err)
      alert(`Failed to delete document: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="p-6 space-y-8 max-w-7xl mx-auto">
      <Card className="shadow-soft">
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold text-foreground">Data Sources</CardTitle>
            <p className="text-sm text-muted-foreground">Manage the knowledge base for your AI assistant.</p>
          </div>
          <Button>
            <UploadIcon className="w-4 h-4 mr-2" />
            Add Document
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileUploadArea onUpload={handleUpload} />
          
          {isLoading && (
            <div className="text-center py-4">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground mt-2">Loading documents...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-4">
              <p className="text-sm text-red-500">Error: {error}</p>
              <Button onClick={loadDocuments} variant="outline" size="sm" className="mt-2">
                Retry
              </Button>
            </div>
          )}

          {!isLoading && !error && (
            <div className="space-y-2">
              {documents.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">No documents yet</p>
                  <p className="text-xs">Upload your first document to get started</p>
                </div>
              ) : (
                documents.map(doc => (
                  <FileListItem
                    key={doc.id}
                    file={doc}
                    onDelete={handleDeleteDocument}
                  />
                ))
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
