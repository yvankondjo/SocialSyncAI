# 🔄 Guide de Migration Base de Données - Webhooks Multi-Tenant

## 📋 **Vue d'ensemble**

Ce guide vous aide à migrer votre base de données existante pour supporter l'architecture multi-tenant des webhooks WhatsApp et Instagram.

## 🛠️ **Étapes de Migration**

### **1. Sauvegarder la Base de Données**

```bash
# Sauvegarde complète
pg_dump socialsync > backup_avant_migration.sql

# Ou sauvegarde structure seulement
pg_dump --schema-only socialsync > schema_backup.sql
```

### **2. Appliquer les Modifications**

```bash
# Se connecter à votre base de données
psql -d socialsync -f schema_updates_webhooks.sql
```

### **3. Vérifier les Nouvelles Tables**

```sql
-- Vérifier les colonnes ajoutées à social_accounts
\d social_accounts

-- Vérifier la nouvelle table webhook_logs
\d webhook_logs

-- Vérifier les fonctions créées
\df get_whatsapp_user_by_phone_number_id
\df get_instagram_user_by_page_id
\df log_webhook
```

### **4. Vérifier les Index**

```sql
-- Index sur phone_number_id
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'social_accounts' 
AND indexname LIKE '%phone_number%';

-- Index sur webhook_logs
SELECT indexname FROM pg_indexes WHERE tablename = 'webhook_logs';
```

## 📊 **Migration des Données Existantes**

### **Si vous avez des comptes WhatsApp existants :**

```sql
-- Mettre à jour les comptes WhatsApp existants avec des données fictives
-- (Remplacez par vos vraies données)

UPDATE social_accounts 
SET 
    phone_number_id = '683178638221369', -- Votre vrai phone_number_id
    app_secret = 'your_app_secret_here',
    verify_token = 'your_verify_token',
    business_name = display_name,
    webhook_events = ARRAY['messages', 'message_deliveries', 'message_reads'],
    webhook_status = 'inactive'
WHERE platform IN ('whatsapp', 'whatsapp_business')
AND phone_number_id IS NULL;
```

### **Si vous avez des comptes Instagram existants :**

```sql
-- Mettre à jour les comptes Instagram existants
UPDATE social_accounts 
SET 
    page_id = 'your_page_id_here', -- Votre vrai page_id Instagram
    app_secret = 'your_app_secret_here',
    verify_token = 'your_verify_token',
    webhook_events = ARRAY['messages', 'comments', 'mentions'],
    webhook_status = 'inactive'
WHERE platform = 'instagram'
AND page_id IS NULL;
```

## 🧪 **Tester la Migration**

### **1. Tester les Fonctions de Routage**

```sql
-- Test fonction WhatsApp
SELECT * FROM get_whatsapp_user_by_phone_number_id('683178638221369');

-- Test fonction Instagram  
SELECT * FROM get_instagram_user_by_page_id('your_page_id');
```

### **2. Tester le Logging des Webhooks**

```sql
-- Test d'insertion de webhook log
SELECT log_webhook(
    (SELECT id FROM social_accounts WHERE phone_number_id = '683178638221369' LIMIT 1)::uuid,
    'whatsapp'::social_platform,
    'test_message',
    '{"test": true}'::jsonb,
    'msg_test_123',
    '33765540003'
);

-- Vérifier l'insertion
SELECT * FROM webhook_logs ORDER BY created_at DESC LIMIT 5;
```

### **3. Tester les Vues de Monitoring**

```sql
-- Comptes avec webhooks
SELECT * FROM active_webhook_accounts;

-- Statistiques par utilisateur
SELECT * FROM webhook_stats_by_user;
```

## 🔧 **Configuration des Variables d'Environnement**

Ajoutez à votre `.env` :

```bash
# Base de données (si pas déjà configuré)
DATABASE_URL=postgresql://user:password@localhost:5432/socialsync

# Ou configuration séparée
DB_HOST=localhost
DB_PORT=5432
DB_NAME=socialsync
DB_USER=postgres
DB_PASSWORD=your_password

# WhatsApp/Instagram (existants)
WHATSAPP_ACCESS_TOKEN=EAAI565Fri...
WHATSAPP_PHONE_NUMBER_ID=683178638221369
WHATSAPP_VERIFY_TOKEN=your_verify_token
META_APP_SECRET=your_app_secret

INSTAGRAM_ACCESS_TOKEN=IGQ...
INSTAGRAM_PAGE_ID=your_page_id
INSTAGRAM_VERIFY_TOKEN=your_verify_token
```

## 🚨 **Vérifications Post-Migration**

### **1. Structure des Tables**

