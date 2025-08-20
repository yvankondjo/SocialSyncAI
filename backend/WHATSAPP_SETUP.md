# Configuration WhatsApp Business API

## Prérequis

1. **Application Meta for Developers** configurée
2. **Numéro de téléphone WhatsApp Business** vérifié
3. **Token d'accès permanent** généré

## 1. Configuration des variables d'environnement

Ajoutez ces variables à votre fichier `.env` :

```bash
# Obligatoires
WHATSAPP_ACCESS_TOKEN=EAAI565Fri...
WHATSAPP_PHONE_NUMBER_ID=683178638221369

# Pour les webhooks
WHATSAPP_VERIFY_TOKEN=mon_token_verification_unique
WHATSAPP_WEBHOOK_SECRET=mon_secret_webhook_securise
```

## 2. Test de l'API (sans webhooks)

Une fois l'API démarrée, testez les endpoints :

### Valider les credentials
```bash
curl -X POST "http://localhost:8000/api/whatsapp/validate-credentials" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "VOTRE_TOKEN",
    "phone_number_id": "VOTRE_PHONE_ID"
  }'
```

### Envoyer un template
```bash
curl -X POST "http://localhost:8000/api/whatsapp/send-template" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "33612345678",
    "template_name": "hello_world",
    "language_code": "en_US"
  }'
```

### Envoyer un message texte
```bash
curl -X POST "http://localhost:8000/api/whatsapp/send-text" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "33612345678", 
    "text": "Hello depuis l'\''API !"
  }'
```

## 3. Configuration des webhooks

### Étape 1 : Exposer votre serveur
Pour que Meta puisse accéder à vos webhooks, utilisez ngrok :

```bash
# Installer ngrok si nécessaire
npm install -g ngrok

# Exposer le port 8000
ngrok http 8000
```

Notez l'URL HTTPS générée (ex: `https://abc123.ngrok.io`)

### Étape 2 : Configurer dans Meta for Developers

1. Allez dans **Meta for Developers** → Votre app → **WhatsApp** → **Configuration**
2. Section **Webhooks** :
   - **URL de callback** : `https://abc123.ngrok.io/api/whatsapp/webhook`
   - **Token de vérification** : La valeur de `WHATSAPP_VERIFY_TOKEN`
   - Cliquez sur **Vérifier et enregistrer**

### Étape 3 : Activer les événements
Cochez ces événements dans la configuration webhook :
- ✅ `messages` - Messages entrants et statuts
- ✅ `message_deliveries` - Accusés de réception  
- ✅ `message_reads` - Accusés de lecture

### Étape 4 : Tester la vérification
Testez manuellement la vérification :

```bash
curl "http://localhost:8000/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=TEST123&hub.verify_token=mon_token_verification_unique"
# Doit retourner : TEST123
```

## 4. Test des webhooks

### Message entrant simulé
```bash
curl -X POST "http://localhost:8000/api/whatsapp/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "test-entry",
      "changes": [{
        "field": "messages",
        "value": {
          "messages": [{
            "id": "msg123",
            "from": "33612345678",
            "timestamp": "1640995200",
            "type": "text",
            "text": {"body": "Bonjour !"}
          }]
        }
      }]
    }]
  }'
```

### Statut de livraison simulé
```bash
curl -X POST "http://localhost:8000/api/whatsapp/webhook-test" \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "id": "test-entry", 
      "changes": [{
        "field": "messages",
        "value": {
          "statuses": [{
            "id": "msg123",
            "recipient_id": "33612345678",
            "status": "delivered",
            "timestamp": "1640995300"
          }]
        }
      }]
    }]
  }'
```

## 5. Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/whatsapp/send-text` | POST | Envoyer message texte |
| `/api/whatsapp/send-template` | POST | Envoyer template approuvé |
| `/api/whatsapp/send-media` | POST | Envoyer média (image/vidéo/audio/doc) |
| `/api/whatsapp/send-batch` | POST | Envoyer messages en lot |
| `/api/whatsapp/validate-credentials` | POST | Valider token et phone ID |
| `/api/whatsapp/business-profile` | GET | Profil business |
| `/api/whatsapp/webhook` | GET/POST | Gestion webhooks |
| `/api/whatsapp/webhook-info` | GET | Info configuration webhooks |
| `/api/whatsapp/health` | GET | Santé du service |

## 6. Documentation Swagger

Une fois l'API démarrée, consultez la documentation interactive :
- http://localhost:8000/docs

## 7. Dépannage

### Messages non reçus
- Vérifiez que votre numéro est ajouté comme testeur dans l'app Meta
- En développement, préférez les templates aux messages texte
- Consultez les logs pour voir les erreurs

### Webhooks non reçus
- Vérifiez que ngrok fonctionne : `curl https://votre-url.ngrok.io/api/whatsapp/webhook-info`
- Vérifiez le `WHATSAPP_VERIFY_TOKEN` dans les logs
- Testez avec l'endpoint `/webhook-test` d'abord

### Erreurs d'authentification
- Régénérez un token permanent dans Meta for Developers
- Vérifiez que le `phone_number_id` correspond à votre numéro configuré
