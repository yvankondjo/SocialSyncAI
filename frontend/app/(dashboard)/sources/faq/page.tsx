"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  HelpCircle,
  Plus,
  Search,
  Edit3,
  Trash2,
  Tag,
  CheckCircle,
  XCircle,
  X,
  Save,
} from "lucide-react"

interface FAQ {
  id: string
  questions: string[]
  answer: string
  tags: string[]
  isActive: boolean
  updatedAt: string
  source: "manual" | "chat_edit" | "import"
}

// Mock data for FAQs
const mockFAQs: FAQ[] = [
  {
    id: "1",
    questions: [
      "How do I reset my password?",
      "I forgot my password, what should I do?",
      "Can you help me reset my account password?",
      "Password reset procedure"
    ],
    answer: "To reset your password, go to the login page and click 'Forgot Password'. Enter your email address and follow the instructions sent to your email.",
    tags: ["account", "password", "security"],
    isActive: true,
    updatedAt: "2024-01-15T10:30:00Z",
    source: "manual",
  },
  {
    id: "2",
    questions: [
      "What payment methods do you accept?",
      "How can I pay for my subscription?",
      "Do you accept credit cards?"
    ],
    answer: "We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and bank transfers for annual subscriptions.",
    tags: ["billing", "payment", "subscription"],
    isActive: true,
    updatedAt: "2024-01-14T15:20:00Z",
    source: "chat_edit",
  },
  {
    id: "3",
    questions: [
      "How do I upgrade my plan?",
      "Can I change my subscription tier?",
      "Upgrade to premium account"
    ],
    answer: "You can upgrade your plan anytime from your account settings. Go to Billing > Change Plan and select your desired tier.",
    tags: ["billing", "upgrade", "plans"],
    isActive: true,
    updatedAt: "2024-01-13T09:15:00Z",
    source: "manual",
  },
  {
    id: "4",
    questions: [
      "Is there a mobile app available?",
      "Do you have an iOS/Android app?"
    ],
    answer: "Yes! We have mobile apps for both iOS and Android. You can download them from the App Store or Google Play Store.",
    tags: ["mobile", "app", "download"],
    isActive: false,
    updatedAt: "2024-01-12T14:45:00Z",
    source: "import",
  },
]

