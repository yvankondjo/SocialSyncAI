# 📸 Instagram API v23.0 - Multi-Tenant Setup Guide

## 🎯 **Vue d'ensemble**

Guide pour configurer les webhooks Instagram v23.0 avec architecture multi-tenant utilisant **Instagram Business Account ID** comme clé de routage.

## 🔄 **Instagram API v23.0 - Nouvelles Spécifications**

### **📱 Architecture Indépendante**

D'après la documentation Meta 2024, Instagram v23.0 fonctionne avec :

- ✅ **Instagram Business Account ID** direct (pas de page_id Facebook requis)
- ✅ **Permissions Instagram natives** : `instagram_basic`, `instagram_manage_messages`, `pages_manage_metadata`
- ✅ **Webhooks Instagram indépendants** avec routage par `account_id`

### **🔍 Structure des Webhooks**

```json
{
  "object": "instagram",
  "entry": [{
    "id": "17841444806457084",  // ← Instagram Business Account ID (clé de routage)
    "changes": [{
      "field": "messages",
      "value": {
        "messaging_product": "instagram",
        "messages": [{
          "id": "msg_instagram_123",
          "from": {"id": "instagram_user_456"},
          "text": "Salut !",
          "timestamp": "1640995200"
        }]
      }
    }]
  }]
}
```

## 🛠️ **Configuration Multi-Tenant**

### **1. Table Social Accounts**

```sql
-- Structure pour Instagram v23.0
INSERT INTO social_accounts (
    platform,
    account_id,                    -- Instagram Business Account ID (clé de routage)
    username,                      -- @mon_restaurant
    display_name,                  -- "Mon Restaurant"
    access_token,                  -- Token Instagram Business
    app_secret,                    -- App Secret Meta
    verify_token,                  -- Token de vérification webhook
    webhook_events,                -- ['messages', 'comments', 'mentions']
    webhook_status,                -- 'active'
    user_id,                       -- UUID utilisateur
    is_active
) VALUES (
    'instagram',
    '17841444806457084',           -- Instagram Business Account ID
    'mon_restaurant',
    'Mon Restaurant',
    'IGQVJYUxxxxxx...',           -- Token Instagram
    'abc123def456',               -- App Secret
    'my_instagram_verify_token',
    ARRAY['messages', 'comments', 'mentions'],
    'active',
    'user_uuid_123',
    true
);
```

### **2. Fonction de Routage SQL**

```sql
-- Routage Instagram v23.0 par account_id
SELECT * FROM get_instagram_user_by_business_account_id('17841444806457084');

-- Retourne :
{
    "user_id": "user_uuid_123",
    "social_account_id": "sa_uuid",
    "instagram_business_account_id": "17841444806457084",
    "access_token": "IGQVJYUxxxxxx...",
    "username": "mon_restaurant",
    "display_name": "Mon Restaurant"
}
```

### **3. Configuration Webhook Meta**

#### **Meta for Developers → Instagram → Webhooks**

```
Application: SocialSync
URL: https://app.com/api/instagram/webhook
Événements: ✅ messages ✅ comments ✅ mentions
Token de vérification: my_instagram_verify_token
```

## 🔧 **Permissions Instagram v23.0**

### **Permissions Requises**

```bash
# Permissions Instagram Business API v23.0
instagram_basic                 # Accès de base
instagram_manage_messages       # Messages directs
pages_manage_metadata          # Métadonnées des pages
instagram_manage_comments      # Gestion des commentaires (optionnel)
```

### **Comment obtenir les permissions**

1. **Meta for Developers** → Votre app → **Instagram Basic Display**
2. **Products** → **Instagram Basic Display** → **Permissions and Features**
3. **Demander les permissions** : `instagram_manage_messages`, `pages_manage_metadata`
4. **Mode Live** : Activer pour tous les utilisateurs (pas seulement les testeurs)

## 📊 **Flux Multi-Tenant Instagram**

