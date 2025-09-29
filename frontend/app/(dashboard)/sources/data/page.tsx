"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
  Database,
  Upload,
  Search,
  FileText,
  CheckCircle,
  AlertCircle,
  Clock,
  Settings,
  Trash2,
  Download,
  RefreshCw,
} from "lucide-react"

// Mock data for uploaded files
const mockFiles = [
  {
    id: "1",
    name: "product-documentation.pdf",
    size: "2.4 MB",
    type: "PDF",
    uploadDate: "2024-01-15T10:30:00Z",
    status: "indexed",
    chunks: 45,
    lastProcessed: "2024-01-15T10:35:00Z",
  },
  {
    id: "2",
    name: "faq-database.csv",
    size: "856 KB",
    type: "CSV",
    uploadDate: "2024-01-14T15:20:00Z",
    status: "processing",
    chunks: 0,
    lastProcessed: null,
  },
  {
    id: "3",
    name: "user-manual.docx",
    size: "1.8 MB",
    type: "DOCX",
    uploadDate: "2024-01-13T09:15:00Z",
    status: "indexed",
    chunks: 32,
    lastProcessed: "2024-01-13T09:20:00Z",
  },
  {
    id: "4",
    name: "api-reference.md",
    size: "345 KB",
    type: "Markdown",
    uploadDate: "2024-01-12T14:45:00Z",
    status: "error",
    chunks: 0,
    lastProcessed: null,
    error: "File format not supported",
  },
  {
    id: "5",
    name: "company-policies.txt",
    size: "123 KB",
    type: "TXT",
    uploadDate: "2024-01-11T11:30:00Z",
    status: "indexed",
    chunks: 15,
    lastProcessed: "2024-01-11T11:32:00Z",
  },
]

export default function DataPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isUploading, setIsUploading] = useState(false)
  const [files, setFiles] = useState(mockFiles)

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.type.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case "indexed":
        return "bg-green-500/20 text-green-400"
      case "processing":
        return "bg-yellow-500/20 text-yellow-400"
      case "error":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = event.target.files
    if (!uploadedFiles) return

    setIsUploading(true)
    
    // Simulate file upload process
    setTimeout(() => {
      Array.from(uploadedFiles).forEach((file, index) => {
        const newFile = {
          id: Date.now().toString() + index,
          name: file.name,
          size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
          type: file.name.split('.').pop()?.toUpperCase() || 'Unknown',
          uploadDate: new Date().toISOString(),
          status: "processing",
          chunks: 0,
          lastProcessed: null,
        }
        
        setFiles(prev => [newFile, ...prev])
      })
      setIsUploading(false)
    }, 2000)
  }

  const handleDeleteFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const handleReprocessFile = (fileId: string) => {
    setFiles(prev => prev.map(file =>
      file.id === fileId
        ? { ...file, status: "processing", error: undefined }
        : file
    ))
    
    // Simulate reprocessing
    setTimeout(() => {
      setFiles(prev => prev.map(file =>
        file.id === fileId
          ? { 
              ...file, 
              status: "indexed", 
              chunks: Math.floor(Math.random() * 50) + 10,
              lastProcessed: new Date().toISOString()
            }
          : file
      ))
    }, 3000)
  }

  const totalFiles = files.length
  const indexedFiles = files.filter(f => f.status === "indexed").length
  const processingFiles = files.filter(f => f.status === "processing").length
  const errorFiles = files.filter(f => f.status === "error").length
  const totalChunks = files.reduce((sum, file) => sum + file.chunks, 0)

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Sources</h1>
          <p className="text-muted-foreground">
            Upload and manage files to train your AI chatbot
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <label htmlFor="file-upload">
            <Button disabled={isUploading} className="cursor-pointer">
              <Upload className="w-4 h-4 mr-2" />
              {isUploading ? "Uploading..." : "Upload Files"}
            </Button>
          </label>
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt,.csv,.md"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFiles}</div>
            <p className="text-xs text-muted-foreground">
              Files uploaded
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Indexed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{indexedFiles}</div>
            <p className="text-xs text-muted-foreground">
              Ready for AI training
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <Clock className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">{processingFiles}</div>
            <p className="text-xs text-muted-foreground">
              Currently processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Knowledge Chunks</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalChunks}</div>
            <p className="text-xs text-muted-foreground">
              Indexed chunks
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Files List */}
      <Card>
        <CardHeader>
          <CardTitle>Uploaded Files</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredFiles.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No files found</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery ? "Try adjusting your search terms" : "Upload your first file to get started"}
              </p>
              {!searchQuery && (
                <label htmlFor="file-upload-empty">
                  <Button className="cursor-pointer">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Files
                  </Button>
                </label>
              )}
              <input
                id="file-upload-empty"
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt,.csv,.md"
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
                      {getFileIcon(file.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium truncate">{file.name}</h3>
                        <Badge variant="outline" className={getStatusColor(file.status)}>
                          <div className="flex items-center gap-1">
                            {getStatusIcon(file.status)}
                            {file.status}
                          </div>
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{file.type}</span>
                        <span>{file.size}</span>
                        <span>Uploaded {formatDate(file.uploadDate)}</span>
                        {file.status === "indexed" && (
                          <span>{file.chunks} chunks</span>
                        )}
                      </div>
                      {file.error && (
                        <p className="text-sm text-red-400 mt-1">{file.error}</p>
                      )}
                      {file.lastProcessed && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Last processed: {formatDate(file.lastProcessed)}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {file.status === "error" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReprocessFile(file.id)}
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Retry
                      </Button>
                    )}
                    <Button variant="outline" size="sm">
                      <Settings className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteFile(file.id)}
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
                <p className="font-medium">Uploading files...</p>
                <p className="text-sm text-muted-foreground">
                  Please wait while we process your files
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}