# Plan de Migration - Social-Sync-AI Design

## Vue d'Ensemble

Migration complète du design et de l'architecture des pages existantes vers le nouveau design Social-Sync-AI, en conservant toutes les fonctionnalités actuelles et en intégrant les nouvelles fonctionnalités.

## Phase 1: Fondation - Layout et Navigation

### 1.1 Migration du Layout Principal
**Fichiers concernés:**
- `/app/dashboard/layout.tsx` → Nouveau pattern avec Sidebar + Header
- `/components/sidebar/Sidebar.tsx` → Simplification selon nouveau design
- Création de `/components/header.tsx` (nouveau composant)

**Changements:**
- Simplification de la navigation hiérarchique vers navigation plate
- Conservation de l'AuthGuard et useSidebarStore
- Nouveau design avec pattern `<Sidebar /><Header /><Content />`
- Mise à jour des routes pour correspondre au nouveau mapping

**Routes à mettre à jour:**
```
Ancien → Nouveau
/dashboard → /playground (page d'accueil)
/dashboard/activity/chat → /activity/chat
/dashboard/sources/data → /sources/data
/dashboard/sources/faq → /sources/faq
/dashboard/settings/ai → /settings/ai
/dashboard/settings/chat-interfaces → /settings/chat-interface
/dashboard/settings/custom-domain → /settings/custom-domains
/dashboard/playground/compare → /playground/compare
```

### 1.2 Nouveaux Composants de Base
- `components/header.tsx`: Header avec notifications et profil utilisateur
- Mise à jour des composants UI pour correspondre au nouveau design
- États de chargement uniformes (`loading.tsx` pour chaque page)

## Phase 2: Migration des Pages Existantes

### 2.1 Activity/Chat - Priorité Haute
**Page:** `/app/activity/chat/page.tsx`

**Fonctionnalités à conserver:**
- Système de conversations avec API backend
- Envoi/réception de messages
- Filtres par canal social
- Gestion des comptes sociaux connectés
- Auto-reply et AI toggles
- Interface de chat complète

**Nouvelles fonctionnalités à intégrer:**
- Édition des réponses IA
- Interface de gestion des conversations améliorée
- Nouveaux filtres (statut, source, date)
- Modal d'édition des messages
- Toggle auto-response par conversation

**Fichier de documentation:** `chat-modif.md`

### 2.2 Analytics - Nouvelle Page
**Page:** `/app/analytics/page.tsx` (à créer)

**Fonctionnalités à implémenter:**
- Dashboard KPI avec métriques temps réel
- Graphiques interactifs avec Recharts:
  - Line chart: Conversations dans le temps
  - Bar chart: Temps de réponse
  - Pie chart: Distribution des sentiments
  - Bar chart horizontal: Top sujets
- Tables avec questions fréquentes et activité récente
- Filtres par période (7j, 30j, 90j)
- Export et refresh des données

**Dépendances à ajouter:**
- `recharts` pour les graphiques
- Nouveaux types pour les données analytics

**Fichier de documentation:** `analytics-modif.md`

### 2.3 Connect - Nouvelle Page
**Page:** `/app/connect/page.tsx` (à créer)

**Fonctionnalités à implémenter:**
- Gestion des intégrations sociales (Meta, X, WhatsApp)
- Statut de connexion des comptes
- Configuration du widget web
- Prévisualisation en temps réel du widget
- Génération du code d'installation
- Personnalisation des thèmes (4 thèmes prédéfinis)
- Configuration de position et messages

**Intégration avec l'existant:**
- Utilisation des services SocialAccountsService existants
- Conservation des données de comptes connectés

**Fichier de documentation:** `connect-modif.md`

### 2.4 Sources/Data - Simplification
**Page:** `/app/sources/data/page.tsx`

**Changements:**
- Simplification de l'interface selon le nouveau design
- Conservation du système de upload de fichiers
- Suppression des intégrations complexes (selon specs)
- Interface épurée avec focus sur les fichiers uploadés

**Fonctionnalités conservées:**
- Upload de fichiers
- Gestion des fichiers uploadés
- Recherche dans les fichiers
- Statuts d'indexation

**Fichier de documentation:** `data-modif.md`

### 2.5 Sources/FAQ - Amélioration
**Page:** `/app/sources/faq/page.tsx`

**Nouvelles fonctionnalités:**
- Support multi-questions par réponse (fonctionnalité clé)
- Interface d'édition améliorée
- Gestion dynamique des questions
- Système de tags amélioré

