# Composants et Services Frontend à Copier - SocialSync

## 🚀 Composants Principaux à Récupérer

### 1. Système d'Authentification
**Fichiers à copier :**
- `frontend/src/lib/supabase/client.ts` - Client Supabase
- `frontend/src/app/auth/callback/route.ts` - Gestion des callbacks OAuth
- `frontend/src/app/page.tsx` - Page de login avec Supabase Auth UI

**Fonctionnalités :**
- Authentification Google OAuth
- Gestion des sessions JWT
- Redirection automatique après login
- Protection des routes

### 2. Layout et Navigation
**Fichiers à copier :**
- `frontend/src/features/dashboard/components/DashboardLayout.tsx`
- `frontend/src/features/dashboard/components/Sidebar.tsx`
- `frontend/src/features/dashboard/components/Header.tsx`

**Fonctionnalités :**
- Sidebar responsive avec navigation complète
- Header avec recherche et profil utilisateur
- Navigation vers toutes les fonctionnalités
- Mode compact toggle

### 3. Dashboard Principal
**Fichiers à copier :**
- `frontend/src/features/dashboard/pages/DashboardPage.tsx`
- `frontend/src/features/dashboard/components/KpiCard.tsx`

**Fonctionnalités :**
- KPI cards avec métriques clés
- Welcome panel personnalisé
- Bouton de création rapide
- Design glassmorphism moderne

### 4. Gestion des Comptes Sociaux
**Fichiers à copier :**
- `frontend/src/features/accounts/pages/AccountsPage.tsx`
- `frontend/src/features/accounts/services/socialAccountsApi.ts`
- `frontend/src/features/accounts/types/socialAccount.ts`

**Fonctionnalités :**
- Liste des comptes connectés
- Connexion OAuth pour 8 plateformes
- Gestion des tokens et expiration
- Suppression de comptes
- Statuts de connexion en temps réel

### 5. Inbox et Conversations
**Fichiers à copier :**
- `frontend/src/features/inbox/pages/InboxPage.tsx`
- `frontend/src/features/inbox/components/ConversationList.tsx`
- `frontend/src/features/inbox/components/ThreadView.tsx`
- `frontend/src/features/inbox/components/MessageComposer.tsx`
- `frontend/src/features/inbox/components/InboxSidebar.tsx`

**Fonctionnalités :**
- Liste des conversations par canal
- Vue des threads de messages
- Composition et envoi de messages
- Filtrage par plateforme
- Marquage comme lu

### 6. Hooks React Personnalisés
**Fichiers à copier :**
- `frontend/src/features/inbox/hooks/useConversations.ts`
- `frontend/src/features/inbox/hooks/useMessages.ts`

**Fonctionnalités :**
- Gestion d'état des conversations
- Gestion d'état des messages
- Envoi de messages avec optimistic updates
- Gestion des erreurs et chargement
- Actualisation automatique

### 7. Services API
**Fichiers à copier :**
- `frontend/src/lib/api.ts` - Client API principal
- `frontend/src/features/inbox/services/inboxApi.ts`
- `frontend/src/features/accounts/services/socialAccountsApi.ts`

**Fonctionnalités :**
- Client HTTP avec authentification automatique
- Gestion des headers JWT
- Endpoints pour conversations et comptes sociaux
- Gestion des erreurs centralisée

### 8. Types TypeScript
**Fichiers à copier :**
- `frontend/src/features/inbox/types/inbox.ts`
- `frontend/src/features/inbox/types/api.ts`
- `frontend/src/features/accounts/types/socialAccount.ts`

**Fonctionnalités :**
- Interfaces complètes pour toutes les données
- Types pour les réponses API
- Validation des données
- Cohérence des types

## 🔧 Configuration et Dépendances

### Package.json Dependencies
```json
{
  "@supabase/auth-ui-react": "^0.4.7",
  "@supabase/auth-ui-shared": "^0.1.8",
  "@supabase/ssr": "^0.6.1",
  "@supabase/supabase-js": "^2.53.0",
  "@tanstack/react-query": "^5.85.0",
  "lucide-react": "^0.525.0",
  "framer-motion": "^12.23.3"
}
```

