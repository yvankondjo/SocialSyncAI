# Recherche - Migration du Design Social-Sync-AI

## Analyse de la Structure Existante

### Architecture Actuelle (/workspace/frontend/)
- **Layout Principal**: `/app/dashboard/layout.tsx` avec AuthGuard
- **Sidebar**: Composant complexe avec sections collapsibles et navigation hiérarchique
- **Pages Existantes**:
  - Activity/Chat: `/dashboard/activity/chat` → Utilise `InboxPage` component
  - Analytics: `/dashboard/analytics` (pas encore implémentée)
  - Connect: `/dashboard/connect` (pas encore implémentée)
  - Sources/Data: `/dashboard/sources/data`
  - Sources/FAQ: `/dashboard/sources/faq`
  - Settings/AI: `/dashboard/settings/ai`
  - Settings/Chat Interfaces: `/dashboard/settings/chat-interfaces`
  - Settings/Custom Domain: `/dashboard/settings/custom-domain`
  - Playground/Compare: `/dashboard/playground/compare`

### Fonctionnalités Actuelles Importantes
1. **Chat/Inbox**: Interface complète avec conversations, messages, envoi de messages, filtres par canal
2. **Authentification**: Système AuthGuard avec useAuth hook
3. **Sidebar**: Navigation collapsible avec gestion d'état (useSidebarStore)
4. **API Integration**: Services pour conversations, comptes sociaux, messages

## Analyse de la Nouvelle Structure (/workspace/social-sync-ai/)

### Architecture Cible
- **Layout Simplifié**: Structure plus simple avec Sidebar + Header pattern
- **Composants UI**: Utilise shadcn/ui avec design cohérent
- **Navigation**: Sidebar avec routes directes (pas de hiérarchie complexe)
- **Pages avec Loading States**: Tous les composants ont des états de chargement

### Nouvelles Pages Analysées
1. **Activity/Chat**: Interface de gestion des conversations avec édition des réponses IA
2. **Analytics**: Dashboard complet avec KPIs, graphiques (Recharts), métriques
3. **Connect**: Gestion des intégrations sociales et widget web
4. **Sources/Data**: Version simplifiée de gestion des fichiers
5. **Sources/FAQ**: Gestion FAQ avec support multi-questions par réponse
6. **Settings/AI**: Configuration des modèles IA avec nouveaux contrôles
7. **Settings/Chat Interface**: Personnalisation de l'interface de chat
8. **Settings/Custom Domains**: Gestion des domaines personnalisés
9. **Playground**: Interface de test des modèles IA
10. **Playground/Compare**: Comparaison côte à côte des modèles

### Différences Architecturales Clés

#### Layouts
- **Ancien**: Layout complexe avec AuthGuard et sidebar collapsible avancée
- **Nouveau**: Layout simple avec pattern `<Sidebar /><Header /><Content />`

#### Navigation
- **Ancien**: Navigation hiérarchique avec sous-menus collapsibles
- **Nouveau**: Navigation plate avec routes directes

#### Composants
- **Ancien**: Composants métier complexes (InboxPage)
- **Nouveau**: Composants simples avec état local, design uniforme

#### États de Chargement
- **Ancien**: États de chargement basiques
- **Nouveau**: Loading states dédiés pour chaque page

## Composants UI Communs
- Tous utilisent shadcn/ui
- Icons: Lucide React
- Charts: Recharts (pour Analytics)
- Patterns de state management avec useState
- Responsive design avec Tailwind CSS

## Points de Migration Critiques

### Fonctionnalités à Préserver
1. **Authentification**: Système AuthGuard et useAuth
2. **API Integration**: Services existants pour conversations, messages
3. **État de la Sidebar**: useSidebarStore pour la persistance
4. **Logique Métier**: Envoi de messages, filtres, gestion des conversations

### Fonctionnalités à Adapter
1. **Design System**: Migration vers le nouveau design
2. **Navigation**: Simplification de la structure de navigation
3. **Loading States**: Ajout des nouveaux patterns de chargement
4. **Composants**: Remplacement par les nouveaux composants

### Nouvelles Fonctionnalités à Intégrer
1. **Analytics Dashboard**: Implémentation complète avec Recharts
2. **Connect Page**: Gestion des intégrations sociales
3. **Enhanced Settings**: Nouvelles options de configuration
4. **Playground**: Interface de test des modèles IA

## Stratégie de Migration

### Approche Page par Page
1. Conserver les fonctionnalités existantes
2. Appliquer le nouveau design et architecture
3. Documenter les changements dans fichiers *-modif.md
4. Tester la compatibilité avec l'API existante

### Ordre de Migration Recommandé
1. **Layout et Sidebar** (fondation)
2. **Activity/Chat** (page la plus complexe)
3. **Analytics** (nouvelle page avec graphiques)
4. **Connect** (nouvelle page avec intégrations)
5. **Sources (Data/FAQ)** (pages simplifiées)
6. **Settings** (pages de configuration)
7. **Playground** (nouvelles fonctionnalités)