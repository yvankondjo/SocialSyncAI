# SOP: Créer des Données de Test (Seeding)

**Version**: 3.0 (Open-Source)
**Dernière mise à jour**: 2025-10-29

## Objectif

Cette procédure explique comment créer rapidement des utilisateurs et comptes sociaux de test pour développer et tester SocialSync AI.

## Prérequis

1. **Projet Supabase actif**
   - URL du projet
   - Service role key (⚠️ NE JAMAIS COMMIT)

2. **Backend installé**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Variables d'environnement**
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Procédure

### Étape 1: Configuration Supabase

```bash
# Récupérer les credentials depuis Supabase Dashboard
# Settings > API

export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGc..."
```

⚠️ **Sécurité**: La service role key a accès ADMIN complet. Ne la partagez jamais.

### Étape 2: Créer des Utilisateurs

```bash
python scripts/seed_users.py
```

**Ce que fait le script:**
1. Se connecte à Supabase avec service key
2. Créé 2 utilisateurs via `admin.create_user()`:
   - `demo@socialsync.ai` / `Demo123456!`
   - `test@socialsync.ai` / `Test123456!`
3. Confirme les emails automatiquement
4. Créé des enregistrements `user_credits` avec 999999 crédits
5. Affiche les credentials de connexion

**Output attendu:**
```
======================================================================
  SOCIALSYNC AI - SEED USERS (Open-Source)
======================================================================

📡 Connexion à Supabase...
✅ Connecté à Supabase

👤 Création des utilisateurs de test...

✅ Utilisateur créé: demo@socialsync.ai (ID: abc-123-def)
   ✅ Crédits créés (illimités)

✅ Utilisateur créé: test@socialsync.ai (ID: xyz-456-uvw)
   ✅ Crédits créés (illimités)

======================================================================
  RÉSUMÉ
======================================================================
✅ 2 utilisateur(s) créé(s)/vérifié(s)

📝 Credentials de connexion:

  • Email: demo@socialsync.ai
    Password: Demo123456!
    User ID: abc-123-def

  • Email: test@socialsync.ai
    Password: Test123456!
    User ID: xyz-456-uvw
```

### Étape 3: Créer des Comptes Sociaux

```bash
python scripts/seed_social_accounts.py
```

**Interaction:**
```
📧 Email de l'utilisateur (demo@socialsync.ai): [Entrée ou taper email]
```

**Ce que fait le script:**
1. Demande l'email de l'utilisateur
2. Récupère le `user_id` depuis Supabase Auth
3. Créé 2 comptes sociaux fictifs:
   - Instagram: `demo_instagram`
   - WhatsApp: `+1234567890`
4. Tokens marqués avec `is_test_account: true`

**Output attendu:**
```
======================================================================
  SOCIALSYNC AI - SEED SOCIAL ACCOUNTS (Open-Source)
======================================================================

📧 Email de l'utilisateur (demo@socialsync.ai): demo@socialsync.ai

📡 Connexion à Supabase...
✅ Connecté à Supabase

🔍 Recherche de l'utilisateur: demo@socialsync.ai
✅ Utilisateur trouvé (ID: abc-123-def)

📱 Création des comptes sociaux...

Création compte INSTAGRAM...
   ✅ Compte instagram créé (ID: ig-001)

Création compte WHATSAPP...
   ✅ Compte whatsapp créé (ID: wa-002)

======================================================================
  RÉSUMÉ
======================================================================
✅ 2 compte(s) social créé(s)

📱 Comptes créés:
  • INSTAGRAM: demo_instagram
  • WHATSAPP: +1234567890

⚠️  IMPORTANT:
  Ces comptes utilisent des tokens FICTIFS et ne fonctionneront pas
  avec les vraies APIs (Instagram, WhatsApp).
```

### Étape 4: Se Connecter

1. Lancez l'application:
   ```bash
   docker-compose up -d
   ```

2. Ouvrez le dashboard:
   ```
   http://localhost:3000
   ```

3. Connectez-vous avec:
   - Email: `demo@socialsync.ai`
   - Password: `Demo123456!`

### Étape 5: (Optionnel) Connecter de Vrais Comptes

Les tokens de seed sont fictifs. Pour utiliser de vrais comptes:

**Via Dashboard:**
1. Dashboard > Paramètres > Comptes Sociaux
2. Cliquez "Connecter Instagram" ou "Connecter WhatsApp"
3. Suivez le flow OAuth
4. Le vrai token remplace le token fictif

**Via Supabase directement:**
1. Supabase Dashboard > Table Editor > `social_accounts`
2. Trouvez votre compte test
3. Mettez à jour `access_token` avec un vrai token
4. Mettez à jour `platform_user_id` avec votre ID réel

## Personnalisation

### Modifier les Utilisateurs de Test

Éditez `scripts/seed_users.py`:

```python
TEST_USERS = [
    {
        "email": "mon-email@example.com",
        "password": "MonMotDePasse123!",
        "full_name": "Mon Nom",
        "username": "mon_username"
    },
    # Ajoutez plus d'utilisateurs ici
]
```

### Modifier les Comptes Sociaux de Test

Éditez `scripts/seed_social_accounts.py`:

```python
TEST_SOCIAL_ACCOUNTS = [
    {
        "platform": "instagram",
        "platform_user_id": "mon_id_instagram",
        "username": "mon_compte_ig",
        "display_name": "Mon Compte Instagram",
        "profile_picture_url": "https://...",
        "access_token": "FAKE_TOKEN_FOR_TESTING",
        "is_active": True
    },
    # Ajoutez plus de comptes ici
]
```

