"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
import {
  Plus,
  Edit,
  Trash2,
  MessageSquare,
  Tag,
  Globe,
  Calendar,
  ToggleLeft,
  ToggleRight,
} from "lucide-react"
import { useAuth } from "@/hooks/useAuth"
import { useToast } from "@/hooks/use-toast"
import { ApiClient, FAQQAService, FAQQA } from "@/lib/api"

export function QAExamplesTab() {
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [selectedExample, setSelectedExample] = useState<Partial<FAQQA> | null>(null)
  const [examples, setExamples] = useState<FAQQA[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const { user } = useAuth()
  const { toast } = useToast()

  // Format date without UTC
  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'Non définie'
    
    try {
      const date = new Date(dateString)
      // Format: DD/MM/YYYY HH:mm
      return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Europe/Paris' // Timezone française
      })
    } catch (error) {
      return 'Date invalide'
    }
  }

  // Load FAQ examples from API
  const loadExamples = async () => {
    try {
      setIsLoading(true)
      const faqs = await FAQQAService.list()
      setExamples(faqs)
    } catch (error) {
      console.error('Error loading FAQ examples:', error)
      toast({
        title: "Error",
        description: "Failed to load FAQ examples",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      loadExamples()
    }
  }, [user])

  const openEditor = (example?: any) => {
    setSelectedExample(
      example || {
        title: "",
        language: "",
        question: "",
        answer: "",
        context: "",
      },
    )
    setIsEditorOpen(true)
  }

  // Save FAQ example
  const saveExample = async (formData: any) => {
    try {
      setIsLoading(true)

      // Validation
      if (!formData.title?.trim()) {
        throw new Error("Title is required")
      }
      if (!formData.language) {
        throw new Error("Language is required")
      }
      if (!formData.question?.trim()) {
        throw new Error("Question is required")
      }
      if (!formData.answer?.trim()) {
        throw new Error("Answer is required")
      }

      // Prepare data
      const faqData = {
        title: formData.title?.trim(),
        language: formData.language,
        question: formData.question.trim(),
        answer: formData.answer.trim(),
        metadata: formData.context ? { context: formData.context.split(',').map((tag: string) => tag.trim()).filter(Boolean) } : {}
      }

      if (formData.id) {
        // Update existing FAQ
        await FAQQAService.update(formData.id, faqData)
        toast({
          title: "Success",
          description: "FAQ example updated successfully",
        })
      } else {
        // Create new FAQ
        await FAQQAService.create(faqData)
        toast({
          title: "Success",
          description: "FAQ example created successfully",
        })
      }

      // Reload examples
      await loadExamples()
      setIsEditorOpen(false)

    } catch (error: any) {
      console.error('Error saving FAQ:', error)
      toast({
        title: "Error",
        description: error.message || "Failed to save FAQ example",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Handle form submission
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    const formData = new FormData(e.currentTarget)
    const data = {
      id: selectedExample?.id,
      title: formData.get('title') as string,
      language: formData.get('language') as string,
      question: formData.get('question') as string,
      answer: formData.get('answer') as string,
      context: formData.get('context') as string,
    }

    saveExample(data)
  }

  // Handle toggle FAQ active/inactive (soft delete)
  const handleToggle = async (faqId: string) => {
    try {
      setIsLoading(true)
      const result = await FAQQAService.toggle(faqId)
      
      toast({
        title: "Success",
        description: result.message,
        variant: "default",
      })
      
      // Recharger la liste des FAQ
      await loadExamples()
    } catch (error: any) {
      console.error('Error toggling FAQ:', error)
      toast({
        title: "Error",
        description: error.message || "Failed to toggle FAQ",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Handle delete FAQ (hard delete)
  const handleDelete = async (faqId: string, title: string) => {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer définitivement "${title}" ?`)) {
      return
    }

    try {
      setIsLoading(true)
      await FAQQAService.remove(faqId)
      
      toast({
        title: "Success",
        description: "FAQ supprimée définitivement avec succès",
        variant: "default",
      })
      
      // Recharger la liste des FAQ
      await loadExamples()
    } catch (error: any) {
      console.error('Error deleting FAQ:', error)
      toast({
        title: "Error",
        description: error.message || "Failed to delete FAQ",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <TooltipProvider>
      <div className="p-4 lg:p-6 space-y-6">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg lg:text-xl font-semibold">Q&A Examples</h2>
          <Badge variant="secondary" className="text-xs">
            {examples.length} examples
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => openEditor()} className="gradient-primary text-white border-0">
            <Plus className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">New Example</span>
            <span className="sm:hidden">New</span>
          </Button>
        </div>
      </div>

      {/* Examples Table */}
      <Card className="shadow-soft">
        <CardContent className="p-0">
          {examples.length > 0 ? (
            <div className="divide-y">
              {examples.map((example) => (
                <div key={example.id} className="p-4 hover:bg-muted/50 transition-colors">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-3 mb-2">
                        <h3 className="font-medium truncate">{example.title || 'Untitled'}</h3>
                        <Badge variant="outline" className="text-xs flex-shrink-0">
                          <Globe className="w-3 h-3 mr-1" />
                          {example.lang_code || example.language || 'FR'}
                        </Badge>
                        <div className="flex items-center">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                className="p-1 h-auto cursor-pointer hover:bg-muted/50"
                                onClick={() => handleToggle(example.id)}
                                disabled={isLoading}
                              >
                                {example.active || example.is_active ? (
                                  <ToggleRight className="w-4 h-4 text-green-500" />
                                ) : (
                                  <ToggleLeft className="w-4 h-4 text-muted-foreground" />
                                )}
                                <span className="sr-only">Toggle active/inactive</span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>{example.active || example.is_active ? 'Désactiver' : 'Activer'}</p>
                            </TooltipContent>
                          </Tooltip>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(example.updated_at || example.created_at)}
                        </div>
                        {example.context && Array.isArray(example.context) && example.context.length > 0 && (
                          <div className="flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            <div className="flex flex-wrap gap-1">
                              {example.context.map((tag: string, index: number) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {tag}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => openEditor(example)}
                      >
                        <Edit className="w-4 h-4" />
                        <span className="sr-only">Edit</span>
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => handleDelete(example.id, example.title || 'Untitled')}
                        disabled={isLoading}
                      >
                        <Trash2 className="w-4 h-4" />
                        <span className="sr-only">Delete</span>
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No examples yet</h3>
              <p className="text-muted-foreground mb-4 text-sm lg:text-base">
                Add 3 examples to guide your AI and improve response quality
              </p>
              <Button onClick={() => openEditor()} className="gradient-primary text-white border-0">
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Example
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Editor Modal */}
      <Dialog open={isEditorOpen} onOpenChange={setIsEditorOpen}>
        <DialogContent className="max-w-[95vw] lg:max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedExample?.id ? "Edit Example" : "New Example"}</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Input */}
            <div className="space-y-4">
              <div>
                <Label>Title *</Label>
                <Input
                  name="title"
                  placeholder="Example title..."
                  defaultValue={selectedExample?.title}
                  className="mt-2"
                  required
                />
              </div>

              <div>
                <Label>Language *</Label>
                <Select name="language" defaultValue={selectedExample?.language || ""}>
                  <SelectTrigger className="mt-2">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="en">English</SelectItem>
                    <SelectItem value="fr">French</SelectItem>
                    <SelectItem value="es">Spanish</SelectItem>
                    <SelectItem value="de">German</SelectItem>
                    <SelectItem value="it">Italian</SelectItem>
                    <SelectItem value="pt">Portuguese</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Question *</Label>
                <Textarea
                  name="question"
                  placeholder="Enter the user's question..."
                  defaultValue={selectedExample?.question}
                  className="mt-2 min-h-[100px] text-sm"
                  required
                />
              </div>

              <div>
                <Label>Context Tags (Optional)</Label>
                <Input
                  name="context"
                  placeholder="refund, shipping, product_info (comma separated)"
                  defaultValue={Array.isArray(selectedExample?.context) ? selectedExample.context.join(", ") : selectedExample?.context || ""}
                  className="mt-2"
                />
              </div>
            </div>

            {/* Right Column - Output */}
            <div className="space-y-4">
              <div>
                <Label>Answer *</Label>
                <Textarea
                  name="answer"
                  placeholder="Enter the expected AI response..."
                  defaultValue={selectedExample?.answer}
                  className="mt-2 min-h-[150px] text-sm"
                  required
                />
              </div>

              <div className="bg-muted/30 p-4 rounded-lg">
                <h4 className="text-sm font-medium mb-2">Preview</h4>
                <div className="text-xs text-muted-foreground space-y-1">
                  <div><strong>Title:</strong> {selectedExample?.title || "Not set"}</div>
                  <div><strong>Language:</strong> {selectedExample?.language || "Not set"}</div>
                  <div><strong>Question:</strong> {selectedExample?.question?.substring(0, 50) || "Not set"}{selectedExample?.question && selectedExample.question.length > 50 ? "..." : ""}</div>
                  <div><strong>Answer:</strong> {selectedExample?.answer?.substring(0, 50) || "Not set"}{selectedExample?.answer && selectedExample.answer.length > 50 ? "..." : ""}</div>
                  {selectedExample?.context && Array.isArray(selectedExample.context) && selectedExample.context.length > 0 && (
                    <div><strong>Context:</strong> {selectedExample.context.join(", ")}</div>
                  )}
                </div>
              </div>
            </div>
          </div>

            <div className="flex flex-col sm:flex-row justify-end gap-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsEditorOpen(false)}
                className="w-full sm:w-auto"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="gradient-primary text-white border-0 w-full sm:w-auto"
              >
                {isLoading ? "Saving..." : (selectedExample?.id ? "Update Example" : "Create Example")}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
      </div>
    </TooltipProvider>
  )
}
