# 🏢 Architecture Multi-Tenant pour les Webhooks WhatsApp

## 🎯 **Le Problème à Résoudre**

**Question :** Comment gérer les webhooks WhatsApp pour plusieurs utilisateurs ?

**Réalité Meta :** Meta for Developers ne permet **PAS** de configurer des webhooks distincts par utilisateur. Il n'y a qu'**1 webhook par application** dans toute la plateforme Meta.

## ✅ **Solution Correcte : Routage Interne**

### **📋 Architecture Recommandée**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Meta for Developers                          │
│                                                                 │
│  Application "SocialSync"                                       │
│  ├─ 1 Webhook URL : https://app.com/api/whatsapp/webhook       │
│  ├─ Événements : messages, deliveries, reads                   │
│  └─ App Secret : abc123...                                     │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                            Webhook Unique
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Notre API (Routeur)                         │
│                                                                 │
│  Router interne basé sur phone_number_id :                     │
│                                                                 │
│  ├─ phone_number_id: 123 → User A                             │
│  ├─ phone_number_id: 456 → User B                             │
│  └─ phone_number_id: 789 → User C                             │
└─────────────────────────────────────────────────────────────────┘
```

### **🔍 Comment ça marche ?**

#### **1. Identification via phone_number_id**

Chaque webhook contient le `phone_number_id` de l'utilisateur :

```json
{
  "entry": [{
    "id": "683178638221369",  // ← phone_number_id unique
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "phone_number_id": "683178638221369"  // ← Clé de routage
        },
        "messages": [{
          "id": "msg_123",
          "from": "33765540003", 
          "text": {"body": "Bonjour !"}
        }]
      }
    }]
  }]
}
```

#### **2. Table de Mapping Utilisateurs**

```sql
CREATE TABLE user_whatsapp_accounts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,                    -- ID de l'utilisateur dans notre système
    phone_number_id VARCHAR(50) UNIQUE NOT NULL,  -- Clé Meta (unique)
    access_token TEXT NOT NULL,               -- Token WhatsApp de l'utilisateur
    app_secret TEXT NOT NULL,                 -- App Secret Meta de l'utilisateur
    verify_token VARCHAR(100) NOT NULL,       -- Token de vérification
    display_phone_number VARCHAR(20),         -- Numéro affiché (+33...)
    business_name VARCHAR(255),               -- Nom de l'entreprise
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index pour le routage rapide
CREATE INDEX idx_phone_number_id ON user_whatsapp_accounts(phone_number_id);
```

#### **3. Processus de Routage**

```python
# 1. Webhook reçu avec phone_number_id
phone_number_id = entry.get("id")  # "683178638221369"

# 2. Lookup utilisateur en BDD
user_info = await get_user_by_phone_number_id(phone_number_id)

# 3. Router vers les fonctions spécifiques à l'utilisateur
await process_webhook_change_for_user(change, user_info)
```

## 🛠️ **Implémentation Technique**

### **1. Configuration Meta for Developers**

#### **Une seule configuration pour toute l'app :**

```
Application : SocialSync
Webhook URL : https://votre-domain.com/api/whatsapp/webhook
Verify Token : global_verify_token_unique
App Secret : abc123def456 (utilisé pour tous les utilisateurs)

Événements activés :
✅ messages
✅ message_deliveries  
✅ message_reads
```

### **2. Gestion Multi-Utilisateurs**

#### **Chaque utilisateur a ses propres credentials :**

```json
{
  "user_id": "user_123",
  "phone_number_id": "683178638221369",  // Clé unique Meta
  "access_token": "EAAI565Fri...",       // Token personnel
  "app_secret": "abc123...",             // App Secret (même pour tous)
  "display_phone_number": "+33765540003",
  "business_name": "Restaurant Chez Pierre"
}
```

### **3. Flux de Traitement**

```python
# Webhook reçu
async def webhook_handler(request: Request):
    payload = await request.body()
    webhook_data = await request.json()
    
    # Traiter chaque entrée
    for entry in webhook_data.get("entry", []):
        # Identifier l'utilisateur
        phone_number_id = entry.get("id")
        user_info = await get_user_by_phone_number_id(phone_number_id)
        
        if user_info:
            # Router vers l'utilisateur spécifique
            await process_webhook_entry_for_user(entry, user_info)
        else:
            logger.warning(f"Utilisateur non trouvé: {phone_number_id}")
