# Migration Sources Pages - Documentation des Modifications

## Vue d'Ensemble
Migration complète des pages Sources (Data et FAQ) vers le nouveau design Social-Sync-AI, avec simplification de l'interface Data selon les spécifications et amélioration majeure de la page FAQ avec support multi-questions par réponse.

## Fichiers Modifiés/Créés

### Pages Data
- **Page principale**: `/app/sources/data/page.tsx`
- **Loading state**: `/app/sources/data/loading.tsx`

### Pages FAQ
- **Page principale**: `/app/sources/faq/page.tsx`
- **Loading state**: `/app/sources/faq/loading.tsx`

## Sources/Data - Simplification ✨

### Fonctionnalités Conservées
- ✅ **Upload de fichiers**: Interface drag-and-drop avec support multi-fichiers
- ✅ **Gestion des fichiers**: Liste des fichiers uploadés avec métadonnées
- ✅ **Statuts d'indexation**: Indexed, Processing, Error avec indicateurs visuels
- ✅ **Recherche**: Filtrage par nom de fichier et type
- ✅ **Actions sur fichiers**: Settings, Delete, Retry pour les erreurs

### Fonctionnalités Supprimées (selon spécifications)
- ❌ **Sources connectées**: Suppression des intégrations complexes (Supabase, Google Drive, S3)
- ❌ **Synchronisation**: Pas de sync automatique avec sources externes
- ❌ **Import/Export avancé**: Fonctionnalités d'import/export complexes supprimées

### Nouvelles Fonctionnalités
- ✨ **Interface simplifiée**: Focus sur l'upload et la gestion de fichiers locaux
- ✨ **Stats dashboard**: 4 KPI cards (Total Files, Indexed, Processing, Knowledge Chunks)
- ✨ **États de chargement**: Animation d'upload avec feedback utilisateur
- ✨ **Gestion d'erreur améliorée**: Bouton retry pour les fichiers en erreur

### Architecture Technique Data
```typescript
interface FileData {
  id: string
  name: string
  size: string
  type: string
  uploadDate: string
  status: "indexed" | "processing" | "error"
  chunks: number
  lastProcessed: string | null
  error?: string
}
```

### Fonctionnalités d'Upload
```typescript
const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
  // Support multi-fichiers
  // Formats: .pdf, .doc, .docx, .txt, .csv, .md
  // Upload avec simulation de processing
  // Mise à jour des stats en temps réel
}
```

## Sources/FAQ - Amélioration Majeure ✨

### Nouvelle Fonctionnalité Clé: Multi-Questions par Réponse
- ✨ **Questions multiples**: Une réponse peut avoir plusieurs formulations de questions
- ✨ **Gestion dynamique**: Ajout/suppression de questions dans l'interface
- ✨ **Interface intuitive**: Numérotation automatique et gestion des questions vides

### Fonctionnalités Conservées
- ✅ **CRUD FAQ**: Create, Read, Update, Delete des FAQ
- ✅ **Système de recherche**: Recherche dans questions, réponses et tags
- ✅ **Filtres par statut**: Active/Inactive
- ✅ **Système de tags**: Catégorisation des FAQ

### Fonctionnalités Supprimées (selon spécifications)
- ❌ **Support multilingue**: Suppression de la gestion des langues
- ❌ **Import/Export CSV**: Fonctionnalités d'import/export supprimées

### Nouvelles Fonctionnalités FAQ
- ✨ **Interface de questions multiples**:
  ```typescript
  interface FAQ {
    id: string
    questions: string[]  // ← NOUVEAU: Array de questions
    answer: string
    tags: string[]
    isActive: boolean
    updatedAt: string
    source: "manual" | "chat_edit" | "import"
  }
  ```

- ✨ **Gestion dynamique des questions**:
  - Ajout de nouvelles questions avec bouton "+"
  - Suppression de questions (minimum 1 requise)
  - Numérotation automatique
  - Validation des questions vides

- ✨ **Source tracking**: Indication de l'origine des FAQ (manual, chat_edit, import)
- ✨ **Stats dashboard**: 4 KPI cards (Total FAQs, Active, Inactive, Total Questions)

### Interface de Gestion Multi-Questions
```typescript
// Ajout de question
const handleAddQuestion = (faqData, setFaqData) => {
  setFaqData({
    ...faqData,
    questions: [...(faqData.questions || []), ""]
  })
}

// Suppression de question (garde minimum 1)
const handleRemoveQuestion = (index, faqData, setFaqData) => {
  const newQuestions = faqData.questions?.filter((_, i) => i !== index) || []
  setFaqData({
    ...faqData,
    questions: newQuestions.length > 0 ? newQuestions : [""]
  })
}
```

### Modal d'Édition Avancée
- ✨ **Section Questions**: Liste dynamique avec ajout/suppression
- ✨ **Section Réponse**: Textarea expandable
- ✨ **Section Tags**: Gestion des tags avec ajout/suppression visuelle
- ✨ **Toggle Actif**: Contrôle de la visibilité pour l'IA
- ✨ **Validation**: Vérification des questions non-vides et réponse requise

