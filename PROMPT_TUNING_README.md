# 🤖 AI Prompt Tuning System - SocialSync

## Overview

The AI prompt tuning system allows users to fully customize their AI assistant with:

- **AI Model Selection** : Claude 3.5 Haiku, GPT-4o, GPT-4o Mini, Gemini 2.5 Flash, Grok 2
- **Industry Templates** : Social Media, E-commerce, Customer Support
- **Essential Settings** : Tone, Language (simplified UX)
- **Real-time Testing** : Validate settings before saving
- **Smart Saving** : Unsaved changes automatically detected

## 🏗️ Architecture

### Backend (`backend/`)

#### Migration de base de données
```sql
-- backend/migrations/migration_005_ai_settings.sql
CREATE TABLE ai_settings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  system_prompt TEXT NOT NULL,
  ai_model TEXT DEFAULT 'claude-3.5-haiku',
  temperature NUMERIC(3,2) DEFAULT 0.20,
  top_p NUMERIC(3,2) DEFAULT 1.00,
  lang TEXT DEFAULT 'fr',
  tone TEXT DEFAULT 'friendly',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id)
);
```

#### Schémas Pydantic
```python
# backend/app/schemas/ai_settings.py
class AISettings(AISettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
```

#### Routes API
```python
# backend/app/routers/ai_settings.py
@router.get("/", response_model=AISettings)
@router.put("/", response_model=AISettings)  
@router.post("/test", response_model=AITestResponse)
@router.get("/templates")
@router.post("/reset")
```

### Frontend (`frontend/`)

#### Hook personnalisé
```typescript
// frontend/hooks/use-ai-settings.ts
export function useAISettings() {
  return {
    settings,
    isLoading,
    error,
    fetchSettings,
    updateSettings,
    testAIResponse,
    getPromptTemplates,
    resetToTemplate,
  }
}
```

#### Composant principal
```typescript
// frontend/components/prompt-tuning-tab.tsx
export function PromptTuningTab() {
  // Gestion des états de travail vs sauvegardés
  // Interface utilisateur riche et responsive
  // Intégration avec les APIs backend
}
```

## 🚀 Fonctionnalités

### 1. Sélection de modèles IA
- **Claude 3.5 Haiku** : Rapide et efficace
- **GPT-4o** : Puissant et polyvalent
- **GPT-4o Mini** : Version optimisée
- **Grok 2** : Approche innovante

### 2. Templates de prompts
- **Réseaux sociaux** : Création de contenu viral
- **E-commerce** : Optimisation des conversions
- **Support client** : Résolution empathique

### 3. Paramètres avancés
- **Température** : Contrôle de la créativité (0.0 - 2.0)
- **Top-P** : Diversité des réponses (0.0 - 1.0)
- **Ton** : Amical, Professionnel, Décontracté, Neutre
- **Langue** : Français, Anglais, Espagnol, Auto

### 4. Test en temps réel
- Validation des paramètres avant sauvegarde
- Métriques de performance (temps de réponse, confiance)
- Aperçu du modèle sélectionné

### 5. Gestion des modifications
- Détection automatique des changements non sauvegardés
- Bouton d'annulation pour revenir aux paramètres sauvegardés
- Confirmation visuelle des sauvegardes

## 🎨 Interface utilisateur

### Layout responsive
- **Desktop** : Layout à 2 colonnes (configuration + test)
- **Tablet/Mobile** : Layout empilé avec sticky panel de test

### Composants UI
- Cards avec shadow-soft pour la cohérence
- Sélection de modèles avec icônes distinctives
- Sliders pour les paramètres numériques
- Variables de prompt cliquables
- Alertes contextuelles pour les modifications

### Feedback utilisateur
- Toasts pour les confirmations/erreurs
- États de chargement sur tous les boutons
- Indicateurs visuels pour les paramètres modifiés
- Métriques de test en temps réel

## 🔧 Installation et utilisation

### 1. Backend
```bash
# Appliquer la migration
psql -d socialsync -f backend/migrations/migration_005_ai_settings.sql

# Les routes sont automatiquement incluses via routers.py
```

### 2. Frontend
```bash
# Les composants sont déjà intégrés
# Le hook use-ai-settings gère les appels API
# L'interface est accessible via l'onglet "Prompt Tuning"
```

### 3. Configuration
```typescript
// frontend/hooks/use-ai-settings.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

## 🔄 Flux de données

1. **Chargement initial** : `useAISettings()` récupère les paramètres existants
2. **Modifications** : L'utilisateur modifie les paramètres (état `workingSettings`)
3. **Détection des changements** : `hasUnsavedChanges` devient `true`
4. **Test optionnel** : L'utilisateur peut tester les nouveaux paramètres
5. **Sauvegarde** : Clic sur "Sauvegarder" → API PUT → Mise à jour de l'état
6. **Confirmation** : Toast de succès + reset du flag `hasUnsavedChanges`

## 🛡️ Sécurité

- **RLS (Row Level Security)** : Chaque utilisateur ne peut voir que ses paramètres
- **Validation Pydantic** : Validation stricte des types et contraintes
- **Authentification** : Middleware `get_current_user_id` sur toutes les routes
- **Sanitisation** : Validation des entrées côté client et serveur

## 🎯 Points d'extension

### Futurs développements possibles
1. **Historique des versions** : Sauvegarder les versions précédentes des prompts
2. **Partage de templates** : Permettre le partage entre utilisateurs
3. **Analytics** : Métriques d'utilisation des différents modèles
4. **A/B Testing** : Test automatique de plusieurs configurations
5. **Import/Export** : Sauvegarde et restauration des configurations

### Intégrations possibles
1. **Monitoring** : Logs des performances par modèle
2. **Coûts** : Tracking des coûts par modèle et utilisateur
3. **Feedback** : Système de notation des réponses IA
4. **Automation** : Ajustement automatique basé sur les performances

## 📝 Notes techniques

- **État local vs distant** : Séparation claire entre `workingSettings` et `currentSettings`
- **Gestion d'erreur** : Centralisation dans le hook `use-ai-settings`
- **Performance** : Debounce sur les modifications pour éviter les re-renders
- **Accessibilité** : Labels appropriés, navigation au clavier
- **Responsive** : Adaptation mobile avec breakpoints Tailwind

## 🐛 Débogage

### Problèmes courants
1. **API non accessible** : Vérifier `NEXT_PUBLIC_API_URL`
2. **Authentification** : S'assurer que le token est présent
3. **Migration non appliquée** : Vérifier la table `ai_settings`
4. **CORS** : Configurer les headers appropriés

### Logs utiles
```bash
# Backend
tail -f logs/api.log | grep ai_settings

# Frontend (Console navigateur)
# Les erreurs API sont automatiquement loggées
```
