# Analyse Complète du Frontend SocialSync - Logique d'API et Fonctionnalités

## Vue d'ensemble du Projet

**SocialSync** est une plateforme de gestion de réseaux sociaux avec IA qui permet de :
- Gérer plusieurs comptes de réseaux sociaux
- Automatiser la publication de contenu
- Gérer les conversations et messages directs
- Analyser les performances et métriques
- Intégrer des webhooks pour la synchronisation en temps réel

## Architecture Frontend

### Technologies Utilisées
- **Framework** : Next.js 15 avec App Router
- **Styling** : Tailwind CSS v4 + shadcn/ui
- **State Management** : React Query (TanStack Query)
- **Authentification** : Supabase Auth
- **UI Components** : Radix UI + Lucide React Icons
- **TypeScript** : Typage strict complet

### Structure des Dossiers
```
frontend/src/
├── app/                    # Pages et routing Next.js
├── components/             # Composants UI partagés
├── features/               # Fonctionnalités organisées par domaine
├── hooks/                  # Hooks React personnalisés
├── lib/                    # Utilitaires et configuration
└── types/                  # Types TypeScript
```

## Système d'Authentification

### Configuration Supabase
- **Client Browser** : `@/lib/supabase/client.ts`
- **Authentification** : Google OAuth + Supabase Auth UI
- **Session Management** : Gestion automatique des tokens JWT
- **Callback Route** : `/auth/callback` pour la redirection OAuth

### Flux d'Authentification
1. **Page d'accueil** (`/`) : Affichage du composant Auth Supabase
2. **OAuth Google** : Redirection vers Google avec Supabase
3. **Callback** : Échange du code OAuth contre une session
4. **Redirection** : Vers `/dashboard` après authentification réussie
5. **Protection des routes** : Vérification automatique de la session

### Gestion des Sessions
```typescript
// Récupération de la session
const { data: { session } } = await supabase.auth.getSession();

// Headers d'authentification automatiques
const headers = {
  "Content-Type": "application/json",
  "Authorization": `Bearer ${session.access_token}`,
};
```

## Gestion des Comptes de Réseaux Sociaux

### Plateformes Supportées
- **Instagram** : API Business avec OAuth
- **TikTok** : API Business avec OAuth
- **YouTube** : API YouTube Data v3
- **X (Twitter)** : API Twitter v2
- **Reddit** : API Reddit OAuth
- **Facebook** : Graph API v23.0
- **LinkedIn** : API LinkedIn Marketing
- **WhatsApp** : WhatsApp Business API

### API Social Accounts (`/api/social-accounts`)

#### Endpoints
- `GET /connect/{platform}` : Génère l'URL d'autorisation OAuth
- `GET /connect/{platform}/callback` : Gère le callback OAuth
- `GET /` : Liste tous les comptes connectés de l'utilisateur
- `DELETE /{account_id}` : Supprime un compte social

#### Fonctionnalités
- **OAuth Flow** : Gestion complète des flux d'autorisation
- **State JWT** : Sécurisation des callbacks avec JWT
- **Upsert Automatique** : Création/mise à jour automatique des comptes
- **Validation des Tokens** : Vérification de l'expiration des tokens
- **Gestion des Erreurs** : Redirection avec messages d'erreur

#### Types de Données
```typescript
interface SocialAccount {
  id: string;
  platform: SocialPlatform;
  account_id: string;
  username: string;
  display_name?: string;
  profile_url?: string;
  access_token: string;
  refresh_token?: string;
  token_expires_at?: string;
  is_active: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
}
```

## Gestion des Conversations et Messages

### API Conversations (`/api/conversations`)

#### Endpoints
- `GET /` : Liste des conversations avec filtres (canal, limite)
- `GET /{conversation_id}/messages` : Messages d'une conversation
- `POST /{conversation_id}/messages` : Envoi d'un message
- `PATCH /{conversation_id}/read` : Marquer comme lu

#### Fonctionnalités
- **Filtrage par Canal** : WhatsApp, Instagram, ou tous
- **Pagination** : Limite configurable (max 100 conversations, 200 messages)
- **Gestion des Participants** : Identification client/agent
- **Marquage de Lecture** : Suivi des conversations non lues
- **Validation des Permissions** : Vérification de l'appartenance utilisateur

