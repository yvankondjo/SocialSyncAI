"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Globe,
  Plus,
  Settings,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Copy,
  ExternalLink,
  Shield,
  Info,
} from "lucide-react"

interface Domain {
  id: string
  domain: string
  status: "pending" | "active" | "failed" | "expired"
  sslStatus: "pending" | "active" | "failed"
  createdAt: string
  expiresAt?: string
  dnsRecords: {
    type: string
    name: string
    value: string
    status: "pending" | "verified"
  }[]
}

const mockDomains: Domain[] = [
  {
    id: "1",
    domain: "chat.mycompany.com",
    status: "active",
    sslStatus: "active",
    createdAt: "2024-01-15T10:30:00Z",
    expiresAt: "2024-04-15T10:30:00Z",
    dnsRecords: [
      {
        type: "CNAME",
        name: "chat",
        value: "widget.socialsync.ai",
        status: "verified"
      },
      {
        type: "TXT",
        name: "_socialsync-verification",
        value: "socialsync-verification=abc123def456",
        status: "verified"
      }
    ]
  },
  {
    id: "2", 
    domain: "support.example.org",
    status: "pending",
    sslStatus: "pending",
    createdAt: "2024-01-14T15:20:00Z",
    dnsRecords: [
      {
        type: "CNAME",
        name: "support",
        value: "widget.socialsync.ai",
        status: "pending"
      },
      {
        type: "TXT",
        name: "_socialsync-verification",
        value: "socialsync-verification=xyz789ghi012",
        status: "pending"
      }
    ]
  },
]