```sql
-- Vérifier que toutes les colonnes existent
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'social_accounts' 
AND column_name IN (
    'phone_number_id', 'page_id', 'app_secret', 
    'verify_token', 'webhook_status'
);
```

### **2. Contraintes et Index**

```sql
-- Vérifier les contraintes
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'social_accounts';

-- Vérifier les index
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('social_accounts', 'webhook_logs');
```

### **3. Permissions RLS**

```sql
-- Vérifier que RLS est activé
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename IN ('social_accounts', 'webhook_logs');

-- Vérifier les politiques
SELECT schemaname, tablename, policyname, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('social_accounts', 'webhook_logs');
```

## 🔄 **Test End-to-End**

### **1. Ajouter un Utilisateur Test**

```sql
-- Insérer un utilisateur de test (ajustez selon vos données)
INSERT INTO social_accounts (
    platform,
    account_id,
    username,
    display_name,
    phone_number_id,
    access_token,
    app_secret,
    verify_token,
    business_name,
    display_phone_number,
    webhook_events,
    webhook_status,
    user_id,
    is_active
) VALUES (
    'whatsapp_business',
    'wa_test_123',
    'test_business',
    'Test Business',
    '683178638221369',
    'test_token',
    'test_app_secret',
    'test_verify_token',
    'Mon Business Test',
    '+33765540003',
    ARRAY['messages', 'message_deliveries'],
    'active',
    (SELECT id FROM users LIMIT 1), -- Premier utilisateur
    true
) ON CONFLICT (platform, account_id) DO UPDATE SET
    phone_number_id = EXCLUDED.phone_number_id,
    app_secret = EXCLUDED.app_secret,
    verify_token = EXCLUDED.verify_token;
```

### **2. Tester le Routage**

```bash
# Test API avec le nouveau système
curl -X POST "http://localhost:8000/api/whatsapp/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "683178638221369",
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "id": "msg_test_123",
            "from": "33765540003",
            "type": "text",
            "text": {"body": "Test message multi-tenant"}
          }]
        }
      }]
    }]
  }'
```

### **3. Vérifier les Logs**

```sql
-- Vérifier que le webhook a été logé
SELECT 
    wl.*,
    sa.business_name,
    u.email
FROM webhook_logs wl
JOIN social_accounts sa ON sa.id = wl.social_account_id
JOIN users u ON u.id = wl.user_id
ORDER BY wl.created_at DESC
LIMIT 10;
```

## ⚠️ **Rollback en Cas de Problème**

Si quelque chose ne fonctionne pas :

```sql
-- Supprimer les nouvelles colonnes (ATTENTION: perte de données)
ALTER TABLE social_accounts 
    DROP COLUMN IF EXISTS phone_number_id,
    DROP COLUMN IF EXISTS page_id,
    DROP COLUMN IF EXISTS app_secret,
    DROP COLUMN IF EXISTS verify_token,
    DROP COLUMN IF EXISTS webhook_url,
    DROP COLUMN IF EXISTS business_name,
    DROP COLUMN IF EXISTS display_phone_number,
    DROP COLUMN IF EXISTS webhook_events,
    DROP COLUMN IF EXISTS webhook_status,
    DROP COLUMN IF EXISTS last_webhook_at,
    DROP COLUMN IF EXISTS webhook_metadata;

-- Supprimer la table webhook_logs
DROP TABLE IF EXISTS webhook_logs;

-- Supprimer les fonctions
DROP FUNCTION IF EXISTS get_whatsapp_user_by_phone_number_id(VARCHAR);
DROP FUNCTION IF EXISTS get_instagram_user_by_page_id(VARCHAR);
DROP FUNCTION IF EXISTS log_webhook(UUID, social_platform, VARCHAR, JSONB, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS mark_webhook_processed(UUID, INTEGER, TEXT);

-- Restaurer depuis la sauvegarde
-- psql -d socialsync < backup_avant_migration.sql
```

## ✅ **Checklist Post-Migration**

- [ ] ✅ **Sauvegarde** effectuée avant migration
- [ ] ✅ **Schema updates** appliqués sans erreur
- [ ] ✅ **Nouvelles colonnes** présentes dans social_accounts
- [ ] ✅ **Table webhook_logs** créée
- [ ] ✅ **Index et contraintes** créés
- [ ] ✅ **Fonctions SQL** disponibles
- [ ] ✅ **Vues de monitoring** fonctionnelles
- [ ] ✅ **Permissions RLS** configurées
- [ ] ✅ **Variables d'environnement** mises à jour
- [ ] ✅ **Test de routage** réussi
- [ ] ✅ **API multi-tenant** fonctionnelle

**La migration est terminée ! Votre système supporte maintenant les webhooks multi-tenant.** 🎉
