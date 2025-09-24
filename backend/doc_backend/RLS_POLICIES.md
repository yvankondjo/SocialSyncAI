# Documentation des Politiques RLS (Row-Level Security)

## Vue d'ensemble

Ce document décrit les politiques de sécurité au niveau des lignes (RLS) implémentées dans SocialSyncAI pour assurer l'isolation des données entre les utilisateurs et maintenir la sécurité multi-tenant.

## Principe de base

Chaque utilisateur ne peut accéder qu'à ses propres données, à l'exception des administrateurs qui ont un accès complet à toutes les données.

## Politiques par table

### 1. Table `users`

**Politiques :**
- `"Users can view their own profile"` : Un utilisateur peut voir uniquement son propre profil
- `"Users can update their own profile"` : Un utilisateur peut modifier uniquement son propre profil
- `"Admins manage all users"` : Les administrateurs peuvent voir et gérer tous les utilisateurs

**Logique :**
```sql
-- Utilisateur normal : auth.uid() = id
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

### 2. Table `social_accounts`

**Politiques :**
- `"Users own their accounts"` : Un utilisateur peut voir ses comptes sociaux
- `"Users can manage their accounts"` : Un utilisateur peut gérer ses comptes sociaux
- `"Admins manage all social_accounts"` : Les administrateurs peuvent tout gérer

**Logique :**
```sql
-- Utilisateur normal : auth.uid() = user_id
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

### 3. Table `content`

**Politiques :**
- `"Users can view their content"` : Un utilisateur peut voir le contenu de ses comptes sociaux
- `"Users can manage their content"` : Un utilisateur peut gérer le contenu de ses comptes sociaux
- `"Admins manage all content"` : Les administrateurs peuvent tout gérer

**Logique :**
```sql
-- Utilisateur normal : auth.uid() IN (SELECT sa.user_id FROM social_accounts sa WHERE sa.id = social_account_id)
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

### 4. Table `analytics`

**Politiques :**
- `"Users can view their analytics"` : Un utilisateur peut voir les analytics de son contenu
- `"Users can manage their analytics"` : Un utilisateur peut gérer les analytics de son contenu
- `"Admins manage all analytics"` : Les administrateurs peuvent tout gérer

**Logique :**
```sql
-- Utilisateur normal : auth.uid() IN (
--     SELECT sa.user_id FROM social_accounts sa 
--     JOIN content c ON c.social_account_id = sa.id 
--     WHERE c.id = content_id
-- )
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

### 5. Table `ai_insights`

**Politiques :**
- `"Users can view their ai_insights"` : Un utilisateur peut voir ses insights IA
- `"Users can manage their ai_insights"` : Un utilisateur peut gérer ses insights IA
- `"Admins manage all ai_insights"` : Les administrateurs peuvent tout gérer

**Logique :**
```sql
-- Utilisateur normal : auth.uid() = user_id
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

### 6. Table `analytics_history`

**Politiques :**
- `"Users manage their analytics history"` : Un utilisateur peut gérer son historique d'analytics
- `"Admins manage all analytics_history"` : Les administrateurs peuvent tout gérer

**Logique :**
```sql
-- Utilisateur normal : auth.uid() = user_id
-- Admin : (SELECT role FROM users WHERE id = auth.uid()) = 'admin'
```

## Hiérarchie des données

```
User (auth.uid())
├── users (profil)
├── social_accounts (comptes sociaux)
│   └── content (publications)
│       └── analytics (métriques)
├── ai_insights (insights IA)
└── analytics_history (historique)
```

## Rôles et permissions

### Utilisateur normal (`role = 'user'`)
- Accès en lecture/écriture à ses propres données uniquement
- Isolation complète des données des autres utilisateurs
- Pas d'accès aux données administratives

### Modérateur (`role = 'moderator'`)
- Mêmes permissions qu'un utilisateur normal
- Peut être étendu avec des permissions spéciales si nécessaire

### Administrateur (`role = 'admin'`)
- Accès complet en lecture/écriture à toutes les données
- Peut gérer tous les utilisateurs et leurs données
- Peut effectuer des opérations administratives

## Fonction d'authentification

Les politiques RLS utilisent `auth.uid()` qui retourne l'UUID de l'utilisateur authentifié via Supabase Auth. Cette fonction est automatiquement disponible dans le contexte des requêtes authentifiées.

## Tests de validation

Un script de test complet est disponible dans `backend/test_rls.sql` pour vérifier :

1. **Isolation des utilisateurs** : Chaque utilisateur ne voit que ses données
2. **Accès administrateur** : Les admins peuvent accéder à toutes les données
3. **Intégrité des relations** : Les jointures respectent les contraintes de sécurité

## Bonnes pratiques

1. **Toujours tester** : Exécuter les tests RLS après toute modification
2. **Principe du moindre privilège** : Donner uniquement les permissions nécessaires
3. **Audit régulier** : Vérifier périodiquement les politiques
4. **Documentation** : Maintenir cette documentation à jour

## Commandes utiles

```sql
-- Voir toutes les politiques RLS
SELECT schemaname, tablename, policyname, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';

-- Vérifier si RLS est activé sur une table
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Désactiver temporairement RLS pour debug (ATTENTION!)
SET row_security = off;

-- Réactiver RLS
SET row_security = on;
```

## Maintenance

- **Ajout de nouvelles tables** : Toujours activer RLS et définir des politiques appropriées
- **Modification des relations** : Vérifier que les politiques restent cohérentes
- **Nouveaux rôles** : Mettre à jour les politiques admin si nécessaire

## Sécurité

⚠️ **Important** : 
- Ne jamais désactiver RLS en production
- Tester toutes les modifications dans un environnement de développement
- Utiliser des requêtes avec `auth.uid()` pour maintenir l'isolation
- Éviter les politiques trop permissives 