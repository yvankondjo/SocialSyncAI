"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import {
  Globe,
  Plus,
  RefreshCw,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  Copy,
  ExternalLink,
  Shield,
} from "lucide-react"

// Mock domains data
const mockDomains = [
  {
    id: "1",
    domain: "chat.mycompany.com",
    status: "active",
    sslStatus: "active",
    createdAt: "2024-01-10T10:30:00Z",
    lastChecked: "2024-01-15T10:30:00Z",
    dnsRecords: [
      { type: "CNAME", name: "chat", value: "widget.socialsyncai.com", status: "verified" },
      { type: "TXT", name: "_socialsync-verification", value: "abc123def456", status: "verified" },
    ],
  },
  {
    id: "2",
    domain: "support.example.org",
    status: "pending_dns",
    sslStatus: "pending",
    createdAt: "2024-01-14T15:20:00Z",
    lastChecked: "2024-01-15T09:45:00Z",
    dnsRecords: [
      { type: "CNAME", name: "support", value: "widget.socialsyncai.com", status: "pending" },
      { type: "TXT", name: "_socialsync-verification", value: "xyz789uvw012", status: "pending" },
    ],
  },
  {
    id: "3",
    domain: "help.startup.io",
    status: "error",
    sslStatus: "error",
    createdAt: "2024-01-12T08:15:00Z",
    lastChecked: "2024-01-15T08:30:00Z",
    error: "DNS resolution failed",
    dnsRecords: [
      { type: "CNAME", name: "help", value: "widget.socialsyncai.com", status: "error" },
      { type: "TXT", name: "_socialsync-verification", value: "mno345pqr678", status: "error" },
    ],
  },
]

