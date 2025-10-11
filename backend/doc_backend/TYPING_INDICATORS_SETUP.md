# Indicateurs de Frappe et Marquage comme Lu

Ce document explique l'implémentation des indicateurs de frappe (typing indicators) et du marquage comme lu pour WhatsApp et Instagram.

## 📱 WhatsApp Business API

### ✅ Fonctionnalités Supportées

**Indicateur de Frappe :**
- ✅ **SUPPORTÉ** par l'API WhatsApp Cloud
- ✅ Utilise `"typing_indicator": {"type": "text"}` (pas `"type": "typing"`)
- ✅ Combiné avec `"status": "read"` en un seul appel
- ✅ S'affiche automatiquement pendant ~25 secondes

**Marquage comme Lu :**
- ✅ Supporté via l'API WhatsApp Business
- ✅ Marque les messages comme lus côté destinataire
- ✅ Fonctionne avec `"status": "read"`

### 🔧 Implémentation

```python
# Indicateur de frappe + Marquage comme lu (EN UN SEUL APPEL)
await service.send_typing_indicator(contact_id, message_id)
# ✅ Fonctionne avec la bonne API : typing_indicator + status: "read"
```

### 📋 Webhook WhatsApp

Le webhook WhatsApp reçoit les messages entrants avec :
```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "id": "wamid.xxx",
          "from": "33612345678",
          "type": "text",
          "text": {"body": "Hello"}
        }]
      }
    }]
  }]
}
```

**Traitement automatique :**
1. Réception du message via webhook
2. Marquage automatique comme lu
3. Envoi de l'indicateur de frappe
4. Traitement du message
5. Envoi de la réponse

## 📸 Instagram Messaging API

### ✅ Fonctionnalités Supportées

**Indicateur de Frappe :**
- ✅ **SUPPORTÉ** par l'API Instagram Messaging avec Instagram Login
- ✅ Utilise `"sender_action": "typing_on"` et `"typing_off"`
- ✅ Combiné avec `"mark_seen"` pour marquer comme lu
- ✅ Fonctionne avec le même endpoint `/PAGE-ID/messages`

**Marquage comme Lu :**
- ✅ Supporté via `"sender_action": "mark_seen"`
- ✅ Marque les messages comme lus côté destinataire
- ✅ Utilise l'API Instagram Messaging

### 🔧 Implémentation

```python
# Indicateur de frappe + Marquage comme lu (EN UN SEUL APPEL OPTIMISÉ)
result = await service.send_typing_and_mark_read(contact_id, message_id)
# Retourne: {'success': True, 'results': {'typing': {...}, 'mark_seen': {...}}}
```

**Méthode optimisée pour Instagram :**
```python
async def send_typing_and_mark_read(self, recipient_ig_id: str, last_message_id: str):
    # Envoi typing_on puis mark_seen en séquence optimisée
    typing_result = await self.send_typing_indicator(recipient_ig_id, "typing_on")
    seen_result = await self.send_typing_indicator(recipient_ig_id, "mark_seen")
    return {'success': typing_result['success'] or seen_result['success'], ...}
```

### 📋 Webhook Instagram

Le webhook Instagram reçoit les messages directs avec :
```json
{
  "entry": [{
    "id": "instagram_business_account_id",
    "changes": [{
      "field": "messages",
      "value": {
        "messages": [{
          "id": "msg_xxx",
          "from": {"id": "user_id"},
          "text": "Hello",
          "timestamp": "1640995200"
        }]
      }
    }]
  }]
}
```

**Traitement automatique :**
1. Réception du message via webhook
2. Marquage automatique comme lu (`mark_seen`)
3. Envoi de l'indicateur de frappe (`typing_on`)
4. Traitement du message par l'IA
5. Arrêt de l'indicateur (`typing_off`) - automatique ou manuel
6. Envoi de la réponse

### 📋 Webhook Instagram

Le webhook Instagram reçoit les messages directs avec :
```json
{
  "entry": [{
    "id": "instagram_business_account_id",
    "changes": [{
      "field": "messages",
      "value": {
        "messages": [{
          "id": "msg_xxx",
          "from": {"id": "user_id"},
          "text": "Hello",
          "timestamp": "1640995200"
        }]
      }
    }]
  }]
}
```

**Traitement :**
1. Réception du message via webhook
2. Pas de marquage comme lu (non supporté)
3. Pas d'indicateur de frappe (non supporté)
4. Traitement direct du message
5. Envoi de la réponse

## 🚀 Utilisation

### Dans le Response Manager

Les indicateurs de frappe sont automatiquement activés lors de la réception d'un message :

```python
async def process_incoming_message_for_user(message, user_info):
    # Marquage automatique comme lu
    await mark_message_as_read(platform, user_credentials, message_id)
    
    # Envoi de l'indicateur de frappe
    await send_typing_indicator(platform, user_credentials, contact_id, message_id)
    
    # Traitement du message...
```

### Configuration

Aucune configuration supplémentaire n'est requise. Les fonctionnalités sont automatiquement activées selon la plateforme :

- **WhatsApp** : Indicateurs de frappe et marquage comme lu
- **Instagram** : Indicateurs de frappe et marquage comme lu (via Instagram Messaging API)

## 📊 Monitoring

### Logs WhatsApp

```
INFO - Marquage comme lu du message wamid.xxx
INFO - Envoi indicateur de frappe vers 33612345678
```

### Logs Instagram

```
INFO - Envoi typing_on + mark_seen Instagram vers user_id
INFO - Envoi action "typing_on" Instagram vers user_id
INFO - Envoi action "mark_seen" Instagram vers user_id
INFO - 📱 Instagram: Sender actions réussis vers user_id - Sender actions envoyés: typing=True, seen=True
```

## 🔄 Workflow Complet

### WhatsApp
1. **Réception** → Webhook reçoit le message
2. **Marquage** → Message marqué comme lu
3. **Indicateur** → Indicateur de frappe activé
4. **Traitement** → Message traité par l'IA
5. **Réponse** → Réponse envoyée (indicateur se désactive)

### Instagram
1. **Réception** → Webhook reçoit le message
2. **Marquage** → Message marqué comme lu (`mark_seen`)
3. **Indicateur** → Indicateur de frappe activé (`typing_on`)
4. **Traitement** → Message traité par l'IA
5. **Réponse** → Réponse envoyée (indicateur s'arrête automatiquement)

## ⚠️ Points d'Attention

1. **WhatsApp** : L'indicateur de frappe dure maximum 25 secondes
2. **Instagram** : L'indicateur de frappe fonctionne comme WhatsApp via sender actions
3. **Performance** : Les appels API supplémentaires peuvent impacter les performances
4. **Erreurs** : Les échecs d'indicateurs n'interrompent pas le traitement principal
5. **API Instagram** : Nécessite l'API Messaging avec Instagram Login (pas Graph API seule)

## 🛠️ Développement

### Ajout de Nouvelles Plateformes

Pour ajouter le support d'une nouvelle plateforme :

1. Implémenter les méthodes dans le service correspondant
2. Ajouter la logique dans `send_typing_indicator()`
3. Ajouter la logique dans `mark_message_as_read()`
4. Tester avec les webhooks de la plateforme

### Tests

```python
# Test WhatsApp
await send_typing_indicator("whatsapp", credentials, "33612345678", "msg_id")
await mark_message_as_read("whatsapp", credentials, "msg_id")

# Test Instagram (maintenant fonctionnel)
await send_typing_indicator("instagram", credentials, "user_id", "msg_id")
await mark_message_as_read("instagram", credentials, "msg_id")
```

