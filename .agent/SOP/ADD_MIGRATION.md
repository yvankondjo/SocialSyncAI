# SOP: Ajouter une Migration Supabase

## Prérequis
- Supabase CLI installé (`npm install -g supabase`)
- Projet lié: `supabase link --project-ref <REF>`
- Base de données locale running (optionnel pour tests)

## Étapes

### 1. Créer le fichier de migration

```bash
cd /workspace
supabase migration new <description>
```

**Exemple**:
```bash
supabase migration new add_scheduled_posts_table
```

Cela crée: `supabase/migrations/YYYYMMDDHHMMSS_add_scheduled_posts_table.sql`

---

### 2. Écrire le SQL

Éditer le fichier créé:

```sql
-- Créer la table
CREATE TABLE public.scheduled_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES public.social_accounts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    content_json JSONB NOT NULL,
    publish_at TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'queued',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Créer les index
CREATE INDEX idx_scheduled_posts_publish ON public.scheduled_posts(publish_at, status)
    WHERE status IN ('queued', 'publishing');

CREATE INDEX idx_scheduled_posts_user ON public.scheduled_posts(user_id, created_at DESC);

-- Activer Row Level Security
ALTER TABLE public.scheduled_posts ENABLE ROW LEVEL SECURITY;

-- Policies RLS
CREATE POLICY "Users can view own scheduled_posts"
    ON public.scheduled_posts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scheduled_posts"
    ON public.scheduled_posts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scheduled_posts"
    ON public.scheduled_posts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own scheduled_posts"
    ON public.scheduled_posts FOR DELETE
    USING (auth.uid() = user_id);
```

---

### 3. Tester localement (optionnel)

```bash
# Démarrer Supabase local
supabase start

# Appliquer migrations
supabase db reset

# Vérifier que tout fonctionne
supabase db diff
```

---

### 4. Appliquer en remote

```bash
# Push la migration vers Supabase cloud
supabase db push

# OU avec confirmation
supabase db push --dry-run  # Preview
supabase db push
```

---

### 5. Vérifier la migration

```bash
# Lister les migrations appliquées
supabase migration list

# Vérifier la table dans Supabase Dashboard
# https://supabase.com/dashboard/project/<REF>/editor
```

---

## Bonnes pratiques

### ✅ DO
- Toujours utiliser `IF NOT EXISTS` pour idempotence
- Activer RLS sur toutes les tables utilisateur
- Créer des index sur colonnes fréquentes (user_id, created_at, status)
- Utiliser `ON DELETE CASCADE` pour foreign keys si approprié
- Documenter les changements complexes avec commentaires SQL

### ❌ DON'T
- Ne jamais modifier une migration déjà appliquée en production
- Ne pas oublier les policies RLS (sécurité critique)
- Éviter les migrations destructrices sans backup (DROP TABLE, etc.)
- Ne pas créer trop d'index (impact performance write)

---

## Rollback

Si une migration échoue:

```bash
# Méthode 1: Créer une migration de rollback
supabase migration new rollback_add_scheduled_posts_table

# Dans le fichier, écrire l'inverse
DROP TABLE IF EXISTS public.scheduled_posts;

# Appliquer
supabase db push
```

**Méthode 2**: Restaurer depuis un snapshot Supabase (Dashboard)

---

## Checklist

- [ ] Fichier migration créé avec nom descriptif
- [ ] SQL écrit et testé
- [ ] RLS activé + policies créées
- [ ] Index ajoutés sur colonnes fréquentes
- [ ] Migration testée localement
- [ ] Migration appliquée en remote
- [ ] Tables visibles dans Supabase Dashboard
- [ ] Backend mis à jour (schemas Pydantic si nécessaire)
- [ ] Frontend TypeScript types mis à jour

---

## Exemple complet

```bash
# 1. Créer migration
supabase migration new add_ai_rules_table

# 2. Éditer supabase/migrations/XXXXXX_add_ai_rules_table.sql
# (SQL comme ci-dessus)

# 3. Appliquer
supabase db push

# 4. Vérifier
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ai_rules;"
```

---

## Ressources

- [Supabase Migrations Docs](https://supabase.com/docs/guides/cli/managing-migrations)
- [PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)

---
*SOP créé: 2025-10-18*