#### Types de Données
```typescript
interface Conversation {
  id: string;
  channel: 'instagram' | 'whatsapp';
  customer_name?: string;
  customer_identifier: string;
  last_message_at?: string;
  last_message_snippet: string;
  unread_count: number;
  social_account_id: string;
}

interface Message {
  id: string;
  conversation_id: string;
  direction: 'inbound' | 'outbound';
  content: string;
  created_at: string;
  sender_id?: string;
  is_from_agent: boolean;
}
```

### Hooks React pour les Conversations

#### `useConversations()`
- **État** : Liste des conversations, chargement, erreurs
- **Filtrage** : Par canal (Instagram, WhatsApp, tous)
- **Actualisation** : Fonction de rechargement
- **Gestion des Erreurs** : Affichage des erreurs utilisateur

#### `useMessages(conversationId)`
- **État** : Messages, chargement, envoi en cours
- **Actions** : Envoi de message, marquage comme lu
- **Optimistic Updates** : Ajout immédiat des messages envoyés
- **Rechargement** : Synchronisation automatique après envoi

## Dashboard et Métriques

### Composants du Dashboard
- **KPI Cards** : Posts automatisés, DMs résolus, ROI, taux d'engagement
- **Welcome Panel** : Salutation personnalisée avec bouton de création
- **Navigation** : Sidebar avec toutes les fonctionnalités
- **Header** : Recherche, notifications, profil utilisateur

### Métriques Affichées
- **Posts Automatisés** : Nombre de publications programmées
- **DMs Résolus** : Messages directs traités (70% par IA)
- **ROI Tracké** : Retour sur investissement mesuré
- **Taux d'Engagement** : Performance globale des contenus

## Intégration Instagram

### API Instagram (`/api/instagram`)

#### Endpoints Principaux
- `POST /validate-credentials` : Validation des credentials
- `POST /send-dm` : Envoi de message direct
- `POST /publish-post` : Publication de post feed
- `POST /publish-story` : Publication de story
- `POST /reply-comment` : Réponse aux commentaires
- `POST /send-dm-batch` : Envoi en lot de messages
- `GET /conversations` : Récupération des conversations
- `POST /webhook` : Réception des webhooks Meta

#### Fonctionnalités Avancées
- **Gestion des Credentials** : Validation automatique des tokens
- **Publication de Contenu** : Posts, stories, commentaires
- **Messagerie Directe** : Envoi individuel et en lot
- **Webhooks** : Réception des événements en temps réel
- **Gestion des Erreurs** : Retry automatique et fallbacks

## Intégration WhatsApp

### API WhatsApp (`/api/whatsapp`)

#### Endpoints Principaux
- `POST /validate-credentials` : Validation des credentials
- `POST /send-text` : Envoi de message texte
- `POST /send-template` : Envoi de template approuvé
- `POST /send-media` : Envoi de média (image, vidéo, document)
- `POST /send-batch` : Envoi en lot de messages
- `GET /business-profile` : Profil business WhatsApp
- `POST /webhook` : Réception des webhooks Meta

#### Fonctionnalités
- **Templates Approuvés** : Utilisation des templates Meta
- **Médias Supportés** : Images, vidéos, documents, audio
- **Envoi en Lot** : Optimisation des performances
- **Webhooks** : Réception des statuts et messages entrants
- **Validation** : Vérification des numéros et credentials

## Système d'Analytics

### API Analytics (`/api/analytics`)

#### Endpoints
- `POST /sync/{content_id}` : Synchronisation des analytics d'un contenu
- `POST /sync/user/{user_id}` : Synchronisation globale utilisateur
- `GET /history/{content_id}` : Historique des analytics
- `GET /trends/{user_id}` : Tendances et agrégations

#### Métriques Suivies
- **Engagement** : Likes, partages, commentaires
- **Portée** : Impressions, reach, clics
- **Conversions** : Actions commerciales
- **Tendances** : Évolution temporelle des performances

#### Fonctionnalités
- **Synchronisation Automatique** : Tâches en arrière-plan
- **Historique** : Données sur 30 jours par défaut
- **Agrégation** : Calculs par jour, semaine, mois
- **Sécurité** : Vérification des permissions utilisateur

## Widget Web Intégrable

### API Web Widget (`/api/web-widget`)

#### Endpoints
- `GET /config/{widget_id}` : Configuration du widget
- `POST /messages` : Envoi de message via widget
- `GET /static/{filename}` : Fichiers statiques du widget
- `POST /webhook` : Réception des événements widget

