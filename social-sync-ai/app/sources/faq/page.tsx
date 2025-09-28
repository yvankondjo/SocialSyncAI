"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Header } from "@/components/header"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { HelpCircle, Plus, Search, Edit3, Trash2, Tag, CheckCircle, XCircle } from "lucide-react"

// Mock FAQ data
const mockFAQs = [
  {
    id: "1",
    questions: ["How do I reset my password?", "I forgot my password, what should I do?", "Password reset help"],
    answer:
      "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email.",
    tags: ["account", "password", "login"],
    isActive: true,
    updatedAt: "2024-01-15T10:30:00Z",
    source: "manual",
  },
  {
    id: "2",
    questions: ["What payment methods do you accept?", "How can I pay?"],
    answer:
      "We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and bank transfers for enterprise customers.",
    tags: ["payment", "billing", "methods"],
    isActive: true,
    updatedAt: "2024-01-15T09:15:00Z",
    source: "chat_edit",
  },
  {
    id: "3",
    questions: ["How do I cancel my subscription?"],
    answer:
      "You can cancel your subscription at any time from your account settings. Go to Billing > Subscription and click 'Cancel Subscription'.",
    tags: ["subscription", "billing", "cancel"],
    isActive: false,
    updatedAt: "2024-01-13T14:45:00Z",
    source: "import",
  },
]

