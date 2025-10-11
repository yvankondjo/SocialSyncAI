# Documentation d'Intégration de Nouvelles Plateformes

## Vue d'ensemble de l'architecture

Le système SocialSyncAI utilise une **architecture unifiée modulaire** pour gérer les messages WhatsApp et Instagram. Cette architecture permet d'intégrer facilement de nouvelles plateformes (Telegram, Twitter, Discord, etc.) en réutilisant les composants communs.

### Flux de traitement des messages

```
Webhook → Extraction → DB Storage → Redis Batching → Background Processing → AI Response → Envoi
```

## Composants Clés du Système

### 1. MessageBatcher (Redis Caching)
**Fichier** : `app/services/message_batcher.py`

**Responsabilités** :
- Groupement des messages par conversation (fenêtre de 2 secondes)
- Stockage temporaire dans Redis avec TTL automatique (30 minutes)
- Gestion des deadlines et locks distribués pour éviter les doublons
- Clés Redis structurées : `conv:{platform}:{account_id}:{contact_id}`

**Pourquoi Redis ?** Haute performance pour le batching haute fréquence, persistence automatique, TTL.

### 2. ResponseManager (Extraction & Crédits)
**Fichier** : `app/services/response_manager.py`

**Responsabilités** :
- **Extraction unifiée** : Fonction `extract_[platform]_message_content()` par plateforme
- **Gestion crédits** : Validation des features (images/audio) selon le plan utilisateur
- **Cache Redis** : Profils, credentials, conversations (TTL 1h)
- **Routage intelligent** : Selon plateforme et fonctionnalités disponibles

**Validation crédits** : Avant traitement, vérifie si l'utilisateur a accès aux features (images, audio, etc.)

### 3. BatchScanner (Background Processing)
**Fichier** : `app/services/batch_scanner.py`

**Responsabilités** :
- Scanner continu des conversations échues (toutes les 0.5s)
- Génération des réponses IA via le RAG agent
- Métriques temps réel (succès, timeouts, erreurs par plateforme)
- Gestion des timeouts (30s max par conversation)

**Métriques trackées** :
- Conversations traitées/échouées
- Temps de traitement moyen
- Taux de succès par plateforme

### 4. Système de Crédits & Rating
**Fichier** : `app/services/credits_service.py`

**Responsabilités** :
- Validation des accès aux features selon le plan de l'utilisateur
- Gestion des quotas et limites par plateforme
- Cache haute performance des données d'abonnement

**Features contrôlées** :
- Images, audio, vidéos selon le plan utilisateur
- Rate limiting par plateforme
- Crédits consommés par message

## Architecture par Plateforme Existante

### WhatsApp Integration

**Service** : `WhatsAppService` (API Graph Meta v23.0)
- Messages texte/images/audio avec retry automatique (3 tentatives)
- Webhooks avec vérification HMAC SHA256
- Téléchargement automatique des médias vers Supabase Storage

**Flux WhatsApp** :
1. Webhook Meta → `process_webhook_entry_with_user_routing()`
2. Extraction → `extract_whatsapp_message_content()` (token counting avec tiktoken)
3. Validation crédits → Features access (images/audio)
4. Sauvegarde DB → `save_unified_message()`
5. Batch Redis → `add_message_to_batch()` (clé: `conv:whatsapp:{phone_id}:{wa_id}`)
6. Traitement différé → `generate_smart_response()` (RAG + crédits)
7. Envoi réponse → `send_text_message()` avec indicateur de frappe

### Instagram Integration

**Service** : `InstagramService` (API Graph Meta)
- Messages directs avec indicateurs de frappe (`typing_on`, `mark_seen`)
- Gestion des profils utilisateurs avec cache enrichi
- Support des pièces jointes (images principalement)

**Particularités Instagram** :
- **Profils enrichis** : Cache des infos utilisateur (username, avatar)
- **Sender actions** : Séquence `typing_on` + `mark_seen`
- **Conversations** : Récupération des historiques de DM

## Étapes pour Intégrer une Nouvelle Plateforme

### Étape 1 : Service de Plateforme
Créer `app/services/[platform]_service.py` avec :
- Classe `[Platform]Service` (init, credentials, send_message, typing indicator)
- Méthode `validate_credentials()` pour vérifier les tokens
- Méthode `_send_with_retry()` avec backoff exponentiel
- Factory function `get_[platform]_service()`

### Étape 2 : Étendre les Schémas
Modifier `app/schemas/messages.py` :
- Ajouter la plateforme dans l'enum `Platform`
- Ajouter les types de médias si nécessaire dans `UnifiedMessageType`

