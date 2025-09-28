"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Database, RefreshCw, Settings, FileText, Upload, CheckCircle, AlertCircle, Clock, Search } from "lucide-react"

// Mock data for data sources
const mockDataSources = [
  {
    id: "1",
    name: "Supabase Database",
    type: "supabase",
    status: "connected",
    lastSync: "2024-01-15T10:30:00Z",
    itemCount: 1250,
    description: "Main application database",
  },
  {
    id: "2",
    name: "Customer Support CSV",
    type: "csv",
    status: "syncing",
    lastSync: "2024-01-15T09:15:00Z",
    itemCount: 850,
    description: "Historical support tickets",
    syncProgress: 65,
  },
  {
    id: "3",
    name: "Google Drive Documents",
    type: "gdrive",
    status: "needs_auth",
    lastSync: "2024-01-14T15:20:00Z",
    itemCount: 0,
    description: "Company documentation",
  },
  {
    id: "4",
    name: "S3 Knowledge Base",
    type: "s3",
    status: "connected",
    lastSync: "2024-01-15T08:45:00Z",
    itemCount: 2100,
    description: "Product documentation and guides",
  },
]

const mockFiles = [
  {
    id: "1",
    name: "product-guide.pdf",
    size: "2.4 MB",
    type: "PDF",
    uploadDate: "2024-01-15T10:30:00Z",
    status: "indexed",
  },
  {
    id: "2",
    name: "faq-data.csv",
    size: "156 KB",
    type: "CSV",
    uploadDate: "2024-01-15T09:15:00Z",
    status: "processing",
  },
  {
    id: "3",
    name: "support-tickets.json",
    size: "5.8 MB",
    type: "JSON",
    uploadDate: "2024-01-14T16:20:00Z",
    status: "indexed",
  },
]

export default function DataSourcesPage() {
  const [searchQuery, setSearchQuery] = useState("")

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "syncing":
        return <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
      case "needs_auth":
        return <AlertCircle className="w-4 h-4 text-yellow-400" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-green-500/20 text-green-400"
      case "syncing":
        return "bg-blue-500/20 text-blue-400"
      case "needs_auth":
        return "bg-yellow-500/20 text-yellow-400"
      case "indexed":
        return "bg-green-500/20 text-green-400"
      case "processing":
        return "bg-blue-500/20 text-blue-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "supabase":
      case "postgres":
        return <Database className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Data Sources</h1>
              <p className="text-muted-foreground">Manage your file uploads</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline">
                <Upload className="w-4 h-4 mr-2" />
                Upload Files
              </Button>
            </div>
          </div>

          {/* Search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Data Sources */}
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">Uploaded Files</h2>
              <Card>
                <CardContent className="p-0">
                  <div className="divide-y divide-border">
                    {mockFiles.map((file) => (
                      <div key={file.id} className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{file.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {file.size} • {file.type} • {new Date(file.uploadDate).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className={getStatusColor(file.status)}>
                            {file.status}
                          </Badge>
                          <Button variant="ghost" size="sm">
                            <Settings className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