#### Fonctionnalités
- **Personnalisation** : Couleurs, logo, texte
- **Intégration** : Script JavaScript à copier
- **Messagerie** : Chat en temps réel
- **Analytics** : Suivi des interactions
- **Multi-tenant** : Support de plusieurs organisations

## Gestion des Erreurs et Sécurité

### Stratégies de Sécurité
- **JWT Tokens** : Authentification via Supabase
- **CORS** : Configuration des origines autorisées
- **Validation** : Vérification des données avec Pydantic
- **Permissions** : Vérification des droits utilisateur
- **Rate Limiting** : Protection contre les abus

### Gestion des Erreurs
- **HTTP Status Codes** : Codes d'erreur appropriés
- **Messages Utilisateur** : Erreurs compréhensibles
- **Logging** : Traçabilité des erreurs
- **Fallbacks** : Gestion gracieuse des échecs
- **Retry Logic** : Tentatives automatiques de récupération

## Configuration et Variables d'Environnement

### Variables Requises
```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend URL (pour les callbacks)
FRONTEND_URL=http://localhost:3000
```

### Configuration Supabase
- **Authentication** : Google OAuth configuré
- **Database** : Tables pour social_accounts, conversations, messages
- **RLS Policies** : Sécurisation des données par utilisateur
- **Webhooks** : Configuration pour les événements d'authentification

## Architecture des Services

### Services Backend
- **SocialAuthService** : Gestion OAuth des plateformes
- **ConversationService** : Logique métier des conversations
- **InstagramService** : Intégration API Instagram
- **WhatsAppService** : Intégration API WhatsApp
- **AnalyticsService** : Traitement des métriques
- **MessageBatcher** : Optimisation des envois en lot

### Services Frontend
- **InboxApi** : Gestion des conversations et messages
- **SocialAccountsApi** : Gestion des comptes sociaux
- **React Query** : Cache et synchronisation des données

## Fonctionnalités Avancées

### Automatisation
- **Publication Programmable** : Planification des posts
- **Réponses Automatiques** : IA pour les messages entrants
- **Synchronisation** : Mise à jour automatique des données
- **Webhooks** : Réactivité en temps réel

### Intelligence Artificielle
- **Génération de Contenu** : Création automatique de posts
- **Réponses Intelligentes** : Suggestions de réponses
- **Analyse des Sentiments** : Compréhension du contexte
- **Optimisation** : Recommandations de performance

### Intégrations
- **Slack/Teams** : Notifications et alertes
- **CRM** : Synchronisation des données clients
- **Analytics** : Intégration Google Analytics, Facebook Pixel
- **Webhooks** : Connecteurs personnalisés

## Points d'Intégration Clés

### 1. Authentification Supabase
- Gestion des sessions utilisateur
- Tokens JWT pour l'API backend
- OAuth Google intégré

### 2. API Backend FastAPI
- Endpoints RESTful complets
- Validation des données avec Pydantic
- Gestion des erreurs HTTP

### 3. Webhooks Meta
- Réception des événements Instagram/WhatsApp
- Traitement en temps réel
- Mise à jour automatique des conversations

### 4. Base de Données
- Schéma relationnel complet
- Politiques RLS Supabase
- Migrations automatisées

## Recommandations pour l'Intégration

### 1. Récupération des Composants
- **Authentification** : Copier le système Supabase complet
- **Navigation** : Sidebar et Header avec toutes les routes
- **Dashboard** : KPI cards et métriques
- **Inbox** : Gestion des conversations et messages
- **Accounts** : Gestion des comptes sociaux

### 2. Récupération des Services API
- **InboxApi** : Gestion des conversations
- **SocialAccountsApi** : Gestion des comptes
- **Hooks React** : useConversations, useMessages
- **Types TypeScript** : Interfaces complètes

### 3. Récupération de la Logique Métier
- **OAuth Flow** : Connexion des réseaux sociaux
- **Gestion des Sessions** : Authentification automatique
- **Gestion des Erreurs** : Stratégies de fallback
- **Optimisations** : React Query, lazy loading

### 4. Configuration Requise
- **Supabase** : Projet avec tables et RLS
- **Variables d'environnement** : URLs et clés API
- **OAuth Apps** : Configuration des plateformes sociales
- **Webhooks** : Endpoints pour les événements

Cette analyse couvre l'ensemble de la logique d'API et des fonctionnalités du frontend SocialSync, fournissant une base solide pour l'intégration dans votre nouveau projet.