### **1. Routage Automatique**

```python
# Webhook reçu
webhook_payload = {
    "entry": [{
        "id": "17841444806457084",  # Instagram Business Account ID
        "changes": [...]
    }]
}

# Routage automatique
instagram_business_account_id = entry.get("id")
user_info = await get_instagram_user_by_business_account_id(instagram_business_account_id)

# Résultat
user_info = {
    "user_id": "user_123",
    "username": "mon_restaurant",
    "instagram_business_account_id": "17841444806457084"
}
```

### **2. Traitement par Utilisateur**

```python
# Chaque utilisateur a sa logique métier
if user_info["username"] == "mon_restaurant":
    if "menu" in message_text:
        await send_restaurant_menu(sender_id, user_info)
    elif "horaires" in message_text:
        await send_opening_hours(sender_id, user_info)

# Sauvegarde automatique en BDD par utilisateur
await save_incoming_instagram_message_to_db(message, user_info)
```

## 🎯 **Types d'Événements Supportés**

### **1. Messages Directs**

```json
{
  "field": "messages",
  "value": {
    "messages": [{
      "id": "msg_123",
      "from": {"id": "user_456"},
      "text": "Bonjour !",
      "timestamp": "1640995200"
    }]
  }
}
```

**Traitement :**
- Routage par `instagram_business_account_id`
- Sauvegarde en conversations par utilisateur
- Réponses automatiques personnalisées

### **2. Commentaires**

```json
{
  "field": "comments",
  "value": {
    "comments": [{
      "id": "comment_123",
      "from": {"id": "user_456"},
      "media": {"id": "media_789"},
      "text": "Super post !",
      "timestamp": "1640995200"
    }]
  }
}
```

**Traitement :**
- Modération automatique par utilisateur
- Réponses aux commentaires positifs
- Alertes pour commentaires négatifs

### **3. Mentions dans Stories**

```json
{
  "field": "mentions",
  "value": {
    "mentions": [{
      "id": "mention_123",
      "from": {"id": "user_456"},
      "media_id": "story_789"
    }]
  }
}
```

**Traitement :**
- Notification équipe par utilisateur
- Analyse du contexte
- Stratégies de réponse personnalisées

## 🧪 **Tests Multi-Tenant**

### **Test Utilisateur A**

```bash
curl -X POST "http://localhost:8000/api/instagram/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "17841444806457084",
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "id": "msg_123",
            "from": {"id": "user_456"},
            "text": "Bonjour Mon Restaurant !"
          }]
        }
      }]
    }]
  }'
```

### **Test Utilisateur B**

```bash
curl -X POST "http://localhost:8000/api/instagram/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "17841444806457085",
      "changes": [{
        "field": "comments",
        "value": {
          "comments": [{
            "id": "comment_456",
            "from": {"id": "user_789"},
            "media": {"id": "media_123"},
            "text": "Génial ce produit !"
          }]
        }
      }]
    }]
  }'
```

## 📋 **Configuration Variables d'Environnement**

```bash
# Instagram API v23.0
INSTAGRAM_ACCESS_TOKEN=IGQVJYUxxxxxx...  # Token Business Account
INSTAGRAM_VERIFY_TOKEN=my_instagram_verify_token
META_APP_SECRET=abc123def456

# Base de données
DATABASE_URL=postgresql://user:pass@localhost:5432/socialsync
```

## 🔍 **Comment obtenir Instagram Business Account ID**

### **1. Via API Meta**

```bash
# Avec un token utilisateur, lister les comptes business
GET /me/accounts?fields=instagram_business_account
Authorization: Bearer USER_ACCESS_TOKEN

# Réponse
{
  "data": [{
    "id": "page_id_facebook",
    "instagram_business_account": {
      "id": "17841444806457084"  // ← Instagram Business Account ID
    }
  }]
}
```

### **2. Via Meta Business Suite**

