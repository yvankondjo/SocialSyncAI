# 📸 Instagram Webhooks - Guide Complet

## Vue d'ensemble

Les **webhooks Instagram** permettent de recevoir en temps réel :
- ✅ **Messages directs** entrants
- ✅ **Commentaires** sur vos posts
- ✅ **Mentions** dans les stories
- ✅ **Événements du feed** (nouveaux posts, etc.)

## 🔧 Configuration

### 1. Variables d'environnement

Ajoutez à votre `.env` :

```bash
# Instagram Business API
INSTAGRAM_ACCESS_TOKEN=IGQ...
INSTAGRAM_PAGE_ID=123...

# Webhooks Instagram
INSTAGRAM_VERIFY_TOKEN=mon_token_verification_instagram
INSTAGRAM_WEBHOOK_SECRET=mon_secret_webhook_instagram
```

### 2. Configuration Meta for Developers

1. **Aller dans Meta for Developers** → Votre app → **Instagram Basic Display**
2. **Section Webhooks** :
   - **URL de callback** : `https://votre-domain.com/api/instagram/webhook`
   - **Token de vérification** : Valeur de `INSTAGRAM_VERIFY_TOKEN`
   - **Événements à souscrire** :
     - ✅ `messages` - Messages directs
     - ✅ `comments` - Commentaires
     - ✅ `mentions` - Mentions
     - ✅ `feed` - Événements feed

3. **Cliquer sur "Vérifier et enregistrer"**

## 🚀 Endpoints Disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/instagram/webhook` | GET | **Vérification du webhook** |
| `/api/instagram/webhook` | POST | **Réception des événements** |
| `/api/instagram/webhook-info` | GET | **Infos de configuration** |
| `/api/instagram/webhook-test` | POST | **Test en local** |

## 📨 Types d'événements reçus

### **1. Messages Directs**

```json
{
  "object": "instagram",
  "entry": [{
    "id": "page_id",
    "changes": [{
      "field": "messages",
      "value": {
        "messages": [{
          "id": "msg_123",
          "from": {"id": "user_id"},
          "timestamp": "1640995200",
          "text": "Bonjour !"
        }]
      }
    }]
  }]
}
```

### **2. Commentaires**

```json
{
  "object": "instagram", 
  "entry": [{
    "id": "page_id",
    "changes": [{
      "field": "comments",
      "value": {
        "comments": [{
          "id": "comment_123",
          "from": {"id": "user_id"},
          "media": {"id": "media_id"},
          "text": "Super post !",
          "timestamp": "1640995200"
        }]
      }
    }]
  }]
}
```

### **3. Mentions**

```json
{
  "object": "instagram",
  "entry": [{
    "id": "page_id", 
    "changes": [{
      "field": "mentions",
      "value": {
        "mentions": [{
          "id": "mention_123",
          "from": {"id": "user_id"},
          "media_id": "story_id"
        }]
      }
    }]
  }]
}
```

## 🤖 Réponses Automatiques

### **Messages Directs**

L'API répond automatiquement aux messages contenant :
- "hello", "salut", "bonjour", "hi"

```python
# Personnaliser dans handle_incoming_instagram_dm()
if message_text.lower() in ["hello", "salut", "bonjour"]:
    await service.send_direct_message(
        recipient_ig_id=sender_id,
        text="Bonjour ! Notre équipe vous répondra bientôt."
    )
```

### **Commentaires**

Réponse automatique aux commentaires positifs :
- "super", "génial", "merci", "love"

```python
# Personnaliser dans handle_incoming_instagram_comment()
if any(word in comment_text.lower() for word in ["super", "génial", "merci"]):
    await service.reply_to_comment(
        comment_id=comment_id,
        message="Merci beaucoup ! 😊"
    )
```

## 🧪 Tests

### **1. Vérification manuelle**

```bash
curl "http://localhost:8000/api/instagram/webhook?hub.mode=subscribe&hub.challenge=TEST123&hub.verify_token=mon_token_verification_instagram"
# Doit retourner : TEST123
```

### **2. Test message direct**