### Variables d'Environnement Requises
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Configuration Supabase
- Projet Supabase avec authentification Google
- Tables : `social_accounts`, `conversations`, `messages`
- RLS policies pour la sécurité
- Webhooks pour l'authentification

## 📁 Structure des Dossiers à Recréer

```
src/
├── lib/
│   ├── supabase/
│   │   └── client.ts
│   ├── api.ts
│   └── react-query.tsx
├── features/
│   ├── dashboard/
│   │   ├── components/
│   │   │   ├── DashboardLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── KpiCard.tsx
│   │   └── pages/
│   │       └── DashboardPage.tsx
│   ├── accounts/
│   │   ├── components/
│   │   ├── pages/
│   │   │   └── AccountsPage.tsx
│   │   ├── services/
│   │   │   └── socialAccountsApi.ts
│   │   └── types/
│   │       └── socialAccount.ts
│   └── inbox/
│       ├── components/
│       │   ├── ConversationList.tsx
│       │   ├── ThreadView.tsx
│       │   ├── MessageComposer.tsx
│       │   └── InboxSidebar.tsx
│       ├── hooks/
│       │   ├── useConversations.ts
│       │   └── useMessages.ts
│       ├── pages/
│       │   └── InboxPage.tsx
│       ├── services/
│       │   └── inboxApi.ts
│       └── types/
│           ├── inbox.ts
│           └── api.ts
└── app/
    ├── auth/
    │   └── callback/
    │       └── route.ts
    ├── dashboard/
    │   └── page.tsx
    ├── layout.tsx
    └── page.tsx
```

## 🎯 Fonctionnalités Clés à Implémenter

### 1. Authentification Complète
- Page de login avec Supabase Auth UI
- Gestion des sessions JWT
- Protection des routes authentifiées
- Callback OAuth pour Google

### 2. Dashboard avec Métriques
- KPI cards pour les métriques importantes
- Welcome panel personnalisé
- Navigation vers toutes les fonctionnalités
- Design moderne et responsive

### 3. Gestion des Comptes Sociaux
- Connexion OAuth pour 8 plateformes
- Gestion des tokens et expiration
- Statuts de connexion en temps réel
- Interface de gestion des comptes

### 4. Inbox Unifié
- Conversations WhatsApp et Instagram
- Filtrage par canal
- Envoi et réception de messages
- Marquage comme lu
- Interface de chat moderne

### 5. API Client Centralisé
- Authentification automatique avec JWT
- Gestion des erreurs centralisée
- Endpoints pour toutes les fonctionnalités
- React Query pour la gestion d'état

## 🔄 Intégration avec Votre Backend

### 1. Adapter les Endpoints
- Modifier `NEXT_PUBLIC_API_URL` vers votre backend
- Adapter les endpoints si nécessaire
- Vérifier la compatibilité des réponses API

### 2. Configuration Supabase
- Créer un projet Supabase
- Configurer l'authentification Google
- Créer les tables nécessaires
- Configurer les RLS policies

### 3. Variables d'Environnement
- Configurer toutes les variables requises
- Vérifier les URLs de callback
- Configurer les clés API des plateformes sociales

### 4. Tests et Validation
- Tester l'authentification
- Vérifier la connexion des comptes sociaux
- Tester l'envoi de messages
- Valider les métriques du dashboard

## 💡 Conseils d'Implémentation

### 1. Copie Progressive
- Commencer par l'authentification
- Ajouter le layout et la navigation
- Implémenter le dashboard
- Ajouter la gestion des comptes
- Finaliser avec l'inbox

### 2. Adaptation des Types
- Vérifier la compatibilité avec votre backend
- Adapter les interfaces si nécessaire
- Maintenir la cohérence des types

### 3. Gestion des Erreurs
- Implémenter la gestion d'erreurs centralisée
- Ajouter des fallbacks pour les cas d'échec
- Logging des erreurs pour le debugging

### 4. Performance
- Utiliser React Query pour le cache
- Implémenter le lazy loading
- Optimiser les re-renders

Cette liste couvre tous les composants essentiels du frontend SocialSync que vous devriez copier pour avoir une base solide dans votre nouveau projet.