1. **Meta Business Suite** → **Instagram** → **Paramètres**
2. **Informations du compte** → **ID du compte Instagram Business**
3. Copier l'ID (format : 17841444806457084)

### **3. Via l'API Instagram directement**

```bash
# Avec un token Instagram Business
GET /me?fields=id,username
Authorization: Bearer INSTAGRAM_ACCESS_TOKEN

# Réponse
{
  "id": "17841444806457084",  // ← Instagram Business Account ID
  "username": "mon_restaurant"
}
```

## 🚀 **Avantages Instagram v23.0 Multi-Tenant**

### **✅ Simplicité**
- **1 webhook unique** pour toute l'application
- **Routage direct** par `instagram_business_account_id`
- **Pas de dépendance** aux Pages Facebook

### **✅ Performance**
- **Index optimisé** sur `account_id` en BDD
- **Lookup O(1)** pour le routage
- **Isolation complète** des données

### **✅ Flexibilité**
- **Logique métier personnalisée** par utilisateur
- **Réponses automatiques** adaptées au business
- **Analytics séparées** par compte Instagram

### **✅ Monitoring**
- **Logs détaillés** par utilisateur
- **Métriques individuelles** (réponses, engagement)
- **Debug facile** avec traces par account_id

## 📊 **Monitoring et Analytics**

### **Vues SQL pour Instagram**

```sql
-- Comptes Instagram actifs
SELECT * FROM active_webhook_accounts WHERE platform = 'instagram';

-- Statistiques par utilisateur Instagram
SELECT * FROM webhook_stats_by_user WHERE platform = 'instagram';

-- Messages Instagram récents
SELECT 
    wl.*,
    sa.username,
    sa.display_name
FROM webhook_logs wl
JOIN social_accounts sa ON sa.id = wl.social_account_id
WHERE sa.platform = 'instagram'
ORDER BY wl.created_at DESC
LIMIT 20;
```

### **Métriques Instagram par Utilisateur**

- **Messages directs** reçus/traités
- **Commentaires** positifs/négatifs
- **Mentions** dans stories
- **Temps de réponse** moyen
- **Taux de résolution** automatique

## 🔧 **Dépannage Instagram v23.0**

### **Problèmes Courants**

#### **1. Webhook non reçu**
```bash
# Vérifier la configuration
curl "localhost:8000/api/instagram/webhook-info"

# Vérifier les permissions
curl -X GET "https://graph.instagram.com/v23.0/me/permissions" \
  -H "Authorization: Bearer INSTAGRAM_ACCESS_TOKEN"
```

#### **2. Utilisateur non trouvé**
```sql
-- Vérifier les comptes en BDD
SELECT account_id, username, display_name 
FROM social_accounts 
WHERE platform = 'instagram' AND is_active = true;
```

#### **3. Token expiré**
```bash
# Vérifier la validité du token
curl -X GET "https://graph.instagram.com/v23.0/me" \
  -H "Authorization: Bearer INSTAGRAM_ACCESS_TOKEN"
```

## ✅ **Checklist Instagram v23.0**

- [ ] ✅ **Permissions accordées** : `instagram_basic`, `instagram_manage_messages`, `pages_manage_metadata`
- [ ] ✅ **Webhook configuré** dans Meta for Developers
- [ ] ✅ **Token Instagram Business** valide et non expiré
- [ ] ✅ **Instagram Business Account ID** récupéré et stocké
- [ ] ✅ **Table social_accounts** mise à jour avec account_id
- [ ] ✅ **Fonction SQL** `get_instagram_user_by_business_account_id` créée
- [ ] ✅ **Test de routage** réussi avec account_id
- [ ] ✅ **Logging automatique** des webhooks fonctionnel
- [ ] ✅ **Mode Live** activé pour tous les utilisateurs

**Instagram v23.0 Multi-Tenant est maintenant opérationnel !** 🎉

La nouvelle architecture utilise directement les **Instagram Business Account IDs** pour un routage plus simple et plus fiable.
