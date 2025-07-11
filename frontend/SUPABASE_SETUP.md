# Configuration Supabase Cloud

## Étapes de configuration

### 1. Créer un projet Supabase Cloud

1. Allez sur [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Connectez-vous ou créez un compte
3. Cliquez sur "New project"
4. Choisissez votre organisation
5. Donnez un nom à votre projet
6. Sélectionnez une région proche de vos utilisateurs
7. Générez un mot de passe pour la base de données
8. Cliquez sur "Create new project"

### 2. Récupérer les clés de configuration

Une fois le projet créé :

1. Allez dans **Settings** → **API**
2. Copiez les valeurs suivantes :
   - **Project URL** : `https://your-project-id.supabase.co`
   - **anon public** : Clé publique pour le frontend
   - **service_role** : Clé privée pour les opérations backend

### 3. Configurer les variables d'environnement

1. Copiez le fichier `.env.example` vers `.env.local` :
   ```bash
   cp .env.example .env.local
   ```

2. Remplissez les valeurs dans `.env.local` :
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   ```

### 4. Activer l'extension pgvector

1. Dans le dashboard Supabase, allez dans **SQL Editor**
2. Exécutez la commande suivante :
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### 5. Tester la connexion

Le client Supabase est configuré dans `lib/supabase.ts`. Vous pouvez l'utiliser dans vos composants :

```typescript
import { supabase } from '@/lib/supabase'

// Exemple d'utilisation
const { data, error } = await supabase
  .from('your_table')
  .select('*')
```

## Avantages de Supabase Cloud vs Local

- ✅ Pas de problèmes de devcontainer/Docker
- ✅ pgvector déjà disponible
- ✅ Sauvegarde automatique
- ✅ Monitoring intégré
- ✅ Scalabilité automatique
- ✅ SSL/TLS configuré
- ✅ Accès depuis n'importe où

## Prochaines étapes

1. Configurer l'authentification sociale
2. Définir le schéma de base de données
3. Implémenter les politiques RLS (Row Level Security) 