export default function CustomDomainsPage() {
  const [domains, setDomains] = useState(mockDomains)
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [newDomain, setNewDomain] = useState("")
  const [selectedDomain, setSelectedDomain] = useState<any>(null)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case "pending_dns":
        return <Clock className="w-4 h-4 text-yellow-400" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-400" />
      default:
        return <Clock className="w-4 h-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-500/20 text-green-400"
      case "pending_dns":
        return "bg-yellow-500/20 text-yellow-400"
      case "error":
        return "bg-red-500/20 text-red-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "active":
        return "Active"
      case "pending_dns":
        return "Pending DNS"
      case "error":
        return "Error"
      default:
        return "Unknown"
    }
  }

  const handleAddDomain = () => {
    if (!newDomain.trim()) return

    const domain = {
      id: Date.now().toString(),
      domain: newDomain.trim(),
      status: "pending_dns",
      sslStatus: "pending",
      createdAt: new Date().toISOString(),
      lastChecked: new Date().toISOString(),
      dnsRecords: [
        {
          type: "CNAME",
          name: newDomain.split(".")[0],
          value: "widget.socialsyncai.com",
          status: "pending",
        },
        {
          type: "TXT",
          name: "_socialsync-verification",
          value: Math.random().toString(36).substring(2, 15),
          status: "pending",
        },
      ],
    }

    setDomains([...domains, domain])
    setNewDomain("")
    setShowAddDialog(false)
  }

  const handleRecheck = (domainId: string) => {
    // Simulate recheck
    setDomains(
      domains.map((d) =>
        d.id === domainId
          ? {
              ...d,
              lastChecked: new Date().toISOString(),
              status: Math.random() > 0.5 ? "active" : "pending_dns",
            }
          : d,
      ),
    )
  }

  const handleRemove = (domainId: string) => {
    setDomains(domains.filter((d) => d.id !== domainId))
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Globe className="w-6 h-6" />
                Custom Domains
              </h1>
              <p className="text-muted-foreground">
                Use your own domain for the chat widget and improve brand consistency
              </p>
            </div>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Domain
            </Button>
          </div>

          {/* Domains List */}
          <div className="space-y-4">
            {domains.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center h-32">
                  <div className="text-center text-muted-foreground">
                    <Globe className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No custom domains configured</p>
                    <p className="text-sm">Add a domain to get started</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              domains.map((domain) => (
                <Card key={domain.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="text-lg font-semibold">{domain.domain}</h3>
                          {getStatusIcon(domain.status)}
                          <Badge variant="outline" className={getStatusColor(domain.status)}>
                            {getStatusText(domain.status)}
                          </Badge>
                          {domain.sslStatus === "active" && (
                            <Badge variant="outline" className="bg-green-500/20 text-green-400">
                              <Shield className="w-3 h-3 mr-1" />
                              SSL Active
                            </Badge>
                          )}
                        </div>

                        {domain.error && (
                          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-4">
                            <p className="text-red-400 text-sm">{domain.error}</p>
                          </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <div className="text-sm font-medium mb-2">DNS Records</div>
                            <div className="space-y-2">
                              {domain.dnsRecords.map((record, index) => (
                                <div key={index} className="flex items-center justify-between text-sm">
                                  <div className="flex items-center gap-2">
                                    <Badge variant="outline" className="text-xs">
                                      {record.type}
                                    </Badge>
                                    <span className="font-mono">{record.name}</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-muted-foreground font-mono text-xs">{record.value}</span>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => navigator.clipboard.writeText(record.value)}
                                    >
                                      <Copy className="w-3 h-3" />
                                    </Button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div>
                            <div className="text-sm font-medium mb-2">Status Information</div>
                            <div className="space-y-1 text-sm text-muted-foreground">
                              <div>Created: {new Date(domain.createdAt).toLocaleDateString()}</div>
                              <div>Last checked: {new Date(domain.lastChecked).toLocaleString()}</div>
                              {domain.status === "active" && (
                                <div className="flex items-center gap-1 text-green-400">
                                  <ExternalLink className="w-3 h-3" />
                                  <a
                                    href={`https://${domain.domain}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:underline"
                                  >
                                    Visit domain
                                  </a>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2 ml-4">
                        <Button variant="outline" size="sm" onClick={() => handleRecheck(domain.id)}>
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => setSelectedDomain(domain)}>
                          View Details
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRemove(domain.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Setup Instructions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold mb-2">1. Add DNS Records</h4>
                  <p className="text-sm text-muted-foreground mb-3">
                    Add the following DNS records to your domain provider:
                  </p>
                  <div className="bg-muted p-3 rounded-lg text-sm font-mono">
                    <div>Type: CNAME</div>
                    <div>Name: your-subdomain</div>
                    <div>Value: widget.socialsyncai.com</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold mb-2">2. Verification</h4>
                  <p className="text-sm text-muted-foreground mb-3">Add this TXT record for domain verification:</p>
                  <div className="bg-muted p-3 rounded-lg text-sm font-mono">
                    <div>Type: TXT</div>
                    <div>Name: _socialsync-verification</div>
                    <div>Value: [generated-token]</div>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-2">3. SSL Certificate</h4>
                <p className="text-sm text-muted-foreground">
                  Once DNS records are verified, we'll automatically provision an SSL certificate using Let's Encrypt.
                  This process usually takes 5-10 minutes.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Add Domain Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Custom Domain</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Domain Name</Label>
              <Input
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="chat.yourcompany.com"
              />
              <p className="text-xs text-muted-foreground">
                Enter the full subdomain you want to use for your chat widget
              </p>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
              <h4 className="font-semibold text-blue-400 mb-2">Before you continue:</h4>
              <ul className="text-sm text-blue-300 space-y-1">
                <li>• Make sure you have access to your domain's DNS settings</li>
                <li>• Choose a subdomain (e.g., chat, support, help)</li>
                <li>• DNS changes can take up to 24 hours to propagate</li>
              </ul>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAddDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddDomain} disabled={!newDomain.trim()}>
                Add Domain
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Domain Details Dialog */}
      <Dialog open={!!selectedDomain} onOpenChange={() => setSelectedDomain(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Domain Details: {selectedDomain?.domain}</DialogTitle>
          </DialogHeader>
          {selectedDomain && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Status</Label>
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusIcon(selectedDomain.status)}
                    <Badge variant="outline" className={getStatusColor(selectedDomain.status)}>
                      {getStatusText(selectedDomain.status)}
                    </Badge>
                  </div>
                </div>
                <div>
                  <Label>SSL Status</Label>
                  <div className="flex items-center gap-2 mt-1">
                    {selectedDomain.sslStatus === "active" ? (
                      <CheckCircle className="w-4 h-4 text-green-400" />
                    ) : (
                      <Clock className="w-4 h-4 text-yellow-400" />
                    )}
                    <Badge
                      variant="outline"
                      className={
                        selectedDomain.sslStatus === "active"
                          ? "bg-green-500/20 text-green-400"
                          : "bg-yellow-500/20 text-yellow-400"
                      }
                    >
                      {selectedDomain.sslStatus}
                    </Badge>
                  </div>
                </div>
              </div>

              <div>
                <Label>DNS Records</Label>
                <div className="mt-2 space-y-2">
                  {selectedDomain.dnsRecords.map((record: any, index: number) => (
                    <div key={index} className="bg-muted p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-mono text-sm">
                            {record.type} {record.name} → {record.value}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={
                              record.status === "verified"
                                ? "bg-green-500/20 text-green-400"
                                : record.status === "error"
                                  ? "bg-red-500/20 text-red-400"
                                  : "bg-yellow-500/20 text-yellow-400"
                            }
                          >
                            {record.status}
                          </Badge>
                          <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(record.value)}>
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setSelectedDomain(null)}>
                  Close
                </Button>
                <Button onClick={() => handleRecheck(selectedDomain.id)}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Recheck Status
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