## Design et UX

### Layout Uniforme
- **Header cohérent**: Titre, description, boutons d'action
- **Stats cards**: 4 KPI en grid responsive
- **Search/Filters**: Barre de recherche et filtres horizontaux
- **Content area**: Cards avec contenu organisé

### Indicateurs Visuels
- **Status badges**: Couleurs distinctives par statut
- **Source badges**: Identification de l'origine des données
- **Icons contextuelles**: CheckCircle, Clock, AlertCircle selon l'état
- **Progress feedback**: États de chargement et d'upload

### Interactions
- **Hover states**: Effets sur les cards et boutons
- **Modal responsive**: Dialogs adaptatifs pour édition
- **Drag & drop**: Interface d'upload intuitive (Data)
- **Dynamic forms**: Ajout/suppression d'éléments en temps réel (FAQ)

## États de Chargement

### Loading States Complets
- **Header skeletons**: Titre et boutons
- **Stats skeletons**: Placeholders pour les KPI
- **Content skeletons**: Cards avec structure préservée
- **Form skeletons**: Éléments de formulaire dans les modals

### Upload Progress (Data)
```typescript
{isUploading && (
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className="animate-spin">
          <RefreshCw className="w-5 h-5" />
        </div>
        <div>
          <p className="font-medium">Uploading files...</p>
          <p className="text-sm text-muted-foreground">
            Please wait while we process your files
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
)}
```

## Intégration Future avec l'API

### Endpoints Data
```typescript
// File management
POST /api/files/upload          // Multi-file upload
GET /api/files                  // List files with filters
DELETE /api/files/:id           // Delete file
POST /api/files/:id/reprocess   // Retry processing
GET /api/files/stats            // Get statistics
```

### Endpoints FAQ
```typescript
// FAQ management with multi-questions support
GET /api/faq                    // List FAQs
POST /api/faq                   // Create FAQ with questions array
PUT /api/faq/:id                // Update FAQ
DELETE /api/faq/:id             // Delete FAQ
GET /api/faq/stats              // Get statistics
POST /api/faq/search            // Advanced search
```

### Data Models
```typescript
// Enhanced FAQ model
interface FAQ {
  id: string
  questions: string[]           // Multiple questions per answer
  answer: string
  tags: string[]
  isActive: boolean
  source: "manual" | "chat_edit" | "import"
  createdAt: string
  updatedAt: string
  createdBy?: string
}

// File model
interface FileData {
  id: string
  name: string
  originalName: string
  size: number
  mimeType: string
  uploadDate: string
  status: "indexed" | "processing" | "error"
  chunks: number
  lastProcessed: string | null
  error?: string
  metadata?: Record<string, any>
}
```

## Améliorations UX Spécifiques

### Page Data
- **Upload intuitif**: Zone de drop claire avec feedback visuel
- **Gestion d'erreur**: Messages d'erreur contextuels avec actions de récupération
- **États de processing**: Indicateurs de progression pour l'indexation
- **Stats temps réel**: Mise à jour automatique des métriques

### Page FAQ
- **Gestion multi-questions**: Interface fluide pour ajouter/supprimer des questions
- **Validation intelligente**: Empêche la suppression de la dernière question
- **Tags visuels**: Interface drag-and-drop pour la gestion des tags
- **Aperçu complet**: Affichage de toutes les questions dans la liste

## Performance et Optimisation

### Optimisations Data
- **Upload progressif**: Traitement des fichiers par batch
- **Preview génération**: Aperçus des fichiers pour navigation rapide
- **Cache intelligent**: Mise en cache des métadonnées de fichiers
- **Lazy loading**: Chargement à la demande des gros fichiers

### Optimisations FAQ
- **Search debounced**: Recherche optimisée avec délai
- **Form validation**: Validation temps réel sans soumission
- **State management**: Gestion efficace des états de formulaire
- **Memoization**: Cache des calculs de filtrage

## Tests Recommandés

### Page Data
- [ ] Upload de fichiers multiples
- [ ] Gestion des formats supportés/non-supportés
- [ ] États de processing et d'erreur
- [ ] Recherche et filtrage
- [ ] Actions sur fichiers (delete, retry)
- [ ] Stats et métriques

### Page FAQ
- [ ] Création FAQ avec questions multiples
- [ ] Ajout/suppression dynamique de questions
- [ ] Validation des formulaires
- [ ] Gestion des tags
- [ ] Recherche dans questions et réponses
- [ ] Toggle actif/inactif
- [ ] Édition et suppression

Cette migration modernise complètement les pages Sources tout en ajoutant des fonctionnalités avancées, particulièrement le support multi-questions pour les FAQ qui constitue une amélioration majeure de l'expérience utilisateur.