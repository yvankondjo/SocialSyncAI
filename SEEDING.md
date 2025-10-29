# Guide de Seeding - SocialSync AI (Open-Source)

Ce guide explique comment créer des données de test pour démarrer rapidement avec SocialSync AI.

## Prérequis

1. **Supabase configuré** : Votre instance Supabase doit être active
2. **Variables d'environnement** : Configurez vos credentials Supabase
3. **Python 3.8+** : Installé sur votre machine
4. **Dépendances** : Installez les dépendances Python

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Avant d'exécuter les scripts, configurez vos variables d'environnement :

```bash
# Exportez vos credentials Supabase
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
```

**Où trouver ces informations ?**

1. Connectez-vous à [supabase.com](https://supabase.com)
2. Ouvrez votre projet
3. Allez dans **Settings > API**
4. Copiez :
   - **Project URL** → `SUPABASE_URL`
   - **service_role secret** → `SUPABASE_SERVICE_ROLE_KEY` ⚠️ Ne partagez JAMAIS cette clé

## Étape 1 : Créer des utilisateurs de test

Le script `seed_users.py` crée des utilisateurs de test avec des crédits illimités.

```bash
python scripts/seed_users.py
```

**Ce que fait le script :**
- ✅ Créé 2 utilisateurs de test (demo@socialsync.ai, test@socialsync.ai)
- ✅ Configure des crédits illimités (999999)
- ✅ Confirme automatiquement les emails
- ✅ Affiche les credentials de connexion

**Output attendu :**
```
======================================================================
  SOCIALSYNC AI - SEED USERS (Open-Source)
======================================================================

✅ Utilisateur créé: demo@socialsync.ai (ID: abc-123-def)
   ✅ Crédits créés (illimités)

📝 Credentials de connexion:
  • Email: demo@socialsync.ai
    Password: Demo123456!
    User ID: abc-123-def
```

## Étape 2 : Créer des comptes sociaux de test

Le script `seed_social_accounts.py` créé des comptes Instagram et WhatsApp fictifs.

```bash
python scripts/seed_social_accounts.py
```

**Utilisation interactive :**
```
📧 Email de l'utilisateur (demo@socialsync.ai): [Entrée]
```

**Ce que fait le script :**
- ✅ Créé un compte Instagram de test
- ✅ Créé un compte WhatsApp de test
- ⚠️ Utilise des tokens FICTIFS (ne fonctionnent pas avec les vraies APIs)

**Output attendu :**
```
======================================================================
  SOCIALSYNC AI - SEED SOCIAL ACCOUNTS (Open-Source)
======================================================================

✅ Utilisateur trouvé (ID: abc-123-def)

Création compte INSTAGRAM...
   ✅ Compte instagram créé (ID: xyz-456-uvw)

📱 Comptes créés:
  • INSTAGRAM: demo_instagram
  • WHATSAPP: +1234567890
```

## Personnalisation

### Modifier les utilisateurs de test

Éditez le fichier `scripts/seed_users.py` :

```python
TEST_USERS = [
    {
        "email": "votre-email@example.com",
        "password": "VotreMotDePasse123!",
        "full_name": "Votre Nom",
        "username": "votre_username"
    }
]
```

### Modifier les comptes sociaux de test

Éditez le fichier `scripts/seed_social_accounts.py` :

```python
TEST_SOCIAL_ACCOUNTS = [
    {
        "platform": "instagram",
        "username": "votre_compte_ig",
        "display_name": "Votre Compte Instagram",
        # ...
    }
]
```

## Utilisation avec de VRAIS comptes sociaux

Les scripts de seed créent des comptes avec des **tokens fictifs**. Pour utiliser de vrais comptes :

### Option 1 : Via le Dashboard (Recommandé)

1. Lancez l'application : `docker-compose up`
2. Ouvrez [http://localhost:3000](http://localhost:3000)
3. Connectez-vous avec les credentials de seed
4. Allez dans **Paramètres > Comptes Sociaux**
5. Cliquez sur "Connecter Instagram" ou "Connecter WhatsApp"
6. Suivez le flow OAuth

### Option 2 : Manuellement dans Supabase

1. Ouvrez votre dashboard Supabase
2. Allez dans **Table Editor > social_accounts**
3. Créez un nouvel enregistrement avec :
   - `user_id` : Votre user ID
   - `platform` : "instagram" ou "whatsapp"
   - `access_token` : Votre vrai token d'accès
   - `platform_user_id` : ID de votre compte
   - Autres champs requis

## Dépannage

### Erreur : "SUPABASE_URL not configured"

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
```

### Erreur : "User already exists"

C'est normal ! Le script détecte les utilisateurs existants et ne les recréé pas.

### Erreur : "Table 'social_accounts' does not exist"

Exécutez d'abord les migrations Supabase :

```bash
cd supabase
supabase db push
```

### Erreur : "Permission denied"

Assurez-vous d'utiliser la **service_role key** (pas la clé anon).

## Sécurité

⚠️ **IMPORTANT :**

- **NE COMMITTEZ JAMAIS** vos vraies clés Supabase dans Git
- **NE PARTAGEZ JAMAIS** votre `SUPABASE_SERVICE_ROLE_KEY`
- Les tokens de test sont marqués comme `is_test_account: true`
- En production, utilisez de vrais tokens OAuth

## Nettoyage

Pour supprimer toutes les données de test :

```sql
-- Dans le SQL Editor de Supabase
DELETE FROM social_accounts WHERE metadata->>'is_test_account' = 'true';
DELETE FROM user_credits WHERE user_id IN (
  SELECT id FROM auth.users WHERE email LIKE '%@socialsync.ai'
);
```

## Prochaines étapes

Après avoir seedé vos données :

1. ✅ Lancez l'application : `docker-compose up`
2. ✅ Ouvrez le dashboard : [http://localhost:3000](http://localhost:3000)
3. ✅ Connectez-vous avec les credentials de seed
4. ✅ Explorez les fonctionnalités !

## Support

Pour toute question :
- 📖 Lisez le [README.md](README.md)
- 🐛 Ouvrez une issue sur GitHub
- 💬 Rejoignez notre communauté

---

**Version Open-Source** • Crédits illimités • Licence AGPL v3