```bash
curl -X POST "http://localhost:8000/api/instagram/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "page_123",
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "id": "msg_123",
            "from": {"id": "user_456"},
            "timestamp": "1640995200",
            "text": "Bonjour !"
          }]
        }
      }]
    }]
  }'
```

### **3. Test commentaire**

```bash
curl -X POST "http://localhost:8000/api/instagram/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "page_123", 
      "changes": [{
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
      }]
    }]
  }'
```

## 🔒 Sécurité

### **Vérification des signatures**

Les webhooks Instagram sont sécurisés avec HMAC SHA256 :

```python
def verify_instagram_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature.replace('sha256=', '')
    return hmac.compare_digest(expected_signature, received_signature)
```

### **Headers de sécurité**

- `X-Hub-Signature-256` : Signature HMAC du payload
- `User-Agent` : `facebookplatform/1.0 (+http://developers.facebook.com)`

## 📊 Logique Métier

### **Personnaliser les réponses**

Modifiez les fonctions dans `instagram.py` :

```python
async def handle_incoming_instagram_dm(sender_id: str, message_text: str, message_id: str):
    # Votre logique personnalisée
    if "prix" in message_text.lower():
        await service.send_direct_message(
            recipient_ig_id=sender_id,
            text="Consultez nos tarifs sur notre site web : https://example.com/prix"
        )
    
    # Sauvegarder en BDD
    # await save_instagram_message_to_db(sender_id, message_text, message_id)
    
    # Notifier l'équipe
    # await notify_team_new_instagram_dm(sender_id, message_text)
```

### **Modération des commentaires**

```python
async def handle_incoming_instagram_comment(commenter_id: str, comment_text: str, comment_id: str, media_id: str):
    # Analyse du sentiment
    sentiment = analyze_sentiment(comment_text)
    
    if sentiment == "negative":
        # Alerter l'équipe de modération
        await alert_moderation_team(comment_id, comment_text)
    
    elif sentiment == "positive":
        # Répondre positivement
        await service.reply_to_comment(comment_id, "Merci pour votre retour ! 😊")
```

## 🎯 Cas d'Usage

### **Support Client**
- ✅ Réponses automatiques aux DM
- ✅ Escalade vers agents humains
- ✅ Collecte d'informations client

### **Community Management**
- ✅ Modération automatique des commentaires
- ✅ Réponses aux mentions positives
- ✅ Gestion de la réputation

### **Marketing**
- ✅ Engagement automatique
- ✅ Lead generation via DM
- ✅ Suivi des performances

### **E-commerce**
- ✅ Support produits via commentaires
- ✅ Gestion des réclamations
- ✅ Promotion des nouveautés

## 🌐 Exposition avec ngrok

Pour tester en local :

```bash
# Installer ngrok
npm install -g ngrok

# Exposer le port 8000
ngrok http 8000

# Utiliser l'URL HTTPS générée dans Meta for Developers
# Exemple : https://abc123.ngrok.io/api/instagram/webhook
```

## 📋 Checklist de configuration

- [ ] ✅ **Variables d'environnement** configurées
- [ ] ✅ **Webhook URL** configurée dans Meta
- [ ] ✅ **Token de vérification** configuré
- [ ] ✅ **Événements souscrits** (messages, comments, mentions)
- [ ] ✅ **Test de vérification** réussi
- [ ] ✅ **Test d'événements** fonctionnel
- [ ] ✅ **Réponses automatiques** personnalisées
- [ ] ✅ **Logique métier** implémentée

## 🔧 Dépannage

### **Webhook non vérifié**
- Vérifiez `INSTAGRAM_VERIFY_TOKEN` dans `.env`
- Vérifiez que l'URL est accessible publiquement
- Consultez les logs pour voir les erreurs

### **Événements non reçus**
- Vérifiez les permissions Instagram requises
- Vérifiez que les événements sont bien souscrits
- Testez avec l'endpoint `/webhook-test`

### **Signatures invalides**
- Vérifiez `INSTAGRAM_WEBHOOK_SECRET`
- Assurez-vous que le secret correspond à celui configuré dans Meta

**Les webhooks Instagram sont maintenant opérationnels !** 🎉