**Fonctionnalités conservées:**
- CRUD des FAQ
- Système de recherche
- Filtres par statut

**Fichier de documentation:** `faq-modif.md`

### 2.6 Settings/AI - Amélioration
**Page:** `/app/settings/ai/page.tsx`

**Nouvelles fonctionnalités:**
- Toggle "Disable AI" (fonctionnalité clé)
- Sélection de modèles avec indicateurs de coût
- Configuration avancée (température, tokens, timeout)
- Modes de réponse (FAQ Only, Hybrid, AI Only)

**Fonctionnalités conservées:**
- Configuration des modèles IA
- System prompt et instructions personnalisées
- Sauvegarde des paramètres

**Fichier de documentation:** `ai-modif.md`

### 2.7 Settings/Chat Interface - Nouvelle Page
**Page:** `/app/settings/chat-interface/page.tsx` (à créer)

**Fonctionnalités à implémenter:**
- Personnalisation complète de l'interface de chat
- Système d'onglets (Appearance, Messages, Behavior)
- Prévisualisation en temps réel
- Configuration des thèmes et couleurs
- Templates de messages
- Paramètres de comportement

**Fichier de documentation:** `chat-interface-modif.md`

### 2.8 Settings/Custom Domains - Nouvelle Page
**Page:** `/app/settings/custom-domains/page.tsx` (à créer)

**Fonctionnalités à implémenter:**
- Gestion des domaines personnalisés
- Configuration DNS
- Vérification SSL
- Processus de vérification de domaine
- Interface step-by-step

**Fichier de documentation:** `custom-domains-modif.md`

## Phase 3: Nouvelles Fonctionnalités

### 3.1 Playground - Page Principale
**Page:** `/app/playground/page.tsx` (à créer)

**Fonctionnalités:**
- Interface de test des modèles IA
- Configuration en temps réel
- Chat de test
- Sauvegarde vers agent
- Instructions système personnalisées

**Fichier de documentation:** `playground-modif.md`

### 3.2 Playground/Compare - Migration
**Page:** `/app/playground/compare/page.tsx`

**Améliorations:**
- Interface côte à côte améliorée
- Métriques de performance
- Export des comparaisons
- Swap des modèles
- Reset des conversations

**Fichier de documentation:** `compare-modif.md`

## Phase 4: Tests et Finalisation

### 4.1 Tests de Compatibilité
- Vérification de toutes les APIs existantes
- Test des fonctionnalités de chat et messages
- Validation des intégrations sociales
- Tests responsive

### 4.2 Documentation Finale
- Compilation de tous les fichiers *-modif.md
- Documentation des changements d'API si nécessaire
- Guide de migration pour les utilisateurs

## Dépendances Techniques

### Nouvelles Dépendances à Ajouter
```json
{
  "recharts": "^2.8.0", // Pour Analytics
  "date-fns": "^2.30.0" // Pour gestion des dates
}
```

### Composants UI à Créer/Modifier
- `components/header.tsx` (nouveau)
- `components/ui/slider.tsx` (pour settings)
- `components/ui/progress.tsx` (pour analytics)
- Mise à jour des composants existants pour le nouveau design

### Types TypeScript
- Types pour les données analytics
- Types pour les configurations de widget
- Types pour les domaines personnalisés
- Extension des types existants

## Ordre d'Implémentation Recommandé

1. **Layout et Sidebar** (fondation critique)
2. **Activity/Chat** (page la plus utilisée)
3. **Analytics** (nouvelle fonctionnalité importante)
4. **Connect** (intégrations sociales)
5. **Settings/AI** (configuration critique)
6. **Sources (Data/FAQ)** (fonctionnalités supportées)
7. **Settings (Chat Interface/Custom Domains)** (nouvelles configurations)
8. **Playground** (fonctionnalités avancées)

## Critères de Validation

### Pour Chaque Page
- ✅ Design conforme au nouveau système
- ✅ Fonctionnalités existantes préservées
- ✅ Nouvelles fonctionnalités implémentées
- ✅ Responsive design
- ✅ États de chargement
- ✅ Gestion d'erreur
- ✅ Documentation *-modif.md complète

### Tests de Régression
- ✅ Authentification fonctionnelle
- ✅ API calls préservées
- ✅ Navigation cohérente
- ✅ Performance maintenue
- ✅ Compatibilité mobile