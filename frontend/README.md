# SocialSync Frontend

Interface moderne pour la gestion des réseaux sociaux avec authentification Supabase et connexion à l'API backend.

## 🚀 Fonctionnalités

- **Authentification Supabase** : Connexion Google OAuth
- **Gestion des comptes sociaux** : Connexion aux vraies plateformes
- **Inbox unifié** : Conversations WhatsApp et Instagram
- **Dashboard** : Métriques et vue d'ensemble
- **Interface moderne** : Design avec Tailwind CSS et shadcn/ui

## 📋 Prérequis

- Node.js 18+
- Backend SocialSync en cours d'exécution
- Projet Supabase configuré

## 🛠️ Installation

1. **Installer les dépendances**
```bash
cd frontend
npm install
```

2. **Configuration de l'environnement**

Copiez le fichier d'exemple et configurez vos variables :
```bash
cp env.example .env.local
```

Remplissez les variables dans `.env.local` :
```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Frontend URL
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
```

3. **Démarrer le serveur de développement**
```bash
npm run dev
```

## 🔧 Configuration Supabase

### 1. Créer un projet Supabase
1. Allez sur [supabase.com](https://supabase.com)
2. Créez un nouveau projet
3. Notez l'URL et la clé anonyme

### 2. Configurer l'authentification Google
1. Dans votre projet Supabase, allez dans Authentication > Providers
2. Activez Google
3. Configurez les credentials OAuth Google
4. Ajoutez l'URL de redirection : `http://localhost:3000/auth/callback`

### 3. Créer les tables de base de données
```sql
-- Tables pour les comptes sociaux
CREATE TABLE social_accounts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  platform TEXT NOT NULL,
  account_id TEXT NOT NULL,
  username TEXT NOT NULL,
  display_name TEXT,
  profile_url TEXT,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  token_expires_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT true,
  user_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Tables pour les conversations
CREATE TABLE conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  channel TEXT NOT NULL,
  customer_name TEXT,
  customer_identifier TEXT NOT NULL,
  last_message_at TIMESTAMPTZ,
  last_message_snippet TEXT DEFAULT '',
  unread_count INTEGER DEFAULT 0,
  social_account_id UUID REFERENCES social_accounts(id),
  user_id UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Tables pour les messages
CREATE TABLE messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
  direction TEXT NOT NULL,
  content TEXT NOT NULL,
  sender_id TEXT,
  is_from_agent BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Activer RLS
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Politiques RLS
CREATE POLICY "Users can view own social accounts" ON social_accounts
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own conversations" ON conversations
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own messages" ON messages
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM conversations
      WHERE conversations.id = messages.conversation_id
      AND conversations.user_id = auth.uid()
    )
  );
```

## 📱 Pages et Fonctionnalités

### Authentification
- **`/auth`** : Page de connexion avec Supabase Auth UI
- **`/auth/callback`** : Gestion des callbacks OAuth

### Dashboard
- **`/dashboard`** : Vue d'ensemble avec métriques
- **`/dashboard/accounts`** : Gestion des comptes sociaux
- **`/dashboard/inbox`** : Inbox unifié pour conversations

## 🔗 Connexion au Backend

Le frontend se connecte automatiquement au backend via les services API :

### Services Disponibles

#### SocialAccountsService
- `getSocialAccounts()` : Liste des comptes connectés
- `getConnectUrl(platform)` : URL d'autorisation OAuth
- `deleteSocialAccount(accountId)` : Suppression d'un compte

#### ConversationsService
- `getConversations(channel?, limit?)` : Liste des conversations
- `getMessages(conversationId, limit?)` : Messages d'une conversation
- `sendMessage(conversationId, content)` : Envoi d'un message
- `markAsRead(conversationId)` : Marquer comme lu

### Gestion des Erreurs

Toutes les erreurs sont automatiquement gérées avec :
- Affichage d'erreurs utilisateur
- Retry automatique pour les échecs temporaires
- Logging des erreurs pour le debugging

## 🎨 Personnalisation

### Thème
Le frontend utilise Tailwind CSS avec un thème moderne :
- Couleurs indigo/violet pour le branding
- Design glassmorphism pour les cartes
- Animations fluides avec Framer Motion

### Composants UI
Utilisation de shadcn/ui pour des composants cohérents :
- Cards, Buttons, Inputs
- Dialogs, Dropdowns, Tooltips
- Avatars, Badges, Toasts

## 🚀 Déploiement

### Vercel
1. Connectez votre dépôt GitHub à Vercel
2. Configurez les variables d'environnement
3. Déployez automatiquement

### Variables d'environnement pour la production
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-prod-anon-key
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_FRONTEND_URL=https://your-frontend-domain.com
```

## 🔍 Debugging

### Outils de développement
- **React DevTools** : Inspection des composants
- **Redux DevTools** : État de l'application
- **Network Tab** : Requêtes API
- **Console** : Logs d'erreurs

### Logs importants
- Erreurs d'authentification Supabase
- Échecs de connexion API
- Erreurs OAuth
- Problèmes de permissions

## 📞 Support

Pour des problèmes ou questions :
1. Vérifiez les logs de la console
2. Validez la configuration Supabase
3. Vérifiez que le backend est accessible
4. Consultez la documentation API backend

## 🎯 Roadmap

- [ ] Analytics et métriques avancées
- [ ] Planification de posts
- [ ] Automatisations IA
- [ ] Templates de messages
- [ ] Intégrations CRM
- [ ] Notifications push
- [ ] Mode hors ligne


