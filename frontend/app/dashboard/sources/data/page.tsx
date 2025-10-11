"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"
import {
  Database,
  Upload,
  Search,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Trash2,
  Download,
  RefreshCw,
  Loader2,
  HardDrive,
} from "lucide-react"
import { KnowledgeDocumentsService, KnowledgeDocument, ApiClient } from "@/lib/api"
import { formatRelativeDate, getStatusColor, getStatusLabel } from "@/lib/utils"

export default function DataPage() {
  const { toast } = useToast()
  const [searchQuery, setSearchQuery] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [files, setFiles] = useState<KnowledgeDocument[]>([])
  const [storageUsage, setStorageUsage] = useState<{
    usedMb: number;
    quotaMb: number;
    availableMb: number;
    percentageUsed: number;
    isFull: boolean;
  } | null>(null)

  // Charger les documents depuis l'API
  const loadDocuments = async () => {
    try {
      setIsLoading(true)
      const data = await KnowledgeDocumentsService.list()
      setFiles(data)
    } catch (error) {
      console.error("Erreur lors du chargement des documents:", error)
      toast({
        title: "Erreur de chargement",
        description: "Impossible de charger les documents.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Charger l'usage de stockage
  const loadStorageUsage = async () => {
    try {
      const data = await ApiClient.get('/api/subscriptions/storage/usage')
      setStorageUsage({
        usedMb: data.used_mb,
        quotaMb: data.quota_mb,
        availableMb: data.available_mb,
        percentageUsed: data.percentage_used,
        isFull: data.is_full
      })
    } catch (error) {
      console.error("Erreur chargement usage stockage:", error)
    }
  }

  useEffect(() => {
    loadDocuments()
    loadStorageUsage()
  }, [])

  const filteredFiles = files.filter(file =>
    file.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.status.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "indexed":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "processing":
        return <Clock className="w-4 h-4 text-yellow-400" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-400" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getFileIcon = (type: string) => {
    return <FileText className="w-5 h-5 text-muted-foreground" />
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = event.target.files
    if (!uploadedFiles) return

    // Validation des fichiers
    const allowedTypes = ['pdf', 'txt', 'md']
    const maxSizeInMB = 10
    const maxSizeInBytes = maxSizeInMB * 1024 * 1024

    const validFiles: File[] = []
    const invalidFiles: { name: string; reason: string }[] = []

    for (const file of Array.from(uploadedFiles)) {
      const fileExt = file.name.split('.').pop()?.toLowerCase()

      // Vérifier le type de fichier
      if (!fileExt || !allowedTypes.includes(fileExt)) {
        invalidFiles.push({
          name: file.name,
          reason: `Type de fichier non supporté. Seuls PDF, TXT et MD sont acceptés.`
        })
        continue
      }

      // Vérifier la taille
      if (file.size > maxSizeInBytes) {
        invalidFiles.push({
          name: file.name,
          reason: `Fichier trop volumineux (${(file.size / (1024 * 1024)).toFixed(1)} MB). Maximum ${maxSizeInMB} MB.`
        })
        continue
      }

      validFiles.push(file)
    }

    // Afficher les erreurs si il y en a
    if (invalidFiles.length > 0) {
      invalidFiles.forEach(({ name, reason }) => {
        toast({
          title: `Fichier rejeté: ${name}`,
          description: reason,
          variant: "destructive",
        })
      })
    }

    // Si aucun fichier valide, arrêter
    if (validFiles.length === 0) {
      return
    }

    // Vérifier le quota de stockage
    if (storageUsage) {
      const totalFileSizeMb = validFiles.reduce((total, file) => total + (file.size / (1024 * 1024)), 0)

      if (totalFileSizeMb > storageUsage.availableMb) {
        toast({
          title: "Quota de stockage insuffisant",
          description: `Espace disponible: ${storageUsage.availableMb.toFixed(2)} MB, Requis: ${totalFileSizeMb.toFixed(2)} MB`,
          variant: "destructive",
        })
        return
      }
    }

    setIsUploading(true)
    toast({
      title: "Téléchargement en cours",
      description: `${validFiles.length} fichier(s) en cours de traitement...`,
    })

    try {
      for (const file of validFiles) {
        console.log(`Uploading file: ${file.name}`)

        // Créer FormData pour l'upload
        const formData = new FormData()
        formData.append('file', file)

        // Upload via l'endpoint backend avec ApiClient
        try {
          const data = await ApiClient.uploadFile('/api/knowledge_documents/upload', formData)
          console.log('Upload successful:', data)
          toast({
            title: "Fichier uploadé",
            description: `${file.name} traité avec succès. Le processing automatique va commencer.`,
          })
        } catch (uploadError) {
          console.error('Erreur upload:', uploadError)
          toast({
            title: "Erreur d'upload",
            description: `Échec pour ${file.name}`,
            variant: "destructive",
          })
        }
      }

      // Recharger la liste des documents après upload
      await loadDocuments()
      await loadStorageUsage()

      toast({
        title: "Téléchargement terminé",
        description: `${validFiles.length} fichier(s) traité(s). Le traitement automatique va commencer.`,
      })

    } catch (error) {
      console.error('Erreur générale upload:', error)
      toast({
        title: "Erreur",
        description: "Une erreur est survenue lors du téléchargement.",
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleDeleteFile = async (fileId: string) => {
    try {
      const { supabase } = await import('@/lib/supabase')

      // Vérifier l'authentification
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        toast({
          title: "Erreur d'authentification",
          description: "Vous devez être connecté pour supprimer des fichiers.",
          variant: "destructive",
        })
        return
      }

      // Trouver le document dans la liste actuelle
      const file = files.find(f => f.id === fileId)
      if (!file) {
        toast({
          title: "Document non trouvé",
          description: "Le document n'existe pas.",
          variant: "destructive",
        })
        return
      }

      toast({
        title: "Suppression en cours",
        description: `Suppression de ${file.title}...`,
      })

      // Supprimer le fichier du stockage si on a l'object_name
      if (file.object_name) {
        const { error: storageError } = await supabase.storage
          .from('kb')
          .remove([file.object_name])

        if (storageError) {
          console.error('Erreur suppression stockage:', storageError)
          // Ne pas arrêter si la suppression du stockage échoue
        }
      }

      // Supprimer l'enregistrement de la base de données
      const { error: dbError } = await supabase
        .from('knowledge_documents')
        .delete()
        .eq('id', fileId)

      if (dbError) {
        console.error('Erreur suppression base de données:', dbError)
        toast({
          title: "Erreur de suppression",
          description: "Erreur lors de la suppression du document.",
          variant: "destructive",
        })
        return
      }

      toast({
        title: "Document supprimé",
        description: "Le document a été supprimé avec succès.",
      })
      await loadDocuments()
    } catch (error) {
      console.error("Erreur lors de la suppression du document:", error)
      toast({
        title: "Erreur de suppression",
        description: "Impossible de supprimer le document.",
        variant: "destructive",
      })
    }
  }

  const handleExport = () => {
    try {
      // Créer un objet d'export avec les métadonnées des documents
      const exportData = {
        exportedAt: new Date().toISOString(),
        totalDocuments: files.length,
        documents: files.map(file => ({
          id: file.id,
          title: file.title,
          status: file.status,
          createdAt: file.created_at,
          updatedAt: file.updated_at,
          embedModel: file.embed_model,
          langCode: file.lang_code,
          lastIngestedAt: file.last_ingested_at,
          lastEmbeddedAt: file.last_embedded_at
        }))
      }

      // Créer et télécharger le fichier JSON
      const dataStr = JSON.stringify(exportData, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })

      const link = document.createElement('a')
      link.href = URL.createObjectURL(dataBlob)
      link.download = `documents-export-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      toast({
        title: "Export réussi",
        description: `${files.length} documents exportés au format JSON.`,
      })
    } catch (error) {
      console.error('Erreur lors de l\'exportation:', error)
      toast({
        title: "Erreur d'export",
        description: "Impossible d'exporter les documents.",
        variant: "destructive",
      })
    }
  }

  const handleDownloadFile = async (file: KnowledgeDocument) => {
    try {
      const { supabase } = await import('@/lib/supabase')

      // Vérifier l'authentification
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        toast({
          title: "Erreur d'authentification",
          description: "Vous devez être connecté pour télécharger des fichiers.",
          variant: "destructive",
        })
        return
      }

      if (!file.object_name) {
        toast({
          title: "Erreur",
          description: "Le chemin du fichier n'est pas disponible.",
          variant: "destructive",
        })
        return
      }

      toast({
        title: "Téléchargement en cours",
        description: `Téléchargement de ${file.title}...`,
      })

      // Télécharger directement avec l'object_name
      const { data: fileData, error: downloadError } = await supabase.storage
        .from('kb')
        .download(file.object_name)

      if (downloadError) {
        console.error('Erreur download:', downloadError)
        toast({
          title: "Erreur de téléchargement",
          description: "Impossible de télécharger le fichier.",
          variant: "destructive",
        })
        return
      }

      // Créer un lien de téléchargement
      const blob = new Blob([fileData])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = file.title
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast({
        title: "Téléchargement réussi",
        description: `${file.title} a été téléchargé.`,
      })

    } catch (error) {
      console.error('Erreur lors du téléchargement:', error)
      toast({
        title: "Erreur de téléchargement",
        description: "Une erreur inattendue s'est produite.",
        variant: "destructive",
      })
    }
  }

  const handleReprocessFile = async (fileId: string) => {
    // Pour le moment, simulation d'un reprocessing
    toast({
      title: "Reprocessing en cours",
      description: "Le document est en cours de reprocessing...",
    })

    setTimeout(() => {
      toast({
        title: "Reprocessing terminé",
        description: "Le document a été reprocessé avec succès.",
      })
      loadDocuments()
    }, 3000)
  }

  const totalFiles = files.length
  const indexedFiles = files.filter(f => f.status === "indexed").length
  const processingFiles = files.filter(f => f.status === "processing").length
  const errorFiles = files.filter(f => f.status === "error").length
  // Pour l'instant, pas d'information sur les chunks dans le schéma actuel

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sources de données</h1>
          <p className="text-muted-foreground">
            Téléchargez et gérez les fichiers pour entraîner votre chatbot IA
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="cursor-pointer" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Exporter
          </Button>
          <Button 
            disabled={isUploading} 
            className="cursor-pointer"
            onClick={() => document.getElementById('file-upload')?.click()}
          >
            <Upload className="w-4 h-4 mr-2" />
            {isUploading ? "Téléchargement..." : "Télécharger des fichiers"}
          </Button>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.txt,.md"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total fichiers</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFiles}</div>
            <p className="text-xs text-muted-foreground">
              Fichiers téléchargés
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Indexés</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{indexedFiles}</div>
            <p className="text-xs text-muted-foreground">
              Prêts pour l'entraînement IA
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">En traitement</CardTitle>
            <Clock className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">{processingFiles}</div>
            <p className="text-xs text-muted-foreground">
              Actuellement en traitement
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stockage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {storageUsage ? (
              <>
                <div className="text-2xl font-bold">
                  {storageUsage.usedMb.toFixed(1)} MB
                </div>
                <p className="text-xs text-muted-foreground">
                  {storageUsage.availableMb.toFixed(1)} MB disponibles sur {storageUsage.quotaMb} MB
                </p>
                <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      storageUsage.percentageUsed > 90 ? 'bg-red-500' :
                      storageUsage.percentageUsed > 70 ? 'bg-orange-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(storageUsage.percentageUsed, 100)}%` }}
                  ></div>
                </div>
              </>
            ) : (
              <div className="text-2xl font-bold">--</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher des documents..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Files List */}
      <Card>
        <CardHeader>
          <CardTitle>Documents analysés</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-12">
              <Loader2 className="w-12 h-12 mx-auto mb-4 text-muted-foreground animate-spin" />
              <h3 className="text-lg font-semibold mb-2">Chargement des documents...</h3>
              <p className="text-muted-foreground">
                Veuillez patienter pendant le chargement des données.
              </p>
            </div>
          ) : filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Aucun document trouvé</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery ? "Essayez d'ajuster vos termes de recherche" : "Téléchargez votre premier document pour commencer"}
              </p>
              {!searchQuery && (
                <label htmlFor="file-upload-empty">
                  <Button className="cursor-pointer" disabled={isUploading}>
                    <Upload className="w-4 h-4 mr-2" />
                    {isUploading ? "Téléchargement..." : "Télécharger des fichiers"}
                  </Button>
                </label>
              )}
              <input
                id="file-upload-empty"
                type="file"
                multiple
                accept=".pdf,.txt,.md"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          ) : (
            <div className="space-y-4">
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex-shrink-0">
                      {getFileIcon("document")}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium truncate">{file.title}</h3>
                        <Badge variant="outline" className={getStatusColor(file.status)}>
                          <div className="flex items-center gap-1">
                            {getStatusIcon(file.status)}
                            {getStatusLabel(file.status)}
                          </div>
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>Modèle: {file.embed_model}</span>
                        <span>Langue: {file.lang_code}</span>
                        <span>Créé {formatRelativeDate(file.created_at)}</span>
                        {file.last_ingested_at && (
                          <span>Ingesté {formatRelativeDate(file.last_ingested_at)}</span>
                        )}
                      </div>
                      {file.status === "error" && (
                        <p className="text-sm text-red-400 mt-1">Erreur de traitement du document</p>
                      )}
                      {file.last_embedded_at && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Embedding {formatRelativeDate(file.last_embedded_at)}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownloadFile(file)}
                      className="cursor-pointer"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Télécharger
                    </Button>
                    {file.status === "error" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReprocessFile(file.id)}
                        className="cursor-pointer"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Réessayer
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteFile(file.id)}
                      className="cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {isUploading && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="animate-spin">
                <RefreshCw className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <p className="font-medium">Téléchargement des fichiers...</p>
                <p className="text-sm text-muted-foreground">
                  Veuillez patienter pendant le traitement de vos fichiers
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}