## Dépannage

### Erreur: "SUPABASE_URL not configured"

```bash
# Assurez-vous d'avoir exporté les variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-key"

# Vérifiez qu'elles sont bien définies
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_ROLE_KEY
```

### Erreur: "User already exists"

C'est normal ! Le script détecte les utilisateurs existants et ne les recréé pas. Il affichera:
```
⚠️  Utilisateur existe déjà: demo@socialsync.ai
```

Le script récupère alors le `user_id` existant et continue.

### Erreur: "Table 'user_credits' does not exist"

Vous devez exécuter les migrations Supabase d'abord:

```bash
cd supabase
supabase db push
```

Ou si vous utilisez un projet Supabase hébergé, exécutez les migrations via le Dashboard SQL Editor.

### Erreur: "Permission denied"

Vous utilisez probablement la **anon key** au lieu de la **service_role key**.

- ❌ Anon key: Accès utilisateur normal avec RLS
- ✅ Service role key: Accès admin complet (bypass RLS)

Récupérez la bonne clé:
1. Supabase Dashboard > Settings > API
2. Copiez "service_role" secret (pas "anon" public)

### Erreur: "Invalid login credentials"

Lors de la connexion au dashboard, vérifiez:
1. Utilisez le bon email/password du seed
2. L'utilisateur a bien été créé (check Supabase Auth)
3. Supabase URL est correct dans `frontend/.env.local`

## Nettoyage des Données

Pour supprimer toutes les données de test:

```sql
-- Dans Supabase SQL Editor
-- Supprimer les comptes sociaux de test
DELETE FROM social_accounts WHERE metadata->>'is_test_account' = 'true';

-- Supprimer les crédits des users de test
DELETE FROM user_credits WHERE user_id IN (
  SELECT id FROM auth.users WHERE email LIKE '%@socialsync.ai'
);

-- Supprimer les users de test (via Supabase Dashboard)
-- Authentication > Users > Sélectionnez les users > Delete
```

⚠️ **Attention**: Ces commandes sont irréversibles.

## Script Alternative: Reset Complet

Créez `scripts/reset_test_data.py`:

```python
#!/usr/bin/env python3
import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Supprimer comptes sociaux de test
result = supabase.table('social_accounts').delete().match({
    'metadata': {'is_test_account': True}
}).execute()

print(f"✅ {len(result.data)} comptes sociaux supprimés")

# Lister les users de test
users = supabase.auth.admin.list_users()
test_users = [u for u in users if '@socialsync.ai' in u.email]

for user in test_users:
    supabase.auth.admin.delete_user(user.id)
    print(f"✅ User supprimé: {user.email}")
```

Utilisation:
```bash
python scripts/reset_test_data.py
```

## Best Practices

### 1. Ne Jamais Commit les Clés

```bash
# .gitignore doit contenir:
.env
.env.local
*.key
```

### 2. Utilisez des Emails Distincts

- Dev: `dev@socialsync.ai`
- Staging: `staging@socialsync.ai`
- Test: `test@socialsync.ai`

### 3. Documentez vos Users de Test

Créez `test_users.md` (local, pas committé):
```markdown
# Users de Test

## Dev
- Email: dev@socialsync.ai
- Password: DevPass123!
- IG Account: @dev_instagram

## Staging
- Email: staging@socialsync.ai
- Password: StagingPass123!
```

### 4. Rotation des Tokens

Les tokens de test expirent. Pour les renouveler:
1. Reconnectez via OAuth dans le dashboard
2. Ou mettez à jour manuellement dans Supabase

## Cas d'Usage

### Développement Local

```bash
# 1. Seed une fois
python scripts/seed_users.py
python scripts/seed_social_accounts.py

# 2. Développez normalement
# 3. Si vous réinitialisez Supabase, re-seed
```

### Tests Automatisés

```python
# tests/conftest.py
import pytest
from supabase import create_client

@pytest.fixture(scope="session")
def test_user():
    """Créé un user de test pour toute la session"""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    result = supabase.auth.admin.create_user({
        "email": "pytest@socialsync.ai",
        "password": "Pytest123!",
        "email_confirm": True
    })

    yield result.user

    # Cleanup
    supabase.auth.admin.delete_user(result.user.id)
```

### Démos & Présentations

```bash
# Préparer des données démo propres
python scripts/seed_users.py
python scripts/seed_demo_conversations.py  # À créer
python scripts/seed_demo_posts.py          # À créer
```

## Ressources

**Documentation complète:**
- `/workspace/SEEDING.md` - Guide utilisateur complet
- `.agent/System/OPENSOURCE_TRANSFORMATION.md` - Contexte transformation open-source

**Scripts:**
- `scripts/seed_users.py` - Création utilisateurs
- `scripts/seed_social_accounts.py` - Création comptes sociaux

**Supabase:**
- [Supabase Admin API](https://supabase.com/docs/reference/javascript/admin-api)
- [Auth Users Management](https://supabase.com/docs/guides/auth/managing-user-data)

## Related Documentation

- `.agent/README.md` - Index documentation
- `.agent/System/OPENSOURCE_TRANSFORMATION.md` - Transformation open-source V3.0
- `.agent/System/DATABASE_SCHEMA.md` - Schéma de la base de données
- `.agent/SOP/ADD_MIGRATION.md` - Comment ajouter des migrations

---

**Version**: 3.0 (Open-Source)
**Dernière mise à jour**: 2025-10-29