export default function FAQPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [editingFAQ, setEditingFAQ] = useState<any>(null)
  const [isAddingNew, setIsAddingNew] = useState(false)
  const [newFAQ, setNewFAQ] = useState({
    questions: [""],
    answer: "",
    tags: "",
    isActive: true,
  })

  const filteredFAQs = mockFAQs.filter((faq) => {
    const matchesSearch =
      faq.questions.some((q) => q.toLowerCase().includes(searchQuery.toLowerCase())) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "active" && faq.isActive) ||
      (statusFilter === "inactive" && !faq.isActive)

    return matchesSearch && matchesStatus
  })

  const getSourceColor = (source: string) => {
    switch (source) {
      case "chat_edit":
        return "bg-blue-500/20 text-blue-400"
      case "manual":
        return "bg-green-500/20 text-green-400"
      case "import":
        return "bg-purple-500/20 text-purple-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
  }

  const handleSaveEdit = () => {
    // Save edited FAQ
    setEditingFAQ(null)
  }

  const handleAddNew = () => {
    // Add new FAQ
    setIsAddingNew(false)
    setNewFAQ({
      questions: [""],
      answer: "",
      tags: "",
      isActive: true,
    })
  }

  const addQuestion = (isEditing = false) => {
    if (isEditing && editingFAQ) {
      setEditingFAQ({ ...editingFAQ, questions: [...editingFAQ.questions, ""] })
    } else {
      setNewFAQ({ ...newFAQ, questions: [...newFAQ.questions, ""] })
    }
  }

  const removeQuestion = (index: number, isEditing = false) => {
    if (isEditing && editingFAQ) {
      const newQuestions = editingFAQ.questions.filter((_: any, i: number) => i !== index)
      setEditingFAQ({ ...editingFAQ, questions: newQuestions })
    } else {
      const newQuestions = newFAQ.questions.filter((_, i) => i !== index)
      setNewFAQ({ ...newFAQ, questions: newQuestions })
    }
  }

  const updateQuestion = (index: number, value: string, isEditing = false) => {
    if (isEditing && editingFAQ) {
      const newQuestions = [...editingFAQ.questions]
      newQuestions[index] = value
      setEditingFAQ({ ...editingFAQ, questions: newQuestions })
    } else {
      const newQuestions = [...newFAQ.questions]
      newQuestions[index] = value
      setNewFAQ({ ...newFAQ, questions: newQuestions })
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
              <h1 className="text-2xl font-bold">FAQ Management</h1>
              <p className="text-muted-foreground">Manage your frequently asked questions and answers</p>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setIsAddingNew(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add FAQ
              </Button>
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search questions, answers, or tags..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-border rounded-md bg-background text-foreground"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* FAQ List */}
          <div className="space-y-4">
            {filteredFAQs.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center h-32">
                  <div className="text-center text-muted-foreground">
                    <HelpCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No FAQs found</p>
                    <p className="text-sm">Try adjusting your search or filters</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              filteredFAQs.map((faq) => (
                <Card key={faq.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="space-y-1">
                            {faq.questions.map((question, index) => (
                              <h3 key={index} className="font-semibold text-lg">
                                {question}
                              </h3>
                            ))}
                          </div>
                          {faq.isActive ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                        </div>

                        <p className="text-muted-foreground">{faq.answer}</p>

                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            {faq.tags.map((tag) => (
                              <Badge key={tag} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                          <Badge variant="outline" className={getSourceColor(faq.source)}>
                            {faq.source.replace("_", " ")}
                          </Badge>
                          <span className="text-muted-foreground">
                            Updated {new Date(faq.updatedAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={() => setEditingFAQ(faq)}>
                          <Edit3 className="w-4 h-4" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Edit FAQ Dialog */}
      <Dialog open={!!editingFAQ} onOpenChange={() => setEditingFAQ(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit FAQ</DialogTitle>
          </DialogHeader>
          {editingFAQ && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Questions</Label>
                {editingFAQ.questions.map((question: string, index: number) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={question}
                      onChange={(e) => updateQuestion(index, e.target.value, true)}
                      placeholder={`Question ${index + 1}`}
                    />
                    {editingFAQ.questions.length > 1 && (
                      <Button variant="outline" size="sm" onClick={() => removeQuestion(index, true)}>
                        Remove
                      </Button>
                    )}
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={() => addQuestion(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Question
                </Button>
              </div>
              <div className="space-y-2">
                <Label>Answer</Label>
                <Textarea
                  value={editingFAQ.answer}
                  onChange={(e) => setEditingFAQ({ ...editingFAQ, answer: e.target.value })}
                  className="min-h-[120px]"
                />
              </div>
              <div className="space-y-2">
                <Label>Tags (comma separated)</Label>
                <Input
                  value={editingFAQ.tags.join(", ")}
                  onChange={(e) => setEditingFAQ({ ...editingFAQ, tags: e.target.value.split(", ") })}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Switch
                    checked={editingFAQ.isActive}
                    onCheckedChange={(checked) => setEditingFAQ({ ...editingFAQ, isActive: checked })}
                  />
                  <Label>Active</Label>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setEditingFAQ(null)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSaveEdit}>Save Changes</Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add FAQ Dialog */}
      <Dialog open={isAddingNew} onOpenChange={setIsAddingNew}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New FAQ</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Questions</Label>
              {newFAQ.questions.map((question, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    value={question}
                    onChange={(e) => updateQuestion(index, e.target.value)}
                    placeholder={`Question ${index + 1}`}
                  />
                  {newFAQ.questions.length > 1 && (
                    <Button variant="outline" size="sm" onClick={() => removeQuestion(index)}>
                      Remove
                    </Button>
                  )}
                </div>
              ))}
              <Button variant="outline" size="sm" onClick={() => addQuestion()}>
                <Plus className="w-4 h-4 mr-2" />
                Add Question
              </Button>
            </div>
            <div className="space-y-2">
              <Label>Answer</Label>
              <Textarea
                value={newFAQ.answer}
                onChange={(e) => setNewFAQ({ ...newFAQ, answer: e.target.value })}
                placeholder="Enter the answer..."
                className="min-h-[120px]"
              />
            </div>
            <div className="space-y-2">
              <Label>Tags (comma separated)</Label>
              <Input
                value={newFAQ.tags}
                onChange={(e) => setNewFAQ({ ...newFAQ, tags: e.target.value })}
                placeholder="tag1, tag2, tag3"
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Switch
                  checked={newFAQ.isActive}
                  onCheckedChange={(checked) => setNewFAQ({ ...newFAQ, isActive: checked })}
                />
                <Label>Active</Label>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setIsAddingNew(false)}>
                  Cancel
                </Button>
                <Button onClick={handleAddNew}>Add FAQ</Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
