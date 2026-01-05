"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import {
  Plus,
  Search,
  CheckCircle,
  X,
  RefreshCw,
  List,
} from "lucide-react"
import { FAQQAService, FAQQA, FAQQACreate, ApiClient } from "@/lib/api"
import { formatRelativeDate, getStatusColor, getStatusLabel } from "@/lib/utils"

export default function FAQPage() {
  const { toast } = useToast()
  const [faqs, setFaqs] = useState<FAQQA[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [editingFAQ, setEditingFAQ] = useState<FAQQA | null>(null)
  const [isAddingFAQ, setIsAddingFAQ] = useState(false)
  const [newFAQ, setNewFAQ] = useState<Partial<FAQQA>>({
    questions: [""],
    answer: "",
    context: [],
    is_active: true
  })
  const [newTag, setNewTag] = useState("")
  const [managingQuestionsFAQ, setManagingQuestionsFAQ] = useState<FAQQA | null>(null)
  const [newQuestion, setNewQuestion] = useState("")
  const [deletingFAQ, setDeletingFAQ] = useState<FAQQA | null>(null)
  const [storageUsage, setStorageUsage] = useState<{
    usedMb: number;
    quotaMb: number;
    availableMb: number;
    percentageUsed: number;
    isFull: boolean;
  } | null>(null)

  // Charger les FAQ depuis l'API
  const loadFAQs = async () => {
    try {
      setIsLoading(true)
      const data = await FAQQAService.list()
      setFaqs(data)
    } catch (error) {
      console.error("Erreur lors du chargement des FAQ:", error)
      toast({
        title: "Erreur de chargement",
        description: "Impossible de charger les FAQ.",
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
    loadFAQs()
    loadStorageUsage()
  }, [])

  const filteredFAQs = faqs.filter(faq => {
    const matchesSearch = 
      faq.questions.some(q => q.toLowerCase().includes(searchQuery.toLowerCase())) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (faq.context || []).some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesStatus = statusFilter === "all" || 
      (statusFilter === "active" && faq.is_active) ||
      (statusFilter === "inactive" && !faq.is_active)

    return matchesSearch && matchesStatus
  })


  const handleAddQuestion = (faqData: Partial<FAQQA>, setFaqData: (data: Partial<FAQQA>) => void) => {
    setFaqData({
      ...faqData,
      questions: [...(faqData.questions || []), ""]
    })
  }

  const handleRemoveQuestion = (index: number, faqData: Partial<FAQQA>, setFaqData: (data: Partial<FAQQA>) => void) => {
    const newQuestions = faqData.questions?.filter((_, i) => i !== index) || []
    setFaqData({
      ...faqData,
      questions: newQuestions.length > 0 ? newQuestions : [""]
    })
  }

  const handleQuestionChange = (index: number, value: string, faqData: Partial<FAQQA>, setFaqData: (data: Partial<FAQQA>) => void) => {
    const newQuestions = [...(faqData.questions || [])]
    newQuestions[index] = value
    setFaqData({
      ...faqData,
      questions: newQuestions
    })
  }

  const handleAddTag = (faqData: Partial<FAQQA>, setFaqData: (data: Partial<FAQQA>) => void) => {
    if (newTag.trim() && !(faqData.context || []).includes(newTag.trim())) {
      setFaqData({
        ...faqData,
        context: [...(faqData.context || []), newTag.trim()]
      })
      setNewTag("")
    }
  }

  const handleRemoveTag = (tagToRemove: string, faqData: Partial<FAQQA>, setFaqData: (data: Partial<FAQQA>) => void) => {
    setFaqData({
      ...faqData,
      context: (faqData.context || []).filter(tag => tag !== tagToRemove)
    })
  }

  const handleSaveFAQ = async (faqData: Partial<FAQQA>) => {
    const validQuestions = faqData.questions?.filter(q => q.trim()) || []
    if (validQuestions.length === 0 || !faqData.answer?.trim()) return

    // Vérifier le quota de stockage
    if (storageUsage) {
      // Calculer la taille de la FAQ (questions + answer)
      let textSizeBytes = 0
      for (const question of validQuestions) {
        textSizeBytes += new Blob([question]).size
      }
      textSizeBytes += new Blob([faqData.answer || ""]).size
      const textSizeMb = textSizeBytes / (1024 * 1024)

      if (textSizeMb > storageUsage.availableMb) {
        toast({
          title: "Quota de stockage insuffisant",
          description: `Espace disponible: ${storageUsage.availableMb.toFixed(2)} MB, Requis: ${textSizeMb.toFixed(2)} MB`,
          variant: "destructive",
        })
        return
      }
    }

    try {
      setIsCreating(true)

      const faqToSave: FAQQACreate = {
      questions: validQuestions,
      answer: faqData.answer,
        context: faqData.context || []
    }

    if (faqData.id) {
      // Update existing FAQ
        await FAQQAService.update(faqData.id, faqToSave)
        toast({
          title: "FAQ mise à jour",
          description: "La FAQ a été mise à jour avec succès.",
        })
    } else {
      // Add new FAQ
        await FAQQAService.create(faqToSave)
        toast({
          title: "FAQ créée",
          description: "La nouvelle FAQ a été créée avec succès.",
        })
      }

      // Recharger les FAQ et l'usage de stockage
      await loadFAQs()
      await loadStorageUsage()

    setEditingFAQ(null)
    setIsAddingFAQ(false)
    setNewFAQ({
      questions: [""],
      answer: "",
        context: [],
        is_active: true
      })
    } catch (error) {
      console.error("Erreur lors de la sauvegarde de la FAQ:", error)
      toast({
        title: "Erreur de sauvegarde",
        description: "Impossible de sauvegarder la FAQ.",
        variant: "destructive",
      })
    } finally {
      setIsCreating(false)
    }
  }

  const handleToggleFAQ = async (faqId: string) => {
    try {
      const result = await FAQQAService.toggle(faqId)
      toast({
        title: result.is_active ? "FAQ activée" : "FAQ désactivée",
        description: result.message,
      })
      await loadFAQs()
    } catch (error) {
      console.error("Erreur lors du toggle de la FAQ:", error)
      toast({
        title: "Erreur",
        description: "Impossible de changer le statut de la FAQ.",
        variant: "destructive",
      })
    }
  }

  const handleAddQuestionToFAQ = async (faqId: string, question: string) => {
    if (!question.trim()) return

    try {
      await FAQQAService.addQuestions(faqId, { items: [question.trim()] })
      toast({
        title: "Question ajoutée",
        description: "La question a été ajoutée avec succès.",
      })
      await loadFAQs()
      setNewQuestion("")
    } catch (error) {
      console.error("Erreur lors de l'ajout de la question:", error)
      toast({
        title: "Erreur",
        description: "Impossible d'ajouter la question.",
        variant: "destructive",
      })
    }
  }

  const handleUpdateQuestionInFAQ = async (faqId: string, index: number, newValue: string) => {
    if (!newValue.trim()) return

    try {
      await FAQQAService.updateQuestions(faqId, {
        updates: [{ index, value: newValue.trim() }]
      })
      toast({
        title: "Question modifiée",
        description: "La question a été modifiée avec succès.",
      })
      await loadFAQs()
    } catch (error) {
      console.error("Erreur lors de la modification de la question:", error)
      toast({
        title: "Erreur",
        description: "Impossible de modifier la question.",
        variant: "destructive",
      })
    }
  }

  const handleDeleteQuestionFromFAQ = async (faqId: string, index: number) => {
    try {
      await FAQQAService.deleteQuestions(faqId, { indexes: [index] })
      toast({
        title: "Question supprimée",
        description: "La question a été supprimée avec succès.",
      })
      await loadFAQs()
    } catch (error) {
      console.error("Erreur lors de la suppression de la question:", error)
      toast({
        title: "Erreur",
        description: "Impossible de supprimer la question.",
        variant: "destructive",
      })
    }
  }

  const handleDeleteFAQ = async (faqId: string) => {
    try {
      await FAQQAService.remove(faqId)
      toast({
        title: "FAQ supprimée",
        description: "La FAQ a été supprimée avec succès.",
      })
      await loadFAQs()
    } catch (error) {
      console.error("Erreur lors de la suppression de la FAQ:", error)
      toast({
        title: "Erreur de suppression",
        description: "Impossible de supprimer la FAQ.",
        variant: "destructive",
      })
    }
  }

  const handleEditFAQ = (faq: FAQQA) => {
    setEditingFAQ({ ...faq })
  }

  const totalFAQs = faqs.length
  const activeFAQs = faqs.filter(f => f.is_active).length
  const inactiveFAQs = faqs.filter(f => !f.is_active).length
  const totalQuestions = faqs.reduce((sum, faq) => sum + faq.questions.length, 0)

  return (
    <div className="flex-1 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Gestion des FAQ</h1>
          <p className="text-muted-foreground">
            Gérez les questions fréquemment posées et leurs réponses pour votre chatbot IA
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setIsAddingFAQ(true)} className="cursor-pointer">
            <Plus className="w-4 h-4 mr-2" />
            Ajouter une FAQ
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total FAQ</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFAQs}</div>
            <p className="text-xs text-muted-foreground">
              Entrées FAQ
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Actives</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-400">{activeFAQs}</div>
            <p className="text-xs text-muted-foreground">
              FAQ publiées
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Inactives</CardTitle>
            <X className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-400">{inactiveFAQs}</div>
            <p className="text-xs text-muted-foreground">
              FAQ brouillon
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Questions</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalQuestions}</div>
            <p className="text-xs text-muted-foreground">
              Questions totales
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stockage</CardTitle>
            <Plus className="h-4 w-4 text-muted-foreground" />
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
              <div className="text-sm text-muted-foreground">Chargement...</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher dans les FAQ, réponses, tags..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            <SelectItem value="active">Actives</SelectItem>
            <SelectItem value="inactive">Inactives</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* FAQ List */}
      <div className="space-y-4">
        {isLoading ? (
          <Card>
            <CardContent className="text-center py-12">
              <RefreshCw className="w-12 h-12 mx-auto mb-4 text-muted-foreground animate-spin" />
              <h3 className="text-lg font-semibold mb-2">Chargement des FAQ...</h3>
              <p className="text-muted-foreground">
                Veuillez patienter pendant le chargement des données.
              </p>
            </CardContent>
          </Card>
        ) : filteredFAQs.length === 0 ? (
          <Card>
            <CardContent className="text-center py-12">
              <Plus className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">Aucune FAQ trouvée</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery ? "Essayez d'ajuster vos termes de recherche" : "Créez votre première FAQ pour commencer"}
              </p>
              {!searchQuery && (
                <Button onClick={() => setIsAddingFAQ(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter une FAQ
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
                      {faq.is_active ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <X className="w-4 h-4 text-gray-400" />
                      )}
                      <Badge variant="outline" className={getStatusColor(faq.is_active ? 'active' : 'inactive')}>
                        {getStatusLabel(faq.is_active ? 'active' : 'inactive')}
                      </Badge>
                      {(faq.context || []).map((tag, index) => (
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
                        Réponse
                      </Label>
                      <p className="text-sm text-muted-foreground">{faq.answer}</p>
                    </div>

                    <div className="text-xs text-muted-foreground">
                      Modifié {formatRelativeDate(faq.updated_at)}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <div className="flex items-center gap-2">
                      <Label htmlFor={`toggle-${faq.id}`} className="text-sm">
                        {faq.is_active ? "Activé" : "Désactivé"}
                      </Label>
                      <Switch
                        id={`toggle-${faq.id}`}
                        checked={faq.is_active}
                        onCheckedChange={() => handleToggleFAQ(faq.id)}
                      />
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setManagingQuestionsFAQ(faq)}
                      title="Gérer les questions"
                      className="cursor-pointer"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditFAQ(faq)}
                      className="cursor-pointer"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="cursor-pointer text-red-600 hover:text-red-700 hover:bg-red-50"
                          title="Supprimer la FAQ"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Confirmer la suppression</AlertDialogTitle>
                          <AlertDialogDescription>
                            Êtes-vous sûr de vouloir supprimer cette FAQ ? Cette action est irréversible.
                            <br />
                            <strong>FAQ : "{faq.questions[0]}"</strong>
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Annuler</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => handleDeleteFAQ(faq.id)}
                            className="bg-red-600 hover:bg-red-700"
                          >
                            Supprimer
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
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
          context: [],
          is_active: true
        })
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingFAQ ? "Modifier la FAQ" : "Ajouter une nouvelle FAQ"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Questions Section */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">
                Questions (Plusieurs formulations pour la même réponse)
              </Label>
              {((editingFAQ?.questions || newFAQ.questions) || [""]).map((question, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground w-6">{index + 1}.</span>
                  <Input
                    value={question}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      const faqData = editingFAQ || newFAQ
                      const value = e.target.value
                      const newQuestions = [...(faqData.questions || [])]
                      newQuestions[index] = value
                      if (editingFAQ) {
                        setEditingFAQ({ ...editingFAQ, questions: newQuestions })
                      } else {
                        setNewFAQ({ ...newFAQ, questions: newQuestions })
                      }
                    }}
                    placeholder="Entrez une question..."
                    className="flex-1"
                  />
                  {(((editingFAQ?.questions || newFAQ.questions) || []).length > 1) && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const faqData = editingFAQ || newFAQ
                        const newQuestions = faqData.questions?.filter((_, i) => i !== index) || []
                        if (editingFAQ) {
                          setEditingFAQ({ ...editingFAQ, questions: newQuestions.length > 0 ? newQuestions : [""] })
                        } else {
                          setNewFAQ({ ...newFAQ, questions: newQuestions.length > 0 ? newQuestions : [""] })
                        }
                      }}
                      className="cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              ))}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  const faqData = editingFAQ || newFAQ
                  if (editingFAQ) {
                    setEditingFAQ({ ...editingFAQ, questions: [...(editingFAQ.questions || []), ""] })
                  } else {
                    setNewFAQ({ ...newFAQ, questions: [...(newFAQ.questions || []), ""] })
                  }
                }}
                className="cursor-pointer"
              >
                <Plus className="w-4 h-4 mr-2" />
                Ajouter une question
              </Button>
            </div>

            {/* Answer Section */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Réponse</Label>
              <Textarea
                value={editingFAQ?.answer || newFAQ.answer || ""}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                  const faqData = editingFAQ || newFAQ
                  if (editingFAQ) {
                    setEditingFAQ({ ...editingFAQ, answer: e.target.value })
                  } else {
                    setNewFAQ({ ...newFAQ, answer: e.target.value })
                  }
                }}
                placeholder="Entrez la réponse..."
                className="min-h-[120px]"
              />
            </div>

            {/* Tags Section */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Tags</Label>
              <div className="flex flex-wrap gap-2">
                {((editingFAQ?.context || newFAQ.context) || []).map((tag, index) => (
                  <Badge key={index} variant="secondary" className="gap-1">
                    {tag}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-auto p-0 hover:bg-transparent cursor-pointer"
                      onClick={() => {
                        const faqData = editingFAQ || newFAQ
                        if (editingFAQ) {
                          setEditingFAQ({ ...editingFAQ, context: (editingFAQ.context || []).filter(t => t !== tag) })
                        } else {
                          setNewFAQ({ ...newFAQ, context: (newFAQ.context || []).filter(t => t !== tag) })
                        }
                      }}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  value={newTag}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewTag(e.target.value)}
                  placeholder="Ajouter un tag..."
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      if (newTag.trim()) {
                        const faqData = editingFAQ || newFAQ
                        if (!(faqData.context || []).includes(newTag.trim())) {
                          if (editingFAQ) {
                            setEditingFAQ({ ...editingFAQ, context: [...(editingFAQ.context || []), newTag.trim()] })
                          } else {
                            setNewFAQ({ ...newFAQ, context: [...(newFAQ.context || []), newTag.trim()] })
                          }
                          setNewTag("")
                        }
                      }
                    }
                  }}
                />
                <Button
                  variant="outline"
                  onClick={() => {
                    if (newTag.trim()) {
                      const faqData = editingFAQ || newFAQ
                      if (!(faqData.context || []).includes(newTag.trim())) {
                        if (editingFAQ) {
                          setEditingFAQ({ ...editingFAQ, context: [...(editingFAQ.context || []), newTag.trim()] })
                        } else {
                          setNewFAQ({ ...newFAQ, context: [...(newFAQ.context || []), newTag.trim()] })
                        }
                        setNewTag("")
                      }
                    }
                  }}
                  className="cursor-pointer"
                >
                  Ajouter
                </Button>
              </div>
            </div>

            {/* Status Toggle */}
            <div className="flex items-center space-x-2">
              <Switch
                id="is-active"
                checked={editingFAQ?.is_active ?? newFAQ.is_active ?? true}
                onCheckedChange={(checked: boolean) => {
                  if (editingFAQ) {
                    setEditingFAQ({ ...editingFAQ, is_active: checked })
                  } else {
                    setNewFAQ({ ...newFAQ, is_active: checked })
                  }
                }}
              />
              <Label htmlFor="is-active">Active (visible à l'IA)</Label>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {
              setIsAddingFAQ(false)
              setEditingFAQ(null)
              setNewFAQ({
                questions: [""],
                answer: "",
                context: [],
                is_active: true
              })
            }}>
              Annuler
            </Button>
            <Button onClick={() => handleSaveFAQ(editingFAQ || newFAQ)} disabled={isCreating}>
              {isCreating ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
              <Plus className="w-4 h-4 mr-2" />
              )}
              {editingFAQ ? "Mettre à jour" : "Sauvegarder"} FAQ
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Manage Questions Dialog */}
      <Dialog open={!!managingQuestionsFAQ} onOpenChange={() => {
        setManagingQuestionsFAQ(null)
        setNewQuestion("")
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Gérer les questions - {managingQuestionsFAQ?.title || "FAQ"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            {/* Current Questions */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">
                Questions actuelles ({managingQuestionsFAQ?.questions?.length || 0})
              </Label>
              <div className="space-y-2">
                {managingQuestionsFAQ?.questions?.map((question, index) => (
                  <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
                    <span className="text-sm text-muted-foreground w-6 font-medium">
                      {index + 1}.
                    </span>
                    <Input
                      value={question}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                        const updatedFAQ = { ...managingQuestionsFAQ }
                        updatedFAQ.questions = [...(updatedFAQ.questions || [])]
                        updatedFAQ.questions[index] = e.target.value
                        setManagingQuestionsFAQ(updatedFAQ)
                      }}
                      className="flex-1"
                      placeholder="Question..."
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleUpdateQuestionInFAQ(managingQuestionsFAQ.id, index, question)}
                      title="Sauvegarder les modifications"
                      className="cursor-pointer"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteQuestionFromFAQ(managingQuestionsFAQ.id, index)}
                      title="Supprimer cette question"
                      className="cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>

            {/* Add New Question */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Ajouter une nouvelle question</Label>
              <div className="flex gap-2">
                <Input
                  value={newQuestion}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewQuestion(e.target.value)}
                  placeholder="Entrez une nouvelle question..."
                  onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => {
                    if (e.key === 'Enter' && newQuestion.trim()) {
                      e.preventDefault()
                      handleAddQuestionToFAQ(managingQuestionsFAQ!.id, newQuestion)
                    }
                  }}
                />
                <Button
                  onClick={() => handleAddQuestionToFAQ(managingQuestionsFAQ!.id, newQuestion)}
                  disabled={!newQuestion.trim()}
                  className="cursor-pointer"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter
                </Button>
              </div>
            </div>

            {/* Answer Preview */}
            {managingQuestionsFAQ?.answer && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">Réponse</Label>
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm">{managingQuestionsFAQ.answer}</p>
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => {
              setManagingQuestionsFAQ(null)
              setNewQuestion("")
            }}>
              Fermer
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}