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

## 📸 Instagram Graph API

### ❌ Limitations

**Indicateur de Frappe :**
- ❌ Non supporté par l'API Instagram Graph
- ❌ Aucune fonctionnalité équivalente disponible
- ℹ️ L'API Instagram se concentre sur la réception d'événements, pas sur les interactions temps réel

**Marquage comme Lu :**
- ❌ Non supporté par l'API Instagram Graph
- ❌ Aucune fonctionnalité équivalente disponible
- ℹ️ Instagram ne fournit pas d'API pour les statuts de lecture

### 🔧 Implémentation

```python
# Pour Instagram, les fonctions retournent True sans action
async def send_typing_indicator(platform, user_credentials, contact_id, message_id):
    if platform == "instagram":
        logger.info("Indicateur de frappe non supporté pour Instagram")
        return True  # Ne bloque pas le processus

async def mark_message_as_read(platform, user_credentials, message_id):
    if platform == "instagram":
        logger.info("Marquage comme lu non supporté pour Instagram")
        return True  # Ne bloque pas le processus
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
- **Instagram** : Aucune fonctionnalité (limitations API)

## 📊 Monitoring

### Logs WhatsApp

```
INFO - Marquage comme lu du message wamid.xxx
INFO - Envoi indicateur de frappe vers 33612345678
```

### Logs Instagram

```
INFO - Marquage comme lu non supporté pour Instagram
INFO - Indicateur de frappe non supporté pour Instagram
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
2. **Traitement** → Message traité directement
3. **Réponse** → Réponse envoyée

## ⚠️ Points d'Attention

1. **WhatsApp** : L'indicateur de frappe dure maximum 25 secondes
2. **Instagram** : Aucune indication visuelle de traitement
3. **Performance** : Les appels API supplémentaires peuvent impacter les performances
4. **Erreurs** : Les échecs d'indicateurs n'interrompent pas le traitement principal

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

# Test Instagram (doit retourner True)
await send_typing_indicator("instagram", credentials, "user_id", "msg_id")
await mark_message_as_read("instagram", credentials, "msg_id")
```