export default function CustomDomainsPage() {
  const [domains, setDomains] = useState<Domain[]>(mockDomains)
  const [isAddingDomain, setIsAddingDomain] = useState(false)
  const [newDomain, setNewDomain] = useState("")
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/20 text-green-400"
      case "pending":
        return "bg-yellow-500/20 text-yellow-400"
      case "failed":
        return "bg-red-500/20 text-red-400"
      case "expired":
        return "bg-gray-500/20 text-gray-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "pending":
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      case "failed":
      case "expired":
        return <AlertTriangle className="w-4 h-4 text-red-400" />
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-400" />
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const handleAddDomain = () => {
    if (!newDomain.trim()) return

    const domain: Domain = {
      id: Date.now().toString(),
      domain: newDomain.trim(),
      status: "pending",
      sslStatus: "pending",
      createdAt: new Date().toISOString(),
      dnsRecords: [
        {
          type: "CNAME",
          name: newDomain.split('.')[0],
          value: "widget.socialsync.ai",
          status: "pending"
        },
        {
          type: "TXT",
          name: "_socialsync-verification",
          value: `socialsync-verification=${Math.random().toString(36).substr(2, 12)}`,
          status: "pending"
        }
      ]
    }

    setDomains(prev => [domain, ...prev])
    setNewDomain("")
    setIsAddingDomain(false)
  }

  const handleDeleteDomain = (domainId: string) => {
    setDomains(prev => prev.filter(d => d.id !== domainId))
  }

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // Toast notification would be shown here
  }

  const handleVerifyDomain = (domainId: string) => {
    // Simulate verification
    setDomains(prev => prev.map(domain => 
      domain.id === domainId 
        ? { 
            ...domain, 
            status: "active", 
            sslStatus: "active",
            dnsRecords: domain.dnsRecords.map(record => ({ ...record, status: "verified" as const }))
          }
        : domain
    ))
  }

  const activeDomains = domains.filter(d => d.status === "active").length
  const pendingDomains = domains.filter(d => d.status === "pending").length
  const totalDomains = domains.length

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Custom Domains</h1>
          <p className="text-muted-foreground">
            Use your own domain for the chat widget and admin interface
          </p>
        </div>
        <Button onClick={() => setIsAddingDomain(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Domain
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Domains</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDomains}</div>
            <p className="text-xs text-muted-foreground">
              Configured domains
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{activeDomains}</div>
            <p className="text-xs text-muted-foreground">
              Verified & working
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <AlertTriangle className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">{pendingDomains}</div>
            <p className="text-xs text-muted-foreground">
              Awaiting verification
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Domains List */}
      <div className="space-y-4">
        {domains.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Globe className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No custom domains</h3>
              <p className="text-muted-foreground mb-4">
                Add your first custom domain to get started
              </p>
              <Button onClick={() => setIsAddingDomain(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Domain
              </Button>
            </CardContent>
          </Card>
        ) : (
          domains.map((domain) => (
            <Card key={domain.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-lg">{domain.domain}</h3>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(domain.status)}
                        <Badge variant="outline" className={getStatusColor(domain.status)}>
                          {domain.status}
                        </Badge>
                        {domain.sslStatus === "active" && (
                          <Badge variant="outline" className="bg-green-500/20 text-green-400">
                            <Shield className="w-3 h-3 mr-1" />
                            SSL Active
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="grid gap-2 text-sm text-muted-foreground">
                      <div>Created: {formatDate(domain.createdAt)}</div>
                      {domain.expiresAt && (
                        <div>SSL Expires: {formatDate(domain.expiresAt)}</div>
                      )}
                      <div>DNS Records: {domain.dnsRecords.filter(r => r.status === "verified").length}/{domain.dnsRecords.length} verified</div>
                    </div>

                    {domain.status === "pending" && (
                      <Alert>
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                          Please configure the DNS records below and wait for propagation (may take up to 24 hours).
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {domain.status === "pending" && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleVerifyDomain(domain.id)}
                      >
                        Verify
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedDomain(domain)}
                    >
                      <Settings className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteDomain(domain.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {domain.status === "pending" && (
                  <div className="mt-4 p-4 bg-muted rounded-lg">
                    <h4 className="font-medium mb-3">Required DNS Records:</h4>
                    <div className="space-y-3">
                      {domain.dnsRecords.map((record, index) => (
                        <div key={index} className="grid gap-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium">{record.type} Record</span>
                            <Badge variant="outline" className={getStatusColor(record.status)}>
                              {record.status}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <Label>Name</Label>
                              <div className="flex items-center gap-2">
                                <code className="bg-background px-2 py-1 rounded text-xs">{record.name}</code>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopyToClipboard(record.name)}
                                >
                                  <Copy className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                            <div className="col-span-2">
                              <Label>Value</Label>
                              <div className="flex items-center gap-2">
                                <code className="bg-background px-2 py-1 rounded text-xs flex-1 truncate">{record.value}</code>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleCopyToClipboard(record.value)}
                                >
                                  <Copy className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Add Domain Dialog */}
      <Dialog open={isAddingDomain} onOpenChange={setIsAddingDomain}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Custom Domain</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Domain Name</Label>
              <Input
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="chat.yourcompany.com"
              />
              <p className="text-xs text-muted-foreground">
                Enter the full domain name you want to use for your chat widget
              </p>
            </div>

            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                After adding the domain, you'll need to configure DNS records with your domain provider.
                We'll provide step-by-step instructions.
              </AlertDescription>
            </Alert>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setIsAddingDomain(false)}>
              Cancel
            </Button>
            <Button onClick={handleAddDomain} disabled={!newDomain.trim()}>
              Add Domain
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Domain Details Dialog */}
      <Dialog open={!!selectedDomain} onOpenChange={() => setSelectedDomain(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedDomain?.domain} - Configuration</DialogTitle>
          </DialogHeader>
          {selectedDomain && (
            <Tabs defaultValue="dns">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="dns">DNS Setup</TabsTrigger>
                <TabsTrigger value="ssl">SSL Certificate</TabsTrigger>
                <TabsTrigger value="usage">Usage</TabsTrigger>
              </TabsList>

              <TabsContent value="dns" className="space-y-4">
                <div className="space-y-4">
                  <h4 className="font-medium">DNS Configuration</h4>
                  {selectedDomain.dnsRecords.map((record, index) => (
                    <div key={index} className="p-4 border rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{record.type} Record</span>
                        <Badge variant="outline" className={getStatusColor(record.status)}>
                          {record.status}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>Name</Label>
                          <code className="block bg-muted px-2 py-1 rounded text-sm">{record.name}</code>
                        </div>
                        <div>
                          <Label>Value</Label>
                          <code className="block bg-muted px-2 py-1 rounded text-sm truncate">{record.value}</code>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="ssl" className="space-y-4">
                <div className="space-y-4">
                  <h4 className="font-medium">SSL Certificate Status</h4>
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      {selectedDomain.sslStatus === "active" ? (
                        <CheckCircle className="w-5 h-5 text-green-400" />
                      ) : (
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                      )}
                      <span className="font-medium">
                        SSL Certificate: {selectedDomain.sslStatus}
                      </span>
                    </div>
                    {selectedDomain.expiresAt && (
                      <p className="text-sm text-muted-foreground">
                        Expires: {formatDate(selectedDomain.expiresAt)}
                      </p>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="usage" className="space-y-4">
                <div className="space-y-4">
                  <h4 className="font-medium">How to Use Your Domain</h4>
                  <div className="space-y-3">
                    <div className="p-4 border rounded-lg">
                      <h5 className="font-medium mb-2">Widget Integration</h5>
                      <p className="text-sm text-muted-foreground mb-2">
                        Use this domain in your widget script:
                      </p>
                      <code className="block bg-muted p-2 rounded text-sm">
                        {`<script src="https://${selectedDomain.domain}/widget.js"></script>`}
                      </code>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h5 className="font-medium mb-2">Admin Interface</h5>
                      <p className="text-sm text-muted-foreground mb-2">
                        Access your admin panel at:
                      </p>
                      <div className="flex items-center gap-2">
                        <code className="bg-muted p-2 rounded text-sm flex-1">
                          https://{selectedDomain.domain}/admin
                        </code>
                        <Button variant="outline" size="sm">
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}