### Étape 3 : ResponseManager
Ajouter dans `response_manager.py` :
- Fonction `extract_[platform]_message_content()` pour l'extraction
- Extension de `send_response()` pour l'envoi
- Extension de `send_typing_indicator_and_mark_read()`

### Étape 4 : Routes Webhook
Créer `app/routers/[platform].py` :
- Endpoint de validation credentials
- Webhook GET pour vérification plateforme
- Webhook POST avec vérification signature
- Routage vers `process_incoming_message_for_user()`

### Étape 5 : Schémas Spécifiques
Créer `app/schemas/[platform].py` :
- Modèles Pydantic pour credentials, messages, validation

### Étape 6 : Intégration Système
- Ajouter router dans `main.py`
- Étendre gestion crédits si features spécifiques
- Variables d'environnement dans `.env`

## Gestion des Médias et Contenu

### Types de Médias Supportés
- **Text** : Comptage tokens avec tiktoken (o200k_harmony)
- **Images** : Redimensionnement automatique (768x768 max), stockage Supabase
- **Audio** : Validation crédits, stockage si autorisé
- **Unsupported** : Messages rejetés avec notification utilisateur

### Processus Médias
1. Détection du type dans le webhook
2. Téléchargement depuis l'API de la plateforme
3. Redimensionnement/compression si nécessaire
4. Upload vers Supabase Storage avec nom unique (UUID)
5. Génération URL signée (expiration 24h)
6. Construction contenu unifié pour l'IA

## Cache Redis Stratégies

### Types de Cache
- **Conversation** : `conversation:{social_account_id}:{customer_id}` (TTL: 1h)
- **Credentials** : `credentials:{platform}:{account_id}` (TTL: 1h)
- **Profiles** : `{platform}_profile:{user_id}` (TTL: 1h)
- **Batch deadlines** : `conv:deadlines` (sorted set avec scores timestamp)

### Stratégies par Plateforme
- WhatsApp : Cache des numéros vérifiés
- Instagram : Cache des profils utilisateur enrichis
- Futures plateformes : Cache adapté selon besoins (tokens, sessions, etc.)

## Crédits & Rate Limiting

### Validation Features
Avant traitement d'un message :
```python
if feature_access:
    if platform == "whatsapp" and message_type == "image" and not feature_access.images:
        # Rejet avec message d'erreur
        return UnifiedMessageContent(unsupported...)
```

### Rate Limiting
- Retry automatique avec backoff exponentiel (0.5s → 1s → 2s)
- Gestion des erreurs 429 (rate limit) de chaque plateforme
- Métriques d'erreurs par plateforme dans BatchScanner

## Sécurité

### Webhooks
- Vérification signature HMAC SHA256 obligatoire
- Secrets stockés en variables d'environnement
- Validation payload avant traitement

### API Calls
- Timeouts configurés (connect: 5s, read: 10s, write: 5s)
- Retry automatique sur erreurs transitoires (429, 5xx)
- Gestion des rate limits par plateforme

## Monitoring & Métriques

### Métriques BatchScanner
- `conversations_processed` : Conversations traitées avec succès
- `conversations_failed` : Échecs de traitement
- `conversations_timed_out` : Timeouts (30s)
- `responses_generated` : Réponses IA générées
- `avg_processing_time` : Temps moyen de traitement

### Logs Structurés
Format standardisé avec contexte :
```
[{PLATFORM}] Message processed - platform, account_id, contact_id, message_type, processing_time
```

## Variables d'Environnement

### Obligatoires par Plateforme
```
[PLATFORM]_ACCESS_TOKEN=...
[PLATFORM]_ACCOUNT_ID=...
[PLATFORM]_VERIFY_TOKEN=...
[PLATFORM]_WEBHOOK_SECRET=...
```

### Optionnelles
```
[PLATFORM]_API_BASE_URL=https://api.[platform].com/v1
[PLATFORM]_WEBHOOK_TIMEOUT=30
[PLATFORM]_RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## Checklist d'Intégration

- [ ] Service plateforme créé avec méthodes standard
- [ ] Schémas étendus (Platform enum, types médias)
- [ ] ResponseManager étendu (extraction, envoi, typing)
- [ ] Routes webhook avec sécurité
- [ ] Crédits/features gérés si nécessaire
- [ ] Tests unitaires
- [ ] Documentation variables d'env
- [ ] Health checks
- [ ] Métriques intégrées

Cette architecture modulaire permet d'ajouter une nouvelle plateforme en 2-3 jours maximum, tout en bénéficiant automatiquement de l'IA, du système de crédits, du cache Redis et du processing en batch.