```

## 📊 **Avantages de cette Architecture**

### ✅ **Avantages**
- **1 seul webhook** à configurer dans Meta
- **Isolation complète** des données par utilisateur
- **Scalabilité** illimitée en ajoutant des utilisateurs
- **Debugging facile** avec logs par utilisateur
- **Sécurité** : chaque utilisateur a ses propres credentials
- **Flexibilité** : logique métier personnalisée par utilisateur

### ⚠️ **Considérations**
- **Point unique de défaillance** (mais avec monitoring approprié)
- **Complexité du routage** (mais gérable avec une bonne architecture)
- **Performance** : nécessite une lookup en BDD par webhook

## 🔧 **Configuration par Utilisateur**

### **1. Onboarding d'un Nouvel Utilisateur**

```python
async def add_new_whatsapp_user(
    user_id: str,
    phone_number_id: str,
    access_token: str,
    display_phone_number: str,
    business_name: str
):
    """Ajouter un nouvel utilisateur WhatsApp"""
    
    user_data = {
        "user_id": user_id,
        "phone_number_id": phone_number_id,
        "access_token": access_token,
        "app_secret": os.getenv("META_APP_SECRET"),  # Même pour tous
        "verify_token": os.getenv("WHATSAPP_VERIFY_TOKEN"),  # Même pour tous
        "display_phone_number": display_phone_number,
        "business_name": business_name,
        "status": "active"
    }
    
    # Sauvegarder en BDD
    await save_user_whatsapp_account(user_data)
    
    # Le webhook est déjà configuré globalement dans Meta
    # Aucune configuration supplémentaire nécessaire !
```

### **2. Logique Métier par Utilisateur**

```python
async def handle_text_message_for_user(sender_phone: str, text: str, user_info: dict):
    """Logique personnalisée par utilisateur"""
    
    user_id = user_info["user_id"]
    business_name = user_info["business_name"]
    
    # Réponse automatique personnalisée
    if "horaires" in text.lower():
        await send_business_hours_response(sender_phone, user_info)
    
    elif "prix" in text.lower():
        await send_pricing_info(sender_phone, user_info)
    
    # Sauvegarder dans le CRM de l'utilisateur
    await save_to_user_crm(sender_phone, text, user_info)
    
    # Notifier l'équipe de l'utilisateur
    await notify_user_team(sender_phone, text, user_info)
```

## 🧪 **Tests Multi-Utilisateurs**

### **Test avec Utilisateurs Fictifs**

```bash
# Test User A
curl -X POST "http://localhost:8000/api/whatsapp/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "683178638221369",  
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "id": "msg_123",
            "from": "33765540003",
            "text": {"body": "Bonjour User A !"}
          }]
        }
      }]
    }]
  }'

# Test User B  
curl -X POST "http://localhost:8000/api/whatsapp/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "456789012345678",  
      "changes": [{
        "field": "messages", 
        "value": {
          "messages": [{
            "id": "msg_456",
            "from": "33612345678",
            "text": {"body": "Salut User B !"}
          }]
        }
      }]
    }]
  }'
```

## 🚀 **Déploiement et Monitoring**

### **1. Métriques Important**

- **Taux de routage réussi** (webhooks correctement acheminés)
- **Utilisateurs actifs** par phone_number_id
- **Latence de traitement** par utilisateur
- **Erreurs de routage** (utilisateurs non trouvés)

### **2. Alertes Recommandées**

```python
# Alertes importantes
- Webhook reçu pour phone_number_id non reconnu
- Échec de traitement pour un utilisateur spécifique  
- Latence élevée dans le routage
- Taux d'erreur élevé pour un utilisateur
```

## 📋 **Checklist de Mise en Place**

- [ ] ✅ **1 webhook configuré** dans Meta for Developers
- [ ] ✅ **Table user_whatsapp_accounts** créée en BDD
- [ ] ✅ **Fonction de routage** `get_user_by_phone_number_id()`
- [ ] ✅ **Traitement par utilisateur** implémenté
- [ ] ✅ **Logs séparés** par utilisateur
- [ ] ✅ **Tests multi-utilisateurs** fonctionnels
- [ ] ✅ **Monitoring** et alertes en place
- [ ] ✅ **Documentation** pour l'onboarding

**L'architecture multi-tenant est maintenant opérationnelle !** 🎉

Cette approche respecte les contraintes de Meta tout en offrant une isolation complète par utilisateur.
