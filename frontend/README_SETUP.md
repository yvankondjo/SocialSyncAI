# Configuration du Frontend SocialSync

## Variables d'environnement nécessaires

Créez un fichier `.env.local` à la racine du projet frontend avec :

```bash
# Configuration de l'API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Configuration Supabase
NEXT_PUBLIC_SUPABASE_URL=votre_url_supabase
NEXT_PUBLIC_SUPABASE_ANON_KEY=votre_clé_anon_supabase

# Configuration Frontend
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

## Démarrage du projet

```bash
# Installation des dépendances
npm install
# ou
pnpm install

# Démarrage en mode développement
npm run dev
# ou
pnpm dev
```

## Fonctionnalités implémentées

### ✅ Authentification
- Connexion/Déconnexion avec Supabase Auth
- Protection automatique des routes dashboard
- Gestion des états de chargement

### ✅ Comptes sociaux
- Affichage des comptes connectés depuis la base de données
- Connexion OAuth pour Instagram, WhatsApp, Twitter, YouTube, TikTok
- Gestion des statuts (actif, expiré, expire bientôt)
- Suppression de comptes

### ✅ Inbox
- Liste des conversations par plateforme (WhatsApp, Instagram)
- Affichage des messages avec distinction envoyés/reçus
- Envoi de messages selon la plateforme
- Marquage automatique comme lu
- Gestion des erreurs d'envoi

### ✅ Dashboard
- KPIs dynamiques connectés aux données réelles
- Statut temps réel des comptes sociaux
- Actions rapides vers les différentes sections
- Gestion des erreurs et états de chargement

### ✅ Sécurité
- Authentification JWT avec Supabase
- Politiques RLS (Row Level Security) côté base de données
- Vérifications côté frontend complémentaires
- Protection contre les accès non autorisés

## Architecture

### Frontend (Next.js + TypeScript)
- **AuthGuard**: Protection des routes authentifiées
- **API Client**: Communication avec le backend
- **Services**: Logique métier séparée
- **Hooks**: Gestion des états et effets

### Backend (FastAPI + Supabase)
- **Routes REST**: Endpoints pour comptes, conversations, messages
- **Services**: Logique métier et intégrations plateformes
- **Sécurité**: JWT + RLS pour protection des données
- **Base de données**: PostgreSQL avec extensions pgvector

## Flux d'authentification

1. **Connexion** → Page `/auth` avec Supabase Auth UI
2. **Callback** → `/auth/callback` traite la réponse OAuth
3. **Dashboard** → `/dashboard` protégé par AuthGuard
4. **API** → Toutes les requêtes incluent le token JWT
5. **Base** → RLS applique automatiquement les filtres utilisateur

## Flux d'envoi de messages

1. **Frontend** → `ConversationsService.sendMessage()`
2. **API** → Route `/conversations/{id}/messages` (POST)
3. **Service** → `ConversationService.send_message()`
4. **Plateforme** → Envoi selon WhatsApp/Instagram APIs
5. **Base** → Sauvegarde du message envoyé
6. **Frontend** → Mise à jour optimiste puis rechargement