export default function FAQPage() {
  const [faqs, setFaqs] = useState<FAQ[]>(mockFAQs)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [editingFAQ, setEditingFAQ] = useState<FAQ | null>(null)
  const [isAddingFAQ, setIsAddingFAQ] = useState(false)
  const [newFAQ, setNewFAQ] = useState<Partial<FAQ>>({
    questions: [""],
    answer: "",
    tags: [],
    isActive: true,
    source: "manual"
  })
  const [newTag, setNewTag] = useState("")

  const filteredFAQs = faqs.filter(faq => {
    const matchesSearch = 
      faq.questions.some(q => q.toLowerCase().includes(searchQuery.toLowerCase())) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesStatus = statusFilter === "all" || 
      (statusFilter === "active" && faq.isActive) ||
      (statusFilter === "inactive" && !faq.isActive)

    return matchesSearch && matchesStatus
  })

  const getSourceColor = (source: string) => {
    switch (source) {
      case "manual":
        return "bg-blue-500/20 text-blue-400"
      case "chat_edit":
        return "bg-green-500/20 text-green-400"
      case "import":
        return "bg-purple-500/20 text-purple-400"
      default:
        return "bg-gray-500/20 text-gray-400"
    }
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

  const handleAddQuestion = (faqData: Partial<FAQ>, setFaqData: (data: Partial<FAQ>) => void) => {
    setFaqData({
      ...faqData,
      questions: [...(faqData.questions || []), ""]
    })
  }

  const handleRemoveQuestion = (index: number, faqData: Partial<FAQ>, setFaqData: (data: Partial<FAQ>) => void) => {
    const newQuestions = faqData.questions?.filter((_, i) => i !== index) || []
    setFaqData({
      ...faqData,
      questions: newQuestions.length > 0 ? newQuestions : [""]
    })
  }

  const handleQuestionChange = (index: number, value: string, faqData: Partial<FAQ>, setFaqData: (data: Partial<FAQ>) => void) => {
    const newQuestions = [...(faqData.questions || [])]
    newQuestions[index] = value
    setFaqData({
      ...faqData,
      questions: newQuestions
    })
  }

  const handleAddTag = (faqData: Partial<FAQ>, setFaqData: (data: Partial<FAQ>) => void) => {
    if (newTag.trim() && !faqData.tags?.includes(newTag.trim())) {
      setFaqData({
        ...faqData,
        tags: [...(faqData.tags || []), newTag.trim()]
      })
      setNewTag("")
    }
  }

  const handleRemoveTag = (tagToRemove: string, faqData: Partial<FAQ>, setFaqData: (data: Partial<FAQ>) => void) => {
    setFaqData({
      ...faqData,
      tags: faqData.tags?.filter(tag => tag !== tagToRemove) || []
    })
  }

  const handleSaveFAQ = (faqData: Partial<FAQ>) => {
    const validQuestions = faqData.questions?.filter(q => q.trim()) || []
    if (validQuestions.length === 0 || !faqData.answer?.trim()) return

    const faqToSave: FAQ = {
      id: faqData.id || Date.now().toString(),
      questions: validQuestions,
      answer: faqData.answer,
      tags: faqData.tags || [],
      isActive: faqData.isActive ?? true,
      updatedAt: new Date().toISOString(),
      source: faqData.source || "manual"
    }

    if (faqData.id) {
      // Update existing FAQ
      setFaqs(prev => prev.map(faq => faq.id === faqData.id ? faqToSave : faq))
    } else {
      // Add new FAQ
      setFaqs(prev => [faqToSave, ...prev])
    }

    setEditingFAQ(null)
    setIsAddingFAQ(false)
    setNewFAQ({
      questions: [""],
      answer: "",
      tags: [],
      isActive: true,
      source: "manual"
    })
  }

  const handleDeleteFAQ = (faqId: string) => {
    setFaqs(prev => prev.filter(faq => faq.id !== faqId))
  }

  const handleEditFAQ = (faq: FAQ) => {
    setEditingFAQ({ ...faq })
  }

  const totalFAQs = faqs.length
  const activeFAQs = faqs.filter(f => f.isActive).length
  const inactiveFAQs = faqs.filter(f => !f.isActive).length
  const totalQuestions = faqs.reduce((sum, faq) => sum + faq.questions.length, 0)

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">FAQ Management</h1>
          <p className="text-muted-foreground">
            Manage frequently asked questions and answers for your AI chatbot
          </p>
        </div>
        <Button onClick={() => setIsAddingFAQ(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add FAQ
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total FAQs</CardTitle>
            <HelpCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFAQs}</div>
            <p className="text-xs text-muted-foreground">
              FAQ entries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{activeFAQs}</div>
            <p className="text-xs text-muted-foreground">
              Published FAQs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inactive</CardTitle>
            <XCircle className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-400">{inactiveFAQs}</div>
            <p className="text-xs text-muted-foreground">
              Draft FAQs
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Questions</CardTitle>
            <Tag className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalQuestions}</div>
            <p className="text-xs text-muted-foreground">
              Total questions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search FAQs, answers, tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* FAQ List */}
      <div className="space-y-4">
        {filteredFAQs.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <HelpCircle className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No FAQs found</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery ? "Try adjusting your search terms" : "Create your first FAQ to get started"}
              </p>
              {!searchQuery && (
                <Button onClick={() => setIsAddingFAQ(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add FAQ
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          filteredFAQs.map((faq) => (
            <Card key={faq.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      {faq.isActive ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-gray-400" />
                      )}
                      <Badge variant="outline" className={getSourceColor(faq.source)}>
                        {faq.source}
                      </Badge>
                      {faq.tags.map((tag, index) => (
                        <Badge key={index} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">
                        Questions ({faq.questions.length})
                      </Label>
                      <div className="space-y-1">
                        {faq.questions.map((question, index) => (
                          <div key={index} className="text-sm font-medium">
                            {index + 1}. {question}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-muted-foreground">
                        Answer
                      </Label>
                      <p className="text-sm text-muted-foreground">{faq.answer}</p>
                    </div>

                    <div className="text-xs text-muted-foreground">
                      Last updated: {formatDate(faq.updatedAt)}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditFAQ(faq)}
                    >
                      <Edit3 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteFAQ(faq.id)}
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

      {/* Add/Edit FAQ Dialog */}
      <Dialog open={isAddingFAQ || !!editingFAQ} onOpenChange={() => {
        setIsAddingFAQ(false)
        setEditingFAQ(null)
        setNewFAQ({
          questions: [""],
          answer: "",
          tags: [],
          isActive: true,
          source: "manual"
        })
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingFAQ ? "Edit FAQ" : "Add New FAQ"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Questions Section */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">
                Questions (Multiple questions for the same answer)
              </Label>
              {(editingFAQ?.questions || newFAQ.questions || [""]).map((question, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground w-6">{index + 1}.</span>
                  <Input
                    value={question}
                    onChange={(e) => handleQuestionChange(
                      index, 
                      e.target.value, 
                      editingFAQ || newFAQ,
                      editingFAQ ? setEditingFAQ : setNewFAQ
                    )}
                    placeholder="Enter a question..."
                    className="flex-1"
                  />
                  {((editingFAQ?.questions || newFAQ.questions || []).length > 1) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRemoveQuestion(
                        index, 
                        editingFAQ || newFAQ,
                        editingFAQ ? setEditingFAQ : setNewFAQ
                      )}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAddQuestion(
                  editingFAQ || newFAQ,
                  editingFAQ ? setEditingFAQ : setNewFAQ
                )}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Question
              </Button>
            </div>

            {/* Answer Section */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Answer</Label>
              <Textarea
                value={editingFAQ?.answer || newFAQ.answer || ""}
                onChange={(e) => {
                  const faqData = editingFAQ || newFAQ
                  const setFaqData = editingFAQ ? setEditingFAQ : setNewFAQ
                  setFaqData({ ...faqData, answer: e.target.value })
                }}
                placeholder="Enter the answer..."
                className="min-h-[120px]"
              />
            </div>

            {/* Tags Section */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Tags</Label>
              <div className="flex flex-wrap gap-2">
                {(editingFAQ?.tags || newFAQ.tags || []).map((tag, index) => (
                  <Badge key={index} variant="secondary" className="gap-1">
                    {tag}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-auto p-0 hover:bg-transparent"
                      onClick={() => handleRemoveTag(
                        tag,
                        editingFAQ || newFAQ,
                        editingFAQ ? setEditingFAQ : setNewFAQ
                      )}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="Add a tag..."
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddTag(
                        editingFAQ || newFAQ,
                        editingFAQ ? setEditingFAQ : setNewFAQ
                      )
                    }
                  }}
                />
                <Button
                  variant="outline"
                  onClick={() => handleAddTag(
                    editingFAQ || newFAQ,
                    editingFAQ ? setEditingFAQ : setNewFAQ
                  )}
                >
                  Add
                </Button>
              </div>
            </div>

            {/* Status Toggle */}
            <div className="flex items-center space-x-2">
              <Switch
                id="is-active"
                checked={editingFAQ?.isActive ?? newFAQ.isActive ?? true}
                onCheckedChange={(checked) => {
                  const faqData = editingFAQ || newFAQ
                  const setFaqData = editingFAQ ? setEditingFAQ : setNewFAQ
                  setFaqData({ ...faqData, isActive: checked })
                }}
              />
              <Label htmlFor="is-active">Active (visible to AI)</Label>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {
              setIsAddingFAQ(false)
              setEditingFAQ(null)
              setNewFAQ({
                questions: [""],
                answer: "",
                tags: [],
                isActive: true,
                source: "manual"
              })
            }}>
              Cancel
            </Button>
            <Button onClick={() => handleSaveFAQ(editingFAQ || newFAQ)}>
              <Save className="w-4 h-4 mr-2" />
              Save FAQ
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}